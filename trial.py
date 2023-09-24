# -*- coding: utf-8 -*-
"""trial.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1XzMg_WWvgZaIdQA7VWbvpz9kXF54lTXg
"""

import numpy as np
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from keras.layers import Embedding, LSTM, Dense, Dropout, Bidirectional
from tensorflow.keras.models import Sequential
from tensorflow.keras.utils import to_categorical

"""1.Dataset"""

from google.colab import drive
drive.mount('/content/drive')

file = open("/content/drive/MyDrive/shona_dataset.txt","r")
shona_text = file.read()

shona_text

import nltk
nltk.download('punkt')

import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Preprocess the text
def clean_text(shona_text):
    # Convert text to lowercase
    shona_text = shona_text.lower()

    # Remove punctuation and special characters
    shona_text = re.sub(r'[^\w\s]', '', shona_text)

    # Tokenize the text
    words = word_tokenize(shona_text)

    # Remove stopwords
    nltk.download('stopwords')
    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word not in stop_words]

    # Join the words back into a cleaned text
    cleaned_text = ' '.join(words)

    return cleaned_text

cleaned_text = clean_text(shona_text)

cleaned_text

# Tokenize and preprocess
tokenizer = Tokenizer()
tokenizer.fit_on_texts([cleaned_text])
total_words = len(tokenizer.word_index) + 1

from keras.preprocessing.text import text_to_word_sequence
# tokenize the document
result = text_to_word_sequence(cleaned_text)
print(result)

"""2. Creating a Vocabulary"""

#using a keras tokenizer to build an optimal vocabulary
tokenizer = Tokenizer()
tokenizer.fit_on_texts([cleaned_text])
max_vocab_size= 10000  # the vocabulary size
word_index = tokenizer.word_index
vocabulary_size = min(max_vocab_size, len(word_index))

reduced_word_index = {}
for word, index in word_index.items():
    if index <= vocabulary_size:
        reduced_word_index[word] = index
    else:
        break



tokenizer.word_index = reduced_word_index
tokenizer.word_index[tokenizer.oov_token] = vocabulary_size + 1
tokenizer.num_words = vocabulary_size + 1
vocabulary_size = len(word_index)
print("Vocabulary size:", vocabulary_size)

"""Genshim Word Embeddings"""

from gensim.models import Word2Vec

# Train word2vec model with gensim
sentences = [sentence.split() for sentence in cleaned_text.split('.')]
model = Word2Vec(sentences, vector_size=100, window=5, min_count=1, workers=4)
model.save("word2vec_shona_embeddings.model")

"""RNN Model 1"""

model1 = Sequential()
model1.add(Embedding(tokenizer.num_words , 100, input_length=5))
model1.add(Bidirectional(LSTM(150, return_sequences=True)))
model1.add(Dropout(0.2))
model1.add(LSTM(100))
model1.add(Dense(tokenizer.num_words , activation='softmax'))

model1.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
#save the trained model
model1.save('model1.h1')
#print the summary of the model
model1.summary()

"""RNN Model 2 with Pretrained embeddings"""

# Load the word2vec model
model_gensim = Word2Vec.load("word2vec_shona_embeddings.model")
embedding_matrix = np.zeros((tokenizer.num_words , 100))
#for word, i in tokenizer.word_index.items():
    #try:
       # embedding_vector = model_gensim.wv[word]
        #if embedding_vector is not None:
            #embedding_matrix[i] = embedding_vector
    #except KeyError:
        # Word not present in gensim model, a zero embedding will be used for this word
        #pass


model2 = Sequential()
model2.add(Embedding(tokenizer.num_words , 100, weights=[embedding_matrix], input_length=5, trainable=False))
model2.add(Bidirectional(LSTM(150, return_sequences=True)))
model2.add(Dropout(0.2))
model2.add(LSTM(100))
model2.add(Dense(tokenizer.num_words , activation='softmax'))

model2.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
#save the trained model
model2.save('model2.h1')
#print summary of the model
model2.summary()

from tensorflow.keras.models import load_model
import numpy as np
import pickle

# Load the model and tokenizer
model = load_model('model1.h1')
model = load_model('model2.h1')

"""Training Models"""

import keras
from tensorflow.keras.preprocessing.sequence import pad_sequences
from sklearn.model_selection import train_test_split

input_sequences = []
for line in cleaned_text.split('.'):
    token_list = tokenizer.texts_to_sequences([line])[0]
for i in range(1, len(token_list)):
    n_gram_sequence = token_list[:i+1]
    input_sequences.append(n_gram_sequence)

input_sequences = np.array(pad_sequences(input_sequences, maxlen=6, padding='pre'))
X, y = input_sequences[:, :-1], input_sequences[:, -1]
y = keras.utils.to_categorical(y, num_classes=tokenizer.num_words)

# Split the dataset into training and validation sets
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.4, random_state=42)

X

y

# Split the dataset into training and validation sets
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.4, random_state=42)

# Training Model 1
history1 = model1.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=100, verbose=1)

# Training Model 2
history2 = model2.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=100, verbose=1)

"""Model Evaluation"""

val_loss_model1 = history1.history['val_loss'][-1]
val_loss_model2 = history2.history['val_loss'][-1]

print(f"Validation Loss for Model 1: {val_loss_model1}")
print(f"Validation Loss for Model 2: {val_loss_model2}")

if val_loss_model1 < val_loss_model2:
    best_model = model1
    best_model_name = "best_model1.h5"
else:
    best_model = model2
    best_model_name = "best_model2.h5"

best_model.save(best_model_name)
print(f"Saved the best model as {best_model_name}")

params_model1 = model1.count_params()
params_model2 = model2.count_params()

print(f"Model 1 has {params_model1} parameters.")
print(f"Model 2 has {params_model2} parameters.")

from keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences

# Load the previously saved model
model = load_model('best_model2.h5')

def predict_next_words(model, tokenizer, text, num_words=1):
    """
    Predict the next set of words using the trained model.

    Args:
    - model (keras.Model): The trained model.
    - tokenizer (Tokenizer): The tokenizer object used for preprocessing.
    - text (str): The input text.
    - num_words (int): The number of words to predict.

    Returns:
    - str: The predicted words.
    """
    for _ in range(num_words):
        # Tokenize and pad the text
        sequence = tokenizer.texts_to_sequences([text])[0]
        sequence = pad_sequences([sequence], maxlen=5, padding='pre')

        # Predict the next word
        predicted_probs = model.predict(sequence, verbose=0)
        predicted = np.argmax(predicted_probs, axis=-1)

        # Convert the predicted word index to a word
        output_word = ""
        for word, index in tokenizer.word_index.items():
            if index == predicted:
                output_word = word
                break

        # Append the predicted word to the text
        text += " " + output_word

    return ' '.join(text.split(' ')[-num_words:])


# Prompt the user for input
user_input = input("Please type five words in Shona: ")

# Predict the next words
predicted_words = predict_next_words(model, tokenizer, user_input, num_words=3)
print(f"The next words might be: {predicted_words}")

import re
import numpy as np
import streamlit as st
from keras.models import load_model
from keras.preprocessing.text import Tokenizer

# Load the tokenizer
tokenizer = Tokenizer()
tokenizer_path = 'tokenizer.pickle'
tokenizer = Tokenizer()
tokenizer.fit_on_texts([''])

# Load the trained model
model_path = 'best_model2.h5'
model = load_model(model_path)

def preprocess_input(text):
    # Convert to lowercase
    text = text.lower()

    # Remove punctuation marks and special characters
    text = re.sub(r"[^\w\s]", "", text)

    # Tokenize the text into words
    tokens = text.split()

    return tokens

def generate_next_words(input_text, num_words):
    # Preprocess the input text
    input_tokens = preprocess_input(input_text)

    # Convert tokens to word indices
    input_sequence = tokenizer.texts_to_sequences([input_tokens])[0]

    # Pad the sequence to a fixed length (if necessary)
    seq_length = len(input_sequence[0])
    max_sequence_length = seq_length# Specify the maximum sequence length used during training
    input_sequence = np.pad(input_sequence, (max_sequence_length - len(input_sequence), 0), 'constant')

    # Generate the next word(s)
    generated_words = input_tokens.copy()

    for _ in range(num_words):
        predicted_word_index = model.predict_classes(input_sequence.reshape(1, -1), verbose=0)
        predicted_word = tokenizer.index_word[predicted_word_index[0]]
        generated_words.append(predicted_word)
        input_sequence = np.roll(input_sequence, -1)
        input_sequence[-1] = predicted_word_index[0]

    return ' '.join(generated_words)

def main():
    st.title('Shona Text Generator')

    # User input
    user_input = st.text_input('Enter five words in Shona:', max_chars=100)

    if user_input:
        num_words_to_generate = 1  # Change this to generate multiple words

        # Generate next word(s)
        generated_words = generate_next_words(user_input, num_words_to_generate)
        st.markdown('**Generated Text:**')
        st.write(generated_words)

if __name__ == '__main__':
    main()

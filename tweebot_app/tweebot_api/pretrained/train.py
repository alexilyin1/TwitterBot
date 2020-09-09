import pandas as pd
import numpy as np
from .proc import ProcessTweets
import keras
from keras.layers import Embedding, Dense, Dropout, LSTM
from keras.callbacks import EarlyStopping, ModelCheckpoint


class KerasGenerator(keras.models.Sequential):

    def __init__(self, vocab_size=None, input_length=None, input=None, output=None, **kwargs):
        super(KerasGenerator, self).__init__(**kwargs)
        self.dim = vocab_size
        self.input_length = input_length
        self.X = input
        self.y = output
        self.callbacks = [(EarlyStopping(monitor='val_sparse_categorical_crossentropy',  patience=3, verbose=1)),
                          (ModelCheckpoint('weights.hdf5', monitor='val_sparse_categorical_crossentropy', verbose=1,
                                           save_best_only=True, save_weights_only=True))]

    def set_params(self):
        self.add(Embedding(input_dim=self.dim, output_dim=100, input_length=self.input_length))
        self.add(LSTM(units=100))
        self.add(Dropout(rate=0.25))
        self.add(Dense(units=1, activation='softmax'))

    def train(self):
        self.fit_generator(generator=self.batch_generator(self.X, self.y),
                           steps_per_epoch=int(len(self.X/128)),
                           epochs=20)

    @staticmethod
    def batch_generator(X, y, batch_size=128):
        while True:
            n_batches_per_epoch = X.shape[0]//batch_size
            for i in range(n_batches_per_epoch):
                index_batch = range(X.shape[0])[batch_size*i: batch_size*(i+1)]
                X_batch = X[index_batch, :]
                y_batch = y[index_batch]
                yield X_batch, np.array(y_batch)

'''
text = pd.read_csv('../../../tweets.csv')
text = text[text['clean_text'].notna()]

proc = ProcessTweets(text['clean_text'].values)

# print(proc.X_train.shape)
# print(proc.y_train)
gen = KerasGenerator(proc.vocab_size, proc.X_train.shape[1],
                      proc.X_train, proc.y_train)

model_json = gen.to_json()
with open('../../../model_setup.json', 'w') as file:
    file.write(model_json)
'''
import os
import pandas as pd
import pickle

from keras.preprocessing.text import Tokenizer
from keras.models import load_model
from tweebot_app.tweebot_api.pretrained.proc import ProcessTweets
from tweebot_app.tweebot_api.pretrained.train import KerasGenerator

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

dat = pd.read_csv('tweets.csv')

dat = dat[dat['clean_text'].notna()].loc[:, 'clean_text'].values


def generate_text(text, length):
    model = load_model('weights.h5', custom_objects={'KerasGenerator': KerasGenerator,
                                                     'callbacks': KerasGenerator().callbacks})
    words = []
    res = text
    for x in range(length):
        tokenizer = Tokenizer()
        tokenizer.fit_on_texts(dat)
        word2index = {v: k for k, v in tokenizer.word_index.items()}

        proc = ProcessTweets(text, False)
        prob = model.predict(proc.pred_enc).flatten()
        word = word2index[proc.sample(prob)]
        res += ' ' + word

    return res


tokenizer = Tokenizer()
tokenizer.fit_on_texts(dat)
with open('tweebot_app/tweebot_api/pretrained/tokenizer.pickle', 'wb') as file:
    pickle.dump(tokenizer, file, protocol=pickle.HIGHEST_PROTOCOL)


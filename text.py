from tweebot_app.tweebot_app.keys import DB, POSTGRES_USER, POSTGRES_PASS, HOST
import os
import pandas as pd
import psycopg2
import regex as re
from nltk.corpus import words
corpus = set(words.words())


def text_cleaner(text):
    slang = ['omg', 'lol', 'lmao', 'wtf', 'smh', 'rofl', 'tmi']
    clean_text = re.sub("RT|@|#|[\,|:|\'|\\|\/|\"|.]", "", text)
    clean_text = " ".join([x for x in clean_text.split(' ') if x.lower() in corpus or x.lower() in slang])
    return clean_text


def query_table(filename):
    if filename not in os.listdir():
        try:
            connection = psycopg2.connect(user=POSTGRES_USER, password=POSTGRES_PASS,
                                          host=HOST, database=DB)
            cursor = connection.cursor()
            query = "SELECT * FROM tweebot"

            cursor.execute(query)
            records = cursor.fetchall()

            dat = pd.DataFrame(records, columns=['likes', 'retweets', 'text'])
            dat['clean_text'] = dat['text'].apply(text_cleaner)
            dat = dat[dat['clean_text'] != '']

            dat.to_csv(filename)

            cursor.close()
            connection.close()

        except psycopg2.Error as error:
            print('Table does not exist, try again')
    else:
        print('File in directory, try reading file instead')


text = pd.read_csv('tweets.csv').loc[:, 'likes':]
text['clean_text'] = text['text'].apply(text_cleaner)
print(text['clean_text'])
text.to_csv('tweets.csv', index=False)
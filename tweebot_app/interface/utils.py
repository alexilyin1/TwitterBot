import uuid
import warnings
import tweepy
import time
import datetime
import psycopg2
import os
import pandas as pd
import regex as re
import nltk
from nltk.corpus import stopwords, words
nltk.download('stopwords')
stopwords = set(stopwords.words())
corpus = set(words.words())

class MyStreamListener(tweepy.StreamListener):

    def __init__(self, time_limit, connection, cursor, email, topic, log_status=True):
        super(MyStreamListener, self).__init__()
        self.start_time = time.time()
        self.limit = time_limit
        self.connection = connection
        self.cursor = cursor
        self.email = email
        self.topic = topic
        self.log_status = log_status

    def on_status(self, status):
        """
        :param status: Tweepy status arg, tweets data located within status
        ### First, check that set streaming time has not been exceeded. If the tweet is a "retweet", extract the full text
        ### retweet count and like count. This data is pushed to postgres table
        """
        try:
            if (time.time() - self.start_time) < self.limit:
                if self.log_status:
                    print('Querying tweet...')

                if 'retweeted_status' in status._json.keys():
                    try:
                        self.cursor.execute('INSERT INTO interface_usertweetsmodel (num_likes, num_retweets, text, tweet_id, user_id, email, topic) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                                           (status.retweeted_status.favorite_count, status.retweeted_status.retweet_count, status._json['retweeted_status']['extended_tweet']['full_text'], status._json['id_str'], status._json['user']['screen_name'], self.email, self.topic, ))
                    except Exception as e:
                        self.cursor.execute('INSERT INTO interface_usertweetsmodel (num_likes, num_retweets, text, tweet_id, user_id, email, topic) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                                           (status.retweeted_status.favorite_count, status.retweeted_status.retweet_count, status._json['retweeted_status']['text'], status._json['id_str'], status._json['user']['screen_name'], self.email, self.topic, ))
                    self.connection.commit()
                    return True
                elif 'extended_tweet' in status._json.keys():
                    try:
                        self.cursor.execute('INSERT INTO interface_usertweetsmodel (num_likes, num_retweets, text, tweet_id, user_id, email, topic) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                                           (status.favorite_count, status.retweet_count, status._json['extended_tweet']['full_text'], status._json['id_str'], status._json['user']['screen_name'], self.email, self.topic, ))
                    except Exception as e:
                        self.cursor.execute('INSERT INTO interface_usertweetsmodel (num_likes, num_retweets, text, tweet_id, user_id, email, topic) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                            (status.favorite_count, status.retweet_count, status._json['extended_tweet']['full_text'], status._json['id_str'], status._json['user']['screen_name'], self.email, self.topic,))
                    self.connection.commit()
                    return True
                else:
                    pass
            else:
                self.connection.close()
                self.cursor.close()
                return False
        except Exception as e:
            print(e)

    def on_connect(self):
        print('Connecting to Tweepy Streaming API...')

    def on_error(self, status):
        return 'Error: {}'.format(status)


class TweepyToSQL:

    def __init__(self, db_name, db_user, db_pass, host, email):
        self.DATABASE = db_name
        self.POSTGRES_USER = db_user
        self.POSTGRES_PASS = db_pass
        self.HOST = host
        self.email = email
        self.connection = None
        self.cursor = None
        self.auth = None
        self.api = None
        self.listener = None
        self.stream = None

        self._connect('interface_usertweetsmodel')

    def _connect(self, table_name):
        """
        :param table_name: Takes the name of the table to be created (for holding tweets)
        :return: returns active cursor and connection objects as class variables
        """
        self.connection = psycopg2.connect(database=self.DATABASE, host=self.HOST,
                                           user=self.POSTGRES_USER, password=self.POSTGRES_PASS)
        self.cursor = self.connection.cursor()

        try:
            self.cursor.execute("CREATE TABLE {} (num_likes integer, num_retweets integer, text varchar);".format(table_name))
        except psycopg2.Error as e:
            warnings.warn('Table already exists')

    def tweepy_auth(self, CKEY, CSECRET, ATOKEN, ATOKEN_SECRET):
        """
        :param CKEY:
        :param CSECRET:
        :param ATOKEN:
        :param ATOKEN_SECRET:
        :return: Set class tweepy API variable
        """
        self.auth = tweepy.OAuthHandler(CKEY, CSECRET)
        self.auth.set_access_token(ATOKEN, ATOKEN_SECRET)
        self.api = tweepy.API(self.auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

    def pass_tweets(self, time_limit: int, track: str):
        """
        :param time_limit: Time limit in seconds for tweet retrieval. Average rate is 1000 tweets per min
        :return: Begins tweet retrieval/storage process using MyStreamListener class defined above
        """
        self.listener = MyStreamListener(time_limit, self.connection, self.cursor, self.email, track)

        self.stream = tweepy.Stream(auth=self.api.auth, listener=self.listener, tweet_mode='extended')
        self.stream.filter(track=[track])

        if self.connection:
            self.cursor.close()
            self.connection.close()

    def query_table(self, filename, target):
        """
        :param filename: The filename (preferrably .csv) to save the tweet data as
        :return: Returns both pandas DataFrame and s
        """
        if filename not in os.listdir():
            try:
                self.cursor.execute("SELECT * FROM interface_usertweetsmodel where email = %s;",
                                    (target, ))
                records = self.cursor.fetchall()

                dat = pd.DataFrame(records, columns=['id', 'likes', 'retweets', 'text',
                                                     'email', 'topic', 'tweet_id', 'user_id'])
                dat['clean_text'] = dat['text'].apply(self.text_cleaner)
                dat = dat[dat['clean_text'] != '']

                dat.to_csv(filename, index=False)

                self.cursor.close()
                self.connection.close()

            except psycopg2.Error as error:
                print('Table does not exist, try again', error)
        else:
            print('File in directory, try reading file instead')

    def purge(self, target):
        self.cursor.execute('DELETE FROM interface_usertweetsmodel WHERE email = %s;',
                            (target, ))
        self.connection.commit()
        self.cursor.close()
        self.connection.close()

    @staticmethod
    def text_cleaner(text):
        slang = ['omg', 'lol', 'lmao', 'wtf', 'smh', 'rofl', 'tmi']
        clean_text = re.sub("RT|@|#|[\,|:|\'|\\|\/|\"|.]", "", text)
        clean_text = " ".join([x for x in clean_text.split(' ') if x.lower() in corpus or x.lower() in slang and x.lower() not in stopwords])
        return clean_text


class UserDB:

    def __init__(self, db_name, db_user, db_pass, host):
        self.DATABASE = db_name
        self.POSTGRES_USER = db_user
        self.POSTGRES_PASS = db_pass
        self.HOST = host
        self.connection = None
        self.cursor = None

        self._connect()

    def _connect(self):
        self.connection = psycopg2.connect(database=self.DATABASE, host=self.HOST,
                                           user=self.POSTGRES_USER, password=self.POSTGRES_PASS)
        self.cursor = self.connection.cursor()

    def _dconnect(self):
        self.connection.close()
        self.cursor.close()

    def to_db(self, email, time=datetime.datetime.now()):
        self.cursor.execute('INSERT INTO interface_user (url, email, date_created) VALUES (%s, %s, %s);',
                            (uuid.uuid4(), email, time, ))
        self.connection.commit()
        print('User succesfully queried')

    def get_all(self):
        self.cursor.execute('SELECT * FROM interface_user')
        res = self.cursor.fetchall()
        return res

    def get_user(self, target):
        self.cursor.execute('SELECT email FROM interface_user WHERE email = %s;',
                            (target, ))
        res = self.cursor.fetchall()
        return res

    def get_id(self, target):
        self.cursor.execute('SELECT url FROM interface_user WHERE email = %s;',
                            (target, ))
        res = self.cursor.fetchall()
        return res

    def drop_user(self, target):
        self.cursor.execute('DELETE FROM interface_user WHERE email = %s;',
                            (target, ))
        self.connection.commit()

    def __repr__(self):
        status = not bool(self.connection.closed)
        return 'Connection open: {}'.format(status)

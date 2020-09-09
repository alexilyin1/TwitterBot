import numpy as np
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences


class ProcessTweets:
    """
    Takes preprocessed text, uses TF-IDF vectorizer for streamlined approach to sequential text building -
    for every loaded tweet, find the top word by "importance"/TF-IDF score. Also processes text for
    seq2seq model building
    """
    def __init__(self, documents, train=True, train_size=0.75):
        self.document_set = documents
        self.train = train
        self.tokenizer = None
        self.vocab_size = None
        self.word2index = None
        self.train_size = train_size

        if self.document_set is not None and self.train:
            self.tokenize_train()
            self.X_train, self.y_train, self.X_test, self.y_test = self.create_data(self.tokenizer)
        elif not self.train:
            self.pred_enc, self.word2index_pred = self.tokenize_preds()
        else:
            raise ValueError('No document set present, pass a set of documents when initializing the ProcessTweets object')

    def tokenize_train(self):
        """
        Use Keras preprocessing module to create word2index and input sequences
        """
        tokenizer = Tokenizer()
        tokenizer.fit_on_texts(self.document_set)

        self.tokenizer = tokenizer
        self.vocab_size = len(tokenizer.word_index)+1
        self.word2index = {v: k for k, v in tokenizer.word_index.items()}

    def tokenize_preds(self):
        self.tokenizer = Tokenizer()
        enc = self.tokenizer.texts_to_sequences([self.document_set])[0]
        enc_padded = pad_sequences([enc], maxlen=27, padding='pre')
        index_word = {v: k for k,v in self.tokenizer.word_index.items()}
        return enc_padded, index_word

    def create_data(self, tokenizer):
        N = np.array(self.document_set).shape[0]
        train_perc = self.train_size
        n_train = int(N*train_perc)
        n_test = N - n_train

        seq, index_train, index_test = [], [], []
        count = 0
        for irow, line in enumerate(self.document_set):
            encoded = self.tokenizer.texts_to_sequences([line])[0]
            for i in range(1, len(encoded)):
                sequence = encoded[:i+1]
                seq.append(sequence)

                if irow < n_train:
                    index_train.append(count)
                else:
                    index_test.append(count)
                count += 1

        max_length = max([len(seq_) for seq_ in seq])
        seq = pad_sequences(seq, maxlen=int(max_length), padding='pre')
        seq = np.array(seq)

        input_ = seq[:, :-1]
        output = seq[:, -1]
        # output = to_categorical(output, num_classes=self.vocab_size, dtype='uint8')
        return input_[index_train], output[index_train], input_[index_test], output[index_test]

    @staticmethod
    def _find_max(input_sequence):
        return max([len(seq) for seq in input_sequence])

    @staticmethod
    def sample(prob):
        return np.random.choice(range(len(prob)), p=prob)
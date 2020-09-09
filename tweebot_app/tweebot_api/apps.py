import os
import pickle
from django.apps import AppConfig

from tensorflow.keras.models import load_model
from .pretrained.train import KerasGenerator

# tb._SYMBOLIC_SCOPE.value = True
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"


class TweebotApiConfig:

    def __init__(self, model):
        self.model = model

        self.TOKENIZER_DIR = os.path.abspath('/home/amt99/Desktop/tweebot/tweebot_app/tweebot_api/pretrained/')
        self.TOKENIZER_PATH = 'tokenizer.pickle'
        self.TOKENIZER_ABS = os.path.join(self.TOKENIZER_DIR, self.TOKENIZER_PATH)

        self.MODEL_DIR = os.path.abspath('/home/amt99/Desktop/tweebot/tweebot_app/tweebot_api/pretrained/')
        self.MODEL_PATH = '{}.h5'.format(self.model)
        self.MODEL_ABS = os.path.join(self.MODEL_DIR, self.MODEL_PATH)

    def tokenizer(self):
        with open(self.TOKENIZER_ABS, 'rb') as file:
            tokenizer = pickle.load(file)
        return tokenizer

    def predictor(self):
        predictor = load_model(self.MODEL_ABS,
                               custom_objects={'KerasGenerator': KerasGenerator,
                                               'callbacks': KerasGenerator().callbacks})
        return predictor

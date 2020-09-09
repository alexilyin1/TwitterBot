import random
from .pretrained.proc import ProcessTweets
from .apps import TweebotApiConfig
from django.http import JsonResponse
from rest_framework.views import APIView


class GenerateTweets(APIView):

    def __init__(self):
        super(GenerateTweets, self).__init__()

    def get(self, request):
        if request.method == 'GET':
            url = request.build_absolute_uri().split('/model/')[1].split('/')[0]
            params = request.GET.get('sentence')

            res = params
            length = random.randint(10, 20)

            tac = TweebotApiConfig(url)
            for x in range(length):
                tokenizer = tac.tokenizer()
                predictor = tac.predictor()

                word2index = {v: k for k, v in tokenizer.word_index.items()}
                proc = ProcessTweets(params, False)
                prob = predictor.predict(proc.pred_enc).flatten()
                word = word2index[proc.sample(prob)]
                res += ' ' + word

            response = res
            return JsonResponse(response, safe=False)


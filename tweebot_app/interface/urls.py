from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('demo', views.demo, name='demo'),
    path('streamer', views.streamer, name='streamer'),
    path('purge', views.purge, name='purge'),
    re_path('login', views.login, name='login'),
    re_path('dash/[a-z|A-z|0-9]{1,64}', views.dash, name='dash'),
    path('bot', views.bot, name='bot'),
    re_path('bot/old/[a-z|A-z]{1,30}', views.bot_old, name='old bots'),
    re_path('bot/new/[a-z|A-z]{1,30}', views.bot_new, name='new bots')
]



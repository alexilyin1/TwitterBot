from django.contrib import admin
from django.urls import path, re_path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    re_path('^model/[a-z|A-z]{1,30}/', views.GenerateTweets.as_view())
]

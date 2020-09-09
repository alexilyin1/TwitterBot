import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class EmailManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, ):
        if not email:
            raise ValueError('Email address must be provided')

        email = self.normalize_email(email)
        user = self.model(email=email)
        user.save(using=self._db)
        return user

    def create_user(self, email=None):
        return self._create_user(email)


class User(AbstractBaseUser, PermissionsMixin):
    password = None
    last_login = None
    is_superuser = None

    REQUIRED_FIELDS = []
    USERNAME_FIELD = 'email'

    objects = EmailManager()

    key = models.UUIDField(name='url', unique=True, default=1234)
    email = models.EmailField(name='email', unique=True, blank=False, null=True)
    date_created = models.DateTimeField(name='date_created', unique=True, blank=False, null=True)

    def get_short_name(self):
        return self.email


class UserTweetsModel(models.Model):
    num_likes = models.IntegerField(name='num_likes')
    num_retweets = models.IntegerField(name='num_retweets')
    text = models.TextField(name='text', default='')
    tweet_user_id = models.TextField(name='user_id', default='')
    tweet_id = models.TextField(name='tweet_id', default='')
    topic = models.TextField(name='topic', default='')
    email = models.EmailField(name='email', default='user@gmail.com')

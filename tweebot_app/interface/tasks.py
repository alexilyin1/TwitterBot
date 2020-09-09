import uuid
from django.core.mail import send_mail
from .celery import app
from celery.schedules import crontab
from celery.task import periodic_task
from celery.utils.log import get_task_logger
from .utils import TweepyToSQL, UserDB
from .keys import (DB, POSTGRES_USER, POSTGRES_PASS, HOST,
				   CONSUMER_SECRET, CONSUMER_KEY, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

logger = get_task_logger(__name__)


def private_link(email, sender=None, url='http://127.0.0.1:8000/login'):
	user = UserDB(DB, POSTGRES_USER, POSTGRES_PASS, HOST)
	print('Connected to Postgres: {}'.format(not bool(user.connection.closed)))

	user.cursor.execute('SELECT url FROM interface_user WHERE email = %s;',
						(email,))
	res = user.cursor.fetchall()
	user._dconnect()
	send_mail(
		'Your tweets are ready!',
		'Your unique ID is: {}, navigate to the authentication page and enter it: {}'.format(str(res[0][0]), url),
		'tweebotemail@gmail.com',
		[email],
		fail_silently=False
	)


@app.task
def stream_task(email, stream_time, track):
	to_sql = TweepyToSQL(DB, POSTGRES_USER, POSTGRES_PASS, HOST, email)

	if to_sql.connection:
		to_sql.connection.rollback()

	to_sql.tweepy_auth(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
	to_sql.pass_tweets(stream_time * 60, track)

	private_link(email)


@periodic_task
def purge_account(email):
	user = UserDB(DB, POSTGRES_USER, POSTGRES_PASS, HOST)
	user.drop_user(email)

	to_sql = TweepyToSQL(DB, POSTGRES_USER, POSTGRES_PASS, HOST, email)
	if to_sql.connection:
		to_sql.connection.rollback()
	to_sql.purge(email)


app.conf.beat_schedule = {
	'purge_account': {
		'task': purge_account,
		'schedule': crontab(0, 0, day_of_month=1)
	}
}

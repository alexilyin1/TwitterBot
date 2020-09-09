import requests
from datetime import datetime
from operator import methodcaller
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib import messages
from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from rest_framework.test import APIClient
from .forms import StreamForm, LoginForm, PurgeForm
from .utils import UserDB, TweepyToSQL
from .ds_utils import Summary, embed_html
from .tasks import stream_task
from .keys import (DB, POSTGRES_USER, POSTGRES_PASS, HOST)


def home(request):
	return render(request, 'interface/body_home.html')


def demo(request):
	return render(request, 'interface/demo.html')


def streamer(request):
	if request.method == 'POST':
		form = StreamForm(request.POST)
		if form.is_valid():
			data = form
			topic = data['topic'].value()
			stream_time = int(data['stream_time'].value())
			email = data['email'].value()

			user = UserDB(DB, POSTGRES_USER, POSTGRES_PASS, HOST)
			print('Connected to Postgres: {}'.format(not bool(user.connection.closed)))

			# user.cursor.execute('DELETE FROM interface_user')
			# user.connection.commit()

			try:
				validate_email(email)
			except ValidationError as e:
				raise ValidationError('Email not valid, try again', e)

			try:
				user.to_db(email)
			except Exception as E:
				messages.error(request, 'Email {} already exists in the system, try a different email or request a new session'.format(email))
				return HttpResponseRedirect(request.path_info)

			try:
				user.get_user(email)
				user._dconnect()
				messages.success(request, 'Check your email in {} minutes to access your unique link'.format(stream_time))
				stream_task.delay(email, stream_time, topic)
				return redirect('/streamer')
			except Exception as E:
				user._dconnect()
				messages.error(request, 'Duplicate email found or something went wrong on this end with error: ' + str(E))
				return HttpResponseRedirect(request.path_info)

			# print(json.loads(requests.get('http://127.0.0.1:8000//model/?sentence='+topic).text))
	else:
		form = StreamForm()
	return render(request, 'interface/streamer.html', {'form': form})


def purge(request):
	if request.method == 'POST':
		form = PurgeForm(request.POST)
		if form.is_valid():
			data = form
			email = data['email'].value()
			user = UserDB(DB, POSTGRES_USER, POSTGRES_PASS, HOST)
			print('Connected to Postgres: {}'.format(not bool(user.connection.closed)))

			user.drop_user(email)

			to_sql = TweepyToSQL(DB, POSTGRES_USER, POSTGRES_PASS, HOST, email)
			if to_sql.connection:
				to_sql.connection.rollback()
			to_sql.purge(email)

			return redirect('/')
	else:
		form = StreamForm()
	return render(request, 'interface/purge.html', {'form': form})


def login(request):
	if request.method == 'POST':
		form = LoginForm(request.POST)
		if form.is_valid():
			data = form
			email = data['email'].value()
			uuid_in = data['uuid'].value()
			user = UserDB(DB, POSTGRES_USER, POSTGRES_PASS, HOST)
			print('Connected to Postgres: {}'.format(not bool(user.connection.closed)))

			if user.get_id(email) == []:
				messages.error(request, 'Email not found in database, redirecting to Streamer page')
				print('Authentication failure')
				return redirect('/streamer')
			elif str(user.get_id(email)[0][0]) != str(uuid_in):
				messages.error(request, 'UUID does not match, check email and try again')
				print('Authentication failure')
				return redirect('/login')
			elif str(user.get_id(email)[0][0]) == str(uuid_in):
				print('Authentication success')
				return redirect('dash/{}'.format(email.split('@')[0]))

			user._dconnect()
	else:
		form = LoginForm()
	return render(request, 'interface/login.html', {'form': form})


def dash(request):
	url = request.build_absolute_uri().split('/dash/')[1]
	filename = None

	user = UserDB(DB, POSTGRES_USER, POSTGRES_PASS, HOST)
	all_users = [x[2] for x in user.get_all()]

	spl = [x[0] for x in map(methodcaller("split", "@"), all_users)]
	idx = ''
	for e in spl:
		if e == url:
			idx = spl.index(e)
	if idx == '':
		raise Http404('User not in DB, return to the streamer page to create a new user')
	user._dconnect()

	user = all_users[idx]
	to_sql = TweepyToSQL(DB, POSTGRES_USER, POSTGRES_PASS, HOST, user)
	if to_sql.connection:
		to_sql.connection.rollback()
	filename = user.split('@')[0] + '_' + datetime.now().strftime('%H:%M:%S') + '_tweets.csv'
	to_sql.query_table(filename, user)

	su = Summary(filename=filename)

	reaction_type = ['likes', 'retweets']
	stat = ['mean', 'std', 'min', 'max']
	res = []
	for t in reaction_type:
		for s in stat:
			res.append(round(su.summary_stats(t, s), 2))

	su.wc(); wc = su.wc_dict
	top = list(zip(list(wc.keys())[:10], list(wc.values())[:10]))

	html_l = embed_html(su.get_most_likes())
	html_re = embed_html(su.get_most_re())
	lr = su.likes_retweets_plot()
	wc = su.wc_plot()

	if request.method == 'POST':
		with open(filename) as file:
			response = HttpResponse(file, content_type='text/csv')
			response['Content-Disposition'] = 'attachment; filename={}'.format(filename)
			return response

	args = {'user': url.capitalize(), 'post': filename,
		    'likes_mean': res[0], 'likes_std': res[1], 'likes_min': res[2], 'likes_max': res[3],
		    're_mean': res[4], 're_std': res[5], 're_min': res[6], 're_max': res[7],
			'top': top, 'lr': lr, 'wc': wc,
			'html_l': html_l, 'html_re': html_re}
	return render(request, 'interface/dash.html', args)


def bot(request):
	return render(request, 'interface/bot.html')


def bot_old(request):
	message = ''
	submitted = False
	url = request.build_absolute_uri().split('/old/')[1]

	if request.method == 'POST':
		client = APIClient()
		res = client.get('/model/{}/'.format(url), {'sentence': url.capitalize()}, format='json')

		message = res.content.decode("utf-8")
		submitted = True

	return render(request, 'interface/bot_old.html', {'url': url.capitalize(), 'message': message, 'submitted': submitted})


def bot_new(request):
	return render(request, 'interface/bot_new.html')
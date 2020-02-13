import os
import json
import time
import logging
import requests
import cloudscraper
from bs4 import BeautifulSoup
from datetime import datetime
from requests.exceptions import *

from .constants import *
from .exceptions import *

class Data:
	def __init__(self):
		self.start = datetime.now()
		self.last_bump = None
		self.last_request = None
		self.totals = {
			'posts': 0,
			'bumps': 0
		}

	def as_dict(self):
		return {
			'start': self.start,
			'last_bump': self.last_bump,
			'last_request': self.last_request,
			'totals': self.totals
		}

class Bumper:
	def __init__(self, username, password, twofac=None, cookie=None):
		"""
		The bumper object itself. If username/password are left empty
		but a cookie is provided, it will log in with that instead.

		Within this __init__ function the logger and cloudflare scraper
		will be started, and the program will check if the login details
		are correct or not.

		:param username: OGU account name
		:param password: OGU password
		:param twofac: current 2FA code
		:param cookie: `ogusersbbuser` cookie

		:return: none
		"""
		self.logger = logging.getLogger(__name__)

		self.data = Data()
		self.__config = None

		self.session = cloudscraper.CloudScraper(
			browser={
				'browser': 'chrome',
				'desktop': True
			}
		)

		if cookie:
			self.session.cookies['ogusersmybbuser'] = cookie
			if not self.logged_in:
				raise InvalidUser('Incorrect login details')
		else:
			if not self.login(username, password, twofac=twofac):
				raise InvalidUser('Incorrect login details')

		self.logger.info('Initialized the bumper successfully')

	def _validate_config(cls, config):
		"""
		Validate a config dictionary/JSON string, if it is not valid
		then an error will be raised

		:param config: the data to use/validate

		:return: the validated config
		"""
		if not isinstance(config, dict):
			try:
				config = json.loads(config)
			except ValueError:
				raise InvalidJSON("Configuration is not valid JSON")

		for item in REQUIRED_VALUES:
			if not config.get(item):
				self.logger.warning(f"Missing `{item}` in the config file, using default value")
				config[item] = DEFAULT_CONFIG[item]
			
			try:
				x = float(config[item])
			except ValueError:
				raise InvalidType(item + " is not of the correct type (should be integer/float)")

		if len(config.get('threads', [])) == 0:
			raise MissingData("No threads provided")

		for index, thread in enumerate(config['threads'], start=1):
			for item in REQUIRED_VALUES_THREAD:
				if not thread.get(item):
					raise MissingData("Missing data in thread " + str(index))

		return config

	@property
	def config(self):
		"""
		Get the current config

		:return: dict
		"""
		return self.__config

	@config.setter
	def config(self, data):
		"""
		Load a new config and validate it

		:param data: dictionary/JSON string to load data from

		:return: none
		"""
		self.__config = self._validate_config(data)

	def save_config(self, file, **kwargs):
		"""
		Save a config to a file

		:param file: the file object to write to
		:kwargs: any other data to load to the JSON dump function

		:return: none
		"""
		json.dump(self.__config, file, **kwargs)

	def _request(self, method, url, **kwargs):
		"""
		Make a request to a specified resource. If the request fails, it retries continually,
		waiting for longer amounts of time after each failure, stopping at 256 seconds.

		:param method: the method to request the resource with (eg GET/POST)
		:param url: the resource to request (eg 'member.php')
		:param **kwargs anything else to pass to the request

		:return: response object
		"""
		wait = 4
		while 1:
			try:
				if method == 'GET':
					resp = self.session.get('https://ogusers.com/' + url, **kwargs)
				elif method == 'POST':
					resp = self.session.post('https://ogusers.com/' + url, **kwargs)

				self.data.last_request = resp
				break
			except (HTTPError, Timeout):
				log.error('The request failed. Waiting ' + str(wait) + ' seconds before trying again')
				time.sleep(wait)
				wait = wait * 2 if wait <= 256 else wait
				continue

		return resp

	def _get_input(self, data, target):
		"""
		Get the value of a specific input

		:param data: BeautifulSoup object to search through
		:param target: the value of the 'name' tag to search for

		:return: string
		"""
		return data.find('input', {'name': target}).get('value')

	@property
	def logged_in(self):
		"""
		Check whether or not the user is logged in

		:return: bool
		"""
		resp = self._request('GET', 'member.php', params={
			'action': 'profile'
		})
		soup = BeautifulSoup(resp.text, 'html.parser')

		return resp.status_code == 200

	@property
	def current_user(self):
		"""
		Get data on the current user

		:return: dict
		"""
		resp = self._request('GET', 'member.php', params={
			'action': 'profile'
		})
		soup = BeautifulSoup(resp.text, 'html.parser')

		return {
			'name': soup.find('title').get_text().split(' |')[0],
			'uid': soup.find('a', {'id': 'profileLink'}).get_text(),
			'avatar': soup.find('div', {'class': 'profile_avatar'}).find('img').get('src'),
			'credits': soup.find_all('a', {'href': 'https://ogusers.com/credits.php'})[1].get_text(),
			'reputation': soup.find('strong', {'class': 'reputation_positive'}).get_text(),
			'vouches': soup.find('strong', {'class': 'reputation_neutral'}).get_text()
		}

	def resolve_thread(self, thread):
		"""
		Attempt to find a thread's ID from a URL or partial URL

		:param thread: a string with a possible thread

		:return: string
		"""
		resp = self._request('GET', thread.split('ogusers.com/')[-1])
		soup = BeautifulSoup(resp.text, 'html.parser')

		reply_button = soup.find('div', {'class': 'newrepliesbutton'})

		if not reply_button:
			raise InvalidThread('Invalid thread: ' + thread)
		
		return reply_button.find('a').get('href').split('?tid=')[-1]

	def login(self, username, password, twofac=None):
		"""
		Log in using the data provided

		:param username: the user's account name
		:param password: the user's password
		:param twofac (optional): current 2FA code for the account
		
		:return: bool
		""" 
		resp = self._request('GET', 'member.php', params={'action': 'login'})
		soup = BeautifulSoup(resp.text, 'html.parser')

		resp = self._request('POST', 'member.php', data={
			'action': 'do_login',
			'my_post_key': self._get_input(soup, 'my_post_key'),
			'username': username,
			'password': password,
			'2facode': twofac
		})

		self.logger.info('Logged in')
		
		return 'index.php' in resp.url

	def logout(self):
		"""
		Log out of the website

		:return: none
		"""
		resp = self._request('GET', 'member.php', params={
			'action': 'logout'
		})
		soup = BeautifulSoup(resp.text)

		self._request('POST', 'member.php', params={
			'action': 'logout',
			'logoutkey': resp.text.split('logoutkey=')[-1].split('"')[0]
		})

		self.logger.info('Logged out')

	def reply(self, thread, message):
		"""
		Make a post to a thread

		:param thread: the thread to post to. if it is not valid,
						try to resolve it using the `resolve_thread`
						function
		:param message: the message to post on the thread

		:return: none
		"""
		if not thread.isdigit():
			thread = self.resolve_thread(thread)

		resp = self._request('GET', 'newreply.php', params={'tid': thread})
		soup = BeautifulSoup(resp.text, 'html.parser')

		self._request('POST', 'newreply.php', data={
			'my_post_key': self._get_input(soup, 'my_post_key'),
			'subject': self._get_input(soup, 'subject'),
			'action': 'do_newreply',
			'posthash': self._get_input(soup, 'posthash'),
			'quoted_ids': 'Array',
			'tid': thread,
			'message': message,
			'postoptions[signature]': 1
		})

		self.logger.info('Made a post on ' + thread)

	def alerts(self):
		"""
		Get a list of alerts

		:return: dict
		"""
		resp = self._request('GET', 'alerts.php')
		soup = BeautifulSoup(resp.text, 'html.parser')

		table = soup.find('tbody', {'id': 'latestAlertsListing'})
		alerts = []

		for alert in table.find_all('tr'):
			data = alert.find_all('td')
			info = [x.replace('<br/>', ' ') for x in data[1].find('a').get_text(strip=True, separator='<br/>').rsplit('<br/>', 1)]

			alerts.append({
				'id': alert.get('id').split('row_')[-1],
				'user': data[0].find('a').get('href'),
				'info': info[0],
				'time': info[1]
			})

		return alerts

	def messages(self):
		"""
		Get a list of messages

		:return: dict
		"""
		resp = self._request('GET', 'private.php')
		soup = BeautifulSoup(resp.text, 'html.parser')

		table = soup.find('table')
		messages = []

		for message in table.find_all('tr')[2:-1]:
			body = message.find_all('td', {'class': 'trow1_pm'})[1].find('a')

			messages.append({
				'id': body.get('href').split('&pmid=')[-1],
				'user': message.find_all('td', {'class': 'trow2_pm'})[1].get_text(),
				'title': body.get_text(),
				'time': message.find('td', {'class': 'time_sent'}).find('span').get_text(),
				'unread': True if 'new_pm' in body.get('class') else False
			})

		return messages

	def run(self):
		"""
		Automatically post to the threads specified in the given
		config at a specific interval

		:return: none
		"""
		self.logger.info('Started running the bumper')
		
		while 1:
			for thread in self.__config['threads']:
				if thread.get('message'):
					message = thread['message']
				elif self.__config.get('default_message'):
					message = self.__config['default_message']
				else:
					message = 'This thread is being auto bumped'

				self.post(thread['id'], message)

				self.logger.info('Bumped ' + (thread['name'] if thread.get('name') is not None else thread['id']))

				self.data.totals['posts'] += 1
				self.data.last_bump = str(datetime.now())

				if thread == self.__config['threads'][-1]:
					break

				time.sleep(self.__config['post_delay'])

			self.data.totals['bumps'] += 1

			self.logger.info('Bumped all threads successfully')
			
			time.sleep(self.__config['bump_delay'] * 60)
import os
import json
import time
import logging
import requests
import cloudscraper
from bs4 import BeautifulSoup
from datetime import datetime
from requests.exceptions import *

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
		self.data = Data()
		self.logger = logging.getLogger(__name__)

		self.logger.debug('Initializing the CloudScraper session')
		self.session = cloudscraper.CloudScraper(browser={'browser': 'chrome','desktop': True})

		if cookie:
			self.logger.debug('Loading session from cookie')
			self.session.cookies['ogusersmybbuser'] = cookie

			if not self.logged_in:
				raise InvalidUser('Incorrect login details')
		else:
			self.logger.debug('Loading session from username/password')
			if not self.login(username, password, twofac=twofac):
				raise InvalidUser('Incorrect login details')

		self.logger.debug('Getting information on the current user')
		self.user = self.current_user()

	@property
	def logged_in(self):
		resp = self._request('GET', 'member.php', params={'action': 'profile'})
		soup = BeautifulSoup(resp.text, 'html.parser')

		return resp.status_code == 200

	def current_user(self):
		resp = self._request('GET', 'member.php', params={'action': 'profile'})
		soup = BeautifulSoup(resp.text, 'html.parser')

		return {
			'name': soup.find('title').get_text().split(' |')[0],
			'uid': soup.find('a', {'id': 'profileLink'}).get_text(),
			'avatar': soup.find('div', {'class': 'profile_avatar'}).find('img').get('src'),
			'credits': soup.find_all('a', {'href': 'https://ogusers.com/credits.php'})[1].get_text(),
			'reputation': soup.find('strong', {'class': 'reputation_positive'}).get_text(),
			'vouches': soup.find('strong', {'class': 'reputation_neutral'}).get_text()
		}

	def _request(self, method, url, **kwargs):
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
		return data.find('input', {'name': target}).get('value')

	def _resolve_thread(self, thread):
		self.logger.debug('Attempting to resolve thread URL "' + thread + '"')
		resp = self._request('GET', thread.split('ogusers.com/')[-1])
		soup = BeautifulSoup(resp.text, 'html.parser')

		reply_button = soup.find('div', {'class': 'newrepliesbutton'})

		if reply_button:
			tid = reply_button.find('a').get('href').split('?tid=')[-1]
			self.logger.debug('Thread exists: ' + tid)
			return tid
		else:
			raise InvalidThread('Invalid thread: ' + thread)

	def load_config(self, file):
		if not os.path.isfile(file):
			raise IOError('Invalid config file name')
			
		with open(file, 'r', encoding='utf-8') as file:
			self.config = json.loads(file.read())

	def save_config(self, file):
		with open(file, 'w+', encoding='utf-8') as file:
			json.dump(self.config, file, ensure_ascii=False, indent=4)

	def login(self, username, password, twofac=None):
		self.logger.debug('Attempting to log in as ' + username)
		resp = self._request('GET', 'member.php', params={'action': 'login'})
		soup = BeautifulSoup(resp.text, 'html.parser')

		self.logger.debug('Sending the login request')
		data = {
			'action': 'do_login',
			'my_post_key': self._get_input(soup, 'my_post_key'),
			'username': username,
			'password': password,
			'2facode': twofac
		}
		resp = self._request('POST', 'member.php', data=data)
		
		return 'https://ogusers.com/index.php' in resp.url

	def post(self, thread, message):
		if not thread.isdigit():
			thread = self._resolve_thread(thread)

		self.logger.debug('Getting info on thread ' + thread)
		resp = self._request('GET', 'newreply.php', params={'tid': thread})
		soup = BeautifulSoup(resp.text, 'html.parser')

		self.logger.debug('Posting reply to ' + thread)
		data = {
			'my_post_key': self._get_input(soup, 'my_post_key'),
			'subject': self._get_input(soup, 'subject'),
			'action': 'do_newreply',
			'posthash': self._get_input(soup, 'posthash'),
			'quoted_ids': 'Array',
			'tid': thread,
			'message': message,
			'postoptions[signature]': 1
		}
		return self._request('POST', 'newreply.php', data=data)

	def alerts(self):
		self.logger.debug('Getting alert page')
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

		self.logger.debug('Got ' + str(len(alerts)) + ' alerts')
		return alerts

	def messages(self):
		self.logger.debug('Getting messages page')
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
				'unread': True if 'new_pm' in body.get('class') else False
			})

		self.logger.debug('Got ' + str(len(messages)) + ' alerts')
		return messages

	def loop(self):
		while 1:
			for thread in self.config['threads']:
				if thread.get('message'):
					message = thread['message']
				elif self.config.get('default_message'):
					message = self.config['default_message']
				else:
					message = 'This thread is being auto bumped'

				self.post(thread['id'], message)

				self.logger.info('Bumped thread ' + thread['id'])
				self.data.totals['posts'] += 1
				self.data.last_bump = str(datetime.now())

				if thread == self.config['threads'][-1]:
					break

				time.sleep(self.config['post_delay'])

			self.logger.info('Finished bumping, waiting ' + str(self.config['bump_delay']) + ' minutes')
			self.data.totals['bumps'] += 1

			time.sleep(self.config['bump_delay'] * 60)

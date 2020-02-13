import os
import dill
import json
import time
import logging
import argparse
import threading
import pkg_resources
from flask import Flask
from waitress import serve
from datetime import datetime

from .bumper import Bumper
from .server.app import create_app

logger = logging.getLogger(__name__)
logging.basicConfig(
	level=logging.INFO,
	format="[%(asctime)s] [%(name)s] %(levelname)s: %(message)s",
	datefmt="%Y-%m-%d %H:%M:%S"
)

def setup():
	parser = argparse.ArgumentParser(description='Autobumper for OGUsers')

	parser.add_argument('-u', '--username', type=str, help='Username for the website')
	parser.add_argument('-p', '--password', type=str, help='Password for the website')
	parser.add_argument('-c', '--cookie', type=str, help='The `ogusersbbuser` cookie, which can be used as a login')

	parser.add_argument('-tfa', type=int, help='Current 2FA code')
	parser.add_argument('-config', type=str, default='config.json', help='Name of the config file')
	parser.add_argument('--server', action='store_true', default=False, help='Serve a webserver alongside the bumper')
	parser.add_argument('--verbose', action='store_true', default=False, help='Print more information for debug purposes')
	parser.add_argument('--version', action='store_true', default=False, help='Display the current version')
	
	args, unknown = parser.parse_known_args()

	if args.version:
		version = pkg_resources.require('bumper')[0].version
		print(version)
		quit()

	if args.verbose:
		logger.setLevel(logging.DEBUG)

	if (not args.username or not args.password) and not args.cookie:
		if os.path.isfile('session.dump'):
			with open('session.dump', 'rb') as file:
				bumper = dill.load(file)

			if not bumper.logged_in:
				raise Exception('Invalid session file, please delete it and log in again')
		else:
			raise Exception('Login information was not given')
	else:
		if not args.cookie:
			bumper = Bumper(args.username, args.password, twofac=args.tfa)
		else:
			bumper = Bumper(None, None, cookie=args.cookie)

		with open('session.dump', 'wb') as file:
			dill.dump(bumper, file)

	if not os.path.isfile(args.config):
		raise Exception('Config file does not exist')

	with open(args.config, 'r', encoding='utf-8') as file:
		bumper.config = file.read()

	app = None
	if args.server:
		app = create_app()
		app.config['STATE'] = bumper

	return bumper, app, args

def main():
	bumper, app, args = setup()
	if args.server:
		def run_job():
			app.config['STATE'].run()

		thread = threading.Thread(target=run_job)
		thread.daemon = True
		thread.start()
		
		serve(
			app,
			host=bumper.config.get('host', '127.0.0.1'),
			port=int(bumper.config.get('port', 80))
		)
	else:
		bumper.run()

if __name__ == '__main__':
	main()
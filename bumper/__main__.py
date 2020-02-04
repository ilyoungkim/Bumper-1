import os
import json
import time
import logging
import argparse
import threading
from flask import Flask
from waitress import serve
from datetime import datetime

from .app import create_app
from .bumper import Bumper

logger = logging.getLogger(__name__)
logging.basicConfig(
	level=logging.INFO,
	format="[%(asctime)s] %(levelname)s: %(message)s",
	datefmt="%H:%M:%S"
)

def setup():
	parser = argparse.ArgumentParser(description='Autobumper for OGUsers')

	# Necessary for login
	parser.add_argument('-u', '--username', type=str, help='Username for the website')
	parser.add_argument('-p', '--password', type=str, help='Password for the website')
	parser.add_argument('-c', '--cookie', type=str, help='The `ogusersbbuser` cookie, which can be used as a login')

	# Optional
	parser.add_argument('-tfa', type=int, help='Current 2FA code')
	parser.add_argument('-config', type=str, default='config.json', help='Name of the config file')
	parser.add_argument('--server', action='store_true', default=False, help='Access data/config for the bumper from a website')
	
	args, unknown = parser.parse_known_args()

	if (not args.username or not args.password) and not args.cookie:
		raise Exception('Username or password was not provided')

	if not args.cookie:
		bumper = Bumper(args.username, args.password, twofac=args.tfa)
	else:
		bumper = Bumper(None, None, cookie=args.cookie)

	logger.info('Initialized bumper')

	if not os.path.isfile(args.config):
		raise Exception('Config file does not exist')

	logger.info('Loading user config from ' + args.config)
	bumper.load_config(args.config)

	if args.server:
		app = create_app()
		app.config['STATE'] = bumper

	logger.info('Finished setup')
	return bumper, app, args

def main():
	bumper, app, args = setup()
	if args.server:
		def run_job():
			app.logger.info('Starting the bumper loop')
			app.config['STATE'].loop()

		thread = threading.Thread(target=run_job)
		thread.daemon = True
		thread.start()
		
		serve(app, host='0.0.0.0', port=80)
	else:
		bumper.loop()

if __name__ == '__main__':
	main()
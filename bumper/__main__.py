import os
import sys
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

def parse_args():
	parser = argparse.ArgumentParser(description="Autobumper for OGUsers")

	parser.add_argument("-u", "--username", type=str, help="Username for the website")
	parser.add_argument("-p", "--password", type=str, help="Password for the website")
	parser.add_argument("-c", "--cookie", type=str, help="The `ogusersbbuser` cookie, which can be used as a login")
	parser.add_argument("-tfa", type=int, help="Current 2FA code")

	parser.add_argument("-config", type=str, default="config.json", help="Name of the config file")
	parser.add_argument("--server", action="store_true", default=False, help="Serve a webserver alongside the bumper")
	parser.add_argument("--verbose", action="store_true", default=False, help="Print more information for debug purposes")
	parser.add_argument("--version", action="store_true", default=False, help="Display the current version")
	
	args, unknown = parser.parse_known_args()

	return args

def setup(args):
	if args.version:
		version = pkg_resources.require("bumper")[0].version
		print(version)
		if len(sys.argv) == 2:
			quit()

	if (not args.username or not args.password) and not args.cookie:
		raise Exception("Login information was not given")

	if not os.path.isfile(args.config):
		raise Exception("Config file does not exist")

	with open(args.config, 'r', encoding="utf-8") as file:
		config = file.read()

	logging_config = {
		"format": "[%(asctime)s] [%(name)s] %(levelname)s: %(message)s",
		"datefmt": "%Y-%m-%d %H:%M:%S"
	}
	
	if args.verbose:
		logging_config["level"] = logging.DEBUG
	else:
		logging_config["level"] = logging.INFO

	logging.basicConfig(**logging_config)

	bumper = Bumper(
		args.username,
		args.password,
		twofac=args.tfa,
		cookie=args.cookie,
		config=config
	)

	app = None
	if args.server:
		app = create_app()
		app.config["STATE"] = bumper

	return bumper, app

def main():
	args = parse_args()
	bumper, app = setup(args)
	if args.server:
		def run_job():
			app.config["STATE"].run()

		thread = threading.Thread(target=run_job)
		thread.daemon = True
		thread.start()
		
		serve(app, host=bumper.config.get("host", "127.0.0.1"), port=int(bumper.config.get("port", 80)))
	else:
		bumper.run()

if __name__ == "__main__":
	main()
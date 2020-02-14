from io import open
from os import path
from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), 'r', encoding="utf-8") as f:
	long_description = f.read()

setup(
	name="bumper",
	version="1.1.2",
	description="Automatic poster for OGUsers",
	author="Shoot",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/Shoot/Bumper",
	packages=find_packages(),
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		"dill==0.3.1.1",
		"Flask==1.1.1",
		"Flask-API==2.0",
		"Flask-PyMongo==2.3.0",
		"Flask-Session==0.3.1",
		"beautifulsoup4==4.8.0",
		"cloudscraper==1.2.21",
		"flask-bcrypt==0.7.1",
		"flask-wtf==0.14.2",
		"requests==2.22.0",
		"setuptools==40.8.0",
		"waitress>=1.4.3",
		"werkzeug==0.16.0",
		"wtforms==2.2.1"
	],
	entry_points={
		"console_scripts": [
			"bumper = bumper.__main__:main"
		]
	}
)
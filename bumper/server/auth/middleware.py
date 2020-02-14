from functools import wraps
from flask import abort, redirect, request, session, url_for

from ..extensions import mongo

def login_required(f):
	@wraps(f)
	def wrapper(*args, **kwargs):
		user_id = session.get("uid")
		if user_id:
			user = mongo.db.admin.find_one({"_id": user_id})
			if user:
				return f(user, *args, **kwargs)
		return redirect(url_for("auth.login"))
	return wrapper
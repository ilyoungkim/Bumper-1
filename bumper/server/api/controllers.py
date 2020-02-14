from flask import ( Blueprint, session, render_template,
					url_for, redirect, current_app,
					request, jsonify )
from flask_api import status

from ..extensions import mongo, bcrypt
from ..auth.middleware import login_required

api = Blueprint("api", __name__, url_prefix="/api")

def api_success(message):
	return jsonify({
		"success": True,
		"message": message
	}), status.HTTP_200_OK

def api_error(message):
	return jsonify({
		"success": False,
		"error": message
	}), status.HTTP_400_BAD_REQUEST

@api.route("/config", methods=["POST"])
@login_required
def config(user):
	state = current_app.config["STATE"]
	form = request.form

	if form.get("bump_delay"):
		try:
			state.config["bump_delay"] = float(form["bump_delay"])
		except ValueError:
			return api_error("Invalid data type given")

	if form.get("post_delay"):
		try:
			state.config["post_delay"] = float(form["post_delay"])
		except ValueError:
			return api_error("Invalid data type given")

	if form.get("default_message"):
		if len(form["default_message"]) < 8:
			return api_error("Default message is too short")

		state.config["default_message"] = form["default_message"]

	return api_success("Updated configuration")

@api.route("/thread", methods=["POST"])
@login_required
def thread(user):
	state = current_app.config["STATE"]
	form = request.form

	if not "method" in form:
		return api_error("No method given")
	if not "thread" in form:
		return api_error("No thread given")

	if form["method"] == "edit":
		for thread in state.config["threads"]:
			if thread["id"] == form["thread"]:
				thread["message"] = form.get("message")
				thread["name"] = form.get("name")

			state.save_config("config.json")
			return api_success("Edited thread successfully")

		return api_error("Thread does not exist")
	elif form["method"] == "create":
		state.config["threads"].append({
			"id": form["thread"],
			"message": form.get("message"),
			"name": form.get("name")
		})

		state.save_config("config.json")
		return api_success("Successfully added thread")
	elif form["method"] == "delete":
		for thread in state.config["threads"]:
			if thread.get("id") == form["thread"]:
				state.config["threads"].remove(thread)
				return api_success("Successfully deleted the thread")
		return api_error("Thread does not exist")
	else:
		return api_error("Invalid method, please use one of the following: create, edit, delete")

@api.route("/user", methods=["POST"])
@login_required
def user(user):
	form = request.form

	if not form.get("old-password"):
		return api_error("No password provided")

	search = mongo.db.admin.find_one({"_id": session["uid"]})

	if not bcrypt.check_password_hash(search["password"], form["old-password"]):
		return api_error("Incorrect current password")

	data = {}
	if "username" in form:
		data["username"] = form["username"]
	if "new-password" in form:
		data["password"] = bcrypt.generate_password_hash(form["new-password"])
	
	mongo.db.admin.update(search, {"$set": data})

	return api_success("Updated info")

@api.route("/last_request", methods=["GET"])
@login_required
def last_request(user):
	state = current_app.config["STATE"]

	if state.data.last_request:
		return state.data.last_request.text

	return api_error("No request has been made")
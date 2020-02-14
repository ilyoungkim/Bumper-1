from datetime import datetime
from flask import Blueprint, session, redirect, render_template, url_for, current_app

from ..extensions import mongo
from ..auth.middleware import login_required

admin = Blueprint("admin", __name__, url_prefix="/admin")

@admin.route("/", methods=["GET"])
@login_required
def index(user):
	state = current_app.config["STATE"]
	data = state.data
	return render_template(
		"admin/home.html",
		user=state.current_user,
		config=state.config,
		data=data.as_dict(),
		elapsed=datetime.now() - data.start
	)
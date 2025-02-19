# Gevent needed for sockets
from gevent import monkey
monkey.patch_all()

# Imports
import os
import json
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

from analysis_scripts import analysis

# Configure app
socketio = SocketIO()
app = Flask(__name__)
app.config.from_object(os.environ["APP_SETTINGS"])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# DB
db = SQLAlchemy(app)

# Import + Register Blueprints
from app.accounts import accounts as accounts
app.register_blueprint(accounts)
from app.irsystem import irsystem as irsystem
app.register_blueprint(irsystem)

# Initialize app w/SocketIO
socketio.init_app(app)

# HTTP error handling
@app.errorhandler(404)
def not_found(error):
  return render_template("404.html"), 404


@app.route("/pdf", methods=["GET", "POST"])
def pdf():
  #pdf_file = request.get_json()
  #pdf = pdf_file["file"]
  pdf_file = request.files.get('file')
  pages = analysis.get_pages(pdf_file)
  raw_corpus = analysis.get_raw_corpus(pages)
  clean_corpus = analysis.get_clean_corpus(raw_corpus)
  lines_text = analysis.get_display_text(clean_corpus)
  image = analysis.make_wordcount_hist(clean_corpus)
  return json.dumps({
    "text": lines_text,
    "img": image
  })

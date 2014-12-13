# -*- coding: utf-8 -*-

import json
import time
from datetime import *
from flask import render_template

from server import app

@app.route('/foo')
def foo():
	return "bar"

@app.route('/')
def show_notifications():
	return render_template('main_stats.html')
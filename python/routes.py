# -*- coding: utf-8 -*-

import json
import time
from datetime import *
from flask import render_template
from unidecode import unidecode

import data.mongo_util
from data.mongo_util import *
from config import *

from server import app

interesting = ['Cod unic candidat', 'Specializare', 'Profil', 'Filiera',
				'NOTE_RECUN_EA',
				'NOTE_RECUN_EB',
				'NOTE_RECUN_EC',
				'NOTA_ED', 'Forma de invatamant']

def get_db():
	# g is provided by flask and is thread-safe!
	global g
	if not hasattr(g, 'mongo'):
		g.mongo = mongo_util.fetch_db(create_client(), BAC_MONGO_DB)

	return g.mongo

def prettify(row):
	clean = {}
	for key in row:
		if key in interesting:
			# use `unidecode(row[key])' if Python starts complaining about UTF
			clean[key] = row[key]
	return clean

def get_keys(doc):
	return [key for key in doc]

@app.route('/api/get_data')
def api_get_data():
	mongo_data = fetch_table(get_db(), BAC_MONGO_TABLE)
	data = [prettify(row) for row in mongo_data.find().limit(100)]
	return json.dumps(data)

@app.route('/api/get_data_size')
def api_get_data_size():
	mongo_data = fetch_table(get_db(), BAC_MONGO_TABLE)
	return json.dumps(mongo_data.size())

@app.route('/')
def index():
	mongo_data = fetch_table(get_db(), BAC_MONGO_TABLE)
	sample = [prettify(row) for row in mongo_data.find().limit(100)]
	header = get_keys(sample[0])

	return render_template('main_stats.html', data = mongo_data,
		header = header, sample = sample)
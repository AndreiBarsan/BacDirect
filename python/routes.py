# -*- coding: utf-8 -*-

import json
import time
from datetime import *
from flask import render_template, g
from ..unidecode import unidecode

from data import mongo_util
from data.mongo_util import *
from config import *

from server import app

interesting = ['id', 'specializare', 'profil', 'filiera',
				'noteRecunEa', 'noteRecunEb', 'noteRecunEc', 'noteRecunEd',
				'formaInvatamant', 'medie']

interesting_display = {
	'id': 'ID',
	'specializare': 'Specializare',
	'profil': 'Profil',
	'filiera': 'Filiera',
	'noteRecunEa': 'Note Recun? EA',
	'noteRecunEB': 'Note Recun? EB',
	'noteRecunEC': 'Note Recun? EC',
	'noteRecunEC': 'Note Recun? EC',
}

def get_db():
	# g is provided by flask and is thread-safe!
	global g
	if not hasattr(g, 'mongo'):
		g.mongo = mongo_util.fetch_db(create_client(), BAC_MONGO_DB)

	return g.mongo

def filter_interesting(row):
	clean = {}
	for key in interesting:
		# use `unidecode(row[key])' if Python starts complaining about UTF
		clean[key] = row[key]
		
	return clean

def get_keys(doc):
	return [key for key in doc]

@app.route('/api/get_data')
def api_get_data():
	mongo_data = fetch_table(get_db(), BAC_MONGO_TABLE)
	data = [filter_interesting(row) for row in mongo_data.find()]
	return json.dumps(data)

@app.route('/api/get_data_size')
def api_get_data_size():
	mongo_data = fetch_table(get_db(), BAC_MONGO_TABLE)
	return json.dumps({'size': mongo_data.count()})

@app.route('/')
def index():
	mongo_data = fetch_table(get_db(), BAC_MONGO_TABLE)
	sample = [filter_interesting(row) for row in mongo_data.find().limit(1000)]
	header = get_keys(sample[0])

	return render_template('main_stats.html', data = mongo_data,
		header = header, sample = sample)
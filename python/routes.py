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

def prettify(row):
	clean = {}
	for key in row:
		if key in interesting:
			clean[key] = unidecode(row[key])
			# clean[key] = unicode(row[key]).encode(BAC_DATASET_ENCODING)
	return clean

def get_keys(doc):
	return [key for key in doc]

@app.route('/')
def show_notifications():
	mongo_data = fetch_table(fetch_db(create_client(), BAC_MONGO_DB), BAC_MONGO_TABLE)
	sample = [prettify(row) for row in mongo_data.find().limit(100)]
	header = get_keys(sample[0])

	return json.dumps(sample)
	#return render_template('main_stats.html', data = mongo_data,
#		header = header, sample = sample)
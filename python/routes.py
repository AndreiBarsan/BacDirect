# -*- coding: utf-8 -*-

import json
import time
from datetime import *
from flask import render_template, g
from unidecode import unidecode

from bson.objectid import ObjectId
from bson import Code
from bson.son import SON

from data import mongo_util
from data.mongo_util import *
from config import *

from server import app

interesting = ['id', 'specializare', 'profil', 'filiera',
				'noteRecunEa', 'noteRecunEb', 'noteRecunEc', 'noteRecunEd',
				'formaInvatamant', 'medie', 'codUnitate', 'school.judet', 'status']

interesting_display = {
	'id': 'ID',
	'specializare': 'Specializare',
	'profil': 'Profil',
	'filiera': 'Filiera',
	'noteRecunEa': 'Note Recun? EA',
	'noteRecunEb': 'Note Recun? EB',
	'noteRecunEc': 'Note Recun? EC',
	'noteRecunEd': 'Note Recun? ED',
	'formaInvatamant': 'Forma Invatamant',
	'medie': 'Medie',
	'codUnitate': 'Cod Unitate Scolara',
	'judet': 'Judet',
	'status': 'Statut'
}

# Needed for jsonifying mongo objectids.  They're not usually needed, but it helps
# to be able to dump them from time to time.
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

def prettify_header(header):
	return [interesting_display[key] for key in header]

def get_db():
	# g is provided by flask and is thread-safe!
	global g
	if not hasattr(g, 'mongo'):
		g.mongo = mongo_util.fetch_db(create_client(), BAC_MONGO_DB)

	return g.mongo

def nestedGrab(obj, bitsLeft):
	if(len(bitsLeft) == 1):
		return obj[bitsLeft[0]]
	else:
		return nestedGrab(obj[bitsLeft[0]], bitsLeft[1:])


def filter_interesting(row):
	clean = {}
	for key in interesting:
		# Hack.
		if key.find(".") > 0:
			bits = key.split(".")
			clean[key] = nestedGrab(row, bits)
		# use `unidecode(row[key])' if Python starts complaining about UTF
		else:
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

@app.route('/api/get_data_by_county')
def api_get_data_by_county():
	bac_table = fetch_table(get_db(), BAC_MONGO_TABLE)
	grp = bac_table.aggregate([
		{
			"$match" : {
				"medie": { "$gt": 0 }
			}
		},
		{
			"$group" : {
				"_id": "$judet",
				"medie" : { "$avg" : "$medie" },
			}
		},
	])

	return json.dumps(grp)
	#return json.dumps({'message': 'Not implemented. Mismatch between datasets.'})

# TODO(andrei) Idee: ce procent din note au fost contestate
# TODO(andrei) Idee: la cât % a contat contestația (pe materii).
# TODO(andrei) Idee: la cât % a scăzut nota contestația (pe materii).

def validContestedSubject(subject):
	validContestedSubjects = {
		'notaContestatieEa': 'Contestatie limba si literatura romana',
		'notaContestatieEb': 'Contestatie limba si literatura materna',
		'notaContestatieEc': 'Contestatie proba profil #1 (ex. Mate)',
		'notaContestatieEd': 'Contestatie proba profil #2 (ex. Fizica)',
	}
	return subject in validContestedSubjects

def validSubject(subject):
	validSubjects = {
		'notaEa': 'Limba si literatura romana',
		'notaEb': 'Limba si literatura materna',
		'notaEc': 'Proba profil #1 (ex. Mate)',
		'notaEd': 'Proba profil #2 (ex. Fizica)',
	}
	return subject in validSubjects

def json_error(message):
	return json.dumps({ 'error': message })

def contestify(subject):
	index = len("nota")
	return subject[:index] + "Contestatie" + subject[index:]

# Returns the number of students who took a given exam. Also works with finding 
# out how many students contested the result of a given exam (for this use
# `contestify(exam)' instead of `exam').
def compute_student_count(subject):
	print "Computing grade count: ", subject, "\n\n\n"

	res = fetch_table(get_db(), BAC_MONGO_TABLE).aggregate([
		# We only want people who actually took the exam.
		{
			"$match": {
				subject: { '$gt': 1 }
			}
		},
		{
			"$group": {
	   			"_id": None, 
	   			"count": { "$sum": 1 }
       		}
		}
	])['result']

	if len(res) == 0:
		return 0
	else:
		return res[0]['count']

# Returns the number of students who took the given exam.
@app.route('/api/count_took_subject/<string:subject>', methods = ['GET'])
def api_count_took_subject(subject):
	if not validSubject(subject):
		return json_error('Invalid subject name.')

	return json.dumps(compute_student_count(subject))

# Returns the number of students who took the given exam and contested the
# result.
@app.route('/api/count_contested_subject/<string:subject>', methods = ['GET'])
def api_count_contested_subject(subject):
	if not validSubject(subject):
		return json_error('Invalid subject name.')

	return json.dumps(compute_student_count(contestify(subject)))

# Returns the percentage of the students who took the given exam who contested
# their grade.
@app.route('/api/percent_contested_by_subject/<string:subject>', methods = ['GET'])
def api_percent_contested_by_subject(subject):
	if not validSubject(subject):
		return json_error('Invalid subject name.')

	# Number of people who took the exam
	resTotal = compute_student_count(subject)

	# Number of people who contested the result
	resContested = compute_student_count(constestify(subject))

	percentContested =  resContested * 1.0 / resTotal * 100.0 
	return json.dumps({ 'percentContested': percentContested })

# Returns how many students increased/lowered/didn't change their grade by
# contesting the exam's result.
def api_test_contested_grade_effect(subject, op):
	contestedSubject = contestify(subject)
	res = fetch_table(get_db(), BAC_MONGO_TABLE).aggregate([
		{
			"$match": {
					# Match students who contested their exam result for `subject'.
					contestedSubject: { '$gt': 1 }
			}
		},
		# And who got a bigger grade as a result of that.
		# This happens in two stages because Mongo.
		{
			"$project": {
				contestedSubject: 1,
				'eq': { "$cond": 
					[ { op: [ '$' + contestedSubject, '$' + subject ] }, 1, 0 ]
				}
			}
		},
		{
			"$match": {
				'eq': 1
			}
		},
		{
			"$group": {
	   			"_id": None, 
	   			"count": { "$sum": 1 }
       		}
		}
		])['result']

	return 0 if len(res) == 0 else res[0]['count']


# Returns the number of students who increased their final grade by contesting
# the exam results.
@app.route('/api/increased_grade_by_contesting/<string:subject>', methods = ['GET'])
def api_increased_grade_by_contesting(subject):
	if not validSubject(subject):
		return json_error('Invalid subject name.')

	return json.dumps(api_test_contested_grade_effect(subject, '$gt'))


# Returns the number of students who lowered their final grade by contesting
# the exam results.
@app.route('/api/decreased_grade_by_contesting/<string:subject>', methods = ['GET'])
def api_decreased_grade_by_contesting(subject):
	if not validSubject(subject):
		return json_error('Invalid subject name.')

	return json.dumps(api_test_contested_grade_effect(subject, '$lt'))

# Returns the number of students for whom contesting the exam results had no
# impact on their final grade.
@app.route('/api/maintained_grade_by_contesting/<string:subject>', methods = ['GET'])
def api_maintained_grade_by_contesting(subject):
	if not validSubject(subject):
		return json_error('Invalid subject name.')

	return json.dumps(api_test_contested_grade_effect(subject, '$eq'))

@app.route('/api/histogram_by_subject/<string:subject>', methods = ['GET'])
@app.route('/api/histogram_by_subject/<string:subject>/<float:binSize>', methods = ['GET'])
def api_histogram_by_subject(subject, binSize = 0.1):
	if not validSubject(subject) and not validContestedSubject(subject):
		return json_error('Invalid subject name.')

	if binSize <= 0.0:
		return json_error('Invalid bin size.')

	tbl = fetch_table(get_db(), BAC_MONGO_TABLE)
	res = tbl.aggregate([
		{
			"$match": {
				subject: { '$gt': 1 }
			}
		},
		{
			"$project": {
        		"gradeLowerBound": {
        			"$subtract": ["$" + subject, { "$mod": [ "$" + subject, binSize]}]
        		}
        	}
        },
   		{
   			"$group": {
       			"_id": "$gradeLowerBound", 
       			"count": { "$sum": 1 }
	       	}
		},
		{
			"$sort": {
				"_id": 1
			}
		}
	])

	return JSONEncoder().encode(res['result'])


@app.route('/')
def index():
	mongo_data = fetch_table(get_db(), BAC_MONGO_TABLE)
	sample = [filter_interesting(row) for row in mongo_data.find().limit(1000)]
	header = get_keys(sample[0])
	pretty_header = prettify_header(header)

	return render_template('main_stats.html', data = mongo_data,
		keys = header, header = pretty_header, sample = sample)
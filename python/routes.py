# -*- coding: utf-8 -*-

# TODO(ioan) Remove all tab indents so that the codebase is consistent.
# TODO(ioan) Ensure everyone is using expandtab with 4-space tabs.

from datetime import *
import json
import time

from bson.objectid import ObjectId
from bson import Code
from bson.son import SON
from flask import render_template
from unidecode import unidecode

from config import *
from data import mongo_util
from data.mongo_util import *
from db.bac_stats import *
from server import app
from util import *

@app.route('/')
def index():
	mongo_data = fetch_table(get_db(), BAC_MONGO_TABLE)
	sample = [filter_interesting(row) for row in mongo_data.find().limit(1000)]
	header = get_keys(sample[0])
	pretty_header = prettify_header(header)

	return render_template('main_stats.html', data = mongo_data,
		keys = header, header = pretty_header, sample = sample)

@app.route('/api/get_data')
def api_get_data():
	mongo_data = fetch_table(get_db(), BAC_MONGO_TABLE)
	data = [filter_interesting(row) for row in mongo_data.find()]
	return json_response(data)

@app.route('/api/get_data_size')
def api_get_data_size():
	mongo_data = fetch_table(get_db(), BAC_MONGO_TABLE)
	return json_response({'size': mongo_data.count()})

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

	return json_error('Not implemented. Mismatch between datasets.')

# Returns the number of students who took a given exam. Also works with finding 
# out how many students contested the result of a given exam (for this use
# `contestify(exam)' instead of `exam').
def compute_student_count(exam):
	res = fetch_table(get_db(), BAC_MONGO_TABLE).aggregate([
		# We only want people who actually took the exam.
		{
			"$match": {
				exam: { '$gt': 1 }
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
@app.route('/api/count_took_exam/<string:exam>', methods = ['GET'])
def api_count_took_exam(exam):
	if not validExam(exam):
		return json_error('Invalid exam name.')

	return json_response(compute_student_count(exam))

# Returns the number of students who took the given exam and contested the
# result.
@app.route('/api/count_contested_exam/<string:exam>', methods = ['GET'])
def api_count_contested_exam(exam):
	if not validExam(exam):
		return json_error('Invalid exam name.')

	return json_response(compute_student_count(contestify(exam)))

# Returns the percentage of the students who took the given exam who contested
# their grade.
@app.route('/api/percent_contested_by_exam/<string:exam>', methods = ['GET'])
def api_percent_contested_by_exam(exam):
	if not validExam(exam):
		return json_error('Invalid exam name.')

	# Number of people who took the exam
	resTotal = compute_student_count(exam)

	# Number of people who contested the result
	resContested = compute_student_count(constestify(exam))

	percentContested =  resContested * 1.0 / resTotal * 100.0 
	return json_response({ 'percentContested': percentContested })


# Returns the number of students who increased their final grade by contesting
# the exam results.
@app.route('/api/increased_grade_by_contesting/<string:exam>', methods = ['GET'])
def api_increased_grade_by_contesting(exam):
	if not validExam(exam):
		return json_error('Invalid exam name.')

	return json_response(compute_contested_grade_effect(exam, '$gt'))


# Returns the number of students who lowered their final grade by contesting
# the exam results.
@app.route('/api/decreased_grade_by_contesting/<string:exam>', methods = ['GET'])
def api_decreased_grade_by_contesting(exam):
	if not validExam(exam):
		return json_error('Invalid exam name.')

	return json_response(compute_contested_grade_effect(exam, '$lt'))

# Returns the number of students for whom contesting the exam results had no
# impact on their final grade.
@app.route('/api/maintained_grade_by_contesting/<string:exam>', methods = ['GET'])
def api_maintained_grade_by_contesting(exam):
	if not validExam(exam):
		return json_error('Invalid exam name.')

	return json_response(compute_contested_grade_effect(exam, '$eq'))

# Return the grade distribution (as a histogram) for the given exam and subject
# combination.  Example: fourth exam (`notaEa'), computer science subject
# (`informatica').
# Note: use `*' to ignore the particular subject and/or exam.
# Note: ignoring the exam but not the subject is currently unsupported. Reason:
# 		We would need to figure out what exam the subject refers to for each
#		individual student.  TODO(ioan) This can be done with a lookup table;
#		There are not subjects that can occur on different exam days.
# TODO(ioan) Move to `bac_stats.py'.
@app.route('/api/histogram_by_subject', methods = ['GET'])
@app.route('/api/histogram_by_subject/<int:binSize>', methods = ['GET'])
@app.route('/api/histogram_by_subject/<float:binSize>', methods = ['GET'])
@app.route('/api/histogram_by_subject/<string:exam>/<string:subject>', methods = ['GET'])
@app.route('/api/histogram_by_subject/<string:exam>/<string:subject>/<int:binSize>', methods = ['GET'])
@app.route('/api/histogram_by_subject/<string:exam>/<string:subject>/<float:binSize>', methods = ['GET'])
def api_histogram_by_subject(exam = '*', subject = '*', binSize = 0.1):
	pipeline = []

	if binSize <= 0.0:
		return json_error('Invalid bin size.')

	if subject != '*' and exam == '*':
		return json_error('Cannot aggregate based on just the subject.')

	if exam != "*":
		if not validExam(exam) and not validContestedExam(exam):
			return json_error('Invalid exam name.')

		pipeline.append({
			"$match": {
				exam: { "$gt": 1 }
			}
		})
		pipeline.append({
			"$project": {
	    		"gradeLowerBound": {
	    			"$subtract": ["$" + exam, { "$mod": [ "$" + exam, binSize] } ]
	    		}
	    	}
	    })
	else:
		# We don't care about an exam in particular.  Evaluate the final
		# average field instead (`medie'), but only if the user also deosn't want
		# to search by subject.  This is done after the next block so as not to
		# interleave `match' and `project' stages.
		if subject == '*':
			pipeline.append({
				"$match": {
					"medie": { "$gt": 1 }
				}
			})

	if subject != "*":
		# Also filter on subject name.
		subject_name = getFancyName(subject)
		if subject_name is None:
			return json_error('Invalid subject name. (Try using \'*\' if the ' +
				'subject itself doesn\'t matter.)')

		exam_subject = get_subject_column(exam)
		subject_matcher =  {
			"$match": {
				exam_subject: subject_name
			}
		}

		# We need to merge multiple conditions.  Apparently having multiple
		# matches in a row doesn't work.  We need to ``and'' them together.
		if '$match' in pipeline[0]:
			pipeline[0] = merge_matchers(pipeline[0], subject_matcher)
		else:
			pipeline.append(subject_matcher)

	if exam == '*' and subject == '*':
		pipeline.append({
			"$project": {
	    		"gradeLowerBound": {
	    			"$subtract": ["$medie", { "$mod": [ "$medie", binSize] } ]
	    		}
	    	}
	    })
	
	pipeline.append({
   		"$group": {
    		"_id": "$gradeLowerBound", 
       		"count": { "$sum": 1 }
	    }
	})
	pipeline.append({
		"$sort": {
			"_id": 1
		}
	})
	
	tbl = fetch_table(get_db(), BAC_MONGO_TABLE)
	res = tbl.aggregate(pipeline)

	return json_response(res['result'])

@app.route('/api/limba_moderna')
def api_limba_moderna():
	tbl = fetch_table(get_db(), BAC_MONGO_TABLE)
	res = tbl.aggregate({
		"$group": {
			"_id": "$limbaModerna",
			"count": { "$sum": 1 }
		}
	})
	for r in res['result']:
		print unicode(r)#.encode('UTF-8')
	return json_response(res['result'])

# Handles the initial loading of the one-page visualization app.
@app.route('/app')
def app_index():
    return render_template('index.html')

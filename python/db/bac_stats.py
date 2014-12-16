# -*- coding: utf-8 -*-

import json
import os

from bson.objectid import ObjectId
from bson import Code
from bson.son import SON
from flask import render_template, g
from unidecode import unidecode

from data.mongo_util import *
from util import *

# Returns how many students increased/lowered/didn't change their grade by
# contesting the exam's result.  `op' is a mongoDB comparison operator.
# Contested results are only taken into consideration if they differ by 0.5 or
# more points from the original grade, if the original grade is less than 9.5. 
# If the original grade is greater than or equal to 9.5, then this threshold is
# lowered to 0.1.
# This function takes this into account.
def compute_contested_grade_effect(subject, op):
	contestedSubject = contestify(subject)
	if op != '$eq':
		matcher = {
			"$match": {
				"$and": [
					{ 'comparePass': 1 },
					{ '$or': [
						
						{ '$and': [{'original': { '$gte': 9.5 }}, { 'diff': { '$gte': 0.1 } }]},
						{ '$and': [{'original': { '$lt': 9.5 }}, { 'diff': { '$gte': 0.5 } }]}
					]}
					
				]
			}
		}
	else:
		# When looking for students unaffected by the updated exam results, we 
		# need to include all students for whom the difference was too small.
		matcher = {
			"$match": {
				"$and": [
					{ '$or': [
						{ '$and': [{'original': { '$gte': 9.5 }}, { 'diff': { '$lt': 0.1 } }]},
						{ '$and': [{'original': { '$lt': 9.5 }}, { 'diff': { '$lt': 0.5 } }]}
					]}
					
				]
			}
		}

	res = fetch_table(get_db(), BAC_MONGO_TABLE).aggregate([
		{
			"$match": {
				# Match students who contested their exam result for `subject'.
				contestedSubject: { '$gt': 1 }
			}
		},
		# And who got a bigger/smaller grade as a result of that.
		# This happens in two stages because of the way Mongo aggregations work.
		{
			"$project": {
				contestedSubject: True,
				'comparePass': { "$cond": 
					[ { op: [ '$' + contestedSubject, '$' + subject ] }, 1, 0 ]
				},
				'diff': { "$subtract": [ '$' + contestedSubject, '$' + subject ] },
				'original': '$' + subject
			}
		},
		{
			"$project": {
				contestedSubject: True,
				'comparePass': True,
				# Compute absolute value of 'diff'.
				'diff': { '$cond': [{'$lt': ['$diff', 0]}, {'$multiply': ['$diff', -1]}, '$diff'] },
				'original': True
			}
		},
		matcher,
		{
			"$group": {
	   			"_id": None, 
	   			"count": { "$sum": 1 }
       		}
		}
		])['result']

	return 0 if len(res) == 0 else res[0]['count']
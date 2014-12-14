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
def compute_contested_grade_effect(subject, op):
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
# -*- coding: utf-8 -*-

import json

from flask import Response, g

from config import *
from data.mongo_util import *

# Adds a default serializer for datetime objects, which python doesn't know how
# to json serialize by default; note: this still allows everything else to be
# serialized just fine!
def json_ser_with_datetime(obj):
	import calendar, datetime

	if isinstance(obj, datetime.datetime):
		if obj.utcoffset() is not None:
			obj = obj - obj.utcoffset()

	millis = int(
		calendar.timegm(obj.timetuple()) * 1000 +
		obj.microsecond / 1000
	)

	return millis

def contestify(subject):
	index = len("nota")
	return subject[:index] + "Contestatie" + subject[index:]

def json_response(obj):
	return Response(
			json.dumps(obj, 
				default = json_ser_with_datetime,
				indent = 4,
				separators=(',', ': ')
				),
			mimetype="application/json"
		)


def validContestedExam(exam):
	validContestedExams = {
		'notaContestatieEa': 'Contestatie limba si literatura romana',
		'notaContestatieEb': 'Contestatie limba si literatura materna',
		'notaContestatieEc': 'Contestatie proba profil #1 (ex. Mate)',
		'notaContestatieEd': 'Contestatie proba profil #2 (ex. Fizica)',
	}
	return exam in validContestedExams

def validExam(exam):
	validExams = {
		'notaEa': 'Limba si literatura romana',
		'notaEb': 'Limba si literatura materna',
		'notaEc': 'Proba profil #1 (ex. Mate)',
		'notaEd': 'Proba profil #2 (ex. Fizica)',
	}
	return exam in validExams

# It seems that unidecode doesn't really support romanian characters, so this 
# mini-helper will have to do.
def transliterate(string):
	romap = {
		u'ă': 'a',
		u'â': 'a',
		u'î': 'i',
		u'ș': 's',
		u'ț': 't',
		u'Ă': 'A',
		u'Â': 'A',
		u'Î': 'I',
		u'Ș': 'S',
		u'Ț': 'T',
	}

	for k in romap:
		string = string.replace(k, romap[k])

	return string

def getFancyName(subject):
	# TODO(ioan) Cache this shit.  It's embarrassing.
	# TODO(ioan) Easy name list: 'Romana', 'Mate' etc.
	validSubjects = [
		# subiectEa
		u"Limba română (UMAN)",
		u"Limba română (REAL)",

		# subiectEb

		# subiectEc
		u"Matematică MATE-INFO",
		u"Matematică TEHN",
		u"Matematică ST-NAT",
		u"Istorie",

		#  subiectEd
		u"Biologie vegetală și animală",
		u"Anatomie și fiziologie umană, genetică și ecologie umană",
		u"Geografie",
		u"Economie",
		u"Informatică MI C/C++",
		u"Informatică MI Pascal",
		u"Fizică TEO",
		u"Fizică TEH",
		u"Chimie anorganică TEO Nivel I/II",
		u"Chimie anorganică TEH Nivel I/II",
		u"Chimie organică TEO",
		u"Chimie organică TEH"
		# TODO(ioan) Nume corecte pentru: filosofie, logica si argumentare,
		# psihologie si sociologie, limbi materne.
	]
	validSubjectMap = {}
	for x in validSubjects:
		validSubjectMap[transliterate(x).lower()] = x
	if subject.lower() in validSubjectMap:
		return validSubjectMap[subject.lower()]
	else:
		return None

def json_error(message):
	return json_response({
		'error': message
	});

# Return the name of the column specifying the subject of this exam.
# Example: `notaEa' -> `subiectEa'.
def get_subject_column(exam):
	return "subiect" + exam[-2:]

# Needed for jsonifying mongo objectids.  They're not usually needed, but it
# helps to be able to dump them from time to time.
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
		g.mongo = fetch_db(create_client(), BAC_MONGO_DB)

	return g.mongo

# Helpful for converting an accessor string like `foo.bar.baz' into multiple
# subsequent dictionary lookups.
def nestedGrab(obj, bitsLeft):
	if(len(bitsLeft) == 1):
		return obj[bitsLeft[0]]
	else:
		return nestedGrab(obj[bitsLeft[0]], bitsLeft[1:])


# Fields we want to display on the main page (pre-visualization).
interesting = ['id', 'specializare', 'profil', 'filiera', 'noteRecunEa',
				'noteRecunEb', 'noteRecunEc', 'noteRecunEd', 'formaInvatamant',
				'medie', 'codUnitate', 'status']

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
	'status': 'Statut'
}

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

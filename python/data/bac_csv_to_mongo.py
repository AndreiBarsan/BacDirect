# -*- coding: utf-8 -*-

import os
import codecs
import sys
import json

import mongo_util
from mongo_util import *
from ..config import *

from unidecode import unidecode

'''
Header: [u'Cod unic candidat ', u'Sex', u'Specializare', u'Profil', u'Fileira', u'Forma de \xeenv\u0
103\u021b\u0103m\xe2nt', u'Mediu candidat', u'Unitate (SIRUES)', u'Clasa', u'Subiect ea', u'Subiect
eb', u'Limba modern\u0103', u'Subiect ec', u'Subiect ed', u'Promo\u021bie', u'NOTE_RECUN_A', u'NOTE_
RECUN_B', u'NOTE_RECUN_C', u'NOTE_RECUN_D', u'NOTE_RECUN_EA', u'NOTE_RECUN_EB', u'NOTE_RECUN_EC', u'
NOTE_RECUN_ED', u'STATUS_A', u'STATUS_B', u'STATUS_C', u'STATUS_D', u'STATUS_EA', u'STATUS_EB', u'ST
ATUS_EC', u'STATUS_ED', u'ITA', u'SCRIS_ITC', u'SCRIS_PMS', u'ORAL_PMO', u'ORAL_IO', u'NOTA_EA', u'N
OTA_EB', u'NOTA_EC', u'NOTA_ED', u'CONTESTATIE_EA', u'NOTA_CONTESTATIE_EA', u'CONTESTATIE_EB', u'NOT
A_CONTESTATIE_EB', u'CONTESTATIE_EC', u'NOTA_CONTESTATIE_EC', u'CONTESTATIE_ED', u'NOTA_CONTESTATIE_
ED', u'PUNCTAJ DIGITALE', u'STATUS', u'Medie\r\n']
'''

# If not present, treat as string.
bac_column_types = {
	"medie": "float"
}

bac_column_map = {
	"Cod unic candidat": "id",
	"Sex": "sex",
	"Specializare": "specializare",
	"Profil": "profil",
	"Fileira": "filiera",
	"Forma de invatamant": "formaInvatamant",
	"Mediu candidat": "mediuCandidat",
	# Aceasta coloana **NU** contine codul SIRUES al institutiei, ci doar codul ei.
	# Codul unei institutii si codul sau SIRUES sunt doua lucruri diferite.
	"Unitate (SIRUES)": "codUnitate",
	"Clasa": "clasa",
	"Subiect ea": "subiectEa",
	"Subiect eb": "subiectEb",
	"Limba moderna" : "limbaModerna",
	"Subiect ec": "subiectEc",
	"Subiect ed": "subiectEd",
	"Promotie" : "promotie",
	"NOTE_RECUN_A": "noteRecunA",
	"NOTE_RECUN_B": "noteRecunB",
	"NOTE_RECUN_C": "noteRecunC",
	"NOTE_RECUN_D": "noteRecunD",
	"NOTE_RECUN_EA": "noteRecunEa",
	"NOTE_RECUN_EB": "noteRecunEb",
	"NOTE_RECUN_EC": "noteRecunEc",
	"NOTE_RECUN_ED": "noteRecunEd",
	"STATUS_A": "statusA",
	"STATUS_B": "statusB",
	"STATUS_C": "statusC",
	"STATUS_D": "statusD",
	"STATUS_EA": "statusEa",
	"STATUS_EB": "statusEb",
	"STATUS_EC": "statusEc",
	"STATUS_ED": "statusEd",
	"ITA": "ITA",
	"SCRIS_ITC": "scrisITC",
	"SCRIS_PMS": "scrisPMS",
	"ORAL_PMO": "oralPMO",
	"ORAL_IO": "oralID",
	"NOTA_EA": "notaEa",
	"NOTA_EB": "notaEb",
	"NOTA_EC": "notaEc",
	"NOTA_ED": "notaEd",
	"CONTESTATIE_EA": "contestatieEa",
	"NOTA_CONTESTATIE_EA": "notaContestatieEa",
	"CONTESTATIE_EB": "contestatieEa",
	"NOTA_CONTESTATIE_EB": "notaContestatieEa",
	"CONTESTATIE_EC": "contestatieEa",
	"NOTA_CONTESTATIE_EC": "notaContestatieEa",
	"CONTESTATIE_ED": "contestatieEa",
	"NOTA_CONTESTATIE_ED": "notaContestatieEa",
	"PUNCTAJ DIGITALE": "punctajCompetenteDigitale",
	"STATUS": "status",
	"Medie": "medie"
}

school_column_map = {
	# We have to go deeper!
	"Nr.": "codUnitate",
	"Judet": "judet"
}

def clean_col(col_name, name_map):
	return name_map[unidecode(col_name)]

def parse_header(line, name_map, separator):
	cols = [el.strip() for el in line.split(separator)]
	clean_cols = []

	for col in cols:
		if unidecode(col) in name_map:
			clean_cols.append(clean_col(col, name_map))
		else:
			print "Warning: no mapping found for column [", unidecode(col), "]"

	return clean_cols

def parse_bac_header(line, separator):
	return parse_header(line, bac_column_map, separator)

def parse_school_header(line, separator):
	return parse_header(line, school_column_map, separator)

def parse_line(header, line, separator):
	# Herp-derp, the CSV is sometimes actually a TSV.  Gotta love consistency, yo.
	fields = [el.strip() for el in line.split(separator)]
	obj = {}
	
	if(len(fields) < len(header)):
		print "WARNING, field possibly malformed. Field hat", len(fields), "elements, header had", len(header)
		return None

	for i in range(len(header)):
		obj[header[i]] = fields[i]

	return obj	

def parse_school_line(header, line, separator, context):
	obj = parse_line(header, line, separator)
	return obj

def parse_bac_line(header, line, separator, context):
	obj = parse_line(header, line, separator)	
	schools = context['schools']
	school = schools.find_one({'codUnitate': obj['codUnitate']})
	if school is None:
		println("Warning! Could not find schoold with ID [" + obj['codUnitate']) + "]."
	else:
		obj['school'] = school
		# Makes grouping easier!
		obj['judet'] = school['judet']

	for el in bac_column_types:
		if(bac_column_types[el] == 'float'):
			try:
				obj[el] = float(obj[el].replace(",", "."))
			except:
				obj[el] = 0

	return obj

# Loads the given file into 'mongo_table'.  Set limit to -1 to load everything.
# 'parse_header' and 'parse_line' are meant to convert a line string to an array
# of cells (while also potentially doing stuff like normalization and cleanup).
def csv_to_mongo(filename, separator, mongo_table, limit, parse_header_fn, parse_line_fn, context):
	input = codecs.open(filename, 'r', BAC_DATASET_ENCODING)
	
	if(mongo_table.count() > 100):
		answer = raw_input("Table (" + str(mongo_table.name) + ") already contains > 10k rows. Really reset? y/n\n")
		if(answer != 'y'):
			print "Aborting."
			return -1

	print "Cleaning our old table..."
	mongo_table.remove()

	data = []
	print "Starting read. Will limit to", limit, "rows (-1 means everything)."
	lineIndex = 0
	for line in input:
		if(lineIndex == 0):
			print "Reading header..."
			header = parse_header_fn(line, separator)
			#for f in header:
			#	print unicode(f).encode('utf-8')
			print "Header end.", len(header), "columns. Reading rows."
		else:
			obj = parse_line_fn(header, line, separator, context)
			if(obj is not None):
				data.append(obj)
			

		lineIndex += 1
		if limit != -1 and lineIndex > limit:
			break

	print "Performing mongo insert!"
	insert_data(mongo_table, data)
	print "Done loading ", mongo_table.name, "! Our mongo table has", mongo_table.count(), "entries."

def load_bac(mongo_table, schools):
	ctx = {
		'schools': schools
	}
	return csv_to_mongo(BAC_DATASET_FILE, "\t", mongo_table, -1, parse_bac_header, parse_bac_line, ctx)

def load_schools(mongo_table):
	return csv_to_mongo(SCHOOL_DATASET_FILE, ",", mongo_table, -1, parse_school_header, parse_school_line, {})

def main():
	mongoc = mongo_util.create_client()
	mongodb = fetch_db(mongoc, BAC_MONGO_DB)
	mongo_table_bac = fetch_table(mongodb, BAC_MONGO_TABLE)
	mongo_table_school = fetch_table(mongodb, SCHOOL_MONGO_TABLE)

	print "Starting to load school data"
	load_schools(mongo_table_school)

	print "Starting to load exam result data"
	load_bac(mongo_table_bac, mongo_table_school)

main()
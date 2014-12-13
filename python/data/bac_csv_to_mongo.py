# -*- coding: utf-8 -*-

import os
import codecs
import sys
import json

import mongo_util
from mongo_util import *
from ..config import *

from unidecode import unidecode

# Rules for converting data from the (untyped) input csv file into typed Mongo
# document fields.  If a rule for a column is not present, treat as string.
# Note: 'float' also implies that commans inside that field get replaced with 
# periods, in order to support romanian decimals.
# TODO(Andrei) Use a proper localization library.
bac_column_types = {
	"medie": "float",
	"notaEa": "float",
	"notaEb": "float",
	"notaEc": "float",
	"notaEd": "float",
	"notaContestatieEa": "float",
	"notaContestatieEb": "float",
	"notaContestatieEc": "float",
	"notaContestatieEd": "float",
	"punctajCompetenteDigitale": "int",
	"id": "int"
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
	"Subiect ec": "subiectEc",
	"Subiect ed": "subiectEd",
	"Limba moderna" : "limbaModerna",
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
	"NOTA_CONTESTATIE_EB": "notaContestatieEb",
	"CONTESTATIE_EC": "contestatieEa",
	"NOTA_CONTESTATIE_EC": "notaContestatieEc",
	"CONTESTATIE_ED": "contestatieEa",
	"NOTA_CONTESTATIE_ED": "notaContestatieEd",
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
		op = bac_column_types[el]
		if(op == 'float'):
			try:
				obj[el] = float(obj[el].replace(",", "."))
			except:
				obj[el] = -1
		elif(op == 'int'):
			try:
				obj[el] = int(obj[el])
			except:
				obj[el] = -1
		else:
			raise Exception('Unknown type conversion operation: [' + op + '].')

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
	return csv_to_mongo(BAC_DATASET_FILE, "\t", mongo_table, 50000, parse_bac_header, parse_bac_line, ctx)

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
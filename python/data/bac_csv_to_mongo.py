# -*- coding: utf-8 -*-

import os
import codecs
import sys
import json

import mongo_util
from mongo_util import *
from ..config import *

from ..unidecode import unidecode

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

column_map = {
	"Cod unic candidat": "id",
	"Sex": "sex",
	"Specializare": "specializare",
	"Profil": "profil",
	"Fileira": "filiera",
	"Forma de invatamant": "formaInvatamant",
	"Mediu candidat": "mediuCandidat",
	"Unitate (SIRUES)": "unitate",
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

def parse_line(header, line):
	# Herp-derp, the CSV is actually a TSV
	fields = [el.strip() for el in line.split('\t')]
	obj = {}
	assert len(header) == len(fields)
	for i in range(len(header)):
		cleanCol = column_map[header[i]]
		obj[cleanCol] = fields[i]
	return obj	

def clean_col(col):
	return unidecode(col)

def parse_header(line):
	cols = [el.strip() for el in line.split('\t')]
	return [clean_col(col) for col in cols]

def main():
	input = codecs.open(BAC_DATASET_FILE, 'r', BAC_DATASET_ENCODING)
	output = codecs.open("test.txt", "w", BAC_DATASET_ENCODING)
	mongoc = mongo_util.create_client()
	mongodb = fetch_db(mongoc, BAC_MONGO_DB)
	mongotbl = fetch_table(mongodb, BAC_MONGO_TABLE)

	if(mongotbl.count() > 100):
		answer = raw_input("Table already contains > 10k rows. Really reset? y/n\n")
		if(answer != 'y'):
			print "Aborting."
			return -1

	print "Cleaning our old table..."
	mongotbl.remove()

	limit = 10000
	data = []
	print "Starting read. Will limit to", limit, "rows (-1 means everything)."
	lineIndex = 0
	for line in input:
		if(lineIndex == 0):
			header = parse_header(line)
			# TODO(andrei) Setup mongo table structure here dynamically, maybe?
			print "Read header:"
			for f in header:
				print unicode(f).encode('utf-8')
			print "Header end.", len(header), "columns. Reading rows."
		else:
			data.append(parse_line(header, line))
			

		lineIndex += 1
		if limit != -1 and lineIndex > limit:
			break

	print "Performing mongo insert!"
	insert_data(mongotbl, data)
	print "Done! Our mongo table has", mongotbl.count(), "entries."

main()
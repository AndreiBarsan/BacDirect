import os
import sys
import json
import pymongo

from pymongo import MongoClient, ASCENDING, DESCENDING

def create_client():
	client = MongoClient()
	return client

def fetch_db(client, db_name):
	return client[db_name]

def fetch_table(db, table_name):
	return db[table_name]

def get_bac_data(db):
	return db.bac_table

def insert_data(table, data):
	id = table.insert(data)
	return id

def merge_matchers(m1, m2):
    cnd1 = m1['$match']
    cnd2 = m2['$match']
    return {
        '$match': {
            '$and': [ cnd1, cnd2 ]
        }
    }
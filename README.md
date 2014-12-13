Created for the Brasov Open Data Hackathon in December 2014.
GPL License.

Setup guide:
	1. Get the dataset here: http://date.gov.ro/dataset/rezultate-bacalaureat-sesiunea-i-2014
	2. Install mongodb.
	3. Install pip. Then flask and pymongo.
	4. Run python/data/bac_csv_to_mongo.py to import the data into the db.
	5. Go to python/ and run `python server.py`.

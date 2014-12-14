Created for the Brasov Open Data Hackathon in December 2014.
GPL License.

Setup guide:
------------
	1. Get the data (save it inside `python/data`).
		1.1 http://date.gov.ro/dataset/rezultate-bacalaureat-sesiunea-i-2014
		1.2 For simplicity's sake (encoding issues can get annoying) the second
			dataset is checked in.
	2. Install mongodb and make sure mongod is running.
	3. Install pip. Then flask (follow the tutorial `http://flask.pocoo.org/`).
		Also install pymongo.
	4. Install `unidecode` (might end up getting discarded in the future).
		4.1. Go to `/python/unidecode`.
		4.2. Run `python setup.py install`.
		4.3. (Optional) Run `python setup.py test`.
	5. Go to `/python` and run `python -m python.data.bac_csv_to_mongo` to
		import the data into the database.
	6. Go to `/python` and run `python -m python.server`.

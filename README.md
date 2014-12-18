Created for the Brasov Open Data Hackathon in December 2014.
Licensed under the GNU General Public License (GPL).

Summary
-------

This is a simple web application that exposes an API which can be used to explore the results of the 2014 Romanian National Baccalaureate exam.  The project also comes with an app (currently under heavy development) which can be used to visualize the data.

The app is written in Python using Flask.  The data are stored in mongoDB and the client side is currently being transitioned to AngularJS.  It uses jQuery flot and d3 for various plots and diagrams.

Setup guide (Windows and Linux)
-------------------------------
	1. Get the data (save it inside `python/data`).
		1.1 http://date.gov.ro/dataset/rezultate-bacalaureat-sesiunea-i-2014
		1.2 For simplicity's sake (encoding issues can get annoying) the second
			dataset is checked in.
	2. Install mongodb and make sure mongod is running.
	3. Install pip. Then flask (follow the tutorial `http://flask.pocoo.org/`).
		Also install pymongo using pip under venv (`pip install pymongo`).
	4. Install `unidecode` (might end up getting discarded in the future).
		4.1. Go to `/python/unidecode`.
    4.2. If the folder is empty, make sure you also grabbed this repository's submodules.  Use `git submodule update --init --recursive` to do this. 
		4.3. Run `python setup.py install`.
		4.4. (Optional) Run `python setup.py test`.
	5. Go to `/python` and run `python -m data.bac_csv_to_mongo` to
		import the data into the database.
	6. Go to `/python` and run `python -m server`.
	7. ???
	8. PROFIT!

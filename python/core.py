import os
from flask import Flask

app = Flask(__name__)
app.debug = True
app.config.from_object(__name__)

app.config.update(dict(
	DATABASE 	= os.path.join(app.root_path, ''),
	DEBUG 		= True,
	SECRET_KEY  = 'development key'
))

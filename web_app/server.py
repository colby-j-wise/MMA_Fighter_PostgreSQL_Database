#!/usr/bin/env python3.5
"""
TEAM: Colby Wise & Dallas 
UNIs: CJW2165 | DRJ2115
DB ADDRESS: DRJ2115
COMS W4111 Part 1.3

README --help
"""

import os
import pandas as pd 
import numpy as np 

from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, ForeignKey
from sqlalchemy import insert, select, case, cast, Float
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

# Create application and set path
tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


# Connect to POSTGRESQL database
def connect(user, password, db, host='35.185.80.252', port=5432):
	""" 
	Returns a connection and metadata object for preset host name/port
	Requires user, password, and db = database name
	"""
	url = 'postgresql://{}:{}@{}:{}/{}'
	url = url.format(user, password, host, port, db)

	# The return value of create_engine() is our database engine object
	connection = create_engine(url, client_encoding='utf8')

	# Bind connection to MetaData()
	metadata = MetaData(bind=connection, reflect=True)

	return connection, metadata

conn, meta = connect('drj2115', 'QWErty', 'w4111')


@app.before_request
def before_request():
	"""
	This function runs at the beginning of every web request. 
	Sets up a database connection that can be used throughout the request.

	Variable g globally accessible.
	"""
	try:
		g.conn = conn.connect()
	except:
		print("Error: Problem connecting to database")
		import traceback; traceback.print_exc()
		g.conn = None


@app.teardown_request
def teardown_request(exception):
	"""
	Ensure database connection closed at end of web request so not to overload server
	"""
	try:
		g.conn.close()
	except Exception as e:
		pass


@app.route('/')
def index():
	"""
	Main page of web app. Displays boxers in drop down format. 
	Lets users select boxers and display stats.
	"""

	# DEBUG: this is debugging code to see what request looks like
	print(request.args)

	fighting_words = {'name': 'An attack is the best form of defense'}

	# Simple query to return table 'fighter' from db to ensure app working
	result = g.conn.execute("SELECT fname, lname, fid FROM fighter GROUP BY fid, fname, lname ORDER BY fname, lname LIMIT 50")
	fighters =[]

	for fighter in result:
		fighters.append(fighter)
	result.close()

	return render_template('index.html', 
							title='All the Fighters in the World',
							user=fighting_words['name'],
							fighter_list=fighters)


if __name__== "__main__":
	app.run()




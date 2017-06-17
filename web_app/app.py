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
@app.route('/index')
def index():
	"""
	Main page of web app. Displays boxers in drop down format. 
	Lets users select boxers and display stats.
	"""

	# DEBUG: this is debugging code to see what request looks like
	print(request.args)

	fighting_words = {'name': 'An attack is the best form of defense'}

	# SQL query to get fighter id and name from table 'fighter' to populate drop down list
	result = g.conn.execute("SELECT fname, lname, fid FROM fighter GROUP BY fid, fname, lname ORDER BY fname, lname LIMIT 50")
	fighters =[]

	for fighter in result:
		fighters.append(fighter)
	result.close()

	return render_template('index.html', 
							title='All the Fighters in the World',
							user=fighting_words['name'],
							fighter_list=fighters)


@app.route('/results', methods=['GET', 'POST'])
def results():
	# DEBUG: this is debugging code to see what request looks like
	print(request.args)

	# Returns fighter selection from drop down menu as **string***
	select = request.form.get('selected_fighter')

	# str indexing to remove fname, lname from select and get only fid used in below SQL query
	fighter_fid = (int(''.join(list(filter(str.isdigit, select)))))
	
	# Get statistics for selected fighter by FID	
	cursor = g.conn.execute("SELECT fid, fname, lname, height, sex FROM fighter WHERE fid = {}".format(fighter_fid))
	stats = [dict(fid=row['fid'], 
				fname=row['fname'], 
				lname=row['lname'], 
				height=row['height'], 
				sex=row['sex']) for row in cursor.fetchall()]
	cursor.close()
	return render_template('results.html', output=stats)


if __name__== "__main__":
	app.run()




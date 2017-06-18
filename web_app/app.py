#!/usr/bin/env python3.5
"""
TEAM: Colby Wise & Dallas 
UNIs: CJW2165 | DRJ2115
DB ADDRESS: DRJ2115
COMS W4111 Part 1.3

README --help
"""
import re
import os
from datetime import date
#import pandas as pd 
#import numpy as np 

from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer
from sqlalchemy import ForeignKey, insert, select, case, cast, Float
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
	Ensure database connection closed at end of web request so not to
	overload server
	"""
	try:
		g.conn.close()
	except Exception as e:
		pass

# map displayed fighter numbers to fids, careful not to expose fids to public (otherwise haxxers can break into the mainframe)
fid_dict = dict()

show_f1_stats = False
show_f2_stats = False
show_f1_events = False
show_f2_events = False

default_fighters = []

@app.route('/')
@app.route('/index')
def index():
	"""
	Main page of web app. Displays boxers in drop down format. 
	Lets users select boxers and display stats.
	"""
	global fid_dict, default_fighters
	# DEBUG: this is debugging code to see what request looks like
	print(request.args)

	fighting_words = {'name': 'An attack is the best form of defense'}

	# SQL query to get fighter id and name from table 'fighter' to
	# populate drop down list
	result = g.conn.execute("SELECT fid, lname, fname " \
				"FROM fighter " \
				"GROUP BY fid, lname, fname " \
				"ORDER BY lname, fname")
	default_fighters =[]
	i = 1
	for fighter in result:
		fid_dict[str(i)] = fighter[0]
		f = str(i) + '. '
		if len(fighter) > 1:
			f += str(fighter[1])
		if len(fighter) > 2:
			f += ', ' + str(fighter[2])
		i += 1
		default_fighters.append(f)

	result.close()
	return render_template('index.html',
				title='All the Fighters in the World',
				user=fighting_words['name'],
				fighter_list=default_fighters)

@app.route('/index', methods=['GET', 'POST'])
def results():
	global fid_dict, default_fighters
	show_f1_stats = False
	show_f2_stats = False
	show_f1_events = False
	show_f2_events = False

	query = None
	if request.form.get('stats1'):
		print("stats1 selected")
	if request.form.get('stats2'):
		print("stats2 checked")
	if request.form.get('events1'):
		print("events1 checked")
	if request.form.get('events2'):
		print("events2 checked")
	# DEBUG: this is debugging code to see what request looks like
	print(request.args)

	# Returns fighter selection from drop down menu as **string**
#	select = request.form.get('selected_fighter')

	selection = None
	selection = request.form.get('select_fighter1')
	prev_fighter1 = selection

	fighter1 = dict()
	fighter2 = dict()
	if selection:
		# Look up the actual fid in the fid dictionary fid_dict
		fighter1['fid'] = fid_dict[re.split('. |, |\s |\n |\r |\t', str(selection))[0]]
		print("FIGHTER1.fid = %d" % fighter1['fid'])
#	else BAD REQUEST

	selection = request.form.get('select_fighter2')
	prev_fighter2 = selection
	if selection:
		# Look up the actual fid in the fid dictionary fid_dict
		fighter2['fid'] = fid_dict[re.split('. |, |\s |\n |\r |\t', str(selection))[0]]
#	else BAD REQUEST

	selection = request.form.get('stats1')
	if selection:
		show_f1_stats = True

	selection = request.form.get('stats2')
	if selection:
		show_f2_stats = True

	selection = request.form.get('events1')
	if selection:
		show_f1_events = True
	selection = request.form.get('events2')
	if selection:
		show_f2_events = True

	query = g.conn.execute("SELECT * FROM fighter WHERE fid = %d" % fighter1['fid'])

	fighter1.update(fill_fighter(query))

	query = g.conn.execute("SELECT * FROM fighter WHERE fid = %d" % fighter2['fid'])
	fighter2.update(fill_fighter(query))

	event_list1 = []
	event_list2 = []
	if show_f1_events:
		query = g.conn.execute("SELECT e.name " \
					"FROM event e, match m, fighter f " \
					"WHERE e.eid = m.eid AND " \
					"(f.fid = m.fid1 OR f.fid = m.fid2) " \
					"AND f.fid = %d" % fighter1['fid'])
		for row in query:
			event_list1.append(row['name'])

	if show_f2_events:
		query = g.conn.execute("SELECT e.name " \
					"FROM event e, match m, fighter f " \
					"WHERE e.eid = m.eid AND " \
					"(f.fid = m.fid1 OR f.fid = m.fid2) " \
					"AND f.fid = %d" % fighter2['fid'])
		for row in query:
			event_list2.append(row['name'])

	tmpp = None
	query.close()

	return render_template('index.html',
				f1_stats=show_f1_stats,
				f2_stats=show_f2_stats,
				prev_f1=prev_fighter1,
				prev_f2=prev_fighter2,
				f1_events=show_f1_events,
				f2_events=show_f2_events,
				f1_events_list=event_list1,
				f2_events_list=event_list2,
				fname1=fighter1['fname'],
				age1=fighter1['age'],
				nname1=fighter1['nickname'],
				lname1=fighter1['lname'],
				wt1=fighter1['wt'],
				ht1=fighter1['ht'],
				nation1=fighter1['nationality'],
				wins1=fighter1['wins'],
				losses1=fighter1['losses'],
				draws1=fighter1['draws'],
				nc1=fighter1['nc'],
				areach1=fighter1['arm_reach'],
				lreach1=fighter1['leg_reach'],

				fname2=fighter2['fname'],
				age2=fighter2['age'],
				nname2=fighter2['nickname'],
				lname2=fighter2['lname'],
				wt2=fighter2['wt'],
				ht2=fighter2['ht'],
				nation2=fighter2['nationality'],
				wins2=fighter2['wins'],
				losses2=fighter2['losses'],
				draws2=fighter2['draws'],
				nc2=fighter2['nc'],
				areach2=fighter2['arm_reach'],
				lreach2=fighter2['leg_reach'],
				fighter_list=default_fighters)

def fill_fighter(query):
	if query == None:
		return None
	fighter = dict()
	for row in query:
		if row['lname']:
			fighter['lname'] = str(row['lname'])
		else:
			fighter['lname'] = None
		if row['fname']:
			fighter['fname'] = str(row['fname'])
		else:
			fighter['fname'] = None
		if row['nickname']:
			fighter['nickname'] = str(row['nickname'])
		else:
			fighter['nickname'] = None
		if row['dob']:
			fighter['age'] = get_age(row['dob'])
		else:
			fighter['age'] = None
		if row['nationality']:
			fighter['nationality'] = str(row['nationality'])
		else:
			fighter['nationality'] = None
		if row['wins']:
			fighter['wins'] = row['wins']
		else:
			fighter['wins'] = 0
		if row['losses']:
			fighter['losses'] = row['losses']
		else:
			fighter['losses'] = 0
		if row['draws']:
			fighter['draws'] = row['draws']
		else:
			fighter['draws'] = None
		if row['nc']:
			fighter['nc'] = row['nc']
		else:
			fighter['nc'] = None
		if row['weight']:
			fighter['wt'] = row['weight']
		else:
			fighter['wt'] = None
		if row['height']:
			fighter['ht'] = row['height']
		else:
			fighter['ht'] = None
		if row['arm_reach']:
			fighter['arm_reach'] = row['arm_reach']
		else:
			fighter['arm_reach'] = None
		if row['leg_reach']:
			fighter['leg_reach'] = row['leg_reach']
		else:
			fighter['leg_reach'] = None

	return fighter

def get_age(birthdate):
	today = date.today()
	return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

if __name__== "__main__":
	app.run()

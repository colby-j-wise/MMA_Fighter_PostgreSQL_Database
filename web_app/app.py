#!/usr/bin/env python3.5
"""
TEAM: Colby Wise & Dallas Jones 
UNIs: CJW2165 | DRJ2115
DB ADDRESS: DRJ2115
COMS W4111 Part 1.3

README --help
"""
import re
import os
import pandas as pd 

from datetime import date
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer
from sqlalchemy import ForeignKey, insert, select, case, cast, Float
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

class Match:
	def __init__(self):
		self.name = None
		self.location = None
		self.opp_name = None
		self.time = None
		self.result = None
		self.round_num = []
		self.knockdowns = []
		self.takedowns = []
		self.strikes = []
		self.sub_att = []
		self.opp_knockdowns = []
		self.opp_takedowns = []
		self.opp_strikes = []
		self.opp_sub_att = []

	def fill(self, eid, mid, swap):
		# Get round data
		query = g.conn.execute("SELECT * FROM round " \
				       "WHERE eid = %d AND mid = %d " \
				       "ORDER BY round_num" % (eid, mid))
		i = 0
		for row in query:
			i += 1
			self.round_num.append(i)
			if swap:
				self.knockdowns.append(row['f2_knockdowns'])
				self.takedowns.append(row['f2_takedowns'])
				self.strikes.append(row['f2_strikes'])
				self.sub_att.append(row['f2_sub_att'])
				self.opp_knockdowns.append(row['f1_knockdowns'])
				self.opp_takedowns.append(row['f1_takedowns'])
				self.opp_strikes.append(row['f1_strikes'])
				self.opp_sub_att.append(row['f1_sub_att'])
				continue

			self.knockdowns.append(row['f1_knockdowns'])
			self.takedowns.append(row['f1_takedowns'])
			self.strikes.append(row['f1_strikes'])
			self.sub_att.append(row['f1_sub_att'])
			self.opp_knockdowns.append(row['f2_knockdowns'])
			self.opp_takedowns.append(row['f2_takedowns'])
			self.opp_strikes.append(row['f2_strikes'])
			self.opp_sub_att.append(row['f2_sub_att'])
		query.close()

class Fighter:
	def __init__(self):
		self.fid = None
		self.lname = None
		self.fname = None
		self.nname = None
		self.dob = None
		self.sex = None
		self.nationality = None
		self.wins = None
		self.losses = None
		self.draws = None
		self.nc = None
		self.weight = None
		self.height = None
		self.arm_reach = None
		self.leg_reach = None
		self.matches = []
		self.team = []
		self.rank_list = []
		self.event_list = []

	def fill(self, fid):
		self.fid = fid

		# Get basic fighter information
		query = g.conn.execute("SELECT * " \
				       "FROM fighter " \
				       "WHERE fid = %d" % self.fid)
		for row in query:
			self.lname = row['lname']
			self.fname = row['fname']
			self.nname = row['nickname']
			self.dob = row['dob']
			self.sex = row['sex']
			self.nationality = row['nationality']
			self.weight = row['weight']
			self.height = row['height']
			self.arm_reach = row['arm_reach']
			self.leg_reach = row['leg_reach']
		query.close()

		# Get data for all matches
		query = g.conn.execute("SELECT e.name, f.lname, f.fname, " \
						"f.nickname, m.eid, m.mid, " \
						"m.fid1, m.f1_result, " \
						"m.result_time, m.method, " \
						"e.location " \
				       "FROM event e, match m, fighter f " \
				       "WHERE ((m.fid1 = %d AND f.fid = m.fid2) " \
						"OR (m.fid1 = f.fid AND m.fid2 = %d)) " \
						"AND m.eid = e.eid " \
				       "ORDER BY e.eid, m.mid" % (self.fid, self.fid))

		# For each match...
		i = 0
		for row in query:
			i += 1
			m = Match()
			m.name = row['name']
			m.location = row['location']
			if row['fname']:
				m.opp_name = row['fname']
			if row['lname']:
				if m.opp_name:
					m.opp_name += " " + row['lname']
				else:
					m.opp_name = row['lname']
			self.event_list.append("%d. %s - vs %s" %(i, m.name, m.opp_name))
			if row['result_time']:
				m.time = row['result_time']
			swap = False
			result = row['f1_result'].upper()
			method = row['method'].upper()
			if result == 'DRAW' or result == 'NC':
				m.result = result
			elif row['fid1'] != self.fid:
				swap = True
				if result == 'WIN':
					m.result = 'LOSS'
				else:
					m.result = 'WIN'
			else:
				m.result = result

			if method:
				m.result += " BY " + method

			m.fill(row['eid'], row['mid'], swap)

			self.matches.append(m)
		query.close()

		# Add ranks to the rank_list
		query = g.conn.execute("SELECT w.name, r.rank " \
				       "FROM ranking r, weightclass w " \
				       "WHERE r.fid = %d AND r.wid = w.wid" \
					% self.fid)
		for row in query:
			self.rank_list.append("#%d %s" % (row['rank'], row['name']))
		query.close()

		# Count wins
		query = g.conn.execute("SELECT COUNT(*) " \
				       "FROM event e, match m " \
				       "WHERE e.eid = m.eid AND " \
				             "((m.fid1 = %d AND m.f1_result = 'win') OR" \
					     "(m.fid2 = %d AND m.f1_result = 'loss'))" \
					     % (self.fid, self.fid))
		for row in query:
			self.wins = row[0]
		query.close()

		# Count losses
		query = g.conn.execute("SELECT COUNT(*) " \
				       "FROM event e, match m " \
				       "WHERE e.eid = m.eid AND " \
				             "((m.fid1 = %d AND m.f1_result = 'loss') OR" \
					     "(m.fid2 = %d AND m.f1_result = 'win'))" \
					     % (self.fid, self.fid))
		for row in query:
			self.losses = row[0]
		query.close()

		# Count draws
		query = g.conn.execute("SELECT COUNT(*) " \
				       "FROM event e, match m " \
				       "WHERE e.eid = m.eid AND " \
				             "(m.fid1 = %d OR m.fid2 = %d) AND " \
					     "m.f1_result = 'draw'" % (self.fid, self.fid))
		for row in query:
			self.draws = row[0]
		query.close()

		# Count nc
		query = g.conn.execute("SELECT COUNT(*) " \
				       "FROM event e, match m " \
				       "WHERE e.eid = m.eid AND " \
				             "(m.fid1 = %d OR m.fid2 = %d) AND " \
					     "m.f1_result = 'NC'" % (self.fid, self.fid))
		for row in query:
			self.nc = row[0]
		query.close()

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

# map displayed fighter numbers to fids, careful not to expose fids to
# public (otherwise haxxers can break into the mainframe)
fid_dict = dict()

# map displayed match numbers to mids
f1_eid_dict = dict()
f2_eid_dict = dict()
f1_mid_dict = dict()
f2_mid_dict = dict()

fighter_list = []

@app.route('/')
@app.route('/index')
def index():
	"""
	Main page of web app. Displays boxers in drop down format. 
	Lets users select boxers and display stats.
	"""
	global fid_dict, fighter_list
	# DEBUG: this is debugging code to see what request looks like
	print(request.args)

	fighting_words = {'name': 'An attack is the best form of defense'}

	# SQL query to get fighter id and name from table 'fighter' to
	# populate drop down list
	result = g.conn.execute("SELECT fid, lname, fname " \
				"FROM fighter " \
				"GROUP BY fid, lname, fname " \
				"ORDER BY lname, fname")

	# Build fighter_list, a list of all the fighters' names, for use
	# in the drop-down menu in index.html.  An index value is appended
	# to the front of the string and mapped (via fid_dict) to the
	# fighters' fids, thus when parsing the string of the drop-down
	# selection, split the foremost integer and get the fighter's fid
	# from fid_dict.
	fighter_list =[]
	i = 1
	for fighter in result:
		fid_dict[str(i)] = fighter['fid']
		f = str(i) + '. '
		if len(fighter) > 1:
			f += str(fighter['lname'])
		if len(fighter) > 2:
			f += ', ' + str(fighter['fname'])
		i += 1
		fighter_list.append(f)

	result.close()
	return render_template('index.html',
				title='All the Fighters in the World',
				user=fighting_words['name'],
				fighter_list=fighter_list)

# Sets the drop-down selection to previous value (instead of having it reset
# to the first each time).
prev_fighter1 = None
prev_fighter2 = None

# Currently loaded fighters (avoid unnecessarily querying the same information
# upon each POST).
fighter1 = Fighter()
fighter2 = Fighter()

# Current match index (default to the first of the fighters' matches).
idx1 = 0
idx2 = 0

# Same as with prev_fighter1/2, sets the drop-down selection to the previous
# value.
prev_event1 = None
prev_event2 = None

@app.route('/index', methods=['GET', 'POST'])
def results():
	global fid_dict, fighter_list, prev_fighter1, prev_fighter2
	global fighter1, fighter2, idx1, idx2, prev_event1, prev_event2

	show_f1_stats = False
	show_f2_stats = False
	show_f1_events = False
	show_f2_events = False
	show_f1_ranks = False
	show_f2_ranks = False
	show_f1_match = False
	show_f2_match = False

	match1 = Match()
	match2 = Match()

	# Get fighter information if a new fighter has been selected, otherwise,
	# use previous information.
	selection = request.form.get('select_fighter1')
	if prev_fighter1 != selection:
		prev_fighter1 = selection
		fid = fid_dict[re.split('. |, |\s |\n |\r |\t', str(selection))[0]]
		fighter1 = Fighter()
		fighter1.fill(fid)

	selection = request.form.get('select_fighter2')
	if prev_fighter2 != selection:
		prev_fighter2 = selection
		fid = fid_dict[re.split('. |, |\s |\n |\r |\t', str(selection))[0]]
		fighter2 = Fighter()
		fighter2.fill(fid)

	# Check whether to display fighter information (stats) or rank information
	selection = request.form.get('stats1')
	if selection:
		show_f1_stats = True

	selection = request.form.get('stats2')
	if selection:
		show_f2_stats = True

	selection = request.form.get('ranks1')
	if selection:
		show_f1_ranks = True

	selection = request.form.get('ranks2')
	if selection:
		show_f2_ranks = True

	# Select fighter1's match
	selection = request.form.get('events1')
	if selection:
		show_f1_events = True
		selection = request.form.get('select_event1')
		if selection:
			show_f1_match = True
			if selection != prev_event1:
				prev_event1 = selection
				idx1 = int(re.split('. |, |\s |\n |\r |\t', str(selection))[0]) - 1
			match1 = fighter1.matches[idx1]

	# Select fighter2's match
	selection = request.form.get('events2')
	if selection:
		show_f2_events = True
		selection = request.form.get('select_event2')
		if selection:
			show_f2_match = True
			if selection != prev_event2:
				prev_event2 = selection
				idx2 = int(re.split('. |, |\s |\n |\r |\t', str(selection))[0]) - 1
			match2 = fighter2.matches[idx2]

	# Get fighter prediction
	guesstimation = predict_result(fighter1.fid, fighter2.fid)
	guess = None
	if guesstimation < 0:
		guess = "WINNER ->\n%s %s" % (fighter2.fname, fighter2.lname)
	elif guesstimation > 0:
		guess = "<- WINNER\n%s %s" % (fighter1.fname, fighter1.lname)
	else:
		guess = "DRAW"

	return render_template('index.html',
				odds=guess,
				f1_stats=show_f1_stats,
				f2_stats=show_f2_stats,
				prev_f1=prev_fighter1,
				prev_f2=prev_fighter2,
				prev_f1_event=prev_event1,
				prev_f2_event=prev_event2,
				f1_events=show_f1_events,
				f2_events=show_f2_events,
				f1_match=show_f1_match,
				f2_match=show_f2_match,
				f1_event_name = match1.name,
				f2_event_name = match2.name,
				f1_location = match1.location,
				f2_location = match2.location,
				f1_opponent = match1.opp_name,
				f2_opponent = match2.opp_name,
				f1_result = match1.result,
				f2_result = match2.result,
				f1_events_list = fighter1.event_list,
				f2_events_list = fighter2.event_list,
				f1_ranks=show_f1_ranks,
				f2_ranks=show_f2_ranks,
				f1_rank_list = fighter1.rank_list,
				f2_rank_list = fighter2.rank_list,

				f1_rd_nums = match1.round_num,
				f1_f1_s = match1.strikes,
				f1_f1_k = match1.knockdowns,
				f1_f1_t = match1.takedowns,
				f1_f1_sub = match1.sub_att,
				f1_f2_s = match1.opp_strikes,
				f1_f2_k = match1.opp_knockdowns,
				f1_f2_t = match1.opp_takedowns,
				f1_f2_sub = match1.opp_sub_att,

				f2_rd_nums = match2.round_num,
				f2_f1_s = match2.strikes,
				f2_f1_k = match2.knockdowns,
				f2_f1_t = match2.takedowns,
				f2_f1_sub = match2.sub_att,
				f2_f2_s = match2.opp_strikes,
				f2_f2_k = match2.opp_knockdowns,
				f2_f2_t = match2.opp_takedowns,
				f2_f2_sub = match2.opp_sub_att,

				fname1 = fighter1.fname,
				age1 = get_age(fighter1.dob),
				nname1 = fighter1.nname,
				lname1 = fighter1.lname,
				wt1 = fighter1.weight,
				ht1 = fighter1.height,
				nation1 = fighter1.nationality,
				wins1 = fighter1.wins,
				losses1 = fighter1.losses,
				draws1 = fighter1.draws,
				nc1 = fighter1.nc,
				areach1 = fighter1.arm_reach,
				lreach1 = fighter1.leg_reach,

				fname2 = fighter2.fname,
				age2 = get_age(fighter2.dob),
				nname2 = fighter2.nname,
				lname2 = fighter2.lname,
				wt2 = fighter2.weight,
				ht2 = fighter2.height,
				nation2 = fighter2.nationality,
				wins2 = fighter2.wins,
				losses2 = fighter2.losses,
				draws2 = fighter2.draws,
				nc2 = fighter2.nc,
				areach2 = fighter2.arm_reach,
				lreach2 = fighter2.leg_reach,
				fighter_list = fighter_list)

def get_age(birthdate):
	if birthdate:
		today = date.today()
		return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
	return None


def predict_result(fid1, fid2):
	if fid1 == None or fid2 == None:
		return None
	query = g.conn.execute("SELECT COUNT(*) " \
				"FROM event e, match m "\
				"WHERE e.eid = m.eid and (m.fid1 = %d and m.f1_result = 'win' " \
				" or m.fid2 = %d and m.f1_result = 'loss') " % (fid1, fid1))
	wins1 = 0
	for row in query:
		wins1 = row[0]
	query = g.conn.execute("SELECT COUNT(*) " \
				"FROM event e, match m "\
				"WHERE e.eid = m.eid and (m.fid1 = %d and m.f1_result = 'loss' " \
				" or m.fid2 = %d and m.f1_result = 'win') " % (fid1, fid1))
	losses1 = 0
	for row in query:
		losses1 = row[0]
	query = g.conn.execute("SELECT COUNT(*) " \
				"FROM event e, match m "\
				"WHERE e.eid = m.eid and (m.fid1 = %d and m.f1_result = 'win' " \
				" or m.fid2 = %d and m.f1_result = 'loss') " % (fid2, fid2))
	wins2 = 0
	for row in query:
		wins2 = row[0]
	query = g.conn.execute("SELECT COUNT(*) " \
				"FROM event e, match m "\
				"WHERE e.eid = m.eid and (m.fid1 = %d and m.f1_result = 'loss' " \
				" or m.fid2 = %d and m.f1_result = 'win') " % (fid2, fid2))
	losses2 = 0
	for row in query:
		losses2 = row[0]

	query = g.conn.execute("SELECT * FROM fighter f where fid = %d" % fid1)
	wt1 = 0
	ht1 = 0
	wt2 = 0
	ht2 = 0
	for row in query:
		wt1 = row['weight']
		ht1 = row['height']
	query = g.conn.execute("SELECT * FROM fighter f where fid = %d" % fid2)
	for row in query:
		wt2 = row['weight']
		ht2 = row['height']

	score = 0
	if wt1 != None and wt1 != 0 and wt2 != None and wt2 != 0:
		score = .5 * (wt1 - wt2)
	if ht1 != None and ht1 != 0 and ht2 != None and ht2 != 0:
		score += 4.0 * (ht1 - ht2)

	score += 5.0 * (wins1 - wins2)
	score -= 5.0 * (losses1 - losses2)
	
	query.close()
	return score


if __name__== "__main__":
	import click

	@click.command()
	@click.option('--debug', is_flag=True)
	@click.option('--threaded', is_flag=True)
	@click.argument('HOST', default='0.0.0.0')
	@click.argument('PORT', default=8111, type=int)
	def run(debug, threaded, host, port):

		HOST, PORT = host, port
		print("running on %s:%d" % (HOST, PORT))
		app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

run()

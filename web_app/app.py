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

# map displayed match numbers to mids
f1_eid_dict = dict()
f2_eid_dict = dict()
f1_mid_dict = dict()
f2_mid_dict = dict()

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
		fid_dict[str(i)] = fighter['fid']
		f = str(i) + '. '
		if len(fighter) > 1:
			f += str(fighter['lname'])
		if len(fighter) > 2:
			f += ', ' + str(fighter['fname'])
		i += 1
		default_fighters.append(f)

	result.close()
	return render_template('index.html',
				title='All the Fighters in the World',
				user=fighting_words['name'],
				fighter_list=default_fighters)

prev_fighter1 = None
prev_fighter2 = None
prev_fid1 = -1
prev_fid2 = -1

@app.route('/index', methods=['GET', 'POST'])
def results():
	global fid_dict, default_fighters, f1_eid_dict, f2_eid_dict, f1_mid_dict, f2_mid_dict, prev_fighter1, prev_fighter2, prev_fid1, prev_fid2
	show_f1_stats = False
	show_f2_stats = False
	show_f1_events = False
	show_f2_events = False
	show_f1_ranks = False
	show_f2_ranks = False
	fighter1 = dict()
	fighter2 = dict()

	query = None

	# DEBUG: this is debugging code to see what request looks like
	print(request.args)

	selection = None
	selection = request.form.get('select_fighter1')
	prev_fighter1 = selection

	if selection:
		# Look up the actual fid in the fid dictionary fid_dict
		fighter1['fid'] = fid_dict[re.split('. |, |\s |\n |\r |\t', str(selection))[0]]
#	else BAD REQUEST

	selection = request.form.get('select_fighter2')
	prev_fighter2 = selection

	if selection:
		# Look up the actual fid in the fid dictionary fid_dict
		fighter2['fid'] = fid_dict[re.split('. |, |\s |\n |\r |\t', str(selection))[0]]
#	else BAD REQUEST

	# Heinous, these flags be
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

	selection = request.form.get('ranks1')
	if selection:
		show_f1_ranks = True
	selection = request.form.get('ranks2')
	if selection:
		show_f2_ranks = True

	# Select data from for fighter1
	query = g.conn.execute("SELECT * FROM fighter WHERE fid = %d" % fighter1['fid'])
	fighter1.update(fill_fighter(query))

	# Count wins for fighter1
	query = g.conn.execute("SELECT COUNT(*) " \
				"FROM event e, match m "\
				"WHERE e.eid = m.eid and (m.fid1 = %d and m.f1_result = 'win' " \
				" or m.fid2 = %d and m.f1_result = 'loss') " % (fighter1['fid'], fighter1['fid']))
	for row in query:
		fighter1['wins'] =row[0]

	# Count losses for fighter1
	query = g.conn.execute("SELECT COUNT(*) " \
				"FROM event e, match m "\
				"WHERE e.eid = m.eid and (m.fid1 = %d and m.f1_result = 'loss' " \
				" or m.fid2 = %d and m.f1_result = 'win') " % (fighter1['fid'], fighter1['fid']))
	for row in query:
		fighter1['losses'] =row[0]

	# Count draws for fighter1
	query = g.conn.execute("SELECT COUNT(*) " \
				"FROM event e, match m "\
				"WHERE e.eid = m.eid and (m.fid1 = %d or m.fid2 = %d) " \
				"and  m.f1_result = 'draw' " % (fighter1['fid'], fighter1['fid']))
	for row in query:
		fighter1['draws'] =row[0]

	# Count nc for fighter1
	query = g.conn.execute("SELECT COUNT(*) " \
				"FROM event e, match m "\
				"WHERE e.eid = m.eid and (m.fid1 = %d or m.fid2 = %d) " \
				"and  m.f1_result = 'nc' " % (fighter1['fid'], fighter1['fid']))
	for row in query:
		fighter1['nc'] =row[0]

	# Get stats for fighter2
	query = g.conn.execute("SELECT * FROM fighter WHERE fid = %d" % fighter2['fid'])
	fighter2.update(fill_fighter(query))

	# Count wins for fighter2
	query = g.conn.execute("SELECT COUNT(*) " \
				"FROM event e, match m "\
				"WHERE e.eid = m.eid and (m.fid1 = %d and m.f1_result = 'win' " \
				" or m.fid2 = %d and m.f1_result = 'loss') " % (fighter2['fid'], fighter2['fid']))
	for row in query:
		fighter2['wins'] =row[0]

	# Count losses for fighter2
	query = g.conn.execute("SELECT COUNT(*) " \
				"FROM event e, match m "\
				"WHERE e.eid = m.eid and (m.fid1 = %d and m.f1_result = 'loss' " \
				" or m.fid2 = %d and m.f1_result = 'win') " % (fighter2['fid'], fighter2['fid']))
	for row in query:
		fighter2['losses'] =row[0]

	# Count draws for fighter2
	query = g.conn.execute("SELECT COUNT(*) " \
				"FROM event e, match m "\
				"WHERE e.eid = m.eid and (m.fid1 = %d or m.fid2 = %d) " \
				"and  m.f1_result = 'draw' " % (fighter2['fid'], fighter2['fid']))
	for row in query:
		fighter2['draws'] =row[0]

	# Count nc for fighter2
	query = g.conn.execute("SELECT COUNT(*) " \
				"FROM event e, match m "\
				"WHERE e.eid = m.eid and (m.fid1 = %d or m.fid2 = %d) " \
				"and  m.f1_result = 'nc' " % (fighter2['fid'], fighter2['fid']))
	for row in query:
		fighter2['nc'] =row[0]

	event_list1 = []
	event_list2 = []
	rank_list1 = []
	rank_list2 = []

	show_f1_match = False
	show_f2_match = False

	f1_ename = None
	f2_ename = None
	f1_loc = None
	f2_loc = None
	f1_opp = None
	f2_opp = None
	f1_res = None
	f2_res = None

	f1_rnum = []
	f1_f1s = []
	f1_f1k = []
	f1_f1t = []
	f1_f1sub = []
	f1_f2s = []
	f1_f2k = []
	f1_f2t = []
	f1_f2sub = []

	swap = True
	selection = request.form.get('select_event1')
	prev_event1 = selection
	if selection and (prev_fid1 == fighter1['fid']):
		tok = str(selection).split(".")[0]
		eid = f1_eid_dict[tok]
		mid = f1_mid_dict[tok]
		f1_fid = fighter1['fid']

		query = g.conn.execute("SELECT e.name, e.location, m.f1_result, m.method, f.lname, f.fname, m.fid1 " \
					"FROM event e, match m, fighter f " \
					"WHERE e.eid = m.eid AND ((m.fid1 = %d AND m.fid2 = f.fid) " \
					"OR (m.fid2 = %d AND m.fid1 = f.fid)) AND m.mid = %d AND m.eid = %d" % \
					(f1_fid, f1_fid, mid, eid))

		show_f1_match = True
		for row in query:
			f1_ename = row['name']
			f1_loc = row['location']
			if row['lname'] and row['fname']:
				f1_opp = "%s, %s" % (row['lname'], row['fname'])
			elif row['lname']:
				f1_opp = row['lname']
			elif row['fname']:
				f1_opp = row['fname']
			else:
				f1_opp = "?"
			result = row['f1_result']
			method = row['method']

			if row['fid1'] == f1_fid:
				swap = False

				if method:
					f1_res = "%s, %s" % (result, method)
				else:
					f1_res = result
			elif result == "win":
				if method:
					f1_res = "loss, %s" % method
			elif result == "draw":
				f1_res = result
			elif method != None:
				f1_res = "no contest, %s" % method
			else:
				f1_res = "no contest"

		# Get round data
		query = g.conn.execute("SELECT * FROM round r WHERE r.eid = %d and r.mid = %d ORDER BY r.round_num" % (eid, mid))
		for row in query:
			f1_rnum.append(row['round_num'])
			f1_f1s.append(row['f1_strikes'])
			f1_f1k.append(row['f1_knockdowns'])
			f1_f1t.append(row['f1_takedowns'])
			f1_f1sub.append(row['f1_sub_att'])
			f1_f2s.append(row['f2_strikes'])
			f1_f2k.append(row['f2_knockdowns'])
			f1_f2t.append(row['f2_takedowns'])
			f1_f2sub.append(row['f2_sub_att'])

		if swap:
			tmp = f1_f1s
			f1_f1s = f1_f2s
			f1_f2s = tmp

			tmp = f1_f1k
			f1_f1k = f1_f2k
			f1_f2k = tmp

			tmp = f1_f1t
			f1_f1t = f1_f2t
			f1_f2t = tmp

			tmp = f1_f1sub
			f1_f1sub = f1_f2sub
			f1_f2sub = tmp

	selection = request.form.get('select_event2')
	prev_event2 = selection

	f2_rnum = []
	f2_f1s = []
	f2_f1k = []
	f2_f1t = []
	f2_f1sub = []
	f2_f2s = []
	f2_f2k = []
	f2_f2t = []
	f2_f2sub = []

	swap = True
	if selection and (prev_fid2 == fighter2['fid']):
		tok = str(selection).split(".")[0]
		eid = f2_eid_dict[tok]
		mid = f2_mid_dict[tok]
		f2_fid = fighter2['fid']
		# query basic match information (location, event, opponent, result)
		query = g.conn.execute("SELECT e.name, e.location, m.f1_result, m.method, f.lname, f.fname, m.fid1 " \
					"FROM event e, match m, fighter f " \
					"WHERE e.eid = m.eid AND ((m.fid1 = %d AND m.fid2 = f.fid) " \
					"OR (m.fid2 = %d AND m.fid1 = f.fid)) AND m.mid = %d AND m.eid = %d" % \
					(f2_fid, f2_fid, mid, eid))
		show_f2_match = True
		for row in query:
			f2_ename = row['name']
			f2_loc = row['location']
			if row['lname'] and row['fname']:
				f2_opp = "%s, %s" % (row['lname'], row['fname'])
			elif row['lname']:
				f2_opp = row['lname']
			elif row['fname']:
				f2_opp = row['fname']
			else:
				f2_opp = "?"
			result = row['f1_result']
			method = row['method']
			if row['fid1'] == f2_fid:
				swap = False
				if method != None:
					f2_res = "%s, %s" % (result, method)
				else:
					f2_res = result
			elif result == "win":
				if method:
					f2_res = "loss, %s" % method
			elif result == "draw":
				f2_res = result
			elif method != None:
				f2_res = "no contest, %s" % method
			else:
				f2_res = "no contest"

		query = g.conn.execute("SELECT * FROM round r WHERE r.eid = %d and r.mid = %d ORDER BY r.round_num" % (eid, mid))
		for row in query:
			f2_rnum.append(row['round_num'])
			f2_f1s.append(row['f1_strikes'])
			f2_f1k.append(row['f1_knockdowns'])
			f2_f1t.append(row['f1_takedowns'])
			f2_f1sub.append(row['f1_sub_att'])
			f2_f2s.append(row['f2_strikes'])
			f2_f2k.append(row['f2_knockdowns'])
			f2_f2t.append(row['f2_takedowns'])
			f2_f2sub.append(row['f2_sub_att'])

		if swap:
			tmp = f2_f1s
			f2_f1s = f2_f2s
			f2_f2s = tmp

			tmp = f2_f1k
			f2_f1k = f2_f2k
			f2_f2k = tmp

			tmp = f2_f1t
			f2_f1t = f2_f2t
			f2_f2t = tmp

			tmp = f2_f1sub
			f2_f1sub = f2_f2sub
			f2_f2sub = tmp

	if show_f1_events:
		query = g.conn.execute("SELECT m.mid, e.eid, e.name, f2.lname " \
					"FROM match m, event e, fighter f, (SELECT fid, lname " \
                                                                           "FROM fighter)f2 " \
                                        "WHERE m.eid = e.eid AND " \
                                              "((m.fid1 = f.fid AND m.fid2 = f2.fid) OR " \
                                              "(m.fid1 = f2.fid AND m.fid2 = f.fid)) AND " \
                                              "f.fid = %d " \
                                        "GROUP BY e.eid, e.name, m.mid, f2.lname " \
                                        "ORDER BY e.eid, e.name, m.mid" % fighter1['fid'])

		f1_eid_dict.clear()
		f1_mid_dict.clear()
		i = 1
		for row in query:
			f1_eid_dict[str(i)] = row['eid']
			f1_mid_dict[str(i)] = row['mid']
			event_list1.append("%d. %s - vs %s" % (i, row['name'], row['lname']))
			i += 1

	if show_f2_events:
		query = g.conn.execute("SELECT m.mid, e.eid, e.name, f2.lname " \
					"FROM match m, event e, fighter f, (SELECT fid, lname " \
                                                                           "FROM fighter)f2 " \
                                        "WHERE m.eid = e.eid AND " \
                                              "((m.fid1 = f.fid AND m.fid2 = f2.fid) OR " \
                                              "(m.fid1 = f2.fid AND m.fid2 = f.fid)) AND " \
                                              "f.fid = %d " \
                                        "GROUP BY e.eid, e.name, m.mid, f2.lname " \
                                        "ORDER BY e.eid, e.name, m.mid" % fighter2['fid'])
		f2_eid_dict.clear()
		f2_mid_dict.clear()
		i = 1
		for row in query:
			f2_mid_dict[str(i)] = row['mid']
			f2_eid_dict[str(i)] = row['eid']
			event_list2.append("%d. %s - vs %s" % (i, row['name'], row['lname']))
			i += 1

	if show_f1_ranks:
		query = g.conn.execute("SELECT w.name, r.rank " \
					"FROM ranking r, fighter f, weightclass w " \
					"WHERE f.fid = r.fid AND r.wid = w.wid " \
					"AND f.fid = %d" % fighter1['fid'])
		for row in query:
			if row['rank'] != None:
				rank_list1.append("#%d %s" % (row['rank'], row['name']))
			else:
				rank_list1.append(row['name'])

	if show_f2_ranks:
		query = g.conn.execute("SELECT w.name, r.rank " \
					"FROM ranking r, fighter f, weightclass w " \
					"WHERE f.fid = r.fid AND r.wid = w.wid " \
					"AND f.fid = %d" % fighter2['fid'])
		for row in query:
			if row['rank'] != None:
				rank_list2.append("#%d %s" % (row['rank'], row['name']))
			else:
				rank_list2.append(row['name'])

	query = g.conn.execute("SELECT eid, mid, result_rnd, result_time "\
				"FROM match " \
				"GROUP BY eid, mid, result_rnd, result_time "\
				"ORDER BY eid, mid")
	query.close()

	prev_fid1 = fighter1['fid']
	prev_fid2 = fighter2['fid']

	guesstimation = predict_result(prev_fid1, prev_fid2)
	guess = None
	if guesstimation < 0:
		guess = "WINNER ->\n%s %s" % (fighter2['fname'], fighter2['lname'])
	elif guesstimation > 0:
		guess = "<- WINNER\n%s %s" % (fighter1['fname'], fighter1['lname'])
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
				f1_event_name = f1_ename,
				f2_event_name = f2_ename,
				f1_location = f1_loc,
				f2_location = f2_loc,
				f1_opponent = f1_opp,
				f2_opponent = f2_opp,
				f1_result = f1_res,
				f2_result = f2_res,
				f1_events_list=event_list1,
				f2_events_list=event_list2,
				f1_ranks=show_f1_ranks,
				f2_ranks=show_f2_ranks,
				f1_rank_list=rank_list1,
				f2_rank_list=rank_list2,

				f1_rd_nums=f1_rnum,
				f1_f1_s=f1_f1s,
				f1_f1_k=f1_f1k,
				f1_f1_t=f1_f1t,
				f1_f1_sub=f1_f1sub,
				f1_f2_s=f1_f2s,
				f1_f2_k=f1_f2k,
				f1_f2_t=f1_f2t,
				f1_f2_sub=f1_f2sub,

				f2_rd_nums=f2_rnum,
				f2_f1_s=f2_f1s,
				f2_f1_k=f2_f1k,
				f2_f1_t=f2_f1t,
				f2_f1_sub=f2_f1sub,
				f2_f2_s=f2_f2s,
				f2_f2_k=f2_f2k,
				f2_f2_t=f2_f2t,
				f2_f2_sub=f2_f2sub,

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


def predict_result(fid1, fid2):
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




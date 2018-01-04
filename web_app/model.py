import pandas as pd

from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, ForeignKey
from sqlalchemy import insert, select, case, cast, Float
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response



# Connect to POSTGRESQL database
def connect(user, password, db, host='xx.xxx.xx.xxx', port='xxxx'):
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


def get_stats(fid):
	fighter_data = pd.read_sql(
	    """
	    SELECT t1.fid1,
	            COALESCE(t8.age, 32) as age,
	            COALESCE(t8.height, 70) as height,
	            COALESCE(t8.weight, 200) as weight,
	            COALESCE(t7.win_per, 0.50) as win_per,
	            COALESCE(t7.loss_per, 0.50) as loss_per,
	            COALESCE(t5.avg_rds, 1) as avg_rds,
                COALESCE(t6.avg_fight_time, '00:00:00') as avg_fight_time,
	            COALESCE(ROUND((CAST(t1.tko as FLOAT)/t4.wins)::numeric,2),0.00) AS tko_per, 
	            COALESCE(ROUND((CAST(t2.submission as FLOAT)/t4.wins)::numeric,2),0.00) AS subm_per, 
	            COALESCE(ROUND((CAST(t3.ko as FLOAT)/t4.wins)::numeric,2),0.00) AS ko_per
	    FROM (SELECT fid1, COUNT(method) as tko 
	            FROM match 
	            WHERE f1_result='win' AND method='TKO' 
	            GROUP BY fid1) t1
	                LEFT OUTER JOIN
	        (SELECT fid1, COUNT(method) as submission 
	            FROM match 
	            WHERE f1_result='win' AND method='Submission' 
	            GROUP BY fid1) t2 ON t2.fid1=t1.fid1
	                LEFT OUTER JOIN
	        (SELECT fid1, COUNT(method) as ko 
	            FROM match 
	            WHERE f1_result='win' AND method='KO' 
	            GROUP BY fid1) t3 ON t3.fid1=t1.fid1
	                LEFT OUTER JOIN
	        (SELECT fid1, COUNT(f1_result) AS wins    
	            FROM match
	            WHERE f1_result='win'
	            GROUP BY fid1) t4 ON t4.fid1=t1.fid1 
	                LEFT OUTER JOIN
	        (SELECT t1.fid1, 
	                (t1.tot_rnds+t2.tot_rnds) as tot_rnds, 
	                (t1.cnt+t2.cnt) as tot_fights, 
	                ((t1.tot_rnds+t2.tot_rnds)/(t1.cnt+t2.cnt)) as avg_rds
	            FROM (SELECT fid1, SUM(result_rnd) as tot_rnds, COUNT(fid1) as cnt 
	                    FROM match 
	                    GROUP BY fid1) t1
	                JOIN
	                (SELECT fid2, SUM(result_rnd) as tot_rnds, COUNT(fid2) as cnt 
	                    FROM match 
	                    GROUP BY fid2) t2 ON t1.fid1=t2.fid2
	            GROUP BY t1.fid1, t1.tot_rnds, t2.tot_rnds, t1.cnt, t2.cnt) t5 ON t5.fid1=t1.fid1
	                LEFT OUTER JOIN
	        (SELECT t1.fid1, 
	                (t1.tot_time+t2.tot_time) as tot_time, 
	                (t1.cnt+t2.cnt) as tot_fights, 
	                ((t1.tot_time+t2.tot_time)/(t1.cnt+t2.cnt)) as avg_fight_time
	            FROM (SELECT fid1, SUM(result_time) as tot_time, COUNT(fid1) as cnt 
	                    FROM match 
	                    GROUP BY fid1) t1
	                JOIN
	                (SELECT fid2, SUM(result_time) as tot_time, COUNT(fid2) as cnt 
	                    FROM match 
	                    GROUP BY fid2) t2 ON t1.fid1=t2.fid2
	            GROUP BY t1.fid1, t1.tot_time, t2.tot_time, t1.cnt, t2.cnt) t6 ON t6.fid1=t1.fid1         
	                LEFT OUTER JOIN
	        (SELECT t3.fid1, 
	                t1.wins, 
	                t2.losses, 
	                (t3.total::int), 
	                ROUND((t1.wins/t3.total)::numeric,3) AS win_per, 
	                ROUND((t2.losses/t3.total)::numeric,3) AS loss_per
	            FROM (SELECT fid2, COUNT(fid2) AS losses 
	                    FROM match 
	                    WHERE f1_result='win' 
	                    GROUP BY fid2) t2 
	                JOIN
	                (SELECT fid1, COUNT(f1_result) AS wins 
	                    FROM match 
	                    GROUP BY fid1) t1 ON t2.fid2=t1.fid1
	                    JOIN
	                (SELECT fid1, SUM(t1.wins + t2.losses) AS total
	                    FROM (SELECT fid2, COUNT(fid2) AS losses 
	                            FROM match 
	                            WHERE f1_result='win' 
	                            GROUP BY fid2) t2,
	                (SELECT fid1, COUNT(f1_result) AS wins 
	                    FROM match 
	                    GROUP BY fid1) t1 
	                    WHERE t2.fid2=t1.fid1
	                    GROUP BY fid1) t3 ON t3.fid1=t1.fid1
	            GROUP BY t3.fid1, t1.wins, t3.total, t2.losses) t7 ON t7.fid1=t1.fid1
	                LEFT OUTER JOIN
	        (SELECT fid, EXTRACT(YEAR from AGE(dob)) as age, height, weight 
	            FROM fighter) t8 ON t8.fid=t1.fid1
        WHERE t1.fid1={}
	    """.format(fid), con=conn)
	return fighter_data


def predict_winner(fid1, fid2):
    

    fighter_1 = get_stats(fid1)
    fighter_2 = get_stats(fid2)
    diff = fighter_1.subtract(fighter_2)

    fighter1_score = 0
    fighter2_score = 0
    
    #Fighter1 is younger +1
    if int(diff['age']) < 0:
        fighter1_score = fighter1_score + 1

    #Fighter1 is taller +1   
    if int(diff['height']) > 0:
        fighter1_score = fighter1_score + 1

    #Fighter1 is heavier + 1    
    if int(diff['weight']) > 0:
        fighter1_score = fighter1_score + 1

    #Fighter1 has better win% + 1, else Fighter2 + 1 <=> greater   
    if float(diff['win_per']) > 0:
        fighter1_score = fighter1_score + 1
        if float(diff['win_per']) < 0:
            fighter2_score = fighter2_score + 1

    #Fighter1 takes more rds to win so Fighter2 more efficient at winning +1
    if int(diff['avg_rds']) > 0:
        fighter2_score = fighter2_score + 1

    #Fighter1 KOs more so +3
    if float(diff['ko_per']) > 0:
        fighter1_score = fighter1_score + 3
        if float(diff['ko_per']) < 0:
            fighter2_score = fighter2_score + 3

    #Fighter1 TKOs more so +2
    if float(diff['tko_per']) > 0:
        fighter1_score = fighter1_score + 2
        if float(diff['tko_per']) < 0:
            fighter2_score = fighter2_score + 2

    #Fighter1 Submissions more so +1
    if float(diff['tko_per']) > 0:
        fighter1_score = fighter1_score + 1
        if float(diff['tko_per']) < 0:
            fighter2_score = fighter2_score + 1

    total_score = fighter1_score + fighter2_score
    fighter1_prob = fighter1_score/total_score
    fighter2_prob = fighter2_score/total_score
    
    return fighter1_score, fighter2_score, fighter1_prob, fighter2_prob


fighter1_score, fighter2_score, fighter1_prob, fighter2_prob = predict_winner(8,14)

#print(fighter1_score)
#print(fighter2_score)
#print(fighter1_prob)
#print(fighter2_prob)

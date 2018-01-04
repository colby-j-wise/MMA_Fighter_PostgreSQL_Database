PostgreSQL Account: #####
Team: Colby Wise & Dallas Jones

# MMA Fighter PostgreSQL Database
## PROJECT OVERVIEW

The goal of this project was to create a web app with a PostgreSQL backend with emphasis placed on design and architecture
of the DB. The two main constraints were that we had to construct the database from scratch; and secondly, we were given
only ~4 days to complete the project given a shortened course schedule. Hence functionality was higher priority than
perfecting code quality and aesthetic design of the web app is at a minimum!  

### WEB APP OVERVIEW

The web app was hosted on local Columbia shared server. Hence to actually run the web app you'd need to copy the DB schema
into your own PostgreSQL DB host on a remote server. From there modifying the web app src is straight forward. The web
app lets you view fight statistics on MMA fighters such as height, weight, prev matches, win %, etc. Then using
a trivial algorithm predicts which fighter would win in a head to head match up. 

Future work would include implementing a non-trivial algorithm for statistically predicting win likelihood between two fighters.

### DESCRIPTION OF DATABASE DESIGN

1. COMPOSITE TYPE "income_source" - In the update schema we created a composite type call income_source which essentially takes a tuple of (company name [text], description [text], and money [numeric]). We use this composite type in a new table called "Endorsements" which basically keeps track of the endorsement money that the top fighters receive per company - i.e. Connor McGregor receives $1,000,000 in endorsements from Reebok as part of a merchandising deal. Again, this is used in a new table called Endorsements; also if a fighter is deleted their endorsements are deleted. 

2. Attribute Array Type - We added an array type attribute to the existing table called "Match", which holds the fighter match data per UFC event. The new array column called "prize_money" stores an array of two numeric values representing the fighter prize (purse) money for the match. The first value coincides with the prize money for fighter1, and the second value is the prize money for fighter2 respectively. Users can then query our database to get an idea for the total dollar winnings are fighter made for a particular match(s) or their total career winnings.

3. Text Attribute/Full Text Search - Logically, given our data boils down to fighters, events, and matches we added a text attribute to the table "Match" that provides a short paragraph summary of the match details - called "match_recap". This essentially gives users a quick blurp on what happened in a specific match. Users can then search for a particular recap from a fight or all recaps of their favorite fighters!

SQL QUERIES 

1. Returns the first name, last name, event details (name/location/date), match number, and prize money for the fighter with the maximum prize money out all matches in the database. Ties included. 

SELECT fname, lname, e.name as UFC_event, e.location, e.date, m.mid as match_num, m.prize_money[1] 
FROM fighter f 
JOIN match m ON f.fid=m.fid1 
JOIN event e ON e.eid=m.eid
WHERE m.prize_money[1]=(SELECT MAX(prize_money[1]) FROM match);

2.  Returns fighter id, first name, last name, endorsement earnings, fight earnings, and total earnings (endorsement + fight) for fighters who have made money from fighting or endorsements or both. 

SELECT temp1.fid, temp1.fname, temp1.lname, (temp1.fight_earnings + temp2.fight_earnings) as fight_earnings, temp3.endorsements, (temp1.fight_earnings + temp2.fight_earnings + temp3.endorsements) as total_earnings
FROM (
		SELECT fid, fname, lname, (COALESCE(t1.sum,0)) as fight_earnings                 
		FROM fighter f
		FULL JOIN                                                               
		(SELECT m.fid1, COALESCE(SUM(m.prize_money[1]),0) as sum                
		FROM match m
		GROUP BY m.fid1) t1 ON fid=t1.fid1
	) temp1
	FULL JOIN
	(
		SELECT fid, fname, lname, (COALESCE(t2.sum,0)) as fight_earnings                 
		FROM fighter f
		FULL JOIN                                                               
		(SELECT m.fid2, COALESCE(SUM(m.prize_money[2]),0) as sum                
		FROM match m
		GROUP BY m.fid2) t2 ON fid=t2.fid2
	) temp2 ON temp1.fid=temp2.fid
	FULL JOIN
	(
		SELECT f.fid, fname, lname, COALESCE(SUM((income).money),0) as endorsements 
		FROM fighter f 
		FULL JOIN endorsements e ON f.fid=e.fid
		GROUP BY f.fid
	) temp3 ON temp2.fid=temp3.fid
WHERE (temp1.fight_earnings + temp2.fight_earnings + temp3.endorsements) > 0
ORDER BY total_earnings DESC;

3. Full Text Search to return the UFC event info, venue location, and date of all match (recaps) discussing TKOs i.e. if a user missed a specific UFC event and just wants to read about all the matches with TKOs! 

SELECT name, location, date, match_recap
FROM match m, event e
WHERE m.eid=e.eid AND m.eid=47933 AND (to_tsvector('english', match_recap) @@ to_tsquery('english', 'TKO'));

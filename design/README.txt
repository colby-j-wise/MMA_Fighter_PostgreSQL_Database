PostgreSQL Account: DRJ2115
Team: Colby Wise (CJW2165) & Dallas Jones (DRJ2115)


DESCRIPTION OF DESIGN

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

SELECT f.fid, f.fname, f.lname, temp.endorsements, temp.fight_earnings, (temp.endorsements+temp.fight_earnings) as total_earnings
FROM fighter f JOIN
(SELECT t2.fid2, COALESCE(t1.endorsements,0) as endorsements, COALESCE(t2.fight_earnings,0) as fight_earnings
FROM (SELECT f.fid, f.fname, COALESCE(SUM((income).money),0) as endorsements 
		FROM fighter f RIGHT OUTER JOIN endorsements e ON f.fid=e.fid
		GROUP BY f.fid, f.fname) t1
	RIGHT OUTER JOIN 
		(SELECT fid2, (COALESCE(m1_sum,0)+COALESCE(m2_sum,0)) as fight_earnings
		FROM (SELECT fid1, SUM(m.prize_money[1]) as m1_sum
				FROM match m
				WHERE m.prize_money[1] IS NOT NULL
				GROUP BY fid1) m1
	RIGHT OUTER JOIN 	
		(SELECT fid2, SUM(m.prize_money[2]) as m2_sum
			FROM match m
			WHERE m.prize_money[2] IS NOT NULL
			GROUP BY fid2) m2 ON m1.fid1=m2.fid2
		) t2 ON t1.fid=t2.fid2
GROUP BY t2.fid2, t1.endorsements, t2.fight_earnings) temp ON f.fid=temp.fid2







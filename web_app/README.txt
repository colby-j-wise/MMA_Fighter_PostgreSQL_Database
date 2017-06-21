PostgreSQL Account: drj2115
Application URL: http://<IP ADDRESS>:8111/

Description of App:
	The application allows you to view numerous statistics on Mixed-Martial Arts (MMA) fighters.
	All features from the proposal were successfully implemented, namely:
		1. Users can select fighters and get back statistics such as age, weight, nationality,
			win/loss record, and opponents.
		2. Users can view match and event history per fighter by selecting the fighter then 
			choosing a specific event users get back detailed match history and round data
		3. Predicting fight odds:
			a. By choosing two fighters and selecting the "odds" button the prediction 
				algorithm assigns weights based on the differences in fighter statistics
				such as [age difference], [win/loss records], [height difference], etc
				to determine which fighter would win a fight between them.

Most Interesting Web Pages:
	The most interesting page is the fighter prediction pages. In order to calculate the core 
	statistics used in the prediction algorithm we perform a series of joins on almost every 
	relation in the database. Moreover, within each joined relation there is one or
	two subqueries that are running to calculate things such as [average round per fight per fighter],
	[percentage of TKOs, KOs, Submissions per fighter], etc. Furthermore, as with all real-world
	data some of it is missing or incomplete. For each returned value, if the value is Null
	we use the SQL "COALESCE" function to fill in missing values with the average for that statistic 
	for all fighters. And finally, we calculate the differences between fighters for each returned
	statistic and plug these metrics into a simple prediction algorithm that weights these
	differences to score each fighter and return the fighter with the greater score. 
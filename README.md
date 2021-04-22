# KnowledgeRepo
A free platform for adding, eding and deleting articles. For soulful sharing of knowledge. 

-	This application is for free sharing of knowledge.
-	How to get it running.
o	app.py is the main file, after all the configurations are completed run 
python app.py

o	first install all the requirements for that type command
pip install -r requirements.txt

o	log in to your mysql using the command
mysql -u root -p

o	create database and table using commands.
CREATE DATABASE mywikiapp;

CREATE TABLE users(id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), email VARCHAR(100), username VARCHAR(30), password VARCHAR(100), register_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, role VARCHAR(50));

CREATE TABLE articles(id INT AUTO_INCREMENT PRIMARY KEY, title VARCHAR(100), author VARCHAR(100), body TEXT, create_date TIMESTAMP CURRENT_TIMESTAMP, status VARCHAR(30));

CREATE TABLE edits(username VARCHAR(100), article VARCHAR(50), edit_date TIMESTAMP CURRENT_TIMESTAMP);

o	Change the values of, in app.py

app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
 
enter the value of the password that you used to enter mysql root console.

o	Run the application using command 
Python app.py

o	Hurray the application is app and running in
localhost:5000

Thank you.

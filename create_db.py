import sqlite3

connection=sqlite3.connect('database.db')
cursor=connection.cursor()

cursor.execute('DROP TABLE IF EXISTS visits;')
cursor.execute("CREATE TABLE visits(VisitID INTEGER PRIMARY KEY AUTOINCREMENT, Timestamp TEXT)")

connection.commit()
connection.close()
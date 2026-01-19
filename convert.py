import mysql.connector
import sqlite3
import pandas as pd

# Connect to your local MySQL
mysql_conn = mysql.connector.connect(
    host='localhost', user='root', password='root', database='university_exams_db'
)

# Create the new SQLite file
sqlite_conn = sqlite3.connect('university.db')

tables = ['departements', 'lieux_examen', 'professeurs', 'formations', 
          'modules', 'etudiants', 'examens', 'surveillances', 'inscriptions']

print("Converting database...")
for table in tables:
    print(f"--> Copying {table}...")
    try:
        df = pd.read_sql(f"SELECT * FROM {table}", mysql_conn)
        df.to_sql(table, sqlite_conn, if_exists='replace', index=False)
    except Exception as e:
        print(f"Error on {table}: {e}")

print("DONE. 'university.db' is ready.")
mysql_conn.close()
sqlite_conn.close()
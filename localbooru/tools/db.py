import sqlite3
import os
import threading
from contextlib import contextmanager

DATABASES = ['main', 'cache', 'prefs']

MAIN_DB_SCHEMA = '''
PRAGMA synchronous = FULL;
CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, website TEXT, origid INTEGER, creation_date datetime DEFAULT NULL, md5 BLOB(32) NOT NULL, image VARCHAR(255) DEFAULT NULL, height INTEGER unsigned default '0', width INTEGER, unsigned default '0', ext varchar(10) DEFAULT NULL, rating text, tags text NOT NULL);
'''

CACHE_DB_SCHEMA = '''
PRAGMA synchronous = OFF
CREATE TABLE IF NOT EXISTS thumbnails (md5 BLOB(16) PRIMARY KEY, imgdata BLOB);
'''

PREFS_DB_SCHEMA = '''
PRAGMA synchronous = FULL;
CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT);
'''


class SerializedConnection:
	'''
	connection = SerializedConnection("db.sqlite")
	with connection.get() as conn, conn: #will automatically commit (or rollback on error)
		cur = conn.cursor()
		cur.execute('INSERT INTO y(x) VALUES (?)', (1,))
	with connection.get() as conn:
		cur = conn.cursor()
		cur.execute('SELECT x FROM y')
		data = cur.fetchall()
	'''
	def __init__(self, filename):
		self.conn = sqlite3.connect(filename, check_same_thread=False)
		self.lock = threading.Lock()
	
	@contextmanager
	def get(self):
		self.lock.acquire()
		try:
			yield self.conn
		finally:
			self.lock.release()

	def close(self):
		self.conn.close()

class LocalbooruDB:
	def __init__(self, database_directory):
		self._conns = []
		for db in DATABASES:
			serconn = SerializedConnection(os.path.join(database_directory, db + '.sqlite3'))
			with serconn.get() as conn, conn:
				cur = conn.cursor()
				for statement in globals()[db.upper() + '_DB_SCHEMA'].splitlines():
					if statement:
						cur.execute(statement)
			self._conns.append(serconn)
			setattr(self, db, serconn)
	def close(self):
		for serconn in self._conns:
			serconn.close()
			

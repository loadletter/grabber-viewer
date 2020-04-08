import sqlite3
import os
import threading
import cherrypy
from contextlib import contextmanager

DATABASES = ['metadata', 'thumb', 'cache']

METADATA_DB_SCHEMA = '''
CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, website TEXT, origid INTEGER, creation_date datetime DEFAULT NULL, hash text NOT NULL, image VARCHAR(255) DEFAULT NULL, height INTEGER unsigned default '0', width INTEGER unsigned default '0', ext varchar(10) DEFAULT NULL, rating text, tags text NOT NULL);
'''

THUMB_DB_SCHEMA = '''
PRAGMA synchronous = OFF
CREATE TABLE IF NOT EXISTS thumbnails (md5 TEXT PRIMARY KEY, imgdata BLOB);
'''

CACHE_DB_SCHEMA = '''
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, website TEXT, origid INTEGER, creation_date datetime DEFAULT NULL, hash BLOB(16) NOT NULL, image VARCHAR(255) DEFAULT NULL, rating text);
CREATE TABLE IF NOT EXISTS tags (id INTEGER PRIMARY KEY, name TEXT, type TEXT, UNIQUE(name, type) ON CONFLICT ABORT);
CREATE TABLE IF NOT EXISTS tagmap (post INTEGER, tag INTEGER, PRIMARY KEY (post, tag), FOREIGN KEY (post) references posts(id) ON DELETE CASCADE, FOREIGN KEY (tag) references tags(id) ON DELETE CASCADE);
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
		cherrypy.log("Initializing...", context='DATABASE')
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
		cherrypy.log("Closing connections", context='DATABASE')
		for serconn in self._conns:
			serconn.close()
		cherrypy.log("Connections closed", context='DATABASE')

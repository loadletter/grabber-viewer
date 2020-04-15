import sqlite3
import os
import threading
import binascii
import cherrypy
from contextlib import contextmanager

from localbooru.settings import IMAGE_NAME_FUNC
from . settings import image_dir

DATABASES = ['metadata', 'thumb', 'cache']

METADATA_DB_SCHEMA = '''
CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, website TEXT, origid INTEGER, creation_date datetime DEFAULT NULL, hash text NOT NULL, image VARCHAR(255) DEFAULT NULL, height INTEGER unsigned default '0', width INTEGER unsigned default '0', ext varchar(10) DEFAULT NULL, rating text, tags text NOT NULL);
'''

THUMB_DB_SCHEMA = '''
PRAGMA synchronous = OFF
CREATE TABLE IF NOT EXISTS thumbnails (md5 BLOB(16) PRIMARY KEY, imgdata BLOB);
'''

CACHE_DB_SCHEMA = '''
PRAGMA synchronous = OFF
CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, website TEXT, origid INTEGER, creation_date datetime DEFAULT NULL, hash BLOB(16) UNIQUE NOT NULL, image VARCHAR(255) DEFAULT NULL, rating text, height INTEGER unsigned default '0', width INTEGER unsigned default '0');
CREATE TABLE IF NOT EXISTS tags (id INTEGER PRIMARY KEY, name TEXT, type TEXT, UNIQUE(name, type) ON CONFLICT ABORT);
CREATE TABLE IF NOT EXISTS tagmap (post INTEGER, tag INTEGER, PRIMARY KEY (post, tag));
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

	def gencache(self):
		generate_cache(self.metadata, self.cache)
	



def generate_cache(inputdb, outputdb):
	data = []
	missing = 0
	inputrow = 0
	insertrow = 0
	existingrow = 0
	cherrypy.log("Generating cache", context='DATABASE')
	with inputdb.get() as conn, conn:
		cur = conn.cursor()
		cur.execute('SELECT id, website, origid, creation_date, hash, image, width, height, rating, tags FROM posts ORDER BY id DESC')
		for row in cur:
			inputrow += 1
			subpath = IMAGE_NAME_FUNC(row[5])
			post = row[0:4] + (binascii.a2b_hex(row[4]), subpath) + row[6:9]
			if not os.path.exists(os.path.join(image_dir, subpath)):
				missing +=1
				continue
			tags = []
			tlist = row[9].strip().split()
			for tag in tlist:
				tags.append(('', tag))
			data.append((post, tags))
			
		cherrypy.log("Metadata size: %i   Found files: %i   Missing files: %i" % (inputrow, inputrow - missing, missing), context='CACHE')
	
	tagmap = []
	for d in data:
		with outputdb.get() as conn, conn:
			cur = conn.cursor()
			cur.execute('INSERT OR IGNORE INTO posts(id, website, origid, creation_date, hash, image, width, height, rating) VALUES (?,?,?,?,?,?,?,?,?)', d[0])
			if not cur.lastrowid:
				existingrow += 1
				continue
			postid = d[0][0]
			
			md5 = binascii.b2a_hex(d[0][4]).decode('ascii')
			if md5 in tagdict:
				tagsrc = tagdict[md5]
			else:
				tagsrc = d[1]
				
			cur.executemany('INSERT OR IGNORE INTO tags(type, name) VALUES (?,?)', tagsrc)
			for t in tagsrc:
				cur.execute('SELECT id FROM tags WHERE type = ? AND name = ?', t)
				res = cur.fetchone()
				if res:
					tagmap.append((postid, res[0]))
			insertrow += 1
	with outputdb.get() as conn, conn:
		cur = conn.cursor()
		cur.executemany('INSERT OR IGNORE INTO tagmap(post, tag) VALUES (?,?)', tagmap)
		
	cherrypy.log("Cache generated:  Inserted: %i   Dup: %i" % (insertrow, existingrow), context='CACHE')

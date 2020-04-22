import sqlite3
import os
import threading
import binascii
import cherrypy
from contextlib import contextmanager

from localbooru.settings import IMAGE_NAME_FUNC
from . settings import image_dir, tags_dir

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
CREATE INDEX IF NOT EXISTS tagmap_post_index ON tagmap (post);
CREATE INDEX IF NOT EXISTS tagmap_tag_index ON tagmap (tag);
CREATE INDEX IF NOT EXISTS tag_name_index ON tags (name);
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
	def __init__(self, filename, isol_level=None):
		self.conn = sqlite3.connect(filename, check_same_thread=False, isolation_level=isol_level)
		self.lock = threading.Lock()
	
	@contextmanager
	def get(self):
		self.lock.acquire()
		try:
			yield self.conn
			self.conn.commit()
		except sqlite3.Error:
			self.conn.rollback()
			raise
		finally:
			self.lock.release()

	def close(self):
		self.conn.close()

class LocalbooruDB:
	def __init__(self, database_directory):
		self._conns = []
		cherrypy.log("Initializing...", context='DATABASE')
		for db in DATABASES:
			serconn = SerializedConnection(os.path.join(database_directory, db + '.sqlite3'), 'DEFERRED')
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
	

def generate_tag_types():
	tags_f = "tags.txt"
	tagtype_f = "tag-types.txt"
	cherrypy.log("Loading tags", context='TAGLOAD')
	dirlist = os.listdir(tags_dir)
	dirlist.sort(reverse=True)
	tags = {}
	for d in dirlist:
		tagtypes = {}
		tagcount = 0
		fn = os.path.join(tags_dir, d)
		if not (os.path.isdir(fn) and os.path.isfile(os.path.join(fn, tags_f)) and os.path.isfile(os.path.join(fn, tagtype_f))):
			cherrypy.log("Invalid tag directory %s" % d, context='TAGLOAD')
			continue
		with open(os.path.join(fn, tagtype_f),'r') as f:
			for line in f:
				spl = line.strip().split(',', 1)
				if len(spl) == 2:
					tagtypes[spl[0]] = spl[1]
		with open(os.path.join(fn, tags_f),'r') as f:
			for line in f:
				spl = line.strip().rsplit(',', 1)
				if len(spl) == 2 and spl[1] in tagtypes:
					tags[spl[0]] = tagtypes[spl[1]]
					tagcount += 1
		cherrypy.log("Loaded tags from %s: %i" % (d, tagcount), context='TAGLOAD')
	return tags

def generate_cache(inputdb, outputdb):
	data = []
	missing = 0
	inputrow = 0
	insertrow = 0
	existingrow = 0
	duprow = 0
	tag_types = generate_tag_types()
	cherrypy.log("Loading", context='CACHE')
	with outputdb.get() as conn, conn:
		cur = conn.cursor()
		cur.execute('SELECT id FROM posts')
		outputexisting = set(map(lambda x: x[0], cur))
	cherrypy.log("Existing: %i" % len(outputexisting), context='CACHE')
	hashdedup = set()
	with inputdb.get() as conn, conn:
		cur = conn.cursor()
		cur.execute('SELECT id, website, origid, creation_date, hash, image, width, height, rating, tags FROM posts ORDER BY id DESC')
		for row in cur:
			inputrow += 1
			if row[4] in hashdedup:
				continue
			hashdedup.add(row[4])
			if row[0] in outputexisting:
				existingrow +=1
				continue
			subpath = IMAGE_NAME_FUNC(row[5])
			post = row[0:4] + (binascii.a2b_hex(row[4]), subpath) + row[6:9]
			if not os.path.exists(os.path.join(image_dir, subpath)):
				missing +=1
				continue
			tags = []
			tlist = row[9].strip().split()
			for tag in tlist:
				if tag in tag_types:
					tagt = tag_types[tag]
				else:
					tagt = ''
				tags.append((tagt, tag))
			data.append((post, tags))
		cherrypy.log("Metadata: %i  Unique: %i  Skipped: %i  Found files: %i  Missing files: %i" % (inputrow, len(hashdedup), existingrow, len(hashdedup) - missing, missing), context='CACHE')
	
	tagmap = []

	with outputdb.get() as conn, conn:
		cur = conn.cursor()
		for d in data:
			cur.execute('INSERT OR IGNORE INTO posts(id, website, origid, creation_date, hash, image, width, height, rating) VALUES (?,?,?,?,?,?,?,?,?)', d[0])
			if not cur.lastrowid:
				duprow += 1
			postid = d[0][0]

			tagsrc = d[1]
			cur.executemany('INSERT OR IGNORE INTO tags(type, name) VALUES (?,?)', tagsrc)
			for t in tagsrc:
				cur.execute('SELECT id FROM tags WHERE type = ? AND name = ?', t)
				res = cur.fetchone()
				if res:
					tagmap.append((postid, res[0]))
			insertrow += 1

		cur.executemany('INSERT OR IGNORE INTO tagmap(post, tag) VALUES (?,?)', tagmap)
		
	cherrypy.log("Generated: Inserted: %i  Dup: %i" % (insertrow - duprow, duprow), context='CACHE')

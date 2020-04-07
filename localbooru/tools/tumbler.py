import multiprocessing
import signal
import sqlite3
import io
import cherrypy

from PIL import Image

THUMB_SIZE = (150, 150)

def img_thumb(src_file):
	img = Image.open(src_file)
	img.thumbnail(THUMB_SIZE)
	stream = io.BytesIO()
	img.save(stream, format='JPEG')
	return stream.getvalue()

def thumb_worker(queue, db_filename, workernum=None):
	signal.signal(signal.SIGINT, signal.SIG_IGN)
	while True:
		qdata = queue.get()
		if len(qdata) != 2:
			break
		md5, src_file = qdata
		data = None
		with sqlite3.connect(db_filename) as conn:
			cur = conn.execute('SELECT md5 FROM thumbnails WHERE md5 = ?', (md5,))
			data = cur.fetchone()
		if data:
			continue
		
		thumb = img_thumb(src_file)
		
		with sqlite3.connect(db_filename) as conn:
			conn.execute('INSERT OR IGNORE INTO thumbnails(md5, imgdata) VALUES (?,?)', (md5, thumb))
		
class ThumbNailer:
	def __init__(self, db_filename):
		self.num_procs = multiprocessing.cpu_count()
		self.queue = multiprocessing.Queue(self.num_procs * 10)
		for i in range(self.num_procs):
			p = multiprocessing.Process(target=thumb_worker, args=(self.queue, db_filename, i))
			p.daemon = True
			p.start()
		
	def create(self, ascii_md5, source_file):
		self.queue.put((ascii_md5, source_file))

	def stop(self):
		for i in range(self.num_procs):
			self.queue.put((None,))
		

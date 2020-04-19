import multiprocessing
import subprocess
import signal
import sqlite3
import io
import os
import cherrypy

from PIL import Image
from tempfile import mktemp

from . settings import image_dir
from . common import is_image

THUMB_SIZE = (150, 150)

def img_thumb(src_file):
	img = Image.open(src_file)
	if img.mode != 'RGB':
		img = img.convert('RGB')
	img.thumbnail(THUMB_SIZE)
	stream = io.BytesIO()
	img.save(stream, format='JPEG')
	return stream.getvalue()

def video_thumb(src_file):
	outfile = mktemp(suffix='.jpg')
	call_args = ['ffmpeg', '-hide_banner', '-loglevel', 'warning', '-y', '-i', src_file, '-ss', '00:00:00.000', '-vframes', '1', outfile]
	subprocess.call(call_args)
	with open(outfile, 'rb') as f:
		thumb = img_thumb(outfile)
	os.unlink(outfile)
	return thumb

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
		
		try:
			if is_image(src_file):
				thumb = img_thumb(src_file)
			else:
				thumb = video_thumb(src_file)
			with sqlite3.connect(db_filename) as conn:
				conn.execute('INSERT OR IGNORE INTO thumbnails(md5, imgdata) VALUES (?,?)', (md5, thumb))
		except Exception as e:
			cherrypy.log("Exception on file %s : %s" % (src_file, e), context='THUMB')
			continue
		
class ThumbNailer:
	def __init__(self, db_filename):
		self.num_procs = multiprocessing.cpu_count() * 2
		self.queue = multiprocessing.Queue(self.num_procs * 10)
		for i in range(self.num_procs):
			p = multiprocessing.Process(target=thumb_worker, args=(self.queue, db_filename, i))
			p.daemon = True
			p.start()
		
	def create(self, md5, source_file):
		self.queue.put((md5, os.path.join(image_dir, source_file)))

	def stop(self):
		for i in range(self.num_procs):
			self.queue.put((None,))

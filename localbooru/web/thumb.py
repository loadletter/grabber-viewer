import cherrypy
import io
import binascii
import time

class ThumbServer:	
	@cherrypy.expose
	def index(self, md5):
		img_data = None
		bin_md5 = binascii.a2b_hex(md5)
		
		for _ in range(5):
			with cherrypy.tools.db.thumb.get() as conn, conn:
				cur = conn.execute('SELECT imgdata FROM thumbnails WHERE md5 = ?', (bin_md5,))
				img_data = cur.fetchone()
				
			if img_data:
				cherrypy.response.headers['Content-Type'] = "image/jpeg"
				return cherrypy.lib.file_generator(io.BytesIO(img_data[0]))
			time.sleep(0.2)
		
		raise cherrypy.HTTPError(status=404)

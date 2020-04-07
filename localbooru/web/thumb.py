import cherrypy
import io

class ThumbServer:	
	@cherrypy.expose
	def index(self, md5):
		img_data = None
		with cherrypy.tools.db.cache.get() as conn, conn:
			cur = conn.execute('SELECT imgdata FROM thumbnails WHERE md5 = ?', (md5,))
			img_data = cur.fetchone()
			
		if img_data:
			cherrypy.response.headers['Content-Type'] = "image/jpeg"
			return cherrypy.lib.file_generator(io.BytesIO(img_data[0]))
		
		raise cherrypy.HTTPError(status=404)

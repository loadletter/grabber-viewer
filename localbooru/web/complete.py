import cherrypy

from . templates import jinja_env

class CompletionServer:
	@cherrypy.expose
	@cherrypy.tools.json_out()
	def index(self, **kwargs):
		if not 'tag' in kwargs or not kwargs['tag']:
			return []
		with cherrypy.tools.db.cache.get() as conn, conn:
			cur = conn.execute('SELECT DISTINCT(name) FROM tags WHERE name LIKE ?', (kwargs['tag'] + '%',))
			res = map(lambda x: x[0], cur)
		return list(res)

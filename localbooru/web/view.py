import cherrypy

from . templates import jinja_env

VIEW_QUERY = '''SELECT tags.name AS tag, posts.hash, posts.image
FROM tagmap 
JOIN posts ON post = posts.id
JOIN tags ON tag = tags.id
WHERE posts.id = ?
ORDER BY posts.id'''

class ViewServer:
	@cherrypy.expose
	def index(self, id):
		img = {}
		with cherrypy.tools.db.cache.get() as conn, conn:
			cur = conn.execute(VIEW_QUERY, (id,))
			res = cur.fetchall()
		if not res:
			raise cherrypy.HTTPError(status=404)
		img['url'] = "/image/%s" % res[0][2]
		img['tags'] = ' '.join(map(lambda x: x[0], res))
		return jinja_env.get_template("view.html").render(view_type="post", img=img)

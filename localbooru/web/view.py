import cherrypy

from . templates import jinja_env
from localbooru.tools.common import is_image

VIEW_QUERY = '''SELECT tags.name, tags.type, posts.hash, posts.image
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
		img['url'] = "/image/%s" % res[0][3]
		is_video = not is_image(res[0][3])
		img['tags'] = ' '.join(map(lambda x: x[0], res))
		taglist = []
		for r in res:
			tag = {}
			if r[1]:
				tag['type'] = r[1]
			else:
				tag['type'] = 'general'
			tag['name'] = r[0]
			taglist.append(tag)
		taglist.sort(key=lambda x: x['type'] in ['general', 'meta'])
		return jinja_env.get_template("view.html").render(view_type="post", img=img, taglist=taglist, video=is_video)

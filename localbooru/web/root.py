import cherrypy

from localbooru.tools.common import get_version
from . templates import jinja_env

class RootServer:
	@cherrypy.expose
	def index(self, **kwargs):
		sw_version = get_version()
		with cherrypy.tools.db.main.get() as conn, conn:
			cur = conn.execute('SELECT Count(1) FROM posts')
			post_count = cur.fetchone()[0]
		return jinja_env.get_template("frontpage.html").render(version = sw_version, postcount = str(post_count), animated = True)

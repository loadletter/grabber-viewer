import cherrypy

from templates import jinja_env

class ViewServer:
	@cherrypy.expose
	def index(self, **kwargs):
		img = {}
		img['url'] = ""
		img['tags'] = "test aaa"
		return jinja_env.get_template("view.html").render(view_type="post", img=img)

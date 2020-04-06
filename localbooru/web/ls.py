import cherrypy

from templates import jinja_env

class ListServer:
	@cherrypy.expose
	def index(self, **kwargs):
		pgnav = {}
		pgnav['current'] = 2
		pgnav['total'] = 5
		pgnav['nexturl'] = '/ls/3'
		pgnav['backurl'] = '/ls/1'
		pgnav['firsturl'] = '/ls/1'
		pgnav['lasturl'] = '/ls/5'
		pglist = []
		for i in range(1, 6):
			pglist.append({'number': i, 'url' : '/ls/%i' % i})
		return jinja_env.get_template("list.html").render(paginator=pgnav, pagelist=pglist, view_type="list")

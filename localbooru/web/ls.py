import binascii
import cherrypy

from . templates import jinja_env

LIST_QUERY = '''SELECT posts.id, tags.name AS tag, posts.hash, posts.image
FROM tagmap 
JOIN posts ON post = posts.id
JOIN tags ON tag = tags.id
ORDER BY posts.id'''

class ListServer:
	@cherrypy.expose
	def index(self, **kwargs):
		postlist = []
		with cherrypy.tools.db.cache.get() as conn, conn:
			cur = conn.execute(LIST_QUERY)
			currpost = None
			post = {}
			for p in cur:
				if not currpost or currpost != p[0]:
					if currpost and post:
						postlist.append(post)
						cherrypy.tools.thumb.create(md5, imagepath)
					post = {}
					post['id'] = p[0]
					post['viewurl'] = '/image/?md5=%s' % binascii.b2a_hex(p[2]).decode('utf-8')
					post['thumburl'] = '/thumb/?md5=%s' % binascii.b2a_hex(p[2]).decode('utf-8')
					post['tags'] = p[1]
					currpost = p[0]
					md5 = p[2]
					imagepath = p[3]
				else:
					post['tags'] += ' %s' % p[1]
		
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
		return jinja_env.get_template("list.html").render(paginator=pgnav, pagelist=pglist, view_type="list", postlist=postlist)

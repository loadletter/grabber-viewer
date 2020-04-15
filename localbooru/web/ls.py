import binascii
import math
import cherrypy
import urllib

from . templates import jinja_env

from localbooru.settings import RESULTS_PER_PAGE

LIST_QUERY = '''SELECT posts.id, tags.name, posts.hash, posts.image
FROM
(SELECT id, hash, image FROM posts ORDER BY id LIMIT ?,?) AS p
INNER JOIN tagmap ON tagmap.post = p.id
INNER JOIN posts ON post = posts.id
INNER JOIN tags ON tagmap.tag = tags.id'''

COUNT_QUERY = '''SELECT COUNT(DISTINCT(posts.id))
FROM tagmap 
INNER JOIN posts ON post = posts.id
INNER JOIN tags ON tag = tags.id'''

class ListServer:
	@cherrypy.expose
	def index(self, **kwargs):
		postlist = []
		if 'page' in kwargs:
			pagearg = int(kwargs['page']) 
		else:
			pagearg = 1
		
		dbpagearg = pagearg
		if dbpagearg > 0:
			dbpagearg -= 1
		
		with cherrypy.tools.db.cache.get() as conn, conn:
			cur = conn.execute(LIST_QUERY, (dbpagearg * RESULTS_PER_PAGE, RESULTS_PER_PAGE))
			currpost = None
			post = {}
			for p in cur:
				if not currpost or currpost != p[0]:
					if currpost and post:
						postlist.append(post)
						cherrypy.tools.thumb.create(md5, imagepath)
					post = {}
					post['id'] = p[0]
					post['viewurl'] = '/view/?id=%s' % p[0]
					post['thumburl'] = '/thumb/?md5=%s' % binascii.b2a_hex(p[2]).decode('utf-8')
					post['tags'] = p[1]
					currpost = p[0]
					md5 = p[2]
					imagepath = p[3]
				else:
					post['tags'] += ' %s' % p[1]
		
		keepargs = dict(kwargs)
		if 'page' in keepargs:
			keepargs.pop('page')
		newargs = urllib.parse.urlencode(keepargs)
		if newargs:
			newargs = '&' + newargs
		
		with cherrypy.tools.db.cache.get() as conn, conn:
			cur = conn.execute(COUNT_QUERY)
			postcount = cur.fetchone()
		
		pgnav = {}
		total_pg = math.ceil(postcount[0] / RESULTS_PER_PAGE)
		pgnav['total'] = total_pg
		pgnav['current'] = pagearg
		pgnav['firsturl'] = "/ls/" + newargs.lstrip('&')
		base_url = "/ls/?page=%i" + newargs
		pgnav['nexturl'] = base_url % (pagearg + 1)
		pgnav['backurl'] = base_url % (pagearg - 1)
		pgnav['lasturl'] = base_url % total_pg
		pglist = []
		for i in range(1, total_pg + 1):
			pglist.append({'number': i, 'url' : base_url % i})
		return jinja_env.get_template("list.html").render(paginator=pgnav, pagelist=pglist, view_type="list", postlist=postlist)

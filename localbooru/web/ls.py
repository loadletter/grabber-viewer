import binascii
import math
import cherrypy
import urllib

from . templates import jinja_env

from localbooru.settings import RESULTS_PER_PAGE

TAG_CTE='''WITH full_cte(postid, tagname) AS
(
	WITH positive_cte(postid, tagname)  AS
	(
		SELECT posts.id, tags.name
		FROM tagmap 
		INNER JOIN posts ON post = posts.id
		INNER JOIN tags ON tag = tags.id
		%s
	)
	SELECT postid, count(tagname) as cnt FROM positive_cte
	%s
	GROUP BY postid
	%s
)
'''

NEGATIVE_CTE='''
	WHERE postid NOT IN 
	(
		SELECT posts.id
		FROM tagmap 
		INNER JOIN posts ON post = posts.id
		INNER JOIN tags ON tag = tags.id
		%s
	)
	'''

LIST_QUERY = '''
SELECT posts.id, tags.name, posts.hash, posts.image
FROM
(SELECT postid FROM full_cte ORDER BY postid LIMIT ?,?) AS p
INNER JOIN tagmap ON tagmap.post = p.postid
INNER JOIN posts ON post = posts.id
INNER JOIN tags ON tagmap.tag = tags.id'''

COUNT_QUERY = '''
SELECT COUNT(DISTINCT(postid)) FROM full_cte'''

def build_cte(positive_tags=[], negative_tags=[]):
	pos_tags = ''
	pos_args = []
	pos_count = ''
	if positive_tags:
		pos_tags += 'WHERE '
		for t in positive_tags:
			prefix = 'OR ' if pos_tags.endswith('? ') else ''
			pos_tags +=  prefix + 'tags.name = ? '
			pos_args.append(t)
		pos_count = 'HAVING cnt = %i' % len(positive_tags)
	
	neg_tags = ''
	neg_args = []
	neg_query = ''
	if negative_tags:
		neg_tags += 'WHERE '
		for nt in negative_tags:
			prefix = 'OR ' if neg_tags.endswith('? ') else ''
			neg_tags +=  prefix + 'tags.name = ? '
			neg_args.append(nt)
		neg_query = NEGATIVE_CTE % neg_tags
	
	cte = TAG_CTE % (pos_tags, neg_query, pos_count)
	cte_args = tuple(pos_args) + tuple(neg_args)
	
	return (cte, cte_args)
	
def build_search_query(page, res_per_page, positive_tags, negative_tags):
	cte, cte_args = build_cte(positive_tags, negative_tags)
	full_query = cte + LIST_QUERY
	full_args = cte_args + (page, res_per_page)
	return (full_query, full_args)

def build_count_query(positive_tags, negative_tags):
	cte, cte_args = build_cte(positive_tags, negative_tags)
	full_query = cte + COUNT_QUERY
	return (full_query, cte_args)


class ListServer:
	@cherrypy.expose
	def index(self, **kwargs):
		postlist = []
		if 'page' in kwargs:
			pagearg = int(kwargs['page']) 
		else:
			pagearg = 1
			
		if 'commit' in kwargs:
			kwargs.pop('commit')
			pagearg = 1
		
		dbpagearg = pagearg
		if dbpagearg > 0:
			dbpagearg -= 1
		
		searchbar = ''
		
		searchpos = []
		searchneg = []
		if 'search' in kwargs:
			parsedsearch = urllib.parse.unquote_plus(kwargs['search']).strip()
			searchbar = parsedsearch
			for el in parsedsearch.split(' '):
				if el.startswith('-'):
					searchneg.append(el.strip('-'))
				else:
					searchpos.append(el)	

		search_query, search_args = build_search_query(dbpagearg * RESULTS_PER_PAGE, RESULTS_PER_PAGE, searchpos, searchneg)
		
		with cherrypy.tools.db.cache.get() as conn, conn:
			cur = conn.execute(search_query, search_args)
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
		
		count_query, count_args = build_count_query(searchpos, searchneg)
		with cherrypy.tools.db.cache.get() as conn, conn:
			cur = conn.execute(count_query, count_args)
			postcount = cur.fetchone()
		
		pgnav = {}
		total_pg = math.ceil(postcount[0] / RESULTS_PER_PAGE)
		pgnav['total'] = total_pg
		pgnav['current'] = pagearg
		pgnav['firsturl'] = "/ls/" + newargs.lstrip('&')
		base_url = "/ls/?page={}" + newargs
		pgnav['nexturl'] = base_url.format(pagearg + 1)
		pgnav['backurl'] = base_url.format(pagearg - 1)
		pgnav['lasturl'] = base_url.format(total_pg)
		pglist = []
		for i in range(1, total_pg + 1):
			pglist.append({'number': i, 'url' : base_url.format(i)})
		return jinja_env.get_template("list.html").render(paginator=pgnav, pagelist=pglist, view_type="list", postlist=postlist, searchbar=searchbar)

import os.path
import cherrypy

from localbooru import settings

current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(current_dir, '..', 'data')
if settings.IMAGE_DIR:
	image_dir = settings.IMAGE_DIR
else:
	image_dir = os.path.join(data_dir, 'images')
db_dir = os.path.join(data_dir, 'db')
cache_db = os.path.join(db_dir, 'cache.sqlite3')

checkpassword = cherrypy.lib.auth_basic.checkpassword_dict(settings.USERS)

cherrypy_config = { 'global': {'server.socket_host': settings.WEBSERVER_HOST,
								'server.socket_port': settings.WEBSERVER_PORT,
								'tools.encode.on' : True,
								'tools.encode.encoding' : 'utf-8',
								'tools.sessions.on' : True}}

application_config = { '/': 	{'tools.auth_basic.on': settings.WEBSERVER_AUTH,
							'tools.auth_basic.realm': 'Restricted space',
							'tools.auth_basic.checkpassword': checkpassword},
					'/static': {'tools.gzip.on': True,
							'tools.staticdir.on': True,
							'tools.staticdir.dir': os.path.join(data_dir, 'static')},
					'/image': {'tools.gzip.on': False,
							'tools.staticdir.on': True,
							'tools.staticdir.dir': image_dir}}

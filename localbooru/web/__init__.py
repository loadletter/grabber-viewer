import cherrypy

from view import ViewServer
from ls import ListServer
from root import RootServer

from localbooru.tools.db import LocalbooruDB
from localbooru.tools.settings import cherrypy_config, application_config, db_dir


class LocalBooru:

	def __init__(self):
		cherrypy.config.update(cherrypy_config)
		self.config = application_config
		cherrypy.tools.db = LocalbooruDB(db_dir)
		
		cherrypy.tree.mount(ListServer(), '/ls', self.config)
		cherrypy.tree.mount(ViewServer(), '/view', self.config)
		cherrypy.engine.subscribe('stop', self.stop)
		
	def start(self):        
		cherrypy.engine.signals.subscribe()
		cherrypy.quickstart(RootServer(), '/', self.config)
	
	def stop(self):
		cherrypy.tools.db.close()
		

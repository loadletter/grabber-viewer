WEBSERVER_HOST = "0.0.0.0"
WEBSERVER_PORT = 8080
WEBSERVER_AUTH = False
USERS = {'user' : 'password'}

RESULTS_PER_PAGE = 40
IMAGE_DIR = ''

import os.path
IMAGE_NAME_FUNC = lambda filename: os.path.join(filename[0:2], filename)

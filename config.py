import os, random, string

class Config(object):
    APP = None

class DevelopmentConfig(Config):
    TESTING = True
    DEBUG = False
    IP_HOST = '127.0.0.1'
    PORT_HOST = 5000
    URL_MAIN = 'http://%s/%s' % (IP_HOST, PORT_HOST)

app_config = {
    'development': DevelopmentConfig(),
    'testing': None,
    'production': None
}

if os.getenv("FLASK_ENV") == None:
    app_active = 'development'
else:
    app_active = os.getenv("FLASK_ENV")
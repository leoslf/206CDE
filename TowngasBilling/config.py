class Config(object):
    name = "205CDE_Project"
    DEBUG = False
    TESTING = False
    domain = "domain.com"
    admin_email = "leosin.205CDE@gmail.com"
    admin_email_pw = "205CDE.."

class ProductionConfig(Config):
    pass

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True


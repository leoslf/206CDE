class Config(object):
    name = "206CDE_Project"
    DEBUG = False
    TESTING = False
    domain = "domain.com"
    admin_email = "lfsin3-c@my.cityu.edu.hk"
    admin_email_pw = "206CDE.."

class ProductionConfig(Config):
    pass

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True


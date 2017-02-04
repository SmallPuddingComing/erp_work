#-*-coding:utf-8-*-
from flask import Flask
from config.db_config.dbengine import DbConfig
from config.redis_config.redis_config import RedisConfig
import os


def create_app(config_name):
    rootdir = os.getcwd()
    static_dir=os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

   # app = Flask(__name__,template_folder=static_dir+"/web/flagship-store/templates",static_folder=static_dir+"/web/flagship-store/static")
    redis_config = RedisConfig()
    app = Flask(__name__)
    app.config['SECRET_KEY'] = "hola_erp_system"
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config.setdefault('REDIS_HOST', redis_config.get_host())
    app.config.setdefault('REDIS_PORT', redis_config.get_port())
    app.config.setdefault('REDIS_DB', redis_config.get_db_number())
    app.config.setdefault('REDIS_PASSWORD', None)
    app.config.setdefault('USE_SECRET_KEY', False)
    app.config.setdefault('USE_REDIS_CONNECTION_POOL', redis_config.get_is_use_connect_pool())
    app.config.setdefault('MAX_CONNECTION', redis_config.get_max_connect())


    from control_center.admin import auth, auth_prefix
    app.register_blueprint(auth, url_prefix=auth_prefix)

    from control_center.flagship_manage import flagship_manage,flagship_manage_prefix
    app.register_blueprint(flagship_manage, url_prefix=flagship_manage_prefix)

    from control_center.main import main, main_prefix
    app.register_blueprint(main, url_prefix=main_prefix)

    from control_center.person_center import personal, personal_prefix
    app.register_blueprint(personal, url_prefix=personal_prefix)

    from control_center.shop_manage import shop_manage,shop_manage_prefix
    app.register_blueprint(shop_manage, url_prefix=shop_manage_prefix)

    from control_center.system import sys, sys_prefix
    app.register_blueprint(sys, url_prefix=sys_prefix)

    from control_center.supply_chain.base_info.views import baseinfo, baseinfo_prefix
    app.register_blueprint(baseinfo, url_prefix=baseinfo_prefix)

    from control_center.flagship_manage import flagship_manage,flagship_manage_prefix
    app.register_blueprint(flagship_manage, url_prefix= flagship_manage_prefix)

    from control_center.warehouse_manage import warehouse_manage, warehouse_manage_prefix
    app.register_blueprint(warehouse_manage, url_prefix=warehouse_manage_prefix)

    from control_center.admin.permission import call_before_request,inject_info
    app.before_request(call_before_request)
    app.context_processor(inject_info)

    from public.logger.syslog import SystemLog
    SystemLog.pub_init_log('myapp.log','JmGO')

    return app

def get_file(filename):  # pragma: no cover
    try:
        src = os.path.join(root_dir(), filename)
        # Figure out how flask returns static files
        # Tried:
        # - render_template
        # - send_file
        # This should not be so non-obvious
        return open(src).read()
    except IOError as exc:
        return str(exc)

def root_dir():  # pragma: no cover
    return os.path.abspath(os.path.dirname(__file__))

#-*-coding:utf-8-*-

from flask import session
from flask import jsonify
from flask import json
from flask.views import MethodView
from flask import  request, url_for
from sqlalchemy import or_, not_


from control_center.admin import add_url

from data_mode.user_center.model.admin_url import AdminUrl

from public.function import tools
from pprint import pprint


class IndexView(MethodView):
    def get(self):
        return tools.en_render_template('main/index.html')
        # from data_mode.user_center.control.mixOp import MixUserCenterOp
        # db_seesion = MixUserCenterOp().get_seesion()
        # m_urls = db_seesion.query(AdminUrl).filter( not_(AdminUrl.endpoint == 'main.index'), AdminUrl.type==add_url.TYPE_ENTRY ).all()
        # permission_urls = session['url_maps']
        #
        # nav_url = []
        # for iurl in m_urls:
        #     if permission_urls[iurl.url]:
        #         nav_url.append(iurl.to_json())
        #
        # return tools.en_render_template('main/index.html', nav_url=nav_url)



class menus(MethodView):
    def get(self):
        urls = None
        return_data = jsonify({ 'code':300 })
        from data_mode.user_center.control.mixOp import MixUserCenterOp
        db_seesion = MixUserCenterOp().get_seesion()

        m_urls = db_seesion.query(AdminUrl).filter(AdminUrl.type==add_url.TYPE_ENTRY)
        return_data = jsonify({
                'code':100,
                'entry_urls': [url.to_json() for url in m_urls],
            })

        return tools.en_return_data(return_data)


class DevelopPageView(MethodView):
    def get(self):
        return tools.en_render_template('public/developPage.html')

from control_center.admin import add_url
from . import main, main_prefix

add_url.add_url(u"主页", None, add_url.TYPE_ENTRY, main_prefix,
                main, '/', 'index', IndexView.as_view('index'), methods=['GET'])


add_url.add_main_url(u"主页", None, add_url.TYPE_ENTRY, main_prefix,
                main, '/', 'index', IndexView.as_view('index'), methods=['GET'])

add_url.add_url(u"开发页面", 'main.index', add_url.TYPE_FEATURE, main_prefix,
                main, '/developingPage/','developingPage', DevelopPageView.as_view('developingPage'), methods=['GET'])

add_url.add_url(u"获取菜单", "main.index", add_url.TYPE_FUNC, main_prefix,
                main, '/menus/', 'menus', menus.as_view('menus'), methods=['GET'])



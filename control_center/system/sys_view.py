#-*-coding:utf-8-*-

from flask import session
from flask.views import MethodView
from flask import render_template, current_app, request, url_for
from flask import jsonify
from flask import json
from pprint import pprint
from public.function import tools

from data_mode.user_center.model.admin_url import AdminUrl


class SysView(MethodView):
    def get(self):
        return tools.en_render_template('system/System-set.html')


class SysDataView(MethodView):
    def get(self):
        return_data = jsonify({ 'code':300 })
        if True or session['user']['is_superuser']:
            father = AdminUrl.query.filter_by(endpoint="sys.set").first()
            m_urls = AdminUrl.query.filter_by(parent_id = father.id, type=add_url.TYPE_FEATURE)
            return_data =  jsonify({
                    'code'        : 100,
                    'feature_urls': [url.to_json() for url in m_urls],
                })
        else:
            pass
        return tools.en_return_data(return_data)



from . import sys, sys_prefix
from control_center.admin import add_url

add_url.add_url(u"系统设置", "main.index", add_url.TYPE_ENTRY, sys_prefix,
                sys, '/', 'set', SysView.as_view('set'), methods=['GET'])

add_url.add_url(u"系统设置页面元素", "sys.set", add_url.TYPE_FUNC, sys_prefix,
                sys, '/sys_data/', 'sys_data', SysDataView.as_view('sys_data'), methods=['GET'])


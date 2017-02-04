#-*-coding:utf-8-*-

from flask import session
from flask.views import MethodView
from flask import render_template, current_app, request, url_for
from flask import jsonify
from flask import json
from pprint import pprint
from public.function import tools

from data_mode.user_center.model.admin_url import AdminUrl


class PersonalWechatView(MethodView):
    def get(self):
        return tools.en_render_template('personal/wxbind2.html')

class PersonalWechatStatuView(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        try:

            return_data = jsonify({ 'code':100,
                                    'wechat_id': "test"})
        except Exception, e:
            print e
        return tools.en_return_data(return_data)


from . import personal, personal_prefix
from control_center.admin import add_url

add_url.add_url(u"微信绑定", "personal.personal", add_url.TYPE_FEATURE, personal_prefix,
                personal, '/wechat/', 'wechat', PersonalWechatView.as_view('wechat'), methods=['GET'])

add_url.add_url(u"微信绑定状态", "personal.personal", add_url.TYPE_FEATURE, personal_prefix,
                personal, '/wechat_statu/', 'wechatstatu', PersonalWechatStatuView.as_view('wechatstatu'), methods=['post'])


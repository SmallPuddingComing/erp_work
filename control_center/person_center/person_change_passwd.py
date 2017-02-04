#-*-coding:utf-8-*-

from flask import session
from flask.views import MethodView
from flask import render_template, current_app, request, url_for
from flask import jsonify
from flask import json
from pprint import pprint

from public.function import tools

from data_mode.user_center.control.mixOp import MixUserCenterOp


class PersonalChangePasswdView(MethodView):
    def get(self):
        return tools.en_render_template('personal/password.html')


class PersonalChangePasswd(MethodView):
    def post(self):
        return_data = jsonify({ 'code':300 })
        try:
            src_password = request.values.get('src_password', "")
            new_password = request.values.get('new_password', "")
            verify_password = request.values.get('verify_password', "")

            auth = False
            username = session['user']['username']
            uid = session['user']['id']
            if new_password == verify_password:
                op = MixUserCenterOp()
                auth = op.auth_password(username, src_password)
                if auth:
                    op.change_password(uid, verify_password)
                    return_data = jsonify({ 'code':100 })
                else:
                    return_data = jsonify({ 'code':107 })
            else:
                return_data = jsonify({ 'code':101 })
        except Exception, e:
            print e
        return tools.en_return_data(return_data)

from . import personal, personal_prefix
from control_center.admin import add_url

add_url.add_url(u"安全设置", "personal.personal", add_url.TYPE_ENTRY, personal_prefix,
                personal, '/change_passwd_view/', 'changepasswdView', PersonalChangePasswdView.as_view('changepasswdView'), methods=['GET'])

add_url.add_url(u"保存密码修改", "personal.personal", add_url.TYPE_FEATURE, personal_prefix,
                personal, '/change_passwd/', 'changepasswd', PersonalChangePasswd.as_view('changepasswd'), methods=['POST'])
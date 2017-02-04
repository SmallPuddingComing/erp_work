#-*-coding:utf-8-*-

from flask import session
from flask.views import MethodView
from flask import render_template, current_app, request, url_for
from flask import jsonify
from flask import json
from pprint import pprint
from public.function import tools

from data_mode.user_center.model.admin_url import AdminUrl


class PersonalView(MethodView):
    def get(self):
        return tools.en_render_template('personal/personData.html')




from . import personal, personal_prefix
from control_center.admin import add_url

add_url.add_url(u"个人中心", "main.index", add_url.TYPE_FEATURE, personal_prefix,
                personal, '/', 'personal', PersonalView.as_view('personal'), methods=['GET'])



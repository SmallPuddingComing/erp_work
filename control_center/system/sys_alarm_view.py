#-*-coding:utf-8-*-


from flask.views import MethodView
from flask import render_template, current_app, request, url_for
from flask import jsonify



class SysView(MethodView):
    def get(self):
        return u"系统设置"
        return render_template('auth/login.html')


    def post(self):
        return_data = jsonify({ 'code':300 })
        try:
            pass
        except Exception, e:
            print e
        return return_data


from . import sys
from control_center.admin import add_url

add_url.add_url(u"系统设置", None, add_url.TYPE_FEATURE,  sys, '', 'account', SysView.as_view('sys'), 10,methods=['GET', 'POST'])

#-*- ucoding:utf-8 -*-

from flask import session
from flask.views import MethodView
from flask import render_template, current_app, request, url_for
from flask import jsonify
from flask import json
from pprint import pprint
from public.function import tools



class FlagshipManageView(MethodView):
    def get(self):
       # return tools.flagship_render_template('storeManage/StoreManage.html')
        return ""

class ClerkManage(MethodView):
    def get(self):
        return tools.flagship_render_template("storeManage/clerkAdmin.html")
# class ShowFlagShip(MethodView):
#     def get(self):
#         return tools.en_render_template("storeManage/dayflow.html")


from control_center.flagship_manage import flagship_manage, flagship_manage_prefix
from control_center.admin import add_url

add_url.flagship_add_url(u"旗舰店铺", "main.index", add_url.TYPE_ENTRY, flagship_manage_prefix,
                flagship_manage, "/", "FlagshipManageView", FlagshipManageView.as_view("FlagshipManageView"),100,methods=["GET"])


# add_url.flagship_add_url(u"门店店员管理", "flagship_manage.FlagshipManageView", add_url.TYPE_ENTRY, flagship_manage_prefix,
#                 flagship_manage, '/clerkdata/', 'ClerkManage', ClerkManage.as_view('ClerkManage'),methods=['GET'])

# add_url.flagship_add_url(u"门店日常登记", "ship_manage.FlagshipManageView", add_url.TYPE_ENTRY, flagship_manage_prefix,
#                 ship_manage, '/psg_flow/', 'ShowFlagShip', ShowFlagShip.as_view('ShowFlagShip'), methods=['GET'])



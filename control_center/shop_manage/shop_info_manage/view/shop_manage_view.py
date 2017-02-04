#-*-coding:utf-8-*-
from flask import session
from flask.views import MethodView
from flask import render_template, current_app, request, url_for
from flask import jsonify
from flask import json
from pprint import pprint
from public.function import tools
from control_center.shop_manage import shop_manage,shop_manage_prefix
from control_center.admin import add_url


class ShopManageView(MethodView):
    def get(self):
        #return tools.en_render_template("system/commoditytype.html")
        return "===="


add_url.add_url(u"店铺管理","main.index",add_url.TYPE_ENTRY,shop_manage_prefix,shop_manage,
        "/","ShopManageView",ShopManageView.as_view("ShopManageView"),90,methods=['GET'])



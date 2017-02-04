#!/usr/bin/python
# -*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : base_view.py.py
#    作者   : WangYi
#  电子邮箱 : ywang@jmgo.com
#    日期   : 2016/12/29 21:49
#
#     描述  :
#
from flask.views import MethodView
from control_center.warehouse_manage import warehouse_manage, warehouse_manage_prefix
from control_center.admin import add_url


class WarehouseManage(MethodView):

    def get(self):
        return ''


add_url.add_url(u'仓库管理',
                'main.index',
                add_url.TYPE_ENTRY,
                warehouse_manage_prefix,
                warehouse_manage,
                "/warehouse_manage/",
                'index',
                WarehouseManage.as_view('index'),
                methods=['GET'])
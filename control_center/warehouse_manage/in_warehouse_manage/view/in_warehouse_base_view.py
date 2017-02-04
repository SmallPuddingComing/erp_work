#!/usr/bin/python
# -*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : outbuy_invoices.py
#    作者   : tangjinxing
#  电子邮箱 :
#    日期   : 2016年12月30日14:08:51
#
#     描述  :
#

from flask.views import MethodView
from flask import request
from flask import json
import traceback
from public.exception.custom_exception import CodeError
from config.service_config.returncode import ServiceCode
from control_center.admin import add_url
from public.function import tools
from public.logger.syslog import SystemLog
from control_center.warehouse_manage.base_view import warehouse_manage, warehouse_manage_prefix


class InWarehouseManage(MethodView):
    """
    新建外购入库单
    """
    @staticmethod
    def get():
        return ""

add_url.add_url(u'入库管理',
                'warehouse_manage.index',
                add_url.TYPE_ENTRY,
                warehouse_manage_prefix,
                warehouse_manage,
                '/in_warehouse_manage/',
                'InWarehouseManage',
                InWarehouseManage.as_view('InWarehouseManage'),
                100,
                methods=['GET', 'POST'])

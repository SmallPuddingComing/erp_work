#!/usr/bin/python
#-*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : attribute.py
#    作者   : WangYi
#  电子邮箱 : ywang@jmgo.com
#    日期   : 2016/8/29 13:57
#
#     描述  :
#
import traceback
from flask.views import MethodView
from flask import current_app, request, url_for, session
from flask import json
import time
import datetime

from public.function import tools
from config.service_config.returncode import ServiceCode

from data_mode.erp_supply.base_op.material_op.attribute_op import Attribute_Op
# from .import material, material_prefix
from control_center.admin import add_url


class DisplayAttribute(MethodView):

    def get(self):
        try:
            attribute_op = Attribute_Op()
            data = {
                'code': ServiceCode.success,
                'rows': attribute_op.get_attribute_all(),
            }
        except Exception as ex:
            print(traceback.format_exc())
            data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            return tools.en_return_data(json.jsonify(data))
        else:
            return tools.en_return_data(json.jsonify(data))

from control_center.supply_chain import baseinfo_prefix, baseinfo

add_url.add_url(u'显示物料属', 'baseinfo.info', add_url.TYPE_FEATURE, baseinfo_prefix, baseinfo,
                '/info/attribute', 'displayAttribute', DisplayAttribute.as_view('displayAttribute'), methods=['GET'])

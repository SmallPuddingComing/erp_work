#!/usr/bin/python
#-*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : views.py.py
#    作者   : WangYi
#  电子邮箱 : ywang@jmgo.com
#    日期   : 2016/9/2 16:29
#
#     描述  :
#
import os
from control_center.admin import add_url
from flask.views import MethodView

class BaseInfoIndex(MethodView):

    def get(self):
        print("1")
        return ''


class SupplierIndex(MethodView):

    def get(self):
        return ''


class MaterialIndex(MethodView):

    def get(self):
        return ''

from control_center.supply_chain import baseinfo_prefix, baseinfo
add_url.add_url(
    u"基础资料",
    "main.index",
    add_url.TYPE_ENTRY,
    baseinfo_prefix,
    baseinfo,
    '/baseinfo/index/',
    'index',
    BaseInfoIndex.as_view('index'),
    methods=['GET'])

add_url.add_url(
    u"供应商管理",
    "baseinfo.index",
    add_url.TYPE_ENTRY,
    baseinfo_prefix,
    baseinfo,
    '/baseinfo/supplier_index/',
    'supplier_index',
    SupplierIndex.as_view('supplier_index'),
    methods=['GET'])

add_url.add_url(
    u"物料",
    "baseinfo.index",
    add_url.TYPE_ENTRY,
    baseinfo_prefix,
    baseinfo,
    '/baseinfo/material_index/',
    'material_index',
    MaterialIndex.as_view('material_index'),
    methods=['GET'])

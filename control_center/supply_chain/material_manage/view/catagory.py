#!/usr/bin/env python
#-*- coding:utf-8 -*-
#######################################################
#    Copyright(c) 2000-2013 JmGO Company
#    All rights reserved.
#
#    文件名 :   catagory.py
#    作者   :   WangYi
#  电子邮箱 :   ywang@jmgo.com
#    日期   :   2016/08/25 10:42:00
#
#    描述   :   展现物料分类页面
#
import traceback

from flask import json
from flask import request, session
from flask.views import MethodView

from config.service_config.returncode import ServiceCode
from control_center.admin import add_url
from data_mode.erp_supply.base_op.material_op.category_op import CategoryOp
from data_mode.erp_supply.base_op.operate_op import Operate_Op
from public.function import tools

DEFAULT_PER_PAGE = '10'


class DisplayCategory(MethodView):
    """
    显示分类信息
    """

    def get(self):
        try:
            cur_page = int(request.values.get('cur_page', 1)) #当前页数
            per_page = int(request.values.get('per_page', 10)) #每页默认显示的数据条数
            print "cur_page, per_page", cur_page, per_page

            categoryOp = CategoryOp()
            body = categoryOp.get_all_category_count(cur_page, per_page)
            data = {
                'code': ServiceCode.success,
                'body': body['data'],
                'total_page': body['count'],
                'count': len(body['data'])
            }
            print "data:  ", data
            return tools.en_render_template(
                'supplyChain/materiel/typeMateriel.html',
                result=json.dumps(data))
        except Exception as ex:
            print(traceback.format_exc())
            data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            return tools.en_render_template(
                'supplyChain/materiel/typeMateriel.html',
                result=json.dumps(data))

class DisplayResearchCategory(MethodView):
    """
    物料分类信息分页显示
    """

    def post(self):
        try:
            cur_page = int(request.values.get('cur_page', 1)) #当前页数
            per_page = int(request.values.get('per_page', 10)) #每页默认显示的数据条数
            print "cur_page, per_page", cur_page, per_page

            categoryOp = CategoryOp()
            body = categoryOp.get_all_category_count(cur_page, per_page)
            data = {
                'code': ServiceCode.success,
                'body': body['data'],
                'total_page': body['count'],
                'count': len(body['data'])
            }
            print "data:  ", data
            return tools.en_return_data(json.jsonify(data))
        except Exception as ex:
            print(traceback.format_exc())
            data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            return tools.en_return_data(json.jsonify(data))

class GetCategory(MethodView):
    """
    获取所有物料分类(数据接口)
    """

    def get(self):
        try:
            categoryOp = CategoryOp()
            is_add = request.args.get('is_add', 0, int)
            body = categoryOp.get_all_category_count(is_add=is_add)
            data = {
                'code': ServiceCode.success,
                'body': body['data']
            }
            return tools.en_return_data(json.jsonify(data))
        except Exception as ex:
            print(traceback.format_exc())
            data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            return tools.en_return_data(json.jsonify(data))


class AddCategory(MethodView):
    """
    添加物料分类信息
    """

    def post(self):
        try:

            code_id = request.form.get('code_id', None)
            name = request.form.get('name', None)
            parent_id = request.form.get('pid', None)

            category_op = CategoryOp()
            data = {}
            if category_op.check_code_id(code_id):
                data = {'code': ServiceCode.params_error, 'msg': u'存在相同的代码'}
            else:
                option = {}
                option['code_id'] = code_id
                option['name'] = name.encode()
                parent_id = int(parent_id.encode())
                option['parent_id'] = parent_id if parent_id > 0 else None
                option['state'] = category_op.STATE_USE
                if category_op.add_category(option):
                    # 添加操作记录

                    data = {
                        'code': ServiceCode.success,
                        'category_list': category_op.get_all_category()
                    }

            return tools.en_return_data(json.jsonify(data))

        except Exception as ex:
            print(traceback.format_exc())
            data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            return tools.en_return_data(json.jsonify(data))


class DelCategory(MethodView):
    """
    删除物料分类
    """

    def post(self):
        data = {}
        try:
            id = int(request.form['id'].encode())
            print "id", id
            categoryOp = CategoryOp()

            if categoryOp.check_id(id):
                return_code = categoryOp.del_category(id)
                print("return_code:", return_code)
                if return_code[0] == 0:
                    data = {'code': ServiceCode.success}
                else:
                    data = {'code': ServiceCode.dealfaild, 'msg': return_code[1]}
            else:
                data = {'code': ServiceCode.notfound, 'msg': u'没有相应记录'}
        except Exception as ex:
            print(traceback.format_exc())
            data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
        finally:
            return tools.en_return_data(json.jsonify(data))


class GetSimpleCategory(MethodView):
    """
    获取单个物料分类(数据接口)
    """

    def get(self):
        data = {}
        try:
            id = int(request.form['id'].encode())
            category_op = CategoryOp()
            return_data = category_op.get_category_by_id(id)
            if return_data[0] == 0:
                data = {'code': ServiceCode.success, 'rows': return_data[1]}
            else:
                data = {'code': ServiceCode.notfound, 'msg': return_data[1]}

        except Exception as ex:
            print(traceback.format_exc())
            data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
        finally:
            return tools.en_return_data(json.jsonify(data))


class UpdateCategory(MethodView):
    """
    更新物料分类(数据接口)
    """

    def post(self):
        data = {}
        try:
            id = int(request.form['id'].encode())
            name = request.form['name'].encode()
            category_op = CategoryOp()
            option = {'id': id, 'name': name}
            return_data = category_op.update_category(option)
            if return_data[0] == 0:
                data = {'code': ServiceCode.success}
            else:
                data = {'code': ServiceCode.update_error, 'msg': return_data[1]}
        except Exception as ex:
            print(traceback.format_exc())
            data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
        finally:
            return tools.en_return_data(json.jsonify(data))



class CategoryOperateRecord(MethodView):
    """
    查看物料分类操作记录(数据接口)
    """
    def get(self):
        try:
            start = request.values.get('start', 0)
            per_page = int(request.values.get('per_page', DEFAULT_PER_PAGE))
            code_id = request.values.get('category_id', '')

            if start < 0:
                data = {'code': ServiceCode.params_error, 'msg': u'起始记录必须不小于0'}
            elif per_page <= 0:
                data = {'code': ServiceCode.params_error, 'msg': u'每页显示记录数必须大于0'}
            else:
                operate_op = Operate_Op()
                rows = operate_op.get_record(
                    start, per_page, CategoryOp.TABEL_NAME, code_id)

                data = {'code': ServiceCode.success,
                    'rows': rows[0],
                    'start': start,
                    'per_page': per_page,
                    'total': rows[1]}
        except Exception:
            print(traceback.format_exc())
            data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
        finally:
            return tools.en_return_data(json.jsonify(data))

from control_center.supply_chain import baseinfo_prefix, baseinfo
add_url.add_url(
    u"物料类别",
    "baseinfo.material_index",
    add_url.TYPE_ENTRY,
    baseinfo_prefix,
    baseinfo,
    '/catagory/display_info/',
    'category',
    DisplayCategory.as_view('category'),
    methods=['GET'])

add_url.add_url(
    u"物料分类分页搜索",
    "baseinfo.category",
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/catagory/search_display_info/',
    'search_display_info',
    DisplayResearchCategory.as_view('search_display_info'),
    methods=['POST'])

add_url.add_url(
    u"添加物料分类",
    "baseinfo.category",
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/catagory/add_category/',
    'addCategory',
    AddCategory.as_view('addCategory'),
    methods=['POST'])

add_url.add_url(
    u"获取物料分类",
    "baseinfo.category",
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/catagory/get_category/',
    'getCategory',
    GetCategory.as_view('getCategory'),
    methods=['GET'])

add_url.add_url(
    u"删除物料分类",
    "baseinfo.category",
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/catagory/del_category',
    'delCategory',
    DelCategory.as_view('delCategory'),
    methods=['POST'])

add_url.add_url(
    u"获取单个物料分类信息",
    "baseinfo.category",
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/catagory/get_simple/',
    'category_getSimple',
    GetSimpleCategory.as_view('category_getSimple'),
    methods=['GET'])

add_url.add_url(
    u"修改物料信息",
    "baseinfo.category",
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/catagory/update/',
    'catagory_update',
    UpdateCategory.as_view('catagory_update'),
    methods=['POST'])

add_url.add_url(
    u"物料分类操作记录",
    "baseinfo.category",
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/catagory/operate_records/',
    'catgory_operate_records',
    CategoryOperateRecord.as_view('catgory_operate_records'),
    methods=['GET']
)

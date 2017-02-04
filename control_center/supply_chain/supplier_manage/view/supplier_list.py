#-*-coding:utf-8-*-
import traceback
from flask import session
from flask.views import MethodView
from flask import render_template, current_app, request, url_for
from flask import jsonify
from flask import json
from pprint import pprint
import json

from public.function import tools
from control_center.supply_chain.supplier_manage.control.supplier_list_info import SupplierListInfo
from config.service_config.returncode import *


import os


class supplierListView(MethodView):

    def get(self):
        try:
            #supplierCode = request.form.get('supplierCode', "")
            #supplierName = request.form.get('supplierName', "")
            searchType = request.values.get('searchType', 2, int)
            searchValue = request.values.get('searchValue', '', str)
            currentPage = request.values.get('currentPage', 1, int)
            pageList = request.values.get('pageList', 10, int)
            supplierlistinfo = SupplierListInfo()
            #count, data = supplierlistinfo.GetSupplierList(supplierCode, supplierName, currentPage, pageList)
            count, data = supplierlistinfo.GetSupplierList(
                searchType, searchValue, currentPage, pageList)
            total = len(data)
            # return_data = jsonify({'code': code,
            #                       'data': data,
            #                       'count': total
            #                       })


            return_data = {'count': count,  # 记录总数
                           'total': total,  # 每页显示的记录数
                           'rows': data  # 数据，总共total条
                           }
            print "----------return_data: ", return_data

            return tools.en_render_template(
                'supplyChain/supplierManage/manage-List.html',
                result=json.dumps(return_data))
        except Exception as ex:
            print(traceback.format_exc())
            data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            return tools.en_render_template(
                'supplyChain/supplierManage/manage-List.html',
                result=json.dumps(data))


# 功能描述：供应商列表“搜索”功能，按条件搜索相应的供应商信息
class supplierListInfo(MethodView):

    def get(self):

        try:
            searchType = request.values.get('searchType', 2, int)
            searchValue = request.values.get('searchValue', '', str)
            #currentPage = request.form.get('currentPage', 1)
            #pageList = request.form.get('pageList', 10)
            currentPage = request.values.get('currentPage', 1, int)
            pageList = request.values.get('pageList', 10, int)
            print('searchValue: %s' % searchValue)
            supplierlistinfo = SupplierListInfo()
            count, data = supplierlistinfo.GetSupplierList(
                searchType, searchValue, currentPage, pageList)
            total = len(data)

            for item in data:
                print(item['supplier_code'])
                print(item['supplier_name'])
                print(item['department_id'])
                print(item['principal_id'])
                print(item['currency_id'])
                print(item['state_id'])

            return_data = {'count': count,  # 记录总数
                           'total': total,  # 每页显示的记录数
                           'rows': data  # 数据，总共total条
                           }

            return tools.en_return_data(jsonify(return_data))
        except Exception as ex:
            print(traceback.format_exc())
            data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            return tools.en_return_data(json.dumps(data))


# 功能：供应商列表分页功能，将按条件搜索的供应商信息按页显示
class supplierListPerPage(MethodView):

    def get(self):

        try:
            searchType = request.values.get('searchType', 2, int)
            searchValue = request.values.get('searchValue', '', str)
            currentPage = request.values.get('currentPage', 1, int)
            pageList = request.values.get('pageList', 10, int)
            print('searcheValue: %s' % searchValue)
            supplierlistinfo = SupplierListInfo()
            count, data = supplierlistinfo.GetSupplierList(
                searchType, searchValue, currentPage, pageList)
            total = len(data)
            print('total %d' % total)
            print(data)
            for item in data:
                print(item['supplier_code'])
                print(item['supplier_name'])
                print(item['department_id'])
                print(item['principal_id'])
                print(item['currency_id'])
                print(item['state_id'])

            return_data = {'count': count,  # 记录总数
                           'total': total,  # 每页显示的记录数
                           'rows': data  # 数据，总共total条
                           }

            return tools.en_return_data(jsonify(return_data))
        except Exception as ex:
            print(traceback.format_exc())
            data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            return tools.en_return_data(json.dumps(data))


# 功能：供应商详情信息
class supplierDetailInfo(MethodView):

    def get(self):
        try:
            supplier_id = request.values.get('supplier_id', 1)

            # 根据供应商代码(supplier_base.supplier_code)从数据库erp_supply的supplier_baseinfo表中读取供应商信息
            # supplier_contact表中读取供应商联系人信息
            supplierlistinfo = SupplierListInfo()
            supplier_data, certificate_data, other_certificate_list = supplierlistinfo.GetDetailInfo(
                supplier_id)
            count = len(other_certificate_list)

            print('supplier_data')
            print(supplier_data)
            print('certificate_data')
            print(certificate_data)
            print('other_certificate_list')
            print(other_certificate_list)
            return_data = {
                'code': ServiceCode.success,
                'data': supplier_data,
                'certificate': certificate_data,
                'count': count,
                'others': other_certificate_list
            }

            return tools.en_render_template(
                'supplyChain/supplierManage/manage-DetailInfo.html',
                result=json.dumps(return_data))
            return tools.en_return_data(jsonify(return_data))
        except Exception as ex:
            print(traceback.format_exc())
            data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            return tools.en_return_data(jsonify(data))
            # return tools.en_render_template('supplyChain/supplierManage/manage-DetailInfo.html',
            #                                result=json.dumps(data))

# 功能：供应商信息删除


class supplierDelete(MethodView):

    def get(self):
        try:
            print('tst')
            searchType = request.values.get('searchType', 2, int)
            searchValue = request.values.get('searchValue', '', str)
            currentPage = request.values.get('currentPage', 1, int)
            pageList = request.values.get('pageList', 10, int)
            supplier_id_list = request.values.get('supplier_id_list')

           # sss = request.values.getlist('supplier_id_list[]')
           # print("ss:")
           # print(sss)

            # 删除数据库erp_supply中supplier_baseinfo表和supplier_contact表中的关于supplierCode的所有内容
            supplierlistinfo = SupplierListInfo()
            supplierlistinfo.DeleteSupplierInfo(json.loads(supplier_id_list))
            # 删除成功后，刷新页面

            supplierlistinfo = SupplierListInfo()
            # print("searchType: %d" % searchType)
            # print("searchValue :%s" % searchValue)
            # print("currentPage: %d" % currentPage)
            # print("pageList: %d" % pageList)
            count, data = supplierlistinfo.GetSupplierList(
                searchType, searchValue, currentPage, pageList)
            total = len(data)

            return_data = {'count': count,  # 记录总数
                           'total': total,  # 每页显示的记录数
                           'rows': data  # 数据，总共total条
                           }
            return tools.en_return_data(jsonify(return_data))
        except Exception as ex:
            print(traceback.format_exc())
            data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            return tools.en_return_data(json.dumps(data))


from control_center.admin import add_url
# from . import supplier, supplier_prefix
from control_center.supply_chain import baseinfo_prefix, baseinfo


add_url.add_url(
    u"供应商列表",
    "baseinfo.supplier_index",
    add_url.TYPE_ENTRY,
    baseinfo_prefix,
    baseinfo,
    '/supplier_list/',
    'supplierlist',
    supplierListView.as_view('supplierlist'),
    methods=['GET'])


add_url.add_url(
    u"搜索",
    "baseinfo.supplierlist",
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/supplier_search/',
    'supplier_search',
    supplierListInfo.as_view('supplier_search'),
    methods=['GET'])

# add_url.add_url(
#     u"下一页",
#     "baseinfo.supplierlist",
#     add_url.TYPE_FEATURE,
#     baseinfo_prefix,
#     baseinfo,
#     '/supplier_search_page/',
#     'supplier_search_page',
#     supplierListPerPage.as_view('supplier_search_page'),
#     methods=['GET'])

add_url.add_url(
    u"删除供应商信息",
    "baseinfo.supplierlist",
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/supplier_delete/',
    'supplier_delete',
    supplierDelete.as_view('supplier_delete'),
    methods=['GET'])

add_url.add_url(
    u"供应商详情",
    "baseinfo.supplierlist",
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/supplier_detail_info/',
    'supplier_detail_info',
    supplierDetailInfo.as_view('supplier_detail_info'),
    methods=['GET'])

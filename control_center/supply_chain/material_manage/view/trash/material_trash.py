#!/usr/bin/python
# -*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : material_trash.py
#    作者   : tangjinxing
#    日期   : 2016年11月29日15:32:28
#     描述  : 物料信息-->回收站页面 视图
#

from flask.views import MethodView
from flask import request
from flask import json
import traceback
from public.exception.custom_exception import CodeError
from config.service_config.returncode import ServiceCode
from control_center.admin import add_url
from public.function import tools
from control_center.supply_chain import baseinfo, baseinfo_prefix
from control_center.supply_chain.material_manage.control.trash_op import TrashOp
from public.logger.syslog import SystemLog


class MaterialTrash(MethodView):
    """
    回收站页面
    """
    @staticmethod
    def get():

        r_data = {}
        return_data = {}
        try:
            op = TrashOp()
            r_data = op.trash_info()

        except CodeError as e:
            return_data = json.dumps(e.json_value())
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败", 'rows': r_data})
        else:
            return_data = json.dumps(
                {'code': ServiceCode.success, 'msg': u"服务器成功", 'rows': r_data})
        finally:
            return tools.en_render_template("/supplyChain/materiel/recycleBin.html", result=return_data)


class TrashSearch(MethodView):
    """
    回收站搜索
    """
    @staticmethod
    def post():
        r_data = {}
        return_data = {}
        try:
            search_dict = dict()
            search_dict["page"] = request.values.get("page", 1, int)
            search_dict["per_page"] = request.values.get("per_page", 10, int)
            search_dict["key"] = request.values.get("key", None, str)
            search_dict["value"] = request.values.get("value", None, str)
            search_dict["m_attr"] = request.values.get("m_attr", None, str)
            search_dict["m_cate_id"] = request.values.get("m_cate_id", None)
            op = TrashOp()
            r_data = op.trash_search_info(search_dict)
        except CodeError as e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(e.json_value())
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败", 'rows': r_data})
        else:
            return_data = json.dumps(
                {'code': ServiceCode.success, 'msg': u"服务器成功", 'rows': r_data})
        finally:
            return tools.en_return_data(return_data)


class TrashOperate(MethodView):
    """
    回收站 删除，批量删除，恢复，批量恢复
    """
    @staticmethod
    def post():
        r_data = {}
        return_data = {}
        try:
            op = TrashOp()
            m_list = request.values.get("m_list", None)
            m_list = json.loads(m_list)
            op_type = request.values.get("op_type", None)
            if op_type not in ("recover","delete"):
                raise CodeError(ServiceCode.service_exception, u"op_type error")
            elif op_type == "recover":
                r_data = op.material_batch_recover(m_list)
            else:
                r_data = op.material_batch_del(m_list)
        except CodeError as e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(e.json_value())
        except Exception as e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败", 'rows': r_data})
        else:
            return_data = json.dumps(
                {'code': ServiceCode.success, 'msg': u"服务器成功", 'rows': r_data})
        finally:
            return tools.en_return_data(return_data)


add_url.add_url(
    u'回收站页面',
    "baseinfo.info",
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/material_trash/',
    'MaterialTrash',
    MaterialTrash.as_view('MaterialTrash'),
    70,
    methods=['GET'])

add_url.add_url(
    u'回收站搜索',
    "baseinfo.MaterialTrash",
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/trash_search/',
    'TrashSearch',
    TrashSearch.as_view('TrashSearch'),
    methods=['POST'])

add_url.add_url(
    u'删除恢复',
    "baseinfo.MaterialTrash",
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/trash_op/',
    'TrashOperate',
    TrashOperate.as_view('TrashOperate'),
    methods=['POST'])

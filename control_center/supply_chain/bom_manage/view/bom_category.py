#!/usr/bin/python
# -*- coding:utf-8 -*-

from flask.views import MethodView
from flask import request
from flask import json
import traceback
from public.exception.custom_exception import CodeError
from config.service_config.returncode import ServiceCode
from control_center.admin import add_url
from public.function import tools
from control_center.supply_chain import baseinfo, baseinfo_prefix
from control_center.supply_chain.bom_manage.control.bom_category_op import BomCategoryOp
from public.logger.syslog import SystemLog


class BomCategory(MethodView):
    """
    BOM 分组页面
    """
    @staticmethod
    def get():
        r_data = {}
        return_data = {}
        try:
            op = BomCategoryOp()
            r_data = op.get_bomcategory_info()

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
            return tools.en_render_template("/supplyChain/BOM/BOMList.html", result=return_data)


class BomCateSearch(MethodView):
    """
    BOM分组搜索
    """
    @staticmethod
    def get():
        r_data = {}
        return_data = {}
        try:
            key = request.values.get("key", None, str)
            value = request.values.get("value", None, str)
            op = BomCategoryOp()
            r_data = op.bom_info_search(key=key, value=value)

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
            return tools.en_return_data(return_data)


class BomOverview(MethodView):
    """
    BOM概览
    """
    @staticmethod
    def get():
        r_data = {}
        return_data = {}
        try:
            bom_id = request.values.get("bom_id", int)
            op = BomCategoryOp()
            r_data = op.get_bom_overview(bom_id)
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


class BomCategoryManage(MethodView):
    """
    BOM分组管理
    """
    @staticmethod
    def get():
        r_data = {}
        return_data = {}
        try:
            op = BomCategoryOp()
            r_data = op.get_bomcategory_info()
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
            return tools.en_render_template("/supplyChain/BOM/bom_manage.html", result=return_data)


class CheckCategoryCode(MethodView):
    """
    检查分组代码
    """
    @staticmethod
    def get():
        r_data = {}
        return_data = {}
        try:
            b_code = request.values.get("b_code", None, str)
            op = BomCategoryOp()
            rs = op.check_category_code(b_code)
            if rs:
                raise CodeError("300", u"该分组代码存在")

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
            return tools.en_return_data(return_data)


class SaveCategory(MethodView):
    """
    BOM保存分组
    """
    @staticmethod
    def post():
        r_data = {}
        return_data = {}
        try:
            b_code = request.values.get("b_code", None, str)
            b_name = request.values.get("b_name", None, str)
            p_id = request.values.get("p_id", None)
            level = request.values.get("level", None, int)
            b_id = request.values.get("b_id", None)

            op = BomCategoryOp()
            if b_code is None or b_code is u"":
                raise CodeError(300, u"code参数错误")
            if b_name is None or b_name is u"":
                raise CodeError(300, u" name参数错误")
            if p_id is not None and p_id is not u"" and p_id != 0:
                p_id = int(p_id.split('g')[0])

            if b_id is not None and b_id is not u"":
                b_id = int(b_id.split('g')[0])
                op.update_category(b_id, b_name, b_code)
            else:
                op.save_category(b_code, b_name, p_id, level)

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
            return tools.en_return_data(return_data)


class DeleteCategory(MethodView):
    """
    BOM删除分组
    """
    @staticmethod
    def get():
        r_data = {}
        return_data = {}
        try:
            bom_id = request.values.get("bom_id", None)
            if bom_id is not None and bom_id is not u"":
                bom_id = int(bom_id.split('g')[0])
            op = BomCategoryOp()
            print bom_id
            r_data = op.delete_category(bom_id)
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
            return tools.en_return_data(return_data)

add_url.add_url(
    u'BOM分组',
    "baseinfo.BomManage",
    add_url.TYPE_ENTRY,
    baseinfo_prefix,
    baseinfo,
    '/bom_category/',
    'BomCategory',
    BomCategory.as_view('BomCategory'),
    100,
    methods=['GET'])

add_url.add_url(
    u'BOM分组搜索 ',
    "baseinfo.BomCategory",
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/bom_cate_search/',
    'BomCateSearch',
    BomCateSearch.as_view('BomCateSearch'),
    methods=['GET'])

add_url.add_url(
    u'BOM概览',
    "baseinfo.BomCategory",
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/bom_overview/',
    'BomOverview',
    BomOverview.as_view('BomOverview'),
    methods=['GET'])

add_url.add_url(
    u'BOM分组管理',
    "baseinfo.BomManage",
    add_url.TYPE_ENTRY,
    baseinfo_prefix,
    baseinfo,
    '/bom_categ_mge/',
    'BomCategoryManage',
    BomCategoryManage.as_view('BomCategoryManage'),
    90,
    methods=['GET'])

add_url.add_url(
    u'检查分组代码',
    "baseinfo.BomCategoryManage",
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/check_cate_code/',
    'CheckCategoryCode',
    CheckCategoryCode.as_view('CheckCategoryCode'),
    methods=['GET'])

add_url.add_url(
    u'保存分组',
    "baseinfo.BomCategoryManage",
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/save_category/',
    'SaveCategory',
    SaveCategory.as_view('SaveCategory'),
    methods=['GET', 'POST'])

add_url.add_url(
    u'删除分组',
    "baseinfo.BomCategoryManage",
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/delete_category/',
    'DeleteCategory',
    DeleteCategory.as_view('DeleteCategory'),
    methods=['GET'])

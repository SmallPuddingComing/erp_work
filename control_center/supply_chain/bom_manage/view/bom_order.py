#!/usr/bin/python
#-*- coding:utf-8 -*-
from flask.views import MethodView
from flask import request
from sqlalchemy.exc import IntegrityError
from flask import json
import traceback
from public.exception.custom_exception import CodeError
from config.service_config.returncode import ServiceCode
from control_center.admin import add_url
from public.function import tools
from control_center.supply_chain import baseinfo, baseinfo_prefix
from data_mode.erp_supply.base_op.bom_base_op import BomBaseOp
from public.logger.syslog import SystemLog

class BomManage(MethodView):
    def get(self):
        return ""


class CreateBomOrder(MethodView):
    '''
    新建BOM
    '''
    def get(self):
        return_data = None
        try:
            bom_op = BomBaseOp()
            # 获取BOM分组列表信息
            bom_category_list = bom_op.traverse_bom_category()
            # 生成BOM编号
            bom_code = bom_op.CreateBomCode()
            # 生成BOM版本
            bom_version = bom_op.CreateVersionNum()
        except CodeError as e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(e.json_value() )
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败"})
        else:
            datas = {
                'code': ServiceCode.success,
                'bomcode': bom_code,
                'bom_version': bom_version,
                'product': bom_category_list
            }
            return_data = json.dumps(datas)
        finally:
            return tools.en_render_template("/supplyChain/BOM/newBOM.html",result=return_data)


class SelectMaterialToBom(MethodView):
    """
    选择物料接口
    """
    def post(self):
        return_data = None
        datas = {}
        try:
            page = request.values.get('page', 1, int)
            pagecount = request.values.get('pagecount', 10, int)
            search_type = request.values.get('type', 0, int)  # 全搜时，type传0
            search_value = request.values.get('value', '', str) # 全搜时，value为空字符串
            father_id = request.values.get('pid',None, int)  # 选择父项物料时，默认传0
            # 前端传入的参数合法性检测
            if page is None or pagecount is None:
                raise CodeError(ServiceCode.service_exception, u'分页参数传输有误')
            if search_type is None or search_value is None:
                raise CodeError(ServiceCode.service_exception, u'搜索内容传输有误')
            if father_id is None or father_id<0 :
                raise CodeError(ServiceCode.service_exception, u"选择物料时，父项物料的物料id有误")
            # 筛选需要滤掉的物料的id
            bom_op = BomBaseOp()
            if father_id>0:
                parent_id_list = bom_op.get_parent_materialid(father_id)
                parent_id_list.append(father_id)
            else:
                # 查找material_baseinfo表中所有绑定了BOM的节点
                bound_datas = bom_op.get_boundbom_materialid()
                parent_id_list = [data['id'] for data in bound_datas]
            total, material_datas = bom_op.SelectMaterialInfo(parent_id_list, page,pagecount,search_type,search_value)
        except CodeError as e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(e.json_value())
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败"})
        else:
            datas['code'] = ServiceCode.success
            datas['total'] = total
            datas['rows'] = material_datas
            return_data = json.dumps(datas)
        finally:
            return tools.en_return_data(return_data)

class BomOrderDetail(MethodView):
    '''
    BOM明细(页面)
    '''
    def get(self):
        return_data = None
        try:
            page = request.values.get('page', 1, int)
            pagecount = request.values.get('pagecount', 10, int)
            bom_code = request.values.get('bom_code', None, str)
            # 前端传入的参数合法性检测
            if page is None or pagecount is None:
                raise CodeError(ServiceCode.service_exception, u'分页参数传输有误')
            if bom_code is None:
                raise CodeError(ServiceCode.service_exception, u'bom编号有误')
            #根据bom编码获取对应的绑定物料的信息
            bom_op = BomBaseOp()
            bom_datas, total = bom_op.get_bound_material_by_bomcode(bom_code)
            # 根据分页，搜索，bom版本信息查询bom_relation表获取数据
            # 跳转页面时，搜索参数均我None
            total, child_datas = bom_op.get_bom_material_info( bom_datas['id'], page, pagecount)
        except CodeError as e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(e.json_value())
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败"})
        else:
            datas = bom_datas
            datas['code'] = ServiceCode.success
            datas['total'] = total
            datas['rows'] = child_datas
            return_data = json.dumps(datas)
        finally:
            return tools.en_render_template("/supplyChain/BOM/BOMDetail.html",result=return_data)

class SelectBomOrderDetail(MethodView):
    '''
    BOM明细(搜索)
    '''
    def post(self):
        return_data = None
        try:
            page = request.values.get('page', 1, int)
            pagecount = request.values.get('pagecount', 10, int)
            bom_code = request.values.get('bom_code', None, str)
            search_type = request.values.get('type', 0, int)  #1：物料代码 2：物料名称（全搜时传0）
            search_value = request.values.get('value', '', str) #全搜时传空字符串
            # 前端传入的参数合法性检测
            if page is None or pagecount is None:
                raise CodeError(ServiceCode.service_exception, u'BOM明细页面搜索时分页参数有误')
            if bom_code is None:
                raise CodeError(ServiceCode.service_exception, u'BOM明细页面搜索时bom编号有误')
            if search_type is None or search_value is None or search_type not in (0, 1, 2):
                raise CodeError(ServiceCode.service_exception, u"BOM明细页面搜索时搜索条件有误")
            if search_type == 0 and len(search_value.strip()) != 0:
                raise CodeError(ServiceCode.service_exception, u"BOM明细页面搜索时搜索条件有误")
            # 根据bom编码获取对应的绑定物料的信息
            bom_op = BomBaseOp()
            bom_datas, total = bom_op.get_bound_material_by_bomcode(bom_code)
            # 根据分页，搜索，bom版本信息查询bom_relation表获取数据
            if search_type == 0 or len(search_value.strip()) == 0:
                # 跳转页面时，搜索参数均我None
                total, child_datas = bom_op.get_bom_material_info(bom_datas['id'], page, pagecount)
            else :
                 # 跳转页面时，搜索参数均我None
                total, child_datas = bom_op.get_bom_material_info(bom_datas['id'],
                                                                   page, pagecount, search_type, search_value)
        except CodeError as e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(e.json_value())
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败"})
        else:
            datas = bom_datas
            datas['code'] = ServiceCode.success
            datas['total'] = total
            datas['rows'] = child_datas
            return_data = json.dumps(datas)
        finally:
            return tools.en_return_data(return_data)

class SaveBomInfo(MethodView):
    def post(self):
        return_data = None
        datas = {}
        try:
            parent_material_id = request.values.get('pid', None, int)
            bom_code = request.values.get('bomcode', None, str)
            bom_rem = request.values.get('rem', None, str)
            bom_version = request.values.get('version', None, str)
            bom_category_id = request.values.get('bom_category_id', None, int)
            child_material_num = request.values.get('total', None, int)
            child_material_str = request.values.get('datas', None)
            # 前端传入的参数合法性检测
            if parent_material_id is None:
                raise CodeError(ServiceCode.service_exception, u"新增Bom保存时，父项物料id值有误")
            if bom_code is None or len(bom_code.strip()) == 0:
                raise CodeError(ServiceCode.service_exception, u"新增Bom保存时，Bom编号值有误")
            if bom_rem is None:
                raise CodeError(ServiceCode.service_exception, u"新增Bom保存时，Bom备注值有误，默认值传空字符串")
            if bom_version is None or len(bom_version.strip()) == 0:
                raise CodeError(ServiceCode.service_exception, u"新增Bom保存时，Bom版本有误，默认值传空字符串")
            if bom_category_id is None:
                raise CodeError(ServiceCode.service_exception, u"新增Bom保存时，Bom分组id值有误")
            if child_material_num is None:
                raise CodeError(ServiceCode.service_exception, u"新增Bom保存时，添加的子项物料数据记录数有误")
            if child_material_str is None:
                raise CodeError(ServiceCode.service_exception, u"新增Bom保存时，添加的子项物料数据有误")
            child_material_lists = json.loads(child_material_str)
            if child_material_num != len(child_material_lists):
                raise CodeError(ServiceCode.service_exception,
                                u"新增Bom保存是，提供的子项物料数目记录数与实际提供的子项物料数据不符")

            for data in child_material_lists:
                # deal_type是判断该子项物料是添加(deal_type=0)、修改(deal_type=1)或删除(deal_type=2)
                data['deal_type'] = 0
            father_info_dict = {}
            father_info_dict['pid'] = parent_material_id
            father_info_dict['code'] = bom_code
            father_info_dict['bom_rem'] = bom_rem
            father_info_dict['bom_version'] = bom_version
            father_info_dict['bom_category_id'] = bom_category_id
            # 保存bom数据
            bom_op = BomBaseOp()
            bom_op.SaveBomInfo(father_info_dict,child_material_lists)
        except CodeError as e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(e.json_value())
        except ValueError:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器错误"})
        except IntegrityError:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(
                    {'code': ServiceCode.service_exception, 'msg': u"服务器错误"})
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = json.dumps(
                    {'code': ServiceCode.service_exception, 'msg': u"服务器错误"})
        else:
            datas['code'] = ServiceCode.success
            return_data = json.dumps(datas)
        finally:
                return tools.en_return_data(return_data)

add_url.add_url(
    u'BOM管理',
    "baseinfo.index",
    add_url.TYPE_ENTRY,
    baseinfo_prefix,
    baseinfo,
    '/bom_manage/',
    'BomManage',
    BomManage.as_view('BomManage'),
    methods=['GET'])

add_url.add_url(
    u'新增BOM',
    "baseinfo.BomManage",
    add_url.TYPE_ENTRY,
    baseinfo_prefix,
    baseinfo,
    '/create_bom/',
    'CreateBomOrder',
    CreateBomOrder.as_view('CreateBomOrder'), 80,
    methods=['GET'])

add_url.add_url(
    u'选择添加物料',
    'baseinfo.CreateBomOrder',
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/select_material/',
    'SelectMaterial',
    SelectMaterialToBom.as_view('SelectMaterial'),
    methods=['POST']
)

add_url.add_url(
    u'保存新增BOM数据',
    'baseinfo.CreateBomOrder',
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/save_bom/',
    'SaveBom',
    SaveBomInfo.as_view('SaveBom'),
    methods=['POST']
)

add_url.add_url(
    u'BOM明细',
    "baseinfo.BomCategory",
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/detail_of_bom/',
    'DetailOfBom',
    BomOrderDetail.as_view('DetailOfBom'),
    methods=['GET'])

add_url.add_url(
    u'BOM明细搜索',
    "baseinfo.DetailOfBom",
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/search_bom_info/',
    'SearchBomInfo',
    SelectBomOrderDetail.as_view('SearchBomInfo'),
    methods=['POST']
)


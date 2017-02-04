#!/usr/bin/env python
#-*- coding:utf-8 -*-
#######################################################
#    Copyright(c) 2000-2013 JmGO Company
#    All rights reserved.
#
#    文件名 :   display_info.py
#    作者   :   WangYi
#  电子邮箱 :   ywang@jmgo.com
#    日期   :   2016/08/25 10:43:25
#
#    描述   :   展现物料基本资料页面
#
import traceback
from flask.views import MethodView
from flask import request, session
from flask import json
import os
from public.function import tools
from public.exception.custom_exception import CodeError
from config.service_config.returncode import ServiceCode
from control_center.admin import add_url
from public.upload_download.upload_download import pub_upload_picture_to_server
from public.upload_download.upload_download import pub_upload_picture_to_qiniu
# from data_mode.erp_base.control.operate_op import Operate_Op
from data_mode.erp_supply.base_op.operate_op import Operate_Op
from data_mode.erp_base.control.uploadOp import UploadOp, UploadConfig
from control_center.supply_chain import baseinfo_base
from control_center.supply_chain.supplier_manage.control.supplier_list_info import SupplierListInfo
from control_center.supply_chain.supplier_manage.control.supplier_baseinfo_op import SupplierBaseInfoOp
from data_mode.erp_supply.base_op.material_op.baseinfo_op import Baseinfo_Op
from data_mode.erp_supply.base_op.material_op.category_op import CategoryOp
from config.share.share_define import *
from control_center.supply_chain import baseinfo_prefix, baseinfo
from control_center.supply_chain.material_warehosue.control.material_warehose_info_op import MaterialWarehouseInfoOp
from public.upload_download.file_manage_op.file_manage_op import FileManageOp
from data_mode.user_center.control.mixOp import MixUserCenterOp
from data_mode.erp_supply.mode.material_manage_mode.material_file_info import MaterialFileInfo
from data_mode.erp_supply.base_op.bom_base_op import BomBaseOp
from public.logger.syslog import SystemLog


class DisplayBaseinfo(MethodView):
    """
    显示物料信息
    """

    def get(self):
        return_data = {}
        datas = {}
        try:
            baseinfo_op = Baseinfo_Op()
            category_op = CategoryOp()
            start = int(request.args.get('page', '1'))
            per_page = int(request.args.get('pagecount', 10))

            if start < 0:
                data = {'code': ServiceCode.params_error, 'msg': u'分页页数必须不小于0'}
            elif per_page <= 0:
                data = {'code': ServiceCode.params_error, 'msg': u'每页显示记录数必须大于0'}
            else:
                select_dict = {
                    'page': start,
                    'pagecount': per_page
                }
                # 获取物料数据
                total, material_datas = baseinfo_op.displaymaterialinfo(**select_dict)
                # 获取物料状态数据
                new_dict = {value: key for key, value in SupplyAttr.MATERIAL_STATE_TYPE.items()}
                state_datas = [
                    {'id': '0', 'name': u"物料状态"},
                    {'id': new_dict[SupplyAttr.MATERIAL_STATE_UNUSE], 'name':SupplyAttr.MATERIAL_STATE_UNUSE},
                    {'id': new_dict[SupplyAttr.MATERIAL_STATE_USE], 'name':SupplyAttr.MATERIAL_STATE_USE},
                    {'id': new_dict[SupplyAttr.MATERIAL_STATE_FORBIDUSE], 'name':SupplyAttr.MATERIAL_STATE_FORBIDUSE}]
                # 获取物料属性数据
                attribute_datas = []
                temp_dict = {}
                temp_dict['id'] = '0'
                temp_dict['name'] = u"物料属性"
                attribute_datas.append(temp_dict)
                for key, value in SupplyAttr.MATERIAL_ATTRIBUTE_TYPE.items():
                    temp_dict = {}
                    temp_dict['id'] = key
                    temp_dict['name'] = value
                    attribute_datas.append(temp_dict)
                # 获取物料类别数据

                category_datas = category_op.get_all_category()
        except CodeError as e:
            return_data = json.dumps(e.json_value())
        except Exception as e:
            print traceback.format_exc(e)
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器成功"})
        else:
            datas['code'] = ServiceCode.success
            datas['total'] = total
            datas['state'] = state_datas
            datas['attribute'] = attribute_datas
            datas['category'] = category_datas
            datas['datas'] = material_datas
            return_data = json.dumps(datas)
        finally:
            return tools.en_render_template(
                'supplyChain/materiel/manageMateriel.html',
                results=return_data)

class SelectMaterialInfo(MethodView):
    def post(self):
        return_data = None
        datas = {}
        try:
            page = request.values.get('page', 1, int)
            pagecount = request.values.get('pagecount', 10, int)
            search_type = request.values.get('type',0, int)
            search_value = request.values.get('value', '', str)
            search_state = request.values.get('state', '', str)
            search_attribute = request.values.get('attribute', '', str)

            if search_attribute == '0':
                search_attribute = ''
            baseinfo_op = Baseinfo_Op()
            select_dict = {
                    'page':page,
                    'pagecount': pagecount,
                    'search_type': search_type,
                    'search_value': search_value,
                    'search_state': search_state,
                    'search_attribute': search_attribute
                }
            #获取物料数据
            total, material_datas = baseinfo_op.displaymaterialinfo(**select_dict)

        except CodeError as e:
            return_data = json.dumps(e.json_value())
        except Exception as e:
            print traceback.format_exc(e)
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器错误"})
        else:
            datas['code'] = ServiceCode.success
            datas['total'] = total
            datas['rows'] = material_datas
            return_data = json.dumps(datas)
        finally:
            return tools.en_return_data(return_data)


class ChangeMaterialState(MethodView):
    """
    物料的状态切换
    """
    def post(self):
        return_data = None
        datas = {}
        try:
            operate_type = request.values.get( 'type', 0, int )
            reason = request.values.get('reason', '', str)
            material_id = request.values.get('id_list')
            if material_id is None:
                raise CodeError(ServiceCode, u"选中的物料数据传输有误")

            material_id_list = json.loads(material_id)
            baseinfo_op = Baseinfo_Op()
            # 更新物料状态切换记录
            baseinfo_op.save_material_operate(operate_type, material_id_list,reason)

        except CodeError as e:
            return_data = json.dumps(e.json_value())
        except Exception as e:
            print traceback.format_exc(e)
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败"})
        else:
            datas['code'] = ServiceCode.success
            datas['msg'] = u"操作成功"
            return_data = json.dumps(datas)
        finally:
            return tools.en_return_data(return_data)


class CheckMaterialState(MethodView):
    """
    检测需要进行物料状态切换的物料数据的合法性
    """
    def post(self):
        return_data = None
        datas = {}
        try:
            operate_type = request.values.get( 'type', 0, int )
            material_id = request.values.get('id_list')
            if material_id is None:
                raise CodeError(ServiceCode, u"选中的物料数据传输有误")

            material_id_list = json.loads(material_id)
            baseinfo_op = Baseinfo_Op()
            count = baseinfo_op.check_material(operate_type, material_id_list)
        except CodeError as e:
            return_data = json.dumps(e.json_value())
        except Exception as e:
            print traceback.format_exc(e)
            return_data = json.dumps(
                {'code': ServiceCode.service_exception, 'msg': u"服务器成功"})
        else:
            datas['code'] = ServiceCode.success
            datas['count'] = count
            return_data = json.dumps(datas)
        finally:
            return tools.en_return_data(return_data)


class InfoDetail(MethodView):
    """
    显示单个物料信息页面
    """
    @staticmethod
    def get():
        data = {}
        try:
            t_id = int(request.values.get('id').encode())
            base_info_op = Baseinfo_Op()

            flags, return_data = base_info_op.get_baseinfo_by_id(t_id)
            if flags == 0:
                data = {'code': ServiceCode.success, 'rows': return_data}
            else:
                data = {'code': ServiceCode.notfound, 'msg': return_data}
        except Exception as ex:
            print(traceback.format_exc())
            data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
        finally:
            return tools.en_render_template(
                'supplyChain/materiel/detail_Manage.html',
                result=json.dumps(data))


class AddInfoDisplay(MethodView):
    """
    添加物料渲染页面
    """
    @staticmethod
    def get():
        # 物料所有分类信息
        category_op = CategoryOp()
        body = category_op.get_all_category_count(is_add=1)
        mc_list = body['data']

        # 物料属性列表
        m_attr_type = SupplyAttr.MATERIAL_ATTRIBUTE_TYPE
        m_attr_list = translate_dict_to_list(m_attr_type)

        # 计划策略
        plan_s_type = SupplyAttr.MATERILA_PLAN_STRATEGY
        plan_s = translate_dict_to_list(plan_s_type)

        # 计划模式
        plan_type = SupplyAttr.MATERIAL_PLAN_MODELS
        plan_m = translate_dict_to_list(plan_type)

        # 订货策略
        order_type = SupplyAttr.MATERIAL_ORDER_STRATEGY
        order_s = translate_dict_to_list(order_type)

        # 检验方式
        check_type = SupplyAttr.MATERIAL_QUALITY_CHECK_TYPE
        check_dict = translate_dict_to_list(check_type)

        # 计量单位列表
        base_op = Baseinfo_Op()
        unit_list = base_op.save_measure_unit()

        return_data = {
            'code': ServiceCode.success,
            'mc_list': mc_list,
            'm_attr_list': m_attr_list,
            'plan_s': plan_s,
            'plan_m': plan_m,
            'order_s': order_s,
            'check_type': check_dict,
            'unit_list': unit_list
            }
        return tools.en_render_template(
            'supplyChain/materiel/addMaterial.html',
            result=json.dumps(return_data))

    # def post(self):
    #     try:
    #         baseinfo_op = Baseinfo_Op()
    #
    #
    #         option = {}
    #         option['code_id'] = request.form['code_id']
    #         option['category_code'] = int(request.form['category_code'])
    #         option['m_name'] = request.form['name']
    #         option['fullname'] = request.form['fullname']
    #         option['old_code'] = request.form.get('old_code', None)
    #         option['specifications'] = request.form.get('specifications', None)
    #         option['attribute_id'] = request.form['attribute_id']
    #         option['auditor'] = request.form.get('auditor', None)
    #         option['adjunct'] = request.form.get('adjunct', None)
    #         option['state'] = SupplyAttr.MATERIAL_STATE_UNUSE
    #         # option['state'] = baseinfo_op.STATE_USE
    #         option['rem1'] = request.form.get('rem1', None)
    #
    #         data = {}
    #         if baseinfo_op.add_info(option):
    #             # 添加操作记录
    #             uid = session['user']['id']
    #             baseinfo_op.add_operate_record(uid, u'新增物料信息', id)
    #             data['code'] = ServiceCode.success
    #
    #     except Exception as ex:
    #         print(ex)
    #         print(traceback.format_exc())
    #         data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
    #         return tools.en_return_data(json.jsonify(data))
    #     else:
    #         return tools.en_return_data(json.jsonify(data))


class CheckCode(MethodView):
    """
    检查物料代码
    """

    @staticmethod
    def post():
        return_data = None
        try:
            base_info = Baseinfo_Op()
            code_id = request.values.get('code_id', None)

            if code_id is None:
                raise CodeError(code=ServiceCode.params_error, msg=u"参数不能为空！")

            if base_info.check_code_id(code_id.encode()):
                return_data = {
                    'code': ServiceCode.existence,
                    'msg': u'存在相同代码'
                }
            else:
                return_data = {
                    'code': ServiceCode.success
                }
        except CodeError:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {
                'code': ServiceCode.data_empty,
                'msg': u'检测数据在服务器中找不到'
            }
        finally:
            return tools.en_return_data(json.jsonify(return_data))


class MaterialUpload(MethodView):
    """
    上传物料图片视图类
    """

    @staticmethod
    def post():
        data = {}
        try:
            file_type = int(request.values.get('file_type', 1, int))  # 0:图片, 1:文件
            describe = request.values.get('describe', "")
            operater = session.get('user')['id']
            user_op = MixUserCenterOp()
            user_data = user_op.get_user_info(operater)
            filename = request.files.get('file').filename

            upload_op = UploadOp()
            state, msg = upload_op.upload(file_type, os.path.join(UploadConfig.SERVER_ERP_FIle), filename=filename,
                    allowFiles=['doc', 'docx', 'xls', 'xlsx', 'pdf', 'ppt', 'pptx', 'png', 'jpg', 'gif', 'bmp', 'svg', 'jpeg'])
            if not state and state != 0:
                msg['size'] = msg['file_size']
                msg.pop('file_size')
                data = {'code': ServiceCode.authcode_error, "msg": msg}

            else:
                # 获得物料code_id从物料映射表中映射出所有相关的文件信息
                msg['size'] = msg['file_size']
                msg.pop('file_size')
                msg['time'] = msg['time'].strftime("%Y-%m-%d %H:%M:%S")
                msg['describe'] = describe.encode()
                msg['operater'] = user_data['name']

                data = {
                    'code': ServiceCode.success,
                    'file_list': msg}

            return tools.en_return_data(json.jsonify(data))
        except CodeError as e:
            print traceback.format_exc()
            data = e.json_value()
        except Exception as ex:
            print(ex)
            SystemLog.pub_warninglog(traceback.format_exc())
            data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
        finally:
            return tools.en_return_data(json.jsonify(data))


class InfoOperateRecord(MethodView):
    """
    显示物料操作记录（数据接口)
    """

    def get(self):
        return_data = None
        try:
            start = int(request.values.get('start', 0))
            per_page = int(request.values.get('per_page', 10))
            code_id = request.values.get('code_id', '').encode()

            if start < 0:
                return_data = {'code': ServiceCode.params_error, 'msg': u'起始记录必须不小于0'}
            elif per_page <= 0:
                return_data = {'code': ServiceCode.params_error, 'msg': u'每页显示记录数必须大于0'}
            else:
                operate_op = Operate_Op()
                rows = operate_op.get_record(
                    start, per_page, Baseinfo_Op().TABEL_NAME, other_id=code_id)

                return_data = {
                    'code': ServiceCode.success,
                    'rows': rows[0],
                    'start': start,
                    'per_page': per_page,
                    'total': rows[1]}
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
        finally:
            return tools.en_return_data(json.jsonify(return_data))

# 新增2016-11-30


class AddMeasureUnit(MethodView):
    """"
    新增计量单位（数据接口)
    """
    @staticmethod
    def post():
        return_data = {}
        try:
            unit_code = request.values.get("unit_code", "")
            unit_name = request.values.get("unit_name", "")
            describe = request.values.get("describe", "")

            base_info = Baseinfo_Op()
            data = base_info.save_measure_unit(unit_code, unit_name, describe)
            return_data = {
                'code': ServiceCode.success,
                'unit_list': data
            }
        except CodeError as e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
        finally:
            return tools.en_return_data(json.dumps(return_data))


class ChocieSupplierList(MethodView):
    """
    选择供应商
    """
    @staticmethod
    def post():
        return_data = {}
        try:
            search_type = request.values.get('searchType', 2, int)
            search_value = request.values.get('searchValue', '', str)
            current_page = request.values.get('currentPage', 1, int)
            page_list = request.values.get('pageList', 10, int)
            supplier_list_info = SupplierListInfo()
            count, data = supplier_list_info.GetSupplierList(
                search_type, search_value, current_page, page_list)
            total = len(data)

            return_data = {
                    'code': ServiceCode.success,
                    'count': count,  # 记录总数
                    'total': total,  # 每页显示的记录数
                    'rows': data  # 数据，总共total条
                           }
        except CodeError as e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = e.json_value()
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
        finally:
            return tools.en_return_data(json.dumps(return_data))


class ChoiceWareHouseList(MethodView):
    """
    选择仓库 数据接口请求
    """
    @staticmethod
    def post():
        return_data = {}
        try:
            curr_page = int(request.values.get("curr_page", int))  # 当前页
            count = int(request.values.get("count", int))    # 当前页数需要显示的条数

            # 调用物料数据库信息接口，获取所有物料数据库信息
            material_warehouse_op = MaterialWarehouseInfoOp()
            return_data = material_warehouse_op.select_material_warehouse(page=curr_page-1, pagesize=count)

            if return_data['code'] == ServiceCode.success:
                # 通过warehouse_type_id转换成warehouse_type_name
                for data in return_data['data']:
                    for type in return_data['warehouse_type']:
                        if int(data['warehouse_type_id']) == int(type['id']):
                            data['warehouse_type_name'] = type['warehouse_type_name']

                return_data = {
                    'code': return_data['code'],
                    'total': return_data['total'],
                    'cur_page': len(return_data['data']),
                    'w_list': return_data['data']
                }
            else:
                return_data = {'code': ServiceCode.service_exception, 'msg': return_data['msg']}
        except CodeError as e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = e.json_value()
        except Exception as e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
        finally:
            return tools.en_return_data(json.dumps(return_data))


class SaveAddMaterial(MethodView):
    """
    保存添加物料信息 数据接口请求
    """

    @staticmethod
    def post():
        return_data = {}
        baseinfo_op = Baseinfo_Op()

        operater = session.get('user')['id']
        new_dict = {value: key for key, value in SupplyAttr.MATERIAL_STATE_TYPE.items()}

        try:
            option = dict()
            option['specifications'] = request.form.get('specifi', None)                # 类型id
            option['auditor'] = request.form.get('auditor', None)                       # 类型id
            option['state'] = new_dict[SupplyAttr.MATERIAL_STATE_UNUSE]                 # 类型id

            option['m_type'] = request.values.get('m_type', int)                        # 类型id
            option['code_id'] = request.values.get('m_code', str, None)                 # 类型id
            option['m_name'] = request.values.get('m_name', str, None)                  # 类型id
            option['m_old_code'] = request.values.get('m_old_code', str, None)          # 类型id
            option['m_attribute_id'] = request.values.get('m_attribute_id', str, None)  # 类型id
            option['m_unit'] = request.values.get('m_unit', str, None)                  # 类型id
            option['bar_code'] = request.values.get('bar_code', str, None)              # 类型id
            option['s_code'] = request.values.get('s_code', str, None)                  # 类型id
            option['s_barname'] = request.values.get('s_barname', str, None)            # 类型id
            option['co_packer_ocde'] = request.values.get('co_packer_ocde', str, None)  # 类型id
            option['co_name'] = request.values.get('co_name', str, None)                # 类型id
            option['s_attr_rate'] = request.values.get('s_attr_rate', float)            # 类型id
            option['is_pour_ware'] = int(request.values.get('is_pour_ware', int).encode())   # 类型id
            option['pour_ware_id'] = request.values.get('pour_ware_id', int)            # 类型id
            option['tax_rate'] = request.values.get('tax_rate', float)                  # 类型id
            option['min_count'] = request.values.get('min_count', int).encode()         # 类型id
            option['max_count'] = request.values.get('max_count', int).encode()         # 类型id
            option['plan_strategy'] = request.values.get('plan_strategy', str, None)    # 类型id
            option['plan_model'] = request.values.get('plan_model', str, None)          # 类型id
            option['order_strategy'] = request.values.get('order_strategy', str, None)  # 类型id
            option['rem1'] = request.values.get('describe', str, None)                  # 类型id

            # 计划资料
            option['auto_integer'] = request.values.get('auto_integer', int)
            option['merge_need'] = request.values.get('merge_need', int)
            option['buy_applicate'] = request.values.get('buy_applicate', int)
            option['fixed_lead_time'] = request.values.get('fixed_lead_time', float).encode()   # 类型id
            print "option['fixed_lead_time']", option['fixed_lead_time']
            option['change_lead_time'] = request.values.get('change_lead_time', float).encode()  # 类型id
            print "option['change_lead_time']", option['change_lead_time']
            option['add_lead_time'] = request.values.get('add_lead_time', float).encode()               # 类型id
            print "option['add_lead_time']", option['add_lead_time']
            option['order_interval_time'] = request.values.get('order_interval_time', float).encode()   # 类型id
            print "option['order_interval_time']", option['order_interval_time']

            # 质量资料
            option['buy_check_type'] = request.values.get('buy_check_type', int).encode()           # 类型id
            option['pro_check_type'] = request.values.get('pro_check_type', int).encode()           # 类型id
            option['co_check_type'] = request.values.get('co_check_type', int).encode()             # 类型id
            option['send_check_type'] = request.values.get('send_check_type', int).encode()         # 类型id
            option['return_check_type'] = request.values.get('return_check_type', int).encode()     # 类型id
            option['ware_check_type'] = request.values.get('ware_check_type', int).encode()         # 类型id
            option['other_check_type'] = request.values.get('other_check_type', int).encode()       # 类型id

            # 附件
            option['file_list'] = request.values.get('file_list', None)     # 附件列表
            option['file_list'] = json.loads(option['file_list'])

            # pic
            option['pic_info'] = request.values.get('pic_info', None)
            if option['pic_info'] is not None:
                option['pic_info'] = json.loads(option['pic_info'])
            else:
                option['pic_info'] = {}
            option['operater'] = operater       # 操作人id
            option['file_list'].append(option['pic_info'])

            t_id = f_id = w_id = None
            msg, t_id = baseinfo_op.add_info(option)
            try:
                if msg:
                    # 添加文件记录
                    op = FileManageOp()
                    if option['file_list'] is not None:
                        for info in option['file_list']:
                            # 保存上传文件信息到物料映射表中
                            if info:
                                save_temp = dict()
                                save_temp['operater_id'] = int(operater)
                                save_temp['upload_id'] = info['id']
                                save_temp['code_id'] = option['code_id']
                                save_temp['describe'] = info['describe'] if info.get('describe', None) else None
                                f_id = op.SaveFileData(save_temp)

                    # 判断仓库有没有被使用
                    material_warehouse_op = MaterialWarehouseInfoOp()
                    if option['pour_ware_id']:
                        w_msg, w_id = material_warehouse_op.warehouse_link_status(option['pour_ware_id'])
                        if w_msg:
                            return_data['code'] = ServiceCode.success
                        else:
                            raise CodeError(code=ServiceCode.warehose_is_not_exist, msg=u'物料仓库id不存在！')
                    return_data['code'] = ServiceCode.success
                else:
                    raise CodeError(code=ServiceCode.uploadSourceError, msg=u'文件上传失败！')
            except CodeError as e:
                SystemLog.pub_warninglog(traceback.format_exc())
                code, msg = e.value()
                if baseinfo_op.rollback_by_id(t_id, f_id, w_id):
                    SystemLog.pub_infolog(u"rollback success!")
                    raise CodeError(code=code, msg=u"错误数据已经回滚！")
                else:
                    raise CodeError(code=code, msg=msg + u' 错误数据回滚失败')
            except Exception as e:
                SystemLog.pub_warninglog(traceback.format_exc())
                if baseinfo_op.rollback_by_id(t_id, f_id, w_id):
                    SystemLog.pub_infolog(u"rollback success!")
                else:
                    raise

        except CodeError as e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = e.json_value()
        except Exception as e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
        finally:
            return tools.en_return_data(json.dumps(return_data))


class ShowMaterialInfo(MethodView):
    """
    查看已存在的物料信息 数据接口请求
    """

    @staticmethod
    def get():
        return_data = {}
        try:
            m_code = request.values.get('m_code', "")

            base_op = Baseinfo_Op()
            msg, data = base_op.get_baseinfo_by_code(m_code)
            if msg != 0:
                raise CodeError(code=ServiceCode.data_empty, msg=data)

            # 供应商信息
            supplier_base_info = SupplierBaseInfoOp()
            s_data = supplier_base_info.get_supplier_base_info_by_code(data['s_name'])

            # 仓库信息
            material_warehouse_op = MaterialWarehouseInfoOp()
            ware_data = material_warehouse_op.get_warehouse_name_by_id(data['pour_ware_id'])

            # 用户
            operater = session.get('user')['id']
            user_op = MixUserCenterOp()
            user_data = user_op.get_user_info(operater)

            # bom 信息
            base_bom_op = BomBaseOp()
            is_use_bom, msg = base_bom_op.is_used(data['code'])

            return_data = {
                'm_type': data['category_id'],  # 类型
                'm_type_name': data['category_name'],
                'm_type_code': data['category_code'],
                'm_code':  data['code'],  # 物料编码
                'm_code_id': data['id'],
                'm_name': data['name'],  # 物料名称
                'm_old_code': data['old_code'],  # 物料旧编码
                'm_attribute_id': data['attribute_name'],  # 物料属性name
                'm_unit':  data['measureunit'],  # 物料计量单位id
                'm_unit_name': base_op.get_measure_name(data['measureunit']),
                'specifi': data['specifications'],  # 规格型号
                'bar_code': data['m_bar_code'],  # 物料条形码
                's_code': data['s_name'],
                's_name': s_data['supplier_name'] if s_data else None,  # 供应商名字
                's_barname': data['s_barname'],  # 品牌
                'co_packer_ocde': data['co_packer_ocde'],  # 加工厂代码
                'co_name': data['co_name'],  # 加工厂物料名称
                's_attr_rate': data['s_attr_rate'] / COVERT_DATA_TO_WASTEUNIT_NUMBER if data[
                    's_attr_rate'] else data['s_attr_rate'],  # 标准损耗率
                'is_pour_ware':  0 if data['is_pour_ware'] == 0 else 1,  # 是否是倒冲仓 （true 是，false 否）
                'pour_ware_id': data['pour_ware_id'],  # 倒冲仓id
                'pour_ware_name': ware_data['warehouse_name'] if ware_data else None,
                'tax_rate': data['tax_rate'] / COVERT_INT_TO_TAC_RATE if data['tax_rate'] else data['tax_rate'],  # 税率
                'min_count': data['min_count'],  # 最小订货量
                'max_count': data['max_count'],  # 最大订货量
                'plan_strategy': SupplyAttr.MATERILA_PLAN_STRATEGY.get(data['plan_strategy'], None),  # 计划策略name
                'plan_model': SupplyAttr.MATERIAL_PLAN_MODELS.get(data['plan_model'], None),  # 计划模式name
                'order_strategy': SupplyAttr.MATERIAL_ORDER_STRATEGY.get(data['order_strategy'], None),  # 订货策略name
                'describe': data['rem1'],  # 备注
                'state': SupplyAttr.MATERIAL_STATE_TYPE.get(data['state'], None),
                'is_use_bom': is_use_bom,

                'auto_integer': u'否' if data['auto_integer'] == 0 else u'是',  # 投料是否取整（true 是， false 否）
                'merge_need': u'否' if data['merge_need'] == 0 else u'是',  # MRP计算是否需要合并（true 是， false 否）
                'buy_applicate': u'否' if data['buy_applicate'] == 0 else u'是',  # MRP计算是否产生采购申请（true 是， false
                'fixed_lead_time': data['fixed_lead_time'] / COVERT_INT_TO_DATE_NUMBER if data[
                    'fixed_lead_time'] else None,  # 固定提前期
                'change_lead_time': data['change_lead_time'] / COVERT_INT_TO_DATE_NUMBER if data[
                    'change_lead_time'] else None,  # 变动提前期
                'add_lead_time': data['add_lead_time'] / COVERT_INT_TO_DATE_NUMBER if data[
                    'add_lead_time'] else None,   # 累计提前期
                'order_interval_time': data['order_interval_time'] / COVERT_INT_TO_DATE_NUMBER if data[
                    'order_interval_time'] else None,  # 订货间隔期


                'buy_check_type': SupplyAttr.MATERIAL_QUALITY_CHECK_TYPE.get(
                    data['buy_check_type'], None),   # 采购检验方式 （1、免检，2、抽检， 3、全检）
                'pro_check_type': SupplyAttr.MATERIAL_QUALITY_CHECK_TYPE.get(
                    data['pro_check_type'], None),  # 产品检验方式
                'co_check_type': SupplyAttr.MATERIAL_QUALITY_CHECK_TYPE.get(
                    data['co_check_type'], None),    # 委外加工检验方式
                'send_check_type': SupplyAttr.MATERIAL_QUALITY_CHECK_TYPE.get(
                    data['send_check_type'], None),  # 发货检验方式
                'return_check_type': SupplyAttr.MATERIAL_QUALITY_CHECK_TYPE.get(
                    data['return_check_type'], None),  # 退货检验方式
                'ware_check_type': SupplyAttr.MATERIAL_QUALITY_CHECK_TYPE.get(
                    data['ware_check_type'], None),   # 库存检验方式
                'other_check_type': SupplyAttr.MATERIAL_QUALITY_CHECK_TYPE.get(
                    data['other_check_type'], None)   # 其他检验方式
            }

            # 获得物料code_id从物料映射表中映射出所有相关的文件信息
            upload_op = UploadOp()
            file_op = FileManageOp()
            temp_list = []
            file_info = file_op.GetFileByCodeId(m_code)
            if file_info is not None:
                for info in file_info:
                    in_data = info.to_json()
                    upload_id = in_data['upload_id']
                    file_info_data = upload_op.GetFileById(upload_id)
                    file_info_data['name'] = file_info_data['filename']
                    file_info_data.pop('filename')
                    file_info_data['time'] = file_info_data['time'].strftime("%Y-%m-%d %H:%M:%S")
                    file_info_data['describe'] = in_data['describe'] if in_data.get('describe', None) else None
                    if user_data is not None:
                        file_info_data['operater'] = user_data['name']
                    else:
                        file_info_data['operater'] = ""
                    if file_info_data['fileType'] == 0:
                        return_data['pic_info'] = file_info_data
                        continue
                    temp_list.append(file_info_data)
                return_data['file_list'] = temp_list
            # file_data = base_op.get_material_file_info(m_code)###优化

            return_data = {
                'code': ServiceCode.success,
                'return_data': return_data
            }
        except CodeError as e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = e.json_value()
        except Exception as e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
        finally:
            return tools.en_render_template(
                'supplyChain/materiel/materialDetail.html',
                result=json.dumps(return_data))


class DownloadMaterialFile(MethodView):
    """
    下载查看附件和图片 数据接口请求
    """
    @staticmethod
    def post():
        file_id = request.values.get('upload_id', type=int)
        return_data = {}
        t_file = None
        try:
            op = UploadOp()
            if not file_id:
                print("[ DownloadFile ] incoming param is error", file_id)
                raise CodeError(code=ServiceCode.params_error, msg=u'传入参数有误')

            t_file = op.GetFileById(file_id)
            if not t_file:
                print("[ DownloadFile ] file is not exist", file_id)
                raise CodeError(code=ServiceCode.fileNotExist, msg=u'文件不存在')

            # 自增下载次数
            op.IncrementDownloadCount(file_id)
            return_data = {
                'code': ServiceCode.success,
                'url': t_file.get('qiniu_addr')
            }

        except CodeError as e:
            return_data = e.json_value()
            SystemLog.pub_warninglog(traceback.format_exc())
        except Exception as e:
            return_data = {
                'code': ServiceCode.downloadFile,
                'url': t_file.get('qiniu_addr')
            }
            SystemLog.pub_warninglog(traceback.format_exc())
        finally:
            return tools.en_return_data(json.dumps(return_data))


class EditMaterial(MethodView):
    """
    编辑物料信息 页面
    """

    @staticmethod
    def get():
        return_data = {}
        try:
            m_code = request.values.get('m_code', "")
            base_op = Baseinfo_Op()
            msg, data = base_op.get_baseinfo_by_code(m_code)
            if msg != 0:
                raise CodeError(code=ServiceCode.data_empty, msg=data)

            # 物料所有分类信息
            category_op = CategoryOp()
            body = category_op.get_all_category_count(is_add=1)
            mc_list = body['data']

            # 物料属性列表
            m_attr_type = SupplyAttr.MATERIAL_ATTRIBUTE_TYPE
            m_attr_list = translate_dict_to_list(m_attr_type)

            # 计划策略
            plan_s_type = SupplyAttr.MATERILA_PLAN_STRATEGY
            plan_s = translate_dict_to_list(plan_s_type)

            # 计划模式
            plan_type = SupplyAttr.MATERIAL_PLAN_MODELS
            plan_m = translate_dict_to_list(plan_type)

            # 订货策略
            order_type = SupplyAttr.MATERIAL_ORDER_STRATEGY
            order_s = translate_dict_to_list(order_type)

            # 检验方式
            check_type = SupplyAttr.MATERIAL_QUALITY_CHECK_TYPE
            check_dict = translate_dict_to_list(check_type)

            # 计量单位列表
            base_op = Baseinfo_Op()
            unit_list = base_op.save_measure_unit()

            # 供应商信息
            supplier_base_info = SupplierBaseInfoOp()
            s_data = supplier_base_info.get_supplier_base_info_by_code(data['s_name'])

            # 仓库信息
            material_warehouse_op = MaterialWarehouseInfoOp()
            ware_data = material_warehouse_op.get_warehouse_name_by_id(data['pour_ware_id'])

            operater = session.get('user')['id']
            user_op = MixUserCenterOp()
            user_data = user_op.get_user_info(operater)

            return_data = {
                'm_type': data['category_id'],                          # 类型
                'm_type_name': data['category_name'],
                'm_code': data['code'],                                 # 物料编码
                'm_name': data['name'],                                 # 物料名称
                'm_old_code': data['old_code'],                         # 物料旧编码
                'm_attribute_id': data['attribute_id'],                 # 物料属性name
                'm_unit': data['measureunit'],                          # 物料计量单位name
                'specifi': data['specifications'],                      # 规格型号
                'bar_code': data['m_bar_code'],                         # 物料条形码
                's_code': data['s_name'],
                's_name': s_data['supplier_name'] if s_data else None,  # 供应商名字
                's_barname': data['s_barname'],                         # 品牌
                'co_packer_ocde': data['co_packer_ocde'],               # 加工厂代码
                'co_name': data['co_name'],                             # 加工厂物料名称
                's_attr_rate': data['s_attr_rate'] / COVERT_DATA_TO_WASTEUNIT_NUMBER if data[
                    's_attr_rate'] else data['s_attr_rate'],  # 标准损耗率
                'is_pour_ware': 0 if data['is_pour_ware'] == 0 else 1,  # 是否是倒冲仓 （true 是，false 否）
                'pour_ware_id': data['pour_ware_id'],                    # 倒冲仓id
                'pour_ware_name': ware_data['warehouse_name'] if ware_data else None,  # 倒冲仓名字
                'tax_rate': data['tax_rate'] / COVERT_INT_TO_TAC_RATE if data[
                    'tax_rate'] else data['tax_rate'],  # 税率
                'min_count': data['min_count'],                         # 最小订货量
                'max_count': data['max_count'],                         # 最大订货量
                'plan_strategy': data['plan_strategy'],                 # 计划策略name
                'plan_model': data['plan_model'],                       # 计划模式name
                'order_strategy': data['order_strategy'],               # 订货策略name
                'describe': data['rem1'],                               # 备注
                'state': SupplyAttr.MATERIAL_STATE_TYPE.get(data['state'], None),  # 物料使用状态

                'auto_integer': 0 if data['auto_integer'] == 0 else 1,      # 投料是否取整（true 是， false 否）
                'merge_need': 0 if data['merge_need'] == 0 else 1,          # MRP计算是否需要合并（true 是， false 否）
                'buy_applicate': 0 if data['buy_applicate'] == 0 else 1,    # MRP计算是否产生采购申请（true 是， false
                'fixed_lead_time': data['fixed_lead_time'] / COVERT_INT_TO_DATE_NUMBER if data[
                    'fixed_lead_time'] else None,  # 固定提前期
                'change_lead_time': data['change_lead_time'] / COVERT_INT_TO_DATE_NUMBER if data[
                    'change_lead_time'] else None,  # 变动提前期
                'add_lead_time': data['add_lead_time'] / COVERT_INT_TO_DATE_NUMBER if data[
                    'add_lead_time'] else None,   # 累计提前期
                'order_interval_time': data['order_interval_time'] / COVERT_INT_TO_DATE_NUMBER if data[
                    'order_interval_time'] else None,  # 订货间隔期

                'buy_check_type': data['buy_check_type'],                   # 采购检验方式 （1、免检，2、抽检， 3、全检）
                'pro_check_type': data['pro_check_type'],                   # 产品检验方式
                'co_check_type': data['co_check_type'],                     # 委外加工检验方式
                'send_check_type': data['send_check_type'],                 # 发货检验方式
                'return_check_type': data['return_check_type'],             # 退货检验方式
                'ware_check_type': data['ware_check_type'],                 # 库存检验方式
                'other_check_type': data['other_check_type']                # 其他检验方式
            }

            # 物料信息文件
            upload_op = UploadOp()
            file_op = FileManageOp()
            temp_list = []
            file_info = file_op.GetFileByCodeId(m_code)
            if isinstance(file_info, MaterialFileInfo):
                file_info = [file_info]
            if file_info is not None:
                for info in file_info:
                    in_data = info.to_json()
                    upload_id = in_data['upload_id']
                    file_info_data = upload_op.GetFileById(upload_id)
                    file_info_data['name'] = file_info_data['filename']
                    file_info_data.pop('filename')
                    file_info_data['time'] = file_info_data['time'].strftime("%Y-%m-%d %H:%M:%S")
                    file_info_data['describe'] = in_data['describe']
                    if user_data is not None:
                        file_info_data['operater'] = user_data['name']
                    else:
                        file_info_data['operater'] = ""
                    if file_info_data['fileType'] == 0:
                        return_data['pic_info'] = file_info_data
                        continue
                    temp_list.append(file_info_data)
                return_data['file_list'] = temp_list

            return_data = {
                'code': ServiceCode.success,
                'return_data': return_data,
                'operatecount': data['operatecount'],  # 根据操作记录判断是否可以编辑,0:可编辑，非0不可编辑
                'mc_list': mc_list,
                'm_attr_list': m_attr_list,
                'plan_s': plan_s,
                'plan_m': plan_m,
                'order_s': order_s,
                'check_type': check_dict,
                'unit_list': unit_list
            }
        except CodeError as e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = e.json_value()
        except Exception as e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
        finally:
            return tools.en_render_template(
                'supplyChain/materiel/editMaterial.html',
                result=json.dumps(return_data))


class SaveEditMaterialInfo(MethodView):
    """
    保存物料编辑信息 （数据请求接口）
    """

    @staticmethod
    def post():
        return_data = {}
        base_info_op = Baseinfo_Op()

        operater = session.get('user')['id']
        new_dict = {value: key for key, value in SupplyAttr.MATERIAL_STATE_TYPE.items()}

        try:
            option = dict()
            option['specifications'] = request.form.get('specifi', None)                # 类型id
            option['auditor'] = request.form.get('auditor', None)                       # 类型id
            option['state'] = new_dict[SupplyAttr.MATERIAL_STATE_UNUSE]                 # 类型id
            option['m_type'] = request.values.get('m_type', int)                        # 类型id
            option['code_id'] = request.values.get('m_code', str, None)
            option['old_code_id'] = request.values.get('old_code_id', str, None)
            option['m_name'] = request.values.get('m_name', str, None)                  # 类型id
            option['m_old_code'] = request.values.get('m_old_code', str, None)          # 类型id
            option['m_attribute_id'] = request.values.get('m_attribute_id', str, None)  # 类型id
            option['m_unit'] = request.values.get('m_unit', str, None)                  # 类型id
            option['bar_code'] = request.values.get('bar_code', str, None)              # 类型id
            option['s_code'] = request.values.get('s_code', str, None)                  # 类型id
            option['s_barname'] = request.values.get('s_barname', str, None)            # 类型id
            option['co_packer_ocde'] = request.values.get('co_packer_ocde', str, None)  # 类型id
            option['co_name'] = request.values.get('co_name', str, None)                # 类型id
            option['s_attr_rate'] = request.values.get('s_attr_rate', float)            # 类型id
            option['is_pour_ware'] = int(request.values.get('is_pour_ware', int).encode())           # 类型id
            option['pour_ware_id'] = request.values.get('pour_ware_id', int)            # 类型id
            option['tax_rate'] = request.values.get('tax_rate', float)                  # 类型id
            option['min_count'] = request.values.get('min_count', int).encode()         # 类型id
            option['max_count'] = request.values.get('max_count', int).encode()         # 类型id
            option['plan_strategy'] = request.values.get('plan_strategy', str, None)    # 类型id
            option['plan_model'] = request.values.get('plan_model', str, None)          # 类型id
            option['order_strategy'] = request.values.get('order_strategy', str, None)  # 类型id
            option['rem1'] = request.values.get('describe', str, None)                  # 类型id

            # 计划资料
            option['auto_integer'] = request.values.get('auto_integer', int)
            option['merge_need'] = request.values.get('merge_need', int)
            option['buy_applicate'] = request.values.get('buy_applicate', int)
            option['fixed_lead_time'] = request.values.get('fixed_lead_time', float).encode()   # 类型id
            option['change_lead_time'] = request.values.get('change_lead_time', float).encode()  # 类型id
            option['add_lead_time'] = request.values.get('add_lead_time', float).encode()               # 类型id
            option['order_interval_time'] = request.values.get('order_interval_time', float).encode()   # 类型id

            # 质量资料
            option['buy_check_type'] = request.values.get('buy_check_type', int).encode()           # 类型id
            option['pro_check_type'] = request.values.get('pro_check_type', int).encode()           # 类型id
            option['co_check_type'] = request.values.get('co_check_type', int).encode()             # 类型id
            option['send_check_type'] = request.values.get('send_check_type', int).encode()         # 类型id
            option['return_check_type'] = request.values.get('return_check_type', int).encode()     # 类型id
            option['ware_check_type'] = request.values.get('ware_check_type', int).encode()         # 类型id
            option['other_check_type'] = request.values.get('other_check_type', int).encode()       # 类型id

            # 附件
            option['file_list'] = request.values.get('file_list', None)     # 附件列表
            option['file_list'] = json.loads(option['file_list'])

            # pic
            option['pic_info'] = request.values.get('pic_info', None)
            if option['pic_info'] is not None:
                option['pic_info'] = json.loads(option['pic_info'])
            else:
                option['pic_info'] = {}
            option['operater'] = operater       # 操作人id
            option['file_list'].append(option['pic_info'])

            db_session = f_id = w_id = None
            msg, db_session = base_info_op.save_edit_info(option)
            try:
                if msg:
                    # 添加文件记录
                    op = FileManageOp()
                    if option['file_list'] is not None:
                        temp_list = []
                        for info in option['file_list']:
                            # 保存上传文件信息到物料映射表中
                            if info:
                                save_temp = dict()
                                save_temp['operater_id'] = int(operater)
                                save_temp['upload_id'] = info['id']
                                save_temp['code_id'] = option['code_id']
                                save_temp['describe'] = info['describe'] if info.get('describe', None) else None
                                temp_list.append(save_temp)
                        f_id = op.SaveFileDataFromEdit(temp_list)

                    material_warehouse_op = MaterialWarehouseInfoOp()
                    if option['pour_ware_id']:
                        w_msg, w_id = material_warehouse_op.warehouse_link_status(option['pour_ware_id'])
                        if w_msg:
                            return_data['code'] = ServiceCode.success
                        else:
                            raise CodeError(code=ServiceCode.warehose_is_not_exist, msg=u'物料仓库id不存在！')
                    db_session.commit()
                    return_data['code'] = ServiceCode.success
                else:
                    raise CodeError(code=ServiceCode.uploadSourceError, msg=u'文件上传失败！')
            except CodeError as e:
                SystemLog.pub_warninglog(traceback.format_exc())
                db_session.rollback()
                code, msg = e.value()
                if base_info_op.rollback_by_id(file_id=f_id, warehouse_id=w_id):
                    print "rollback success!"
                    raise CodeError(code=code, msg=u"错误数据已经回滚！")
                else:
                    raise CodeError(code=code, msg=msg + u' 错误数据回滚失败')
            except Exception as e:
                db_session.rollback()
                SystemLog.pub_warninglog(traceback.format_exc())
                if base_info_op.rollback_by_id(file_id=f_id, warehouse_id=w_id):
                    print "rollback success!"
                else:
                    raise

        except CodeError as e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = e.json_value()
        except Exception as e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
        finally:
            return tools.en_return_data(json.dumps(return_data))


class CopyMaterialInfo(MethodView):
    """
    复制（新增物料信息）
    """

    @staticmethod
    def get():
        return_data = {}
        try:
            m_code = request.values.get('m_code', "")

            # 物料所有分类信息
            category_op = CategoryOp()
            body = category_op.get_all_category_count(is_add=1)
            mc_list = body['data']

            # 物料属性列表
            m_attr_type = SupplyAttr.MATERIAL_ATTRIBUTE_TYPE
            m_attr_list = translate_dict_to_list(m_attr_type)

            # 计划策略
            plan_s_type = SupplyAttr.MATERILA_PLAN_STRATEGY
            plan_s = translate_dict_to_list(plan_s_type)

            # 计划模式
            plan_type = SupplyAttr.MATERIAL_PLAN_MODELS
            plan_m = translate_dict_to_list(plan_type)

            # 订货策略
            order_type = SupplyAttr.MATERIAL_ORDER_STRATEGY
            order_s = translate_dict_to_list(order_type)

            # 检验方式
            check_type = SupplyAttr.MATERIAL_QUALITY_CHECK_TYPE
            check_dict = translate_dict_to_list(check_type)

            # 计量单位列表
            base_op = Baseinfo_Op()
            unit_list = base_op.save_measure_unit()

            base_op = Baseinfo_Op()
            msg, data = base_op.get_baseinfo_by_code(m_code)
            if msg != 0:
                raise CodeError(code=ServiceCode.data_empty, msg=data)

            # 供应商信息
            supplier_base_info = SupplierBaseInfoOp()
            s_data = supplier_base_info.get_supplier_base_info_by_code(data['s_name'])

            # 仓库信息
            material_warehouse_op = MaterialWarehouseInfoOp()
            ware_data = material_warehouse_op.get_warehouse_name_by_id(data['pour_ware_id'])

            operater = session.get('user')['id']
            user_op = MixUserCenterOp()
            user_data = user_op.get_user_info(operater)

            return_dict = {
                # 基础资料
                'm_type': data['category_id'],                      # 类型
                'm_type_name': data['category_name'],               # 类型名称
                'm_code':  data['code'],                            # 物料编码
                'm_name': data['name'],                             # 物料名称
                'm_old_code': data['old_code'],                     # 物料旧编码
                'm_attribute_id': data['attribute_id'],             # 物料属性name
                'm_unit':  data['measureunit'],                     # 物料计量单位name
                'specifi': data['specifications'],                  # 规格型号
                'bar_code': data['m_bar_code'],                     # 物料条形码
                's_code': data['s_name'],
                's_name': s_data['supplier_name'] if s_data else None,   # 供应商名字
                's_barname': data['s_barname'],                     # 品牌
                'co_packer_ocde': data['co_packer_ocde'],           # 加工厂代码
                'co_name': data['co_name'],                        # 加工厂物料名称
                's_attr_rate': data['s_attr_rate'] / COVERT_DATA_TO_WASTEUNIT_NUMBER if data[
                    's_attr_rate'] else data['s_attr_rate'],  # 标准损耗率
                'is_pour_ware':  0 if data['is_pour_ware'] == 0 else 1,  # 是否是倒冲仓 （true 是，false 否）
                'pour_ware_id': data['pour_ware_id'],                   # 倒冲仓名字
                'pour_ware_name': ware_data['warehouse_name'] if ware_data else None,
                'tax_rate': data['tax_rate'] / COVERT_INT_TO_TAC_RATE if data['tax_rate'] else data['tax_rate'],  # 税率
                'min_count': data['min_count'],                     # 最小订货量
                'max_count': data['max_count'],                     # 最大订货量
                'plan_strategy': data['plan_strategy'],             # 计划策略name
                'plan_model': data['plan_model'],                   # 计划模式name
                'order_strategy': data['order_strategy'],           # 订货策略name
                'describe': data['rem1'],                           # 备注
                'state': SupplyAttr.MATERIAL_STATE_TYPE.get(data['state'], None),  # 物料使用状态

                # 质量信息
                'auto_integer': 0 if data['auto_integer'] == 0 else 1,   # 投料是否取整（true 是， false 否）
                'merge_need': 0 if data['merge_need'] == 0 else 1,       # MRP计算是否需要合并（true 是， false 否）
                'buy_applicate': 0 if data['buy_applicate'] == 0 else 1,  # MRP计算是否产生采购申请（true 是， false
                'fixed_lead_time': data['fixed_lead_time'] / COVERT_INT_TO_DATE_NUMBER if data[
                    'fixed_lead_time'] else None,  # 固定提前期
                'change_lead_time': data['change_lead_time'] / COVERT_INT_TO_DATE_NUMBER if data[
                    'change_lead_time'] else None,  # 变动提前期
                'add_lead_time': data['add_lead_time'] / COVERT_INT_TO_DATE_NUMBER if data[
                    'add_lead_time'] else None,   # 累计提前期
                'order_interval_time': data['order_interval_time'] / COVERT_INT_TO_DATE_NUMBER if data[
                    'order_interval_time'] else None,  # 订货间隔期

                # 计划信息
                'buy_check_type': data['buy_check_type'],           # 采购检验方式 （1、免检，2、抽检， 3、全检）
                'pro_check_type': data['pro_check_type'],           # 产品检验方式
                'co_check_type': data['co_check_type'],             # 委外加工检验方式
                'send_check_type': data['send_check_type'],         # 发货检验方式
                'return_check_type': data['return_check_type'],     # 退货检验方式
                'ware_check_type': data['ware_check_type'],         # 库存检验方式
                'other_check_type': data['other_check_type']        # 其他检验方式
            }

            # 物料信息文件
            upload_op = UploadOp()
            file_op = FileManageOp()
            temp_list = []
            file_info = file_op.GetFileByCodeId(m_code)
            if file_info is not None:
                for info in file_info:
                    if info:
                        in_data = info.to_json()
                        upload_id = in_data['upload_id']
                        file_info_data = upload_op.GetFileById(upload_id)
                        file_info_data['name'] = file_info_data['filename']
                        file_info_data.pop('filename')
                        file_info_data['time'] = file_info_data['time'].strftime("%Y-%m-%d %H:%M:%S")
                        file_info_data['describe'] = in_data['describe']
                        if user_data is not None:
                            file_info_data['operater'] = user_data['name']
                        else:
                            file_info_data['operater'] = ""
                        if file_info_data['fileType'] == 0:
                            return_dict['pic_info'] = file_info_data
                            continue
                        temp_list.append(file_info_data)
                return_dict['file_list'] = temp_list

            return_data = {
                'code': ServiceCode.success,
                'return_data': return_dict,
                'mc_list': mc_list,
                'm_attr_list': m_attr_list,
                'plan_s': plan_s,
                'plan_m': plan_m,
                'order_s': order_s,
                'check_type': check_dict,
                'unit_list': unit_list
            }
        except CodeError as e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = e.json_value()
        except Exception as e:
            print e
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
        finally:
            return tools.en_render_template(
                'supplyChain/materiel/copyMaterial.html',
                result=json.dumps(return_data))


class ShowNextMaterialInfo(MethodView):
    """
    展示下一条物料信息
    """

    @staticmethod
    def post():
        return_data = {}
        try:
            code_id = request.values.get('code_id', "")
            base_op = Baseinfo_Op()
            msg, base_mater_data = base_op.get_next_for_currency_id(code_id)
            m_code = None
            if msg == 0:
                m_code = base_mater_data["code"]
            else:
                print "msg :", base_mater_data
                raise CodeError(code=ServiceCode.data_empty, msg=base_mater_data)

            return_data = {
                'code': ServiceCode.success,
                'return_data': m_code
            }
        except CodeError as e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = e.json_value()
        except Exception as e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
        finally:
            return tools.en_return_data(json.dumps(return_data))


class ShowFrontMaterialInfo(MethodView):
    """
    展示上一条物料信息
    """

    @staticmethod
    def post():
        return_data = {}
        try:
            code_id = request.values.get('code_id', "")

            base_op = Baseinfo_Op()
            msg, base_mater_data = base_op.get_front_for_currency_id(code_id)
            m_code = None
            if msg == 0:
                m_code = base_mater_data["code"]
            else:
                raise CodeError(code=ServiceCode.data_empty, msg=base_mater_data)

            return_data = {
                'code': ServiceCode.success,
                'return_data': m_code
            }
        except CodeError as e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = e.json_value()
        except Exception as e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return_data = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
        finally:
            return tools.en_return_data(json.dumps(return_data))

add_url.add_url(
    u"物料信息",
    "baseinfo.material_index",
    add_url.TYPE_ENTRY,
    baseinfo_prefix,
    baseinfo,
    '/info/display_info/',
    'info',
    DisplayBaseinfo.as_view('info'),
    methods=['GET'])

add_url.add_url(
    u"物料搜索",
    "baseinfo.info",
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/info/search/',
    'SelectMaterialInfo',
    SelectMaterialInfo.as_view('SelectMaterialInfo'),
    methods=['POST']
)

add_url.add_url(
    u"物料状态切换",
    "baseinfo.info",
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/info/changestate',
    'ChangeMaterialState',
    ChangeMaterialState.as_view('ChangeMaterialState'),
    methods=['POST']
)

add_url.add_url(
    u"检测物料状态切换合法性",
    "baseinfo.info",
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/info/checkstate/',
    'CheckMaterialState',
    CheckMaterialState.as_view('CheckMaterialState'),
    methods=['POST']
)

add_url.add_url(
    u'显示物料添加页面',
    'baseinfo.info',
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/info/add/display',
    'AddInfoDisplay',
    AddInfoDisplay.as_view('AddInfoDisplay'),
    methods=['GET', 'POST'])

add_url.add_url(
    u'检查物料代码',
    'baseinfo.AddInfoDisplay',
    add_url.TYPE_FUNC,
    baseinfo_prefix,
    baseinfo,
    '/info/add/check_code_id',
    'checkCode',
    CheckCode.as_view('checkCode'),
    methods=['POST'])

add_url.add_url(
    u'上传物料图片',
    'baseinfo.AddInfoDisplay',
    add_url.TYPE_FUNC,
    baseinfo_prefix,
    baseinfo,
    '/info/add/image',
    'AddImage',
    MaterialUpload.as_view('AddImage'),
    methods=['POST'])

add_url.add_url(
    u'物料操作记录',
    'baseinfo.info',
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/info/operate_records/',
    'InfoOperateRecord',
    InfoOperateRecord.as_view('InfoOperateRecord'),
    methods=['GET']
)

# ####################################################
# 2016-11-30 新增路由
# ####################################################
add_url.add_url(
    u'新增计量单位',
    'baseinfo.AddInfoDisplay',
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/info/add/add_measureunit',
    'add_measureunit',
    AddMeasureUnit.as_view('add_measureunit'),
    methods=['POST'])

add_url.add_url(
    u'选择供应商',
    'baseinfo.AddInfoDisplay',
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/info/add/chocie_supplier_list',
    'chocie_supplier_list',
    ChocieSupplierList.as_view('chocie_supplier_list'),
    methods=['POST'])

add_url.add_url(
    u'选择仓库',
    'baseinfo.AddInfoDisplay',
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/info/add/chocie_warehouse_list',
    'chocie_warehouse_list',
    ChoiceWareHouseList.as_view('chocie_warehouse_list'),
    methods=['POST'])

add_url.add_url(
    u'保存新增物料信息',
    'baseinfo.AddInfoDisplay',
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/info/add/save_add_material',
    'save_add_material',
    SaveAddMaterial.as_view('save_add_material'),
    methods=['POST'])

# ################################
# 编辑物料信息
# ################################
add_url.add_url(
    u'编辑物料信息',
    'baseinfo.info',
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/info/edit_material_info',
    'edit_material_info',
    EditMaterial.as_view('edit_material_info'),
    methods=['GET'])

add_url.add_url(
    u'保存物料编辑信息',
    'baseinfo.info',
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/info/save_edit_material_info',
    'save_edit_material_info',
    SaveEditMaterialInfo.as_view('save_edit_material_info'),
    methods=['POST'])


# ################################
# 查看物料信息
# ################################
add_url.add_url(
    u'查看物料信息',
    'baseinfo.info',
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/info/show_material_info',
    'show_material_info',
    ShowMaterialInfo.as_view('show_material_info'),
    methods=['GET'])

add_url.add_url(
    u'物料文件下载',
    'baseinfo.show_material_info',
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/info/download_material_file',
    'download_material_file',
    DownloadMaterialFile.as_view('download_material_file'),
    methods=['POST'])

add_url.add_url(
    u'下一条物料记录',
    'baseinfo.show_material_info',
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/info/shownext_material_info',
    'shownext_material_info',
    ShowNextMaterialInfo.as_view('shownext_material_info'),
    methods=['POST'])

add_url.add_url(
    u'上一条物料记录',
    'baseinfo.show_material_info',
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/info/showfront_material_info',
    'showfront_material_info',
    ShowFrontMaterialInfo.as_view('showfront_material_info'),
    methods=['POST'])


# ####################################
# 复制物料信息
# ####################################
add_url.add_url(
    u'复制增物料信息',
    'baseinfo.info',
    add_url.TYPE_FEATURE,
    baseinfo_prefix,
    baseinfo,
    '/info/copy_material_info',
    'copy_material_info',
    CopyMaterialInfo.as_view('copy_material_info'),
    methods=['GET'])

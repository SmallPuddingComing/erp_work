#-*-coding:utf-8-*-
import traceback
from flask.views import MethodView
from flask import request
import json
from config.service_config.returncode import ServiceCode
from public.function import tools
from control_center.supply_chain.material_warehosue.control.material_warehose_info_op import MaterialWarehouseInfoOp
from public.logger.syslog import SystemLog
from control_center.admin import add_url
from control_center.supply_chain import baseinfo_prefix, baseinfo


class MaterialWarehouseManage(MethodView):
    @staticmethod
    def get():
        return tools.en_render_template('supplyChain/warehouse/warehouse_info.html')


class MaterialWarehouseInfo(MethodView):
    @staticmethod
    def get():
        try:
            search_list = [{'id': 1, 'val': u'仓库类型'}, {'id': 2, 'val': u'仓库名称'}, {'id': 3, 'val': u'仓库编码'}]
            page = request.args.get('page', 0, int)
            pagesize = request.args.get('pagesize', 10, int)
            # warehouse_code = request.args.get('warehouse_code', '')
            # warehouse_name = request.args.get('warehouse_name', '')
            # warehouse_type_name = request.args.get('warehouse_type_name', '')
            warehouse_code = ''
            warehouse_name = ''
            warehouse_type_name = ''
            key = request.args.get('key', 0, int)
            val = request.args.get('val', '')
            if key == 1:
                warehouse_type_name = val
            elif key == 2:
                warehouse_name = val
            elif key == 3:
                warehouse_code = val
            is_page = request.args.get('is_page', 0, int)
            material_warehouse_op = MaterialWarehouseInfoOp()
            res = material_warehouse_op.select_material_warehouse(page,
                                                                  pagesize,
                                                                  warehouse_code=warehouse_code,
                                                                  warehouse_name=warehouse_name,
                                                                  warehouse_type_name=warehouse_type_name)
            if res['code'] == ServiceCode.success:
                res['search_list'] = search_list
                result = res
            else:
                result = {'code': ServiceCode.service_exception, 'data': '', 'warehouse_type': '', 'total': '',
                          'search_list': search_list}

            if is_page == 1:
                return tools.en_return_data(json.dumps(result))
            else:
                return tools.en_render_template('supplyChain/warehouse/warehouse_info.html', result=json.dumps(result))
        except Exception,e:
            SystemLog.pub_warninglog(traceback.format_exc())


class MaterialAddWarehouseInfo(MethodView):
    @staticmethod
    def get():
        try:
            para_dict = dict()
            para_dict['warehouse_code'] = request.args.get('warehouse_code', '')
            para_dict['warehouse_name'] = request.args.get('warehouse_name', '')
            para_dict['warehouse_type_id'] = request.args.get('warehouse_type_id', '')
            para_dict['contacts'] = request.args.get('contacts', '')
            para_dict['contact_phone'] = request.args.get('contact_phone', '')
            para_dict['province'] = request.args.get('province', '')
            para_dict['city'] = request.args.get('city', '')
            para_dict['county'] = request.args.get('county', '')
            para_dict['address'] = request.args.get('address', '')
            para_dict['is_minus_stock'] = request.args.get('is_minus_stock', '')
            para_dict['is_mrp_mps'] = request.args.get('is_mrp_mps', '')
            para_dict['is_accounting'] = request.args.get('is_accounting', '')
            para_dict['rem'] = request.args.get('rem', '')
            if not para_dict['warehouse_code'] or not para_dict['warehouse_name'] or not para_dict['warehouse_type_id']:
                result = {'code': ServiceCode.params_error, 'msg': u'参数不全'}
                return tools.en_return_data(json.dumps(result))
            material_warehouse_op = MaterialWarehouseInfoOp()

            res = material_warehouse_op.add_material_warehouse(para_dict)
            if res['code'] == ServiceCode.success:
                result = {'code': ServiceCode.success, 'msg': u'添加成功'}
            elif res['code'] == ServiceCode.service_exception:
                result = {'code': ServiceCode.params_error, 'msg': u'插入数据重复'}
            else:
                result = {'code': ServiceCode.service_exception, 'msg': u'添加失败'}
            return tools.en_return_data(json.dumps(result))
        except Exception,e:
            SystemLog.pub_warninglog(traceback.format_exc())
            result = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            return tools.en_return_data(json.dumps(result))


class MaterialCheckWarehouseInfo(MethodView):
    @staticmethod
    def get():
        try:
            material_warehouse_op = MaterialWarehouseInfoOp()
            warehouse_name = request.args.get('warehouse_name', '')
            warehouse_code = request.args.get('warehouse_code', '')
            warehouse_id = request.args.get('warehouse_id', '')
            res = material_warehouse_op.MaterialCheckWarehouseName(warehouse_name=warehouse_name,
                                                                   warehouse_code=warehouse_code,
                                                                   warehouse_id=warehouse_id)
            msg = ''
            if warehouse_name:
                msg = u'仓库名字重复'
            if warehouse_code:
                msg = u'仓库编码重复'
            if res:
                result = {'code': ServiceCode.service_exception, 'msg': msg}
            else:
                result = {'code': ServiceCode.success, 'msg': u'可用'}
            return tools.en_return_data(json.dumps(result))

        except Exception,e:
            SystemLog.pub_warninglog(traceback.format_exc())
            result = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            return tools.en_return_data(json.dumps(result))


class MaterialUpdateWarehouseInfo(MethodView):
    @staticmethod
    def get():
        try:
            para_dict = dict()
            para_dict['warehouse_id'] = request.args.get('warehouse_id', '')
            para_dict['warehouse_code'] = request.args.get('warehouse_code', '')
            para_dict['warehouse_name'] = request.args.get('warehouse_name', '')
            para_dict['warehouse_type_id'] = request.args.get('warehouse_type_id', '')
            para_dict['contacts'] = request.args.get('contacts', '')
            para_dict['contact_phone'] = request.args.get('contact_phone', '')
            para_dict['province'] = request.args.get('province', '')
            para_dict['city'] = request.args.get('city', '')
            para_dict['county'] = request.args.get('county', '')
            para_dict['address'] = request.args.get('address', '')
            para_dict['is_minus_stock'] = request.args.get('is_minus_stock', '')
            para_dict['is_mrp_mps'] = request.args.get('is_mrp_mps', '')
            para_dict['is_accounting'] = request.args.get('is_accounting', '')
            para_dict['rem'] = request.args.get('rem', '')
            material_warehouse_op = MaterialWarehouseInfoOp()
            res = material_warehouse_op.MaterialUpdateWarehouse(para_dict)
            if res['code'] == ServiceCode.success:
                result = {'code': ServiceCode.success, 'msg': u'修改成功'}
            elif res['code'] == ServiceCode.service_exception:
                result = {'code': ServiceCode.service_exception, 'msg': u'数据重复插入'}
            else:
                result = {'code': ServiceCode.service_exception, 'msg': u'修改失败'}
            return tools.en_return_data(json.dumps(result))
        except Exception,e:
            SystemLog.pub_warninglog(traceback.format_exc())
            result = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            return tools.en_return_data(json.dumps(result))


class MaterialWarehouseType(MethodView):
    @staticmethod
    def get():
        try:
            material_warehouse_op = MaterialWarehouseInfoOp()
            page = request.args.get('page', 0, int)
            pagesize = request.args.get('pagesize', 10, int)
            is_page = request.args.get('is_page', 0, int)
            res = material_warehouse_op.select_material_warehouse_type(page, pagesize)
            result = {'code': ServiceCode.success, 'total': res[1], 'data': res[0]}
            if is_page == 1:
                return tools.en_return_data(json.dumps(result))
            else:
                return tools.en_render_template('supplyChain/warehouse/warehouse_type.html', result=json.dumps(result))
        except Exception,e:
            SystemLog.pub_warninglog(traceback.format_exc())


class MaterialAddWarehouseType(MethodView):
    @staticmethod
    def get():
        result = {}
        try:
            warehouse_type_name = request.args.get('warehouse_type_name', '')
            warehouse_type_code = request.args.get('warehouse_type_code', '')
            warehouse_type_rem = request.args.get('warehouse_type_rem', '')
            if not warehouse_type_code or not warehouse_type_name:
                result = {'code': ServiceCode.params_error, 'msg': u'仓库类型名或者仓库类型编码不能为空'}
                return tools.en_return_data(json.dumps(result))
            material_warehouse_op = MaterialWarehouseInfoOp()
            res = material_warehouse_op.add_material_warehouse_type(warehouse_type_name=warehouse_type_name,
                                                                    warehouse_type_code=warehouse_type_code,
                                                                    warehouse_type_rem=warehouse_type_rem)
            if res['code'] == ServiceCode.success:
                result = {'code': ServiceCode.success, 'msg': u'添加'}
            elif res['code'] == ServiceCode.service_exception:
                result = {'code': ServiceCode.service_exception, 'msg': u'插入数据重复'}
            return tools.en_return_data(json.dumps(result))
        except Exception,e:
            SystemLog.pub_warninglog(traceback.format_exc())
            result = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            return tools.en_return_data(json.dumps(result))


class MaterialUpdateWarehouseType(MethodView):
    @staticmethod
    def get():
        result = {}
        try:
            warehouse_type_id = request.args.get('warehouse_type_id', 0, int)
            warehouse_type_code = request.args.get('warehouse_type_code', '')
            warehouse_type_name = request.args.get('warehouse_type_name', '')
            warehouse_type_rem = request.args.get('warehouse_type_rem', '')
            if not warehouse_type_id:
                result = {'code': ServiceCode.params_error, 'msg': u'仓库类型ID不能为空'}
                return tools.en_return_data(json.dumps(result))
            material_warehouse_op = MaterialWarehouseInfoOp()
            res = material_warehouse_op.update_material_warehouse_type(warehouse_type_id=warehouse_type_id,
                                                                       warehouse_type_code=warehouse_type_code,
                                                                       warehouse_type_name=warehouse_type_name,
                                                                       warehouse_type_rem=warehouse_type_rem)
            if res['code'] == ServiceCode.success:
                result = {'code': ServiceCode.success, 'msg': u'修改成功'}
            elif res['code'] == ServiceCode.service_exception:
                result = {'code': ServiceCode.service_exception, 'msg': u'重复插入'}
            return tools.en_return_data(json.dumps(result))
        except Exception,e:
            SystemLog.pub_warninglog(traceback.format_exc())
            result = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            return tools.en_return_data(json.dumps(result))


class MaterialCheckCode(MethodView):
    @staticmethod
    def get():
        try:
            warehouse_type_code = request.args.get('warehouse_type_code')
            warehouse_type_name = request.args.get('warehouse_type_name')
            material_warehouse_op = MaterialWarehouseInfoOp()
            res = material_warehouse_op.material_type_code_check(warehouse_type_code=warehouse_type_code,
                                                                 warehosue_type_name=warehouse_type_name)
            msg = ''
            if warehouse_type_name:
                msg = u'仓库类型名重复'
            elif warehouse_type_code:
                msg = u'仓库类型编码重复'
            if res:
                result = {'code': ServiceCode.service_exception, 'msg': msg}
            else:
                result = {'code': ServiceCode.success, 'msg': u'编码可用'}
            return tools.en_return_data(json.dumps(result))
        except Exception,e:
            SystemLog.pub_warninglog(traceback.format_exc())
            result = {'code': ServiceCode.service_exception, 'msg': u'服务器错误'}
            return tools.en_return_data(json.dumps(result))


class MaterialDelWarehouseType(MethodView):
    @staticmethod
    def get():
        try:
            warehose_type_id = request.args.get('warehouse_type_id', 0, int)
            page = request.args.get('page', 0, int)
            if not warehose_type_id:
                result = {'code': ServiceCode.params_error, 'msg': u'仓库类型ID不能为空'}
                return tools.en_return_data(json.dumps(result))
            material_warehouse_op = MaterialWarehouseInfoOp()
            res = material_warehouse_op.material_type_del(warehose_type_id, page=page)
            if res['code'] == ServiceCode.success:
                result = res
            elif res['code'] == ServiceCode.check_error:
                result = {'code': ServiceCode.params_error, 'msg': u'删除失败,被使用中'}
            else:
                result = {'code': ServiceCode.params_error, 'msg': u'删除失败'}
            return tools.en_return_data(json.dumps(result))
        except Exception,e:
            SystemLog.pub_warninglog(traceback.format_exc())
            result = {'code': ServiceCode.service_exception, 'msg': u'删除失败'}
            return tools.en_return_data(json.dumps(result))


class MaterialDelWarehouseInfo(MethodView):
    @staticmethod
    def get():
        try:
            warehouse_id = request.args.get('warehouse_id', 0, int)
            page = request.args.get('page', 0, int)
            if not warehouse_id:
                result = {'code': ServiceCode.params_error, 'msg': u'仓库类型ID不能为空'}
                return tools.en_return_data(json.dumps(result))
            material_warehouse_op = MaterialWarehouseInfoOp()
            res = material_warehouse_op.MareiraDelWarehouse(warehouse_id, page)
            if res['code'] == ServiceCode.success:
                result = res
            elif res['code'] == ServiceCode.params_error:
                result = {'code': ServiceCode.params_error, 'msg': u'仓库被使用，删除失败'}
            else:
                result = {'code': ServiceCode.params_error, 'msg': u'删除失败'}
            return tools.en_return_data(json.dumps(result))
        except Exception,e:
            SystemLog.pub_warninglog(traceback.format_exc())
            result = {'code': ServiceCode.service_exception, 'msg': u'删除失败'}
            tools.en_return_data(json.dumps(result))


add_url.add_url(u"仓库",
                "baseinfo.index",
                add_url.TYPE_ENTRY,
                baseinfo_prefix,
                baseinfo,
                '/base_warehouse_manage/',
                'MaterialWarehouseManage',
                MaterialWarehouseManage.as_view('MaterialWarehouseManage'),
                methods=['POST', 'GET'])

add_url.add_url(u"仓库信息",
                "baseinfo.MaterialWarehouseManage",
                add_url.TYPE_ENTRY,
                baseinfo_prefix,
                baseinfo,
                '/base_warehouse_info/',
                'MaterialWarehouseInfo',
                MaterialWarehouseInfo.as_view('MaterialWarehouseInfo'),
                100,
                methods=['POST', 'GET'])

add_url.add_url(u"添加仓库信息",
                "baseinfo.MaterialWarehouseInfo",
                add_url.TYPE_FEATURE,
                baseinfo_prefix,
                baseinfo,
                '/add_warehouse_info/',
                'MaterialAddWarehouseInfo',
                MaterialAddWarehouseInfo.as_view('MaterialAddWarehouseInfo'),
                methods=['POST', 'GET'])

add_url.add_url(u"编辑仓库信息",
                "baseinfo.MaterialWarehouseInfo",
                add_url.TYPE_FEATURE,
                baseinfo_prefix,
                baseinfo,
                '/update_warehouse_info/',
                'MaterialUpdateWarehouseInfo',
                MaterialUpdateWarehouseInfo.as_view('MaterialUpdateWarehouseInfo'),
                methods=['POST', 'GET'])

add_url.add_url(u"删除仓库信息",
                "baseinfo.MaterialWarehouseInfo",
                add_url.TYPE_FEATURE,
                baseinfo_prefix,
                baseinfo,
                '/del_warehouse_info/',
                'MaterialDelWarehouseInfo',
                MaterialDelWarehouseInfo.as_view('MaterialDelWarehouseInfo'),
                methods=['POST', 'GET'])

add_url.add_url(u"检测仓库名称或者仓库类型唯一",
                "baseinfo.MaterialWarehouseInfo",
                add_url.TYPE_FEATURE,
                baseinfo_prefix,
                baseinfo,
                '/check_warehouse_name/',
                'MaterialCheckWarehouseInfo',
                MaterialCheckWarehouseInfo.as_view('MaterialCheckWarehouseInfo'),
                methods=['POST', 'GET'])

add_url.add_url(u"仓库类型",
                "baseinfo.MaterialWarehouseManage",
                add_url.TYPE_ENTRY,
                baseinfo_prefix,
                baseinfo,
                '/base_warehouse_type/',
                'MaterialWarehouseType',
                MaterialWarehouseType.as_view('MaterialWarehouseType'),
                90,
                methods=['POST', 'GET'])

add_url.add_url(u"添加仓库类型",
                "baseinfo.MaterialWarehouseType",
                add_url.TYPE_FEATURE,
                baseinfo_prefix,
                baseinfo,
                '/add_warehouse_type/',
                'MaterialAddWarehouseType',
                MaterialAddWarehouseType.as_view('MaterialAddWarehouseType'),
                methods=['POST', 'GET'])

add_url.add_url(u"修改仓库类型",
                "baseinfo.MaterialWarehouseType",
                add_url.TYPE_FEATURE,
                baseinfo_prefix,
                baseinfo,
                '/update_warehouse_type/',
                'MaterialUpdateWarehouseType',
                MaterialUpdateWarehouseType.as_view('MaterialUpdateWarehouseType'),
                methods=['POST', 'GET'])

add_url.add_url(u"检测仓库类型代码",
                "baseinfo.MaterialWarehouseType",
                add_url.TYPE_FEATURE,
                baseinfo_prefix,
                baseinfo,
                '/check_warehouse_type_code/',
                'MaterialCheckCode',
                MaterialCheckCode.as_view('MaterialCheckCode'),
                methods=['POST', 'GET'])

add_url.add_url(u"删除仓库类型",
                "baseinfo.MaterialWarehouseType",
                add_url.TYPE_FEATURE,
                baseinfo_prefix,
                baseinfo,
                '/del_warehouse_type/',
                'MaterialDelWarehouseType',
                MaterialDelWarehouseType.as_view('MaterialDelWarehouseType'),
                methods=['POST', 'GET'])

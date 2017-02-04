#-*- coding:utf-8 -*-
import traceback, math
from data_mode.erp_supply.control_base.controlBase import ControlEngine
from data_mode.erp_supply.mode.material_manage_mode.material_warehouse import MaterialWarehouseType,MaterialWarehouse
from sqlalchemy import or_, and_, func
from config.service_config.returncode import ServiceCode
from public.logger.syslog import SystemLog


class MaterialWarehouseInfoOp(ControlEngine):
    def __init__(self):
        ControlEngine.__init__(self)

    def add_material_warehouse_type(self, warehouse_type_name=None, warehouse_type_code=None, warehouse_type_rem=None):
        """
        添加仓库类型
        :param warehouse_type_name: 仓库类型名称
        :param warehouse_type_code: 仓库类型编码
        :param warehouse_type_rem:  仓库类型备注
        :return:
        """
        try:
            ch_res = self.controlsession.query(MaterialWarehouseType).filter(
                    or_(MaterialWarehouseType.warehouse_type_code == warehouse_type_code,
                        MaterialWarehouseType.warehouse_type_name == warehouse_type_name)).first()
            if ch_res:
                return {'code': ServiceCode.service_exception, 'msg': '插入数据重复'}
            else:
                warehouse_type_obj = MaterialWarehouseType(warehouse_type_name=warehouse_type_name,
                                                           warehouse_type_code=warehouse_type_code,
                                                           warehouse_type_rem=warehouse_type_rem)
                self.controlsession.add(warehouse_type_obj)
                self.controlsession.commit()
                return {'code': ServiceCode.success, 'msg': '添加成功'}
        except Exception,e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return {'code': ServiceCode.params_error, 'msg': '添加失败'}

    def update_material_warehouse_type(self,
                                       warehouse_type_name=None,
                                       warehouse_type_code=None,
                                       warehouse_type_rem=None,
                                       warehouse_type_id=None):
        """
        修改仓库类型
        :param warehouse_type_name:
        :param warehouse_type_code:
        :param warehouse_type_rem:
        :param warehouse_type_id:
        :return:
        """
        try:
            ch_res = self.controlsession.query(MaterialWarehouseType).filter(
                    or_(MaterialWarehouseType.warehouse_type_code == warehouse_type_code,
                        MaterialWarehouseType.warehouse_type_name == warehouse_type_name),
                    MaterialWarehouseType.id != warehouse_type_id).first()
            # print 'ch_res=',ch_res
            if ch_res:
                return {'code': ServiceCode.service_exception, 'msg': '插入数据重复'}
            else:
                res = self.controlsession.query(MaterialWarehouseType).filter(
                        MaterialWarehouseType.id == warehouse_type_id).first()
                if not res:
                    raise Exception('Not found the record in MaterialWarehouseType')
                res.warehouse_type_code = warehouse_type_code
                res.warehouse_type_name = warehouse_type_name
                res.warehouse_type_rem = warehouse_type_rem
                self.controlsession.add(res)
                self.controlsession.commit()
                return {'code': ServiceCode.success, 'msg': '修改成功'}
        except Exception, e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return {'code': ServiceCode.params_error, 'msg': '修改失败'}

    def select_material_warehouse_type(self, page=0, pagesize=10):
        try:
            start = page*pagesize
            # end = page*pagesize+pagesize
            condition = ''
            condition = 'and_('+condition+')'
            total = self.controlsession.query(func.count(MaterialWarehouseType.id)).scalar()
            if total > 0:
                if page > int(math.ceil(float(total)/pagesize)) - 1:
                    start = (page-1)*pagesize
            res = self.controlsession.query(MaterialWarehouseType).filter(eval(condition)).limit(pagesize).offset(start)
            res = [item.to_json() for item in res]

            return res, total
        except Exception,e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return False

    def material_type_code_check(self, warehouse_type_code=None, warehosue_type_name=None):
        try:
            condition = ''
            if warehosue_type_name:
                condition = "MaterialWarehouseType.warehouse_type_name =='%s'" % (warehosue_type_name)
            elif warehouse_type_code:
                condition = "MaterialWarehouseType.warehouse_type_code == '%s'" % (warehouse_type_code)
            else:
                pass
            condition = 'and_('+condition+')'
            res = self.controlsession.query(MaterialWarehouseType).filter(eval(condition)).first()
            if res:
                return True
            else:
                return False
        except Exception,e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return False

    def material_type_del(self, warehouse_type_id, page=0):
        try:

            obj = self.controlsession.query(MaterialWarehouse).filter(MaterialWarehouse.warehouse_type_id ==
                                                                      warehouse_type_id).first()
            if obj:
                return {'code': ServiceCode.check_error, 'msg': '仓库类型被使用'}

            del_obj = self.controlsession.query(MaterialWarehouseType).filter(MaterialWarehouseType.id ==
                                                                              warehouse_type_id).first()
            if not del_obj:
                raise Exception('没有查到相关数据')
            self.controlsession.delete(del_obj)
            self.controlsession.commit()
            res = self.select_material_warehouse_type(page=page, pagesize=10)
            return {'code': ServiceCode.success, 'msg': '删除成功', 'total': res[1], 'data': res[0]}
        except Exception,e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return {'code': ServiceCode.service_exception, 'msg': '服务器错误'}

    def select_material_warehouse(self, page=0, pagesize=10, warehouse_type_name=None, warehouse_name=None, warehouse_code=None):
        """
        :param page: 页码
        :param pagesize: 分页大小
        :param warehouse_type_name: 仓库类型名称
        :param warehouse_name: 长裤名称
        :param warehouse_code: 仓库编码
        :return:
        """
        try:
            start = pagesize * page
            condition = ''
            if warehouse_type_name:
                # print 'warehouse_type_name', warehouse_type_name
                warehouse_type_obj = self.controlsession.query(MaterialWarehouseType).\
                    filter(MaterialWarehouseType.warehouse_type_name == warehouse_type_name).first()
                # print 'warehouse_type_obj=',warehouse_type_obj
                warehouse_type_id = 0
                if warehouse_type_obj:
                    warehouse_type_id = warehouse_type_obj.id
                condition = "MaterialWarehouse.warehouse_type_id == %s" % (warehouse_type_id)
            elif warehouse_name:
                condition = "MaterialWarehouse.warehouse_name == '%s'" % (warehouse_name)
            elif warehouse_code:
                condition = "MaterialWarehouse.warehouse_code == '%s'" % (warehouse_code)
            else:
                condition = ''
            condition = 'and_('+condition+')'
            total = self.controlsession.query(func.count(MaterialWarehouse.id)).filter(eval(condition)).scalar()
            if total > 0:
                if page > int(math.ceil(float(total)/pagesize)) - 1:
                    start = (page-1)*pagesize
            # print 'start=', start
            res = self.controlsession.query(MaterialWarehouse).filter(eval(condition)).limit(pagesize).offset(start)
            warehouse_type = self.controlsession.query(MaterialWarehouseType).filter(
                        MaterialWarehouseType.warehouse_type_status == 0).all()
            warehouse_type = [item.to_id_name() for item in warehouse_type]
            if res:
                res = [item.to_json() for item in res]
                return {'total': total, 'data': res, 'warehouse_type': warehouse_type, 'code': ServiceCode.success, 'msg': 'OK'}
            else:
                return {'total': total, 'data': '', 'warehouse_type': warehouse_type, 'code': ServiceCode.success, 'msg': 'OK'}
        except Exception,e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return {'code': ServiceCode.service_exception, 'msg': '查询失败'}

    def warehouse_link_status(self, warehouse_id, link_name= None):
        """
        仓库被调用一次连接数+1
        :param warehouse_id: 仓库ID
        :param link_name 链接名
       :return: True:更新成功，False:更新状态失败
        """
        t_id = None
        # print "warehouse_id", warehouse_id
        try:
            if not warehouse_id:
                raise Exception('Warehouse ID can not be empty')
            link_obj = self.controlsession.query(MaterialWarehouse).filter(MaterialWarehouse.id ==
                                                                           warehouse_id).first()
            if not link_obj:
                raise Exception('Did not find the relevant data')
            link_obj.links = int(link_obj.links) + 1
            self.controlsession.add(link_obj)
            self.controlsession.commit()
            t_id = link_obj.id
            return (True, t_id)
        except Exception,e:
            SystemLog.pub_warninglog(traceback.format_exc())
            self.controlsession.rollback()
            return (False, t_id)

    def delete_warehouse_link(self, warehouse_id):
        """
        删除warehouse的链接数
        :param warehouse_id: int 仓库链接数
        :return: True or False
        """
        from public.function.tools import check_type
        check_type(warehouse_id, (int, long), 'warehouse_id')
        try:
            link = self.controlsession.query(MaterialWarehouse).filter(MaterialWarehouse.id == warehouse_id).first()
            if link is None:
                return False

            if link.links - 1 < 0:
                return False

            link.links = link.links -1
            self.controlsession.add(link)
            self.controlsession.commit()
            return True
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            self.controlsession.rollback()
            return False
        # else:
        #     return True

    def add_material_warehouse(self, para_dict):
        try:
            warehouse_code = para_dict.get('warehouse_code', '')
            warehouse_name = para_dict.get('warehouse_name', '')
            warehouse_type_id = para_dict.get('warehouse_type_id', '')
            contacts = para_dict.get('contacts', '')
            contact_phone = para_dict.get('contact_phone', '')
            province = para_dict.get('province', '')
            city = para_dict.get('city', '')
            county = para_dict.get('county', '')
            address = para_dict.get('address', '')
            is_minus_stock = para_dict.get('is_minus_stock', '')
            is_mrp_mps = para_dict.get('is_mrp_mps', '')
            is_accounting = para_dict.get('is_accounting', '')
            rem = para_dict.get('rem', '')

            ch_res = self.controlsession.query(MaterialWarehouse).filter(
                    or_(MaterialWarehouse.warehouse_code == warehouse_code,
                        MaterialWarehouse.warehouse_name == warehouse_name)).first()
            if ch_res:
                return {'code': ServiceCode.service_exception, 'msg': '插入数据重复'}
            else:
                obj = MaterialWarehouse(warehouse_type_id=warehouse_type_id,
                                        warehouse_code=warehouse_code,
                                        warehouse_name=warehouse_name,
                                        contacts=contacts,
                                        contact_phone=contact_phone,
                                        province=province,
                                        city=city,
                                        county=county,
                                        address=address,
                                        is_minus_stock=is_minus_stock,
                                        is_mrp_mps=is_mrp_mps,
                                        is_accounting=is_accounting,
                                        rem=rem)
                self.controlsession.add(obj)
                self.controlsession.commit()
                return {'code': ServiceCode.success, 'msg': '添加成功'}
        except Exception,e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return {'code': ServiceCode.params_error, 'msg': '添加失败'}

    def MaterialCheckWarehouseName(self, warehouse_name=None, warehouse_code=None, warehouse_id=None):
        try:
            condition = ''
            if warehouse_name:
                condition = 'MaterialWarehouse.warehouse_name == "%s"' % (warehouse_name)
            if warehouse_code:
                condition = 'MaterialWarehouse.warehouse_code == "%s"' % (warehouse_code)
            # condition = condition + ',MaterialWarehouse.id != %s' % (warehouse_id)
            condition = 'and_('+condition+')'
            res = self.controlsession.query(MaterialWarehouse).filter(eval(condition)).first()
            if res:
                return True
            else:
                return False
        except Exception,e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return False

    def MaterialUpdateWarehouse(self, para_dict):
        try:
            warehouse_id = para_dict.get('warehouse_id', '')
            ch_res = self.controlsession.query(MaterialWarehouse).filter(
                    or_(MaterialWarehouse.warehouse_code == para_dict.get('warehouse_code', ''),
                        MaterialWarehouse.warehouse_name == para_dict.get('warehouse_name', '')), MaterialWarehouse.id != warehouse_id).first()
            # print 'ch_res=',ch_res
            if ch_res:
                return {'code': ServiceCode.service_exception, 'msg': '插入数据重复'}
            update_obj = self.controlsession.query(MaterialWarehouse).filter(MaterialWarehouse.id == warehouse_id).first()
            if not update_obj:
                raise Exception('Not found the record in MaterialWarehouse')
            update_obj.warehouse_code = para_dict.get('warehouse_code', '')
            update_obj.warehouse_name = para_dict.get('warehouse_name', '')
            update_obj.warehouse_type_id = para_dict.get('warehouse_type_id', '')
            update_obj.contacts = para_dict.get('contacts', '')
            update_obj.contact_phone = para_dict.get('contact_phone', '')
            update_obj.province = para_dict.get('province', '')
            update_obj.city = para_dict.get('city', '')
            update_obj.county = para_dict.get('county', '')
            update_obj.address = para_dict.get('address', '')
            update_obj.is_minus_stock = para_dict.get('is_minus_stock', '')
            update_obj.is_mrp_mps = para_dict.get('is_mrp_mps', '')
            update_obj.is_accounting = para_dict.get('is_accounting', '')
            update_obj.rem = para_dict.get('rem', '')
            self.controlsession.add(update_obj)
            self.controlsession.commit()
            return {'code': ServiceCode.success, 'msg': '修改成功'}
        except Exception,e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return {'code': ServiceCode.params_error, 'msg': '修改失败'}

    def MareiraDelWarehouse(self, warehouse_id, page=0):
        try:
            res = self.controlsession.query(MaterialWarehouse).filter(MaterialWarehouse.id == warehouse_id).first()
            if res:
                if res.links == 0:
                    self.controlsession.delete(res)
                    self.controlsession.commit()
                    res = self.select_material_warehouse(page)
                    res['msg'] = '删除成功'
                    return res
                else:
                    return {'code': ServiceCode.params_error, 'msg': '仓库被使用，不能删除'}
            else:
                return {'code': ServiceCode.service_exception, 'msg': '没有相关数据'}

        except Exception,e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return {'code': ServiceCode.service_exception, 'msg': '删除失败'}

    def get_warehouse_name_by_id(self, warehouse_id):
        try:
            res = self.controlsession.query(MaterialWarehouse).filter(MaterialWarehouse.id == warehouse_id).first()
            if res:
                return res.to_json()
        except Exception, e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return None


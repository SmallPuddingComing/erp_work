#!/usr/bin/python
# -*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : material_warehouse_mix_op.py
#    作者   : DengLiming
#  电子邮箱 : lmdeng@jmgo.com
#    日期   : 2017/1/11 16:07
#
#     描述  :
#
import traceback, math
from data_mode.erp_supply.control_base.controlBase import ControlEngine
from data_mode.erp_supply.mode.material_manage_mode.material_warehouse import MaterialWarehouseType,MaterialWarehouse
from sqlalchemy import or_, and_, func
# from config.service_config.returncode import ServiceCode
from public.logger.syslog import SystemLog


class GetWarehouseInfo(ControlEngine):
    # 获取所有仓库信息（可根据仓库名、仓库编码，仓库类型搜索，同时支持分页查询）
    def get_warehouse_all(self,
                          warehouse_name=None,
                          warehouse_code=None,
                          warehouse_type=None,
                          page_size=None,
                          page_number=None):
        """

        :param warehouse_name: 仓库名称
        :param warehouse_code:仓库编码
        :param warehouse_type:仓库类型
        :param page_size:分页大小
        :param page_number:当前页码,默认第一页
        :return:
        """
        try:
            condition = ''
            if warehouse_name:
                condition = "MaterialWarehouse.warehouse_name == '%s'" % warehouse_name
            if warehouse_code:
                condition = "MaterialWarehouse.warehouse_code == '%s'" % warehouse_code
            if warehouse_type:
                c_type = self.get_warehouse_type_name(warehouse_type)
                condition = "MaterialWarehouse.warehouse_type_id == '%s'" % c_type['id']
            condition = "and_("+condition+")"

            if page_size and page_number:
                # 分页处理
                if page_size is not None and page_number is not None:
                    if page_size > 0 and page_number > 0:
                        start = (page_number-1) * page_size
                        total = self.controlsession.query(func.count(MaterialWarehouse.id)).filter(eval(condition)).scalar()
                        data = self.controlsession.query(MaterialWarehouse).filter(eval(condition)).limit(page_size).offset(start).all()
                        if data:
                            data = [item.to_data() for item in data]
                        else:
                            data = []
                        return total, data
                    else:
                        raise Exception(u'当前页码不能为负数')
                else:
                    raise Exception(u'参数错误')
            else:
                total = self.controlsession.query(func.count(MaterialWarehouse.id)).filter(eval(condition)).scalar()
                data = self.controlsession.query(MaterialWarehouse).filter(eval(condition)).all()
                if data:
                    data = [item.to_data() for item in data]
                else:
                    data = []
                return total, data

        except Exception:
            # SystemLog.pub_warninglog(traceback.format_exc())
            # raise Exception(u'查询失败')
            raise

    # 通过仓库类型名查询
    def get_warehouse_type_name(self, warehouse_type_name):
        try:
            if warehouse_type_name:
                data = self.controlsession.query(MaterialWarehouseType).filter(
                        MaterialWarehouseType.warehouse_type_name == warehouse_type_name).first()
                if data:
                    data = data.to_json()
                else:
                    data = {}
                return data
            else:
                raise ValueError(u'仓库类型名不能为空')
        except Exception:
            # SystemLog.pub_warninglog(traceback.format_exc())
            # raise Exception(u'通过ID获取仓库类型查询失败')
            raise

    # 获取仓库的部分信息
    def get_warehouse_list(self):
        try:
            res_all = self.controlsession.query(MaterialWarehouse).all()
            total = self.controlsession.query(func.count(MaterialWarehouse.id)).scalar()
            if res_all:
                res_all = [item.to_list() for item in res_all]
                id_list = list()
                for item in res_all:
                    id_list.append(item['pid'])
                id_list = set(id_list)
                warehouse_type = list()
                for item in id_list:
                    warehouse_dict = dict()
                    a = list()
                    for item1 in res_all:
                        b = dict()
                        if item == item1['pid']:
                            b['id'] = item1['id']
                            b['flag'] = 0
                            b['text'] = item1['warehouse_name']
                            a.append(b)
                    warehouse_dict['children'] = a
                    warehouse_dict['id'] = item
                    warehouse_dict['flag'] = 1
                    warehouse_dict['text'] = self.get_warehouse_type_id(item)['warehouse_type_name']
                    warehouse_type.append(warehouse_dict)

                data = warehouse_type
            else:
                data = []
            return data, total
        except Exception:
            # SystemLog.pub_warninglog(traceback.format_exc())
            # print traceback.format_exc()
            # raise Exception(u'查询仓库数据失败')
            raise

    # 通过仓库类型ID获取仓库类型名
    def get_warehouse_type_id(self, warehouse_type_id):
        try:
            if warehouse_type_id:
                res = self.controlsession.query(MaterialWarehouseType).filter(MaterialWarehouseType.id == warehouse_type_id).first()
                if res:
                    data = res.to_json()
                else:
                    data = {}
                return data
            else:
                raise KeyError(u'参数错误,仓库类型ID不能为空')
        except Exception:
            raise

    # 通过仓库ID获取对应数据
    def get_warehouse_id_info(self, warehouse_id):
        try:
            res = self.controlsession.query(MaterialWarehouse).filter(MaterialWarehouse.id == warehouse_id).first()
            if res:
                data = res.to_json()
            else:
                data = {}
            return data
        except Exception:
            raise

    def get_warehouse_type_by_id(self, warehouse_type_id):
        data = self.controlsession.query(MaterialWarehouseType).filter_by(id=warehouse_type_id).first()
        if data is None:
            raise ValueError("Can't find record in material_warehouse_type table when id=%s." % warehouse_type_id)
        return data.warehouse_type_name


if __name__ == '__main__':
    op = GetWarehouseInfo()
    # print op.get_warehouse_all(warehouse_type=u'工厂仓')
    # print op.get_warehouse_type_name(u'工厂仓')
    op.get_warehouse_list()

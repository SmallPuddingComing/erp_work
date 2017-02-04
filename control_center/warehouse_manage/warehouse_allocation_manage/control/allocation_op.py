#!/usr/bin/python
# -*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : allocation_op.py
#    作者   : WangYi
#  电子邮箱 : ywang@jmgo.com
#    日期   : 2017/1/12 18:10
#
#     描述  : 调库操作
#
from data_mode.erp_supply.control_base.controlBase import ControlEngine
from data_mode.erp_supply.mode.material_repertory_model.warehouse_allocation_invoice import WarehouseAllocationInvoice
from data_mode.erp_supply.mode.material_repertory_model.warehouse_allocation_detail import WarehouseAllocationDetail
from redis_cache.public_cache.serial_number import check_number_exists
from public.function.tools import check_type
from sqlalchemy import and_, func
from types import NoneType, FunctionType
import datetime
from control_center.supply_chain.material_warehosue.control.material_warehose_info_op import (
            MaterialWarehouseInfoOp)
from config.share.share_define import WarehouseManagementAttr as WMA
from flask import session


def add_warehouse_id_to_link(warehouse_id, link):
    if warehouse_id in link:
        link[warehouse_id] += 1
    else:
        link[warehouse_id] = 1
    return link


class AllocationOp(ControlEngine):
    def __init__(self):
        ControlEngine.__init__(self)
        self.__is_commit = True

    def __save_invoice_base(self, m_dict):
        """
        保存单据表信息
        :param m_dict:
         invoice_number: str		# 单据编号
         invoice_date: str			# 单据日期
         maker_id: int			    # 制单人ID
         invoice_type_id: int		# 单据类型ID
         invoice_state_id: int	    # 单据状态ID
         storeman_id: int			# 保管员ID
         allocation_type _id: int		# 调拨类型ID
         callOut_warehouse_id: str	# 调出仓库ID
         inspector_id: int		    # 验收员ID
         department_id: int			# 部门组织ID
         transferred_warehouse_id: int	# 调入仓库ID
         salesman_id: int			# 业务员ID
         remarks: str				# 备注
        :return:
        """
        def check_person_id(user_id_list):
            check_type(user_id_list, list, 'user_id_list')
            temp = set(user_id_list)
            format_str = "(" + "%s," * (len(temp) - 1) + "%s)"
            sql = "SELECT COUNT(1) from hola_control_center.admin_users WHERE id in " + format_str + \
                  " and is_active=1;"
            sql = sql % tuple(temp)
            result = self.controlsession.execute(sql)
            if result.fetchone()[0] != len(temp):
                return False
            else:
                return True

        def check_department_id(department_id_list):
            check_type(department_id_list, list, 'department_id_list')
            temp = set(department_id_list)
            if not len(temp):
                return True

            format_str = "(" + "%s," * (len(temp) - 1) + "%s)"
            sql = "SELECT COUNT(1) from hola_control_center.organ_department WHERE id in "  + format_str + ";"
            sql = sql % tuple(temp)
            result = self.controlsession.execute(sql)
            if result.fetchone()[0] != len(temp):
                return False
            else:
                return True

        def check_warehouse_id(warehouse_id_list):
            check_type(warehouse_id_list, list, 'warehouse_id_list')
            temp = set(warehouse_id_list)
            if not len(temp):
                return True

            format_str = "(" + "%s," * (len(temp) - 1) + "%s)"
            sql = "SELECT COUNT(1) from material_warehouse WHERE id in " + format_str +";"
            sql = sql % tuple(temp)
            result = self.controlsession.execute(sql)
            if result.fetchone()[0] != len(temp):
                return False
            else:
                return True

        def get_list(*args):
            t_list = []
            for element in args:
                if element:
                    t_list.append(element)
            return t_list

        # ####
        # 参数检测
        # #####
        m_list = get_list(m_dict['maker_id'],
                          m_dict['storeman_id'],
                          m_dict['inspector_id'],
                          m_dict.get('salesman_id')
                          )
        assert check_person_id(m_list), "person error:%s not exist" % m_list

        m_list = get_list(m_dict['department_id'])
        assert check_department_id(m_list), "department error:%s not exist" % m_list

        m_list = get_list(m_dict.get('callOut_warehouse_id'), m_dict.get('transferred_warehouse_id'))
        assert check_warehouse_id(m_list), "warehouse error:%s not exist" % m_list

        m_dict['invoice_date'] = datetime.datetime.now()
        if m_dict['allocation_type_id'] not in WMA.ALLOCATION_TYPE:
            raise ValueError("allocation_type_id not in WarehouseManagementAttr.ALLOCATION_TYPE range. %s" % (
                m_dict['allocation_type_id']))

        if m_dict['invoice_state_id'] not in WMA.INVOICE_STATE:
            raise ValueError("invoice_state_id not in WarehouseManagementAttr.INVOICE_STATE range. %s" % (
                m_dict['invoice_state_id']))

        if m_dict['invoice_state_id'] != WMA.TEMPORARY_STORAGE:
            raise ValueError("invoice_state_id value error.")

        # ###
        # 数据保存
        # ###
        if m_dict.get('id', None) is not None:
            invoice = self.controlsession.query(WarehouseAllocationInvoice).filter_by(id=m_dict['id']).first()
            invoice.inspector_id = m_dict['inspector_id']
            invoice.keeper_id = m_dict['storeman_id']
            invoice.salesman_id = m_dict.get('salesman_id')
            invoice.allocation_type_id = m_dict['allocation_type_id']
            invoice.callout_warehouse_id = m_dict.get('callOut_warehouse_id')
            invoice.transferred_warehouse_id = m_dict.get('transferred_warehouse_id')
            invoice.department_id = m_dict.get('department_id')
            invoice.remark = m_dict.get('remarks', '')
        else:
            invoice = WarehouseAllocationInvoice(
                invoice_number=m_dict['invoice_number'],
                invoice_date=m_dict['invoice_date'],
                invoice_type_id=m_dict['invoice_type_id'],
                invoice_state_id=m_dict['invoice_state_id'],
                invoice_maker_id=m_dict['maker_id'],
                inspector_id=m_dict['inspector_id'],
                keeper_id=m_dict['storeman_id'],
                salesman_id=m_dict.get('salesman_id'),
                allocation_type_id=m_dict['allocation_type_id'],
                callout_warehouse_id=m_dict.get('callOut_warehouse_id'),
                transferred_warehouse_id=m_dict.get('transferred_warehouse_id'),
                department_id=m_dict.get('department_id'),
                remark=m_dict.get('remarks', ''),
            )
        self.controlsession.add(invoice)
        try:
            if self.__is_commit:
                self.controlsession.commit()
        except Exception:
            self.controlsession.rollback()
            raise
        return invoice.id

    def __save_invoice_detail(self, invoice_id, m_list):
        """
        保存单据明细。
        :param m_list:
        [
        {
        invoice_id: int
        material_id: int		# 产品ID（即物料ID）
        callOut_warehouse_id:int   # 调出仓库ID
        transferred_warehouse_id: int	# 调入仓库ID
        allocation_number: int		# 调拨数量
        }
        ]
        :return:
        """
        op = MaterialWarehouseInfoOp()
        check_type(invoice_id, (int, long), 'invoice_id')
        link_dict = {}
        for element in m_list:
            try:
                op.warehouse_link_status(element['callOut_warehouse_id'])
                link_dict = add_warehouse_id_to_link(element['callOut_warehouse_id'], link_dict)
                op.warehouse_link_status(element['transferred_warehouse_id'])
                link_dict = add_warehouse_id_to_link(element['transferred_warehouse_id'], link_dict)
                detail = WarehouseAllocationDetail(
                        invoice_id=invoice_id,
                        material_id=element['material_id'],
                        callout_warehouse_id=element['callOut_warehouse_id'],
                        transferred_warehouse_id=element['transferred_warehouse_id'],
                        allocation_number=element['allocation_number']
                )
                self.controlsession.add(detail)
            except Exception:
                # 回滚链接数
                for key, value in link_dict.items():
                    for i in range(0, value):
                        op.delete_warehouse_link(key)
                raise

        try:
            if self.__is_commit:
                self.controlsession.commit()
        except Exception:
            self.controlsession.rollback()
            # 回滚链接数
            for key, value in link_dict.items():
                for i in range(0, value):
                    op.delete_warehouse_link(key)
            raise

        return link_dict

    def __delete_invoice_detail(self, invoice_id):
        def add_warehouse_id_to_link(warehouse_id, link):
            if warehouse_id in link:
                link[warehouse_id] += 1
            else:
                link[warehouse_id] = 1
            return link

        op = MaterialWarehouseInfoOp()
        link_dict = {}
        rs = self.controlsession.query(WarehouseAllocationDetail).filter_by(invoice_id=invoice_id).all()
        if rs is None:
            return link_dict
        else:
            for element in rs:
                try:
                    op.delete_warehouse_link(element.callout_warehouse_id)
                    link_dict = add_warehouse_id_to_link(element.callout_warehouse_id, link_dict)
                    op.delete_warehouse_link(element.transferred_warehouse_id)
                    link_dict = add_warehouse_id_to_link(element.transferred_warehouse_id, link_dict)
                except Exception:
                    for key, value in link_dict.items():
                        for i in range(0, value):
                            op.warehouse_link_status(key)
                    raise
                self.controlsession.delete(element)
            try:
                if self.__is_commit:
                    self.controlsession.commit()
            except Exception:
                self.controlsession.rollback()
                for key, value in link_dict.items():
                    for i in range(0, value):
                        op.warehouse_link_status(key)
                raise
        return link_dict

    def __delete_invoice(self, invoice_num):
        check_type(invoice_num, (str, unicode), 'invoice_number')
        m_op = MaterialWarehouseInfoOp()
        invoice = self.controlsession.query(WarehouseAllocationInvoice).filter_by(invoice_number=invoice_num).first()
        if invoice is None:
            return None
        else:
            m_id = invoice.id
            self.__is_commit = False
            m_link_dict = self.__delete_invoice_detail(m_id)
            self.controlsession.delete(invoice)
            if self.__is_commit:
                try:
                    self.controlsession.commit()
                except Exception:
                    self.controlsession.rollback()
                    for key, value in m_link_dict.items():
                        for i in range(0, value):
                            m_op.warehouse_link_status(key)
                    raise

        return m_id

    def add_operate_record(self, record_id, user_id, detail, remark=None):
        from data_mode.erp_supply.base_op.operate_op import Operate_Op
        op = Operate_Op()
        option = {
            'detail': detail,
            'operator_id': user_id,
            'operate_time': datetime.datetime.now(),
            'other_tblname': WarehouseAllocationInvoice.__tablename__,
            'other_id': record_id,
            'reason': remark,
            'is_commit': self.__is_commit
        }
        op.add_record(self.controlsession, **option)

    def get_opreate_record(self, page, page_num, m_dict):
        """
        获取记录信息
        :param page: 页数，从1开始
        :param page_num: 每页显示内容。
        :param m_dict:
        {
           'id': int    Invoice的记录ID
           或
           'invoice_number':str 单据号
        }
        :return: data, total
        """
        check_type(m_dict, dict, 'm_dict')
        from data_mode.erp_supply.base_op.operate_op import Operate_Op
        op = Operate_Op()
        # 优先根据ID获取信息
        start = (page - 1) * page_num if page > 1 else 0
        if m_dict.get('id'):
            m_id_id = m_dict.get('id')
        elif m_dict.get('invoice_number'):
            m_id = self.controlsession.query(WarehouseAllocationInvoice.id).filter_by(
                    invoice_number=m_dict.get('invoice_number')).first()
            m_id_id = m_id[0]
        else:
            raise ValueError("Error:m_dict key out value range. %s" % m_dict.keys())

        return op.get_record(start,
                             page_num,
                             WarehouseAllocationInvoice.__tablename__,
                             m_id_id)

    @staticmethod
    def deal_to_data(m_dict):
        from control_center.supply_chain.material_warehosue.control.material_warehouse_mix_op import GetWarehouseInfo
        from data_mode.user_center.control.mixOp import MixUserCenterOp

        if m_dict.get('callOut_warehouse_id'):
            op = GetWarehouseInfo()
            temp = op.get_warehouse_id_info(m_dict.get('callOut_warehouse_id'))
            m_dict['callOut_warehouse'] = temp['warehouse_name']

        if m_dict.get('transferred_warehouse_id'):
            op = GetWarehouseInfo()
            temp = op.get_warehouse_id_info(m_dict.get('transferred_warehouse_id'))
            m_dict['transferred_warehouse'] = temp['warehouse_name']

        if m_dict.get('maker_id'):
            op = MixUserCenterOp()
            temp = op.get_user_info(m_dict.get('maker_id'))
            m_dict['maker'] = temp['name']

        if m_dict.get('storeman_id'):
            op = MixUserCenterOp()
            temp = op.get_user_info(m_dict.get('storeman_id'))
            m_dict['storeman'] = temp['name']

        if m_dict.get('inspector_id'):
            op = MixUserCenterOp()
            temp = op.get_user_info(m_dict.get('inspector_id'))
            m_dict['inspector'] = temp['name']

        if m_dict.get('salesman_id'):
            op = MixUserCenterOp()
            temp = op.get_user_info(m_dict.get('salesman_id'))
            m_dict['salesman'] = temp['name']

        if m_dict.get('department_id'):
            op = MixUserCenterOp()
            m_dict['department_organization'] = op.get_department_name_byID(m_dict.get('department_id'))

        if m_dict.get('invoice_state_id'):
            print("invoice_state_id:", m_dict['invoice_state_id'], type(m_dict['invoice_state_id']))
            m_dict['invoice_state'] = WMA.INVOICE_STATE.get(m_dict['invoice_state_id'])

        if m_dict.get('invoice_type_id'):
            m_dict['invoice_type'] = WMA.INVOICE_TYPE.get(m_dict['invoice_type_id'])

        if m_dict.get('allocation_type_id'):
            m_dict['allocation_type'] = WMA.ALLOCATION_TYPE.get(m_dict['allocation_type_id'])

        return m_dict

    def check_invoice_number(self, invoice_number):
        return check_number_exists(self.controlsession,
                                   WarehouseAllocationInvoice.__tablename__,
                                   'invoice_number',
                                   invoice_number)

    def create_invoice(self):
        from redis_cache.public_cache.serial_number import create_number
        invoice = create_number('REMV{DATE}{SERIAL_NUMBER_4}',
                                self.controlsession,
                                WarehouseAllocationInvoice.__tablename__,
                                'invoice_number',
                                is_auto_create=True)
        return invoice

    def get_invoice_by_field(self, class_type, field_name, value, page=None, page_num=None, deal_func=None):
        """
        根据单据表的栏位获取单据表信息.
        :param class_type: 类 表的类
        :param field_name: str 栏位名
        :param value: 要与表栏位的类型相同, 或者是list。list中存放多个值，会进行值相‘与’操作。
        :param page:int
        :param page_num:int
        :param deal_func: 函数地址. 处理返回的data()
        :return:total, list
        """
        # check value
        class_name = class_type().__class__.__name__
        if field_name not in class_type.__dict__.keys():
            raise ValueError("field_name error.It isn't %s attribute. %s" % (class_name, field_name))

        # check_type(value, (eval('WarehouseAllocationInvoice.%s' % field_name), list), 'value')
        check_type(page, (int, NoneType), 'page')
        check_type(page_num, (int, NoneType), 'page_num')

        # get query condition
        if isinstance(value, list):
            condition = and_()
            for element in value:
                check_type(element, eval('%s.%s' % (class_name, field_name)), "value's element")
                condition.append(eval('%s.%s' % (class_name, field_name)) == element)
        else:
            condition = and_(eval('%s.%s' % (class_name, field_name)) == value)

        # execute sql
        if page is None or page_num is None:
            rs = self.controlsession.query(class_type).filter(condition).all()
        else:
            new_page = page - 1 if page > 0 else 0
            start = new_page * page_num
            rs = self.controlsession.query(class_type).filter(condition).limit(page_num).offset(start)

        total = self.controlsession.query(func.count(class_type.id)).filter(condition).scalar()
        if rs is None:
            return total, []

        if isinstance(deal_func, FunctionType):
            data = [deal_func(x.to_data()) for x in rs]
        else:
            data = [x.to_data() for x in rs]

        return total, data

    def get_invoice_information(self, invoice_number):
        """
        根据单据号, 获取单据信息与单据明细
        :param invoice_number: str 单据号
        :return: dict
        """
        _, rs = self.get_invoice_by_field(WarehouseAllocationInvoice,
                                          'invoice_number',
                                          invoice_number,
                                          deal_func=AllocationOp.deal_to_data)
        if rs is None:
            return {}
        invoice_data = rs[0]
        _, rs = self.get_invoice_by_field(WarehouseAllocationDetail,
                                          'invoice_id',
                                          invoice_data['id'],
                                          deal_func=AllocationOp.deal_to_data)
        invoice_data['rows'] = rs
        return invoice_data

    def save_invoice(self, para_dict, operate, operate_remark):
        check_type(para_dict, dict, 'para_dict')
        # 先存基础信息
        # assert not self.check_invoice_number(para_dict['invoice_number']), \
        #     "number exist. %s" % para_dict['invoice_number']
        invoice_id = self.__save_invoice_base(para_dict)
        # 后存明细
        try:
            self.__is_commit = False
            self.add_operate_record(invoice_id,
                                    session['user']['id'],
                                    operate,
                                    u'%s%s' % (session['user']['name'], operate_remark)
                                    )
            self.__is_commit = True
            self.__save_invoice_detail(invoice_id, para_dict['rows'])
        except Exception:
            self.__delete_invoice(para_dict['invoice_number'])
            raise
        return True

    def delete_invoice(self, invoice_number):
        self.__is_commit = False
        record_id = self.__delete_invoice(invoice_number)
        self.__is_commit = True
        self.add_operate_record(record_id,
                                session['user']['id'],
                                u'删除单据',
                                u'%s删除单据' % session['user']['name'])

    def modify_invoice(self, para_dict, operate, operate_remark):
        check_type(para_dict, dict, 'para_dict')
        # assert not self.check_invoice_number(para_dict['invoice_number']), \
        #     "number isn't existed. %s" % para_dict['invoice_number']

        _, rs = self.get_invoice_by_field(WarehouseAllocationInvoice,
                                          'invoice_number',
                                          para_dict['invoice_number'],
                                          deal_func=AllocationOp.deal_to_data)
        op = MaterialWarehouseInfoOp()
        invoice = rs[0]
        para_dict['id'] = invoice['id']
        para_dict['invoice_number'] = invoice['invoice_number']
        para_dict['invoice_date'] = invoice['invoice_date']
        para_dict['maker_id'] = invoice['maker_id']
        para_dict['invoice_type_id'] = invoice['invoice_type_id']
        print("para_dict", para_dict)
        self.__is_commit = False
        # 修改基础信息
        self.__save_invoice_base(para_dict)
        # 删除旧的信息
        add_link = self.__delete_invoice_detail(invoice['id'])
        # 添加新的信息
        del_link = self.__save_invoice_detail(invoice['id'], para_dict['rows'])
        self.add_operate_record(invoice['id'],
                                session['user']['id'],
                                operate,
                                u'%s%s。' % (session['user']['name'], operate_remark))
        try:
            self.controlsession.commit()
        except Exception:
            self.controlsession.rollback()
            for key, value in add_link.items():
                for i in range(0, value):
                    op.warehouse_link_status(key)
            for key, value in del_link.items():
                for i in range(0, value):
                    op.delete_warehouse_link(key)
            raise
        self.__is_commit = True
        return True

    def commit_invoice(self, invoice_number, is_add_record=False, operate_remark=''):
        """
        提交函数
        :param invoice_number:str 单据号。
        :param is_add_record: Boolean 是否添加操作记录
        :param operate_remark: str 操作记录明细
        :return:True
        """
        from public.exception.custom_exception import CodeError
        from config.service_config.returncode import ServiceCode
        from data_mode.erp_supply.base_op.warehouse_manage_op.inventory_op import pub_batch_allocation_warehouse
        try:
            invoice = self.controlsession.query(WarehouseAllocationInvoice).filter_by(
                    invoice_number=invoice_number).first()
            if invoice is None:
                raise CodeError(ServiceCode.params_error, u'单据不存在')

            if not invoice.invoice_state_id != WMA.TEMPORARY_STORAGE:
                raise CodeError(ServiceCode.exception_op, u'单据状态为已完成的单据不能重复提交')

            invoice.invoice_state_id = WMA.COMPLETED
            try:
                # 添加记录
                if is_add_record:
                    self.__is_commit = False
                    if operate_remark:
                        operate_remark = u"%s%s" % (session['user']['name'], operate_remark)
                    self.add_operate_record(invoice.id,
                                            session['user']['id'],
                                            u'提交单据',
                                            operate_remark)
                    self.__is_commit = True
                # 修改单据状态
                self.controlsession.add(invoice)
                self.controlsession.commit()
            except Exception:
                self.controlsession.rollback()
                raise
            # 根据单据号获取原单据信息
            _, rs = self.get_invoice_by_field(WarehouseAllocationDetail,
                                              'invoice_id',
                                              invoice.id,
                                              deal_func=AllocationOp.deal_to_data)
            # 批量调度
            try:
                pub_batch_allocation_warehouse(invoice_number, rs)
            except Exception:
                invoice.invoice_state_id = WMA.COMPLETED
                self.controlsession.add(invoice)
                self.controlsession.commit()
                raise
        except Exception:
            from public.logger.syslog import SystemLog
            SystemLog.pub_warninglog("invoice_number:%s commit fail" % invoice_number)
            raise
        return True

    def search(self, m_dict, page=None, page_num=None):
        """
        搜索单据信息, 单据列表
        :param m_dict:
        {
        'invoice_number':str or None     # 单据号,
        'start_time':str or None       # 单据日期-起始,
        'stop_time':str or None        # 单据日期-关闭,
        'invoice_state_id':str or None # 单据状态
        'allocation_type_id':str or None # 调拨类型
        }
        :param page: int 页数
        :param page_num: int 每页显示内容
        :return: total, data
        """
        from public.exception.custom_exception import CodeError
        def check_date(m_str):
            import re
            if re.match(r'^\d{4}-\d{2}-\d{2}$', m_str):
                return True
            else:
                return False
        check_type(m_dict, dict, 'm_dict')

        condition = and_()

        # 单据号
        if m_dict.get('invoice_number'):
            condition.append(WarehouseAllocationInvoice.invoice_number == m_dict.get('invoice_number'))

        # 单据日期
        if m_dict.get('start_time') and m_dict.get('stop_time'):
            if not check_date(m_dict.get('start_time')) or not check_date(m_dict.get('stop_time')):
                raise CodeError(101, u'日期格式错误')
            # 由于datetime要包含当天，需要时间上
            new_end_data = m_dict.get('stop_time') + " 23:59:59"

            condition.append(WarehouseAllocationInvoice.invoice_date >= m_dict.get('start_time'))
            condition.append(WarehouseAllocationInvoice.invoice_date <= new_end_data)
        # 单据状态
        if m_dict.get('invoice_state_id'):
            condition.append(WarehouseAllocationInvoice.invoice_state_id == m_dict.get('invoice_state_id'))

        # 调拨类型
        if m_dict.get('allocation_type_id'):
            condition.append(WarehouseAllocationInvoice.allocation_type_id == m_dict.get('allocation_type_id'))

        if page is None or page_num is None:
            # 查询全部
            rs = self.controlsession.query(WarehouseAllocationInvoice).filter(condition).all()
        else:
            check_type(page, int, 'page')
            check_type(page_num, int, 'page')
            start = (page - 1) * page_num if page > 0 else page
            rs = self.controlsession.query(WarehouseAllocationInvoice).filter(condition).limit(page_num).offset(start)

        total = self.controlsession.query(func.count(WarehouseAllocationInvoice.id)).filter(condition).scalar()
        if rs is None:
            return 0, []
        else:
            data = [self.deal_to_data(x.to_data()) for x in rs]
            return total, data

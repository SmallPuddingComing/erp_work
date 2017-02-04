#!/usr/bin/python
# -*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : customer_mix_op.py
#    作者   : DengLiming
#  电子邮箱 : lmdeng@jmgo.com
#    日期   : 2017/1/5 10:57
#
#     描述  :客户公共接口
#
from sqlalchemy import or_, func, and_, not_
# from config.service_config.returncode import ServiceCode
from public.logger.syslog import SystemLog
from data_mode.erp_supply.control_base.controlBase import ControlEngine
from data_mode.erp_supply.mode.material_repertory_model.customer_info import CustomerInfo
from data_mode.erp_supply.mode.material_repertory_model.link_record_info import LinkRecordInfo
import traceback


class QueryCustomerInfo(ControlEngine):
    def __init__(self):
        ControlEngine.__init__(self)

    # 获取客户信息，支持搜索，分页等功能
    def get_customer_relevant_info(self, **kw):
        """
        :param kw: page_number:当前页码，page_size:分页大小，支持按客户名（customer_name）/联系人（contacts）搜索
        :return:
        """
        try:
            parameter_dict = kw
            page_number = parameter_dict.get('page_number', 1)
            page_size = parameter_dict.get('page_size', 10)
            customer_name = parameter_dict.get('customer_name', '')
            contacts = parameter_dict.get('contacts', '')
            start = (page_number - 1) * page_size
            condition = ''
            if customer_name:
                condition = "CustomerInfo.customer_name == '%s'" % customer_name
            if contacts:
                condition = "CustomerInfo.contact_person == '%s'" % contacts
            condition = "and_("+condition+")"
            res = self.controlsession.query(CustomerInfo).filter(eval(condition)).limit(page_size).offset(start).all()
            total = self.controlsession.query(func.count(CustomerInfo.id)).order_by(CustomerInfo.id).filter(eval(condition)).scalar()
            if res:
                data = [item.to_data() for item in res]
            else:
                data = []
            return total, data
        except Exception:
            print traceback.format_exc()
            SystemLog.pub_warninglog(traceback.format_exc())
            raise Exception(u'查询失败,服务器错误')

    # 通过客户ID获取相应数据
    def get_customer_id_info(self, customer_id):
        """
        # 通过客户ID获取相应数据
        :param customer_id: 用户ID必填
        :return:
        """
        try:
            if customer_id:
                res = self.controlsession.query(CustomerInfo).filter(CustomerInfo.id == customer_id).first()
                if res:
                    res = res.to_json()
                else:
                    res = {}
                return res
            else:
                raise Exception(u'客户ID不能失败')
        except Exception:
            print traceback.format_exc()
            SystemLog.pub_warninglog(traceback.format_exc())
            raise Exception(u'通过客户ID查询失败')

    # 获取全部客户信息
    def get_customer_info_all(self):
        """
        获取客户全部信息
        :return:
        """
        try:
            res = self.controlsession.query(CustomerInfo).all()
            total = self.controlsession.query(func.count(CustomerInfo.id)).scalar()
            if res:
                data = [item.to_json() for item in res]
            else:
                data = []
            return total, data
        except Exception:
            print traceback.format_exc()
            SystemLog.pub_warninglog(traceback.format_exc())
            raise Exception(u'获取全部数据失败')

    # 操作get_customer_relevant_info方法后，保存时调用此方法
    def add_customer_links(self, customer_id_list=list(), tablename=None):
        """
        添加客户连接数
        :param tablename: 表名
        :param customer_id_list: 关联ID列表
        :return: True修改成功，False
        """
        try:
            if tablename is None:
                raise KeyError(u'表名不能为空')
            if isinstance(customer_id_list, list):
                if len(customer_id_list) > 0:
                    for key in customer_id_list:
                        res = self.controlsession.query(LinkRecordInfo).filter(LinkRecordInfo.associated_id == key,
                                                                               LinkRecordInfo.associated_tblname == tablename).first()
                        if res:
                            res.operatecount = res.operatecount + 1
                            self.controlsession.add(res)
                        else:
                            add_link = LinkRecordInfo(associated_tblname=tablename, associated_id=key, operatecount=1)
                            self.controlsession.add(add_link)
                    self.controlsession.commit()
                    return True
                else:
                    # 参数列表为空
                    return False
            else:
                # 参数列表错误
                return False

        except Exception:
            print traceback.format_exc()
            self.controlsession.rollback()
            SystemLog.pub_warninglog(traceback.format_exc())
            raise Exception(u'更新用户连接数失败')

    # 删除连接数
    def del_customer_links(self, customer_id_list=list(), tablename=None):
        """
        :param tablename: 表名
        :param customer_id_list: 客户ID列表
        :return:
        """
        try:
            if tablename is None:
                raise KeyError(u'表名不能为空')
            if len(customer_id_list) > 0:
                for key in customer_id_list:
                    res = self.controlsession.query(LinkRecordInfo).filter(LinkRecordInfo.associated_id == key,
                                                                           LinkRecordInfo.associated_tblname == tablename).first()
                    if res:
                        if res.operatecount > 0:
                            res.operatecount = res.operatecount - 1
                            self.controlsession.add(res)
                            self.controlsession.commit()
                            return True
                        else:
                            raise Exception(u'当前连接数为0,删除失败')
                    else:
                        raise Exception(u'删减连接数失败')
            else:
                raise Exception(u'删除用户ID不能为空')
        except Exception:
            self.controlsession.rollback()
            raise Exception(u'删除连接数失败')

if __name__ == '__main__':
    op = QueryCustomerInfo()
    # print op.add_customer_links(customer_id_list=[1,2], tablename='test')
    # print op.get_customer_info_all()
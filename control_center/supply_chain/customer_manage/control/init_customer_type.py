#!/usr/bin/python
# -*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : init_customer_type.py
#    作者   : DengLiming
#  电子邮箱 : lmdeng@jmgo.com
#    日期   : 2017/1/5 14:36
#
#     描述  :
#
import os
from data_mode.erp_supply.mode.material_repertory_model.customer_type_info import CustomerTypeInfo
from config.warehouse_management_config.customer import BaseDataCustomerConfig
from data_mode.erp_supply.control_base.controlBase import ControlEngine


class InitCustomerType(ControlEngine):

    def init_customer_type(self):
        b = BaseDataCustomerConfig()
        xml_data = b.paytype_get_xml()
        print 'XML数据',b.paytype_get_xml()
        res = self.controlsession.query(CustomerTypeInfo).all()
        if res:
            pass
        else:
            try:
                for item in xml_data['data']:
                    c_obj = CustomerTypeInfo(id=item['id'], content=item['name'])
                    self.controlsession.add(c_obj)
            except Exception, e:
                print e
                self.controlsession.rollback()
            self.controlsession.commit()
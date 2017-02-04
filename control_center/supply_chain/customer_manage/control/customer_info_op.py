#!/usr/bin/python
# -*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : customer_info_op.py
#    作者   : DengLiming
#  电子邮箱 : lmdeng@jmgo.com
#    日期   : 2017/1/5 10:54
#
#     描述  :
#
from sqlalchemy import or_, func, and_, not_, cast, LargeBinary
import traceback
from config.service_config.returncode import ServiceCode
from public.logger.syslog import SystemLog
from data_mode.erp_supply.control_base.controlBase import ControlEngine
from data_mode.erp_supply.mode.material_repertory_model.customer_info import CustomerInfo
from data_mode.erp_supply.mode.material_repertory_model.customer_type_info import CustomerTypeInfo
from data_mode.erp_supply.mode.material_repertory_model.link_record_info import LinkRecordInfo
from control_center.supply_chain.customer_manage.control.customer_mix_op import QueryCustomerInfo


class CustomerInfoOp(ControlEngine):
    # 检测用户是否有业务关联
    def is_display(self, customer_id):
        try:
            if customer_id:
                condition = "LinkRecordInfo.associated_id == %d" % customer_id
                l = 0
                condition = condition + ", LinkRecordInfo.operatecount > %d" % l
                condition = "and_("+condition+")"
                res = self.controlsession.query(LinkRecordInfo).filter(LinkRecordInfo.associated_id == customer_id).first()
                if res:
                    return True
                else:
                    return False
            else:
                return False
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            print traceback.format_exc()
            return False

    # 获取客户列表
    def customer_info_list(self, page_number=None, customer_name=None, page_size=None, contacts=None):
        try:
            query_op = QueryCustomerInfo()
            res = query_op.get_customer_relevant_info(page_number=page_number,
                                                      customer_name=customer_name,
                                                      page_size=page_size,
                                                      contacts=contacts)
            if res[1]:
                for item in res[1]:
                    # print item['id'],'ffff', self.is_display(item['id'])
                    if self.is_display(item['id']):
                        item['is_display'] = 1
                    else:
                        item['is_display'] = 0
                data = {'msg': u'查询成功', 'code': ServiceCode.success, 'data': res[1], 'total': res[0]}
            else:
                data = {'msg': u'查询成功', 'code': ServiceCode.success, 'data': [], 'total': 0}
            # print '数据列表', data
            return data
        except Exception, e:
            SystemLog.pub_warninglog(traceback.format_exc())
            raise Exception(u'查询失败')

    # 获取客户类型
    def get_customer_type(self, content=None):
        try:
            condition = ''
            if content:
                condition = "CustomerTypeInfo.content == '%s'" % content
            condition = "and_("+condition+")"
            res = self.controlsession.query(CustomerTypeInfo).filter(eval(condition)).all()
            if res:
                res = [item.to_json() for item in res]
                data = {'msg': u'获取数据成功', 'code': ServiceCode.success, 'data': res}
                return data
            else:
                data = {'msg': u'暂无客户类型相关数据', 'code': ServiceCode.data_empty, 'data': ''}
                return data
        except Exception, e:
            SystemLog.pub_warninglog(traceback.format_exc())
            print traceback.format_exc()
            data = {'msg': u'获取数据失败', 'code': ServiceCode.notfound, 'data': ''}
            return data

    # 检测客户名/客户编码唯一性
    def check_customer_only(self, customer_name=None, customer_code=None, customer_id=None):
        try:
            condition = ''
            if customer_name:
                condition = "CustomerInfo.customer_name == '%s'" % customer_name
            if customer_code:
                condition = "CustomerInfo.customer_code == '%s'" % customer_code
            if customer_id:
                condition = condition + ", not_(CustomerInfo.id == %d)" % customer_id

            condition = "and_("+condition+")"
            res = self.controlsession.query(CustomerInfo).filter(eval(condition)).first()
            if res:
                return ServiceCode.success
            else:
                return ServiceCode.notfound
        except Exception, e:
            SystemLog.pub_warninglog(traceback.format_exc())
            print traceback.format_exc()

    # 检查客户类型唯一
    def check_customer_type_name(self, customer_type_name):
        try:
            res = self.controlsession.query(CustomerTypeInfo).filter(CustomerTypeInfo.content == customer_type_name).first()
            if res:
                return ServiceCode.success
            else:
                return ServiceCode.notfound
        except Exception, e:
            SystemLog.pub_warninglog(traceback.format_exc())
            print traceback.format_exc()

    # 保存客户信息
    def save_customer_info(self, parameter_dict):
        try:
            insrt_customer = CustomerInfo(customer_code=parameter_dict.get('customer_code', ''),
                                          customer_name=parameter_dict.get('customer_name', ''),
                                          customer_province=parameter_dict.get('province', ''),
                                          customer_city=parameter_dict.get('city', ''),
                                          customer_area=parameter_dict.get('county', ''),
                                          customer_addr=parameter_dict.get('address', ''),
                                          customer_type_id=parameter_dict.get('customer_type_id'),
                                          company_tel=parameter_dict.get('company_tel', ''),
                                          company_fax=parameter_dict.get('company_fax', ''),
                                          company_website=parameter_dict.get('network_address', ''),
                                          contact_person=parameter_dict.get('contacts', ''),
                                          contact_tel=parameter_dict.get('telephone', ''),
                                          remark=parameter_dict.get('remarks', ''))
            self.controlsession.add(insrt_customer)
            self.controlsession.commit()
            return {'code': ServiceCode.success, 'msg': u'添加成功'}
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            print traceback.format_exc()
            self.controlsession.rollback()
            return {'code': ServiceCode.service_exception, 'msg': u'添加失败'}

    # 添加客户类型
    def save_customer_type(self, content):
        result = {}
        try:
            customer_type = CustomerTypeInfo(content=content)
            self.controlsession.add(customer_type)
            self.controlsession.commit()
            customer_type_obj = self.get_customer_type(content=content)
            if customer_type_obj['code'] == ServiceCode.success:
                result = {'code': ServiceCode.success, 'data': customer_type_obj['data'], 'msg': u'查询成功'}
            else:
                result = {'code': customer_type_obj['code'], 'data': customer_type_obj['data'], 'msg': u'查询失败'}
            return result
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            print traceback.format_exc()
            self.controlsession.rollback()
            result = {'code': ServiceCode.notfound, 'data': '', 'msg': u'添加失败'}
            return result

    # 通过用户ID获取相应用户
    def get_customer_id(self, customer_id=None):
        try:
            condition = ''
            if customer_id:
                condition = "CustomerInfo.id == %d" % customer_id
            condition = "and_("+condition+")"
            customer_info_obj = self.controlsession.query(CustomerInfo).filter(eval(condition)).first()
            if customer_info_obj:
                infos = customer_info_obj.to_json()
                if self.is_display(infos['id']):
                    infos['is_display'] = 1
                else:
                    infos['is_display'] = 0
                result = {'code': ServiceCode.success, 'msg': u'查询成功', 'data': infos}
            else:
                result = {'code': ServiceCode.params_error, 'msg': u'暂无客户相关数据', 'data': []}
            return result
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            print traceback.format_exc()
            result = {'code': ServiceCode.check_error, 'msg': u'服务器错误', 'data': []}
            return result

    # 保存修改信息
    def save_update_info(self, parameter_dict):
        try:
            res = self.controlsession.query(CustomerInfo).filter(CustomerInfo.id == parameter_dict['customer_id']).first()
            if res:
                res.customer_code = parameter_dict.get('customer_code', '')
                res.customer_name = parameter_dict.get('customer_name', '')
                res.customer_province = parameter_dict.get('province', '')
                res.customer_city = parameter_dict.get('city', '')
                res.customer_area = parameter_dict.get('county', '')
                res.customer_addr = parameter_dict.get('address', '')
                res.customer_type_id = parameter_dict.get('customer_type_id')
                res.company_tel = parameter_dict.get('company_tel', '')
                res.company_fax = parameter_dict.get('company_fax', '')
                res.company_website = parameter_dict.get('network_address', '')
                res.contact_person = parameter_dict.get('contacts', '')
                res.contact_tel = parameter_dict.get('telephone', '')
                res.remark = parameter_dict.get('remarks', '')
                self.controlsession.add(res)
                self.controlsession.commit()
                result = {'code': ServiceCode.success, 'msg': u'修改成功'}
                return result
            else:
                result = {'code': ServiceCode.params_error, 'msg': u'暂无修改客户相关数据'}
                return result
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            print traceback.format_exc()
            result = {'code': ServiceCode.check_error, 'msg': u'服务器错误', 'data': []}
            return result

    # 删除客户信息
    def del_customer_info(self, customer_id):
        try:
            is_display = self.is_display(customer_id)
            if is_display:
                result = {'code': ServiceCode.check_error, 'msg': u'已经有业务关联，删除失败'}
                return result
            customer_id_del = self.controlsession.query(CustomerInfo).filter(CustomerInfo.id == customer_id).first()
            if customer_id_del:
                self.controlsession.delete(customer_id_del)
                self.controlsession.commit()
                result = {'code': ServiceCode.success, 'msg': u'删除成功'}
                return result
            else:
                result = {'code': ServiceCode.check_error, 'msg': u'删除失败'}
                return result
        except Exception:
            SystemLog.pub_warninglog(traceback.format_exc())
            print traceback.format_exc()
            result = {'code': ServiceCode.check_error, 'msg': u'服务器错误'}
            return result

    def get_customer_id_by_name(self, customer_name=None):
        if customer_name is None:
            customer_id = self.controlsession.query(CustomerInfo.id).order_by(CustomerInfo.id).all()
        else:
            if not isinstance(customer_name, str):
                raise TypeError("unsupported operand types(s) for customer_name: %s " % type(customer_name))
            customer_id = self.controlsession.query(CustomerInfo.id).filter(
                CustomerInfo.customer_name.cast(LargeBinary)==customer_name).order_by(CustomerInfo.id).all()
        customer_id_list = []
        for data in customer_id:
            customer_id_list.append(data[0])

        return customer_id_list


if __name__ == "__main__":
    op = CustomerInfoOp()
    id_list = op.get_customer_id("sss")
    print("success")

#/usr/bin/python
#-*- coding:utf-8 -*-

'''
Created on : 2016/08/25
@author : YuanRong
'''

import json
import traceback
from config.service_config.returncode import ServiceCode
from public.exception.custom_exception import CodeError
from sqlalchemy import and_, func, cast, LargeBinary
from data_mode.erp_supply.mode.supply_manage_mode.supplier_achieve import SupplierAchieve
from data_mode.erp_supply.mode.supply_manage_mode.supplier_info import SupplierBaseInfo
from data_mode.erp_supply.mode.supply_manage_mode.supplier_contact import SupplierContact
from data_mode.user_center.control.mixOp import MixUserCenterOp
from data_mode.erp_supply.control_base.controlBase import ControlEngine
from config.share.share_define import *
from config.share.share_define import SupplyAttr
from config.share.share_define import get_key_by_value
from data_mode.erp_supply.mode.supply_manage_mode.supplier_attribute import SupplierAttribute

class SupplierBaseInfoOp(ControlEngine):
    '''operation supplier_info table'''

    def __init__(self):
        '''控制引擎初始化'''
        ControlEngine.__init__(self)

    @property
    def StateShow(self):
        return "01" #显示

    @property
    def StateUnShow(self):
        return "02" #不显示

    def get_currency(self, id):
        '''
        @function : 获得货币类型名称
        :param id:
        :return:
        '''
        # type = SupplyAttr.ATTR_TYPE_CURRENCY
        rs = self.controlsession.query(SupplierAttribute).filter_by(id=id).first()
        if rs:
            rs = rs.to_json()
            return rs
        else:
            return {}

    def get_all_currency_info(self):
        '''
        @function : 获得所有结算币种类型名称
        :return:
        '''
        # rs_list = self.controlsession.query(SupplierCurrency).all()
        rs_list = SupplyAttr.SUPPLIER_CURRENCY_TYPE
        # print rs_list.pop('type')
        if rs_list:
            return rs_list
        else:
            return {}
        # dataDict = {}
        # if rs_list:
        #     for rs in rs_list:
        #         rs = rs.to_json()
        #         id = rs['id']
        #         name = rs['name']
        #         dataDict[id] = name
        #     return dataDict
        # else:
        #     return {}

    def get_selt_modes(self, id):
        '''
        @function : 根据id获得结算方式类型名称
        :param id:
        :return:
        '''
        # models_type = SupplyAttr.ATTR_TYPE_SELT_MODELS
        rs = self.controlsession.query(SupplierAttribute).filter_by(id=id).first()
        if rs:
            rs = rs.to_json()
            return rs
        else:
            return {}

    def get_all_selt_modes_info(self):
        '''
        @function : 获得所有结算方式类型名称
        :return:
        '''
        rs_list = SupplyAttr.SELT_MODELS_TYPE
        # rs_list.pop('type')
        if rs_list:
            return rs_list
        else:
            return {}
        # rs_list = self.controlsession.query(SelttementModels).all()
        # dataDict = {}
        # if rs_list:
        #     for rs in rs_list:
        #         rs = rs.to_json()
        #         id = rs['id']
        #         name = rs['name']
        #         dataDict[id] = name
        #     return dataDict
        # else:
        #     return {}

    def get_selt_date(self, id):
        '''
        @function : 根据id获得结算日期类型名称
        :param id:
        :return:
        '''
        # dater_type = SupplyAttr.ATTR_TYPE_SELT_DATER
        rs = self.controlsession.query(SupplierAttribute).filter_by(id=id).first()
        if rs:
            rs = rs.to_json()
            return rs
        else:
            return {}

    def get_all_selt_date_type(self):
        '''
        @function : 获得所有结算日期类型名称
        :return:
        '''
        rs_list = SupplyAttr.SELT_DATE_TYPE
        # rs_list.pop('type')
        if rs_list:
            return rs_list
        else:
            return {}
        # rs_list = self.controlsession.query(SelttementDater).all()
        # dataDict = {}
        # if rs_list:
        #     for rs in rs_list:
        #         rs = rs.to_json()
        #         id = rs['id']
        #         name = rs['name']
        #         dataDict[id] = name
        #     return dataDict
        # else:
        #     return {}

    def get_achieve_type_by_id(self, type_id):
        '''
        @function :　根据type_id获得所资料类型名称
        :param type_id:
        :return: type_name
        '''
        # achieve_type = SupplyAttr.ATTR_TYPE_ARCHIVE
        rs = self.controlsession.query(SupplierAttribute).filter_by(id=type_id).first()
        if rs:
            return rs.to_name_json()
        else:
            return {}

    def get_supplier_achieve_info(self, sup_id):
        '''
        @function : 获得供应商资料存档信息
        :param sup_id: 供应商id
        :return: dict
        '''
        achieve_list = self.controlsession.query(SupplierAchieve).filter_by(supplier_id=sup_id).all()
        allInfoDict = {} #资料全部信息
        allInfoDict['supplier_id'] = sup_id
        allInfoDict['other'] = []
        allInfoDict['normal'] = []
        if achieve_list:
            for achieve_info in achieve_list:
                achieve_info_dict = achieve_info.to_json()
                type_id = achieve_info_dict['file_type_id']
                if SupplyAttr.SUPPLIER_ARCHIEVE_TYPE[type_id] == SupplyAttr.OTHER_ARCHIEVE:
                    allInfoDict['other'].append(achieve_info.to_json())
                else:
                    allInfoDict['normal'].append(achieve_info.to_json())
            return allInfoDict
        else:
            return allInfoDict

    def get_supplier_base_info(self, sup_id):
        '''
        @function : 获得供应商基础信息
        :return:
        '''
        rs = self.controlsession.query(SupplierBaseInfo).get(sup_id)
        if rs:
            rs = rs.to_baseinfo_json()
            #获得币种类型名字
            currency_id = rs.get('currency_id')
            currency = self.get_currency(currency_id)
            rs['currency_name'] = currency.get('name')

            #根据相应的id获得分管部门名字和对接
            principal_id = rs.get('principal_id')
            mc = MixUserCenterOp()
            principal_info = mc.get_user_info(principal_id)
            if not principal_info:
                rs['principal_name'] = ""
                return rs
            principal_name = principal_info.get('username', "")
            rs['principal_name'] = principal_name
            return rs
        else:
            return {}

    def get_supplier_base_info_by_code(self, s_code):
        '''
                @function : 获得供应商基础信息
                :return:
                '''
        rs = self.controlsession.query(SupplierBaseInfo).filter_by(supplier_code=s_code).first()
        if rs:
            rs = rs.to_baseinfo_json()
            # 获得币种类型名字
            currency_id = rs.get('currency_id')
            currency = self.get_currency(currency_id)
            rs['currency_name'] = currency.get('name')

            # 根据相应的id获得分管部门名字和对接
            principal_id = rs.get('principal_id')
            mc = MixUserCenterOp()
            principal_info = mc.get_user_info(principal_id)
            if not principal_info:
                rs['principal_name'] = ""
                return rs
            principal_name = principal_info.get('username', "")
            rs['principal_name'] = principal_name
            return rs
        else:
            return None

    def get_supplier_other_info(self, sup_id):
        '''
        @function : 获得供应商其他信息
        :return: dict
        '''
        return_data = {}
        link_list = []
        rs = self.controlsession.query(SupplierBaseInfo).filter_by(id=sup_id).first()
        link_info_list = self.controlsession.query(SupplierContact).filter_by(supplier_id=sup_id).all()
        if rs:
            rs = rs.to_otherinfo_json()
            return_data['other_info'] = rs
        if link_info_list:
            for link_info in link_info_list: #多个数据返回的类型，是不是列表还是元祖
                link_info = link_info.to_json()
                link_list.append(link_info)
            return_data['link_info'] = link_list
        return return_data


    def save_supplier_baseinfo(self, sup_code, sup_name, sup_full_name, currency_id,
                               principal_id, state_id, state_show):
        '''
        @function : 保存供应商基本信息
        :param sup_id: 供应商id
        :param sup_code: 供应商代码
        :param sup_name: 供应商名称
        :param sup_full_name: 供应商全称
        :param currency_id: 币种
        :param principal_id: 采购对接人
        :param state: 状态
        :return: bool
        '''
        try:
            rs = self.controlsession.query(SupplierBaseInfo).filter_by(supplier_code=sup_code).first()
            if rs:
                rs.supplier_name = sup_name
                rs.supplier_full_name = sup_full_name
                rs.currency_id = currency_id
                rs.principal_id = int(principal_id)
                rs.state_id = state_id
                self.controlsession.add(rs)
                self.controlsession.commit()
                supplier_id = rs.id
            else:
                supplier = SupplierBaseInfo(supplier_code=sup_code, supplier_name=sup_name,
                                            supplier_full_name=sup_full_name, currency_id=currency_id,
                                            principal_id=principal_id, state_id=state_id, show_state=state_show)
                self.controlsession.add(supplier)
                self.controlsession.commit()
                supplier_id = supplier.id
                #返回数据库中存进去的supplier_id
                # rs = self.controlsession.query(SupplierBaseInfo).filter_by(supplier_code=sup_code).first()
                # if rs:
                #     supplier_id = rs.id
                # else:
                #     raise
            # self.controlsession.commit()
            return json.dumps({"code": ServiceCode.success, 'supplier_id': supplier_id})
        except Exception as e:
            self.controlsession.rollback()
            print(traceback.format_exc())
            return json.dumps({"code": ServiceCode.service_exception})

    def save_supplier_otherinfo(self, sup_id, selt_modes_id, selt_dater_id, vat_rates,
                                supplier_country, supplier_province, supplier_city,
                                supplier_addr, bank_name, acct_no, tax_regist_no,
                                business_lincese, organize_code):
        '''
        @function : 保存供应商其他信息
        :param sup_id: 供应商id
        :param selt_modes_id: 结算方式id
        :param selt_dater_id: 结算日期id
        :param vat_rates: 增值税率
        :param supplier_country: 所属国家
        :param supplier_province: 所属省份
        :param supplier_city: 所属城市
        :param bank_name: 开户银行
        :param acct_no: 银行账号
        :param tax_regist_no: 税务登记号
        :param business_lincese: 营业执照注册号
        :param organize_code: 组织机构代码
        :return: bool 返回值
        '''
        try:
            rs = self.controlsession.query(SupplierBaseInfo).filter_by(id=sup_id).first()
            if rs:
                rs.selt_modes_id = selt_modes_id
                rs.selt_dater_id = selt_dater_id
                rs.vat_rates = vat_rates
                rs.supplier_country = supplier_country
                rs.supplier_province = supplier_province
                rs.supplier_city = supplier_city
                rs.supplier_addr = supplier_addr
                rs.bank_name = bank_name
                rs.acct_no = acct_no
                rs.tax_regist_no = tax_regist_no
                rs.business_lincese = business_lincese
                rs.organize_code = organize_code
                self.controlsession.commit()
                return json.dumps({"code": ServiceCode.success})

            return json.dumps({"code": ServiceCode.service_exception})  #添加错误码 ： 供应商不存在，请先添加供应商
        except Exception, e:
            print traceback.format_exc()
            return json.dumps({"code": ServiceCode.service_exception})

    def save_supplier_contact_info(self, sup_id, contactAllList):
        '''
        @function : 保存供应商其他信息中联系人信息，本接口不支持编辑联系人功能
        :param sup_id:供应商id
        :param , contactAllDict: 联系人id信息
        :param , contactAllDict: 联系人id删除列表
        :return:
        '''

        try:
            rs = self.controlsession.query(SupplierBaseInfo).filter_by(id=sup_id).first()
            supplier_id = rs.id
            if rs:
                contact_list_info = self.controlsession.query(SupplierContact).filter_by(supplier_id=supplier_id).all()
                if contact_list_info: #编辑供应商联系人信息
                    for contact in contactAllList: #更新供应商联系人信息（更新和插入功能）
                        info = contact
                        if info['id']: #能获得联系人id，证明数据库有此条记录，则进行更新
                            contact_info = self.controlsession.query(SupplierContact).filter_by(id=info['id']).first()
                            contact_info.supplier_contact_name = info['name']
                            contact_info.supplier_contact_position = info['position']
                            contact_info.supplier_contact_mobile = info['mobile']
                            contact_info.supplier_contact_email = info['email']
                            contact_info.supplier_contact_telphone = info['telphone']
                            contact_info.supplier_contact_tax = info['tax']
                            self.controlsession.add(contact_info)
                        else: #否则就是编辑添加联系人
                            contact = SupplierContact(supplier_id=supplier_id, supplier_contact_name=info['name'],
                                                      supplier_contact_position=info['position'],
                                                      supplier_contact_mobile=info['mobile'],
                                                      supplier_contact_email=info['email'],
                                                      supplier_contact_telphone=info['telphone'],
                                                      supplier_contact_tax=info['tax'])
                            self.controlsession.add(contact)
                else: #新增供应商其他信息中添加联系人
                    for contact in contactAllList:
                        info = contact
                        contact_obj = SupplierContact(supplier_id=supplier_id, supplier_contact_name=info['name'],
                                                      supplier_contact_position=info['position'], supplier_contact_mobile=info['mobile'],
                                                      supplier_contact_email=info['email'], supplier_contact_telphone=info['telphone'],
                                                      supplier_contact_tax=info['tax'])
                        self.controlsession.add(contact_obj)
                self.controlsession.commit()
                return json.dumps({"code": ServiceCode.success})

        except Exception,e:
            self.controlsession.rollback()
            print traceback.format_exc()
            return json.dumps({"code": ServiceCode.service_exception})

    def del_supplier_contact_by_id(self, id):
        '''
        @function :　删除供应商联系人id
        :param id:
        :return:
        '''
        # 删除供应商联系人信息（删除id）
        need_del_info = self.controlsession.query(SupplierContact).filter_by(id=id).one()
        if need_del_info:
            self.controlsession.delete(need_del_info)
        else:
            self.controlsession.close()
            return json.dumps({"code": ServiceCode.service_exception})  # 添加错误码 ：联系人id不存在，删除失败
        return json.dumps({"code": ServiceCode.success})

    def save_achieve_info_new(self, supplier_id, id, file_url, file_name, file_path, file_type_id, file_state=None):
        try:
            rs = self.controlsession.query(SupplierBaseInfo).filter_by(id=supplier_id).first()
            achieve_info = self.controlsession.query(SupplierAchieve).filter_by(id=id).first()
            if id:
                achieve_info = self.controlsession.query(SupplierAchieve).filter_by(id=id).first()
                if achieve_info:
                    achieve_info['file_url'] = file_url
                    achieve_info['file_name'] = file_name
                    achieve_info['file_path'] = file_path
                    achieve_info['file_type_id'] = file_type_id
                    achieve_info['file_state'] = file_state
                    self.controlsession.add(achieve_info)
            else:
                achieve = SupplierAchieve(supplier_id=supplier_id, file_url=file_url,
                                        file_name=file_name, file_path=file_path,
                                        file_type_id=file_type_id, file_state=file_state)
                self.controlsession.add(achieve)
            self.controlsession.commit()
            return json.dumps({"code": ServiceCode.success})
        except Exception, e:
            self.controlsession.rollback()
            print traceback.format_exc()
            return json.dumps({"code": ServiceCode.service_exception})

    def save_achieve_info(self, supplier_id, file_info_dict):
        '''
        @function : 添加供应商存档资料
        :param sup_id:
        :param file_info_list:
        :return:
        '''
        try:
            rs = self.controlsession.query(SupplierBaseInfo).filter_by(id=supplier_id).first()
            if rs:
                achieve_info_list = self.controlsession.query(SupplierAchieve).filter_by(supplier_id=supplier_id).all()
                normal_info_list = file_info_dict.get('normal', None)
                other_info_dict = file_info_dict.get('other', None)
                if achieve_info_list:
                    #更新存档资料信息
                    for info in normal_info_list:
                        achieve_info = self.controlsession.query(SupplierAchieve).filter_by(
                            id=info['id']).first()
                        if achieve_info:
                            achieve_info['file_url'] = info['file_url']
                            achieve_info['file_name'] = info['file_name']
                            achieve_info['file_path'] = info['file_path']
                            achieve_info['file_type_id'] = info['file_type_id']
                            achieve_info['file_state'] = info['file_state']
                        self.controlsession.add(achieve_info)

                    for key, val in file_info_dict.items():
                        other = val
                        other_info = self.controlsession.query(SupplierAchieve).filter_by(
                            id=other['id']).first()
                        if other_info:
                            other_info['file_url'] = other['file_url']
                            other_info['file_name'] = other['file_name']
                            other_info['file_path'] = other['file_path']
                            other_info['file_type_id'] = other['file_type_id']
                            other_info['file_state'] = other['file_state']
                        self.controlsession.add(other_info)
                else:
                    #创建存档资料信息
                    for achieve_info in normal_info_list:
                        achieve = SupplierAchieve(supplier_id=achieve_info['supplier_id'], file_url=achieve_info['file_url'],
                                                  file_name=achieve_info['file_name'], file_path=achieve_info['file_path'],
                                                  file_type_id=achieve_info['file_type_id'], file_state=achieve_info['file_state'])
                        self.controlsession.add(achieve)

                    otherList = []
                    for i in xrange(len(other_info_dict)):
                        val = other_info_dict.get(str(i), "")
                        if val:
                            otherList.append(val)

                    for other_in in otherList:
                        other_cretirfication = SupplierAchieve(supplier_id=other_in['supplier_id'], file_url=other_in['file_url'],
                                                               file_name=other_in['file_name'], file_path=other_in['file_path'],
                                                               file_type_id=other_in['file_type_id'], file_state=other_in['file_state'])
                        self.controlsession.add(other_cretirfication)
                self.controlsession.commit()
                return json.dumps({"code": ServiceCode.success})

            return json.dumps({"code": ServiceCode.service_exception})  # 添加错误码 ： 供应商不存在，请先添加供应商
        except Exception, e:
            self.controlsession.rollback()
            print e
            return json.dumps({"code": ServiceCode.service_exception})

    def get_clerk_info(self, sup_code):
        '''
        @function : 检查供应商代码
        :param sup_id:
        :return:
        '''
        try:
            rs = self.controlsession.query(SupplierBaseInfo).filter_by(supplier_code=sup_code).first()
            if rs:
                return json.dumps({"code": ServiceCode.service_exception})  #添加错误码：已经存在供应商code
            return json.dumps({"code": ServiceCode.success})
        except Exception, e:
            return json.dumps({"code": ServiceCode.service_exception})

    def get_check_supplier_name_info(self, sup_name):
        '''
        @function : 检查供应商全名
        :param sup_name:
        :return:
        '''
        try:
            rs = self.controlsession.query(SupplierBaseInfo).filter_by(supplier_name=sup_name).first()
            if rs:
                return json.dumps({"code": ServiceCode.service_exception})  #添加错误码：已经存在供应商code
            return json.dumps({"code": ServiceCode.success})
        except Exception, e:
            return json.dumps({"code": ServiceCode.service_exception})

    def get_supplier_code_by_auto(self):
        '''
        @funtion : 获得数据库自动检索的下一个为空的supplier_code
        :return: supplier_code
        '''
        try:
            rs = self.controlsession.query(SupplierBaseInfo).order_by(SupplierBaseInfo.id.desc()).first()
            if rs is not None:
                if len(rs.supplier_code) > 7:
                    return json.dumps({"code": ServiceCode.service_exception})
                code = eval(rs.supplier_code) + 0.0001  #supplier_code_list[1]后四位数据
                supplier_code = str(code)
                supplier_code = supplier_code.split('.')[1]
            else:
                supplier_code = "0001"
            return json.dumps({'code': ServiceCode.success, 'supllier_code': supplier_code})
        except Exception, e:
            print traceback.format_exc()
            return json.dumps({"code": ServiceCode.service_exception})

    def get_state_all_type_info(self):
        '''
        @function : 获得供应商状态所有类型
        :return:
        '''
        rs_list = SupplyAttr.SUPPLIER_STATE_TYPE
        # rs_list.pop('type')
        if rs_list:
            return rs_list
        else:
            return {}
        # rs_list = self.controlsession.query(SupplierState).all()
        # dataDict = {}
        # if rs_list:
        #     for rs in rs_list:
        #         rs = rs.to_json()
        #         id = rs['id']
        #         name = rs['name']
        #         dataDict[id] = name
        #     return dataDict
        # else:
        #     return {}

    def get_all_supplier_baseinfo(self, supplier_used_state=SupplyAttr.STATE_USE, show_state=SupplyAttr.SUPPLIER_STATE_SHOW):
        """
        :param supplier_used_state: 供应商状态
        :param show_state: 供应商显示状态
        :return:
        """
        supplier_used_state_type = get_key_by_value(SupplyAttr.SUPPLIER_STATE_TYPE, supplier_used_state)
        # total = self.controlsession.query(func.count(SupplierBaseInfo.id)).filter_by(
        #     state_id=supplier_used_state_type,show_state=show_state).scalar()
        # base_datas = self.controlsession.query(SupplierBaseInfo).filter_by(state_id=supplier_used_state_type,
        #                                                                    show_state=show_state).\
        #     order_by(SupplierBaseInfo.id).all()
        total = self.controlsession.query(func.count(SupplierBaseInfo.id)).filter_by(
            state_id=supplier_used_state_type).scalar()
        base_datas = self.controlsession.query(SupplierBaseInfo).filter_by(state_id=supplier_used_state_type).\
            order_by(SupplierBaseInfo.id).all()

        if base_datas:
            base_datas_list = []
            for data in base_datas:
                temp_dict = {}
                temp_dict['supplier_id'] = data.id # 供应商ID
                temp_dict['supplier_name'] = data.supplier_name # 供应商名字
                temp_dict['supplier_fullname'] = data.supplier_full_name # 供应商全名supplier_full_name
                temp_dict['supplier_code'] = data.supplier_code # 供应商代码supplier_code
                temp_dict['supplierState_id'] = data.state_id # 状态类型ID
                supplier_state = SupplyAttr.SUPPLIER_STATE_TYPE.get(data.state_id)
                if supplier_state is None:
                    raise CodeError(ServiceCode.service_exception,
                                    msg=u"供应商%s的状态信息有误" % data.supplier_name)
                else:
                    temp_dict['supplier_state'] = "" # 状态类型

                temp_dict['purchaseContacts_id'] = data.principal_id # 采购对接人ID
                mc = MixUserCenterOp()
                principal_info = mc.get_user_info(data.principal_id)
                if principal_info:
                    temp_dict['purchase_contacts'] = principal_info.get('username', "") # 采购对接人
                else:
                    raise CodeError(ServiceCode.service_exception,
                                    msg=u"供应商%s的采购对接人信息有误" % data.supplier_name)

                temp_dict['currency_id'] = data.currency_id # 结算币种类型ID
                currency_dict = self.get_currency(data.currency_id)
                if currency_dict:
                    temp_dict['currency'] = currency_dict.get("name")
                else:
                    raise CodeError(ServiceCode.service_exception,
                                    msg=u"供应商%s的结算币种信息有误" % data.supplier_name)

                temp_dict['show_state'] = data.show_state  # 显示状态show_state

                temp_dict['val_added_rate'] = data.vat_rates if data.vat_rates is not None else "" # 增值税率vat_rates

                # 结算方式ID
                temp_dict['settlementMode_id'] = data.selt_modes_id if data.selt_modes_id is not None else ""
                if data.selt_modes_id is None:
                    temp_dict['settlement_mode'] = "" # 结算方式
                else:
                    settlement_mode_dict = self.get_selt_modes(data.selt_modes_id)
                    if settlement_mode_dict:
                        temp_dict['settlement_mode'] = settlement_mode_dict.get("name") # 结算方式
                    else:
                        raise CodeError(ServiceCode.service_exception,
                                        msg=u"供应商%s的结算方式信息有误" % data.supplier_name)

                # 结算时间ID
                temp_dict['settlementDate_id'] = data.selt_dater_id if data.selt_dater_id is not None else ""
                if data.selt_dater_id is None:
                    temp_dict['settlement_date'] = "" # 结算时间
                else:
                    settlement_date_dict = self.get_selt_date(data.selt_dater_id)
                    if settlement_date_dict:
                        temp_dict['settlement_date'] = settlement_date_dict.get("name") # 结算时间
                    else:
                        raise CodeError(ServiceCode.service_exception,
                                          msg=u"供应商%s的结算时间信息有误" % data.supplier_name)

                # 国家supplier_country
                temp_dict['country'] = data.supplier_country if data.supplier_country is not None else ""
                # 省份supplier_province
                temp_dict['prov'] = data.supplier_province if data.supplier_province is not None else ""
                # 城市supplier_city
                temp_dict['city'] = data.supplier_city if data.supplier_city is not None else ""
                # 地址supplier_addr
                temp_dict['address'] = data.supplier_addr if data.supplier_addr is not None else ""
                # 开户银行bank_name
                temp_dict['deposit_bank'] = data.bank_name if data.bank_name is not None else ""
                # 银行账号acct_no
                temp_dict['bank_account'] = data.acct_no if data.acct_no is not None else ""
                # 税务登记号tax_regist_no
                temp_dict['tax_registration_number'] = data.tax_regist_no if data.tax_regist_no is not None else ""
                # 营业执照注册号business_lincese
                temp_dict['business_license_number'] = data.business_lincese if data.business_lincese is not None else ""
                # 组织结构代码organize_code
                temp_dict['organizational_structure_code'] = data.organize_code if data.organize_code is not None else ""
                base_datas_list.append(temp_dict)
            return total, base_datas_list
        else:
            return total, []


    def get_supplier_contact_info(self, supplier_id=None):
        """
        :param supplier_id: 供应商ID
        :return: 返回该供应商ID对应的联系方式等信息，字典格式
        """
        if supplier_id is None:
            raise ValueError("supplier_id must be an integer")
        cont_datas = self.controlsession.query(SupplierContact).filter(SupplierContact.supplier_id == supplier_id
                                                                       ).order_by(SupplierContact.id).first()
        result_dict = {}
        if cont_datas is None:
            return result_dict

        cont_datas_dict = cont_datas.to_json()

        result_dict['contact_id'] = cont_datas_dict.get("id", None) # 联系人ID
        result_dict['supplier_id'] = cont_datas_dict.get("supplier_id", None) # 供应商ID
        result_dict['contacts'] = cont_datas_dict.get("supplier_contact_name", None) # 联系人
        result_dict['contact_title'] = cont_datas_dict.get("supplier_contact_position", None) # 联系人职务
        result_dict['contact_information'] = cont_datas_dict.get("supplier_contact_mobile", None) # 联系人方式（手机）
        result_dict['contact_telephone'] = cont_datas_dict.get("supplier_contact_telphone", None) # 联系人电话（座机）
        result_dict['email_address'] = cont_datas_dict.get("supplier_contact_email", None) # 邮件地址
        result_dict['faxes'] = cont_datas_dict.get("supplier_contact_tax") # 传真

        return result_dict

    def get_supplier_id(self, supplier_name=None):
        if supplier_name is None:
            supplier_id = self.controlsession.query(SupplierBaseInfo.id).order_by(SupplierBaseInfo.id).all()
        else:
            if not isinstance(supplier_name, str):
                raise TypeError("unsupported operand types(s) for customer_name: %s " % type(supplier_name))
            supplier_id = self.controlsession.query(SupplierBaseInfo.id).filter(
                SupplierBaseInfo.supplier_name.cast(LargeBinary)==supplier_name).order_by(SupplierBaseInfo.id).all()
        supplier_id_list = []
        for data in supplier_id:
            supplier_id_list.append(data[0])

        return supplier_id_list




# -*-coding:utf-8-*-

import json
from flask import jsonify
from flask import session
import traceback
import types
from data_mode.erp_supply.control_base.controlBase import ControlEngine
from data_mode.erp_supply.mode.supply_manage_mode.supplier_info import SupplierBaseInfo
from data_mode.erp_supply.mode.supply_manage_mode.supplier_contact import SupplierContact
from data_mode.erp_supply.mode.supply_manage_mode.supplier_achieve import SupplierAchieve

from data_mode.user_center.control_base.controlBase import ControlEngine as userControlEngine
from data_mode.user_center.model.organ_department import OrganDepartMent
from data_mode.user_center.model.admin_user import AdminUser
from data_mode.user_center.control.mixOp import MixUserCenterOp
from data_mode.user_center.model.organ_position import OrganPosition

from config.service_config.returncode import ServiceCode
from config.share.share_define import *

from sqlalchemy import func, or_, and_, cast, LargeBinary
from config.share.share_define import SupplyAttr
from data_mode.erp_supply.mode.supply_manage_mode.supplier_attribute import SupplierAttribute


class SupplierListInfo(ControlEngine, userControlEngine):
    def __init__(self):
        ControlEngine.__init__(self)

        #文件格式
        self.fileFormatPictureList = ['jpg','png','jpeg','gif','doc', 'excel', 'pdf','txt']
        self.fileFormatDocList = ['doc', 'excel', 'pdf','txt']

    def GetShowState(self):
        show_state = '01'
        return show_state

    def GetDeleteState(self):
        del_state = '02'
        return del_state

    # 功能描述：根据提供的供应商代码或供应商名称关键字，搜索供应商信息，并分页列出
    # @param supplierCode：供应商代码     supplierName:供应商名称  currentPage: 分页的当前页数  u  pageList:分页每页显示的记录数
    # @return 供应商信息列表
    def GetSupplierList(self,searchType, searchValue, currentPage, pageList ):
        # print "searchType, searchValue", searchType, searchValue
        try:
            start = (currentPage - 1) * pageList
            pagination = None
            count = 0
            supp_state_dict = {val: key for key, val in SupplyAttr.SUPPLIER_STATE_TYPE.items()}

            #搜索内容为空的情况，返回供应商所有有效数据
            if len(searchValue.strip()) == 0:
                count = self.controlsession.query(func.count(SupplierBaseInfo.id)).order_by(
                    SupplierBaseInfo.id.asc()).filter_by(
                    show_state=SupplyAttr.SUPPLIER_STATE_SHOW,
                    state_id=supp_state_dict[SupplyAttr.STATE_USE]).scalar()

                pagination = self.controlsession.query(SupplierBaseInfo).order_by(
                    SupplierBaseInfo.id.asc()).filter_by(
                    show_state=SupplyAttr.SUPPLIER_STATE_SHOW,
                    state_id=supp_state_dict[SupplyAttr.STATE_USE]).limit(pageList).offset(start)
            else:
                #搜索内容不为空
                if searchType == SUPPLIER_SECERCH_TYPE_CODE:         #表示按照供应商代码查询
                    supplierCode = searchValue
                    # print('print*******************', supplierCode)
                    count = self.controlsession.query(func.count(SupplierBaseInfo.id)).order_by(
                                SupplierBaseInfo.id.asc()).filter(SupplierBaseInfo.supplier_code.cast(LargeBinary)
                                                                  == supplierCode,
                                                                  SupplierBaseInfo.show_state ==
                                                                  SupplyAttr.SUPPLIER_STATE_SHOW,
                                                                  SupplierBaseInfo.state_id ==
                                                                  supp_state_dict[SupplyAttr.STATE_USE]).scalar()

                    pagination = self.controlsession.query(SupplierBaseInfo).order_by(
                                     SupplierBaseInfo.id.asc()).filter(SupplierBaseInfo.supplier_code.cast(LargeBinary)
                                                                  == supplierCode, SupplierBaseInfo.show_state ==
                                                                  SupplyAttr.SUPPLIER_STATE_SHOW,
                                                                  SupplierBaseInfo.state_id ==
                                                                  supp_state_dict[SupplyAttr.STATE_USE]
                                                                       ).limit(pageList).offset(start)
                elif searchType == SUPPLIER_SECERCH_TYPE_NAME:   # 供应商名称
                    supplierName = searchValue
                    search_str = '%' + supplierName.strip() + '%'

                    count = self.controlsession.query(func.count(SupplierBaseInfo.id)).order_by(
                                SupplierBaseInfo.id.asc()).filter(
                                SupplierBaseInfo.show_state == SupplyAttr.SUPPLIER_STATE_SHOW,
                                SupplierBaseInfo.state_id == supp_state_dict[SupplyAttr.STATE_USE],
                                SupplierBaseInfo.supplier_name.cast(LargeBinary).like(search_str)).scalar()

                    pagination = self.controlsession.query(SupplierBaseInfo).order_by(
                                     SupplierBaseInfo.id.asc()).filter(
                                     SupplierBaseInfo.show_state == SupplyAttr.SUPPLIER_STATE_SHOW,
                                     SupplierBaseInfo.state_id == supp_state_dict[SupplyAttr.STATE_USE],
                                     SupplierBaseInfo.supplier_name.cast(LargeBinary).like(search_str)).limit(pageList).offset(start)
                elif searchType == SUPPLIER_SECERCH_TYPE_CALL_MAN:    # 供应商联系人
                    supplierName = searchValue
                    search_str = '%' + supplierName.strip() + '%'

                    contract_list = self.controlsession.query(SupplierContact).order_by(SupplierContact.id.asc()).filter(
                        SupplierContact.supplier_contact_name.cast(LargeBinary).like(search_str)).all()

                    pagination = []
                    for t_info in contract_list:
                        info = t_info.to_json()
                        s_id = info['supplier_id']

                        rs = self.controlsession.query(SupplierBaseInfo).filter(
                            SupplierBaseInfo.show_state == SupplyAttr.SUPPLIER_STATE_SHOW,
                            SupplierBaseInfo.state_id == supp_state_dict[SupplyAttr.STATE_USE],
                            SupplierBaseInfo.id == s_id).first()
                        pagination.append(rs)
                    count = len(pagination)
                elif searchType == SUPPLIER_SECERCH_TYPE_TEL_NUMBER:  #供应商联系电话
                    supplierName = searchValue
                    search_str = '%' + supplierName.strip() + '%'

                    contract_list = self.controlsession.query(SupplierContact).order_by(SupplierContact.id.asc()).filter(
                        SupplierContact.supplier_contact_telphone.like(search_str)).all()
                    pagination = []
                    for t_info in contract_list:
                        info = t_info.to_json()
                        s_id = info['supplier_id']

                        rs = self.controlsession.query(SupplierBaseInfo).filter(
                            SupplierBaseInfo.show_state == SupplyAttr.SUPPLIER_STATE_SHOW,
                            SupplierBaseInfo.state_id == supp_state_dict[SupplyAttr.STATE_USE],
                            SupplierBaseInfo.id == s_id).first()
                        pagination.append(rs)
                    count = len(pagination)

            if isinstance(pagination, types.NoneType): #type(pagination) is types.NoneType
                list_baseinfo = {}
            else:
                list_baseinfo = [item.to_json() for item in pagination]

            for item in list_baseinfo:
                principal_id = item['principal_id']
                currency_id = item['currency_id']
                state_id = item['state_id']

                item['currency_id'] = self.GetCurrencyName(currency_id)
                item['state_id'] = self.GetState(state_id)

                #新增给新增物料选择供应商字段 2016-11-30
                if isinstance(item['supplier_province'], types.NoneType):
                    item['supplier_province'] = ""
                if isinstance(item['supplier_city'], types.NoneType):
                    item['supplier_city'] = ""
                if isinstance(item['supplier_addr'], types.NoneType):
                    item['supplier_addr'] = ""
                item['addr'] = item['supplier_province'] + item['supplier_city'] + item['supplier_addr']
                item['code'] = item['supplier_code']
                item['name'] = item['supplier_name']
                contract = self.controlsession.query(SupplierContact).order_by(SupplierContact.id.asc()).filter(
                    SupplierContact.supplier_id == item['id']).first()
                if contract:
                    contract = contract.to_json()
                    item['call_man'] = contract['supplier_contact_name']
                    item['tel'] = contract['supplier_contact_telphone']
                else:
                    item['call_man'] = ""
                    item['tel'] = ""

                userControlEngine.__init__(self)
                if principal_id.strip() == '':
                    item['department_id'] = ''
                    item['principal_id'] = ''
                else:
                    print "principal_id", principal_id
                    item['department_id'] = self.GetDepartmentName(int(principal_id))
                    item['principal_id'] = self.GetPrincipalName(int(principal_id))

                ControlEngine.__init__(self)
        except Exception, e:
            print traceback.format_exc()
            list_baseinfo=[]
            count = 0
            raise

        return count, list_baseinfo


    def GetCurrencyName(self, currencyID):
        """
        功能描述：根据对应的货币币种ID解析货币币种含义（人民币、美元、欧元...)
        :param currencyID: 货币币种ID
        :return: 货币币种
        """
        # curr_type = SupplyAttr.ATTR_TYPE_CURRENCY
        data = self.controlsession.query(SupplierAttribute).filter_by(id=currencyID).first()
        CurrencyName= {}
        if isinstance(data, types.NoneType):
            CurrencyName['name'] = ''
        else:
            CurrencyName = data.to_json()

        return CurrencyName['name']

    def GetDepartmentName(self, principalID):
        """
        功能描述：根据对应的采购对接人ID（principalID）解析对应的部门（行政部、人力部...)
        :param principalID: 采购对接人ID
        :return: 部门名称
        """
        departmentName = {}

        #根据principalID从admin_user表中查找position_id
        #print('principalID %d' % principalID)
        data_pos = self.controlsession.query(AdminUser).filter_by(id=principalID).first()
        if isinstance(data_pos, AdminUser):
            pos_id = data_pos.position_id
            if isinstance(pos_id, types.NoneType):
                departmentName['name'] = ''
            else:
                #根据position_id从organ_position中查找department_id
                department_data = self.controlsession.query(OrganPosition).filter_by(id=pos_id).first()
                if isinstance(department_data, OrganPosition):
                    department_id = department_data.department_id
                    if isinstance(department_id, types.NoneType):
                        departmentName['name'] = ''
                    else:
                        #根据department_id
                        data = self.controlsession.query(OrganDepartMent).filter_by(id=department_id).first()
                        if isinstance(data, OrganDepartMent):
                            departmentName = data.to_json(False)
                        else:
                            departmentName['name'] = ''
                else:
                    departmentName['name'] = ''
        else:
            departmentName['name'] = ''
        return departmentName['name']

    def GetPrincipalName(self, principalID):
        """
        功能描述：根据对应的采购对接人的ID解析对应的部门
        :param principalID: 采购对接人ID
        :return: 采购对接人名称
        """
        data = self.controlsession.query(AdminUser).filter_by(id=principalID).first()
        principalName = {}
        if isinstance(data, types.NoneType):
            principalName['name'] = ''
        else:
            principalName = data.to_json_simple()
        return principalName['name']

    def GetSelttementMode(self, selttmentModeID):
        """
        功能描述：根据结算模式ID解析出相应的结算模式
        :param selttmentModeID: 结算模式ID
        :return: 结算模式
        """
        # selt_model_type = SupplyAttr.ATTR_TYPE_SELT_MODELS
        data = self.controlsession.query(SupplierAttribute).filter_by(id=selttmentModeID).first()
        selttmentMode={}
        if isinstance(data, types.NoneType):
            selttmentMode['name'] = ''
        else:
            selttmentMode = data.to_json()
        return selttmentMode['name']

    def GetSelttementTime(self, selttmentTimeID):
        """
        功能描述：根据结算时间ID解析出相应的结算时间
        :param selttmentTimeID: 结算时间ID
        :return: 结算时间
        """
        # selt_date_type = SupplyAttr.ATTR_TYPE_SELT_DATER
        data = self.controlsession.query(SupplierAttribute).filter_by(id=selttmentTimeID).first()
        selttmentTime={}
        if isinstance(data, types.NoneType):
            selttmentTime['name'] = ''
        else:
            selttmentTime = data.to_json()
        return selttmentTime['name']

    def GetState(self, state_id):
        """
        功能描述：根据数据库erp_supply中的supplier_baseinfo表中的state_id字段从supplier_state中解析state_id
        :param state_id: 供应商使用状态id
        :return: 解析后的供应商使用状态
        """
        # state_type = SupplyAttr.ATTR_TYPE_SUPPLIER_STATE
        data = self.controlsession.query(SupplierAttribute).filter_by(id=state_id).first()
        state = {}
        if isinstance(data, types.NoneType):
            state['name'] = ''
        else:
            state = data.to_json()
        return state['name']

    def GetAchiverType(self, file_type_id):
        """
        功能描述：解析证书类型
        :param file_type_id:
        :return:
        """
        # achieve_type = SupplyAttr.ATTR_TYPE_ARCHIVE
        data = self.controlsession.query(SupplierAttribute).filter_by(id=file_type_id).first()
        file_type = {}
        if isinstance(data, types.NoneType):
            file_type['name'] = ''
        else:
            file_type = data.to_json()
        return file_type['name']

    def GetDetailInfo(self, supplier_id):
        """
        功能描述：根据提供的供应商代码，获取该供应商关联的相关信息
        :param supplier_code: 供应商代码
        :return: 供应商相关联的信息
        """
        ControlEngine.__init__(self)
        #从数据库erp_supply的supplier_baseinfo表中读取供应商信息
        return_supplier_data = {}
        certificate_list = []
        other_certificate_list = []

        baseInfo = {}       #基本信息
        seltInfo = {}       #结算信息
        contactInfo={}      #联系人信息
        contact_list = []
        addrInfo = {}       #地址信息
        industryInfo = {}   #工商信息
        print('supplier_datas')
        supplier_datas = self.controlsession.query(SupplierBaseInfo).filter_by(id=supplier_id).first()
        print(supplier_datas)
        if isinstance(supplier_datas, SupplierBaseInfo):
            supplier_datas_dict = supplier_datas.to_json()

            #supplier_id = supplier_datas_dict['id']

            principal_id = supplier_datas_dict['principal_id']      #采购对接人id
            currency_id = supplier_datas_dict['currency_id']        #币种id
            selt_modes_id = supplier_datas_dict['selt_modes_id']    #结算模式id
            selt_dater_id = supplier_datas_dict['selt_dater_id']    #结算时间id
            state_id = supplier_datas_dict['state_id']

            #从数据库erp_supply的supplier_contact表中读取供应商联系人信息
            supplier_contact_datas = self.controlsession.query(SupplierContact).filter_by(supplier_id=supplier_id).all()

            supplier_certificates = self.controlsession.query(SupplierAchieve).order_by(
                                     SupplierAchieve.id.asc()).filter_by(supplier_id=supplier_id).all()
            #根据id解析数据
            supplier_datas_dict['currency_id'] = self.GetCurrencyName(currency_id)          #币种信息
            supplier_datas_dict['selt_modes_id'] = self.GetSelttementMode(selt_modes_id)    #结算方式
            supplier_datas_dict['selt_dater_id'] = self.GetSelttementTime(selt_dater_id)    #结算时间
            supplier_datas_dict['state_id'] = self.GetState(state_id)

            #组合证书信息
            #other_certificate_list = []
            #temp_other_certificate = {}
            if isinstance(supplier_certificates, types.ListType):
                for cer_data in supplier_certificates:
                    temp_dict = {}
                    file_type = self.GetAchiverType(cer_data.file_type_id)
                    supplier_dict = {val: key for key, val in SupplyAttr.SUPPLIER_ARCHIEVE_TYPE.items()}
                    return_certificate = {}
                    if file_type == SupplyAttr.OTHER_ARCHIEVE: #其他证书
                        temp_dict['name'] = cer_data.file_name
                        temp_dict['url'] = cer_data.file_url
                        #return_certificate[cer_data.id] = temp_dict
                        other_certificate_list.append(temp_dict)
                    else:
                        temp_dict['name'] = cer_data.file_name
                        temp_dict['url'] = cer_data.file_url
                        file_key = supplier_dict[file_type]
                        file_str_name = SupplyAttr.SUPPLIER_ARCHIEVE_TYPE_ENGLISH[file_key]
                        return_certificate[file_str_name] = temp_dict
                        certificate_list.append(return_certificate)
            #temp_other_certificate['others'] = other_certificate_list
            #certificate_list.append(temp_other_certificate)


            userControlEngine.__init__(self)
            if principal_id.strip() == '':
                supplier_datas_dict['department_id'] = ''
                supplier_datas_dict['principal_id'] = ''
            else:
                supplier_datas_dict['department_id'] = self.GetDepartmentName(int(principal_id))
                supplier_datas_dict['principal_id'] = self.GetPrincipalName(int(principal_id))

            #组合基本信息
            baseInfo['id'] = supplier_datas_dict['id']
            baseInfo['supplier_code'] = supplier_datas_dict['supplier_code']
            baseInfo['supplier_name'] = supplier_datas_dict['supplier_name']
            baseInfo['supplier_full_name'] = supplier_datas_dict['supplier_full_name']
            baseInfo['department_id'] = supplier_datas_dict['department_id']
            baseInfo['principal_id'] = supplier_datas_dict['principal_id']
            baseInfo['currency_id'] = supplier_datas_dict['currency_id']
            baseInfo['state_id'] = supplier_datas_dict['state_id']

            #组合结算信息
            seltInfo['selt_modes_id'] = supplier_datas_dict['selt_modes_id']
            seltInfo['selt_dater_id'] = supplier_datas_dict['selt_dater_id']
            seltInfo['vat_rates'] = supplier_datas_dict['vat_rates']

            #组合联系人信息
            if isinstance(supplier_contact_datas, types.ListType):
                temp_dict = {}
                for data in supplier_contact_datas:
                    temp_dict['supplier_contact_name'] = data.supplier_contact_name
                    temp_dict['supplier_contact_position'] = data.supplier_contact_position
                    temp_dict['supplier_contact_mobile'] = data.supplier_contact_mobile
                    temp_dict['supplier_contact_email'] = data.supplier_contact_email
                    temp_dict['supplier_contact_telphone'] = data.supplier_contact_telphone
                    temp_dict['supplier_contact_tax'] = data.supplier_contact_tax

                    contact_list.append(temp_dict)
                    temp_dict = {}
                contactInfo['count'] = len(contact_list)
                contactInfo['rows'] = contact_list
            else:
                contactInfo['count'] = 0
                contactInfo['rows'] = []


            #组合地址信息
            addrInfo['supplier_country'] = supplier_datas_dict['supplier_country']
            addrInfo['supplier_province'] = supplier_datas_dict['supplier_province']
            addrInfo['supplier_city'] = supplier_datas_dict['supplier_city']
            addrInfo['supplier_addr']= supplier_datas_dict['supplier_addr']

            #组合工商信息
            industryInfo['bank_name'] = supplier_datas_dict['bank_name']
            industryInfo['acct_no'] = supplier_datas_dict['acct_no']
            industryInfo['tax_regist_no'] = supplier_datas_dict['tax_regist_no']
            industryInfo['business_lincese'] = supplier_datas_dict['business_lincese']
            industryInfo['organize_code'] = supplier_datas_dict['organize_code']

            return_supplier_data['baseInfo'] = baseInfo
            return_supplier_data['seltInfo'] = seltInfo
            return_supplier_data['contactInfo'] = contactInfo
            return_supplier_data['addrInfo'] = addrInfo
            return_supplier_data['industryInfo'] = industryInfo

        return return_supplier_data, certificate_list, other_certificate_list

    def DeleteSupplierInfo(self, supplier_id_list):
        """
        功能描述：根据提供的供应商id删除相关的供应商信息,并返回删除后的供应商列表
        :param supplier_id_list: 需要删除信息的供应商id列表
        :return: 删除了指定供应商后的供应商信息列表
        """
        try:
            #supplier_id_list=[66]
            for supplier_id in supplier_id_list:
                print('supplier_id %s' % supplier_id)

                print("GetDeleteState:**************")
                print(self.GetDeleteState())
                self.controlsession.query(SupplierBaseInfo).filter_by(id=supplier_id).update({SupplierBaseInfo.show_state: '02'})

                print('delete success')

                try:
                    self.controlsession.commit()
                except Exception as e:
                    raise

        except Exception, ex:
            print ex
            raise

#-*- coding:utf-8 –*-

import datetime,json
import re

from flask import session
from sqlalchemy import LargeBinary, and_
from sqlalchemy import or_, func
from sqlalchemy.exc import SQLAlchemyError,IntegrityError
from config.service_config.returncode import ServiceCode
from control_center.flagship_manage.warehouse_manage.control.in_out_warehouse_op import InOutWarehouseOp
from control_center.shop_manage.good_info_manage.control.mixOp import HolaWareHouse
from data_mode.hola_flagship_store.control_base.controlBase import ControlEngine
from data_mode.hola_flagship_store.mode.warehouse_mode.warehouse_manage import *
from data_mode.hola_flagship_store.mode.sale_mode.customer_info import CustomerInfo
from data_mode.hola_flagship_store.mode.after_sale.deal_with_infomation import *
import traceback
from data_mode.hola_flagship_store.mode.warehouse_mode.warehouse_manage import *
from public.exception.custom_exception import CodeError
from data_mode.hola_flagship_store.mode.sale_mode.sale_order_detail import SaleOrderDetail
from data_mode.hola_flagship_store.mode.sale_mode.sale_order import SaleOrder
from data_mode.hola_flagship_store.mode.sale_mode.set_product_record import SetProductRecord
from data_mode.hola_flagship_store.mode.sale_mode.set_record_info import SetRecordInfo
from control_center.flagship_manage.flagship_info_manage.control.flagship_op import FlagShipOp
from data_mode.user_center.control.mixOp import MixUserCenterOp
from config.share.share_define import SCENE_EXCHANGE_GOOD,TH_RECEIPTS
from control_center.flagship_manage.flagship_info_manage.control.mixOp import ClerkOp
from public.sale_share.share_function import *
from public.logger.syslog import SystemLog

class ReturnService(ControlEngine):
    def __init__(self):
        '''
        初始化数据库引擎
        :return:
        '''
        ControlEngine.__init__(self)

    def AddServiceInfo(self, return_dict):
        result = {}
        number = return_dict['number']
        newnumber = None
        try:
            customer_dict = {}
            deal_with_dict = {}
            in_out_warehouse_dict = {}
            relation_dict = {}
            invoice_dict = {}
            other_info_list = json.loads(return_dict['other_info_list'])
            treatment_list = json.loads(return_dict['treatment_list'])

            for key, value in return_dict.items():
                # 客户信息
                if key in ('number', 'customerName',
                           'customerPhone', 'customerEmail',
                           'customerAddress', 'flagshipid'):
                    customer_dict[key] = value

                # 处理信息
                if key in ('treatment',
                           'problem_describe', 'rem',
                           'relation_order_number',
                           'buy_machine_tiem',
                           'invoice', 'quote', 'actual_amount', 'is_shop_voucher'):
                    if key == 'buy_machine_tiem':
                        deal_with_dict[key] = datetime.datetime.strptime(value, '%Y-%m-%d')
                    elif key == 'is_shop_voucher':
                        flg_set = {'is_shop_voucher': value}
                        deal_with_dict['flg_set'] = str(flg_set)
                    else:
                        deal_with_dict[key] = value

                # 单据信息
                if key in ('number', 'flagshipid', 'other_info', 'add_user'):
                    in_out_warehouse_dict[key] = value

                # 关联信息
                if key in('number', 'flagshipid', 'serial', 'product_id', 'actual_amount'):
                    relation_dict[key] = value

                # 库存
                if key in('flagshipid', 'product_id'):
                    invoice_dict[key] = value
            is_exchange_goods = True if int(return_dict['treatment']) == int(SCENE_EXCHANGE_GOOD) else False
            date_time = datetime.datetime.now()
            if customer_dict['customerAddress']:
                adds = (customer_dict['customerAddress']).split(',')
                buy_prov = adds[0]
                buy_city = adds[1]
                buy_addr = adds[2]
            else:
                buy_prov = ''
                buy_city = ''
                buy_addr = ''

            # 用户信息
            customer_info_obj = CustomerInfo(store_id=customer_dict['flagshipid'],
                                             orderNo=customer_dict['number'],
                                             name=customer_dict['customerName'],
                                             tel=customer_dict['customerPhone'],
                                             email=customer_dict['customerEmail'],
                                             buy_addr=buy_addr,
                                             buy_city=buy_city,
                                             buy_prov=buy_prov)
            self.controlsession.add(customer_info_obj)
            self.controlsession.commit()
            customer_id = customer_info_obj.id
            # 处理信息
            if not deal_with_dict['quote']:
                deal_with_dict_quote = 0
            else:
                deal_with_dict_quote = deal_with_dict['quote']

            if not deal_with_dict['actual_amount']:
                deal_with_dict_actual_amount = 0
            else:
                deal_with_dict_actual_amount = deal_with_dict['actual_amount']

            deal_with_infomation_obj = DealWithInfomation(deal_type=deal_with_dict['treatment'],
                                                          problem_describe=deal_with_dict['problem_describe'],
                                                          rem=deal_with_dict['rem'],
                                                          associated_order_number=deal_with_dict['relation_order_number'],
                                                          buy_machine_tiem=deal_with_dict['buy_machine_tiem'],
                                                          invoice=deal_with_dict['invoice'],
                                                          quote=(float(deal_with_dict_quote))*COVERT_MONEY_TYPE_NUMBER,
                                                          actual_amount=(float(deal_with_dict_actual_amount))*COVERT_MONEY_TYPE_NUMBER,
                                                          flg_set=deal_with_dict['flg_set'])
            self.controlsession.add(deal_with_infomation_obj)
            self.controlsession.commit()

            deal_with_information_id = deal_with_infomation_obj.id
            name = return_dict['add_user']
            clerk_op = ClerkOp()
            clerk_infos = clerk_op.get_clerks_info(customer_dict['flagshipid'])
            for itme in clerk_infos:
                if itme['name'] == name:
                    user_id = itme['id']

            other_info = return_dict['other_info']  # 备注信息
            # 首先生成一条退货记录
            TH_in_out_warehouse_obj = InOutWarehouse(number=customer_dict['number'],
                                                     date=date_time,
                                                     user=name,
                                                     user_id=user_id,
                                                     remark_info=other_info,
                                                     operate_type=OperateType.return_service,
                                                     flagship_id=customer_dict['flagshipid'],
                                                     number_type=TH_RECEIPTS,
                                                     in_out_number=len(treatment_list))

            self.controlsession.add(TH_in_out_warehouse_obj)
            self.controlsession.commit()

            from public.sale_share.share_function import ShareFunctionOp

            in_out_obj = ShareFunctionOp()
            # 根据是否返厂生成相应的单据,0:表示不返厂，1:表示返厂(根据条件是生成返厂单or入库单)
            INnumber = in_out_obj.create_numberNo(relation_dict['flagshipid'],
                                               OperateType.other_in)
            is_flag = True
            is_flag1 = True
            flag_first = True
            newnumber=''
            in_out_len = 0
            for itme in treatment_list:
                if itme['is_to_factory'] == 0:
                    in_out_len = in_out_len + 1
            in_number = 0
            for itme in treatment_list:
                warehouse_type = None
                condition = 'ProductRelation.flagship_id == %s,ProductRelation.warehouse_type_id == %s,ProductRelation.num == %s' % (relation_dict['flagshipid'],WarehouseType.out_warehouse,1)
                if itme['serial']:
                    condition = condition+",ProductRelation.number == '%s' " % (itme['serial'])
                condition ='and_('+condition+')'
                update_num = self.controlsession.query(ProductRelation).filter(eval(condition)).first()
                if update_num:
                    update_num.num = 0
                    self.controlsession.add(update_num)
                if itme['is_to_factory'] == 1:
                    if is_flag:
                        product_relation_obj = ProductRelation(number=itme['serial'],
                                                               good_id=itme['product_id'],
                                                               order_number=customer_dict['number'],
                                                               warehouse_type_id=WarehouseType.back_factory_warehouse,
                                                               flagship_id=relation_dict['flagshipid'],
                                                               is_exchange_goods=is_exchange_goods,
                                                               num=1,
                                                               customer_id=customer_id,
                                                               spare='主件',
                                                               deal_with_information_id=deal_with_information_id)
                        is_flag = False
                    else:
                        product_relation_obj = ProductRelation(number=itme['serial'],
                                                               good_id=itme['product_id'],
                                                               order_number=customer_dict['number'],
                                                               warehouse_type_id=WarehouseType.back_factory_warehouse,
                                                               flagship_id=relation_dict['flagshipid'],
                                                               is_exchange_goods=is_exchange_goods,
                                                               num=1,
                                                               customer_id=customer_id,
                                                               deal_with_information_id=deal_with_information_id)

                    warehouse_type = WarehouseType.back_factory_warehouse
                    self.controlsession.add(product_relation_obj)
                else:
                    warehouse_type = WarehouseType.inventory_warehouse
                    if is_flag1:
                        in_number = in_number + 1
                        newnumber = INnumber['number']
                        IN_in_out_warehouse_obj = InOutWarehouse(number=newnumber,
                                                                 date=date_time,
                                                                 user=name,
                                                                 user_id=user_id,
                                                                 operate_type=OperateType.other_in,
                                                                 flagship_id=in_out_warehouse_dict['flagshipid'],
                                                                 in_out_number=in_out_len)

                        self.controlsession.add(IN_in_out_warehouse_obj)
                        self.controlsession.commit()
                        is_flag1 = False
                    if is_flag:
                        i_product_relation_obj = ProductRelation(number=itme['serial'],
                                                                 good_id=itme['product_id'],
                                                                 order_number=newnumber,
                                                                 warehouse_type_id=WarehouseType.inventory_warehouse,
                                                                 flagship_id=relation_dict['flagshipid'],
                                                                 is_exchange_goods=is_exchange_goods,
                                                                 num=1,
                                                                 spare='主件',
                                                                 customer_id=customer_id,
                                                                 deal_with_information_id=deal_with_information_id)
                        self.controlsession.add(i_product_relation_obj)
                        is_flag = False
                    else:
                        i_product_relation_obj = ProductRelation(number=itme['serial'],
                                                                 good_id=itme['product_id'],
                                                                 order_number=newnumber,
                                                                 warehouse_type_id=WarehouseType.inventory_warehouse,
                                                                 flagship_id=relation_dict['flagshipid'],
                                                                 is_exchange_goods=is_exchange_goods,
                                                                 num=1,
                                                                 customer_id=customer_id,
                                                                 deal_with_information_id=deal_with_information_id)




                        self.controlsession.add(i_product_relation_obj)

                getInventoryInfo = self.controlsession.query(Inventory).filter(Inventory.store_id == invoice_dict['flagshipid'],
                                                                               Inventory.good_id == itme['product_id'],
                                                                               Inventory.warehouse_type_id == warehouse_type
                                                                               ).first()
                if getInventoryInfo:
                    getInventoryInfo.inventory_amount=getInventoryInfo.inventory_amount+itme['pnumber']
                    self.controlsession.add(getInventoryInfo)
                else:
                    obj = Inventory(store_id=invoice_dict['flagshipid'],
                                    warehouse_type_id=warehouse_type,
                                    good_id=itme['product_id'],
                                    inventory_amount=itme['pnumber'])
                    self.controlsession.add(obj)
            out_rs = ''
            if len(other_info_list) > 0:
                out_number = in_out_obj.create_numberNo(relation_dict['flagshipid'],
                                                        OperateType.other_out)
                new_other_info_list = []

                for itme in other_info_list:
                    itme['is_exchange_goods'] = is_exchange_goods
                    itme['customer_id'] = customer_id
                    itme['deal_with_information_id'] = deal_with_information_id
                    itme['actual_amount']=(float(itme['actual_amount']))*COVERT_MONEY_TYPE_NUMBER
                    new_other_info_list.append(itme)

                return_info = {'user': name,
                               'number': out_number['number'],
                               'date': date_time,
                               'remark_info': other_info,
                               'all_amount': len(other_info_list),
                               'operate_type': OperateType.other_out,
                               'flagshipid': in_out_warehouse_dict['flagshipid'],
                               'warehouse_type_id': WarehouseType.inventory_warehouse,
                               'to_warehouse_type_id': WarehouseType.out_warehouse,
                               'good_list': new_other_info_list,
                               'actual_amount': len(other_info_list),
                               'is_exchange_goods': is_exchange_goods,
                               'customer_id': customer_id,
                               'deal_with_information_id': deal_with_information_id}

                out_rs = AutoCreateOrderInfoExp(return_info,self.controlsession)
            else:
                pass
            if out_rs:
                if out_rs['code'] == ServiceCode.success:
                    self.controlsession.commit()
                    result['out_number'] = out_rs['out_number']
                else:
                    raise Exception('出库失败')
            else:
                result['out_number'] = ''
                self.controlsession.commit()
            result['in_number'] = newnumber
            result['th_number'] = customer_dict['number']
            result['code'] = ServiceCode.success
            return result
        except IntegrityError as e:
            SystemLog.pub_warninglog(e)
            self.controlsession.rollback()
            if e.orig[0] == 1062:
                SystemLog.pub_warninglog("插入重复")
        except Exception,e:
            SystemLog.pub_warninglog(traceback.format_exc())
            self.controlsession.rollback()
            delCustomer = self.controlsession.query(CustomerInfo).filter(CustomerInfo.orderNo == number).first()
            delrelation = None
            DealWithInfomation_id = None
            if delCustomer is not None:
                self.controlsession.delete(delCustomer)

            if delCustomer is not None and isinstance(delCustomer, CustomerInfo):
                delrelation = self.controlsession.query(ProductRelation).filter(ProductRelation.customer_id == delCustomer.id).all()
                if delrelation:
                    for itme in delrelation:
                        DealWithInfomation_id = itme.deal_with_information_id
                        self.controlsession.delete(itme)

            if delrelation is not None and DealWithInfomation_id is not None:
                delDealWithInformation = self.controlsession.query(DealWithInfomation).filter(DealWithInfomation.id == DealWithInfomation_id).first()
                if delDealWithInformation is not None:
                    self.controlsession.delete(delDealWithInformation)

            delInOutWarehouse = self.controlsession.query(InOutWarehouse).filter(InOutWarehouse.number == number).first()
            if delInOutWarehouse is not None:
                self.controlsession.delete(delInOutWarehouse)

            if newnumber is not None and newnumber:
                del_in_first = self.controlsession.query(InOutWarehouse).filter(InOutWarehouse.number == newnumber).first()
                self.controlsession.delete(del_in_first)

            self.controlsession.commit()
            result['code'] = ServiceCode.service_exception
            return result

    def GetOrderInfo(self, category_id=None, product_id=None, serial=None, flagshipid=None):
        from data_mode.hola_flagship_store.mode.sale_mode.sale_order_detail import SaleOrderDetail
        saleOrder=self.controlsession.query(SaleOrderDetail).filter(and_(SaleOrderDetail.store_id == flagshipid,SaleOrderDetail.serialNo ==serial,SaleOrderDetail.name ==product_id ) ).all()
        saleOrder=[itme.to_json() for itme in saleOrder]

    def GetReturnProductInfo(self,categories_id=None):
            #通过类别ID查所有产品
            all_ca = ''
            try:
                productInfoObj=HolaWareHouse()
                all_ca=productInfoObj.get_category_product(categories_id=categories_id)
            except Exception,e:
                SystemLog.pub_warninglog(traceback.format_exc())
            return all_ca

    def GetOrderQuery(self,flagshipid_dict):
            # 订单查询接口
            try:
                flagshipid = flagshipid_dict['flagshipid']
                serial = flagshipid_dict['serial']
                product_name = flagshipid_dict['product_name']
                pl = flagshipid_dict['pl']
                category = flagshipid_dict['category']
                pagesize = flagshipid_dict['pagesize']
                work_number = flagshipid_dict['work_number']
                mixusercenterop = MixUserCenterOp()
                productInfoObj = HolaWareHouse()
                all_cate = productInfoObj.show_all_category()

                for itme in all_cate:
                    if int(category) == int(itme['id']):
                        categoryName = itme['name']
                # 查询单品
                condition = 'SaleOrder.orderNo == SaleOrderDetail.orderNo,' \
                            'CustomerInfo.orderNo == SaleOrder.orderNo,' \
                            'SaleOrderDetail.name == "%s",' \
                            'SaleOrderDetail.serialNo == "%s",' \
                            'SaleOrderDetail.store_id == %s' % (product_name, serial, flagshipid)

                if work_number:
                    condition = condition + ",SaleOrder.salesman == '%s'" % (work_number)
                else:
                    pass
                condition = 'and_('+condition+')'
                SaleOrderDetail_op_1 = self.controlsession.query(SaleOrder.orderNo,
                                                                 SaleOrder.salesman,
                                                                 SaleOrder.seltDate,
                                                                 SaleOrderDetail.name,
                                                                 SaleOrderDetail.serialNo,
                                                                 CustomerInfo.name,
                                                                 CustomerInfo.tel,
                                                                 SaleOrderDetail.salePrice,
                                                                 SaleOrderDetail.Rem1
                                                                 ).filter(eval(condition)).all()

                p_list = self.ReturnGroup(SaleOrderDetail_op_1,mixusercenterop)
                # print '单品SaleOrderDetail_op_1:', SaleOrderDetail_op_1

                order_list_1 = []
                for itme in p_list:
                    order_list_1.append(itme['orderNo'])
                # print 'order_list_1结果：',order_list_1
                # 查询套餐
                package_condition = 'SaleOrder.orderNo == SetProductRecord.orderNo,' \
                                    'SetProductRecord.orderNo == SetRecordInfo.orderNo,' \
                                    'SetRecordInfo.set_meal_id == SetProductRecord.set_meal_id,' \
                                    ' CustomerInfo.orderNo == SaleOrder.orderNo,' \
                                    'SetRecordInfo.serialNo == "%s",' \
                                    'SaleOrder.store_id == %d,' \
                                    'SetRecordInfo.name == "%s"' % (serial, flagshipid, product_name)


                if work_number:
                    package_condition = package_condition+ ",SaleOrder.salesman == '%s'" % (work_number)
                else:
                    if len(order_list_1) > 0:
                        #package_condition = package_condition+ ",SetProductRecord.orderNo.in_(tuple(%s))" % (order_list_1)
                        pass
                    else:
                        pass
                package_condition = 'and_('+package_condition+')'
                SetProductRecord_op_1 = self.controlsession.query(SaleOrder.orderNo,
                                                                  SaleOrder.salesman,
                                                                  SaleOrder.seltDate,
                                                                  SetRecordInfo.name,
                                                                  SetRecordInfo.serialNo,
                                                                  CustomerInfo.name,
                                                                  CustomerInfo.tel,
                                                                  SetRecordInfo.price,
                                                                  SetRecordInfo.Rem2,
                                                                  SetProductRecord.Rem1).filter(eval(package_condition)).all()

                p_list_1 = []

                if SetProductRecord_op_1:
                    p_list_1 = self.ReturnGroup(SetProductRecord_op_1, mixusercenterop, is_package = True)
                # print '套餐SetProductRecord_op_1:', SetProductRecord_op_1, package_condition
                p_all = p_list+p_list_1
                # print len(p_all),'p_all', p_all
                total = len(p_all)
                start = pl*pagesize
                end = pl*pagesize+pagesize
                if end > total:
                    end = total
                re_data = []
                for idx, val in enumerate(p_all):
                    if idx>=start and idx <end:
                        re_data.append(val)

                pro = FlagShipOp()
                dataList = pro.get_flagship_info_by_flagship_id(flagshipid)
                flagshipName = dataList['name']
                r_data = {'code': ServiceCode.success,
                          'total': total,
                          'data': re_data,
                          'network_spot': flagshipName,
                          'serialNo': serial,
                          'product_name': product_name,
                          'product_categroy': categoryName}
                return r_data
            except Exception,e:
                SystemLog.pub_warninglog(traceback.format_exc())
                r_data = {'code': ServiceCode.service_exception, 'msg': '查询失败'}
                return r_data

    def ReturnGroup(self,list, obj, is_package=False):
        if len(list) == 0:
            return list
        new_list = []
        for k, v in enumerate(list):
                j = {}
                for key,itme in enumerate(v):
                    if key == 0:
                        j['orderNo'] = v[key]
                    if key == 1:
                        j['salesman'] = obj.get_salesmen_name(v[key])
                    if key == 2:
                        j['seltDate'] = v[key]
                    if key == 3:
                        j['productName'] = v[key]
                    if key == 4:
                        j['serial'] = v[key]
                    if key == 5:
                        j['customer_name'] = v[key]
                    if key == 6:
                        j['customer_phone'] = v[key]
                    if key == 7:
                        j['order_money'] = (v[key])/COVERT_MONEY_TYPE_NUMBER
                    if key == 8:
                        j['product_categroy'] = v[key]
                    if is_package:
                        j['is_package'] = 1
                    else:
                        j['is_package'] = 0
                new_list.append(j)
        return new_list

    def GetOrderInfos(self,p_dict):
            flagshipid = p_dict['flagshipid']
            order_number = p_dict['order_number']
            pl = p_dict['pl']
            pagesize = p_dict['pagesize']
            productInfoObj = HolaWareHouse()

            SaleOrderDetail_op_1=self.controlsession.query(SaleOrder,SaleOrderDetail).filter(SaleOrder.orderNo == SaleOrderDetail.orderNo,
                                                                                             SaleOrder.orderNo == order_number,
                                                                                                 SaleOrderDetail.store_id == flagshipid,
                                                                                                 SaleOrderDetail.orderNo == order_number).all()

            # print 'SaleOrderDetail_op_1',len(SaleOrderDetail_op_1),SaleOrderDetail_op_1

            p_list=[]
            data_all=[]
            for itme in SaleOrderDetail_op_1:
                p_json={}
                for itme1 in itme:
                    v=itme1.to_json()
                    if v.has_key('salesman'):
                        p_json['salesman']=v['salesman']
                    if v.has_key('pCode'):
                        p_json['pCode']=v['pCode']
                    if v.has_key('pCode'):
                        p_id=productInfoObj.getProIdByGoodCode(v['pCode'])
                        price=productInfoObj.get_product_price_by_product_flagship(p_id,flagshipid)
                        p_json['order_money']=(v['price'])/COVERT_MONEY_TYPE_NUMBER
                        p_json['floor_price'] = price['floor_price']
                    if v.has_key('pCode'):
                        p_id=productInfoObj.getProIdByGoodCode(v['pCode'])
                        price=productInfoObj.get_product_info(p_id)
                        p_json['img']=price['img']
                    if v.has_key('pCode'):
                        pro_id=productInfoObj.getProIdByGoodCode(v['pCode'])
                        p_json['product_id']=pro_id
                    if v.has_key('name'):
                        p_json['name']=v['name']
                    if v.has_key('serialNo'):
                        p_json['serialNo']=v['serialNo']
                    if v.has_key('state'):
                        p_json['state'] = v['state']
                    else:
                        p_json['serialNo']=''
                    if v.has_key('Rem1') and v.has_key('pCode') :
                        p_json['product_categroy']=v['Rem1']
                    if v.has_key('salePrice'):
                        p_json['salePrice']=(v['salePrice'])/COVERT_MONEY_TYPE_NUMBER
                    p_json['is_package']=0
                    p_json['set_meal_id']=''
                    p_json['packageName']=''
                    p_json['orderNo']=v['orderNo']

                p_list.append(p_json)
            # print 'SaleOrderDetail_op_1',SaleOrderDetail_op_1
            # print 'len(p_list)',len(p_list),p_list
            order_list_1=[]
            # if len(p_list) == 0:
            #     #没有查到对应的数据
            #     return_data={'code':ServiceCode.service_exception}
            #     return return_data
            for itme in p_list:
                order_list_1.append(itme['orderNo'])

            try:
                if len(p_list) > 0:
                    SetProductRecord_op_1=self.controlsession.query(SetProductRecord,SaleOrder,SetRecordInfo).filter(SaleOrder.orderNo ==SetProductRecord.orderNo,SetProductRecord.orderNo ==SetRecordInfo.orderNo,
                                                                                                             SetRecordInfo.set_meal_id== SetProductRecord.set_meal_id,SaleOrder.store_id == flagshipid,
                                                                                                             and_(SetProductRecord.store_id == flagshipid,SetProductRecord.orderNo.in_(tuple(order_list_1)))
                                                                                  ).all()
                else:
                    SetProductRecord_op_1=self.controlsession.query(SetProductRecord,SaleOrder,SetRecordInfo).filter(SaleOrder.orderNo ==SetProductRecord.orderNo,SetProductRecord.orderNo ==SetRecordInfo.orderNo,
                                                                                                                     SetRecordInfo.set_meal_id== SetProductRecord.set_meal_id,
                                                                                                                     SetRecordInfo.orderNo == order_number,
                                                                                                                     SetRecordInfo.store_id == flagshipid,
                                                                                                                     SaleOrder.store_id == flagshipid
                                                                                                                     ).all()
            except Exception,e:
                SystemLog.pub_warninglog(traceback.format_exc())
                return_data={'code':ServiceCode.service_exception}
                raise Exception('没有查到对应的数据,SetProductRecord参数错误')
                return return_data
            p_list_1=[]
            if SetProductRecord_op_1:
                for itme in SetProductRecord_op_1:
                    p_json={}
                    for itme1 in itme:
                        v=itme1.to_json()
                        if v.has_key('set_meal_id') and v.has_key('salePrice') and v.has_key('Rem2'):
                            p_json['orderNum']=v['Rem2']
                        if v.has_key('salesman'):
                            p_json['salesman']=v['salesman']
                        if v.has_key('pCode'):
                            p_json['pCode']=v['pCode']
                        if v.has_key('serialNo'):
                            p_json['serialNo']=v['serialNo']
                        else:
                            p_json['serialNo']=''
                        if v.has_key('pCode'):
                            pro_id=productInfoObj.getProIdByGoodCode(v['pCode'])
                            p_json['product_id']=pro_id
                        if v.has_key('pCode'):
                            p_id=productInfoObj.getProIdByGoodCode(v['pCode'])
                            price=productInfoObj.get_product_price_by_product_flagship(p_id,flagshipid)
                            p_json['order_money']=(v['price'])/COVERT_MONEY_TYPE_NUMBER
                            p_json['floor_price'] = price['floor_price']
                        if v.has_key('pCode'):
                            p_id=productInfoObj.getProIdByGoodCode(v['pCode'])
                            price=productInfoObj.get_product_info(p_id)
                            p_json['img']=price['img']
                        if v.has_key('name'):
                            p_json['name']=v['name']
                        if v.has_key('Rem1') and v.has_key('salePrice') and v.has_key('set_meal_id'):
                            p_json['packageName']=v['Rem1']
                        if v.has_key('Rem2') and v.has_key('pCode') and v.has_key('serialNo'):
                            p_json['product_categroy']=v['Rem2']
                        if v.has_key('salePrice'):
                            p_json['salePrice']=(v['salePrice'])/COVERT_MONEY_TYPE_NUMBER
                        if v.has_key('set_meal_id'):
                            p_json['set_meal_id']=v['set_meal_id']

                        p_json['is_package']=1
                        p_json['orderNo']=v['orderNo']
                        p_json['state']= ''
                    p_list_1.append(p_json)
            else:
                pass

            pro=FlagShipOp()
            dataList=pro.get_flagship_info_by_flagship_id(flagshipid)
            flagshipName=dataList['name']
            re_data={}
            if len(p_list_1) > 0:
                # 有套餐情况
                p_all=p_list+p_list_1

                # 组合套餐
                conbination=[]
                conbination_id=[]
                for itme in p_all:
                    if itme['set_meal_id']:
                        conbination_id.append(itme['set_meal_id'])


                conbination_id=set(conbination_id)
                for itme in conbination_id:
                    a={}
                    n=0
                    for itme1 in p_all:
                        if itme1['set_meal_id'] == itme:
                            n=n+1
                            a['len']=n
                            a['name']=itme1['packageName']
                            a['orderNum']=itme1['orderNum']
                            a['set_meal_id'] = itme1['set_meal_id']

                        # a['len']=int(itme['len'])/int(itme['orderNum'])
                    conbination.append(a)
                for itme in conbination:
                    itme['len']=int(itme['len'])/int(itme['orderNum'])
                # print len(conbination),'conbination',conbination
                data_all=p_all
                re_data={'network_spot':flagshipName,'order_number':order_number,'list':p_all,'data':conbination}
                # return re_data
            else:
                data_all=p_list
                conbination=[]
                re_data={'network_spot':flagshipName,'order_number':order_number,'list':p_list}
                # print '结果',re_data
                # return re_data

            total=len(data_all)
            start=pl*pagesize
            end=pl*pagesize+pagesize
            if end > total:
                end=total
            re_data=[]
            for idx,val in enumerate(data_all):
                if idx>=start and idx <end:
                    re_data.append(val)


            return {'network_spot':flagshipName,'order_number':order_number,'list':re_data,'data':conbination,'total':total}

    def IsProductSerial(self,product_id):
        '''
        检测产品序列号
        :param product_id:
        :return:
        '''
        try:
            product_id=product_id
            rs=self.controlsession.query(ProductRelation).filter(ProductRelation.good_id == product_id).first()
            if rs:
                rs=rs.to_json()
                if rs['number']:
                    return 1
                else:
                    return ''
            else:
                return ''

        except Exception,e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return ''

    def GetStockInfo(self,flagshipid=None,pagesize=None,pl=0,product_id_list=[]):
        return_data={}
        try:
            # print 'id', product_id_list,type(product_id_list)
            # product_id_list=set(product_id_list)
            flagshipid=flagshipid
            start=pl*pagesize
            productInfoObj=HolaWareHouse()

            ptoduct_id_list=(product_id_list)

            all_product=productInfoObj.get_all_product_info()
            # print 'all_product-----------------------',type(all_product),len(all_product),all_product
            gift_flg_list=[]
            for itme in all_product:
                if itme['gift_flg']:
                    gift_flg_list.append(itme['id'])

            ret_list = list(set(gift_flg_list)^set(ptoduct_id_list))

            condition='Inventory.store_id == %s,Inventory.warehouse_type_id == %s' % (flagshipid,WarehouseType.inventory_warehouse)
            if len(product_id_list) == 0:
                condition = condition+',Inventory.good_id.notin_(%s)' % (gift_flg_list)
            else:
                condition = condition+',Inventory.good_id.in_(%s)' % (ptoduct_id_list)
            condition='and_('+condition+')'
            res=self.controlsession.query(Inventory).filter(eval(condition)).all()
            res=[itme.to_json() for itme in res]


            for itme in res:
                ptoduct_id_list.append(itme['good_id'])
            r=productInfoObj.get_products_by_idlist(ptoduct_id_list,flagshipid,start,pagesize)
            data_arr=[]
            return_data={}
            for itme1 in r[0]:
                j={}
                for itme in res:
                    if itme['good_id'] == itme1['id']:
                        j['inventory_num']=itme['inventory']
                        j['img']=itme1['img']
                        j['name']=itme1['name']
                        j['product_categroy']=itme1['category']['name']
                        j['pCode']=itme1['code']
                        j['barcode']=itme1['bar_code']
                        j['product_id']=itme1['id']
                        price_obj=productInfoObj.get_product_price_by_product_flagship(itme1['id'],flagshipid)
                        j['floor_price']=price_obj['floor_price']
                        j['order_money']=itme1['price']
                        if self.IsProductSerial(itme['good_id']):
                            j['is_serial']=1 #产品有序列号
                        else:
                            j['is_serial']=0 #没有序列号
                data_arr.append(j)
            return_data['total']=r[1]
            pro=FlagShipOp()
            dataList=pro.get_flagship_info_by_flagship_id(flagshipid)
            flagshipName=dataList['name']
            return_data['network_spot']=flagshipName
            return_data['list']=data_arr
            return return_data
        except Exception ,e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return return_data

    def GetOrderDetailedInfo(self,flagshipid=None,number=None):
        # 退换货明细
        try:
            flagshipid = flagshipid
            number = number
            res = self.controlsession.query(CustomerInfo).filter(CustomerInfo.store_id== flagshipid,CustomerInfo.orderNo == number).first()
            res = res.to_json()

            r=self.controlsession.query(ProductRelation).filter(ProductRelation.customer_id == res['id']).first()
            r=r.to_json()

            in_out_warehouse_info=self.controlsession.query(InOutWarehouse).filter(InOutWarehouse.number== number).first()
            in_out_warehouse_info=in_out_warehouse_info.to_json()

            customer_infos=self.controlsession.query(CustomerInfo).filter(CustomerInfo.id == res['id']).first()
            customer_infos=customer_infos.to_json()


            information_infos=self.controlsession.query(DealWithInfomation).filter(DealWithInfomation.id == r['deal_with_information_id']).first()
            information_infos=information_infos.to_json()

            relation_infos=self.controlsession.query(ProductRelation).filter(and_(ProductRelation.flagship_id == flagshipid,
                                                                                  ProductRelation.customer_id == customer_infos['id']),
                                                                             or_(ProductRelation.warehouse_type_id == WarehouseType.inventory_warehouse,
                                                                                 ProductRelation.warehouse_type_id == WarehouseType.back_factory_warehouse),
                                                                             ).all()

            relation_infos_other=self.controlsession.query(ProductRelation).filter(ProductRelation.customer_id == customer_infos['id'],
                                                                                 ProductRelation.warehouse_type_id == WarehouseType.out_warehouse,
                                                                                   ProductRelation.order_number.like('OU%')).all()
            # print 'relation_infos',relation_infos
            relation_infos=[ itme.to_json() for itme in relation_infos]
            relation_infos_other=[ itme.to_json() for itme in relation_infos_other]#information_infos['associated_order_number']

            sale_order_detial=self.controlsession.query(SaleOrderDetail).filter(SaleOrderDetail.orderNo == information_infos['associated_order_number']).all()
            sale_order_detial=[ itme.to_json() for itme in sale_order_detial]

            sale_order_rec=self.controlsession.query(SetProductRecord).filter(SetProductRecord.orderNo == information_infos['associated_order_number']).all()
            sale_order_rec=[ itme.to_json() for itme in sale_order_rec]

            sale_order_rec_info=self.controlsession.query(SetRecordInfo).filter(SetRecordInfo.orderNo == information_infos['associated_order_number']).all()
            sale_order_rec_info=[ itme.to_json() for itme in sale_order_rec_info]
            # print '套餐sale_order_rec', sale_order_rec

            tc=[]
            if sale_order_rec:
                for itme in sale_order_rec_info:
                    j = dict()
                    for itme1 in sale_order_rec:

                        if itme1['set_meal_id'] == itme['set_meal_id']:
                            j['orderNo'] = itme1['orderNo']
                            j['package_name'] = itme1['Rem1']
                            j['price'] = itme['price']
                            j['name'] = itme['name']
                            j['serial'] = itme['serialNo']
                    tc.append(j)

                    # print 'j=', j

            print '单号tc', tc, 'tc_len',len(tc)
            if sale_order_detial:
                d_all = sale_order_detial+tc
            else:
                d_all = tc
            print 'd_all',d_all
            from control_center.shop_manage.good_info_manage.control.mixOp import HolaWareHouse
            hwop=HolaWareHouse()
            # p_info=hwop.get_product_info()
            data_all = {}
            pro = FlagShipOp()
            dataList=pro.get_flagship_info_by_flagship_id(in_out_warehouse_info['flagship_id'])
            fname=dataList['name']
            pinfos=hwop.get_product_info(r['good_id'])
            d_dict=eval(information_infos['flg_set'])
            data_all['number']=in_out_warehouse_info['number']
            if customer_infos['buy_prov']:
                address=customer_infos['buy_prov']+','+customer_infos['buy_city']+','+customer_infos['buy_addr']
            else:
                address=customer_infos['buy_addr']
            #.strftime('%Y-%m-%d %H:%M:%S')
            # print "in_out_warehouse_info['date']类型",type(in_out_warehouse_info['date']),'--',in_out_warehouse_info['date']
            data_all['date']=(in_out_warehouse_info['date'])
            data_all['create_name']=in_out_warehouse_info['user']
            data_all['network_spot']=fname
            data_all['customerName']=customer_infos['name']
            data_all['customerPhone']=customer_infos['tel']
            data_all['customerEmail']=customer_infos['email']
            data_all['customerAddress']=address
            data_all['product_id']=r['good_id']
            data_all['treatment_type']= u'现场换货' if r['is_exchange_goods'] else u'现场退货'
            # data_all['r_actual_amount']=r['actual_amount']
            data_all['product_name']=pinfos['product_name']
            data_all['category_name']=pinfos['category_name']
            data_all['serial']=r['number']
            data_all['invoice'] =information_infos['invoice']
            data_all['associated_order_number'] =information_infos['associated_order_number']
            data_all['buy_machine_tiem']=(information_infos['buy_machine_tiem']).strftime('%Y-%m-%d %H:%M:%S')
            data_all['is_shop_voucher']=d_dict['is_shop_voucher']
            data_all['other_info']=in_out_warehouse_info['remark_info']
            data_all['is_exchange_goods']=r['is_exchange_goods']
            data_all['problem_describe']=information_infos['problem_describe']
            data_all['deal_type']=information_infos['deal_type']
            data_all['actual_amount']=(information_infos['actual_amount'])/COVERT_MONEY_TYPE_NUMBER
            data_all['quote']=(information_infos['quote'])/COVERT_MONEY_TYPE_NUMBER
            data_all['rem']=information_infos['rem']
            treatment_list = []
            other_info_list = []


            for itme in relation_infos:
                j={}
                j['serial']=itme['number']
                j['product_id']=itme['good_id']
                j['remarks']=itme['product_rem']

                pname=hwop.get_product_info(itme['good_id'])
                if len(d_all) > 0:
                    for itme1 in d_all:
                        t_name = ''
                        if str(itme1['serial']) == str(itme['number']):
                            if itme1.has_key('package_name'):
                                j['package_name'] = itme1['package_name']
                                t_name = itme1['package_name']
                            else:
                                j['package_name'] = itme1['package_name']
                            j['p_price'] = (itme1['price'])/COVERT_MONEY_TYPE_NUMBER
                            print "itme1['package_name']报名", pname['product_name'], itme['number'], itme1
                else:
                    j['package_name'] = ''
                    j['p_price'] = ''
                print '------------', t_name
                j['barcode']=pname['barcode']
                j['product_categroy'] = pname['category_name']
                j['product_name'] = pname['product_name']
                j['product_price'] = pname['price']
                if itme['warehouse_type_id'] == WarehouseType.back_factory_warehouse:
                    j['is_to_factory'] = 1
                elif itme['warehouse_type_id'] == WarehouseType.inventory_warehouse:
                    j['is_to_factory'] = 0
                treatment_list.append(j)
            if relation_infos_other:
                for itme in relation_infos_other:
                    j = {}
                    j['serial'] = itme['number']
                    j['product_id'] = itme['good_id']
                    if itme['actual_amount'] is not None:
                        j['actual_amount']=(itme['actual_amount'])/COVERT_MONEY_TYPE_NUMBER
                    else:
                        j['actual_amount']=itme['actual_amount']
                    other_name = hwop.get_product_info(itme['good_id'])
                    j['price'] = (other_name['price'])
                    j['product_name'] = other_name['product_name']
                    j['category_name'] = other_name['category_name']
                    j['barcode'] = other_name['barcode']
                    other_info_list.append(j)
            data_all['treatment_list']=treatment_list
            data_all['other_info_list']=other_info_list

            # print '结果：',treatment_list
            return data_all
        except Exception,e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return ''
    def UpdateOrderInfo(self,params_dict):
        '''
        修改订单信息
        :param flagshipid:
        :param number:
        :return:
        '''
        result={}
        try:

            # print 'params_dict',params_dict
            flagship_id = params_dict['flagshipid']
            number = params_dict['number']
            customerName=params_dict['customerName']
            customerPhone=params_dict['customerPhone']
            customerEmail=params_dict['customerEmail']
            customerAdd=params_dict['customerAddress']
            is_shop_voucher=params_dict['number']
            flg_set=str({'is_shop_voucher':is_shop_voucher})
            problem_describe=params_dict['problem_describe']
            other_info=params_dict['other_info']
            quote=params_dict['quote']
            actual_amount=params_dict['actual_amount']
            rem = params_dict['rem']

            customer_infos=self.controlsession.query(CustomerInfo).filter(CustomerInfo.orderNo == number,CustomerInfo.store_id == flagship_id).first()
            # customer_infos=customer_infos.to_json()

            relation_infos=self.controlsession.query(ProductRelation).filter(ProductRelation.customer_id == customer_infos.id,ProductRelation.flagship_id == flagship_id).first()
            relation_infos=relation_infos.to_json()

            Infomation_infos=self.controlsession.query(DealWithInfomation).filter(DealWithInfomation.id == relation_infos['deal_with_information_id']).first()
            # Infomation_infos=Infomation_infos.to_json()

            in_out_info=self.controlsession.query(InOutWarehouse).filter(InOutWarehouse.number == number).first()
            # in_out_info=in_out_info.to_json()

            if not customer_infos or not Infomation_infos or not in_out_info:
                return ''
            # print 'customer_infos',customer_infos
            if customerAdd:
                address_list = customerAdd.split(',')
                buy_prov = address_list[0]
                buy_city = address_list[1]
                buy_addr = address_list[2]
            else:
                buy_prov = ''
                buy_city = ''
                buy_addr = ''
            customer_infos.name = customerName
            customer_infos.tel=customerPhone
            customer_infos.email=customerEmail
            customer_infos.buy_prov=buy_prov
            customer_infos.buy_city=buy_city
            customer_infos.buy_addr=buy_addr
            self.controlsession.add(customer_infos)

            Infomation_infos.problem_describe=problem_describe
            Infomation_infos.quote=float(quote)*COVERT_MONEY_TYPE_NUMBER
            Infomation_infos.actual_amount=float(actual_amount)*COVERT_MONEY_TYPE_NUMBER
            Infomation_infos.flg_set=flg_set
            Infomation_infos.rem=rem
            self.controlsession.add(Infomation_infos)

            in_out_info.remark_info=other_info
            self.controlsession.add(in_out_info)

            self.controlsession.commit()

            return ServiceCode.success
        except Exception,e:
            SystemLog.pub_warninglog(traceback.format_exc())
            self.controlsession.rollback()
            return ''
    def CheckSn(self,flagshipid,productid,sn):
        '''
        检测序列号
        :param flagshipid:
        :param productid:
        :param sn:
        :return:
        '''
        try:
            from control_center.flagship_manage.warehouse_manage.control.ship_in_warehouse_op import ShipInwarehouse
            ShipInwarehouseOp=ShipInwarehouse()
            rs=ShipInwarehouseOp.GetSnCode(sn,flagshipid,productid)
            return rs
        except Exception , e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return ''
    def GetPackageInfo(self,package_number,order_no):
        try:
            infos=self.controlsession.query(SetRecordInfo).order_by().filter(SetRecordInfo.set_meal_id == package_number,SetRecordInfo.orderNo == order_no).all()
            if infos:
                infos=[ itme.to_json() for itme in infos]

                if infos:
                    return infos
                else:
                    return ''
            else:
                return ''

        except Exception,e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return ''
    def GetPrintTick(self,flagship_id,number):

        try:
            productInfoObj=HolaWareHouse()
            customer_obj = self.controlsession.query(CustomerInfo).filter(CustomerInfo.store_id == flagship_id,
                                                                             CustomerInfo.orderNo == number
                                                                             ).first()
            if not customer_obj:
                return ''

            relation_obj = self.controlsession.query(ProductRelation).filter(ProductRelation.flagship_id == flagship_id,
                                                                             ProductRelation.customer_id == customer_obj.id
                                                                             ).all()
            relation_obj_1 = self.controlsession.query(ProductRelation).filter(ProductRelation.flagship_id == flagship_id,
                                                                               ProductRelation.customer_id == customer_obj.id,
                                                                               or_(ProductRelation.warehouse_type_id == WarehouseType.back_factory_warehouse,
                                                                                   ProductRelation.warehouse_type_id == WarehouseType.inventory_warehouse)
                                                                               ).all()
            not_serial = []

            old_serial_list = []
            relation_obj_1=[itme.to_json() for itme in relation_obj_1]
            for itme in relation_obj_1:
                old_serial_list.append(itme['number'])

            for itme in relation_obj_1:
                if itme['number'] is None or itme['number'] == '':
                    product_info=productInfoObj.get_product_info((itme['good_id']))
                    not_serial.append(product_info['product_name'])

            a = {}
            myset = set(not_serial)  #myset是另外一个列表，里面的内容是mylist里面的无重复 项
            for item in myset:
                # print("the %s has found %d" %(item,not_serial.count(item)))
                a[item] = not_serial.count(item)

            # print '没有序列号',not_serial,'--',relation_obj_1
            #a=Counter(not_serial)
            #a=dict(a)
            # print '统计',a,type(a),len(a)

            # for k,i in enumerate(a):
            #     print '111111===k',k,'v',i,'==',a[i]
            in_out_warehouse=self.controlsession.query(InOutWarehouse).filter(InOutWarehouse.number == number).first()
            in_out_warehouse=in_out_warehouse.to_json()
            information_id=''
            relation_obj = [itme.to_json() for itme in relation_obj]
            for itme in relation_obj:
                information_id = itme['deal_with_information_id']
            # print 'information_id',information_id
            # print 'ProductRelation.deal_with_information_id====',information_id
            exchange_goods_info = self.controlsession.query(ProductRelation).filter(ProductRelation.deal_with_information_id == information_id,
                                                                                    ProductRelation.warehouse_type_id == WarehouseType.out_warehouse
                                                                                    )
            if exchange_goods_info:
                exchange_goods_info = [itme.to_json() for itme in exchange_goods_info]
            else:
                pass

            associated_obj=self.controlsession.query(DealWithInfomation).filter(DealWithInfomation.id == information_id).first()
            associated_obj = associated_obj.to_json()
            exchange_goods_list = []
            product_name_list = []


            for itme in relation_obj:
                product_info=productInfoObj.get_product_info(int(itme['good_id']))
                product_name_list.append(product_info['product_name'])

            sale_info=self.controlsession.query(SaleOrderDetail).filter(SaleOrderDetail.orderNo == associated_obj['associated_order_number'],
                                                                           SaleOrderDetail.name.in_(tuple(product_name_list)),
                                                                            SaleOrderDetail.serialNo.in_(tuple(old_serial_list))
                                                                           ).all()
            sale_info=[itme.to_json() for itme in sale_info]

            package_info=self.controlsession.query(SetRecordInfo).filter(SetRecordInfo.orderNo == associated_obj['associated_order_number'],
                                                                         SetRecordInfo.name.in_(tuple(product_name_list)),
                                                                         SaleOrderDetail.serialNo.in_(tuple(old_serial_list))
                                                                         )
            package_info = [itme.to_json() for itme in package_info]

            old_order_info=sale_info+package_info
            # print '------',old_order_info

            old_list=[]

            for itme in old_order_info:
                j={}
                if itme.has_key('salePrice'):
                    j['price'] = (itme['salePrice'])/1000
                else:
                    j['price'] = (itme['price'])/1000
                    # print "itme['price']",itme['price'], 'type',type(itme['price'])
                if itme.has_key('state'):
                    j['state'] = itme['state']
                else:
                    j['state'] = ''
                j['product_name'] = itme['name']
                j['serial_number'] = itme['serialNo']
                old_list.append(j)


            have_serial = []
            new_not_serial = {}
            # print 'old_list=',old_list
            for itme in old_list:
                if itme['serial_number']:
                    have_serial.append(itme)
                else:
                    pname = itme['product_name']
                    data = new_not_serial.get(pname,{})
                    if not len(data):
                        data = itme
                        data['number'] = 1
                        new_not_serial[pname] = data
                    else:
                        data['number'] += 1
                        new_not_serial[pname] = data
            # print '-------'
            # print 'new_not_serial=',new_not_serial
            # print '有序列号',have_serial
            # print '没有序列号',new_not_serial
            # print '---end----'
            end_not_serial = []
            if len(new_not_serial) > 0:
                for key,itme in new_not_serial.items():
                    for k,v in enumerate(a):
                        # print("k==", k, "  v==", v, "  a[v]:", a[v])
                        # print("itme['product_name']:", itme['product_name'], "  key==", key)
                        if v == key and itme.get('number',0) >= a[v]:
                            for i in range(0,a[v]):
                                end_not_serial.append(itme)

            # print 'end_not_serial=',end_not_serial
            end_old_list = end_not_serial+have_serial
            Total_amount = 0
            if exchange_goods_info:
                for itme in exchange_goods_info:
                    j = {}
                    j['serial_number'] = itme['number']
                    product_info=productInfoObj.get_product_info(int(itme['good_id']))
                    # for itme1 in product_info:
                    j['product_name'] = product_info['product_name']
                    j['price'] = (product_info['price'])
                    # print "product_info['price']",product_info['price'], 'type',type(product_info['price'])
                    Total_amount = Total_amount+((product_info['price']))

                    exchange_goods_list.append(j)

            # print '单号=',associated_obj['associated_order_number'],'old_list====',len(old_list),'list=',old_list

            result = {'quote': (associated_obj['quote'])/1000,'actual_amount': (associated_obj['actual_amount'])/1000,'old_list': end_old_list,'new_list' :exchange_goods_list,
                      'work_name':in_out_warehouse['user'],'work_number':in_out_warehouse['user_id'],'date':datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
                      'th_number':number,'sale_number':associated_obj['associated_order_number'],'Total_amount': Total_amount,
                      'address':'广东深圳南山区海岸城1001号'
                      }
            # print 'result',result
            return result

        except Exception,e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return ''
    def CheckProductIsFlow(self,flagshipid,serial_list):
        try:
            shfop=ShareFunctionOp()
            rs=shfop.check_seriNo_is_exist(flagshipid,serial_list)
            return rs
        except Exception,e:
            SystemLog.pub_warninglog(traceback.format_exc())
            return ''

if __name__=='__main__':
    op = ReturnService()
    # s40
    # flagshipid_dict = {'flagshipid': 1,
    #                            'serial': '',
    #                            'product_name': '支架',
    #                            'pl': 0,
    #                            'pagesize': 10,
    #                            'category': 1,
    #                            'work_number': ''}
    # rs = op.GetOrderQuery(flagshipid_dict)
    # print '结果',rs

#/usr/bin/python
#-*- coding:utf-8 -*-

import time
import json
import datetime
from sqlalchemy import and_, or_, func
from sqlalchemy.exc import IntegrityError
from config.share.share_define import *
from config.service_config.returncode import ServiceCode
from public.exception.custom_exception import CodeError
from data_mode.hola_flagship_store.control_base.controlBase import ControlEngine
from data_mode.hola_flagship_store.mode.sale_mode.sale_order import SaleOrder
from data_mode.hola_flagship_store.mode.sale_mode.customer_info import CustomerInfo
from data_mode.hola_flagship_store.mode.sale_mode.sale_order_detail import SaleOrderDetail
from data_mode.hola_flagship_store.mode.sale_mode.set_record_info import SetRecordInfo
from data_mode.hola_flagship_store.mode.sale_mode.set_product_record import SetProductRecord
from data_mode.hola_flagship_store.mode.after_sale.deal_with_infomation import DealWithInfomation
from data_mode.hola_flagship_store.mode.warehouse_mode.warehouse_manage import InOutWarehouse, Inventory,\
     ProductRelation, OperateType, WarehouseType

from data_mode.user_center.control.mixOp import MixUserCenterOp
from data_mode.hola_warehouse.control.base_op import ProductBaseInfoOp
import traceback
from public.sale_share.share_function import *

class MaintenanceSingleOp(ControlEngine):
    '''新建维修单处理op'''

    def __init__(self):
        ControlEngine.__init__(self)

    def save_mainten_info(self, flagship_id, numberNo, accep_net, state_id,
                          cus_info_dict, pro_info_dict, deal_info_dict,
                          user_id, main_info_dict, take_mach_dict):
        '''
        FUNCTION : 保存维修单处理
        :param flagship_id:
        :param numberNo:
        :param accep_net:
        :param state_id:
        :param cus_info_dict:
        :param pro_info_dict:
        :param deal_info_dict:
        :param main_info_dict:
        :param take_mach_dict:
        :return:
        # 处理方式：
            # 自行维修和其他维修 -- 不返厂 -- 只有受理和已完成的过程 -- 取机信息必填
            # 代客维修和返厂维修 -- 返厂

            # 维修单进度：
            # 受理状态-填写-客户信息，产品信息，处理信息
            # 待处理状态 -填写- 维修信息
            # 待取机状态 -填写- 取机信息
            # 已完成状态 - 完成
        '''
        try:
            print "------ enter save maininfo op --------"
            pro_base_op = ProductBaseInfoOp()  # 商品资料操作基础op
            share_op = ShareFunctionOp()       # 共享模块
            warehouse_id = None                # 处理状态
            total_amount = 1                   # 维修或者退换货入库记录数量
            mix_user_op = MixUserCenterOp()
            userId = mix_user_op.get_salesmen_uid(user_id)
            treatment_man = mix_user_op.get_salesmen_name(user_id)
            good_info_list = []
            good_id_list = []

            print "------ enter save maininfo --------"
            if state_id == TO_ACCEPT:
                print '*' * 40
                print "---受理状态---"
                print '*' * 40
                # 录入客户信息
                if cus_info_dict is None or not isinstance(cus_info_dict, dict):
                    raise TypeError("cus_info_dict must be dict.")

                c_name = test_if_None(cus_info_dict, 'name')    #cus_info_dict.get('name', None)
                c_tel = test_if_None(cus_info_dict, 'tel')      #cus_info_dict.get('tel', None)
                c_qq = test_if_None(cus_info_dict, 'qq')        #cus_info_dict.get('qq', None)
                c_email = test_if_None(cus_info_dict, 'email')  #cus_info_dict.get('email', None)
                c_prov = test_if_None(cus_info_dict, 'prov')    #cus_info_dict.get('prov', None)
                c_city = test_if_None(cus_info_dict, 'city')    #cus_info_dict.get('city', None)
                c_addr = test_if_None(cus_info_dict, 'addr')    #cus_info_dict.get('addr', None)
                c_rs = CustomerInfo(
                    store_id=flagship_id,
                    orderNo=numberNo,
                    name=c_name,
                    email=(
                        c_email if c_email else c_qq),
                    buy_prov=c_prov,
                    buy_city=c_city,
                    buy_addr=c_addr,
                    tel=c_tel)
                self.controlsession.add(c_rs)
                self.controlsession.commit()  # 先提交 ，后续需要使用
                print "---插入用户成功---"

                # 维修商品入库状态记录
                print '*' * 40
                print "---维修商品入库状态记录---"
                print '*' * 40
                if pro_info_dict is not None:
                    categroy_id = test_if_None(pro_info_dict, 'categroy_id')# 商品种类
                    pro_name = test_if_None(pro_info_dict, 'pro_name')      # 商品名称
                    p_serNo = test_if_None(pro_info_dict, 'p_serNo')        # 商品序列号
                    if p_serNo is not None:
                        check_rs = share_op.check_seriNo_is_exist(flagship_id, p_serNo)         # 检查序列号是否存在
                        if check_rs == 'False':
                            raise CodeError(ServiceCode.GoodsCannotThandWx, msg=u"此序列号产品不满足退换和维修")

                    print "pro_info_dict  ",pro_info_dict
                    ass_orderNo = test_if_None(pro_info_dict, 'ass_orderNo')  # 关联销售单号
                    buy_time = test_if_None(pro_info_dict, 'buy_time')  # 购机时间
                    invo_No = test_if_None(pro_info_dict, 'invo_No')   # 发票单号
                    s_price = test_if_None(pro_info_dict, 's_price')  # 单品价格
                    if s_price is None:
                        s_price = 0
                    s_space = test_if_None(pro_info_dict, 's_space')  # 备注
                    s_code = test_if_None(pro_info_dict, 's_code')  # 单品条形码
                    acc_pro_list = test_if_None(pro_info_dict, 'acc_list')  # 配件列表

                    # 获取已经插入的客户信息id
                    get_cus_id = c_rs.id

                    # 录入处理方式信息
                    print '*' * 40
                    print "---录入处理方式信息---"
                    print '*' * 40
                    if deal_info_dict is None or not isinstance(deal_info_dict, dict):
                        raise ValueError("deal_info_dict must be dict.")

                    deal_type_id = int(deal_info_dict.get('deal_type', ""))

                    # 根据处理方式来觉得维修商品是否需要返厂,不返仓暂时放在售后仓
                    print '*' * 40
                    print "---根据处理方式来是否需要返厂---"
                    print '*' * 40
                    flg_set_dict = {}
                    if deal_type_id in NEED_RETURN_FACTORY_SET:
                        warehouse_id = WarehouseType.back_factory_warehouse
                    else:
                        #自行维修 / 其他维修
                        state_id = ACCEPT_COMPELET
                        warehouse_id = WarehouseType.aftersale_warehouse

                    print "---是否需要返厂---", warehouse_id
                    #维修信息
                    print "main_info_dict", main_info_dict
                    if test_if_None(main_info_dict, 'is_free') is not None:
                        flg_set_dict['is_free'] = str(main_info_dict['is_free'])
                    else:
                        flg_set_dict['is_free'] = None
                    if test_if_None(main_info_dict, 'sure_money') is not None:
                        flg_set_dict['sure_money'] = str(main_info_dict['sure_money'])
                    else:
                        flg_set_dict['sure_money'] = None
                    if test_if_None(main_info_dict, 'actual_amount') is not None:
                        actual_amount = int(float(main_info_dict['actual_amount']) * COVERT_MONEY_TYPE_NUMBER)
                    else:
                        actual_amount = 0
                    if test_if_None(main_info_dict, 'quote') is not None:
                        quote = int(float(main_info_dict['quote']) * COVERT_MONEY_TYPE_NUMBER)
                    else:
                        quote = 0
                    if test_if_None(main_info_dict, 'service_content') is not None:
                        service_content = str(main_info_dict['service_content'])
                    else:
                        service_content = None


                    #取机信息
                    if test_if_None(take_mach_dict, 'take_mechine_time') is not None :
                        take__time = take_mach_dict['take_mechine_time']
                        take_mechine_time = datetime.datetime.strptime(
                            take__time, "%Y-%m-%d")
                    else:
                        take_mechine_time = None
                    if test_if_None(take_mach_dict, 'customer') is not None:
                        take_customer = take_mach_dict.get('customer', None)
                    else:
                        take_customer = None


                    #处理信息
                    if test_if_None(deal_info_dict, 'warranty_type') is not None:
                        warranty_type = int(test_if_None(deal_info_dict, 'warranty_type')) # 保修类型
                    else:
                        warranty_type = None
                    flg_set = test_if_None(deal_info_dict, 'flg_set') # 是否多返
                    flg_set_dict['treatment'] = TREATMENT_KEEP[warranty_type]
                    flg_set_dict['is_multi_re'] = str(flg_set) if flg_set else None
                    flg_data = json.dumps(flg_set_dict)
                    describe = test_if_None(deal_info_dict, 'describe')  # 描述
                    space = test_if_None(deal_info_dict, 'space')        # 备注
                    deal_rs = DealWithInfomation(
                        deal_type=deal_type_id,
                        problem_describe=describe,
                        invoice=invo_No,
                        rem=space,
                        buy_machine_tiem=buy_time,
                        state=state_id,
                        flg_set=flg_data,
                        take_mechine_time=take_mechine_time,
                        associated_order_number=ass_orderNo,
                        customer=take_customer,
                        actual_amount=actual_amount,
                        service_content=service_content,
                        quote=quote
                    )
                    self.controlsession.add(deal_rs)
                    self.controlsession.commit()
                    print "---首次插入处理方式信息成功---"

                    get_deal_id = deal_rs.id

                    # 返厂入库
                    print '*' * 40
                    print "---返厂入库---"
                    print '*' * 40
                    send_site = accep_net
                    recv_site = None
                    logistics_company = None
                    in_out_number = total_amount + len(acc_pro_list)
                    operate_type = OperateType.to_factory
                    create_date = datetime.datetime.now()

                    ware_rs = InOutWarehouse(
                        number=numberNo,
                        date=create_date,
                        user=treatment_man,
                        send_site=send_site,
                        recv_site=recv_site,
                        user_id=userId,
                        logistics_company=logistics_company,
                        number_type=2,
                        in_out_number=in_out_number,
                        operate_type=operate_type,
                        flagship_id=flagship_id,
                        remark_info=ass_orderNo)
                    self.controlsession.add(ware_rs)
                    self.controlsession.commit()
                    print "------------插入库存记录成功InOutWarehouse--------------"

                    # 录入需要查询的维修商品（单个）
                    # print "s_code", s_code
                    # s_base_info = pro_base_op.getGoodInfoByproCode(s_code)
                    print "s_code", s_code
                    if s_code is None:
                        s_base_info = pro_base_op.getGoodInfoByproName(pro_name)
                    else:
                        s_base_info = pro_base_op.getGoodInfoByproCode(s_code)
                    s_good_id = int(s_base_info.get('id', None))
                    query_pro_rs = ProductRelation(
                        number=p_serNo,
                        good_id=s_good_id,
                        order_number=numberNo,
                        warehouse_type_id=warehouse_id,
                        spare=u"主件",
                        flagship_id=flagship_id,
                        actual_amount=int(float(s_price) * COVERT_MONEY_TYPE_NUMBER),
                        product_rem=s_space,
                        num=1,
                        customer_id=get_cus_id,
                        deal_with_information_id=get_deal_id)
                    self.controlsession.add(query_pro_rs)
                    good_id_list.append(s_good_id)
                    good_info_list.append([s_good_id, p_serNo])
                    print "---插入商品库存信息成功---"

                    # 配件商品入库状态记录
                    print '*' * 40
                    print "---配件商品入库状态记录---"
                    print '*' * 40
                    if acc_pro_list:
                        for pro_info in acc_pro_list:
                            # # a_categroy_id = pro_info.get('categroy_id', "")
                            a_categ_model = pro_info.get('categ_model', None)
                            # a_p_count = pro_info.get('p_count', 1)
                            # a_unit_price = pro_info.get('unit_price', None)
                            a_p_code = test_if_None(pro_info, 'p_code')
                            a_price = test_if_None(pro_info, 'price')
                            if a_price is None:
                                a_price = 0
                            a_serNo = test_if_None(pro_info, 'serNo')
                            if a_serNo is not None:
                                check_rs = share_op.check_seriNo_is_exist(flagship_id, a_serNo)  # 检查序列号是否存在
                                if check_rs == 'False':
                                    raise CodeError(ServiceCode.GoodsCannotThandWx, msg=u"此序列号产品不满足退换和维修")
                            a_space = test_if_None(pro_info, 'space')

                            if a_p_code is None:
                                p_base_info = pro_base_op.getGoodInfoByproName(a_categ_model)
                            else:
                                p_base_info = pro_base_op.getGoodInfoByproCode(a_p_code)
                            a_good_id = int(p_base_info['id']) if test_if_None(p_base_info, 'id') else None
                            pro_rs = ProductRelation(
                                number=a_serNo,
                                good_id=a_good_id,
                                order_number=numberNo,
                                warehouse_type_id=warehouse_id,
                                flagship_id=flagship_id,
                                actual_amount=int(float(a_price) * COVERT_MONEY_TYPE_NUMBER),
                                product_rem=a_space,
                                num=1,
                                customer_id=get_cus_id,
                                deal_with_information_id=get_deal_id)
                            self.controlsession.add(pro_rs)
                            # print "---插入配件商品入库状态记录成功---"
                            good_id_list.append(a_good_id)
                            good_info_list.append([a_good_id, a_serNo])

                    #增加返厂库存
                    if deal_type_id in NEED_RETURN_FACTORY_SET:
                        for good_id in good_id_list:
                            inventory = self.controlsession.query(Inventory).filter_by(
                                good_id=good_id,
                                store_id=flagship_id,
                                warehouse_type_id=WarehouseType.back_factory_warehouse).first()
                            if inventory is not None:
                                inventory.inventory_amount += 1
                            else:
                                inventory = Inventory(good_id=good_id, store_id=flagship_id,
                                                      inventory_amount=1,
                                                      warehouse_type_id=WarehouseType.back_factory_warehouse)
                            self.controlsession.add(inventory)

                        for good_info in good_info_list:
                            #修改有序列号维修之前num状态
                            goodId = good_info[0]
                            seriNo = good_info[1]
                            print 'seriNo:', seriNo, type(seriNo)
                            rs = self.controlsession.query(ProductRelation).filter(
                                ProductRelation.good_id == goodId,
                                ProductRelation.warehouse_type_id == WarehouseType.out_warehouse,
                                ProductRelation.number == seriNo,
                                ProductRelation.flagship_id == flagship_id,
                                ProductRelation.num == 1
                            ).first()

                            if rs is None and deal_type_id != INSTEAD_OF_CUSTOMER_TREATMENT :
                                raise CodeError(ServiceCode.inventory_is_not_enought, u'该商品已售出，库存为0')
                            elif isinstance(rs, ProductRelation) :
                                print "-------------rs:", rs.to_json()
                                print "find one data.............."
                                rs.num = 0
                                self.controlsession.add(rs)

                self.controlsession.commit()


                print "---受理状态数据记录成功---"

            elif state_id == WAIT_ACCEPT:
                print '*' * 40
                print "---待受理状态---"
                print '*' * 40
                if test_if_None(main_info_dict, 'is_free') is not None:
                    is_free = str(main_info_dict['is_free'])
                else:
                    is_free = None
                if test_if_None(main_info_dict, 'sure_money') is not None:
                    sure_money = str(main_info_dict['sure_money'])
                else:
                    sure_money = None
                if test_if_None(main_info_dict, 'actual_amount') is not None:
                    actual_amount = int(float(main_info_dict['actual_amount']) * COVERT_MONEY_TYPE_NUMBER)
                else:
                    actual_amount = 0
                if test_if_None(main_info_dict, 'quote') is not None:
                    quote = int(float(main_info_dict['quote']) * COVERT_MONEY_TYPE_NUMBER)
                else:
                    quote = 0
                if test_if_None(main_info_dict, 'service_content') is not None:
                    service_content = str(main_info_dict['service_content'])
                else:
                    service_content = None

                relat_rs = self.controlsession.query(
                    ProductRelation).filter_by(order_number=numberNo).first()
                if relat_rs is not None:
                    deal_id = relat_rs.deal_with_information_id
                    print "---待取机状态 -- 商品关系表 -- 更新记录成功---", deal_id
                else:
                    print "---待取机状态 -- 商品关系表 -- 更新记录失败---"
                    raise CodeError(
                        ServiceCode.MainRelationInfoNotExist,
                        msg="维修查询无相关的库存关系信息")

                main_rs = self.controlsession.query(
                    DealWithInfomation).filter_by(id=deal_id).first()
                if main_rs is not None:
                    flg_set = {}
                    flg_set['is_free'] = is_free
                    flg_set['sure_money'] = sure_money
                    flg_data = json.loads(main_rs.flg_set)
                    flg_data.update(flg_set)
                    flg_data = json.dumps(flg_data)
                    main_rs.flg_set = flg_data

                    main_rs.actual_amount = actual_amount
                    main_rs.quote = quote
                    main_rs.service_content = service_content
                    main_rs.state = WAIT_RECIVED_MACHIME
                    self.controlsession.add(main_rs)
                    self.controlsession.commit()
                    print "---待受理状态更新记录成功---"
                else:
                    print "---待受理状态更新记录失败---"
                    raise CodeError(
                        ServiceCode.MainDealInfoNotExist,
                        msg="维修查询无相关的处理信息")

            elif state_id == WAIT_RECIVED_MACHIME:
                if take_mach_dict is not None:
                    take_person = test_if_None(take_mach_dict, 'customer')
                    take_mechine_time = test_if_None(take_mach_dict, 'take_mechine_time')

                    relat_rs = self.controlsession.query(
                        ProductRelation).filter_by(order_number=numberNo).first()
                    if relat_rs is not None:
                        print "---待取机状态 -- 商品关系表 -- 更新记录成功---"
                        deal_id = relat_rs.deal_with_information_id
                    else:
                        print "---待取机状态 -- 商品关系表 -- 更新记录失败---"
                        raise CodeError(
                            ServiceCode.MainRelationInfoNotExist,
                            msg="维修查询无相关的库存关系信息")

                    deal_rs = self.controlsession.query(
                        DealWithInfomation).filter_by(id=deal_id).first()
                    if deal_rs is not None:
                        deal_rs.customer = take_person
                        deal_rs.take_mechine_time = take_mechine_time
                        deal_rs.state = ACCEPT_COMPELET

                        self.controlsession.add(deal_rs)

                    self.controlsession.commit()
                    print "---待取机状态更新记录成功---"

            elif state_id == ACCEPT_COMPELET:
                raise CodeError(
                    ServiceCode.MainStateIsCompelete,
                    msg="已完成状态，不做其他处理")
            else:
                raise CodeError(
                    ServiceCode.MainSaveInfoFailer,
                    msg="创建保存维修单号失败，维修进度不符合")

        except CodeError as e:
            print "CodeError"
            print traceback.format_exc()
            self.wx_delete(state_id, numberNo)
            raise

        except IntegrityError as e:
            print e
            print traceback.format_exc()
            self.controlsession.rollback()
            if e.orig[0] == 1062:
                print "插入重复"
                raise
            else:
                print 'IntegrityError no 1062'
                self.wx_delete(state_id, numberNo)
                raise
            print"IntegrityError"

        except Exception as e:
            print traceback.format_exc()
            print "Exception"
            self.wx_delete(state_id, numberNo)
            raise


    def wx_delete(self, state_id, numberNo):
        '''
        FUNCTION : 回滚函数，用于删除已经插入的数据
        :param state_id:
        :param numberNo:
        :return:
        '''
        # print "--- rollback info ---"
        # 如果回滚，需要先删除相应在处理过程中先提交的数据
        # print "state_id: numberNo", state_id, numberNo
        if state_id == TO_ACCEPT or state_id == ACCEPT_COMPELET:
            self.controlsession.rollback()

            # 删除插入的客户信息
            c_info = self.controlsession.query(
                CustomerInfo).filter_by(orderNo=numberNo).first()
            if c_info is not None:
                self.controlsession.delete(c_info)
                # print u'---删除客户信息---', numberNo, c_info.id

            from sqlalchemy import distinct
            deal_ids = self.controlsession.query(distinct(ProductRelation.deal_with_information_id)).filter_by(order_number=numberNo).all()

            if deal_ids is not None and len(deal_ids):
                deal_info = self.controlsession.query(DealWithInfomation).filter(
                    DealWithInfomation.id.in_(deal_ids)).first()
                if deal_info is not None:
                    self.controlsession.delete(deal_info)
                # print u'---删除客户信息---', numberNo, deal_info.id

            relations = self.controlsession.query(ProductRelation).filter_by(order_number=numberNo).all()
            for relation in relations:
                self.controlsession.delete(relations)
                # print u'---删除单据关联表(ProductRelation)', numberNo, relation.id

            in_out_warehouse = self.controlsession.query(InOutWarehouse).filter_by(number=numberNo).first()
            if in_out_warehouse is not None:
                self.controlsession.delete(in_out_warehouse)
                # print u'---删除单据信息(InOutWarehouse)', numberNo, in_out_warehouse.id
            self.controlsession.commit()
        else:
            self.controlsession.rollback()
        raise CodeError(ServiceCode.MainSaveInfoFailer, msg="维修保存信息失败")

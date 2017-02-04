#/usr/bin/python
#-*- coding:utf-8 -*-

'''
Created on 2016-10-20
Author : YuanRong
Function : 查询获得返厂的信息
'''

from sqlalchemy import and_, or_, func, cast, LargeBinary,distinct
from config.share.share_define import *
from public.exception.custom_exception import CodeError
from config.service_config.returncode import ServiceCode
from data_mode.hola_flagship_store.control_base.controlBase import ControlEngine
from data_mode.hola_flagship_store.mode.after_sale.deal_with_infomation import DealWithInfomation
from data_mode.hola_flagship_store.mode.warehouse_mode.warehouse_manage import InOutWarehouse, Inventory
from data_mode.hola_flagship_store.mode.sale_mode.customer_info import CustomerInfo
from data_mode.hola_flagship_store.mode.warehouse_mode.warehouse_manage import ProductRelation
from data_mode.hola_warehouse.control.base_op import ProductBaseInfoOp
from data_mode.hola_flagship_store.base_op.customer_base_op import FlagShipCustomerOp
from data_mode.hola_flagship_store.mode.sale_mode.customer_info import CustomerInfo
from data_mode.hola_flagship_store.base_op.product_repair_service import AfterSaleRepariOp
from public.sale_share.share_function import *

class QueryReturnFactoryInfoOp(ControlEngine):
    def __init__(self):
        ControlEngine.__init__(self)

    def query_info(self, flagship_id, f_type, f_content, r_reason, f_state, curPage, pageList):
        try:
            pro_base_op = ProductBaseInfoOp()
            custimer_op = FlagShipCustomerOp()

            curPage = curPage - 1
            if curPage < 0:
                curPage = 0
            if pageList > SALE_ORDER_DETAIL_SHOW_PER_PAGE:
                pageList = SALE_ORDER_DETAIL_SHOW_PER_PAGE
            start = curPage * pageList

            dataList = None
            rules = None
            if f_content and f_content!=0:  # is not None
                if f_type == 1: #产品序列号
                    rules = ProductRelation.number.like(str(f_content))
                elif f_type == 2: #客户姓名
                    rules = CustomerInfo.name.like(str(f_content))
                elif f_type == 3: #客户联系方式
                    rules = CustomerInfo.tel.like(str(f_content))
            if r_reason and r_reason!=0: #返厂理由
                r_data = self.controlsession.query(DealWithInfomation).filter(
                    DealWithInfomation.deal_type.like(r_reason)).all()
                temp = []
                for data in r_data:
                    data = data.to_json()
                    temp.append(data['id'])
                if rules is not None:
                    rules = and_(ProductRelation.deal_with_information_id.in_(temp),rules)#匹配所有满足处理方式的id
                else:
                    rules = and_(ProductRelation.deal_with_information_id.in_(temp))
            if f_state and f_state!=0: #返厂状态类型
                state = None
                if f_state == 1:
                    state = 104
                elif f_state == 2:
                    state = 106
                if rules is not None:
                    rules = and_(ProductRelation.warehouse_type_id.like(state), rules)
                else:
                    rules = and_(ProductRelation.warehouse_type_id.like(state))

            # 没有搜索条件，全局搜索
            if rules is None:
                rules = and_(ProductRelation.flagship_id.like(1),
                             or_(ProductRelation.order_number.like('%TH%'),
                                 ProductRelation.order_number.like('%WX%')),
                             or_(ProductRelation.warehouse_type_id.like(int(104)),
                                 ProductRelation.warehouse_type_id.like(int(106))))
            else:
                rules = and_(ProductRelation.flagship_id.like(1),
                             or_(ProductRelation.order_number.like('%TH%'),
                                 ProductRelation.order_number.like('%WX%')),
                             or_(ProductRelation.warehouse_type_id.like(int(104)),
                                 ProductRelation.warehouse_type_id.like(int(106))),
                             rules)
            dataList = self.controlsession.query(ProductRelation).filter(rules).limit(pageList).offset(curPage)

            DataList = []
            # 在订单数据表中搜索出对应店铺下满足条件的数据
            if dataList is not None:
                for t_data in dataList:
                    data = t_data.to_json()
                    if data['flagship_id'] == long(flagship_id):
                        tempDict = {}
                        r_data = self.controlsession.query(DealWithInfomation).filter(
                            DealWithInfomation.id.like(data['deal_with_information_id'])).first()
                        if r_data:
                            d_data = r_data.to_json()
                            tempDict['r_reason'] = d_data['deal_type']  #处理理由
                        else:
                            raise CodeError(ServiceCode.data_empty, msg="查询的处理理由id不存在")

                        tempDict['p_name'] = pro_base_op.getGoodNameById(data['good_id']) #商品名称
                        tempDict['p_sn'] = data['number'] #序列号
                        cus_info = custimer_op.getCustomerInfoById(data['customer_id'])
                        if cus_info:
                            tempDict['c_name'] = cus_info['name']  #客户姓名
                            tempDict['c_tel'] = cus_info['tel']  # 客户联系方式
                        else:
                            raise CodeError(ServiceCode.data_empty, msg="查询的客户信息id不存在")

                        tempDict['f_No'] = data['order_number'] #查询单号
                        tempDict['description'] = ""#r_data['rem']  #备注
                        tempDict['state'] = "123" #r_data['state']  #状态
                        warehouse_type_id = data['warehouse_type_id']
                        if warehouse_type_id == 106:
                            rules = and_(ProductRelation.customer_id.like(data['customer_id']),
                                         ProductRelation.num.like(1),
                                         ProductRelation.is_exchange_goods.like(True))
                            result = self.controlsession.query(ProductRelation).filter(rules).all()
                            tempDict['r_No'] = result['order_number']  #返厂单号
                        else:
                            tempDict['r_No'] = None

                        tempDict['cus_id'] = data['customer_id']
                        tempDict['deal_with_information_id'] = data['deal_with_information_id']
                        tempDict['product_id'] = data['good_id']
                        DataList.append(tempDict)

                # 搜索出相应条件满足的数据条数
                total = self.controlsession.query(func.count(ProductRelation.id)).filter(
                    rules, ProductRelation.flagship_id == flagship_id).scalar()
                if total >= 10:
                    count = 10
                else:
                    count = total
                return DataList, total, count

        except Exception as e:
            raise

    def get_number_of_repair(self, flagshipid,starttime,stoptime,searchtype,searchvalue,page,pagenum,dealtype=None):
        """
        :param flagshipid:      旗舰店id
        :param starttime:       搜索起始时间
        :param stoptime:        搜索结束时间
        :param searchtype:      搜索类型（1:返修单号、2:产品名称、3:客户姓名、4:产品序列号）
        :param searchvalue:     searchtype对应的搜索内容
        :param page:            分页的当前页数
        :param pagenum:         每页默认显示的记录数最大数
        :param dealtype:        处理方式(1:自行维修、2:返厂维修、3:代客送修、4:其它维修)
        :return: list(dict)    满足搜索条件的维修单信息列表
        """
        from control_center.shop_manage.good_info_manage.control.mixOp import HolaWareHouse

        holawarehouse_op = HolaWareHouse()
        repari_op = AfterSaleRepariOp()

        total = 0
        product_info_list = []
        all_repair_numbers = []
        sub_repair_numbers = []
        total = 0
        start = (page-1)*pagenum
        if starttime and stoptime:
            starttime +=" 00:00:00"
            stoptime +=" 23:59:59"
            all_repair_numbers = self.controlsession.query(InOutWarehouse.number).filter(InOutWarehouse.flagship_id==flagshipid,
                                                                                InOutWarehouse.date>=starttime,
                                                                                InOutWarehouse.date<=stoptime,
                                                                                InOutWarehouse.number.cast(LargeBinary).like('WX%')).order_by(InOutWarehouse.number).all()
        elif starttime or stoptime:
            raise ValueError(u"起始时间或结束时间有一个未设置")
        else:
            all_repair_numbers = self.controlsession.query(InOutWarehouse.number).filter(InOutWarehouse.flagship_id==flagshipid,
                                                                                InOutWarehouse.number.cast(LargeBinary).like('WX%')).order_by(InOutWarehouse.number).all()

        if dealtype is None:
            if searchvalue:
                if searchtype==1: #返修单号
                    rule = and_(InOutWarehouse.number.cast(LargeBinary)==searchvalue,
                                InOutWarehouse.flagship_id==flagshipid,
                                InOutWarehouse.number.cast(LargeBinary).like('WX%'))

                    sub_repair_numbers = self.controlsession.query(InOutWarehouse.number).filter(rule).order_by(InOutWarehouse.number).all()
                elif searchtype==2:#产品名称
                    # 从BaseProductUnit表中获取商品名称对应的商品id列表
                    product_id_list = holawarehouse_op.get_product_id_list_byname(searchvalue)
                    if product_id_list:
                        id_list = [product_id[0] for product_id in product_id_list]
                        #从ProductRelation表中搜选出满足rule条件的维修单号
                        rule = and_(ProductRelation.good_id.in_(id_list),
                                    ProductRelation.flagship_id==flagshipid,
                                    ProductRelation.order_number.like('WX%'))
                        sub_repair_numbers = self.controlsession.query(distinct(ProductRelation.order_number)).filter(rule).order_by(ProductRelation.order_number).all()
                    else:
                        sub_repair_numbers = []
                elif searchtype==3: #客户姓名
                    #根据客户姓名获取绑定的维修单号
                    rule = and_(CustomerInfo.name.cast(LargeBinary)==searchvalue,
                                CustomerInfo.store_id==flagshipid,
                                CustomerInfo.orderNo.cast(LargeBinary).like('WX%'))
                    sub_repair_numbers = self.controlsession.query(CustomerInfo.orderNo).filter(rule).order_by(CustomerInfo.orderNo).all()
                elif searchtype==4: #产品序列号
                    #搜出序列号为searchvalue的维修单号信息列表
                    rule = and_(ProductRelation.number.cast(LargeBinary)==searchvalue,
                                ProductRelation.flagship_id==flagshipid,
                                ProductRelation.order_number.cast(LargeBinary).like('WX%'))
                    sub_repair_numbers = self.controlsession.query(distinct(ProductRelation.order_number)).filter(rule).order_by(ProductRelation.order_number).all()
            else:
                rule = and_(InOutWarehouse.flagship_id==flagshipid,
                            InOutWarehouse.number.like('WX%'))
                sub_repair_numbers = self.controlsession.query(InOutWarehouse.number).filter(rule).order_by(InOutWarehouse.number).all()

        else:
            #从DealWithInfomation的deal_type获取相应的deal_with_information_id列表
            deal_info_id = self.controlsession.query(DealWithInfomation.id).filter(DealWithInfomation.deal_type==dealtype).order_by(DealWithInfomation.id).all()

            deal_info_id_list = [deal_id[0] for deal_id in deal_info_id]

            #从ProductRelation表中根据deal_with_information_id列表获取相应的维修单号
            if deal_info_id_list:
                if searchvalue:
                    if searchtype==1: #返修单号
                        rule = and_(ProductRelation.order_number.cast(LargeBinary)==searchvalue,
                                    ProductRelation.flagship_id==flagshipid,
                                    ProductRelation.deal_with_information_id.in_(deal_info_id_list),
                                    ProductRelation.order_number.cast(LargeBinary).like('WX%'))
                        sub_repair_numbers = self.controlsession.query(distinct(ProductRelation.order_number)).filter(rule).order_by(ProductRelation.order_number).all()
                    elif searchtype==2: #产品名称
                        # 从BaseProductUnit表中获取商品名称对应的商品id列表
                        product_id_list = holawarehouse_op.get_product_id_list_byname(searchvalue)
                        if product_id_list:
                            id_list = [product_id[0] for product_id in product_id_list]
                            #从ProductRelation表中搜选出满足rule条件的维修单号
                            rule = and_(ProductRelation.deal_with_information_id.in_(deal_info_id_list),
                                        ProductRelation.flagship_id==flagshipid,
                                        ProductRelation.order_number.cast(LargeBinary).like('WX%'),
                                        ProductRelation.good_id.in_(id_list))
                            sub_repair_numbers = self.controlsession.query(distinct(ProductRelation.order_number)).filter(rule).order_by(ProductRelation.order_number).all()
                        else:
                            sub_repair_numbers = []
                    elif searchtype==3: #客户姓名
                        rule = and_(CustomerInfo.name.cast(LargeBinary)==searchvalue,
                                    CustomerInfo.store_id==flagshipid,
                                    CustomerInfo.orderNo.cast(LargeBinary).like('WX%'))
                        customer_id_list = self.controlsession.query(CustomerInfo.id).filter(rule).order_by(CustomerInfo.orderNo).all()
                        if customer_id_list:
                            rule = and_(ProductRelation.customer_id.in_(customer_id_list),
                                        ProductRelation.flagship_id==flagshipid,
                                        ProductRelation.order_number.cast(LargeBinary).like('WX%'),
                                        ProductRelation.deal_with_information_id.in_(deal_info_id_list))
                            sub_repair_numbers = self.controlsession.query(distinct(ProductRelation.order_number)).filter(rule).order_by(ProductRelation.order_number).all()
                        else:
                            sub_repair_numbers = []
                    elif searchtype==4: #产品序列号
                        #搜出序列号为searchvalue的维修单号信息列表
                        rule = and_(ProductRelation.number.cast(LargeBinary)==searchvalue,
                                    ProductRelation.flagship_id==flagshipid,
                                    ProductRelation.order_number.cast(LargeBinary).like('WX%'),
                                    ProductRelation.deal_with_information_id.in_(deal_info_id_list))
                        sub_repair_numbers = self.controlsession.query(distinct(ProductRelation.order_number)).filter(rule).order_by(ProductRelation.order_number).all()
                else:
                    rule = and_(ProductRelation.deal_with_information_id.in_(deal_info_id_list),
                                ProductRelation.flagship_id==flagshipid,
                                ProductRelation.order_number.cast(LargeBinary).like('WX%'))
                    sub_repair_numbers = self.controlsession.query(distinct(ProductRelation.order_number)).filter(rule).order_by(ProductRelation.order_number).all()
            else:
                sub_repair_numbers = []
        #取维修单号的交集
        selected_repair = list(set(all_repair_numbers) & set(sub_repair_numbers))
        total = len(selected_repair)

        selected_number = selected_repair[start:start+pagenum]

        selected_repair_numbers = []
        if selected_number:
            selected_repair_numbers = [data[0] for data in selected_number]  #当前需要显示的返修单号

        for number in selected_repair_numbers:
            temp_dict = {}
            temp_dict['number'] = number

            deal_info, searialno, product_name ,progress= repari_op.get_product_info_byrepairnumber(number)
            temp_dict['dealvalue'] = deal_info
            temp_dict['name'] = product_name
            temp_dict['searialno'] = searialno
            temp_dict['progress'] = progress

            customer_dict = repari_op.get_customer_info_by_reparinumber(number)
            customer = customer_dict['name']
            tel = customer_dict['tel']

            temp_dict['customer'] = customer
            temp_dict['tel'] = tel

            date, user = repari_op.get_number_info_by_repairnumber(number)
            temp_dict['datetime'] = date
            temp_dict['worker'] = user

            product_info_list.append(temp_dict)

        return product_info_list,total

    def ConvertReturnFactory(self, good_dict):
        '''
        库存仓转返厂仓
        good_dict :
        :return:
        '''

        try:
            good_dict['user'] = session.get('user', None).get('name')
            good_dict['date'] = datetime.datetime.now()
            good_dict['send_site'] = "库存仓"
            good_dict['recv_site'] = "返厂仓"
            good_dict['logistics_name'] = None
            good_dict['remark_info'] = None
            good_dict['all_amount'] = 1
            good_dict['operate_type'] = OperateType.roll_over  #库存转出 类型 转入返厂仓

            deal_with_info_id = None
            if good_dict['deal_with_type']:
                deal_with_type = good_dict['deal_with_type']
                deal_with = self.controlsession.query(DealWithInfomation).order_by(DealWithInfomation.id.desc()).first()
                if deal_with is None:
                    deal_with_id = 0
                else:
                    deal_with_id = deal_with.id
                rs = DealWithInfomation(id=deal_with_id + 1, deal_type=deal_with_type, rem=u"库存转返厂仓")
                self.controlsession.add(rs)
                deal_with_info_id = rs.id

            op = ShareFunctionOp()

            number = op.create_numberNo(good_dict['flagshipid'], good_dict['operate_type'])
            good_dict['number'] = number['number']
            good_dict['good_list'][0]['deal_with_information_id'] = deal_with_info_id
            good_dict['good_list'][0]['spare'] = u"库存转返厂仓"
            data = AutoCreateOrderInfoExp(good_dict, self.controlsession, is_commit=True)


            if data['code'] == ServiceCode.success:
                return data
            else:
                CodeError(ServiceCode.convert_factory_error, msg="库存仓转返厂仓失败")
        except CodeError as e:
            print traceback.format_exc()
            self.controlsession.rollback()
        except Exception as e:
            print traceback.format_exc()
            self.controlsession.rollback()

class AfterServiceRollback(ControlEngine):
    """
    用于回滚售后的事务
    """
    def __init__(self):
        ControlEngine.__init__(self)

    def rollback_by_id(self, id, class_name):
        """
        用于手动回滚事务
        :param id: ID
        :return:
        """
        instance = self.controlsession.query(class_name).filter_by(id=id).first()
        if instance is not None:
            self.controlsession.delete(instance)
            self.controlsession.commit()
            return True
        else:
            return False

    def rollback_by_inventory(self, good_id, flagship_id, warehouse_type_id):
        """
        用于手动回滚仓库库存
        :param good_id: 商品ID
        :param flagship_id: 旗舰店ID
        :param warehouse_type_id: 库存类型ID
        :return:
        """
        inventory = self.controlsession.query(Inventory).filter_by(good_id=good_id, store_id=flagship_id,
                                                                   warehouse_type_id=warehouse_type_id)
        if inventory is not None and inventory.inventory_amount > 0:
            inventory.inventory_amount -= 1
            self.controlsession.add(inventory)
            self.controlsession.commit()
            return True
        else:
            return False

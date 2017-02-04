#!/usr/bin/python
#-*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : after_sale_operate.py
#    作者   : WangYi
#  电子邮箱 : ywang@jmgo.com
#    日期   : 2016/10/24 17:24
#
#     描述  : 售后业务模块
#
from sqlalchemy import func, and_, or_, distinct
from types import NoneType
from datetime import datetime
from data_mode.hola_flagship_store.control_base.controlBase import ControlEngine
from data_mode.hola_flagship_store.mode.after_sale.deal_with_infomation import DealWithInfomation
from data_mode.hola_flagship_store.mode.sale_mode.customer_info import CustomerInfo
from control_center.shop_manage.good_info_manage.control.mixOp import HolaWareHouse
from data_mode.hola_flagship_store.mode.warehouse_mode.warehouse_manage import InOutWarehouse, WarehouseType
from data_mode.hola_flagship_store.mode.warehouse_mode.warehouse_manage import ProductRelation
from config.share.share_define import DEAL_WITH_TYPE, ORDER_PROGRESS, WAREHOUSE_TYPE, FC_RECEIPTS, \
    TH_RECEIPTS, WX_RECEIPTS, SELECT_RETURN_FACTORY_SET, SCENE_EXCHANGE_GOOD, SCENE_RETURN_GOOD, \
    COVERT_DATA_TO_MONEY_NUMBER, MV_RETURN


class AfterSaleOp(ControlEngine):
    """
    售后业务混合模块。
    """
    # 搜索
    SEARCH_TYPE_ORDER_NUM = 1  # 搜索条件 - 订单号
    SEARCH_TYPE_GOODS_NAME = 2  # 搜索条件 - 商品名称
    SEARCH_TYPE_GOODS_SKU = 4  # 搜索条件 - 商品序列号
    SEARCH_TYPE_CUSTOMER_NAME = 3  # 搜索条件 - 客户名称
    SEARCH_TYPE_CUSTOMER_PHONE = 5  # 搜索条件 - 客户联系方式
    SEARCH_TYPE_ORDER_TYPE = 6  # 搜索条件 - 单据类型
    SEARCH_TYPE_ALL_TX_WX = 7  # 搜索条件 - 全部维修与退换

    SEARCH_TYPE = [SEARCH_TYPE_ORDER_NUM,
                   SEARCH_TYPE_CUSTOMER_NAME,
                   SEARCH_TYPE_CUSTOMER_PHONE,
                   SEARCH_TYPE_GOODS_NAME,
                   SEARCH_TYPE_GOODS_SKU,
                   SEARCH_TYPE_ORDER_TYPE,
                   SEARCH_TYPE_ALL_TX_WX]

    def __init__(self):
        ControlEngine.__init__(self)

    def get_after_sale_baseinfo(self, baseinfo, is_fc_select=None):
        """
        根据定单号获取售后基础信息。
        :param baseinfo: (订单号,处理信息ID,客户ID,商品ID, 商品序列号) or  [(订单号,处理信息ID,客户ID,商品ID，商品序列号),
        (订单号,处理信息ID,客户ID,商品ID，商品序列号)]
        :param is_fc_select: 是否是返厂查询。
        :return: dict
        """
        in_out_warehouse = None
        return_list = []

        hola = HolaWareHouse()
        for base in baseinfo:
            print("base:", base)
            warehouse = self.controlsession.query(InOutWarehouse).filter(
                InOutWarehouse.number == base[0]).first()
            deal_with_information = self.controlsession.query(
                DealWithInfomation).filter(DealWithInfomation.id == base[1]).first()
            customer = self.controlsession.query(CustomerInfo).filter(
                CustomerInfo.id == base[2]).first()

            temp = {}
            # 返修单号
            temp['number'] = warehouse.number
            if deal_with_information is not None:
                temp['dealvalue'] = DEAL_WITH_TYPE[
                    deal_with_information.deal_type]   # 处理方式
                if temp['dealvalue'] == u'返厂维修' or temp['dealvalue'] == u'返厂理由':
                    print("deal_with_information.deal_type:", deal_with_information.deal_type)

                temp['dealvalue_id'] = deal_with_information.deal_type
                if is_fc_select is not None:
                    if warehouse.spare == 'True':
                        temp['progress'] = u'已返厂'
                    elif warehouse.spare is None:
                        temp['progress'] = u'待返厂'
                    else:
                        temp['progress'] = u'未知状态'
                else:
                    if deal_with_information.state in ORDER_PROGRESS:
                        temp['progress'] = ORDER_PROGRESS[
                            deal_with_information.state]        # 进度
            else:
                temp['dealvalue'] = u''
                temp['progress'] = u''

            if customer is not None:
                # 客户姓名
                temp['customer'] = customer.name
                # 客户电话
                temp['tel'] = customer.tel
                # 有关联的返厂单号
                if warehouse.spare == 'True':
                    warehouse_temp = self.controlsession.execute(
                        "select distinct b.order_number from flagship_product_relation as a, flagship_product_relation as b  where a.order_number='%s' and a.customer_id = b.customer_id and b.warehouse_type_id!=a.warehouse_type_id and a.order_number != b.order_number" % (warehouse.number))
                    # 关联订单号
                    temp['assosciate_number'] = warehouse_temp.fetchone()[0]
            else:
                temp['customer'] = u''
                temp['tel'] = u''

            temp['name'] = hola.get_product_byid(
                base[3])['name']                 # 产品名称
            # 产品序列号
            temp['searialno'] = base[4]
            # 受理人
            temp['worker'] = warehouse.user
            temp['datetime'] = warehouse.date.strftime(
                '%Y-%m-%d %H:%M:%S')       # 受理时间
            # 备注
            temp['rem'] = warehouse.remark_info

            # 客户ID
            temp['a_c_id'] = customer.id if customer is not None else None
            # 处理信息ID
            temp['a_t_id'] = deal_with_information.id
            # 商品ID
            temp['a_p_id'] = base[3]

            return_list.append(temp)
        return return_list

    def search(
            self,
            flagship_id,
            swhere_type,
            swhere_value,
            page=None,
            page_num=None,
            **kw):
        """
        用于售后搜索功能，展示单号相关的信息。
        :param flagship_id: 旗舰店ID
        :param swhere_type: 搜索类型，可参考AfterSaleOp.SEARCH_TYPE当中的类型
        :param swhere_value: 值
        :param page: 页数（如不需要分页功能，则无需赋值）
        :param page_num: 每页显示内容（需与page同时赋值）
              swhere_value_list[0]  --  搜索值，精确匹配
              swhere_value_list[1]  -- 开始时间Datetime型
              swhere_value_list[2]  -- 结束时间Datetime型
        :param kw: 辅助筛选条件
        start_time -- datetime
        end_time -- datetime
        deal_type   --  int    处理方式
        deal_state  -- int   处理状态
        is_fc -- Boolean
        fc_select -- Boolean 用于查返厂的特殊条件。
        :return: list, int   结果list 和 符合条件的记录总数
        """
        # 参数检查
        if not isinstance(page, (int, NoneType)):
            raise ValueError("page must be int or NoneType ")
        elif not isinstance(page_num, (int, NoneType)):
            raise ValueError("page_num must be integer or NoneType")
        elif not isinstance(page, type(page_num)):
            raise TypeError("page's type must be equire page_num's type")

        # 局部变量声明
        return_list = []
        rule = and_()

        # 查询条件为客户名字或客户电话
        if swhere_type in (AfterSaleOp.SEARCH_TYPE_CUSTOMER_NAME,
                           AfterSaleOp.SEARCH_TYPE_CUSTOMER_PHONE):
            from data_mode.hola_flagship_store.base_op.customer_base_op import FlagShipCustomerOp
            fs_custop = FlagShipCustomerOp()
            if swhere_type == AfterSaleOp.SEARCH_TYPE_CUSTOMER_NAME:
                customer_info = fs_custop.search(name=swhere_value)
            else:
                customer_info = fs_custop.search(tel=swhere_value)

            print(customer_info)
            if not len(customer_info):
                return return_list, 0
            else:
                customer_id_list = [x['id'] for x in customer_info]
                rule.append(ProductRelation.customer_id.in_(customer_id_list))

        # 查询条件为商品名称
        elif swhere_type == AfterSaleOp.SEARCH_TYPE_GOODS_NAME:
            hola_op = HolaWareHouse()
            product = hola_op.get_product_byname(swhere_value)
            if product is None:
                return return_list, 0
            else:
                rule.append(ProductRelation.good_id == product['id'])

        # 查询条件为商品序列号
        elif swhere_type == AfterSaleOp.SEARCH_TYPE_GOODS_SKU:
            rule.append(ProductRelation.number == swhere_value)

        # 根据单据号查询in_out_warehouse。因为单据号是唯一值，所以直接返回
        elif swhere_type == AfterSaleOp.SEARCH_TYPE_ORDER_NUM:
            rule.append(InOutWarehouse.number == swhere_value)

        # 根据单据类型查询
        if swhere_type == AfterSaleOp.SEARCH_TYPE_ORDER_TYPE:
            rule.append(InOutWarehouse.number_type == swhere_value)
            child_child_rule_1 = and_(InOutWarehouse.number == CustomerInfo.orderNo,
                                      CustomerInfo.id == ProductRelation.customer_id)
            child_child_rule_2 = and_(InOutWarehouse.number == ProductRelation.order_number)
            child_rule = or_(child_child_rule_1, child_child_rule_2)
            rule.append(child_rule)
            # 返厂仓做特殊处理
            if swhere_value != FC_RECEIPTS:
                rule.append(ProductRelation.spare == u'主件')

        # 查询所有退换货和维修的单号
        elif kw.get('fc_select') is not None:
            rule.append(
                    InOutWarehouse.number_type.in_(
                            [TH_RECEIPTS, WX_RECEIPTS, MV_RETURN]))
            child_child_rule_1 = and_(InOutWarehouse.number == CustomerInfo.orderNo,
                                      CustomerInfo.id == ProductRelation.customer_id)
            child_child_rule_2 = and_(InOutWarehouse.number == ProductRelation.order_number)
            child_rule = or_(child_child_rule_1, child_child_rule_2)
            rule.append(child_rule)
            rule.append(ProductRelation.warehouse_type_id == WarehouseType.back_factory_warehouse)
        else:
            rule.append(
                    InOutWarehouse.number_type.in_(
                            [TH_RECEIPTS, WX_RECEIPTS]))
            rule.append(ProductRelation.spare == u'主件')
            rule.append(InOutWarehouse.number == CustomerInfo.orderNo)
            rule.append(CustomerInfo.id == ProductRelation.customer_id)

        # 时间跨度条件
        if kw.get(
                'start_time',
                None) is not None and kw.get(
                'end_time',
                None) is not None:
            rule.append(InOutWarehouse.date >= kw.get('start_time').strftime('%Y-%m-%d %H:%M:%S'))
            rule.append(InOutWarehouse.date <= kw.get('end_time').strftime('%Y-%m-%d %H:%M:%S'))

        # 处理方式
        if kw.get('deal_type', None) is not None:
            rule.append(DealWithInfomation.deal_type.in_(kw.get('deal_type')))
            rule.append(ProductRelation.deal_with_information_id == DealWithInfomation.id)

        # 处理状态
        if kw.get('deal_state', None) is not None:
            rule.append(DealWithInfomation.state == kw.get('deal_state'))

        rule.append(ProductRelation.flagship_id == flagship_id)

        # 是否返厂
        if kw.get('is_fc') is not None:
            if kw.get('is_fc'):
                rule.append(InOutWarehouse.spare == 'True')
            else:
                rule.append(InOutWarehouse.spare == None)

        print("#"*80)
        print("rule:%s" % rule)
        print("#"*80)
        query = [distinct(InOutWarehouse.number),
                 ProductRelation.deal_with_information_id,
                 ProductRelation.customer_id,
                 ProductRelation.good_id,
                 ProductRelation.number,
                 ProductRelation.id]
        if page is None:
            # 不使用分页
            order_number_list = self.controlsession.query(
                   *query).filter(rule).all()
            return_list = self.get_after_sale_baseinfo(order_number_list, is_fc_select=kw.get('fc_select'))
            total = len(return_list)
        else:
            # 使用分页
            start = (page-1) * page_num
            order_number_list = self.controlsession.query(
                    *query).filter(rule).limit(page_num).offset(start)
            total = self.controlsession.query(func.count(
                    distinct(ProductRelation.id))).filter(rule).scalar()
            return_list = self.get_after_sale_baseinfo(order_number_list, is_fc_select=kw.get('fc_select'))

        return return_list, total

    def get_all_records_by_warehouse(
            self,
            order_type,
            flagship_id,
            start,
            page_num,
            **kw):
        """
        用于售后查询单据信息
        :param order_type: 单据类型
        :param flagship_id: 旗舰店ID
        :param start: 数据偏移量
        :param page_num: 每页显示内容
        :param kw:
        start_time -- datetime
        end_time -- datetime
        is_need_spare -- Boolean 是否需要查询‘主件’
        :return: list
        """
        if not isinstance(order_type, int):
            raise TypeError(
                "order_type must be integer. %s" %
                type(order_type))
        elif WAREHOUSE_TYPE.get(order_type, None) is None:
            raise ValueError(
                "order_type value range %s. you input value:%d" %
                (WAREHOUSE_TYPE.keys(), order_type))

        rule = and_(InOutWarehouse.number_type == order_type,
                    InOutWarehouse.number == CustomerInfo.orderNo,
                    CustomerInfo.id == ProductRelation.customer_id,
                    ProductRelation.flagship_id == flagship_id)

        if kw.get('is_need_spare') is not None and not kw.get('is_need_spare'):
            pass
        else:
            rule.append(ProductRelation.spare == u'主件')

        if kw.get(
                'start_time',
                None) is not None and kw.get(
                'end_time',
                None) is not None:
            rule.append(InOutWarehouse.date >= kw.get('start_time'))
            rule.append(InOutWarehouse.date <= kw.get('end_time'))

        if kw.get('deal_type', None) is not None:
            rule.append(DealWithInfomation.deal_type == kw.get('deal_type'))
            rule.append(ProductRelation.deal_with_information_id == DealWithInfomation.id)

        baseinfo_list = self.controlsession.query(
            distinct(
                InOutWarehouse.number),
            ProductRelation.deal_with_information_id,
            ProductRelation.customer_id,
            ProductRelation.good_id,
            ProductRelation.number).filter(rule).limit(page_num).offset(start)
        total = self.controlsession.query(func.count(
            distinct(InOutWarehouse.number))).filter(rule).scalar()
        return_list = self.get_after_sale_baseinfo(baseinfo_list)
        return return_list, total

    def fc_search(
            self,
            flagship_id,
            is_fc=None,
            swhere_type=None,
            swhere_value=None,
            page=None,
            page_num=None,
            **kw):
        """
        用返厂查询
        :param flagship_id: 旗舰店ID
        :param is_fc: 是否已返厂？
               False  则待返厂
               True 已返厂
        :param swhere_type: 搜索类型，可参考AfterSaleOp.SEARCH_TYPE当中的类型
        :param swhere_value: 值
        :param page: 页数
        :param page_num: 每页显示内容
        :param kw:
            start_time -- datetime
            end_time -- datetime

        :return: list[dict], total
        """
        kw['is_fc'] = is_fc
        if kw.get('deal_type') is not None and not isinstance(kw.get('deal_type'), list):
            kw['deal_type'] = [kw.get('deal_type'),]
        elif kw.get('deal_type') is None:
            kw['deal_type'] = SELECT_RETURN_FACTORY_SET

        kw['fc_select'] = True
        swhere_type_1 = swhere_type if swhere_type is not None else AfterSaleOp.SEARCH_TYPE_ALL_TX_WX
        swhere_value_1 = swhere_value if swhere_value is not None else 0
        data, total = self.search(flagship_id,
                                  swhere_type_1,
                                  swhere_value_1,
                                  page,
                                  page_num, **kw)
        print("total:",total)
        return data, total


    def th_export_data(self, flagship_id, **kw):
        """
        导出的旗舰店退换货全部数据
        :param flagship_id: int 旗舰店ID
        :param kw:
        start_time -- datetime
        end_time -- datetime
        deal_type   --  int    处理方式
        :return: [list, list, ...]
        """
        # 参数检测
        if not isinstance(flagship_id, (int, long, str)):
            raise TypeError("flagship_id type error. type range:(int,long, str). %s" % type(flagship_id))

        # 目前需求只根据单据查询全部数据，所以忽略收入的swhere_type 和 swhere_value.
        # 如果需求需要加上搜索条件，需要修改此处，和search函数。


        select_field = """
        select distinct d.deal_type, a.number,
                        a.user, a.date, c.name, c.tel, d.associated_order_number,
                        d.buy_machine_tiem, d.invoice, e.totalPrice/%d, e.setPrice/%d ,
                        e.actPrice/%d, f.name,1, b.actual_amount/%d, d.quote/%d, d.actual_amount/%d
        """ % (COVERT_DATA_TO_MONEY_NUMBER,
               COVERT_DATA_TO_MONEY_NUMBER,
               COVERT_DATA_TO_MONEY_NUMBER,
               COVERT_DATA_TO_MONEY_NUMBER,
               COVERT_DATA_TO_MONEY_NUMBER,
               COVERT_DATA_TO_MONEY_NUMBER)
        from_table = """
        from flagship_in_out_warehouse as a,
                        flagship_product_relation as b,
                        customer_info as c,
                        deal_with_infomation as d,
                        sale_order as e,
                        hola_warehouse.base_product_unit as f
                        """
        where = """
        where a.number_type=%d and b.warehouse_type_id in (%s, %s) and (d.deal_type = %d or
               d.deal_type = %d)
               and a.number = c.orderNo and c.id = b.customer_id
               and b.deal_with_information_id = d.id
               and d.associated_order_number = e.orderNo
               and b.good_id = f.id
               and b.flagship_id = %d
               order by a.number;
               """ % (TH_RECEIPTS,
                      WarehouseType.back_factory_warehouse,
                      WarehouseType.inventory_warehouse,
                      SCENE_EXCHANGE_GOOD,
                      SCENE_RETURN_GOOD,
                      flagship_id)

        result = self.controlsession.execute(select_field + from_table + where)
        from control_center.flagship_manage.flagship_info_manage.control.flagship_op import FlagShipOp
        flagship_op = FlagShipOp()
        flagship = flagship_op.get_flagship_info_by_flagship_id(flagship_id)
        return_list = []
        i = 1
        for row in result.fetchall():
            base_row = [i, flagship['name']]
            base_row.append(DEAL_WITH_TYPE[row[0]])
            for col in row[1:]:
                base_row.append(col)
            i += 1
            return_list.append(base_row)

        return return_list


if __name__ == "__main__":
    test = AfterSaleOp()
    test.th_export_data(3)



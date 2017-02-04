#/usr/bin/python
#-*- coding:utf-8 -*-

'''
Created on 2016-10-11
Function : 测试销售模块进行开单时候，销售数据的统计测试
Author : Yuan Rong
'''

import traceback
from public.exception.custom_exception import CodeError
# from control_center.flagship_manage.sale_manage.control.mixOp import FlagshipOrderInfoOp
from control_center.flagship_manage.sale_manage.test_mixOp import testMixOp
from data_mode.hola_flagship_store.base_op.sale_order_base_op import FlagShipSaleOp
from data_mode.hola_warehouse.control.base_op import ProductBaseInfoOp
from data_mode.user_center.control.mixOp import MixUserCenterOp
from data_mode.user_center.model.admin_user import AdminUser

def test_statictis_data():
    '''
    FUNCTION : 测试销售统计数据
    :return:
    '''
    try:
        print "start"
        operator_statictis_op = testMixOp()
        pro_base_info_op = ProductBaseInfoOp()

        sale_op = FlagShipSaleOp()
        sale_order_info = sale_op.get_all_sale_info()

        for order_info in sale_order_info:
            order_info = order_info.to_json()
            orderNo = order_info.get('orderNo')
            saleman_id = order_info.get('salesman')
            user = MixUserCenterOp()
            temp = user.controlsession.query(AdminUser).filter(AdminUser.work_number == saleman_id).first()
            saleman_id = temp.id
            flagship_id = order_info.get('store_id')
            time = order_info.get('seltDate').replace('-', "")
            myday = int(time)
            ym = int(time[:-2])

            #销售单品统计
            pro_info = sale_op.get_sale_pro_info_by_orderNo(orderNo)
            for pro in pro_info:
                pro_data = pro.to_json()
                pro_sale_price = pro_data.get('salePrice')

                pro_base_info = pro_base_info_op.getGoodInfoByproCode(pro_data.get('pCode'))
                pro_id = pro_base_info.get('id')
                pro_categroy_id = pro_base_info['category']['id']


                #折叠统计销售商品数据
                operator_statictis_op.add_flagship_sale(saleman_id, pro_id, flagship_id, pro_sale_price, 0,
                                                        pro_categroy_id, myday, ym)

            #销售套餐统计
            set_info = sale_op.get_sale_set_info_by_orderNo(orderNo)
            for set in set_info:
                set_data = set.to_json()
                set_count = int(set_data.get("Rem2"))
                set_id = set_data.get('set_meal_id')
                set_sale_price = set_data.get('salePrice')

                #折叠统计套餐数据
                for i in xrange(set_count):
                    operator_statictis_op.add_flagship_sale_set(saleman_id, set_id, flagship_id, set_sale_price,
                                                                0, myday=myday, ym=ym)

            #销售套餐内商品数据统计
            set_detail_info = sale_op.get_sale_set_info_detail_info_by_orderNo(orderNo)
            for detail_info in set_detail_info:
                detail_data = detail_info.to_json()
                set_pro_count = int(detail_data.get("Rem3"))
                pro_base_info = pro_base_info_op.getGoodInfoByproCode(detail_data.get('pCode'))
                set_pro_id = pro_base_info.get('id')
                set_pro_categroy_id = pro_base_info['category']['id']
                set_pro_price = 0  #因为是套餐中的商品，做统计时无法精准到其价格，所以给0，并且这边只是做销售量的统计
                pro_type = 2  #标记商品是套餐内的商品，不是单品


                #折叠统计套餐内商品的数据
                for i in xrange(set_pro_count):
                    operator_statictis_op.add_flagship_sale_set_detail(set_pro_id, flagship_id, set_pro_price,
                                                                   set_pro_categroy_id, myday=myday, ym=ym, proType=pro_type)
    except CodeError as e:
        print traceback.format_exc()
        raise


if __name__ == '__main__':
    test_statictis_data()

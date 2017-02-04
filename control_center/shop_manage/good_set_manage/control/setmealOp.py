#!/usr/bin/python
#-*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : setmealOp.py
#    作者   : WangYi
#  电子邮箱 : ywang@jmgo.com
#    日期   : 2016/9/8 14:51
#
#     描述  : 套餐逻辑操作接口
#
import traceback
from datetime import datetime

from sqlalchemy import func, and_, or_
from sqlalchemy.exc import IntegrityError

from control_center.flagship_manage.flagship_info_manage.control.flagship_op import FlagShipOp
from data_mode.erp_base.control.uploadOp import UploadOp
from data_mode.erp_supply.base_op.operate_op import Operate_Op
from data_mode.hola_warehouse.control_base.controlBase import ControlEngine
from data_mode.hola_warehouse.model.base_product_unit import BaseProductUnit
from data_mode.hola_warehouse.model.base_setmeal_price import BaseSetmealPrice
from data_mode.hola_warehouse.model.base_setmeal_unit import BaseSetmealUnit
from data_mode.hola_warehouse.model.product_setmeal import ProductSetmeal


class SetMealOp(ControlEngine):
    """
    套餐接口类
    """

    def __init__(self):
        ControlEngine.__init__(self)

    def __get_associate_product(self, set_meal, flagship_id):
        """
        封装返回套餐的商品信息函数
        :param set_meal: <BaseSetmealUnit> 对象
        :param flagship: 旗舰店ID
        :return: dict
        'set_id':
		'name':
		'set_content':
			[{
				'p_name':str	#商品名称
				'p_code': str	#商品编码
				'p_barCode':str	#商品条形码
				'p_file'：str	#商品图片存放路径
				'p_setcount':	#该套餐类型该商品的数量
				'p_price':float	#该商品的价格
				'p_floor_price': float #商品最低价
				'p_type': str	#商品类别
				'p_type_id': int #商品类别id
			}]
		'price':	#套餐价格
        """
        if not isinstance(set_meal, BaseSetmealUnit):
            raise ValueError(
    "set_meal must be <BaseSetmealUnit> instance. not %s" %
     type(set_meal))

        json_data = {}
        json_data['set_id'] = set_meal.id
        json_data['name'] = set_meal.name
        # 套餐内的商品信息
        json_data['set_content'] = []
        for assoc in set_meal.goods:
            temp_dict = {}
            temp_dict['p_name'] = assoc.goods.name
            temp_dict['p_code'] = assoc.goods.code
            temp_dict['p_barCode'] = assoc.goods.bar_code
            temp_dict['p_file'] = assoc.goods.img
            for flagship_price in assoc.goods.flagships_price:
                if flagship_price.flagship_id == flagship_id:
                    temp_dict['p_price'] = flagship_price.price
                    temp_dict['p_floor_price'] = flagship_price.floor_price
            temp_dict['p_type'] = assoc.goods.category.name
            temp_dict['p_type_id'] = assoc.goods.category_id
            temp_dict['p_setcount'] = assoc.product_num
            temp_dict['p_is_gift'] = assoc.goods.gift_flg
            json_data['set_content'].append(temp_dict)

        for flagship_price in set_meal.flagship_price:
            if flagship_price.flagship_id == flagship_id:
                json_data['price'] = flagship_price.price
                json_data['floor_price'] = flagship_price.floor_price

        return json_data if 'price' in json_data else None

    def getallsetmeal(self, start=None, per_page=None, operate=None, **kw):
        """
        获取套餐信息
        :param start: 起始记录位置
        :param per_page: 每页显示数量
        :param operate: key与key之间的逻辑操作。0 -- '与'  1 -- '或'
        :param kw: 筛选条件字典。key为筛选的对象名，value为筛选值
                   需注意如果给多个key，且其value不为None。则会执行
                   默认逻辑操作。
        :return: list(dict)
        """
        if start is not None and per_page is not None:
            if kw or len(kw) != 0:
                rule = []
                reg = None
                # 获取键值对关系
                for key, value in kw.items():
                    if hasattr(BaseSetmealUnit, key) and value is not None:
                        rule.append(getattr(BaseSetmealUnit, key) == value)
                if operate is not None and operate == 1:
                    reg = and_(or_(*rule), BaseSetmealUnit.putaway)
                else:
                    reg = and_(and_(*rule), BaseSetmealUnit.putaway)
                setmeals = self.controlsession.query(BaseSetmealUnit).filter(
                    reg).order_by(BaseSetmealUnit.id).limit(per_page).offset(start)
                total = self.controlsession.query(func.count(
                    BaseSetmealUnit.id)).filter(reg).scalar()
            else:
                setmeals = self.controlsession.query(BaseSetmealUnit).filter(
                    BaseSetmealUnit.putaway).order_by(
                    BaseSetmealUnit.id).limit(
                    per_page).offset(start)
                total = self.controlsession.query(
                    func.count(
                        BaseSetmealUnit.id)).filter(
                    BaseSetmealUnit.putaway).scalar()
        else:
            setmeals = self.controlsession.query(
                BaseSetmealUnit).filter(
                    BaseSetmealUnit.putaway).order_by(
                    BaseSetmealUnit.id).all()
            total = self.controlsession.query(
                func.count(
                    BaseSetmealUnit.id)).filter(
                BaseSetmealUnit.putaway).scalar()
        if setmeals is not None:
            data = []
            seq = start if start is not None else 0
            for setmeal in setmeals:
                json_data = setmeal.to_json()
                seq += 1
                json_data['sequnence'] = seq
                data.append(json_data)
            return data, total
        else:
            return [], 0

    def get_setmeal_for_sale(self, flagship_id, stype, svalue, page, per_page):
        """
        根据旗舰店ID相关条件查询套餐信息，用于销售
        :param flagship_id: 旗舰店ID
        :param stype:搜索类型 (1：商品名称关键字 2：商品编码（完全匹配）3:套餐名称, 4:套餐ID)
        :param svalue:搜索内容，根据stype判断
        :param page:分页的当前页数
        :param per_page:每页显示的记录数
        :return: list(dict)
        """
        # 计算页面
        __type = (1, 2, 3)
        page = page - 1
        if page < 0:
            page = 0
        if per_page > 60:
            per_page = 60
        start = page * per_page

        sou = '%' + str(svalue) + '%'
        data = []
        total = 0
        if stype not in __type:
            raise ValueError("stype not in allow range.")
        elif stype == 1 or stype == 2:
            # 根据商品名称查询,返回结果
            if stype == 2:
                # 商品编码使用全匹配,不是非空
                sou = str(svalue)
                rule = and_(BaseProductUnit.code.like(sou),
                            BaseProductUnit.putaway == True,
                            ProductSetmeal.product_id == BaseProductUnit.id,
                            ProductSetmeal.set_meal_id == BaseSetmealUnit.id)
            else:
                rule = and_(BaseProductUnit.name.like(sou),
                            BaseProductUnit.putaway == True,
                            ProductSetmeal.product_id == BaseProductUnit.id,
                            ProductSetmeal.set_meal_id == BaseSetmealUnit.id)
            set_meals = self.controlsession.query(BaseSetmealUnit).filter(
                    rule).distinct().limit(per_page).offset(start)
            total = self.controlsession.query(func.count(BaseSetmealUnit.id.distinct())).filter(
                    rule).scalar()
            for set_meal in set_meals:
                json_data = self.__get_associate_product(set_meal, flagship_id)
                if json_data is None:
                    continue
                data.append(json_data)

        elif stype == 3:
            rule = and_( BaseSetmealUnit.name.like(sou), BaseSetmealUnit.putaway == True)
            set_meals = self.controlsession.query(BaseSetmealUnit).filter(
                    rule).limit(per_page).offset(start)
            total = self.controlsession.query(func.count(BaseSetmealUnit.id.distinct())).filter(
                    rule).scalar()
            for set_meal in set_meals:
                json_data = self.__get_associate_product(set_meal, flagship_id)
                if json_data is None:
                    continue
                data.append(json_data)
        return data, total

    def get_set_meal_detail(self, set_meal_id, flagship_id=None):
        """
        获取商品套餐详细信息
        :param set_meal_id: 商品套餐ID
        :param flagship_id: 旗舰店ID
        :return: tuple(code, msg or dict)
        code:
          0 --  data
          1 --  该套餐已被下架
        """
        set_meal = self.controlsession.query(BaseSetmealUnit).filter(
            BaseSetmealUnit.id == set_meal_id).first()
        if set_meal is None:
            return 0, {}
        elif not set_meal.putaway:
            return 1, u'该套餐已被下架'

        json_data = set_meal.to_json()
        # 移除不需要的内容.
        list_for_not_need = [
            'commission_amount',
            'award',
            'putaway',
            'goods_number']
        for content in list_for_not_need:
            json_data.pop(content)

        # 添加旗舰店信息标签
        json_data['flagship'] = []
        for flagship in set_meal.flagship_price:
            fg_op = FlagShipOp()
            fs = fg_op.get_flagship_info_by_flagship_id(flagship.flagship_id)
            json_data['flagship'].append({
                'id': flagship.flagship_id,
                'name': fs['name'],
                'price': flagship.price if flagship.price is not None else u'空',
                'floor_price': flagship.floor_price if flagship.floor_price is not None else u'空'
            })

        # 添加商品信息标签
        json_data['goods'] = []
        for assoc in set_meal.goods:
            temp_dict = {}
            temp_dict['id'] = assoc.goods.id
            temp_dict['name'] = assoc.goods.name
            temp_dict['code'] = assoc.goods.code
            temp_dict['category_id'] = assoc.goods.category_id
            temp_dict['category_name'] = assoc.goods.category.name
            if assoc.goods.price_max - assoc.goods.price_min < 0.01:
                price = "%.2f" % (assoc.goods.price_max)
            else:
                price = "%.2f~%.2f" % (
                    assoc.goods.price_min, assoc.goods.price_max)
            temp_dict['price'] = price
            temp_dict['number'] = assoc.product_num
            json_data['goods'].append(temp_dict)
        print("json_data", json_data)
        return 0, json_data

    def get_set_meal_flagship_price(self, set_meal_id):
        """
        获取套餐对应的旗舰店价格
        :param set_meal_id: 套餐ID
        :return: (code,list[dict] or msg)
        code:
        0 -- list[dict]
        1 --  该套餐已被下架
        """
        # print("get_set_meal_flagship_price: set_meal_id", set_meal_id)
        set_meal = self.controlsession.query(BaseSetmealUnit).filter(
            BaseSetmealUnit.id == set_meal_id).first()
        if set_meal is None:
            return 0, []
        elif not set_meal.putaway:
            return 1, u'该套餐已被下架'
        else:
            data = [price.to_json() for price in set_meal.flagship_price]
            return 0, data

    def add_set_meal(self, set_meal_para):
        """
        添加商品套餐
        :param set_meal_para: 商品套餐数据
        :return: True or False
        """
        try:
            # print("set_meal_para:",set_meal_para)
            t = self.controlsession.query(BaseSetmealUnit).order_by(BaseSetmealUnit.id.desc()).first()
            tid = t.id + 1 if t is not None else 1
            set_meal = BaseSetmealUnit(
                id=tid,
                name=set_meal_para['name'],
                description=set_meal_para['description'],
                img=set_meal_para['img'],
                unify_flg=set_meal_para['unify_flg'],
                floor_price_max=set_meal_para['floor_price_max'],
                floor_price_min=set_meal_para['floor_price_min'],
                price_max=set_meal_para['price_max'],
                price_min=set_meal_para['price_min'],
                putaway=True
            )

            for good in set_meal_para['goods_id']:
                association = ProductSetmeal(product_num=good['number'])
                association.goods = self.controlsession.query(BaseProductUnit).filter(
                    BaseProductUnit.id == good['id']).first()
                set_meal.goods.append(association)

            self.controlsession.add(set_meal)
            #self.controlsession.commit()

            fg_op = FlagShipOp()
            # 添加旗舰店价格
            if set_meal_para['unify_flg']:
                flagships = fg_op.get_all_flagship_info()
                for flagship in flagships:
                    set_meal_price = BaseSetmealPrice(
                        set_meal_id=set_meal.id,
                        flagship_id=flagship.id,
                        price=set_meal_para['price_max'],
                        floor_price=set_meal_para['floor_price_max'],
                        commission_amount=0)
                    self.controlsession.add(set_meal_price)
            else:
                for flagship in set_meal_para['flagship']:
                    set_meal_price = BaseSetmealPrice(
                        set_meal_id=set_meal.id,
                        flagship_id=flagship['id'],
                        price=flagship['price'],
                        floor_price=flagship['floor_price'],
                        commission_amount=0)
                    self.controlsession.add(set_meal_price)

            # 添加图片链接数
            upload_op = UploadOp()
            if set_meal.img is not None and set_meal != "" and \
                not upload_op.add_link(UploadOp.LINK_TYPE_SRV_ADR, set_meal.img, False):
                return False, None

            self.controlsession.commit()
        except IntegrityError as e:
            print(traceback.format_exc())
            self.controlsession.rollback()
            return False, None
        else:
            return True, set_meal.id

    def edit_set_meal(self, set_meal_para):
        """
        编辑套餐信息
        :param set_meal_para:
        :return: True or False
        """
        try:
            # print("set_meal_para: ", set_meal_para)
            set_meal = self.controlsession.query(BaseSetmealUnit).filter(
                BaseSetmealUnit.id == set_meal_para['id']).first()

            # 找不到对应ID或商品下架
            if not set_meal or not set_meal.putaway:
                return False
            set_meal.name = set_meal_para['name']
            set_meal.description = set_meal_para['description']
            # 在修改img之前,需要删原操作的链接数。之后增加新的图片链接数
            upload_op = UploadOp()
            if set_meal.img != set_meal_para['img']:
                if not upload_op.del_link(
                        UploadOp.LINK_TYPE_SRV_ADR, set_meal.img, False):
                    return False
                else:
                    set_meal.img = set_meal_para['img']
                    if not upload_op.add_link(UploadOp.LINK_TYPE_SRV_ADR, set_meal.img, False):
                        return False

            set_meal.unify_flg = set_meal_para['unify_flg']
            if set_meal_para.get('floor_price_max', None) is not None:
                set_meal.floor_price_max = set_meal_para['floor_price_max']
            if set_meal_para.get('floor_price_min', None) is not None:
                set_meal.floor_price_min = set_meal_para['floor_price_min']
            if set_meal_para.get('price_max', None) is not None:
                set_meal.price_max = set_meal_para['price_max']
            if set_meal_para.get('price_min', None) is not None:
                set_meal.price_min = set_meal_para['price_min']

            # sql = "delete from product_setmeal where set_meal_id='%d'" % set_meal_para['id']
            # self.controlsession.execute(sql)
            self.controlsession.query(ProductSetmeal).filter_by(
                set_meal_id=set_meal_para['id']).delete()
            for good in set_meal_para['goods_id']:
                # print("good['id']", good['id'])
                association = ProductSetmeal(
                    product_num=good['number'],
                    set_meal_id=set_meal_para['id'])
                association.goods = self.controlsession.query(BaseProductUnit).filter(
                    BaseProductUnit.id == good['id']).first()
                set_meal.goods.append(association)
            self.controlsession.add(set_meal)

            # 添加旗舰店价格
            if set_meal_para['unify_flg'] and set_meal_para.get('price_max', None) is not None and \
                                               set_meal_para.get('floor_price_max', None) is not None:
                fg_op=FlagShipOp()
                flagships=fg_op.get_all_flagship_info()
                for flagship in flagships:
                    set_meal_price=self.controlsession.query(BaseSetmealPrice).filter(
                        BaseSetmealPrice.set_meal_id == set_meal.id,
                        BaseSetmealPrice.flagship_id == flagship.id).first()
                    if set_meal_price is None:
                        raise ValueError("Can't match the flagship price infomation !")
                    set_meal_price.price=set_meal_para['price_max']
                    set_meal_price.floor_price=set_meal_para[
                        'floor_price_max']
                    self.controlsession.add(set_meal_price)
            else:
                for flagship in set_meal_para['flagship']:
                    set_meal_price = self.controlsession.query(BaseSetmealPrice).filter_by(
                        set_meal_id = set_meal.id, id = flagship['id']).first()
                    if set_meal_price is None:
                        raise ValueError("Can't match the flagship price infomation !")
                    set_meal_price.price=flagship['price']
                    set_meal_price.floor_price=flagship['floor_price']
                    self.controlsession.add(set_meal_price)

            self.controlsession.commit()
        except IntegrityError as e:
            print(e)
            self.controlsession.rollback()
            return False
        else:
            return True

    def delete_set_meal(self, set_meal_id):
        """
        下架套餐
        :param set_meal_id: 套餐ID
        :return: True or False
        """
        try:
            print("set_meal_id", set_meal_id)
            set_meal=self.controlsession.query(BaseSetmealUnit).filter_by(
                    id = set_meal_id).first()
            if set_meal is None:
                return False
            set_meal.putaway = False
            self.controlsession.add(set_meal)
            self.controlsession.commit()
        except IntegrityError as e:
            print(e)
            self.controlsession.rollback()
            return False
        else:
            return True

    def add_operate_record(self, uid, detail, id, other_tblname):
        """
        添加操作记录
        :param 操作用户ID
        :param detail: 记录详情描述
        :return:
        """
        operate_op = Operate_Op()
        operate_op.add_record(detail=detail,
                              operator_id=uid,
                              operate_time=datetime.now(),
                              other_tblname=other_tblname,
                              other_id=str(id),
                              is_commit=True)

    def add_flagship_to_setmeal_price(self, flagship_id):
        """
        用于创建旗舰店时，为新添加的旗舰店添加相应的商品价格
        :param flagship_id:
        :return:
        """
        setmeals = self.controlsession.query(BaseSetmealUnit).all()
        for setmeal in setmeals:
            if setmeal.unify_flg:
                setmeals_price = BaseSetmealPrice(set_meal_id=setmeal.id,
                                                  flagship_id=flagship_id,
                                                  price=setmeal.price_max,
                                                  floor_price=setmeal.floor_price_max)

            else:
                setmeals_price = BaseSetmealPrice(set_meal_id=setmeal.id, flagship_id=flagship_id)

            self.controlsession.add(setmeals_price)
        self.controlsession.commit()

    def test_for_associate_select(self, sou):
        """
        测试函数，用于测试多对多连表查询。
        :param sou: 模糊名字
        :return: dict
        """
        # from sqlalchemy import distinct
        temp = self.controlsession.query(BaseSetmealUnit).filter(
                                                               ProductSetmeal.product_id == BaseProductUnit.id,
                                                               ProductSetmeal.set_meal_id == BaseSetmealUnit.id,
                                                               BaseProductUnit.name.like(sou)).distinct().all()
        print("-"*80)
        print("temp:",temp)
        print("type(temp):", temp)


    def get_set_meal_by_id(self,set_meal_id):
        '''

        :param set_meal_id:  套餐数量
        :return:
        '''
        setmeals = self.controlsession.query(ProductSetmeal.set_meal_id,func.sum(ProductSetmeal.product_num)).\
            filter(ProductSetmeal.set_meal_id==set_meal_id).first()
        rs = self.controlsession.query(BaseSetmealUnit).filter(BaseSetmealUnit.id==set_meal_id).first()
        print '*********************************',setmeals,rs.name
        r_data={
            "set_meal_id" : set_meal_id,
            "setmeal_info" : rs.to_json(),
            "product_amount" : int(setmeals[1])
        }
        return r_data

    def get_set_info_by_id(self,set_meal_id):
        '''

        :param set_meal_id:
        :return:
        '''

        set_meal = self.controlsession.query(ProductSetmeal.product_id,ProductSetmeal.product_num).filter_by(set_meal_id=set_meal_id).all()

        return set_meal
if __name__ == "__main__":
    set_meal_id = 2
    op = SetMealOp()
    data = op.get_set_info_by_id(1)
    print data
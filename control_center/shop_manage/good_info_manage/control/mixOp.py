#-*- coding:utf-8 -*-


import traceback
from datetime import datetime

from sqlalchemy import func, distinct, or_, and_, LargeBinary
from sqlalchemy.exc import IntegrityError

from data_mode.erp_base.control.uploadOp import UploadOp
from data_mode.erp_supply.base_op.operate_op import Operate_Op
from data_mode.hola_warehouse.control_base.controlBase import ControlEngine
from data_mode.hola_warehouse.model.base_product_category import BaseProductCategory
from data_mode.hola_warehouse.model.base_product_price import BaseProductPrice
from data_mode.hola_warehouse.model.base_product_unit import BaseProductUnit
from data_mode.hola_warehouse.model.product_setmeal import ProductSetmeal

Dict_Categorgory_touyingyi = {
    'id': 1,
    'name': u"坚果投影仪"
}

Dict_Categorgory_peijian = {
    'id': 2,
    'name': u"坚果配件"
}


def get_products_by_category(Category, noputaway=False):
    product_set = set()
    products = Category.products
    for product in products:
        if noputaway or product.putaway:
            product_set.add(product)
    children_category = Category.children
    for child_category in children_category:
        product_set = product_set | get_products_by_category(
            child_category, noputaway)
    return product_set


def sort_price(mdict):
    return mdict.get('price', None)


def sort_floor_price(mdict):
    return mdict.get('floor_price', None)


class HolaWareHouse(ControlEngine):

    def __init__(self):
        ControlEngine.__init__(self)

    @property
    def TABLENAME(self):
        return BaseProductUnit.__tablename__

    def GetBaseProductCategory(self):
        list = self.controlsession.query(BaseProductCategory).all()
        if not list:
            return
        list = [item.to_json() for item in list]
        return list

    def GetBaseProductUnitByID(self, id):
        baseGoodsInfo = self.controlsession.query(
            BaseProductUnit).filter(BaseProductUnit.id == id).first()
        if not baseGoodsInfo:
            return
        return baseGoodsInfo.to_json()

    def get_all_product_info(self):
        rs = self.controlsession.query(BaseProductUnit).filter(
            BaseProductUnit.putaway).all()
        rs = [item.to_json() for item in rs]
        print rs
        return rs

    def get_all_product_info_not_filter_putaway(self):
        rs = self.controlsession.query(BaseProductUnit).all()
        rs = [item.to_json() for item in rs]
        print rs
        return rs

    def get_all_product_dict_info(self, putaway=True):
        rs = []
        if putaway:
            rs = self.controlsession.query(BaseProductUnit).filter(
                BaseProductUnit.putaway).all()
        else:
            rs = self.controlsession.query(BaseProductUnit).all()
        items = [(item.id, item.to_json()) for item in rs]
        return dict(items)
        
    def get_product_info_by(self, pname='',pcode='',pbarcode=''):
        if len(pname):
            return self.controlsession.query(BaseProductUnit).filter_by(name=pname).scalar()
        elif len(pcode):
            return self.controlsession.query(BaseProductUnit).filter_by(code=pcode).scalar()
        elif len(pbarcode):
            return self.controlsession.query(BaseProductUnit).filter_by(bar_code=pbarcode).scalar()
        
        return None

    def get_product_info(self, product_id):
        '''
        根据商品id 获取商品名称和分类名称
        '''
        rs = self.controlsession.query(BaseProductUnit).get(product_id)
        if rs:
            dct = {}
            dct["product_name"] = rs.name
            dct["category_name"] = rs.category.name
            dct['product_model'] = rs.specification
            dct['barcode'] = rs.bar_code
            dct['img'] = rs.img
            # dct["price"] = rs.price
            dct["price"] = rs.price_min #要注明啊啊啊啊啊啊
            return dct
        else:
            return {}

    def add_category(self, pid, name):
        category = None
        try:
            if pid != 0:
                category = BaseProductCategory(name=name, parent_id=pid)
            else:
                category = BaseProductCategory(name=name)
            self.controlsession.add(category)
            self.controlsession.commit()
        except IntegrityError as e:
            self.controlsession.rollback()
            return False,None
        return True, category.id

    def category_rename(self, category_id, name):
        """
        重命名商品分类。其中，固定的分类禁止重命名
        :param category_id:
        :param name:
        :return: code
        0 -- success
        1 -- database error
        2 -- prohibit rename resource
        """
        category = self.controlsession.query(BaseProductCategory).filter(
            BaseProductCategory.id == category_id).first()
        try:
            category.name = name
            if category.id in (Dict_Categorgory_touyingyi['id'],
                               Dict_Categorgory_peijian['id']):
                return 2
            self.controlsession.add(category)
            self.controlsession.commit()
        except IntegrityError as e:
            self.controlsession.rollback()
            return 1
        return 0

    def get_product_reward_by_product_id(self, product_id):
        '''
        根据商品id 获取商品奖励
        :param product_id:
        :return: 商品奖励数
        '''
        rs = self.controlsession.query(BaseProductPrice).filter_by(
            product_id=product_id).first()
        if rs:
            rs = rs.commission_amount
            return rs
        else:
            return 0

    def delete_category(self, category_id):
        """

        :param category_id:
        :return:
        0 -- success
        1 -- has children
        2 -- has product
        3 -- didn't have category
        4 -- prohibit delete resource
        """
        print("category_id:",int(category_id))
        category = self.controlsession.query(BaseProductCategory).filter_by(
            id = int(category_id)).first()
        try:
            if category is None:
                return 3
            if category.children is not None and len(category.children):
                return 1
            if category.products is not None and len(category.products):
                return 2
            if category.id in (Dict_Categorgory_peijian['id'],
                               Dict_Categorgory_touyingyi['id']):
                return 4

            self.controlsession.delete(category)
            self.controlsession.commit()
        except IntegrityError as e:
            self.controlsession.rollback()
            return 1
        return 0

    def show_product(self, id):
        unit = self.controlsession.query(BaseProductUnit).filter(
            BaseProductUnit.id == id).first()
        return unit.to_json()

    def add_product(self, product, category_id):
        try:
            t = self.controlsession.query(BaseProductUnit).order_by(BaseProductUnit.id.desc()).first()
            tid = t.id + 1 if t is not None else 1
            unit = BaseProductUnit(
                id= tid,
                category_id=category_id,
                name=product['name'],
                code=product['code'],
                specification=product['specification'],
                bar_code=product['bar_code'],
                img=product['img'],
                unify_flg=product['unify_flg'],
                price_min=product['price_min'],
                price_max=product['price_max'],
                floor_price_min=product['floor_price_min'],
                floor_price_max=product['floor_price_max'],
                weight=product['weight'],
                gift_flg=product['gift_flg'],
                measure=product['measure'],
                remark=product['remark'])

            self.controlsession.add(unit)
            from control_center.flagship_manage.flagship_info_manage.control.flagship_op import FlagShipOp
            fg_op = FlagShipOp()
            # 全国统一价格标志
            if unit.unify_flg:
                flagships = fg_op.get_all_flagship_info()
                for flagship in flagships:
                    product_price = BaseProductPrice(
                        product_id=unit.id,
                        flagship_id=flagship.id,
                        price=product['price_max'],
                        floor_price=product['floor_price_max'],
                        commission_amount=0)
                    self.controlsession.add(product_price)
            else:
                for flagship in product['flagship']:
                    product_price = BaseProductPrice(
                        product_id=unit.id,
                        flagship_id=flagship['id'],
                        price=flagship['price'],
                        floor_price=flagship['floor_price'],
                        commission_amount=0)
                    self.controlsession.add(product_price)


            # 增加图片的链接数
            upload_op = UploadOp()
            if unit.img is not None and unit != "" and not upload_op.add_link(
                    UploadOp.LINK_TYPE_SRV_ADR, unit.img, False):
                return False, None

            self.controlsession.commit()
        except Exception as e:
            print(e)
            self.controlsession.rollback()
            return False, None
        return True, unit.id

    def add_flagship_to_price(self, flagship_id):
        units = self.controlsession.query(BaseProductUnit).all()
        for unit in units:
            # 商品是否全国统一
            if unit.unify_flg:
                product_price = BaseProductPrice(
                    product_id=unit.id, flagship_id=flagship_id,
                        price=unit.price_max, floor_price=unit.floor_price_max)
            else:
                product_price = BaseProductPrice(
                    product_id=unit.id, flagship_id=flagship_id)
            self.controlsession.add(product_price)
        self.controlsession.commit()

    def Edit_product(self, product):
        try:
            upload_op = UploadOp()
            unit = self.controlsession.query(BaseProductUnit).filter(
                BaseProductUnit.id == product['id']).first()
            # 可以使用 getattr 和 hasattr内建函数。前提key等于BaseProductUnit的栏位名
            print("type(unit):",type(unit))
            if unit is None:
                return False
            for key, value in product.items():
                if hasattr(unit, key):
                    # 如果编辑中有包含img,且图片地址与原先存储的地址不同时，需要
                    # 先减少原地址的链接数，之后再增加对新地址的链接数。为了保证
                    # 事务的原子性和一致性，在调用del_link时，不提交事务。
                    # 之后对修改的图片增加链接
                    if key == 'img' and getattr(unit, key) != value:
                        if not upload_op.del_link(UploadOp.LINK_TYPE_SRV_ADR, getattr(unit,key), False):
                            return False
                        else:
                            setattr(unit, key, value)
                            if not upload_op.add_link(UploadOp.LINK_TYPE_SRV_ADR, getattr(unit,key), False):
                                return False

                    setattr(unit, key, value)

            self.controlsession.add(unit)
            # 更新BaseProductPrice的信息
            # 为了保持数据一致性，只有当事务完成时，才进行commit操作
            from control_center.flagship_manage.flagship_info_manage.control.flagship_op import FlagShipOp
            # from control_center.departments.flagship.control.flagship_op import FlagShipOp
            fg_op = FlagShipOp()
            print("unit.unify_flg:", unit.unify_flg)
            # 全国统一价格标志
            if unit.unify_flg:
                flagships = fg_op.get_all_flagship_info()
                for flagship in flagships:
                    product_price=self.controlsession.query(BaseProductPrice).filter_by(
                            flagship_id = flagship.id,
                            product_id = product['id']).first()
                    product_price.price=product['price_max'],
                    product_price.floor_price=product['floor_price_max'],

                    self.controlsession.add(product_price)
            elif len(product['flagship']) > 0:
                for flagship in product['flagship']:
                    product_price=self.controlsession.query(BaseProductPrice).filter_by(
                            id = flagship['id'],
                            product_id = product['id']).first()
                    product_price.price = flagship['price']
                    product_price.floor_price = flagship['floor_price']

                    self.controlsession.add(product_price)

            self.controlsession.commit()
        except Exception as e:
            self.controlsession.rollback()
            print traceback.format_exc()
            return False
        return True

    def Delete_product(self, product):
        try:
            unit = self.controlsession.query(BaseProductUnit).filter(
                BaseProductUnit.id == product['id']).first()
            #减少图片的链接数
            upload_op = UploadOp()
            if not upload_op.del_link(UploadOp.LINK_TYPE_SRV_ADR, unit.img, False):
                return False

            self.controlsession.delete(unit)
            self.controlsession.commit()
        except IntegrityError as e:
            self.controlsession.rollback()
            return False
        return True

    def putaway_product(self, product):
        try:
            unit = self.controlsession.query(BaseProductUnit).filter(
                BaseProductUnit.id == product['id']).first()
            # self.controlsession.delete(unit)
            unit.putaway = not unit.putaway
            self.controlsession.add(unit)
            self.controlsession.commit()
        except IntegrityError as e:
            self.controlsession.rollback()
            return False
        return True

    def batch_putaway_product(self, product_list, putaway):
        """
        商品批量上架或下架
        :param product_list: list 存放商品id的列表
        :param putaway: 上架或下架标志  True 上架  False 下架
        :return Boolean 成功--True   失败--False
        """
        try:
            print("product_list")
            for unit_id in product_list:
                self.controlsession.query(BaseProductUnit).filter(
                    BaseProductUnit.id == unit_id).update({BaseProductUnit.putaway: putaway})
            self.controlsession.commit()
        except IntegrityError as e:
            self.controlsession.rollback()
            print(e)
            return False
        return True

    def show_all_product(self, start, per_page):
        units = self.controlsession.query(BaseProductUnit).filter(
            BaseProductUnit.putaway).order_by(
            BaseProductUnit.id).limit(per_page).offset(start)
        data = [unit.to_json() for unit in units]
        return data

    def show_all_product_filter(self, start, per_page, putway=None, **kw):
        """
        获取商品信息,同时根据店铺id显示售价
        :param start: 起始记录位置
        :param per_page: 每页显示记录数
        :param putway: 如果为None则不筛选上下架条件
        :param kw: 目前只支持name，code，bar_code属性
        :return:
        """
        units = None
        total = 0
        if kw or len(kw) != 0:
            for key, value in kw.items():
                # if key not in ('name', 'code', 'bar_code'):
                    # raise ValueError(
                    #     "kw[%s] must be in range ('name', 'code', 'bar_code')!")
                if key not in ('name', 'code', 'bar_code', 'category_id'):
                    raise ValueError(
                        "kw[%s] must be in range ('name', 'code', 'bar_code','category_id')!")
                elif value is None:
                    continue

                if key is 'category_id':
                    units = self.controlsession.query(BaseProductUnit).filter(
                        getattr(BaseProductUnit, key) == value).order_by(
                        BaseProductUnit.id).limit(per_page).offset(start)
                    total = self.controlsession.query(
                        func.count(BaseProductUnit.id)).filter(
                        getattr(BaseProductUnit, key) == value).scalar()
                elif putway is not None:
                    value = "%" + str(value) + "%"
                    units = self.controlsession.query(BaseProductUnit).filter(
                        getattr(BaseProductUnit, key).like(value),
                        BaseProductUnit.putaway == putway).order_by(
                        BaseProductUnit.id).limit(per_page).offset(start)
                    total = self.controlsession.query(
                        func.count(
                            BaseProductUnit.id)).filter(
                        getattr(
                            BaseProductUnit,
                            key).like(value),
                        BaseProductUnit.putaway == putway).scalar()
                else:
                    value = "%" + str(value) + "%"
                    units = self.controlsession.query(BaseProductUnit).filter(
                        getattr(BaseProductUnit, key).like(value)).order_by(
                        BaseProductUnit.id).limit(per_page).offset(start)
                    total = self.controlsession.query(
                        func.count(
                            BaseProductUnit.id)).filter(
                        getattr(
                            BaseProductUnit,
                            key).like(value)).scalar()
                break
        else:
            if putway is None:
                units = self.controlsession.query(BaseProductUnit).order_by(
                    BaseProductUnit.putaway.desc(), BaseProductUnit.id).limit(per_page).offset(start)
                total = self.controlsession.query(
                    func.count(BaseProductUnit.id)).scalar()
            else:
                units = self.controlsession.query(BaseProductUnit).filter(
                        BaseProductUnit.putaway == putway).order_by( 
                                BaseProductUnit.putaway.desc(), BaseProductUnit.id).limit(
                                        per_page).offset(start)
                total = self.controlsession.query(
                        func.count(BaseProductUnit.id)).filter(
                                BaseProductUnit.putaway == putway).scalar()

        if units is not None:
            data = [unit.to_json() for unit in units]
        else:
            data = {}
        return data, total

    def get_products_detail_info_by_category(
            self, category_id, start, per_page, sou):
        products = None
        total = 0
        if len(sou):
            sou = "%" + sou + "%"
            products = self.controlsession.query(BaseProductUnit).filter(or_(BaseProductUnit.name.like(
                sou), BaseProductUnit.code.like(sou))).order_by(BaseProductUnit.id).limit(per_page).offset(start)
            total = self.controlsession.query(func.count(BaseProductUnit.id)).filter(
                or_(BaseProductUnit.name.like(sou), BaseProductUnit.code.like(sou))).scalar()
        else:
            if category_id != 0:
                category = self.controlsession.query(BaseProductCategory).filter(
                    BaseProductCategory.id == category_id).first()
                products = list(get_products_by_category(category))
                total = len(products)
                products = products[start:start + per_page]
            else:
                products = self.controlsession.query(BaseProductUnit).filter(
                    BaseProductUnit.putaway).order_by(
                    BaseProductUnit.id).limit(per_page).offset(start)
                total = self.controlsession.query(
                    func.count(
                        BaseProductUnit.id)).filter(
                    BaseProductUnit.putaway).scalar()
        return self.show_all_product_info(products), total

    def get_products_count(self):
        total = self.controlsession.query(
            func.count(
                BaseProductUnit.id)).filter(
            BaseProductUnit.putaway).scalar()
        return total

    def get_products_detail_info_by_product_id(self, product_id):
        unit = self.controlsession.query(BaseProductUnit).filter(
            BaseProductUnit.id == product_id).first()
        return self.show_product_datail_info(unit)

    # def get_products_dict_detail_info_by_category(self, category_id):
    #     category = self.controlsession.query(BaseProductCategory).filter(BaseProductCategory.id == category_id).first()
    #     products = category.products
    # return  dict([(product.id,product.to_json()) for product in products])
    def get_products_dict_detail_info_by_category(
            self, category_id, noputaway=False):
        category = self.controlsession.query(BaseProductCategory).filter(
            BaseProductCategory.id == category_id).first()
        products = list(get_products_by_category(category, noputaway))
        return dict([(product.id, product.to_json()) for product in products])

    def show_all_product_info(self, products):
        data = []
        # from control_center.departments.flagship.control.flagship_op import FlagShipOp
        from control_center.flagship_manage.flagship_info_manage.control.flagship_op import FlagShipOp
        flagship_op = FlagShipOp()
        flagship_info = flagship_op.get_all_flagship_dict_info()

        for product in products:
            products_data = product.to_json()
            if product.flagships_price is not None:
                price_datas = []
                for price in product.flagships_price:
                    price_data = price.to_json()
                    flagshipid = price_data.pop('flagship_id')
                    price_data['flagship'] = flagship_info[flagshipid]
                    price_datas.append(price_data)
                products_data['flagships_price'] = price_datas
            data.append(products_data)

        return data

    def show_product_datail_info(self, product):
        data = []
        from control_center.flagship_manage.flagship_info_manage.control.flagship_op import FlagShipOp
        flagship_op = FlagShipOp()
        flagship_info = flagship_op.get_all_flagship_dict_info()

        products_data = product.to_json()
        if product.flagships_price is not None:
            price_datas = []
            for price in product.flagships_price:
                price_data = price.to_json()
                flagshipid = price_data.pop('flagship_id')
                price_data['flagship'] = flagship_info[flagshipid]
                price_datas.append(price_data)
            products_data['flagships_price'] = price_datas
        return products_data

    def show_all_category(self):
        categorys = self.controlsession.query(
            BaseProductCategory).order_by(BaseProductCategory.id).all()
        data = [category.to_json() for category in categorys]
        return data

    def init_category(self):
        try:
            touyingyi_category = BaseProductCategory(
                id=Dict_Categorgory_touyingyi['id'],
                name=Dict_Categorgory_touyingyi['name'])
            peijian_category = BaseProductCategory(
                id=Dict_Categorgory_peijian['id'],
                name=Dict_Categorgory_peijian['name'])
            self.controlsession.add(touyingyi_category)
            self.controlsession.add(peijian_category)
            self.controlsession.commit()
            print u"初始化 商品分类"
        except Exception as e:
            print e

    def edit_prouct_detail_info(
            self,
            product_id,
            price,
            open_unify_floor_price,
            unify_floor_price,
            floor_prices,
            open_unify_commission_amount,
            unify_commission_amount,
            commission_amounts):
        try:
            unit = self.controlsession.query(BaseProductUnit).filter(
                BaseProductUnit.id == product_id).first()
            if product_id is None:
                return False
            unit.price = price
            from control_center.flagship_manage.flagship_info_manage.control.flagship_op import FlagShipOp
            flagship_op = FlagShipOp()
            dict_flagship = flagship_op.get_all_flagship_dict_info()

            for key, value in dict_flagship.items():
                cur_floor_prices = None
                cur_commission_amount = None
                if open_unify_floor_price:
                    cur_floor_prices = unify_floor_price
                else:
                    cur_floor_prices = floor_prices[str(key)]

                if open_unify_commission_amount:
                    cur_commission_amount = unify_commission_amount
                else:
                    cur_commission_amount = commission_amounts[str(key)]
                product_price = self.controlsession.query(BaseProductPrice).filter(
                    BaseProductPrice.product_id == product_id,
                    BaseProductPrice.flagship_id == key).first()
                if product_price is None:
                    product_price = BaseProductPrice(
                        product_id=product_id,
                        flagship_id=key,
                        floor_price=cur_floor_prices,
                        commission_amount=cur_commission_amount)
                else:
                    product_price.floor_price = cur_floor_prices
                    product_price.commission_amount = cur_commission_amount

                self.controlsession.add(product_price)
            self.controlsession.add(unit)
            self.controlsession.commit()
        except Exception as e:
            self.controlsession.rollback()
            print e

    def get_product_price_by_product_flagship(self, product_id, flagship_id):
        product_price = self.controlsession.query(BaseProductPrice).filter(
            BaseProductPrice.product_id == product_id,
            BaseProductPrice.flagship_id == flagship_id).first()
        data = {
            'price': product_price.price,
            'floor_price': product_price.floor_price,
            'commission_amount': product_price.commission_amount,
        }
        return data

    def get_product_byname(self, product_name):
        product = self.controlsession.query(BaseProductUnit).filter(
            BaseProductUnit.name == product_name).first()
        if product is None:
            return None
        from data_mode.hola_warehouse.model.base_product_category import get_father_father
        unit_data = product.to_json()
        father = get_father_father(product.category)
        unit_data['father_category'] = father.to_json()
        return unit_data

    def get_product_id_list_byname(self, product_name):  #2016-10-25 by cq
        product_id_list = self.controlsession.query(BaseProductUnit.id).filter(
            BaseProductUnit.name.cast(LargeBinary)==product_name).order_by(BaseProductUnit.id).all()

        return product_id_list

    def get_product_byid(self, product_id):
        product = self.controlsession.query(BaseProductUnit).filter(
            BaseProductUnit.id == product_id).first()
        if product is None:
            return None
        from data_mode.hola_warehouse.model.base_product_category import get_father_father
        unit_data = product.to_json()
        father = get_father_father(product.category)
        unit_data['father_category'] = father.to_json()
        return unit_data

    def get_product_price(self, flagship_id):
        products_price = self.controlsession.query(BaseProductPrice).filter(
            BaseProductPrice.flagship_id == flagship_id).all()
        # return dict([(product_price.product_id,  product_price.to_json()) for
        # product_price  in products_price])
        data = {}
        for product_price in products_price:
            if product_price.product is not None and product_price.product.putaway:
                data[product_price.product_id] = product_price.to_json()
        return data

    def get_product_father_category_info(self, noputaway=False):
        units = self.controlsession.query(BaseProductUnit).all()
        data = {}
        from data_mode.hola_warehouse.model.base_product_category import get_father_father
        for unit in units:
            if noputaway or unit.putaway:
                unit_data = unit.to_json()
                category = unit.category
                father = get_father_father(category)
                unit_data['father_category'] = father.to_json()
                data[unit.id] = unit_data
        return data

    def get_category_ancestor(self, categoryId):

        from data_mode.hola_warehouse.model.base_product_category import get_father_father
        category = self.controlsession.query(BaseProductCategory).filter(
            BaseProductCategory.id == categoryId).first()
        if not category:
            return 0
        father = get_father_father(category)

        return father.id

    def Edit_one_product_floorprice(
            self,
            flagship_id,
            product_id,
            floor_price):
        #product_price = BaseProductPrice(product_id = product_id, flagship_id=flagship_id)
        product_price = self.controlsession.query(BaseProductPrice).filter(
            BaseProductPrice.product_id == product_id,
            BaseProductPrice.flagship_id == flagship_id).first()
        product_price.floor_price = floor_price
        self.controlsession.add(product_price)
        self.controlsession.commit()

    def Edit_one_product_commissionamount(
            self, flagship_id, product_id, commission_amount):
        product_price = self.controlsession.query(BaseProductPrice).filter(
            BaseProductPrice.product_id == product_id,
            BaseProductPrice.flagship_id == flagship_id).first()
        product_price.commission_amount = commission_amount
        self.controlsession.add(product_price)
        self.controlsession.commit()

    def Get_leaf_category(self):
        data = {}
        categorys = self.controlsession.query(
            BaseProductCategory).order_by(BaseProductCategory.id).all()
        for category in categorys:
            if category.children is None:
                continue
            if len(category.children):
                continue
            data[category.id] = category.name
        return data

    def Get_leaf_category_list_info(self):
        data = []
        categorys = self.controlsession.query(
            BaseProductCategory).order_by(BaseProductCategory.id).all()
        for category in categorys:
            if category.children is None:
                continue
            if len(category.children):
                continue
            data.append(category.to_json())
        return data

    def get_commission_amount_by_flagship_product(
            self, flagship_id, product_id):
        product_price = self.controlsession.query(BaseProductPrice).filter(
            BaseProductPrice.product_id == product_id,
            BaseProductPrice.flagship_id == flagship_id).first()
        return product_price.commission_amount

    def get_product_all_flagship_price(self, product_id):
        unit = self.controlsession.query(BaseProductUnit).filter_by(id=product_id).first()
        data = unit.to_json()
        print("-"*80)
        # 加入旗舰店信息
        from control_center.flagship_manage.flagship_info_manage.control.flagship_op import FlagShipOp
        fg_op = FlagShipOp()
        data['flagship'] = []
        for flagship in unit.flagships_price:
            json_data = flagship.to_json()
            info = fg_op.get_flagship_info_by_flagship_id(flagship.flagship_id)
            json_data['name'] = info['name']
            data['flagship'].append(json_data)

        data['category_id'] = data['category']['id']
        data.pop('category')
        print("data:", data)
        print("-"*80)
        return data

    def get_product_by_gift(self, flagship_id, stype, svalue, page, per_page, is_gift):
        """
        根据旗舰店ID相关条件查询商品信息
        :param flagship_id: 旗舰店ID
        :param stype: 搜索类型 (1：商品名称关键字 2：商品编码（完全匹配）)
        :param svalue: 搜索内容，根据stype判断
        :param page: 分页的当前页数
        :param per_page: 每页显示的记录数
        :param is_gift: 是否为赠品。
        :return: list(dict)
        """
        if stype not in (1, 2):
            raise ValueError("stype value must be in (1,2)!")
        # 计算页面
        page = page - 1
        if page < 0:
            page = 0
        if per_page > 60:
            per_page = 60
        start = page * per_page

        if stype == 1:
            rule = and_(BaseProductUnit.name.like('%'+str(svalue)+'%'), BaseProductUnit.putaway == True)
        else:
            rule = and_(BaseProductUnit.code.like(str(svalue)), BaseProductUnit.putaway == True)

        units = self.controlsession.query(BaseProductUnit).filter(
                rule,
                BaseProductUnit.gift_flg == is_gift).limit(per_page).offset(start)
        total = self.controlsession.query(func.count(BaseProductUnit.id)).filter(
                rule, BaseProductUnit.gift_flg == is_gift).scalar()
        data = []
        print("-"*40 + "get_product_by_gift" + "-"*40)
        for unit in units:
            unit_json = {}
            unit_json['p_name'] = unit.name
            unit_json['p_code'] = unit.code
            unit_json['p_barCode'] = unit.bar_code
            unit_json['p_file'] = unit.img
            for flagship_price in unit.flagships_price:
                if flagship_price.flagship_id == flagship_id:
                    unit_json['p_price'] = flagship_price.price
                    unit_json['p_floor_price'] = flagship_price.floor_price
            unit_json['p_type'] = unit.category.name
            unit_json['p_type_id'] = unit.category_id
            unit_json['p_is_gift'] = unit.gift_flg
            data.append(unit_json)
        print("data:", data)
        print("rule:", rule)
        print("-"*40 + "End" + "-"*40)

        return data, total

    def get_product_price_by_id(self, product_id):
        prices = self.controlsession.query(BaseProductPrice).filter(
                BaseProductPrice.product_id == product_id).all()
        data = [price.to_json() for price in prices]
        return data

    def is_contain_set_meal(self, product_id):
        """
        判断商品是否包含在套餐内
        :param product_id: 商品ID
        :return: True or False
        """
        product = self.controlsession.query(BaseProductUnit).filter_by(
                id=product_id).first()

        if product is None:
            raise ValueError("Can't found the record, you input id:",product_id)

        num = 0
        for accos in product.set_meal:
            if accos.set_meal.putaway == True:
                num += 1

        return True if num > 0 else False

    def is_contain_set_meal_for_batch(self, product_id_list):
        """
        判断商品是否包含在套餐内,用于批量操作
        :param product_id_list:
        :return: tuple(Boolean, msg)
        """
        for product_id in product_id_list:
            product = self.controlsession.query(BaseProductUnit).filter_by(
                id=product_id).first()

            if product is None:
                raise ValueError("Can't found the record, you input id:",product_id)

            num = 0
            for accos in product.set_meal:
                if accos.set_meal.putaway == True:
                    num += 1

            if num > 0:
                return (False, u'商品:%s包含在套餐中,请先移除该商品' % product.name)
        return (True, u'成功')

    def verify_product_field_exist(self, stype, value):
        """
        验证产品表BaseProductUnit栏位值是否存在
        :param stype: 栏位类型
        :param value: 栏位值
        :return: True or False  存在或不存在
        """
        if stype == 1:
            product = self.controlsession.query(BaseProductUnit).filter_by(code=value).first()
        elif stype == 2:
            product = self.controlsession.query(BaseProductUnit).filter_by(bar_code=value).first()
        else:
            raise ValueError("stype not in allow range")

        if product is None:
            return False
        else:
            return True

    def add_operate_record(self, uid, detail, id, tablename=None):
        """
        添加操作记录
        :param 操作用户ID
        :param detail: 记录详情描述
        :return:
        """
        operate_op = Operate_Op()
        # print("add record: [%s] [%s] [%s]" % (detail, uid, id))
        operate_op.add_record(detail=detail,
                              operator_id=uid,
                              operate_time=datetime.now(),
                              other_tblname=self.TABLENAME if tablename is None else tablename,
                              other_id=str(id),
                              is_commit=True)

    def get_category_info(self, category_id):
        """
        获取分类信息
        :param category_id: 分类ID
        :return: json
        """
        category = self.controlsession.query(BaseProductCategory).filter_by(id=category_id).first()
        if category is None:
            return None
        else:
            return category.to_json()

    def get_product_desc_first(self):
        return self.controlsession.query(BaseProductUnit).order_by(BaseProductUnit.id.desc()).first()

    def getProIdByGoodCode(self, proCode):
        try:
            rs = self.controlsession.query(BaseProductUnit).filter_by(code=proCode).first()
            if rs is not None:
                pro_id = rs.id
                return pro_id
        except Exception as e:
            print traceback.format_exc(e)
            return None

    def get_product_count_in_set(self,store_id, setmeal_id, pCode):
        """
        :param store_id: 店铺id
        :param setmeal_id: 套餐id
        :param pCode: 商品编码
        :return:
        """
        #product_list = self.get_id_by_productCode(store_id, pCode)
        product = self.controlsession.query(BaseProductUnit).filter(BaseProductUnit.code==pCode).first()
        if product is None:
            raise ValueError(u"没有找到商品编码:%s相关信息" % pCode)

        productSetmeal = self.controlsession.query(ProductSetmeal).filter_by(set_meal_id=setmeal_id,product_id=product.id).first()
        if productSetmeal is not None:
            return productSetmeal.product_num
        else:
            raise ValueError(u'套餐%s内没有商品%s的数量' % (productSetmeal.set_meal.name,product.name))

    def get_all_product_id(self):
        product_datas = self.controlsession.query(distinct(BaseProductUnit.id)).order_by(BaseProductUnit.id).all()
        product_id_list = [int(item[0]) for item in product_datas]

        return product_id_list

    def get_category_product(self,categories_id=None):
        product_datas = self.controlsession.query(BaseProductUnit).filter(BaseProductUnit.category_id == categories_id).all()

        product_datas=[itme.to_json() for itme in product_datas]

        return product_datas

    def get_products_by_idlist(self, id_list, store_id, start=None, page_num=None):
        """
        select id list
        :param id_list: list. contain id infomation.
        :param store_id: store id
        :return: list, int
        """
        if not isinstance(id_list, list):
            raise TypeError("id_list must be list type.")

        if start is None and page_num is None:
            products = self.controlsession.query(BaseProductUnit).filter(
                    BaseProductUnit.id.in_(tuple(id_list))).all()
        elif start is not None and page_num is not None:
            products = self.controlsession.query(BaseProductUnit).filter(
                    BaseProductUnit.id.in_(tuple(id_list))).limit(page_num).offset(start)
        else:
            raise ValueError('start types must be equit page_num types')

        total = self.controlsession.query(func.count(BaseProductUnit.id)).filter(
                BaseProductUnit.id.in_(id_list)).scalar()

        return_list = []

        if products is None:
            return return_list, 0

        for product in products:
            temp = {}
            temp = product.to_json()
            for flagship_price in product.flagships_price:
                if flagship_price.flagship_id == store_id:
                    temp['p_price'] = flagship_price.price
                    temp['p_floor_price'] = flagship_price.floor_price
            return_list.append(temp)

        return return_list, total

    def get_all_products_name(self):
        """
        返回商品名称的
        :param limit: 限制数量
        :return: dict
        """
        product_list = self.controlsession.query(BaseProductUnit.id, BaseProductUnit.name).all()
        result = {}
        for product in product_list:
            result[product[0]] = product[1]
        return result

if __name__ == '__main__':
    op = HolaWareHouse()
    data = op.Get_leaf_category()
    from pprint import pprint
    pprint(data)

#-*-coding:utf-8-*-

import traceback

from flask import jsonify, session, json
from flask import request
from flask.views import MethodView

from config.service_config.returncode import ServiceCode
from control_center.admin import add_url
from control_center.shop_manage import shop_manage, shop_manage_prefix
from control_center.shop_manage.good_info_manage.control.mixOp import HolaWareHouse, sort_price, sort_floor_price
from data_mode.erp_supply.base_op.operate_op import Operate_Op
from public.exception.custom_exception import CodeError
from public.function import tools

class ProductView(MethodView):

    def get(self):
        HolaWareHouse_op = HolaWareHouse()
        data, total = HolaWareHouse_op.show_all_product_filter(0, 10)
        result = {
            'code': ServiceCode.success,
            'total': total,
            'rows': data,
        }
        return tools.en_render_template(
            'shop_Management/Commodity_information.html',
            results=json.dumps(result))


class AllProductData(MethodView):
    """
    获取所有商品的数据接口
    """

    def get(self):
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        name = request.values.get('name', None, type=str)
        code = request.values.get('code', None, type=str)
        bar_code = request.values.get('bar_code', None, type=str)
        putaway_tmp = request.values.get('putaway', None, type=str)
        category_id = request.values.get('category_id', None, type=int) #20160928cq新增
        putaway = bool(
            int(putaway_tmp)) if putaway_tmp is not None and putaway_tmp != "" else None
        # 计算页面
        page = page - 1
        if page < 0:
            page = 0
        if per_page > 60:
            per_page = 60
        start = page * per_page
        HolaWareHouse_op = HolaWareHouse()
        # 获取数据
        # print("start:%d   per_page:%d" % (start, per_page))
        # print("putaway:", putaway)
        #if name is not None or code is not None or bar_code is not None:
        if name is not None or code is not None or bar_code is not None or category_id is not None:
            data, total = HolaWareHouse_op.show_all_product_filter(
                start, per_page, putaway, name=name, code=code, bar_code=bar_code, category_id=category_id)
        elif putaway is not None:
            data, total = HolaWareHouse_op.show_all_product_filter(
                start, per_page, putaway)
        else:
            data, total = HolaWareHouse_op.show_all_product_filter(
                start, per_page)

        return_data = jsonify({'code': 100,
                               'rows': data,
                               'total': total
                               })

        return tools.en_return_data(return_data)


class AllCategoryData(MethodView):

    def get(self):
        HolaWareHouse_op = HolaWareHouse()
        return_data = jsonify({'code': 100,
                               'products': HolaWareHouse_op.show_all_category()
                               })
        return tools.en_return_data(return_data)


class ProductCategoryAdd(MethodView):

    def post(self):
        return_data = jsonify({'code': 300})
        try:
            name = request.values.get('name', "")
            parent_id = request.values.get('parent_id', 0)
            parent_id = int(parent_id)
            if len(name):
                HolaWareHouse_op = HolaWareHouse()
                re, id = HolaWareHouse_op.add_category(parent_id, name)
                if re:
                    user = session['user']['id']
                    HolaWareHouse_op.add_operate_record(user, u'添加商品分类', id, u'商品分类')
                    return_data = jsonify({'code': 100})
                else:
                    return_data = jsonify({'code': 109})
        except Exception as e:
            print e
        return tools.en_return_data(return_data)


class ProductCategoryRename(MethodView):

    def post(self):
        return_data = jsonify({'code': 300})
        try:
            category_id = request.values.get('category_id', 0)
            name = request.values.get('name', "")
            if len(name):
                HolaWareHouse_op = HolaWareHouse()
                re = HolaWareHouse_op.category_rename(category_id, name)
                if re == 0:
                    user = session['user']['id']
                    HolaWareHouse_op.add_operate_record(user, u'重命名商品分类', category_id, u'商品分类')
                    return_data = jsonify({'code': ServiceCode.success})
                elif re == 1:
                    return_data = jsonify({'code': ServiceCode.duplicate, 'msg': u'重命名失败'})
                elif re == 2:
                    return_data = jsonify({'code': ServiceCode.check_error, 'msg': u'该分类禁止重命名'})
        except Exception as e:
            print e
        return tools.en_return_data(return_data)


class ProductCategoryDelete(MethodView):

    def post(self):
        return_data = jsonify({'code': 300})
        try:
            category_id = request.values.get('category_id', 0, type=int)

            if category_id == 0:
                raise CodeError(ServiceCode.params_error, u'所选分类不存在')

            HolaWareHouse_op = HolaWareHouse()
            # 用于提示信息
            category = HolaWareHouse_op.get_category_info(category_id)
            name = category['name'] if category is not None else u'空'
            re = HolaWareHouse_op.delete_category(category_id)
            if re == 1:
                raise CodeError(ServiceCode.exception_op, u'该分类下有子分类，无法删除')
            elif re == 2:
                raise CodeError(ServiceCode.exception_op, u'该分类下有商品，无法删除')
            elif re == 3:
                raise CodeError(ServiceCode.exception_op, u'找不到此分类信息')
            elif re == 4:
                raise CodeError(ServiceCode.exception_op, u'该分类禁止删除')
            else:
                user = session['user']['id']
                decribe = u'删除商品分类:[%s]' % name
                HolaWareHouse_op.add_operate_record(user, decribe, category_id, u'商品分类')

        except CodeError as e:
            return_data = jsonify(e.json_value())
        except Exception as e:
            print traceback.format_exc()
            return_data = jsonify(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败"})
        else:
            return_data = jsonify({'code': ServiceCode.success})
        finally:
            return tools.en_return_data(return_data)


class ProductShow(MethodView):

    def post(self):
        product_id = request.values.get('product_id', 0)
        HolaWareHouse_op = HolaWareHouse()
        return_data = jsonify({
            'code': 100,
            'data': HolaWareHouse_op.show_product(product_id)
        })
        return tools.en_return_data(return_data)


class ProductAdd(MethodView):

    def get(self):
        HolaWareHouse_op = HolaWareHouse()
        results = HolaWareHouse_op.show_all_category()
        from control_center.flagship_manage.flagship_info_manage.control.flagship_op import FlagShipOp
        fg_op = FlagShipOp()
        flagships = fg_op.get_all_flagship_info()
        flagship_data = [{'id': flagship.id, 'name': flagship.name}
                         for flagship in flagships]
        product_code = HolaWareHouse_op.get_product_desc_first()
        if product_code is None:
            product_code = 'SP%.6d' % 1
        else:
            product_code = 'SP%.6d' % (product_code.id + 1)

        return tools.en_render_template('shop_Management/addCommodity.html',
                                        results=json.dumps(results),
                                        flagship=json.dumps(flagship_data),
                                        product_code=product_code)

    def post(self):
        return_data = None
        try:
            product = {}
            category_id = request.values.get('category_id', 0)
            product['name'] = request.values.get('name', '')
            product['code'] = request.values.get('code', '')
            product['specification'] = request.values.get('specification', '')
            product['bar_code'] = request.values.get('bar_code', type=str)
            product['measure'] = request.values.get('measure', '')
            product['local_img'] = None
            product['img'] = request.values.get('img', '')
            product['unify_flg'] = bool(
                request.values.get(
                    'unify_flg', type=int))
            if not product['unify_flg']:
                product['flagship'] = request.values.get('flagship')
                flagship = json.loads(product['flagship'])
                if len(flagship) == 0:
                    raise CodeError(ServiceCode.params_error, u'旗舰店销售价格不能为空')
                for flagship_price in flagship:
                    if float(flagship_price['price']) < float(flagship_price['floor_price']):
                        raise CodeError(ServiceCode.params_error, u'旗舰店销售价格不能低于最低价')
                    if float(flagship_price['price']) < 1 or float(flagship_price['price']) > 999999999:
                        raise CodeError(ServiceCode.params_error, u'销售价请输入:1~999999999')
                    if float(flagship_price['floor_price']) < 1 or float(flagship_price['floor_price']) > 999999999:
                        raise CodeError(ServiceCode.params_error, u'最低价格请输入:1~999999999')

                product['flagship'] = flagship
                flagship_prices = sorted(flagship, key=sort_price)
                flagship_floor_prices = sorted(flagship, key=sort_floor_price)
                product['price_min'] = flagship_prices[0]['price']
                product['price_max'] = flagship_prices[-1]['price']
                product['floor_price_min'] = flagship_floor_prices[
                    0]['floor_price']
                product['floor_price_max'] = flagship_floor_prices[-1]['floor_price']
            else:
                product['price_min'] = request.values.get('price', None, type=float)
                product['price_max'] = request.values.get('price', None, type=float)
                product['floor_price_min'] = request.values.get('floor_price', None, type=float)
                product['floor_price_max'] = request.values.get('floor_price', None, type=float)
                if product['price_min'] is None:
                    raise CodeError(ServiceCode.params_error, u'全国统一销售价不能为空')
                if product['floor_price_max'] is None:
                    raise CodeError(ServiceCode.params_error, u'全国统一最低价不能为空')
                if float(product['price_max']) < float(product['floor_price_min']):
                    raise CodeError(ServiceCode.params_error, u'全国统一销售价格不能低于最低价')
                if float(product['price_max']) < 1 or float(product['price_max']) > 999999999:
                    raise CodeError(ServiceCode.params_error, u'销售价请输入:1~999999999')
                if float(product['floor_price_min']) < 1 or float(product['floor_price_min']) > 999999999:
                    raise CodeError(ServiceCode.params_error, u'最低价格请输入:1~999999999')

            product['remark'] = request.values.get('remark', '')
            product['weight'] = request.values.get('weight', type=float)
            product['putaway'] = bool(request.values.get('putaway', type=int))
            product['gift_flg'] = bool(request.values.get('gift_flg', type=int))

            print("-" * 80)
            print(product)
            print("-" * 80)
            #####
            # parameter check
            #####
            if product['name'] == '':
               raise CodeError(ServiceCode.params_error, u'商品名字不能为空')
            if product['code'] == '':
                raise CodeError(ServiceCode.params_error, u'商品编码不能为空')
            if category_id == 0:
                raise CodeError(ServiceCode.params_error, u'请选择商品类别')
            if product['bar_code'] == '':
                raise CodeError(ServiceCode.params_error, u'商品条码不能为空')
            if len(product['specification']) > 128:
                raise CodeError(ServiceCode.params_error, u'商品规格不能大于限定字符长度')
            if len(product['measure']) > 5:
                raise CodeError(ServiceCode.params_error, u'计量单位字数超过限制')
            ####
            # add product
            ####
            HolaWareHouse_op = HolaWareHouse()
            s, id = HolaWareHouse_op.add_product(category_id=category_id, product=product)
            if not s:
                raise CodeError(ServiceCode.update_error, u'保持数据失败')

            ###
            # add operate record
            ###
            user = session['user']['id']
            HolaWareHouse_op.add_operate_record(user, u'添加商品', id)
        except CodeError as e:
            return_data = jsonify(e.json_value())
        except Exception as e:
            print(traceback.format_exc())
            if 'product_upload_file' in session:
                session.pop('product_upload_file')
            return_data = jsonify(
                {'code': ServiceCode.service_exception, 'msg': u'服务器错误'})
        else:
            return_data = jsonify({'code': ServiceCode.success})
        finally:
            return tools.en_return_data(return_data)


# class ProductPicAdd(MethodView):
#
#     def post(self):
#         return_data = jsonify({'code': 300})
#         try:
#             state = pub_upload_picture_to_server()
#             if state:
#                 print "ProductPicAdd state =", state
#                 session['product_upload_file'] = state
#                 return_data = jsonify({'code': 100})
#             else:
#                 return_data = jsonify({'code': 112})
#         except Exception as e:
#             print e
#         return tools.en_return_data(return_data)


# class ProductPicDel(MethodView):
#
#     def post(self):
#         return_data = jsonify({'code': 300})
#         try:
#             if 'product_upload_file' in session:
#                 session.pop('product_upload_file')
#             return_data = jsonify({'code': 100})
#         except Exception as e:
#             print e
#         return tools.en_return_data(return_data)
#

class ProductEdit(MethodView):

    def get(self):
        id = request.values.get('id', type=int)
        HolaWareHouse_op = HolaWareHouse()
        results = HolaWareHouse_op.show_all_category()
        data = HolaWareHouse_op.get_product_all_flagship_price(id)

        return tools.en_render_template(
            'shop_Management/editCommodity.html',
            results=json.dumps(results),
            product=json.dumps(data))

    def post(self):
        return_data = jsonify({'code': 300})
        try:
            product = {}
            HolaWareHouse_op = HolaWareHouse()
            product['id'] = request.values.get('id', 0)
            product['category_id'] = request.values.get('category_id', 0)
            product['name'] = request.values.get('name', '')
            product['code'] = request.values.get('code', '')
            product['specification'] = request.values.get('specification', '')
            product['bar_code'] = request.values.get('bar_code', type=str)
            product['measure'] = request.values.get('measure', '')
            product['local_img'] = None
            product['img'] = request.values.get('img', '')
            print("img:", product['img'])
            product['unify_flg'] = bool(
                request.values.get(
                    'unify_flg', type=int))
            if not product['unify_flg']:
                product['flagship'] = request.values.get('flagship', None)
                flagship = json.loads(product['flagship'])

                flagship_temp = HolaWareHouse_op.get_product_price_by_id(product[
                                                                         'id'])
                if len(flagship) > 0:
                    # flagship是上传列表， flagship_temp是获取的内容
                    product['flagship'] = flagship
                    for temp in flagship_temp:
                        for flagship_simple in flagship:
                            if temp['id'] == long(flagship_simple['id']):
                                temp['price'] = float(flagship_simple['price'])
                                temp['floor_price'] = float(
                                    flagship_simple['floor_price'])
                                if temp['price'] < temp['floor_price']:
                                    raise CodeError(ServiceCode.params_error, u'旗舰店最低价不能大于销售价')
                                if temp['price'] < 1 or temp['price'] > 999999999:
                                    raise CodeError(ServiceCode.params_error, u'销售价格请输入:1~999999999')
                                if temp['floor_price'] < 1 or temp['floor_price'] > 999999999:
                                    raise CodeError(ServiceCode.params_error, u'最低价格请输入:1~999999999')

                product['flagship'] = flagship_temp

                flagship_prices = sorted(product['flagship'], key=sort_price)
                flagship_floor_prices = sorted(
                    product['flagship'], key=sort_floor_price)
                product['price_min'] = flagship_prices[0]['price']
                product['price_max'] = flagship_prices[-1]['price']
                product['floor_price_min'] = flagship_floor_prices[
                    0]['floor_price']
                product['floor_price_max'] = flagship_floor_prices[-1]['floor_price']

            else:
                product['price_min'] = request.values.get('price', None, type=float)
                product['price_max'] = request.values.get('price', None, type=float)
                product['floor_price_min'] = request.values.get('floor_price', None, type=float)
                product['floor_price_max'] = request.values.get('floor_price', None, type=float)
                if product['price_max'] is None:
                    raise CodeError(ServiceCode.params_error, u'全国统一销售价不能为空')
                if product['floor_price_max'] is None:
                    raise CodeError(ServiceCode.params_error, u'全国统一最低价不能为空')
                if float(product['price_max']) < float(product['floor_price_max']):
                    raise CodeError(ServiceCode.params_error, u'全国统一销售价不能低于最低价')
                if product['price_max'] < 1 or product['price_max'] > 999999999:
                    raise CodeError(ServiceCode.params_error, u'销售价格请输入:1~999999999')
                if product['floor_price_max'] < 1 or product['floor_price_max'] > 999999999:
                    raise CodeError(ServiceCode.params_error, u'最低价格请输入:1~999999999')

            product['remark'] = request.values.get('remark', '')
            product['weight'] = request.values.get('weight', type=float)
            product['putaway'] = bool(request.values.get('putaway', type=int))
            product['gift_flg'] = bool(request.values.get('gift_flg', type=int))
            #####
            # parameter check
            #####
            if product['name'] == '':
               raise CodeError(ServiceCode.params_error, u'商品名字不能为空')
            if product['code'] == '':
                raise CodeError(ServiceCode.params_error, u'商品编码不能为空')
            if product['category_id'] == 0:
                raise CodeError(ServiceCode.params_error, u'请选择商品类别')
            if product['bar_code'] == '':
                raise CodeError(ServiceCode.params_error, u'商品条码不能为空')
            if len(product['specification']) > 128:
                raise CodeError(ServiceCode.params_error, u'商品规格不能大于限定字符长度')
            if len(product['measure']) > 5:
                raise CodeError(ServiceCode.params_error, u'计量单位字数超过限制')
            # print("-" * 80)
            # print(product)
            # print("-" * 80)

            if not HolaWareHouse_op.Edit_product(product):
                raise CodeError(ServiceCode.update_error, u'更新失败')

            ###
            # add operate record
            ###
            user = session['user']['id']
            HolaWareHouse_op.add_operate_record(user, u'编辑商品', product['id'])

        except CodeError as e:
            return_data = jsonify(e.json_value())
        except Exception as e:
            print traceback.format_exc()
            return_data = jsonify(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败"})
        else:
            return_data = jsonify({'code': ServiceCode.success})
        finally:
            return tools.en_return_data(return_data)


# class ProductDelete(MethodView):
#
#     def post(self):
#         return_data = jsonify({'code': 300})
#         try:
#             product = {}
#             product['id'] = request.values.get('product_id', 0)
#             HolaWareHouse_op = HolaWareHouse()
#             re = HolaWareHouse_op.Delete_product(product)
#             if re:
#                 return_data = jsonify({'code': 100})
#             else:
#                 return_data = jsonify({'code': 109})
#         except CodeError as e:
#             return_data = jsonify(e.json_value())
#         except Exception as e:
#             print traceback.format_exc()
#             return_data = jsonify(
#                 {'code': ServiceCode.service_exception, 'msg': u"服务器失败"})
#         else:
#             return_data = jsonify({'code': ServiceCode.success})
#         finally:
#             return tools.en_return_data(return_data)


class ProductPutaway(MethodView):

    def post(self):
        return_data = None
        try:
            product = {}
            product['id'] = request.values.get('product_id', type=int)
            HolaWareHouse_op = HolaWareHouse()
            if HolaWareHouse_op.is_contain_set_meal(product['id']):
                raise CodeError(ServiceCode.check_error, u'该商品包含套餐中，请先移除该商品')

            if not HolaWareHouse_op.putaway_product(product):
                raise CodeError(ServiceCode.update_error, u'商品下架失败')

            user = session['user']['id']
            HolaWareHouse_op.add_operate_record(user, u'下架商品', product['id'])
        except CodeError as e:
            return_data = jsonify(e.json_value())
        except Exception as e:
            print(traceback.format_exc())
            return_data = jsonify(
                {'code': ServiceCode.service_exception, 'msg': u'服务器错误'})
        else:
            return_data = jsonify({'code': ServiceCode.success})
        finally:
            return tools.en_return_data(return_data)


class BatchProductPutaway(MethodView):
    """商品批量上架或下架数据接口"""

    def post(self):
        return_data = None
        try:
            product_id_list = request.values.get('product_id', None)
            putaway = bool(request.values.get('putaway', type=int))

            if product_id_list is None:
                raise CodeError(ServiceCode.params_error, u"请选择批量操作的商品")

            HolaWareHouse_op = HolaWareHouse()
            products = json.loads(product_id_list)

            if not isinstance(products, list):
                raise CodeError(ServiceCode.params_error, u"上送参数错误")

            status, msg = HolaWareHouse_op.is_contain_set_meal_for_batch(products)
            if not status:
                raise CodeError(ServiceCode.params_error, msg)

            if not HolaWareHouse_op.batch_putaway_product(products, putaway):
                raise CodeError(ServiceCode.update_error, u"更新状态失败")

            user = session['user']['id']
            for id  in product_id_list:
                HolaWareHouse_op.add_operate_record(user, u'批量下架商品', id)

        except CodeError as e:
            return_data = jsonify(e.json_value())
        except Exception as e:
            print traceback.format_exc()
            return_data = jsonify(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败"})
        else:
            return_data = jsonify({'code': ServiceCode.success})
        finally:
            return tools.en_return_data(return_data)


class VerifyInput(MethodView):
    def get(self):
        return_data = None
        field_value = request.values.get('field_value', None, type=str)
        input_type = request.values.get('input_type', None, type=int)

        if field_value is None:
            raise CodeError(ServiceCode.params_error, u'请上送栏位值')
        if input_type is None:
            raise CodeError(ServiceCode.params_error, u'请上送校验类型')

        try:
            HolaWareHouse_op = HolaWareHouse()
            if HolaWareHouse_op.verify_product_field_exist(input_type,field_value):
                if input_type == 1:
                    raise CodeError(ServiceCode.check_error, u'存在相同的商品编码')
                elif input_type == 2:
                    raise CodeError(ServiceCode.check_error, u'存在相同的商品条码')

        except CodeError as e:
            return_data = jsonify(e.json_value())
        except ValueError as e:
            return_data = jsonify({'code':ServiceCode.check_error, 'msg':u'上送类型不正确'})
        except Exception as e:
            print traceback.format_exc()
            return_data = jsonify(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败"})
        else:
            return_data = jsonify({'code': ServiceCode.success})
        finally:
            return tools.en_return_data(return_data)


class ProductOperateRecord(MethodView):
    def post(self):
        return_data = None
        try:
            page = request.values.get('page', 1, type=int)
            per_page = request.values.get('per_page', 10, type=int)
            id = request.values.get('id', None, type=int)
            operate_op = Operate_Op()
            HolaWareHouse_Op = HolaWareHouse()

            page = page - 1
            if page < 0:
                page = 0
            if per_page > 60:
                per_page = 60
            start = page * per_page

            operate_op.get_record(start,per_page, HolaWareHouse_Op.TABLENAME, id)
        except CodeError as e:
            return_data = jsonify(e.json_value())
        except ValueError as e:
            return_data = jsonify({'code':ServiceCode.check_error, 'msg':u'上送类型不正确'})
        except Exception as e:
            print traceback.format_exc()
            return_data = jsonify(
                {'code': ServiceCode.service_exception, 'msg': u"服务器失败"})
        else:
            return_data = jsonify({'code': ServiceCode.success})
        finally:
            return tools.en_return_data(return_data)


add_url.add_url(
    u"商品资料",
    'shop_manage.ShopManageView',
    add_url.TYPE_ENTRY,
    shop_manage_prefix,
    shop_manage,
    '/all_product_show/',
    'allproductshow',
    ProductView.as_view('allproductshow'),
    100,
    methods=['GET'])

add_url.add_url(
    u"商品类型添加",
    'shop_manage.allproductshow',
    add_url.TYPE_FEATURE,
    shop_manage_prefix,
    shop_manage,
    '/category_add/',
    'categoryadd',
    ProductCategoryAdd.as_view('categoryadd'),
    methods=['POST'])

add_url.add_url(
    u"商品类型删除",
    'shop_manage.allproductshow',
    add_url.TYPE_FEATURE,
    shop_manage_prefix,
    shop_manage,
    '/category_delete/',
    'categorydelete',
    ProductCategoryDelete.as_view('categorydelete'),
    methods=['POST'])

add_url.add_url(
    u"商品类型重命名",
    'shop_manage.allproductshow',
    add_url.TYPE_FEATURE,
    shop_manage_prefix,
    shop_manage,
    '/category_rename/',
    'categoryrename',
    ProductCategoryRename.as_view('categoryrename'),
    methods=['POST'])

add_url.add_url(
    u"查看商品",
    'shop_manage.allproductshow',
    add_url.TYPE_FEATURE,
    shop_manage_prefix,
    shop_manage,
    '/product_show/',
    'productshow',
    ProductShow.as_view('productshow'),
    methods=['POST'])

add_url.add_url(
    u"添加商品",
    'shop_manage.allproductshow',
    add_url.TYPE_FEATURE,
    shop_manage_prefix,
    shop_manage,
    '/product_add/',
    'productadd',
    ProductAdd.as_view('productadd'),
    methods=[
        'GET',
        'POST'])

# add_url.add_url(
#     u"添加商品图片",
#     'shop_manage.productadd',
#     add_url.TYPE_FEATURE,
#     shop_manage_prefix,
#     shop_manage,
#     '/product_add_pic/',
#     'productaddpic',
#     ProductPicAdd.as_view('productaddpic'),
#     methods=['POST'])

# add_url.add_url(
#     u"删除商品图片",
#     'shop_manage.productadd',
#     add_url.TYPE_FEATURE,
#     shop_manage_prefix,
#     shop_manage,
#     '/product_del_pic/',
#     'productdelpic',
#     ProductPicDel.as_view('productdelpic'),
#     methods=['POST'])

add_url.add_url(
    u"编辑商品",
    'shop_manage.allproductshow',
    add_url.TYPE_FEATURE,
    shop_manage_prefix,
    shop_manage,
    '/product_edit/',
    'productedit',
    ProductEdit.as_view('productedit'),
    methods=['GET', 'POST'])

# add_url.add_url(
#     u"删除商品",
#     'shop_manage.allproductshow',
#     add_url.TYPE_FEATURE,
#     shop_manage_prefix,
#     shop_manage,
#     '/product_delete/',
#     'productdelete',
#     ProductDelete.as_view('productdelete'),
#     methods=['POST'])

add_url.add_url(
    u"查看所有商品",
    'shop_manage.allproductshow',
    add_url.TYPE_FUNC,
    shop_manage_prefix,
    shop_manage,
    '/all_product_data/',
    'allproductdata',
    AllProductData.as_view('allproductdata'),
    methods=['GET'])

add_url.add_url(
    u"查看所有商品类型",
    'shop_manage.allproductshow',
    add_url.TYPE_FUNC,
    shop_manage_prefix,
    shop_manage,
    '/all_category_data/',
    'allcategorydata',
    AllCategoryData.as_view('allcategorydata'),
    methods=['GET'])

add_url.add_url(
    u"上架或者下架产品",
    'shop_manage.allproductshow',
    add_url.TYPE_FUNC,
    shop_manage_prefix,
    shop_manage,
    '/product_putaway/',
    'productputaway',
    ProductPutaway.as_view('productputaway'),
    methods=['POST'])

add_url.add_url(
    u"批量上架或下架",
    'shop_manage.allproductshow',
    add_url.TYPE_FUNC,
    shop_manage_prefix,
    shop_manage,
    '/batch_product_putaway/',
    'batch_productputaway',
    BatchProductPutaway.as_view('batch_productputaway'),
    methods=['POST']
)

add_url.add_url(
    u"验证商品输入栏位",
    'shop_manage.allproductshow',
    add_url.TYPE_FUNC,
    shop_manage_prefix,
    shop_manage,
    '/product_verify_input/',
    'product_verify_input',
    VerifyInput.as_view('product_verify_input'),
    methods=['GET']
)
#!/usr/bin/python
#-*- coding:utf-8 -*-
#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : shop_setmeal_view.py
#    作者   : WangYi
#  电子邮箱 : ywang@jmgo.com
#    日期   : 2016/9/8 17:28
#
#     描述  : 商品套餐视图类
#
import traceback

from flask import json, jsonify, request, session
from flask.views import MethodView
from config.service_config.returncode import ServiceCode
from control_center.flagship_manage.flagship_info_manage.control import flagship_op
from control_center.shop_manage.good_info_manage.control.mixOp import sort_price, sort_floor_price
from control_center.shop_manage.good_set_manage.control.setmealOp import SetMealOp
from public.exception.custom_exception import CodeError
from public.function import tools
from control_center.shop_manage import shop_manage, shop_manage_prefix
from control_center.admin import add_url


class SetMealView(MethodView):
    """
    进入超值套餐界面
    """

    def get(self):
        setmeal_op = SetMealOp()
        data, total = setmeal_op.getallsetmeal(0, 10)
        result = {
            'rows': data,
            'total': total
        }
        return tools.en_render_template(
            'shop_Management/valueMeals.html',
            results=json.dumps(result))

    def post(self):
        return_data = None
        try:
            page = request.values.get('page', 0, type=int)
            per_page = request.values.get('per_page', 10, type=int)

            setmeal_op = SetMealOp()
            page = page - 1
            if page < 0:
                page = 0
            if per_page > 60:
                per_page = 60
            start = page * per_page

            data, total = setmeal_op.getallsetmeal(start, per_page)
            return_data = {
                'code': ServiceCode.success,
                'rows': data,
                'total': total
            }
        except Exception as e:
            print(traceback.format_exc())
            return_data = {
                'code': ServiceCode.service_exception,
                'msg': u'服务器错误'}
        finally:
            return tools.en_return_data(jsonify(return_data))


class AddSetMeal(MethodView):
    """
    添加商品套餐界面和请求
    """

    def get(self):
        fg_op = flagship_op.FlagShipOp()
        flagships = fg_op.get_all_flagship_info()
        flagship_data = [{'id': flagship.id, 'name': flagship.name}
                         for flagship in flagships]
        return tools.en_render_template('shop_Management/addValueMeals.html',
                                        flagship=json.dumps(flagship_data))

    def post(self):
        return_data = None
        try:
            print("-" * 40 + "AddSetMeal [POST] " + "-" * 40)
            print("request.values:", request.values)
            product = {}
            product['name'] = request.values.get('name', '')
            product['description'] = request.values.get('description', '')
            product['img'] = request.values.get('img', '')
            product['unify_flg'] = bool(
                request.values.get(
                    'unify_flg', type=int))
            product['price'] = request.values.get('price', None, type=float)
            product['floor_price'] = request.values.get(
                'floor_price', None, type=float)

            flagships = request.values.get('flagship', None)
            goods_id = request.values.get('goods', None)

            if goods_id is None:
                raise CodeError(ServiceCode.params_error, u'必须添加商品')

            if not product['unify_flg'] and flagships is None:
                raise CodeError(ServiceCode.params_error, u'请填写旗舰店套餐价格')

            if not product['unify_flg']:
                product['flagship'] = json.loads(flagships)
                for flagship_price in product['flagship']:
                    if float(flagship_price['price']) < float(flagship_price['floor_price']):
                        raise CodeError(ServiceCode.params_error, u'旗舰店销售价格不能低于最低价')
                    if float(flagship_price['price']) < 1 or float(flagship_price['price']) > 999999999:
                        raise CodeError(ServiceCode.params_error, u'销售价格设置范围:1~999999999')
                    if float(flagship_price['floor_price']) < 1 or float(flagship_price['floor_price']) > 999999999:
                        raise CodeError(ServiceCode.params_error, u'最低价格设置范围:1~999999999')

                flagship_prices = sorted(
                    product['flagship'], key=sort_price)
                flagship_floor_prices = sorted(
                    product['flagship'], key=sort_floor_price)
                product['price_min'] = flagship_prices[0]['price']
                product['price_max'] = flagship_prices[-1]['price']
                product['floor_price_min'] = flagship_floor_prices[
                    0]['floor_price']
                product[
                    'floor_price_max'] = flagship_floor_prices[-1]['floor_price']
            else:
                product['price_min'] = request.values.get(
                    'price', None, type=float)
                product['price_max'] = request.values.get(
                    'price', None, type=float)
                product['floor_price_min'] = request.values.get(
                    'floor_price', None, type=float)
                product['floor_price_max'] = request.values.get(
                    'floor_price', None, type=float)
                if product['price_min'] is None :
                    raise CodeError(ServiceCode.params_error, u'请输入全国统一销售价格')
                elif product['floor_price_max'] is None:
                    raise CodeError(ServiceCode.params_error, u'请输入全国统一最低价格')
                if float(product['price_max']) < float(product['floor_price_min']):
                    raise CodeError(ServiceCode.params_error, u'全国统一销售价格不能低于最低价')
                if float(product['price_max']) < 1 or float(product['price_max']) > 999999999:
                    raise CodeError(ServiceCode.params_error, u'销售价请输入:1~9999999')
                if float(product['floor_price_min']) < 1 or float(product['floor_price_min']) > 999999999:
                    raise CodeError(ServiceCode.params_error, u'最低价格请输入:1~9999999')


            product['goods_id'] = json.loads(goods_id)
            if len(product['goods_id']) < 1:
                raise CodeError(ServiceCode.params_error, u'套餐中需包含商品,请选择商品')

            set_meal_op = SetMealOp()
            s, id = set_meal_op.add_set_meal(product)
            if not s:
                raise CodeError(ServiceCode.duplicate, u'保存数据失败')

            user = session['user']['id']
            set_meal_op.add_operate_record(user, u'添加套餐', id, u'商品套餐')

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


class EditSetMeal(MethodView):

    def get(self):
        set_meal_id = request.values.get('set_meal_id', None, type=int)
        set_meal_op = SetMealOp()
        status, results = set_meal_op.get_set_meal_detail(set_meal_id)
        return tools.en_render_template('shop_Management/editValueMeals.html',
                                        results=json.dumps(results))

    def post(self):
        return_data = None
        try:
            product = {}
            set_meal_op = SetMealOp()
            product['id'] = request.values.get('id', None, type=int)
            product['name'] = request.values.get('name', '')
            product['description'] = request.values.get('description', '')
            product['img'] = request.values.get('img', '')
            product['unify_flg'] = bool(request.values.get('unify_flg', type=int))
            product['price'] = request.values.get('price', None, type=float)
            product['floor_price'] = request.values.get( 'floor_price', None, type=float)
            flagships = request.values.get('flagship', None)
            goods_id = request.values.get('goods', None)
            ###
            # Check Parament
            ###
            if goods_id is None:
                raise CodeError(ServiceCode.params_error, u'请在套餐内添加商品')
            elif product['id'] is None:
                raise CodeError(ServiceCode.params_error, u'缺少套餐关键信息，请联系管理人员')
            elif product['name'] == '':
                raise CodeError(ServiceCode.params_error, u'请输入套餐名称')

            product['goods_id'] = json.loads(goods_id)

            if not product['unify_flg'] and flagships is not None:
                status ,flagship_temp = set_meal_op.get_set_meal_flagship_price(product['id'])
                flagship = json.loads(flagships)
                if len(flagship) > 0:
                    for temp in flagship_temp:
                        for flagship_simple in flagship:
                            if temp['flagship_id'] == long(flagship_simple['id']):
                                temp['price'] = float(flagship_simple['price'])
                                temp['floor_price'] = float(flagship_simple['floor_price'])
                                if temp['price'] < temp['floor_price']:
                                    raise CodeError(ServiceCode.params_error, u'旗舰店最低价不能大于销售价')
                                if temp['price'] < 1 or temp['price'] > 999999999:
                                    raise CodeError(ServiceCode.params_error, u'销售价请输入:1~999999999')
                                if temp['floor_price'] < 1 or temp['floor_price'] > 999999999:
                                    raise CodeError(ServiceCode.params_error, u'最低价格请输入:1~999999999')

                product['flagship'] = flagship_temp
                flagship_prices = sorted(flagship_temp, key=sort_price)
                flagship_floor_prices = sorted(
                    flagship_temp, key=sort_floor_price)
                product['price_min'] = flagship_prices[0]['price']
                product['price_max'] = flagship_prices[-1]['price']
                product['floor_price_min'] = flagship_floor_prices[0]['floor_price']
                product['floor_price_max'] = flagship_floor_prices[-1]['floor_price']

            else:
                product['price_min'] = request.values.get('price', None,type=float)
                product['price_max'] = request.values.get('price', None,type=float)
                product['floor_price_min'] = request.values.get(
                    'floor_price', None, type=float)
                product['floor_price_max'] = request.values.get(
                    'floor_price', None, type=float)
                if product['price_min'] is None or product['floor_price_max'] is None:
                    raise CodeError(ServiceCode.params_error, u'请输入价格')
                if float(product['price_max']) < float(product['floor_price_max']):
                    raise CodeError(ServiceCode.params_error, u'全国统一销售价不能低于最低价')
                if product['price'] < 1 or product['price'] > 999999999:
                    raise CodeError(ServiceCode.params_error, u'销售价请输入:1~999999999')
                if product['floor_price'] < 1 or product['floor_price'] > 999999999:
                    raise CodeError(ServiceCode.params_error, u'最低价格请输入:1~999999999')

            if not set_meal_op.edit_set_meal(product):
                raise CodeError(ServiceCode.params_error, u'编辑套餐失败')

            user = session['user']['id']
            set_meal_op.add_operate_record(user, u'编辑套餐', product['id'], u'商品套餐')
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


class DeleteSetMeal(MethodView):
    """
    删除套餐接口
    """

    def post(self):
        return_data = None
        try:
            set_meal_id = request.values.get('set_meal_id', None, type=int)

            if set_meal_id is None:
                raise CodeError(ServiceCode.params_error, u'请选择删除套餐')

            set_meal_op = SetMealOp()
            if not set_meal_op.delete_set_meal(set_meal_id):
                raise CodeError(ServiceCode.dealfaild, u'套餐删除失败')

            user = session['user']['id']
            set_meal_op.add_operate_record(user, u'套餐下架', set_meal_id, u'商品套餐')
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


add_url.add_url(
    u'超值套餐',
    'shop_manage.ShopManageView',
    add_url.TYPE_ENTRY,
    shop_manage_prefix,
    shop_manage,
    '/diplay_setmeal/',
    'display_setemal',
    SetMealView.as_view('display_setemal'),
    95,
    methods=['GET', 'POST']
)

add_url.add_url(
    u'添加套餐',
    'shop_manage.display_setemal',
    add_url.TYPE_FEATURE,
    shop_manage_prefix,
    shop_manage,
    '/setmeal_add/',
    'setmeal_add',
    AddSetMeal.as_view('setmeal_add'),
    methods=['GET', 'POST']
)

add_url.add_url(
    u'编辑套餐',
    'shop_manage.display_setemal',
    add_url.TYPE_FEATURE,
    shop_manage_prefix,
    shop_manage,
    '/setmeal_edit/',
    'setmeal_edit',
    EditSetMeal.as_view('setmeal_edit'),
    methods=['GET', 'POST']
)

add_url.add_url(
    u'删除套餐',
    'shop_manage.display_setemal',
    add_url.TYPE_FEATURE,
    shop_manage_prefix,
    shop_manage,
    '/setmeal_delete/',
    'setmeal_delete',
    DeleteSetMeal.as_view('setmeal_delete'),
    methods=['POST']
)

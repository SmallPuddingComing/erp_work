#-*-coding:utf-8 -*-

from flask import Blueprint
shop_manage_base = 'shop_manage'
shop_manage=Blueprint(shop_manage_base, __name__)
shop_manage_prefix='/shop'

import shop_info_manage
import good_info_manage
import good_set_manage
import shop_sale_statistics
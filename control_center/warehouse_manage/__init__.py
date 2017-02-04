#/usr/bin/python
#-*- coding:utf-8 -*-

from flask import Blueprint

warehouse_manage = Blueprint("warehouse_manage", __name__)
warehouse_manage_prefix = "/warehousemanage"

import base_view
import in_warehouse_manage
import warehouse_allocation_manage.view
import warehouse_out_manage
import real_time_inventory

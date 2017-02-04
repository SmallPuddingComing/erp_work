#-*- coding:utf-8 -*-
from flask import Blueprint
baseinfo_base = 'base_info'

baseinfo_prefix = '/baseinfo'
baseinfo = Blueprint('baseinfo', __name__, url_prefix=baseinfo_prefix)
# material_prefix = '/material'
# material = Blueprint('material', __name__, url_prefix=material_prefix)

import base_info.views
import material_manage.view
import supplier_manage.view
import bom_manage.view
import material_warehosue.view
import customer_manage.view

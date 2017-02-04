#/usr/bin/python
#-*- coding:utf-8 -*-

from flask import Blueprint

# flagship_manage = Blueprint('ship_manage',__name__)
# flagship_manage_prefix ='/index_t'

flagship_manage = Blueprint("flagship_manage", __name__)
flagship_manage_prefix = "/flagshipstoremanage"

import flagship_info_manage
import sale_manage
import warehouse_manage
import customer_service






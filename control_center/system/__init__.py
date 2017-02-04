#-*-coding:utf-8 -*-
from flask import Blueprint

sys = Blueprint('sys', __name__)
sys_prefix = '/sys'


import sys_view
import sys_account_view
import sys_organ_view
import sys_privilege_view
import sys_position_view
# import sys_product_category
# import sys_log_view

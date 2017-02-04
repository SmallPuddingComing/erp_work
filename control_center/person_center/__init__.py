#-*-coding:utf-8 -*-
from flask import Blueprint

personal = Blueprint('personal', __name__)
personal_prefix = '/personal'

import person_info_view
import person_view
import person_change_passwd
import person_wechat
# import person_sale_view


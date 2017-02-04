#-*-coding:utf-8 -*-
from flask import Blueprint

auth = Blueprint('auth', __name__)
auth_prefix = ''

import auth_view

#-*-coding:utf-8-*-
from flask import Blueprint

main = Blueprint('main', __name__)
main_prefix = '/main'


import index_views
import notice

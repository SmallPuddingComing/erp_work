#!/usr/bin/env python
#-*- coding:utf-8 -*-
#######################################################
#    Copyright(c) 2000-2013 JmGO Company
#    All rights reserved.
#    
#    文件名 :   __init__.py
#    作者   :   WangYi
#  电子邮箱 :   ywang@jmgo.com
#    日期   :   2016/08/24 17:34:49
#    
#    描述   :   蓝图注册与路由绑定
#
from flask import Blueprint

# material_prefix = '/material'
# material = Blueprint('material', __name__, url_prefix=material_prefix)


from . import catagory
from . import info
from . import attribute
# from . import attribute
# from . import info
import trash


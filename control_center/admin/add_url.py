#-*-coding:utf-8-*-

from flask import Blueprint

dict_url_name = {}

dict_flagship_url_name = {}


TYPE_ENTRY = 0          #导航
TYPE_FEATURE = 1        #按钮
TYPE_FUNC = 2           #函数


def add_url(name, father_endpoint, type, prefix, bp, rule, endpoint=None, view_func=None, priority=0, **options):

    global dict_url_name
    str_endpoint = bp.name + '.' + endpoint
    str_rule = prefix+rule
    dict_url_name[str_endpoint] = {'name': name,
                                   'url': str_rule,
                                   'father_endpoint': father_endpoint,
                                   'type': type,
                                   'priority': priority}

    return bp.add_url_rule(rule, endpoint, view_func, **options)



def flagship_add_url(name, father_endpoint, type, prefix, bp, rule, endpoint=None, view_func=None, priority=0, **options):

    global dict_flagship_url_name
    # print '*'*20
    str_endpoint = bp.name + '.' + endpoint
    str_rule = prefix+rule
    dict_flagship_url_name[str_endpoint] = {'name': name,
                                            'url': str_rule,
                                            'father_endpoint': father_endpoint,
                                            'type': type,
                                            'priority': priority}

    return bp.add_url_rule(rule, endpoint, view_func, **options)

def add_main_url(name, father_endpoint, type, prefix, bp, rule, endpoint=None, view_func=None, **options):
    str_endpoint = bp.name +'.' + endpoint
    str_rule = prefix+rule
    dict_flagship_url_name[str_endpoint]=  {'name': name, 'url': str_rule, 'father_endpoint': father_endpoint, 'type': type}
    return

def add_endpoint(dict_in, dict_out, self_key, list):
    father_endpoint = dict_in[self_key]['father_endpoint']
    if father_endpoint is None:
        if not dict_out.has_key(self_key):
            dict_out[self_key] = dict_in[self_key]
            item = {}
            item[self_key] = dict_in[self_key]
            list.append(item)
        return
    else:
        # print "self_key = " , self_key
        # print "father_endpoint = ", father_endpoint
        try:
            assert dict_in.has_key(father_endpoint)
        except AssertionError as e:
            print "self_key = " , self_key
            print "father_endpoint = ", father_endpoint
            raise
        add_endpoint(dict_in, dict_out, father_endpoint, list)
        if not dict_out.has_key(self_key):
            dict_out[self_key] = dict_in[self_key]
            item = {}
            item[self_key] = dict_in[self_key]
            list.append(item)


def init_urls():
    from  pprint import  pprint
    from control_center.admin.add_url import dict_url_name
    from data_mode.user_center.model.admin_url import AdminUrl
    from data_mode.user_center.control.mixOp import MixUserCenterOp
    db_seesion = MixUserCenterOp().get_seesion()

    dict_out = {}
    list_ep = []
    for k in dict_url_name:
        add_endpoint(dict_url_name, dict_out, k, list_ep)
    #pprint(list_ep)
    print "="*40
    for item in list_ep:
        for k in item:
            if k == "sys.delete_position":
                debug = 1
            try:
                temp = db_seesion.query(AdminUrl).filter(AdminUrl.endpoint == k).first()
                if temp is not None:
                    continue

                if item[k]['father_endpoint'] is None:
                    url = AdminUrl(url = item[k]['url'], name = item[k]['name'],
                                   type = item[k]['type'], endpoint=k)
                    db_seesion.add(url)
                    db_seesion.commit()
                    dict_out[k]['id'] = url.id
                else:
                    xx = item[k]['father_endpoint']
                    temp_url = db_seesion.query(AdminUrl).filter(AdminUrl.endpoint == xx).first()
                    url = AdminUrl(url = item[k]['url'], name = item[k]['name'],
                                   type = item[k]['type'], endpoint=k,
                                   parent_id=temp_url.id,
                                   priority=item[k]['priority'])
                    url.parent_id = temp_url.id
                    db_seesion.add(url)
                    db_seesion.commit()
                    dict_out[k]['id'] = url.id
                    print "add url to database : ", item[k]['name']
            except Exception, e:
                #print e
                db_seesion.rollback()
                continue
    add_flag_ship_url()


def add_flag_ship_url():
    from control_center.admin.add_url import dict_flagship_url_name
    from data_mode.user_center.model.admin_url import AdminUrl
    from data_mode.user_center.model.organ_department import OrganDepartMent
    from data_mode.user_center.control.mixOp import MixUserCenterOp
    from control_center.flagship_manage.flagship_info_manage.control.flagship_op import FlagShipOp
    from flask import url_for
    db_seesion = MixUserCenterOp().get_seesion()

    dict_out = {}
    list_ep = []
    for k in dict_flagship_url_name:
        add_endpoint(dict_flagship_url_name, dict_out, k, list_ep)

    print "="*40
    flagships = FlagShipOp()
    qijiandians = flagships.get_all_active_flagship_info()

    for qijiandian in qijiandians:
        for item in list_ep:
            for k in item:
                if k == "ship_manage.get_Product_Infos":
                    debug = 1
                try:
                    temp = db_seesion.query(AdminUrl).filter(AdminUrl.endpoint == k).first()
                    if temp is not None:
                        continue
                        
                    if item[k]['father_endpoint'] is None:
                        pass
                    else:
                        father_key = item[k]['father_endpoint']
                        father = dict_out[father_key]
                        father_url = None
                        url_name = item[k]['name']
                        url_type = item[k]['type']
                        if url_type == 0 and father['url'] == url_for('main.index'):
                            url_name = url_name + '( '+ qijiandian.name + ' )'
                            # url_name = url_name
                            father_url = father['url']
                        else:
                            father_url = url_for(father_key, flagshipid=qijiandian.id)

                        temp_url = db_seesion.query(AdminUrl).filter(AdminUrl.url == father_url).first()
                        url_args = url_for(k, flagshipid=qijiandian.id)
                        # url = AdminUrl(url = url_args, name = url_name,
                        #                type = item[k]['type'], endpoint=k,
                        #                parent_id=temp_url.id, addons_args=True,flagship_name=qijiandian.name,flagship_id=qijiandian.id)
                        url = AdminUrl(url = url_args, name = url_name,
                                       type = item[k]['type'], endpoint=k,
                                       parent_id=temp_url.id, addons_args=True,
                                       priority=item[k]['priority'])
                        db_seesion.add(url)
                        db_seesion.commit()
                        print "add url to database : ", url_name + '( '+ qijiandian.name + ' )'
                except Exception, e:
                    db_seesion.rollback()
                    continue

def update_urls():
    from  pprint import  pprint
    from control_center.admin.add_url import dict_url_name
    from data_mode.user_center.model.admin_url import AdminUrl
    from data_mode.user_center.control.mixOp import MixUserCenterOp
    db_seesion = MixUserCenterOp().get_seesion()

    dict_out = {}
    list_ep = []
    for k in dict_url_name:
        add_endpoint(dict_url_name, dict_out, k, list_ep)
    #pprint(list_ep)
    print "="*40
    for item in list_ep:
        for k in item:
            if k == "sys.delete_position":
                debug = 1
            try:
                if item[k]['father_endpoint'] is None:
                    pass
                else:
                    xx = item[k]['father_endpoint']
                    # print 'xx',xx
                    temp_url = db_seesion.query(AdminUrl).filter(AdminUrl.endpoint == xx).first()
                    # print 'temp_url',temp_url
                    update_url=db_seesion.query(AdminUrl).filter(AdminUrl.endpoint == k).first()
                    update_url.parent_id = temp_url.id
                    db_seesion.add(update_url)
                    db_seesion.commit()

                    # print "update url : ", item[k]['name']
            except Exception, e:
                #print e
                db_seesion.rollback()
                continue
    update_flag_ship_url()

def update_flag_ship_url():
    from control_center.admin.add_url import dict_flagship_url_name
    from data_mode.user_center.model.admin_url import AdminUrl
    from data_mode.user_center.model.organ_department import OrganDepartMent
    from data_mode.user_center.control.mixOp import MixUserCenterOp
    from control_center.flagship_manage.flagship_info_manage.control.flagship_op import FlagShipOp
    from flask import url_for
    db_seesion = MixUserCenterOp().get_seesion()

    dict_out = {}
    list_ep = []
    for k in dict_flagship_url_name:
        add_endpoint(dict_flagship_url_name, dict_out, k, list_ep)

    print "="*40
    flagships = FlagShipOp()
    qijiandians = flagships.get_all_active_flagship_info()

    for qijiandian in qijiandians:
        for item in list_ep:
            for k in item:
                if k == "ship_manage.get_Product_Infos":
                    debug = 1
                try:
                    if item[k]['father_endpoint'] is None:
                        pass
                    else:
                        father_key = item[k]['father_endpoint']
                        father = dict_out[father_key]
                        father_url = None
                        url_name = item[k]['name']
                        url_type = item[k]['type']
                        if url_type == 0 and father['url'] == url_for('main.index'):
                            url_name = url_name + '( '+ qijiandian.name + ' )'
                            # url_name = url_name
                            father_url = father['url']
                        else:
                            father_url = url_for(father_key, flagshipid=qijiandian.id)

                        temp_url = db_seesion.query(AdminUrl).filter(AdminUrl.url == father_url).first()

                        update_url=db_seesion.query(AdminUrl).filter(AdminUrl.endpoint == k,
                                                                     AdminUrl.url.like('%%flagshipid=%d'% (qijiandian.id))).first()
                        update_url.parent_id = temp_url.id
                        db_seesion.add(update_url)
                        db_seesion.commit()

                        print "update url to database : ", url_name + '( '+ qijiandian.name + ' )'
                except Exception, e:
                    db_seesion.rollback()
                    continue



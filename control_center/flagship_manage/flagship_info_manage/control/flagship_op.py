#-*-coding:utf-8-*-
import json

from sqlalchemy import func, or_, and_

from control_center.admin.add_url import add_flag_ship_url
from control_center.shop_manage.good_info_manage.control.mixOp import HolaWareHouse
from data_mode.hola_flagship_store.control_base.controlBase import ControlEngine
from data_mode.hola_flagship_store.mode.ship_model.flagship_clerk_info import Clerk
from data_mode.hola_flagship_store.mode.ship_model.flagship_store_info import FlagShipStoreInfo
from data_mode.hola_flagship_store.mode.ship_model.flagship_store_need import FlagShipStoreNeed
from data_mode.hola_flagship_store.mode.ship_model.flagship_store_show import FlagShipStoreShow
from data_mode.hola_flagship_store.mode.ship_model.flagship_store_show_check import FlagShipStoreShowCheck
from data_mode.user_center.control.mixOp import MixUserCenterOp



class FlagShipOp(ControlEngine):
    def __init__(self):
        ControlEngine.__init__(self)


    def add_flagship(self, flagship_info):
        try:
            user_op = MixUserCenterOp()
            name = user_op.get_department_name_byID(flagship_info['department_id'])

            flagship = FlagShipStoreInfo(name = name, area=flagship_info['area'], address=flagship_info['address'],
                                        telephone=flagship_info['telephone'], leader=flagship_info['user_id'], department_id=flagship_info['department_id'] )
            self.controlsession.add(flagship)
            self.controlsession.commit()
            warehouse_op = HolaWareHouse()
            warehouse_op.add_flagship_to_price(flagship.id)
            from control_center.shop_manage.good_set_manage.control.setmealOp import SetMealOp
            setmeal_op = SetMealOp()
            setmeal_op.add_flagship_to_setmeal_price(flagship.id)
            from control_center.admin.add_url import add_flag_ship_url
            add_flag_ship_url()
            return True
        except Exception, e:
            print e
            return False

    def edit_flagship(self, id, flagship_info):
        user_op = MixUserCenterOp()
        name = user_op.get_department_name_byID(flagship_info['department_id'])

        flagships = self.controlsession.query(FlagShipStoreInfo).filter(FlagShipStoreInfo.id == id).first()

        flagships.name = name
        flagships.area=flagship_info['area']
        flagships.address=flagship_info['address']
        flagships.telephone=flagship_info['telephone']
        flagships.leader=flagship_info['user_id']
        flagships.department_id=flagship_info['department_id']

        self.controlsession.add(flagships)
        self.controlsession.commit()
        self.controlsession.commit()

    def get_all_flagship_detail_info(self):
        flagships = self.controlsession.query(FlagShipStoreInfo).order_by(FlagShipStoreInfo.id).all()
        user_op = MixUserCenterOp()
        data = []
        for item in flagships:
            item_data = item.to_json()
            leader = item_data.pop('leader')
            # if leader != 0:
            #     user_info = user_op.get_user_info(leader)
            #     item_data['leader_name'] = user_info['name']
            #     item_data['leader_telphone'] = user_info['telephone']
            # else:
            #     item_data['leader_name'] = ""
            #     item_data['leader_telphone'] = ""
            leader_data = user_op.get_department_master(item.department_id)
            if leader_data is not None and leader_data.has_key('leader'):
                item_data['leader_name'] = leader_data['leader']['name']
                item_data['leader_telphone'] = leader_data['leader']['telephone']
            else:
                item_data['leader_name'] = ""
                item_data['leader_telphone'] = ""
            data.append(item_data)
        return data

    def get_all_flagship_detail_info_page(self, start, per_page, filter, sou):
        #flagships = self.controlsession.query(FlagShipStoreInfo).order_by(FlagShipStoreInfo.id).all()
        flagships = None
        total = 0
        if len(filter):
            filters =  str(filter).split(',')
            if len(filters)==1:
                filter1 = "%" + filters[0] + "%"
                flagships = self.controlsession.query(FlagShipStoreInfo).filter(FlagShipStoreInfo.area.like(filter1)
                            ).order_by(FlagShipStoreInfo.id).limit(per_page).offset(start)
                total = self.controlsession.query(func.count(FlagShipStoreInfo.id)).filter(FlagShipStoreInfo.area.like(filter1)
                            ).scalar()
            if len(filters)==2:
                filter1 = "%" + filters[0] + "%"
                filter2 = "%" + filters[1] + "%"
                flagships = self.controlsession.query(FlagShipStoreInfo).filter(and_(FlagShipStoreInfo.area.like(filter1),
                            FlagShipStoreInfo.area.like(filter2))).order_by(FlagShipStoreInfo.id).limit(per_page).offset(start)
                total = self.controlsession.query(func.count(FlagShipStoreInfo.id)).filter(and_(FlagShipStoreInfo.area.like(filter1),
                            FlagShipStoreInfo.area.like(filter2))).scalar()
            if len(filters)==3:
                filter1 = "%" + filters[0] + "%"
                filter2 = "%" + filters[1] + "%"
                filter3 = "%" + filters[2] + "%"
                flagships = self.controlsession.query(FlagShipStoreInfo).filter(and_(FlagShipStoreInfo.area.like(filter1),
                            FlagShipStoreInfo.area.like(filter2),
                            FlagShipStoreInfo.area.like(filter3))).order_by(FlagShipStoreInfo.id).limit(per_page).offset(start)
                total = self.controlsession.query(func.count(FlagShipStoreInfo.id)).filter(and_(FlagShipStoreInfo.area.like(filter1),
                            FlagShipStoreInfo.area.like(filter2),
                            FlagShipStoreInfo.area.like(filter3))).scalar()
        if len(sou):
            sou = "%" + sou + "%"
            flagships = self.controlsession.query(FlagShipStoreInfo).filter(or_(FlagShipStoreInfo.name.like(sou),
                        FlagShipStoreInfo.address.like(sou))).order_by(FlagShipStoreInfo.id).limit(per_page).offset(start)
            total = self.controlsession.query(func.count(FlagShipStoreInfo.id)).filter(or_(FlagShipStoreInfo.name.like(sou),
                        FlagShipStoreInfo.address.like(sou))).scalar()
        if not len(filter) and not len(sou):
            flagships = self.controlsession.query(FlagShipStoreInfo).order_by(FlagShipStoreInfo.id).limit(per_page).offset(start)
            total = self.controlsession.query(func.count(FlagShipStoreInfo.id)).scalar()
        user_op = MixUserCenterOp()
        data = []
        for item in flagships:
            item_data = item.to_json()
            leader = item_data.pop('leader')
            if leader != 0:
                user_info = user_op.get_user_info(leader)
                item_data['leader_name'] = user_info['name']
                item_data['leader_telphone'] = user_info['telephone']
            else:
                item_data['leader_name'] = ""
                item_data['leader_telphone'] = ""
            data.append(item_data)
        return data, total

    def get_flagship_count(self):
        total = self.controlsession.query(func.count(FlagShipStoreInfo.id)).scalar()
        return total


    def get_all_flagship_info(self):
        flagships = self.controlsession.query(FlagShipStoreInfo).order_by(FlagShipStoreInfo.id).all()
        return flagships

    def get_all_active_flagship_info(self):
        flagships = self.controlsession.query(FlagShipStoreInfo).filter(FlagShipStoreInfo.open == True).all()
        return flagships

    def get_all_flagship_dict_info(self):
        flagships = self.controlsession.query(FlagShipStoreInfo).order_by(FlagShipStoreInfo.id).all()
        items = [(item.id,item.to_json()) for item in flagships]
        return dict(items)

    def stop_flagship_business(self, id):
        flagships = self.controlsession.query(FlagShipStoreInfo).filter(FlagShipStoreInfo.id == id).first()
        user_op = MixUserCenterOp()


        flagships.open = not flagships.open
        self.controlsession.add(flagships)
        self.controlsession.commit()
        if not flagships.open:
            user_op.delete_flagshipurl(id)
        else:
            add_flag_ship_url()

        return flagships

    def is_flagship_do_business(self, id):
        flagships = self.controlsession.query(FlagShipStoreInfo).filter(FlagShipStoreInfo.id == id).first()
        return flagships.open

    def show_flagships(self):
        flagships = self.controlsession.query(FlagShipStoreInfo).order_by(FlagShipStoreInfo.id).all()
        data = []
        user_op = MixUserCenterOp()
        for ship in flagships:
            ship_data = ship.to_json()
            leader = ship_data.pop('leader')
            # if leader != 0:
            #     user_info = user_op.get_user_info(leader)
            #     ship_data['leader_name'] = user_info['name']
            #     ship_data['leader_telphone'] = user_info['telephone']
            # else:
            #     ship_data['leader_name'] = ""
            #     ship_data['leader_telphone'] = ""
            leader_data = user_op.get_department_master(ship.department_id)
            if leader_data is not None and leader_data.has_key('leader'):
                ship_data['leader_name'] = leader_data['leader']['name']
                ship_data['leader_telphone'] = leader_data['leader']['telephone']
            else:
                ship_data['leader_name'] = ""
                ship_data['leader_telphone'] = ""

            ship_data['examples'] = 0
            if len(ship.flagship_show) :
                ship_data['show'] = ship.flagship_show[0].to_json()
            else:
                ship_data['show'] = {
                    'id' : None,
                    'picture': None,
                    'add_time': None,
                }

            if len(ship.flagship_show_check):
                ship_data['show_check'] = ship.flagship_show_check[0].to_json()
            else:
                ship_data['show_check'] ={
                    'id' : None ,
                    'check_time': None,
                    'check_statu': (0 < len(ship.flagship_show)) and 1 or 0 ,
                    'check_comment': "",
                    'check_user': ""
                }
            data.append(ship_data)

        example_show = self.controlsession.query(FlagShipStoreShow).order_by(FlagShipStoreShow.id).first()
        show_data = None
        if example_show is not None:
            show_data = example_show.to_json()

        example_data = {
            'id' : None,
            'name': u"坚果旗舰店门店展示示例",
            'area': u"广东, 深圳, 南山",
            'address': u"广东科兴科学苑8楼",
            'telephone': "18688888888",
            'open': 1,
            'leader_name': u"老胡",
            'leader_telphone': "18688888888",
            'show': show_data,
            'show_check': {
                'id' : None ,
                'check_time': None,
                'check_statu': (show_data is not None) and 1 or 0 ,
                'check_comment': "",
                'check_user': ""
            },
            'examples': 1
        }
        data.append(example_data)
        return data

    def show_flagships_example_pictures(self):
        data  = {}
        examples_show = self.controlsession.query(FlagShipStoreShow).filter(FlagShipStoreShow.examples == True).all()
        data['show'] = [ example.to_json() for example in examples_show]
        needs = self.controlsession.query(FlagShipStoreNeed).order_by(FlagShipStoreNeed.id).first()
        if needs is not None:
            data['needs'] = needs.examples_need
        else:
            data['needs'] = ""
            data['show_check'] = {
                    'id' : None ,
                    'check_time': None,
                    'check_statu': (0 < len(data['show'])) and 1 or 0 ,
                    'check_comment': "",
                    'check_user': ""
        }
        return data

    def show_flagships_example_needs(self):
        needs = self.controlsession.query(FlagShipStoreNeed).order_by(FlagShipStoreNeed.id).first()
        if needs is None:
            return ""
        return needs.examples_need


    def show_flagships_pictures(self, flagshipid):
        data = {}
        flagship = self.controlsession.query(FlagShipStoreInfo).filter(FlagShipStoreInfo.id == flagshipid).first()
        shows = flagship.flagship_show

        #data['show'] = [ show.to_json() for show in shows]
        data['show'] = []
        data['update_time'] = None
        for show_data in shows:
            data['show'].append(show_data.to_json())
            if data['update_time'] is not None:
                if show_data.add_time > data['update_time']:
                    data['update_time'] = show_data.add_time
            else:
                data['update_time'] = show_data.add_time   #.strftime("%Y-%m-%d %H:%M:%S"),
        if data['update_time'] is not None:
            data['update_time'] = data['update_time'].strftime("%Y-%m-%d %H:%M:%S")

        user_op = MixUserCenterOp()
        flagship_info = flagship.to_json()
        leader = flagship_info.pop('leader')
        # user_info = user_op.get_user_info(leader)
        # flagship_info['leader_name'] = user_info['name']
        # flagship_info['leader_telphone'] = user_info['telephone']

        leader_data = user_op.get_department_master(flagship.department_id)
        if leader_data is not None and leader_data.has_key('leader'):
            flagship_info['leader_name'] = leader_data['leader']['name']
            flagship_info['leader_telphone'] = leader_data['leader']['telephone']
        else:
            flagship_info['leader_name'] = ""
            flagship_info['leader_telphone'] = ""

        data['info'] = flagship_info
        data['show_checks'] = []
        checks = flagship.flagship_show_check
        data['check_statu'] = (0 < len(data['show'])) and 1 or 0
        check_time = None
        for check in checks:
            check_data = check.to_json()
            uid = check_data.pop('check_user_id')
            check_data['check_user'] = user_op.get_user_simple_info(uid)
            data['show_checks'].append(check_data)
            if check_time is not None:
                if check.check_time> check_time:
                    check_time = check.check_time
                    data['check_statu'] = check.check_statu
            else:
                check_time = check.check_time
                data['check_statu'] = (0 < len(data['show'])) and 1 or 0
        return data

    def get_flagship_checkstatu(self, flagshipid):
        print "flagship id is: " ,flagshipid
        flagship = self.controlsession.query(FlagShipStoreInfo).filter(FlagShipStoreInfo.id == flagshipid).first()
        checks = flagship.flagship_show_check
        shows = flagship.flagship_show
        check_statu = 0
        for show in shows:
            check_statu = 1
            break
        check_time = None
        for check in checks:
            if check_time is not None:
                if check.check_time> check_time:
                    check_time = check.check_time
                    check_statu = check.check_statu
            else:
                check_time = check.check_time
        picture = ""
        show_check = flagship.flagship_show
        if show_check is not None and len(show_check):
            picture = show_check[0].picture

        return check_statu, picture

    def edit_example_need(self, etext):
        needs = self.controlsession.query(FlagShipStoreNeed).order_by(FlagShipStoreNeed.id).first()
        if needs is None:
            needs = FlagShipStoreNeed(examples_need=etext)
        else:
            needs.examples_need = etext
        self.controlsession.add(needs)
        self.controlsession.commit()

    def add_example_picture(self, picture, local_picture):
        examples_show = FlagShipStoreShow(examples = True)
        examples_show.picture = picture
        examples_show.local_picture = local_picture
        self.controlsession.add(examples_show)
        self.controlsession.commit()


    def edit_example_picture(self, show_id, picture, local_picture):
        examples_show = self.controlsession.query(FlagShipStoreShow).filter(FlagShipStoreShow.id == show_id).first()
        examples_show.picture = picture
        examples_show.local_picture = local_picture
        self.controlsession.add(examples_show)
        self.controlsession.commit()

    def delete_example_picture(self, show_id):
        examples_show = self.controlsession.query(FlagShipStoreShow).filter(FlagShipStoreShow.id == show_id).first()
        self.controlsession.delete(examples_show)
        self.controlsession.commit()

    def modify_check(self, flagshipid, check_statu, uid, comment):
        flagship = self.controlsession.query(FlagShipStoreInfo).filter(FlagShipStoreInfo.id == flagshipid).first()
        flagship_show_check = FlagShipStoreShowCheck(flagship_id=flagshipid, check_statu=check_statu, check_user_id=uid, check_comment=comment)
        self.controlsession.add(flagship_show_check)
        self.controlsession.commit()

    def add_show_picture(self, flagshipid, picture, local_picture):
        flagship_show = FlagShipStoreShow(flagship_id = flagshipid, picture=picture, local_picture=local_picture)
        self.controlsession.add(flagship_show)
        self.controlsession.commit()

    def edit_show_picture(self, show_id, picture, local_picture):
        flagship_show = self.controlsession.query(FlagShipStoreShow).filter(FlagShipStoreShow.id == show_id).first()
        flagship_show.picture = picture
        flagship_show.local_picture = local_picture
        self.controlsession.add(flagship_show)
        self.controlsession.commit()

    def get_flagship_users(self, flagship_id):
        flagship = self.controlsession.query(FlagShipStoreInfo).filter(FlagShipStoreInfo.id == flagship_id).first()
        department_id = flagship.department_id
        user_op = MixUserCenterOp()
        #user_data = user_op.get_dict_users_info_by_department(department_id)
        user_data = user_op.get_list_users_info_by_department(department_id)
        return user_data

    def get_flagship_dict_users(self, flagship_id):
        flagship = self.controlsession.query(FlagShipStoreInfo).filter(FlagShipStoreInfo.id == flagship_id).first()
        department_id = flagship.department_id
        user_op = MixUserCenterOp()
        user_data = user_op.get_dict_users_info_by_department(department_id)
        #user_data = user_op.get_list_users_info_by_department(department_id)
        return user_data


    def get_commission_amount_by_product_id_user(self, user_id, product_id):
        object = self.controlsession.query(Clerk).filter(Clerk.user_id == user_id, Clerk.product_id==product_id).first()
        if not object:
            return 0
        return object.commission_amount

    def get_flagship_info_by_flagship_id(self, flagship_id):
        rs = self.controlsession.query(FlagShipStoreInfo).filter(FlagShipStoreInfo.id == flagship_id).first()
        if rs:
            return rs.to_json()
        else:
            return {}

    def get_dict_user_info(self, name, flagship_id):
        flagship = self.controlsession.query(FlagShipStoreInfo).filter(FlagShipStoreInfo.id == flagship_id).first()
        department_id = flagship.department_id
        user_op = MixUserCenterOp()
        user_data = user_op.get_dict_users_info_by_department(department_id)
        users_info_one = user_op.get_dict_user_info(name)
        data = {}
        for user_id in users_info_one:
            if user_data.has_key(user_id):
                data[user_id] = users_info_one[user_id]
        return data

    def get_all_flagship_store(self):
        """
        return all flagship_store
        :return: dict
        """
        flagship_stores = self.controlsession.query(FlagShipStoreInfo.id, FlagShipStoreInfo.name).all()
        result = {}
        for flagship in flagship_stores:
            if result.get(flagship[0]) is None:
                result[flagship[0]] = flagship[1]

        return result

if __name__ == '__main__':
    fs = FlagShipOp()
    print json.dumps(fs.get_flagship_info_by_flagship_id(6))


#!/usr/bin/python
# -*- coding:utf-8 -*-

#    Copyright(c) 2015-2016 JmGo Company
#    All rights reserved.
#
#    文件名 : ecn_op.py
#    作者   : tangjinxing
#    日期   : 2016年12月2日10:59:13
#     描述  : ECN 管理 op
#
import datetime
import time
from flask import session
from sqlalchemy import and_, func
from public.exception.custom_exception import CodeError
from config.service_config.returncode import ServiceCode
from data_mode.erp_supply.control_base.controlBase import ControlEngine
from data_mode.erp_supply.mode.material_manage_mode.material_baseinfo import MaterialBaseInfo
from data_mode.erp_supply.mode.material_manage_mode.bom_relation_info import BomRelationInfo
from data_mode.erp_supply.mode.material_manage_mode.ecn_baseinfo import EcnBaseinfo
from data_mode.erp_supply.mode.material_manage_mode.ecn_principal import EcnPrincipal
from data_mode.erp_supply.mode.material_manage_mode.ecn_record import EcnRecord
from redis_cache.supply_cache.control.bom_op import RedisBomOp, split
from data_mode.user_center.control.mixOp import MixUserCenterOp
from data_mode.erp_supply.base_op.bom_base_op import migrate_bom_history_data, updateFatherMaterialInfo, \
    updateChildMaterialInfo
from config.share.share_define import (COVERT_WASTEUNIT_TYPE_NUMBER,
                                       COVERT_DATA_TO_WASTEUNIT_NUMBER)
from data_mode.erp_supply.base_op.material_op.baseinfo_op import Baseinfo_Op


class EcnManageOp(ControlEngine):
    """
    ECN 管理 数据接口
    """

    def __init__(self):
        """
        控制引擎初始化
        :return:
        """
        ControlEngine.__init__(self)

    @staticmethod
    def get_create_ecn_info():
        """
        获取创建ecn所需数据
        :return:
        """
        from data_mode.user_center.model.admin_user import AdminUser
        r_data = {}
        prin_list = []
        r_data["ecn_code"] = "ECN"+datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        r_data["create_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if session["user"]["work_number"] is None:
            work_number = "001"
        else:
            work_number = session["user"]["work_number"]
        r_data["create_user"] = work_number + " " + session["user"]["name"]
        op = MixUserCenterOp()
        sql = """
        SELECT user_id
        FROM admin_user_group, admin_group_url, admin_url
        where admin_url.endpoint='baseinfo.EcnCreateView' and
        admin_group_url.url_id = admin_url.id  and admin_user_group.group_id=admin_group_url.group_id;
        """
        result = op.controlsession.execute(sql).fetchall()
        super_result = op.controlsession.query(AdminUser.id).filter(AdminUser.is_superuser)
        if result is None:
            r_data["principal_list"] = []
        else:
            temp_list = [x[0] for x in result] + [x[0] for x in super_result]
            rs_user = op.controlsession.query(AdminUser).filter(AdminUser.id.in_(temp_list))
            for item in rs_user:
                item_dict = dict()
                item_dict["principal_list_id"] = item.id
                item_dict["name"] = item.work_number + " " + \
                    item.name if item.work_number is not None else "001 " + item.name
                prin_list.append(item_dict)
            r_data["principal_list"] = prin_list
        return r_data

    def get_bom_info(self, page, per_page, key=None, value=None, exist_bom_id_list=None):
        """
        选择Bom
        :param page:
        :param per_page:
        :param key:
        :param value:
        :param exist_bom_id_list:
        :return:
        """
        r_data = []
        try:
            start = (page-1)*per_page
            condition = and_()
            condition.append(MaterialBaseInfo.bom_code.isnot(None))
            if value is not None and value is not u"" and value is not "":
                if key == 0:
                    condition.append(MaterialBaseInfo.bom_code == value)
                if key == 1:
                    condition.append(MaterialBaseInfo.name == value)
            if exist_bom_id_list is not None:
                condition.append(MaterialBaseInfo.id.notin_(exist_bom_id_list))

            rs = self.controlsession.query(MaterialBaseInfo).filter(condition).limit(per_page).offset(start).all()
            total = self.controlsession.query(func.count(MaterialBaseInfo.id)).filter(condition).scalar()
            if rs:
                for item in rs:
                    js_data = item.to_bomandmaterial_json()
                    item_dict = dict()
                    item_dict["bom_id"] = js_data["id"]
                    item_dict["bom_code"] = js_data["bom_code"]
                    item_dict["material_name"] = js_data["material_name"]
                    old_version = js_data["bom_version"]
                    item_dict["old_version"] = old_version
                    new_version = old_version[0] + str(int(old_version[1::])+1)
                    item_dict["bom_version"] = new_version
                    item_dict["specification"] = js_data["material_model"]
                    r_data.append(item_dict)

        except CodeError:
            raise
        except EcnManageOp:
            raise
        return r_data, total

    def get_material_info(self, page, per_page, bom_id, exist_id_list, function_type, key=None, value=None):
        """
        :param page
        :param per_page
        :param bom_id:
        :param exist_id_list:
        :param function_type:
        :param key
        :param value
        :return:
        """
        r_data = []
        total = 0
        try:
            op_b = Baseinfo_Op()
            if len(exist_id_list):
                exist_id_list = [int(item) for item in exist_id_list]
            op_rds = RedisBomOp()
            parent_id_list = op_rds.get_bom_parent_list(bom_id)
            son_id_list = op_rds.get_bom_detail(bom_id)
            start = (page-1)*per_page
            # 添加新物料
            if function_type == 0:
                m_id_list = []
                condition = and_()
                for item in son_id_list:
                    m_id, level = split(item)
                    if level == 1:
                        m_id_list.append(m_id)
                m_id_list += parent_id_list
                m_id_list.append(bom_id)
                if value is not None and value is not u"" and value is not "":
                    if key == 0:
                        condition.append(MaterialBaseInfo.code == value)
                    if key == 1:
                        condition.append(MaterialBaseInfo.name == value)
                condition.append(MaterialBaseInfo.id.notin_(m_id_list+exist_id_list))
                rs_m = self.controlsession.query(MaterialBaseInfo).filter(condition).limit(per_page).offset(start).all()
                total = self.controlsession.query(func.count(MaterialBaseInfo.id)).filter(condition).scalar()
                for m_item in rs_m:
                    item_dict = dict()
                    item_dict["material_id"] = m_item.id
                    item_dict["material_code"] = m_item.code
                    item_dict["material_name"] = m_item.name
                    item_dict["material_specification"] = m_item.specifications
                    item_dict["material_attribute"] = op_b.get_attribute_name(m_item.attribute_id)
                    item_dict['material_unit'] = m_item.measureunit
                    item_dict["material_dosage"] = ""
                    item_dict["material_waste_rate"] = ""
                    item_dict["bit_number"] = ""
                    item_dict["material_change"] = ""
                    r_data.append(item_dict)

            if function_type == 1 or function_type == 2:
                m_id_list = []
                condition = and_()
                for item in son_id_list:
                    m_id, level = split(item)
                    if m_id not in exist_id_list and level == 1:
                        m_id_list.append(m_id)
                if value is not None and value is not u"" and value is not "":
                    if key == 0:
                        condition.append(MaterialBaseInfo.code == value)
                    if key == 1:
                        condition.append(MaterialBaseInfo.name == value)

                condition.append(MaterialBaseInfo.id.in_(m_id_list))
                condition.append(BomRelationInfo.material_id == MaterialBaseInfo.id)
                condition.append(BomRelationInfo.parent_id == bom_id)

                rs_m = self.controlsession.query(MaterialBaseInfo.id,
                                                 MaterialBaseInfo.code,
                                                 MaterialBaseInfo.name,
                                                 MaterialBaseInfo.specifications,
                                                 MaterialBaseInfo.attribute_id,
                                                 MaterialBaseInfo.measureunit,
                                                 BomRelationInfo.number,
                                                 BomRelationInfo.wasterate,
                                                 BomRelationInfo.usedsite).\
                    filter(condition).group_by(MaterialBaseInfo.id).limit(per_page).offset(start).all()

                total = self.controlsession.query(func.count(MaterialBaseInfo.id)).filter(condition).scalar()
                for r_item in rs_m:
                    item_dict = dict()
                    item_dict["material_id"] = r_item[0]
                    item_dict["material_code"] = r_item[1]
                    item_dict["material_name"] = r_item[2]
                    item_dict["material_specification"] = r_item[3]
                    item_dict["material_attribute"] = op_b.get_attribute_name(r_item[4])
                    item_dict['material_unit'] = r_item[5]
                    item_dict["material_dosage"] = r_item[6]
                    item_dict["material_waste_rate"] = int(r_item[7])/COVERT_DATA_TO_WASTEUNIT_NUMBER
                    item_dict["bit_number"] = r_item[8] if r_item[8] is not None else ""
                    item_dict["material_change"] = ""
                    r_data.append(item_dict)

        except CodeError:
            raise
        except Exception:
            raise
        return r_data, total

    def get_all_principal_info(self):

        rs_principal = self.controlsession.query(EcnPrincipal).group_by(EcnPrincipal.principal_user_id).all()
        r_data = [item.to_json() for item in rs_principal]

        return r_data

    @staticmethod
    def get_principal_info():
        """
        获取所有联系人信息
        :return:
        """
        r_data = []
        try:
            from data_mode.user_center.model.admin_user import AdminUser
            op = MixUserCenterOp()
            sql = """
            SELECT user_id
            FROM admin_user_group, admin_group_url, admin_url
            where admin_url.endpoint='baseinfo.EcnCreateView' and
            admin_group_url.url_id = admin_url.id  and admin_user_group.group_id=admin_group_url.group_id;
            """
            result = op.controlsession.execute(sql).fetchall()
            super_result = op.controlsession.query(AdminUser.id).filter(AdminUser.is_superuser)
            if result is None:
                r_data = []
            else:
                temp_list = [x[0] for x in result] + [x[0] for x in super_result]
                rs_user = op.controlsession.query(AdminUser).filter(AdminUser.id.in_(temp_list))
                for item in rs_user:
                    item_dict = dict()
                    item_dict["id"] = item.id
                    item_dict["content"] = item.work_number + " " + \
                        item.name if item.work_number is not None else "001 " + item.name
                    r_data.append(item_dict)
        except Exception:
            raise
        return r_data

    def get_ecn_info(self, page, per_page, ecn_id=None, e_code=None, principal_id=None):
        """
        获取ECN记录信息
        :param page:
        :param per_page:
        :param ecn_id:
        :param e_code:
        :param principal_id:
        :return:
        """
        r_data = []
        try:

            start = per_page*(page-1)
            condition = and_()

            if e_code is not None:
                condition.append(EcnBaseinfo.code == e_code)
            if ecn_id is not None:
                condition.append(EcnBaseinfo.id == ecn_id)
            if principal_id is not None:
                condition.append(EcnBaseinfo.id == EcnPrincipal.ecn_id)
                condition.append(EcnPrincipal.principal_user_id == principal_id)
            rs = self.controlsession.query(EcnBaseinfo).filter(condition).limit(per_page).offset(start).all()
            total = self.controlsession.query(func.count(EcnBaseinfo.id)).filter(condition).scalar()
            op_user = MixUserCenterOp()
            for item in rs:
                js_data = item.to_json()
                condition_principal = and_()
                item_dict = dict()
                item_dict["id"] = js_data["id"]
                item_dict["code"] = js_data["code"]
                item_dict["create_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(js_data["create_time"]))
                rs_uer = op_user.get_user_info(js_data["create_user_id"])
                item_dict["create_user"] = rs_uer["name"]
                item_dict["contain_bom_num"] = js_data["contain_bom_num"]
                item_dict["change_reason"] = js_data["change_reason"]
                item_dict["principal"] = ""
                condition_principal.append(EcnPrincipal.ecn_id == js_data["id"])
                r_pric = self.controlsession.query(EcnPrincipal).filter(condition_principal).all()
                for pric_item in r_pric:
                    pric_data = pric_item.to_json()
                    item_dict["principal"] += str(pric_data["name"])+";"
                r_data.append(item_dict)
            pass
        except CodeError:
            raise
        except Exception:
            raise
        return r_data, total

    def get_ecn_detail_search(self, page, per_page, ecn_id, bom_id, key=None, value=None):
        """
        获取ecn变更的物料信息
        :param ecn_id:
        :param bom_id:
        :param page:        当前页数
        :param per_page:    每页记录数
        :param key:         0-物料代码  1-物料名称
        :param value:       搜索值
        :return:
        """
        r_data = []
        try:
            start = per_page*(page-1)
            condition = and_()
            condition.append(EcnRecord.ecn_id == ecn_id)
            condition.append(EcnRecord.parent_material_id == bom_id)
            condition.append(MaterialBaseInfo.id == EcnRecord.material_id)
            op_b = Baseinfo_Op()
            if value is not None and value is not u"" and value is not "":
                if key == 0:
                    condition.append(MaterialBaseInfo.code == value)
                if key == 1:
                    condition.append(MaterialBaseInfo.name == value)

            rs_detail = self.controlsession.query(EcnRecord.material_id,
                                                  MaterialBaseInfo.code,
                                                  MaterialBaseInfo.name,
                                                  MaterialBaseInfo.specifications,
                                                  MaterialBaseInfo.attribute_id,
                                                  MaterialBaseInfo.measureunit,
                                                  EcnRecord.material_num,
                                                  EcnRecord.waste_rate,
                                                  EcnRecord.bit_number,
                                                  EcnRecord.change_describe).\
                filter(condition).group_by(EcnRecord.material_id).limit(per_page).offset(start).all()

            total = self.controlsession.query(func.count(EcnRecord.material_id)).filter(condition).scalar()

            for m_detail in rs_detail:
                detail_dict = dict()
                detail_dict["material_code"] = m_detail[1]
                detail_dict["material_name"] = m_detail[2]
                detail_dict["material_specification"] = m_detail[3]
                detail_dict["material_attribute"] = op_b.get_attribute_name(m_detail[4])
                detail_dict["material_unit"] = m_detail[5]
                detail_dict["material_dosage"] = m_detail[6]
                detail_dict["material_waste_rate"] = int(m_detail[7])/COVERT_DATA_TO_WASTEUNIT_NUMBER
                detail_dict["material_bit_number"] = m_detail[8]
                detail_dict["material_change"] = m_detail[9]
                r_data.append(detail_dict)

            pass
        except CodeError:
            raise
        except EcnRecord:
            raise
        return r_data, total

    def get_ecn_detail_info(self, ecn_id):
        """
        根据ecn_id获取ECN明细
        :param ecn_id:
        :return:
        """
        r_data = {}
        try:
            bom_list = []
            r_ecn = self.get_ecn_info(1, 10, ecn_id)
            if r_ecn:
                r_data = r_ecn[0][0]

            rs = self.controlsession.query(EcnRecord.parent_material_id, EcnRecord.version).\
                filter(EcnRecord.ecn_id == ecn_id).\
                group_by(EcnRecord.parent_material_id).all()
            for item in rs:
                item_dict = dict()
                item_dict["bom_id"] = item[0]
                item_dict["bom_version"] = item[1]
                rs_bom = self.controlsession.query(MaterialBaseInfo).filter(MaterialBaseInfo.id == item[0]).first()
                if rs_bom:
                    item_dict["bom_name"] = rs_bom.name
                    item_dict["bom_code"] = rs_bom.bom_code
                else:
                    raise CodeError(ServiceCode.service_exception, u"物料查询失败")
                rows, total = self.get_ecn_detail_search(1, 10, ecn_id, item[0])
                item_dict["rows"] = rows
                item_dict["total"] = total
                bom_list.append(item_dict)
            r_data["data"] = bom_list
            pass
        except EcnPrincipal:
            raise
        return r_data

    def save_ecn_info(self, ecn_base_info, prin_list, data):
        """
        ecn信息保存
        :param ecn_base_info:        ecn基础信息
            "ecn_code"
            "create_time"
            "create_user"
            "change_reason"
        :param prin_list: 联系人id list
        :param data:       #修改的BOM子物料信息

        :return:
        """
        e_code = ecn_base_info["ecn_code"]
        try:
            c_time = int(time.time())
            change_reason = ecn_base_info["change_reason"]
            user_id = session["user"]['id']
            # EcnBaseinfo表插入记录
            ecn_id = self.controlsession.query(EcnBaseinfo.id).order_by(EcnBaseinfo.id.desc()).first()
            ecn_id = ecn_id[0] + 1 if ecn_id is not None else 1
            ecn_base_obj = EcnBaseinfo(id=ecn_id, code=e_code, create_time=c_time,
                                       create_user_id=user_id, change_reason=change_reason, contain_bom_num=len(data))
            self.controlsession.add(ecn_base_obj)

            op_user = MixUserCenterOp()
            for item in prin_list:
                user_info = op_user.get_user_info(item)
                if user_info:
                    if not user_info["work_number"]:
                        user_info["work_number"] = "0"
                    name = user_info['work_number'] + " " + user_info["name"]
                else:
                    raise CodeError(ServiceCode.service_exception, u"保存失败")
                # EcnPrincipal表插入记录
                prin_obj = EcnPrincipal(ecn_id=ecn_id, principal_user_id=item, name=name)
                self.controlsession.add(prin_obj)
            self.controlsession.commit()
        except CodeError:
            self.controlsession.rollback()
            raise
        except Exception:
            self.controlsession.rollback()
            raise
        # 防止重复提交 分两次try
        try:
            sync_dict = []
            for b_item in data:
                updata_id_list = []
                temp_dict = {
                    'bom_id': int(b_item["bom_id"]),
                    'version': b_item["bom_version"],
                    'create_time': c_time,
                    'child': []
                }
                bom_id = int(b_item["bom_id"])
                bom_version = b_item["bom_version"]

                for m_item in b_item["detail_data"]:
                    if m_item["material_dosage"] is u"" or m_item["material_dosage"] is "":
                        m_item["material_dosage"] = None
                    temp_temp_dict = {
                        'id': int(m_item["material_id"]),
                        'number': m_item["material_dosage"],
                        'wasterate': m_item["material_waste_rate"],
                        'pos': m_item["bit_number"],
                        'deal_type': int(m_item["function_type"])
                    }
                    temp_dict['child'].append(temp_temp_dict)
                    m_id = int(m_item["material_id"])
                    # 物料用量参数判断
                    if m_item["material_dosage"] is u"" \
                            or m_item["material_dosage"] is None \
                            or m_item["material_dosage"] is "":

                        raise CodeError(ServiceCode.service_exception, u"物料用量不能为空")
                    m_num = m_item["material_dosage"]
                    # 损耗率参数判断
                    if m_item["material_waste_rate"] is u"" \
                            or m_item["material_waste_rate"] is None \
                            or m_item["material_waste_rate"] is "":

                        raise CodeError(ServiceCode.service_exception, u"损耗率不能为空")

                    waste_rate = float(m_item["material_waste_rate"])
                    bit_number = m_item["bit_number"]

                    change_describe = m_item["material_change"]
                    operate = int(m_item["function_type"])

                    if operate == 1:
                        del_dict = dict()
                        del_dict["id"] = m_id
                        del_dict["operate_type"] = 1
                        rs = self.controlsession.query(BomRelationInfo).filter(
                                BomRelationInfo.parent_id == bom_id,
                                BomRelationInfo.material_id == m_id).first()

                        if rs is None:
                            raise CodeError(ServiceCode.service_exception, u"修改bom_id: %d下m_id: %d" % (bom_id, m_id))
                        elif rs.number == int(m_num) and \
                            rs.wasterate == waste_rate*COVERT_WASTEUNIT_TYPE_NUMBER and \
                                rs.usedsite == bit_number:
                            raise CodeError(
                                    ServiceCode.service_exception,
                                    u"修改bom_id: %d下m_id: %d 未做修改" % (bom_id, m_id))
                        else:
                            temp_str = ""
                            if rs.number != int(m_num):
                                temp_str = "物料用量从%d变更为%s  " % (rs.number, m_num)
                            if rs.wasterate != waste_rate*COVERT_WASTEUNIT_TYPE_NUMBER:
                                temp_str += "损耗率从%.4f变更为%s  " % (rs.wasterate/COVERT_DATA_TO_WASTEUNIT_NUMBER,
                                                                        m_item["material_waste_rate"])
                            if rs.usedsite != bit_number:
                                temp_str += "位号从%s变更为%s  " % (rs.usedsite, bit_number)

                            change_describe = temp_str

                    updata_id_list.append(m_id)
                    # EcnRecord表插入记录el
                    record_obj = EcnRecord(ecn_id=ecn_id, parent_material_id=bom_id, material_id=m_id,
                                           version=bom_version, material_num=m_num,
                                           waste_rate=(waste_rate*COVERT_WASTEUNIT_TYPE_NUMBER),
                                           bit_number=bit_number, change_describe=change_describe)
                    record_obj.deal_type = operate
                    self.controlsession.add(record_obj)
                sync_dict.append(temp_dict)
            sync_bom_info(db_session=self.controlsession, ecn_id=ecn_id, sync_dict=sync_dict)
            self.controlsession.commit()
        except CodeError:
            self.controlsession.rollback()
            r_obj = self.controlsession.query(EcnBaseinfo).filter_by(code=e_code).first()
            prin_obj = self.controlsession.query(EcnPrincipal).filter_by(ecn_id=r_obj.id).all()
            if r_obj:
                self.controlsession.delete(r_obj)
            for prin_item in prin_obj:
                self.controlsession.delete(prin_item)
            self.controlsession.commit()
            raise
        except Exception:
            self.controlsession.rollback()
            r_obj = self.controlsession.query(EcnBaseinfo).filter_by(code=e_code).first()
            prin_obj = self.controlsession.query(EcnPrincipal).filter_by(ecn_id=r_obj.id).all()
            if r_obj:
                self.controlsession.delete(r_obj)
            for prin_item in prin_obj:
                self.controlsession.delete(prin_item)
            raise


def sync_bom_info(db_session, ecn_id, sync_dict=None):
    """
    将ECN的变更同步到BOM中。
    :param db_session: sqlalchemy.orm.session.Session
    :param ecn_id: int ECN单据的ID
    :param sync_dict: dict 如果没上送此结构,则根据ECN_ID的ECN_record进行BOM同步
    sync_dict结构:
        [      {
                  'bom_id': 1,
                  'create_time': int 时间戳,
                  'code': str BOM
                  'version': 'V2',
                  'child':[{
                               'id': 物料ID,
                               'number': 物料用量,
                               'wasterate': 损耗率,
                               'pos': 位号,
                               'deal_type': 操作类型, 0 -- 添加 1--修改 2--删除
                               }],
                  ...
                }
        }]
    :return:
    """
    import time
    from sqlalchemy.orm.session import Session
    if not isinstance(db_session, Session):
        raise TypeError("db_session must be sqlalchemy.orm.session.Session. %s" % type(db_session))
    elif not isinstance(ecn_id, (int, long)):
        raise TypeError("ecn_id must be int or long. %s" % type(ecn_id))
    elif sync_dict is not None and not isinstance(sync_dict, list):
        raise TypeError("sync_dict must be list. %s" % type(sync_dict))

    if sync_dict is None:
        # 获取ECN记录
        pass
    else:
        #######
        # 采用sync_dict进行结构同步
        #######
        index = 0
        for bom_dict in sync_dict:
            if not isinstance(bom_dict, dict):
                raise TypeError("sync_dict's value must be dict. %s" % type(bom_dict))

            if not all([bom_dict.get('version'),
                        bom_dict.get('bom_id'),
                        bom_dict.get('create_time'),
                        bom_dict.get('child')]):
                raise KeyError("""sync_dict[%d] record must have key:
                               version, bom_id, create_time, child. you keys:%s""" % (index, bom_dict.keys()))

            # sync_list = []
            bom_id = bom_dict.get('bom_id')
            create_time = bom_dict.get('create_time')
            version = bom_dict.get('version')

            if int(version[1::]) - 1 > 0:
                old_version = version[0] + str(int(version[1::]) - 1)
            else:
                raise ValueError("Bom_ID:%d version value has Error. value:%s" % (bom_id, bom_dict.get('version')))
            ###
            # 更新旧版本
            ###
            migrate_bom_history_data(db_session, bom_id, old_version)

            ###
            # 更新新版本信息
            ###
            bom_instance = db_session.query(MaterialBaseInfo).filter(MaterialBaseInfo.id == bom_id).first()
            if bom_instance is None:
                raise ValueError("not found bom infomation.")

            info_dict = dict()
            info_dict["pid"] = bom_id
            info_dict["code"] = bom_instance.bom_code
            info_dict["bom_rem"] = bom_instance.bom_rem if bom_instance.bom_rem is not None else ""
            info_dict["bom_version"] = version
            info_dict["bom_category_id"] = bom_instance.bom_category_id
            updateFatherMaterialInfo(db_session, info_dict)
            ###
            # 更新BOM关系
            ###
            time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(create_time))
            updateChildMaterialInfo(db_session, time_str, int(bom_id), version, bom_dict.get('child'))


if __name__ == "__main__":

    import os
    root = os.getcwd()

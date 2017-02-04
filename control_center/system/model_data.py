#-*-coding:utf-8-*-


from data_mode.user_center.model.organ_company import OrganCompany

def get_organ_data(disable_positions = False, disable_users = False, disable_groups = False):
    from data_mode.user_center.control.mixOp import MixUserCenterOp
    db_seesion = MixUserCenterOp().get_seesion()
    companys = db_seesion.query(OrganCompany).order_by(OrganCompany.id)
    data_companys = []
    for company in companys:
        data_company = company.to_json()
        departMents = company.departments
        data_company['departMents'] = []
        for departMent in departMents:
            data_departMent = departMent.to_json()
            if not disable_positions:
                data_departMent['positions'] = []
                positions = departMent.positions
                for position in positions:
                    data_postion = position.to_json()
                    if not disable_users:
                        data_postion['users'] = []
                        users = position.users
                        for user in users:
                            if not user.is_active:
                                continue
                            data_user = user.to_json()
                            groups = user.groups
                            if not disable_groups:
                                data_user['groups'] = [group.to_json() for group in groups]
                            data_postion['users'].append(data_user)
                        parttime_users = position.parttime_users
                        for parttime_user in parttime_users:
                            if not parttime_user.is_active:
                                continue
                            data_user = parttime_user.to_json()
                            groups = parttime_user.groups
                            if not disable_groups:
                                data_user['groups'] = [group.to_json() for group in groups]
                            data_postion['users'].append(data_user)
                    data_departMent['positions'].append(data_postion)
            data_company['departMents'].append(data_departMent)
        data_companys.append(data_company)
    return data_companys

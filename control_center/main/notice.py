#-*-coding:utf-8-*-

from flask import session
from flask import jsonify
from flask import json
from flask.views import MethodView
from flask import  request, url_for,redirect
from sqlalchemy import or_, not_,and_

from sqlalchemy import func
import time
from datetime import datetime
from control_center.admin import add_url

from data_mode.user_center.model.admin_url import AdminUrl

from data_mode.user_center.model.organ_company import OrganCompany
from data_mode.user_center.model.organ_department import OrganDepartMent
from data_mode.user_center.control.mixOp import MixUserCenterOp

from public.function import tools
from pprint import pprint
from data_mode.erp_base.control.messageOp import MessageOperation
from data_mode.erp_base.control.messageOp import UserMessageRecord
from data_mode.erp_base.model.messageModel import ContentType
from data_mode.erp_base.model.messageModel import FlagType,FinishType,StateType

from data_mode.erp_base.control.messageOp import MessageContent,MessageAttachment
from public.send.reqrep.client import pub_send_message


from public.upload_download.upload_download import pub_upload_attachment_to_server
from public.upload_download.upload_download import pub_upload_attachment_to_qiniu

import traceback

from pprint import pprint
from datetime import datetime
from flask import g



import sys

reload(sys)
sys.setdefaultencoding('utf8')

class NoticeManagerView(MethodView):
    def get(self):
        return tools.en_render_template('notifies/notifymgr.html')


class NoticeDataView(MethodView):
    def get(self):
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        if per_page > 60:
            per_page = 60

        # uId = request.args.get('userId',2,type=int)

        try:

            uId = session['user']['id']
            flag = request.args.get('flag', 0, type=int)
            return_data = jsonify({'code': 300})

            op = MessageOperation()
            db_session = op.get_seesion()

            # 获取数据总数量
            if(flag==-1): #查询所有通知总数

                total = db_session.query(func.count(MessageContent.id)).filter(and_(MessageContent.fromUserId==uId,MessageContent.contentType==ContentType.infomation,
                                                                                    MessageContent.flag.in_([2,5]))).scalar()
            elif (flag == -2): #查询所有报警总数
                total = db_session.query(func.count(MessageContent.id)).filter(
                    and_(MessageContent.fromUserId == uId, MessageContent.contentType == ContentType.infomation,
                         MessageContent.flag.in_([FlagType.warning,FlagType.alarm_red,FlagType.alarm_orange]))).scalar()

            else:
                total = db_session.query(func.count(MessageContent.id)).filter(
                    and_(MessageContent.fromUserId == uId, MessageContent.flag == flag,
                         MessageContent.contentType == ContentType.infomation)).scalar()

            #获取分页数据
            start = (page - 1) * per_page
            list = op.getMessageList(uId,per_page,start,flag,ContentType.infomation)

            return_data = jsonify({'code': 100,
                                   'data': list,
                                   'count': total
                                   })

        except Exception, e:
            print e
            return_data = jsonify({'code': 112,
                                   'data': [],
                                   'count': 0,
                                   'msg':str(e)
                                   })


        return tools.en_return_data(return_data)


class NoticeManagerDelete(MethodView):
    def get(self):
        return_data = jsonify({'code': 300})
        try:
            id = request.args.get('id')
            op = MessageOperation()
            code = op.deleteMessageById(id)

            return_data = jsonify({'code': code})
        except Exception,e:
            traceback.format_exc()
            pprint(e)
        return tools.en_return_data(return_data)



class NoticeManagerPublish(MethodView):
    def get(self):
        code = 300
        return_data = jsonify({'code': code})
        try:
            id = request.args.get('id',-1,int)
            state = request.args.get('state',-1,int)

            if(id==-1):
                return_data = jsonify({'code': 101})
                return tools.en_return_data(return_data)

            if(state ==0 or state ==1):
                op = MessageOperation()
                code = op.upMessageState(id, state)


            return_data = jsonify({'code': code})
        except Exception,e:
            traceback.format_exc()
            pprint(e)
        return tools.en_return_data(return_data)


class NoticeDetailView(MethodView):
    def get(self):
        id = request.args.get('id', -1, int)

        op = MessageOperation()
        data = op.getMessageById(id)
        list = data.recordList
        dictList = []
        ids = []
        for record in list:
            dictList.append(record.obj2dict())
            ids.append(record.UserId)

        userOp = MixUserCenterOp()
        userList = userOp.getUserNameByListId(ids)
        names = ''
        for user in userList:
            names = names+' '+user.name
        #print (' NoticeDetailDataView %s  %s ' % (userList,names))

        #获取附件信息
        attach = data.attachments
        attachList = ''
        if(attach!=None):
            attachIds = attach.split(',')
            attachList = op.getAttachmentByIds(attachIds)


        listDict = []
        for at in attachList:
            listDict.append(at.obj2dict())

        jsonAttachList = json.dumps(listDict)

        dict = {}

        dict["id"] = data.id
        dict["topic"] = data.topic
        dict["fromUserId"] = data.fromUserId
        dict["busType"] = data.busType
        dict["content"] = data.content
        dict["flag"] = data.flag
        dict["contentType"] = data.contentType
        dict["addTime"] = data.addTime
        dict["records"] = dictList
        dict["sendUsers"] = names

        ltime = time.localtime(data.addTime)
        timeStr = time.strftime("%Y-%m-%d %H:%M:%S", ltime)

        return tools.en_render_template('notifies/notify-detail.html', data=data, timeStr=timeStr,
                                        attachList=jsonAttachList, sendList=names)


class NoticeUpdateDetailDataView(MethodView):
    def get(self):
        code = 300
        return_data = jsonify({'code': code})
        try:
            id = request.args.get('id', -1, int)
            flag = request.args.get('flag',-1,int)

            op = MessageOperation()

            if (id == -1):
                return_data = jsonify({'code': 101})
                return tools.en_return_data(return_data)

            if (flag != -1):
                if (flag == 2):
                    code = op.upMessageFlag(id,2)
                elif(flag == 5): #标记重要
                    code = op.upMessageFlag(id,5)
                else:
                    return_data = jsonify({'code': 101})
                    return tools.en_return_data(return_data)

            data = op.getMessageById(id)

            dict = {}

            dict["id"] = data.id
            dict["topic"] = data.topic
            dict["fromUserId"] = data.fromUserId
            dict["busType"] = data.busType
            dict["content"] = data.content
            dict["flag"] =  data.flag
            dict["contentType"] = data.contentType
            dict["addTime"] = data.addTime

            return_data = jsonify({
                'code': code,
                'data':json.dumps(dict)
            })



        except Exception, e:
            traceback.format_exc()
            pprint(e)


        return tools.en_return_data(return_data)

class NoticeReadAction(MethodView):
        def get(self):
            code = 300
            return_data = jsonify({'code': code})
            try:
                id = request.args.get('id', -1, int)
                isFinish = request.args.get('isFinish', -1, int)
                userId = session['user']['id']
                op = MessageOperation()


                if (id == -1):
                    return_data = jsonify({'code': 101})
                    return tools.en_return_data(return_data)

                if (isFinish != -1):
                    if (isFinish == 1): # 标记已读
                        bool = op.up_user_record(userId=userId,msgId=id, isFinished=1)
                        if bool:
                            code=100
                    elif (isFinish == 0):
                        bool = op.up_user_record(userId=userId,msgId=id, isFinished=0)
                        if bool:
                            code=100
                    else:
                        return_data = jsonify({'code': 101})
                        return tools.en_return_data(return_data)

                data = op.getMessageById(id)

                dict = {}

                dict["id"] = data.id
                dict["topic"] = data.topic
                dict["fromUserId"] = data.fromUserId
                dict["busType"] = data.busType
                dict["content"] = data.content
                dict["flag"] = data.flag
                dict["contentType"] = data.contentType
                dict["addTime"] = data.addTime

                return_data = jsonify({
                    'code': code,
                    'data': json.dumps(dict)
                })



            except Exception, e:
                traceback.format_exc()
                pprint(e)

            return tools.en_return_data(return_data)





# 创建通知 kangwx
class NoticeCreate(MethodView):
    def post(self):

        return_data = jsonify({'code': 300})
        msg = ''
        try:
            op = MessageOperation()
            uId = session['user']['id']
            topic = request.values.get('topic')
            content = request.values.get('content')
            attachments = request.values.get('filelist')

            flag = request.values.get('flag')
            if flag is None: #普通通知
                flag = 2
            contentType = 2 #消息
            addTime = time.time()
            strUserId = request.values.get('listUserId')
            # print(strUserId)
            listUserId = strUserId.split(',')

            # pprint(" attach: %s"%attachments)

            busType = 1
            state = 1
            result = pub_send_message(uId, listUserId, [], topic, busType, flag, contentType, content, state, attachments)
            # print(result)
            if(result[0]):
                return_data = jsonify({'code': 100})
                code = 100
            else:
                code = 300
                return_data = jsonify({'code': 300, 'msg':result})
        except Exception,e:

            print traceback.format_exc()
            msg = str(e)
            code = 300

        return_data = jsonify({'code': code,'msg':msg})

        return tools.en_return_data(return_data)

    def get(self):

        return_data = jsonify({'code': 300})
        try:

            uId = session['user']['id']
            topic = request.values.get('topic')
            content = request.values.get('content')
            flag = request.values.get('flag')
            contentType = 2 #消息
            addTime = time.time()
            strUserId = request.values.get('listUserId')
            listUserId = json.loads(strUserId)
            busType = 1
            result = pub_send_message(uId, listUserId, [], topic,busType, flag, contentType, content)
            # print(result)
            if(result[0]):
                return_data = jsonify({'code': 100})
            else:
                return_data = jsonify({'code': 300})
        except Exception,e:
            print(e)

        return tools.en_return_data(return_data)

#最新通知
class NewNoticeView(MethodView):
    def get(self):
        return tools.en_render_template('notifies/notifies.html')

class NewNoticeDetail(MethodView):

    def get(self):
        try:
            id = request.args.get('msgId', -1, int)
            recordId = request.args.get('id',-1,int)

            op = MessageOperation()
            data = op.getMessageById(id)
            list = data.recordList
            dictList = []
            ids = []
            recordFlag = 0
            isFinished = 0
            recordTime = 0
            for record in list:
                # pprint(record)
                dictList.append(record.obj2dict())
                ids.append(record.UserId)
                recordFlag = record.flag
                isFinished = record.isFinished
                recordTime = record.addTime
                if(recordId==record.id):
                    record.isFinished = 1
                    op.updateRecordReadByid(recordId, 1)



            userOp = MixUserCenterOp()
            userList = userOp.getUserNameByListId(ids)
            names = ''
            for user in userList:
                names = names + ' ' + user.name

            # 获取附件信息
            attach = data.attachments
            attachList = ''
            if (attach != None):
                attachIds = attach.split(',')
                attachList = op.getAttachmentByIds(attachIds)


            listDict = []
            for at in attachList:
                listDict.append(at.obj2dict())
            jsonAttachList = json.dumps(listDict)


            dict = {}

            dict["id"] = recordId
            dict["topic"] = data.topic
            dict["fromUserId"] = data.fromUserId
            dict["busType"] = data.busType
            dict["content"] = data.content
            dict["contentType"] = data.contentType
            dict["records"] = dictList
            dict["sendUsers"] = names

            dict["flag"] = recordFlag
            dict["addTime"] = recordTime

            ltime = time.localtime(data.addTime)
            timeStr = time.strftime("%Y-%m-%d %H:%M:%S", ltime)
        except Exception, e:
            print e

        return tools.en_render_template('notifies/mynotify-detail.html', data=dict, timeStr=timeStr, sendList=names, attachList=jsonAttachList)

#获取消息接口 kangwx
#flagtype 2-通知  4-警报  5-严重 -1 全部通知
class UserNoticeDataView(MethodView):
    def get(self):
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        if per_page > 60:
            per_page = 60


        try:
            return_data = jsonify({'code': 300})
            uId = session['user']['id']
            flag = request.args.get('flag', -1, type=int)

            op = MessageOperation()
            db_session = op.get_seesion()


            # recordList = self.controlsession.query(UserMessageRecord, MessageContent). \
            #     filter(UserMessageRecord.contentId == MessageContent.id) \
            #     .filter(
            #     and_(UserMessageRecord.UserId == uid, MessageContent.state == StateType.publish,
            #          UserMessageRecord.flag==flag,
            #          UserMessageRecord.contentType == ContentType.infomation)).order_by(
            #     UserMessageRecord.addTime.desc()).limit(limit).offset(offset)

            total = 0
            if( flag == -1): #获取全部通知

                total = db_session.query(func.count(UserMessageRecord.id)).filter(
                    UserMessageRecord.contentId == MessageContent.id,MessageContent.state==1,
                    UserMessageRecord.isFinished.in_([FinishType.read,FinishType.unread]),
                    UserMessageRecord.UserId == uId, UserMessageRecord.flag.in_([FlagType.notice, FlagType.serious]),
                    UserMessageRecord.contentType == ContentType.infomation).scalar()

            elif( flag == -2): #获取全部报警
                total = db_session.query(func.count(UserMessageRecord.id)).filter(
                    UserMessageRecord.contentId == MessageContent.id, MessageContent.state == 1,
                    UserMessageRecord.isFinished.in_([FinishType.read, FinishType.unread]),
                    UserMessageRecord.UserId == uId, UserMessageRecord.flag.in_([FlagType.warning, FlagType.alarm_orange,FlagType.alarm_red]),
                    UserMessageRecord.contentType == ContentType.infomation).scalar()

            else:

                total = db_session.query(func.count(UserMessageRecord.id))\
                    .filter(UserMessageRecord.contentId == MessageContent.id,MessageContent.state==1,
                            UserMessageRecord.isFinished.in_([FinishType.read, FinishType.unread]),)\
                    .filter(and_(
                    UserMessageRecord.UserId == uId, UserMessageRecord.flag == flag,
                    UserMessageRecord.contentType == ContentType.infomation))\
                    .scalar()

            start = (page - 1) * per_page
            rows = op.getRecordByUserId(uId,per_page,start,flag)

            return_data = jsonify({'code': 100,
                                   'rows': rows,
                                   'count': total
                                   })

        except Exception, e:
            traceback.format_exc()
            print e

        return tools.en_return_data(return_data)




class OrganDataView(MethodView):
    def get(self):
        return_data = jsonify({ 'code':300 })


        try:

            print "enter organ data"
            from data_mode.user_center.control.mixOp import MixUserCenterOp
            db_seesion = MixUserCenterOp().get_seesion()

            companys = db_seesion.query(OrganCompany).order_by(OrganCompany.id)

            companys_datas = []
            for company in companys:
                print "have companys", companys
                company_data = company.to_json()
                departMents = company.departments
                company_data['departMents'] = []
                for departMent in departMents:
                    print "have departments", departMents
                    departMent_data = departMent.to_json(company=False)
                    departMent_data['users']  = []
                    positions = departMent.positions
                    for position in positions:
                        print "have position", positions
                        users = position.users
                        for user in users:
                            print "have users: ", users
                            if not user.is_active:
                                continue
                            user_data = user.to_json_simple()
                            departMent_data['users'].append(user_data)
                            if position.parent_id is None:
                                departMent_data['leader'] = user_data
                        parttime_users = position.parttime_users
                        for parttime_user in parttime_users:
                            if not parttime_user.is_active:
                                continue
                            user_data = parttime_user.to_json_simple()
                            departMent_data['users'].append(user_data)
                            if position.parent_id is None:
                                departMent_data['leader'] = user_data

                    company_data['departMents'].append(departMent_data)
                companys_datas.append(company_data)


            return_data =  jsonify({
                    'code': 100,
                    'companys': companys_datas
                })
        except Exception, e:
            print e

        return tools.en_return_data(return_data)



#删除最新通知
class NoticeNewDelete(MethodView):

    def get(self):
        return_data = jsonify({'code': 300})
        try:
            ids = request.args.get('ids', -1, str)

            if (ids == -1):
                return_data = jsonify({'code': 101})
                return tools.en_return_data(return_data)


            list = ids.split(',')
            op = MessageOperation()
            code = op.deleteRecordByids(list)

            return_data = jsonify({'code': code})
        except Exception,e:
            traceback.format_exc()
            pprint(e)
        return tools.en_return_data(return_data)


class NoticeUpdateRecordFlag(MethodView):
    def get(self):
        code = 300
        return_data = jsonify({'code': code})
        try:
            ids = request.args.get('ids', -1, str)
            flag = request.args.get('flag',-1,int)

            op = MessageOperation()




            list = []
            if (ids == -1):

                return_data = jsonify({'code': 101})
                return tools.en_return_data(return_data)
            else:
                list = ids.split(',')



            if (flag in [2,5]):
                for id in list:
                    op.updateRecordFlagByid(id,flag)

                return_data = jsonify({'code': 100})
            else:
                return_data = jsonify({'code': 101})
                return tools.en_return_data(return_data)


        except Exception, e:
            traceback.format_exc()
            pprint(e)


        return tools.en_return_data(return_data)


class NoticeUpdateRecordRead(MethodView):
    def get(self):
        code = 300
        return_data = jsonify({'code': code})
        try:
            ids = request.args.get('ids', -1, str)
            isFinish = request.args.get('isFinish',-1,int)

            op = MessageOperation()



            list = []
            if (ids == -1):

                return_data = jsonify({'code': 101})
                return tools.en_return_data(return_data)
            else:
                list = ids.split(',')



            if (isFinish in [0,1]):
                for id in list:
                    op.updateRecordReadByid(id,isFinish)

                return_data = jsonify({'code': 100})
            else:
                return_data = jsonify({'code': 101})
                return tools.en_return_data(return_data)


        except Exception, e:
            traceback.format_exc()
            pprint(e)


        return tools.en_return_data(return_data)

class ClearSessionAttachment(MethodView):
    def post(self):
        if session.has_key('upload_message_attachment'):

            session.pop('upload_message_attachment')

class MessageAttachmentAdd(MethodView):
    def post(self):


        return_data = jsonify({ 'code':300 })
        try:
            id = request.values.get('id')
            name = request.values.get('name')
            size = request.values.get('size')


            state = pub_upload_attachment_to_server()

            if state:

                state['fileId'] = id
                state['fileName'] = name
                state['fileSize'] = size
                state['localPath'] = state['path']
                state['localName'] = state['name']
                dict = {}

                qnState = pub_upload_attachment_to_qiniu(state)
                if (qnState[0]):
                    state['path'] = qnState[1]
                else:
                    state['path'] = ''

                op = MessageOperation()
                attach = MessageAttachment(name=state['name'], path=state['path'], fileName=state['fileName']
                           , fileSize=state['fileSize'], localPath=state['localPath'], localName=state['localName'])
                op.addAttachment(attach)



                return_data = jsonify({ 'code':100,
                                        'id':attach.id
                                        })

            else:
                return_data = jsonify({ 'code':112 })
        except Exception, e:
            print e
            return_data = jsonify({ 'code':112 })

        return tools.en_return_data(return_data)

class MessageAttachmentRemove(MethodView):
    def post(self):

        return_data = jsonify({ 'code':300 })
        id = request.values.get('id')
        try:
            op = MessageOperation()
            op.delAttachment(id)

            return_data = jsonify({ 'code':100 })

        except Exception, e:
            print e
            return_data = jsonify({ 'code':112 })
        return tools.en_return_data(return_data)



class AlarmShowView(MethodView):
    def get(self):

        return tools.render_template('alert/alert.html')


class NoticeAlarmCount(MethodView):
    def get(self):
        return_data = jsonify({'code': 300})

        try:
            if session.has_key('user'):
                uId = session['user']['id']
                noticeCount = 0
                alarmCount = 0

                op = MessageOperation()
                db_session = op.get_seesion()

                # 获取未读全部通知
                noticeCount = db_session.query(func.count(UserMessageRecord.id)).filter(
                        UserMessageRecord.contentId == MessageContent.id,
                        MessageContent.state == 1,
                        UserMessageRecord.UserId == uId,UserMessageRecord.isFinished==0,
                        UserMessageRecord.flag.in_([FlagType.notice, FlagType.serious]),
                        UserMessageRecord.contentType == ContentType.infomation).scalar()

                 # 获取未读全部报警
                alarmCount = db_session.query(func.count(UserMessageRecord.id)).filter(

                        UserMessageRecord.contentId == MessageContent.id,
                        MessageContent.state == 1,
                        UserMessageRecord.UserId == uId,UserMessageRecord.isFinished==0,
                        UserMessageRecord.flag.in_([FlagType.warning, FlagType.alarm_orange, FlagType.alarm_red]),
                        UserMessageRecord.contentType == ContentType.infomation).scalar()

                return_data = jsonify({
                    'code': 100,
                    'notice_count':noticeCount,
                    'alarm_count':alarmCount
                })
            else:
                return_data = jsonify({'code': 112})
        except Exception, e:
            print e

        return tools.en_return_data(return_data)

from control_center.admin import add_url
from . import main, main_prefix




# add_url.add_url(u"通知", "main.index", add_url.TYPE_FEATURE, main_prefix,
#                 main, '/notice_new/', 'notice_new', NewNoticeView.as_view('notice_new'), methods=['GET'])
main.add_url_rule('/notice_alarm_count/', 'notice_alarm_count', NoticeAlarmCount.as_view('notice_alarm_count'), methods=['GET'])

main.add_url_rule('/alarm/', 'alarm', AlarmShowView.as_view('alarm'), methods=['GET'])

main.add_url_rule('/notice_new/', 'notice_new', NewNoticeView.as_view('notice_new'), methods=['GET'])

main.add_url_rule('/notice_new_detail/', 'notice_new_detail', NewNoticeDetail.as_view('notice_new'), methods=['GET'])


add_url.add_url(u"最新通知页面", "main.notice_manager", add_url.TYPE_FUNC,  main_prefix,
                main, '/notice_new_data/', 'notice_new_data', UserNoticeDataView.as_view('notice_new_data'), methods=['GET'])

add_url.add_url(u"删除最新通知", "main.notice_manager", add_url.TYPE_FEATURE,  main_prefix,
                main, '/notice_new_delete/', 'notice_new_delete', NoticeNewDelete.as_view('notice_new_delete'), methods=['GET'])

add_url.add_url(u"更新最新通知重要性", "main.notice_manager", add_url.TYPE_FEATURE,  main_prefix,
                main, '/notice_new_update_flag/', 'notice_new_update_flag', NoticeUpdateRecordFlag.as_view('notice_new_update_flag'), methods=['GET'])


add_url.add_url(u"更新最新通知已读", "main.notice_manager", add_url.TYPE_FEATURE,  main_prefix,
                main, '/notice_new_update_read/', 'notice_new_update_read', NoticeUpdateRecordRead.as_view('notice_new_update_read'), methods=['GET'])



add_url.add_url(u"通知管理页面", "main.index", add_url.TYPE_FEATURE, main_prefix,
                main, '/notice_manager/', 'notice_manager', NoticeManagerView.as_view('notice'), methods=['GET'])

add_url.add_url(u"通知管理页面元素", "main.notice_manager", add_url.TYPE_FUNC,  main_prefix,
                main, '/notice_data/', 'notice_data', NoticeDataView.as_view('notice_data'), methods=['GET'])

add_url.add_url(u"删除通知元素", "main.notice_manager", add_url.TYPE_FEATURE,  main_prefix,
                main, '/notice_manager_delete/', 'notice_manager_delete', NoticeManagerDelete.as_view('notice_manager_delete'), methods=['GET'])

add_url.add_url(u"发布撤销通知", "main.notice_manager", add_url.TYPE_FEATURE,  main_prefix,
                main, '/notice_manager_publish/', 'notice_manager_publish', NoticeManagerPublish.as_view('notice_manager_publish'), methods=['GET'])

add_url.add_url(u"通知详细页面", "main.notice_manager", add_url.TYPE_FUNC, main_prefix,
                main, '/notice_detail/', 'notice_detail', NoticeDetailView.as_view('notice_detail'), methods=['GET'])


add_url.add_url(u"通知详细数据更新", "main.notice_manager", add_url.TYPE_FEATURE,  main_prefix,
                main, '/notice_update_detail_data/', 'notice_update_detail_data', NoticeUpdateDetailDataView.as_view('notice_update_detail_data'), methods=['GET'])

add_url.add_url(u"通知详细数据更新", "main.notice_manager", add_url.TYPE_FEATURE,  main_prefix,
                main, '/notice_read_action/', 'notice_read_action', NoticeReadAction.as_view('notice_read_action'), methods=['GET'])


add_url.add_url(u"创建通知", "main.notice_manager", add_url.TYPE_FEATURE,  main_prefix,
                main, '/notice_create/', 'notice_create', NoticeCreate.as_view('notice_create'), methods=['GET','POST'])


add_url.add_url(u"获取公司组织架构信息", "main.notice_manager", add_url.TYPE_FUNC,  main_prefix,
                main, '/organ_data/', 'organ_data', OrganDataView.as_view('organ_data'), methods=['GET'])


add_url.add_url(u"添加附件", 'main.notice_manager', add_url.TYPE_FEATURE, main_prefix,
                main, '/notice_add_attachment/', 'notice_add_attachment', MessageAttachmentAdd.as_view('notice_add_attachment'), methods=['POST'])


add_url.add_url(u"删除附件", 'main.notice_manager', add_url.TYPE_FEATURE, main_prefix,
                main, '/notice_remove_attachment/', 'notice_remove_attachment', MessageAttachmentRemove.as_view('notice_remove_attachment'), methods=['POST'])


add_url.add_url(u"清除会话附件", 'main.notice_manager', add_url.TYPE_FEATURE, main_prefix,
                main, '/notice_clear_attachment/', 'notice_clear_attachment', ClearSessionAttachment.as_view('notice_clear_attachment'), methods=['POST'])


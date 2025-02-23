# -*- coding: utf-8 -*-

import re

from basic.get import *
from basic.send import send_wxuser_list
from basic.task import *
from multithread.threads import *
from apibase.ChatGPTAPI import Chatbot
from basic.schedule import addScheduleTask, removeScheduleTask
from basic.wechatModel import *


# data
global_thread = []

current_user_wx_id = ""
current_user_wx_name = ""

def handle_personal_info(j):
    logging.info(j)
    data = json.loads(j["content"])
    current_user_wx_id = data["wx_id"]
    adminUsers.append(current_user_wx_id)
    current_user_wx_name = data["wx_name"]

def debug_switch():
    qs = {
        "id": getid(),
        "type": DEBUG_SWITCH,
        "content": "off",
        "wxid": "",
    }
    s = json.dumps(qs)
    return s


def handle_nick(j):
    data = json.loads(j["content"])
    logging.info("测试群成员昵称：" + data["nick"])
    return data["nick"]


def hanle_memberlist(j):
    data = j["content"]
    logging.info(data)
    # for d in data:
    #     logging.info(d["room_id"])


def destroy_all():
    qs = {
        "id": getid(),
        "type": DESTROY_ALL,
        "content": "none",
        "wxid": "node",
    }
    s = json.dumps(qs)
    return s


def handle_wxuser_list(j):
    content = j["content"]
    group_id_dict.clear()
    group_name_dict.clear()
    friend_id_dict.clear()
    friend_name_dict.clear()
    i = 0
    # 微信群
    for item in content:
        i += 1
        id = item["wxid"]
        name = item["name"]
        m = id.find("@")
        if m != -1:
            group_info = "{index}, 群聊, {id}, {name}".format(index=i, id=id, name = name)
            logging.info(group_info)
            group = Group(id, name)
            group_id_dict[id] = group
            if name in group_name_dict:
                group_name_dict[id] = group
                reply = "群聊名称：{name}重复 建议使用group_id定位群聊".format(name=name)
                logging.info(reply)
                for user_id in adminUsers:
                    nm = NormalTask(ws, None, reply, user_id, user_id, user_id.find("@") == -1, False)
                    nrm_que.put(nm)
            else:
                group_name_dict[name] = group

    # 微信其他好友，公众号等
    for item in content:
        i += 1
        id = item["wxid"]
        name = item["name"]
        m = id.find("@")
        if m == -1:
            friend_info = "{index}, 个体, {id}, {name}, {wxcode}".format(index=i, id=id, name=name, wxcode=item["wxcode"])
            logging.info(friend_info)
            friend = Friend(id, name, item["wxcode"])
            friend_id_dict[i] = friend
            if name in friend_name_dict:
                friend_name_dict[id] = friend
                reply = "朋友名称：{name}重复 建议使用wx_id定位朋友".format(name=name)
                logging.info(reply)
                for user_id in adminUsers:
                    nm = NormalTask(ws, None, reply, user_id, user_id, user_id.find("@") == -1, False)
                    nrm_que.put(nm)
            else:
                friend_name_dict[name] = friend
    for user_id in adminUsers:
        reply = "群聊和朋友列表刷新成功"
        nm = NormalTask(ws, None, reply, user_id, user_id, user_id.find("@") == -1, False)
        nrm_que.put(nm)
            


def handle_recv_txt_msg(j):
    logging.info(j)

    wx_id = j["wxid"]
    room_id = ""
    content: str = j["content"].strip()

    access_internet: bool = False
    is_room: bool
    chatbot: Chatbot

    is_admin_user: bool = False

    if len(wx_id) < 9 or wx_id[-9] != "@":
        is_room = False
        wx_id: str = j["wxid"]
        chatbot = global_dict.get((wx_id, ""))
        if wx_id in adminUsers:
            is_admin_user = True

    else:
        is_room = True
        wx_id = j["id1"]
        room_id = j["wxid"]
        chatbot = global_dict.get((wx_id, room_id))

    is_citation = (grpCitationMode and is_room) or (prvCitationMode and not is_room)

    if is_admin_user:
        if content.startswith(groupRefreshKey):
            ws.send(send_wxuser_list())
            reply = "刷新群聊和朋友列表"
            return
        if content.startswith(groupGetKey):
            reply = "群聊列表如下\n"
            for value in group_id_dict.values():
                    reply += str(value) + "\n" 
            nm = NormalTask(ws, content, reply, wx_id, room_id, is_room, False)
            nrm_que.put(nm)
            return
        if content.startswith(friendGetKey):
            reply = "朋友列表如下\n"
            for value in friend_id_dict.values():
                reply += str(value) + "\n" 
            nm = NormalTask(ws, content, reply, wx_id, room_id, is_room, False)
            nrm_que.put(nm)
            return
        if content.startswith(scheduleAddKey):
            jon_reply = re.sub("^" + scheduleAddKey, "", content, 1).lstrip()
            sche_cron_args = re.split(scheduleCronKey, jon_reply)
            job_tip = ""
            cron_str = ""
            if len(sche_cron_args) < 2:
                job_tip = "请设置定时任务cron表达式 ep: " + scheduleCronKey + " */1 * * * *"
            else:
                job_tip, cron_str, sche_wx_id, sche_room_id, sche_is_room = get_wx_arg(sche_cron_args[1])
                if len(job_tip) == 0:
                    ct = ScheduleTask(ws, content, sche_cron_args[0], sche_wx_id, sche_room_id, sche_is_room, cron_str)
                    job_tip = addScheduleTask(ct)
            nm = NormalTask(ws, content, job_tip, wx_id, room_id, is_room, True)
            nrm_que.put(nm)
            return
        if content.startswith(scheduleDeleteKey):
            arg_content= re.sub("^" + scheduleDeleteKey, "", content, 1).lstrip()
            job_tip, cron_str, sche_wx_id, sche_room_id, sche_is_room = get_wx_arg(arg_content)
            if len(job_tip) == 0:
                job_tip = "任务取消成功"
            job_content = removeScheduleTask(sche_is_room, sche_wx_id, sche_room_id)
            nm = NormalTask(ws, job_content, job_tip, wx_id, room_id, is_room, True)
            nrm_que.put(nm)
            return
    if autoReply and ((not is_room and prvReplyMode) or (is_room and grpReplyMode)):
        if content.startswith(helpKey):
            reply = str(
                b'\xe6\xac\xa2\xe8\xbf\x8e\xe4\xbd\xbf\xe7\x94\xa8 ChatGPT-weBot \xef\xbc\x8c\xe6\x9c\xac\xe9'
                b'\xa1\xb9\xe7\x9b\xae\xe5\x9c\xa8 github \xe5\x90\x8c\xe5\x90\x8d\xe5\xbc\x80\xe6\xba\x90\n',
                'utf-8') + helpKey + " 查看可用命令帮助\n" + \
                    ((groupChatKey + " 提问群聊天机器人\n ") if is_room else ( "直接提问聊天机器人\n" if prvReplyAlways else (privateChatKey + " 提问聊天机器人\n ")))  + \
                    resetChatKey + " 重置上下文\n" + \
                    regenerateKey + " 重新生成答案\n" + \
                    rollbackKey + " +数字n 回滚到倒数第n个问题\n" + \
                    characterKey + "更改机器人角色设定\n" + \
                    ((scheduleAddKey + "新增定时任务 ep: -sa 定时任务内容 -sc */1 * * * *\n") if not scheduleAdminOnly else "") + \
                    ((scheduleDeleteKey + "删除定时任务\n") if not scheduleAdminOnly else "") + \
                    conclusionKey + "总结对话\n"
            if openAiImg:
                reply += ((groupImgKey + " 提问群AI画图机器人(openAI)\n ") if is_room else (privateImgKey + " 提问AI画图机器人(openAI)\n"))
            if stableDiffRly:
                reply += ((groupImgKey + " 提问群AI画图机器人(Stable Diffusion 仅英语)\n ") if is_room else (privateImgKey + " 提问AI画图机器人( Stable Diffusion 仅英语)\n "))
            if is_admin_user:
                reply += "管理员功能\n"  + \
                    helpKey + " 查看可用命令帮助\n"  + \
                    groupRefreshKey +" 刷新群聊和朋友列表\n" + \
                    groupGetKey +" 获取群聊列表\n" + \
                    friendGetKey +" 获取朋友列表\n" + \
                    scheduleAddKey + "指定给某群或某人新增定时任务 ep: -sa 定时任务内容 -sc */1 * * * * [--wx_id|--wx_name|--group_id|--group_name]\n"+ \
                    scheduleDeleteKey + "删除指定给某群或某人的定时任务 ep: -sd [--wx_id|--wx_name|--group_id|--group_name]\n"
            nm = NormalTask(ws, content, reply, wx_id, room_id, is_room, False)
            nrm_que.put(nm)

        elif content.startswith(scheduleAddKey):
            job_tip = ""
            if scheduleAdminOnly and not is_admin_user:
                job_tip = "定时任务是管理员限定功能 普通成员无法添加定时任务"
            else:
                jon_reply = re.sub("^" + scheduleAddKey, "", content, 1).lstrip()
                sche_args = re.split(scheduleCronKey, jon_reply)
                if len(sche_args) < 2:
                    job_tip = "请设置定时任务cron表达式 ep: " + scheduleCronKey + " */1 * * * *"
                else:
                    ct = ScheduleTask(ws, content, sche_args[0], wx_id, room_id, is_room, sche_args[1].strip())
                    job_tip = addScheduleTask(ct)
            nm = NormalTask(ws, content, job_tip, wx_id, room_id, is_room, True)
            nrm_que.put(nm)

        elif content.startswith(scheduleDeleteKey):
            job_content = content
            job_tip = ""
            if scheduleAdminOnly and not is_admin_user:
                job_tip = "定时任务是管理员限定功能 普通成员无法添加定时任务"
            else:
                job_content = removeScheduleTask(is_room, wx_id, room_id)
                job_tip = "任务已取消"
            nm = NormalTask(ws, job_content, job_tip, wx_id, room_id, is_room, True)
            nrm_que.put(nm)

        elif content.startswith(resetChatKey):
            ct = ChatTask(ws, content, access_internet, chatbot, wx_id, room_id, is_room, is_citation, "rs")
            chat_que.put(ct)

        elif content.startswith(regenerateKey):
            ct = ChatTask(ws, content, access_internet, chatbot, wx_id, room_id, is_room, is_citation, "rg")
            chat_que.put(ct)

        elif content.startswith(rollbackKey):
            if chatbot is None or chatbot.question_num == 0:
                reply = "您还没有问过问题"

            else:
                num = re.sub("^" + rollbackKey, "", content, 1).lstrip()
                if num.isdigit():
                    if chatbot.question_num < int(num):
                        reply = "无法回滚到" + num + "个问题之前"

                    else:
                        chatbot.rollback_conversation(int(num))
                        reply = "已回滚到" + num + "个问题之前"
                else:
                    reply = "请在回滚指令后输入有效数字"

            nm = NormalTask(ws, content, reply, wx_id, room_id, is_room, is_citation)
            nrm_que.put(nm)

        elif content.startswith(characterKey):
            content = re.sub("^" + characterKey, "", content, 1).lstrip()
            if chatbot is None:
                chatbot = Chatbot(
                    api_config,
                )
                if is_room:
                    global_dict[(wx_id, room_id)] = chatbot
                else:
                    global_dict[(wx_id, "")] = chatbot

            ct = ChatTask(ws, content, access_internet, chatbot, wx_id, room_id, is_room, is_citation, "p")
            chat_que.put(ct)

        elif content.startswith(conclusionKey):
            ct = ChatTask(ws, content, access_internet, chatbot, wx_id, room_id, is_room, is_citation, "z")
            chat_que.put(ct)

        elif openAiImg and (
                (content.startswith(privateImgKey) and not is_room) or (content.startswith(groupImgKey) and is_room)):
            content = re.sub("^" + (groupImgKey if is_room else privateImgKey), "", content, 1).lstrip()
            #prompt_list = re.split(negativePromptKey, content)
            if chatbot is None:
                chatbot = Chatbot(
                    api_config,
                )
                if is_room:
                    global_dict[(wx_id, room_id)] = chatbot
                else:
                    global_dict[(wx_id, "")] = chatbot
            ig = GptImgTask(ws, content, chatbot, wx_id, room_id, is_room)
            img_que.put(ig)

        elif stableDiffRly and (
                (content.startswith(sdiPrivateImgKey) and not is_room) or (content.startswith(sdiGroupImgKey) and is_room)):
            content = re.sub("^" + (sdiGroupImgKey if is_room else sdiPrivateImgKey), "", content, 1).lstrip()
            prompt_list = re.split(negativePromptKey, content)
            if chatbot is None:
                chatbot = Chatbot(
                    api_config,
                )
                if is_room:
                    global_dict[(wx_id, room_id)] = chatbot
                else:
                    global_dict[(wx_id, "")] = chatbot
            # ig = ImgTask(ws, prompt_list, wx_id, room_id, is_room, "2.1")
            ig = SdiImgTask(ws, prompt_list[0], "" if len(prompt_list) == 1 else prompt_list[1], chatbot, wx_id, room_id, is_room)
            img_que.put(ig)

        elif ((prvReplyAlways or privateChatKey in content) and not is_room) or (groupChatKey in content and is_room):
            content = content.replace((groupChatKey if is_room else privateChatKey), "").lstrip()
            if content.startswith(internetKey):
                content = re.sub("^" + internetKey, "", content, 1).lstrip()
                access_internet = True
            if chatbot is None:
                chatbot = Chatbot(
                    api_config,
                )
                if is_room:
                    global_dict[(wx_id, room_id)] = chatbot
                else:
                    global_dict[(wx_id, "")] = chatbot

            ct = ChatTask(ws, content, access_internet, chatbot, wx_id, room_id, is_room, is_citation, "c")
            chat_que.put(ct)

def get_wx_arg(arg_content):
    job_tip = ""
    sche_wx_id = ""
    sche_room_id = ""
    sche_is_room = False
    if wxIdKey in arg_content:
        sche_is_room = False
        sche_wxId_args = re.split(wxIdKey, arg_content)
        cron_str = sche_wxId_args[0].strip()
        wx_id_arg = sche_wxId_args[1].strip()
        if wx_id_arg in friend_id_dict:
            sche_wx_id = friend_id_dict[wx_id_arg].wx_id
        else:
            job_tip = "朋友不存在 " + wxIdKey + ": " + wx_id_arg + "可使用 " + friendGetKey + " 获取朋友列表"
    if wxNameKey in arg_content:
        sche_is_room = False
        sche_wxName_args = re.split(wxNameKey, arg_content)
        cron_str = sche_wxName_args[0].strip()
        wx_name_arg = sche_wxName_args[1].strip()
        if wx_name_arg in friend_name_dict:
            sche_wx_id = friend_name_dict[wx_name_arg].wx_id
        else:
            job_tip = "朋友不存在 " + wxNameKey + ": " + wx_name_arg + "可使用 " + friendGetKey + " 获取朋友列表"
    if groupIdKey in arg_content:
        sche_is_room = True
        sche_groupId_args = re.split(groupIdKey, arg_content)
        cron_str = sche_groupId_args[0].strip()
        groupId_arg = sche_groupId_args[1].strip()
        if groupId_arg in group_id_dict:
            sche_room_id = group_id_dict[groupId_arg].room_id
        else:
            job_tip = "群聊不存在 " + groupIdKey + ": " + groupId_arg + "可使用 " + groupGetKey + " 获取群聊列表"
    if groupNameKey in arg_content:
        sche_is_room = True
        sche_groupName_args = re.split(groupNameKey, arg_content)
        cron_str = sche_groupName_args[0].strip()
        groupName_arg = sche_groupName_args[1].strip()
        if groupName_arg in group_name_dict:
            sche_room_id = group_name_dict[groupName_arg].room_id
        else:
            job_tip = "群聊不存在 " + groupNameKey + ": " + groupName_arg + "可使用 " + groupGetKey + " 获取群聊列表"
    return job_tip,cron_str,sche_wx_id,sche_room_id,sche_is_room


def handle_recv_pic_msg(j):
    logging.info(j)


def handle_recv_txt_cite(j):
    pass


def handle_heartbeat(j):
    pass


def on_open(ws):
    # chatbot = Chatbot(
    #     rev_config,
    #     conversation_id=None,
    #     parent_id=None,
    # )
    # try:
    #     chatbot.login()
    # except Exception:
    #     raise Exception("Exception detected, check revChatGPT login config")
    # else:
    #     logging.info("\nChatGPT login test success!\n")

    # ws.send(send_pic_msg(wx_id="filehelper", room_id="", content=""))
    ws.send(get_personal_info())
    ws.send(send_wxuser_list())
    # ws.send(get_chatroom_memberlist())

    # ws.send(send_txt_msg("server is online", "filehelper"))
    # ws.send(send_pic_msg(wx_id="filehelper", content=os.path.join(os.path.abspath(cache_dir), "")))
    

    for i in range(0, 4):
        normal_processor = Processor(nrm_que)
        global_thread.append(normal_processor)

    for i in range(0, 2):
        chat_processor = Processor(chat_que)
        global_thread.append(chat_processor)

    for i in range(0, 4):
        image_processor = Processor(img_que)
        global_thread.append(image_processor)

    for i in range(0, 2):
        image_processor = Processor(sche_que)
        global_thread.append(image_processor)


def on_message(ws, message):
    j = json.loads(message)
    # logging.info(j)

    resp_type = j["type"]

    # switch
    action = {
        HEART_BEAT: handle_heartbeat,
        RECV_TXT_MSG: handle_recv_txt_msg,
        RECV_PIC_MSG: handle_recv_pic_msg,
        NEW_FRIEND_REQUEST: logging.info,
        RECV_TXT_CITE_MSG: handle_recv_txt_cite,

        TXT_MSG: logging.info,
        PIC_MSG: logging.info,
        AT_MSG: logging.info,

        USER_LIST: handle_wxuser_list,
        GET_USER_LIST_SUCCESS: handle_wxuser_list,
        GET_USER_LIST_FAIL: handle_wxuser_list,
        ATTACH_FILE: logging.info,

        CHATROOM_MEMBER: hanle_memberlist,
        CHATROOM_MEMBER_NICK: handle_nick,
        DEBUG_SWITCH: logging.info,
        PERSONAL_INFO: handle_personal_info,
        PERSONAL_DETAIL: logging.info,
    }

    action.get(resp_type, logging.info)(j)


def on_error(ws, error):
    logging.info(ws)
    logging.info(error)


def on_close(ws):
    for key, value in global_dict.items():
        logging.info("clear conversation:" + key)
        del value

    logging.info(ws)
    logging.info("closed")


server = "ws://" + server_host

# websocket.enableTrace(True)

ws = websocket.WebSocketApp(server,
                            on_open=on_open,
                            on_message=on_message,
                            on_error=on_error,
                            on_close=on_close)
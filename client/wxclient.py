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
    print(j)
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
    print("测试群成员昵称：" + data["nick"])
    return data["nick"]


def hanle_memberlist(j):
    data = j["content"]
    print(data)
    # for d in data:
    #     print(d["room_id"])


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
            print(i, "群聊", id, name)
            group = Group(id, name)
            group_id_dict[id] = group
            if name in group_name_dict:
                group_name_dict[id] = group
                reply = "群聊名称：{name}重复 建议使用group_id定位群聊".format(name=name)
                print(reply)
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
            print(i, "个体", id, name, item["wxcode"])
            friend = Friend(id, name, item["wxcode"])
            friend_id_dict[i] = friend
            if name in friend_name_dict:
                friend_name_dict[id] = friend
                reply = "朋友名称：{name}重复 建议使用wx_id定位朋友".format(name=name)
                print(reply)
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
    print(j)

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
                    scheduleAddKey + "新增定时任务 ep: -sa 定时任务内容 -sc */1 * * * *\n" + \
                    scheduleDeleteKey + "删除定时任务\n" + \
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
                    friendGetKey +" 获取朋友列表" 
            nm = NormalTask(ws, content, reply, wx_id, room_id, is_room, False)
            nrm_que.put(nm)

        elif content.startswith(scheduleAddKey):
            jon_reply = re.sub("^" + scheduleAddKey, "", content, 1).lstrip()
            sche_args = re.split(scheduleCronKey, jon_reply)
            job_tip = ""
            if len(sche_args) < 2:
                job_tip = "请设置定时任务cron表达式 ep: " + scheduleCronKey + " */1 * * * *"
            else:
                ct = ScheduleTask(ws, content, sche_args[0], wx_id, room_id, is_room, sche_args[1])
                job_tip = addScheduleTask(ct)
            nm = NormalTask(ws, content, job_tip, wx_id, room_id, is_room, True)
            nrm_que.put(nm)

        elif content.startswith(scheduleDeleteKey):
            job_content = removeScheduleTask(is_room, wx_id, room_id)
            nm = NormalTask(ws, job_content, "任务已取消", wx_id, room_id, is_room, True)
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


def handle_recv_pic_msg(j):
    print(j)


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
    #     print("\nChatGPT login test success!\n")

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
    # print(j)

    resp_type = j["type"]

    # switch
    action = {
        HEART_BEAT: handle_heartbeat,
        RECV_TXT_MSG: handle_recv_txt_msg,
        RECV_PIC_MSG: handle_recv_pic_msg,
        NEW_FRIEND_REQUEST: print,
        RECV_TXT_CITE_MSG: handle_recv_txt_cite,

        TXT_MSG: print,
        PIC_MSG: print,
        AT_MSG: print,

        USER_LIST: handle_wxuser_list,
        GET_USER_LIST_SUCCESS: handle_wxuser_list,
        GET_USER_LIST_FAIL: handle_wxuser_list,
        ATTACH_FILE: print,

        CHATROOM_MEMBER: hanle_memberlist,
        CHATROOM_MEMBER_NICK: handle_nick,
        DEBUG_SWITCH: print,
        PERSONAL_INFO: handle_personal_info,
        PERSONAL_DETAIL: print,
    }

    action.get(resp_type, print)(j)


def on_error(ws, error):
    print(ws)
    print(error)


def on_close(ws):
    for key, value in global_dict.items():
        print("clear conversation:" + key)
        del value

    print(ws)
    print("closed")


server = "ws://" + server_host

# websocket.enableTrace(True)

ws = websocket.WebSocketApp(server,
                            on_open=on_open,
                            on_message=on_message,
                            on_error=on_error,
                            on_close=on_close)
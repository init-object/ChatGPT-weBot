# -*- coding: utf-8 -*-
import json
import time
import os

from apibase.revChatGPT import configure


def str_to_bool(str):
    return True if str.lower() == 'true' else False

# api model check
with open(".config/api_config.json", encoding="utf-8") as f:
    api_config = json.load(f)
f.close()

if api_config["engine"] not in [
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-0301",
    "gpt-4",
    "gpt-4-0314",
    "gpt-4-32k",
    "gpt-4-32k-0314",
]:
    error = NotImplementedError("Unsupported engine {self.engine}")
    raise error

if "CHATGPT_API_KEY" in os.environ:
    api_config["api_key"] = os.environ["CHATGPT_API_KEY"]

# server config
with open(".config/server_config.json", encoding="utf-8") as f:
    config = json.load(f)
f.close()
server_host = config["server_host"]
sd_server_host = config["sd_server_host"]
if "SERVER_HOST" in os.environ:
    server_host = os.environ["SERVER_HOST"]
if "SD_SERVER_HOST" in os.environ:
    sd_server_host = os.environ["SD_SERVER_HOST"]

# general config
with open(".config/config.json", encoding="utf-8") as f:
    config = json.load(f)
f.close()

autoReply = config["autoReply"]
adminUsers = config["adminUsers"]
if "ADMIN_USER_IDS" in os.environ:
    adminUsersEnv = os.environ["ADMIN_USER_IDS"].split(",")
    adminUsers.extend(adminUsersEnv)
internetKey = config["internetKey"]
internetResult = config["internetResult"]

groupChatKey = config["groupChatKey"]
grpReplyMode = config["grpReplyMode"]
grpCitationMode = config["grpCitationMode"]
privateChatKey = config["privateChatKey"]
prvReplyMode = config["prvReplyMode"]
prvReplyAlways = config["prvReplyAlways"]
prvCitationMode = config["prvCitationMode"]
characterKey = config["characterKey"]
scheduleAddKey = config["scheduleAddKey"]
scheduleCronKey = config["scheduleCronKey"]
scheduleDeleteKey = config["scheduleDeleteKey"]
conclusionKey = config["conclusionKey"]

stableDiffRly = config["stableDiffRly"]
sdiPrivateImgKey = config["sdiPrivateImgKey"]
sdiGroupImgKey = config["sdiGroupImgKey"]
openAiImg = config["openAiImg"]
groupImgKey = config["groupImgKey"]
privateImgKey = config["privateImgKey"]
negativePromptKey = config["negativePromptKey"]
isCached = config["isCached"]

helpKey = config["helpKey"]
resetChatKey = config["resetChatKey"]
regenerateKey = config["regenerateKey"]
rollbackKey = config["rollbackKey"]

groupRefreshKey = config["groupRefreshKey"]
groupGetKey = config["groupGetKey"]
friendGetKey = config["friendGetKey"]
wxIdKey = config["wxIdKey"]
wxNameKey = config["wxNameKey"]
groupIdKey = config["groupIdKey"]
groupNameKey = config["groupNameKey"]

scheduleAdminOnly=config["scheduleAdminOnly"]
if "SCHEDULE_ADMIN_ONLY" in os.environ:
    scheduleAdminOnly = str_to_bool(os.environ["SCHEDULE_ADMIN_ONLY"])

webHooKSecret=config["webHooKSecret"]
if "WEB_HOOK_SECRET" in os.environ:
    webHooKSecret = os.environ["WEB_HOOK_SECRET"]
# apibase config
rev_config = configure()

# Signal Number
HEART_BEAT = 5005
RECV_TXT_MSG = 1
RECV_PIC_MSG = 3
NEW_FRIEND_REQUEST = 37
RECV_TXT_CITE_MSG = 49

TXT_MSG = 555
PIC_MSG = 500
AT_MSG = 550

USER_LIST = 5000
GET_USER_LIST_SUCCESS = 5001
GET_USER_LIST_FAIL = 5002
ATTACH_FILE = 5003
CHATROOM_MEMBER = 5010
CHATROOM_MEMBER_NICK = 5020

DEBUG_SWITCH = 6000
PERSONAL_INFO = 6500
PERSONAL_DETAIL = 6550

DESTROY_ALL = 9999
OTHER_REQUEST = 10000

# stable_diff config
API_URL_v21 = sd_server_host + "/queue/join"
API_URL_v15 = ""
cache_dir = ".cache/"


def getid():
    id = time.strftime("%Y%m%d%H%M%S", time.localtime(time.time()))
    return id


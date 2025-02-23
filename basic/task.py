# -*- coding: utf-8 -*-

import base64
import logging
import os.path
import string
import random
import datetime
import websocket

from shared.shared import *
from apibase.ChatGPTAPI import ChatbotError
from .send import send_txt_msg, send_pic_msg

global_dict = dict()


class ChatTask:
    def __init__(self, ws, prompt, access, chatbot, wx_id, room_id, is_room, is_citation, type):
        self.ws = ws
        self.prompt = prompt
        self.access = access
        self.bot = chatbot
        self.wx_id = wx_id
        self.room_id = room_id
        self.is_room = is_room
        self.is_citation = is_citation
        self.type = type
        self.reply = ""

    def play(self):
        if self.type == "rs":
            if self.bot is not None and len(self.bot.conversation) > 1:
                self.bot.reset()
                self.reply = "重置完成"
            else:
                self.reply = "您还没有开始第一次对话"
                time.sleep(0.5)

        elif self.type == "rg":
            if self.bot is None or self.bot.question_num == 0:
                self.reply = "您还没有问过问题"
                time.sleep(0.5)
            else:
                logging.info("ask:" + self.bot.prev_question[-1][-1])
                try:
                    self.reply += self.bot.ask(prompt=None)
                except ChatbotError as CE:
                    self.reply += CE.__str__()

        elif self.type == "z":
            if self.bot is None or self.bot.question_num < 1:
                self.reply = "您还没有问过问题"
                time.sleep(0.5)
            else:
                logging.info("ask: 用150字内总结全部对话")
                self.reply += self.bot.conclusion()

        elif self.type == "p":
            try:
                self.bot.set_system_character(role=self.prompt)
                self.reply += f"设定角色 {self.prompt} 成功"
            except ChatbotError as CE:
                self.reply += CE.__str__()
                time.sleep(0.5)

        elif self.type == "c":
            logging.info("ask:" + self.prompt)
            try:
                self.reply += self.bot.ask(prompt=self.prompt, access_internet=self.access,
                                           access_result=internetResult)
            except ChatbotError as CE:
                self.reply += CE.__str__()

        logging.info("reply: " + self.reply)
        if self.is_citation:
            citation = self.prompt
            if self.type == "rg":
                if self.bot is None or self.bot.question_num == 0:
                    citation = self.prompt
                else:
                    citation = self.bot.prev_question[-1][-1]
            else:
                if  self.type == "z":
                    citation = "用150字内总结全部对话"
            self.reply = citation + "\n- - - - - - - - - -\n" + self.reply.strip()
        self.ws.send(send_txt_msg(text_string=self.reply.strip(), wx_id=self.room_id if self.is_room else self.wx_id))

class GptImgTask:
    def __init__(self, ws, prompt, chatbot, wx_id, room_id, is_room):
        self.ws = ws
        self.prompt = prompt
        self.bot = chatbot
        self.wx_id = wx_id
        self.room_id = room_id
        self.is_room = is_room
        self.reply = ""

    def play(self):
        logging.info("ask:" + self.prompt)
        try:
            image_base64 = self.bot.image_create(prompt=self.prompt)
            source_str = base64.urlsafe_b64decode(image_base64)
            filename = self.wx_id + "_" + self.room_id + "_" + getid() + ".jpg"
            if not os.path.exists(".cache/"):
                os.makedirs(cache_dir)
            with open(cache_dir + filename, "wb") as file_object:
                file_object.write(source_str)
            file_object.close()

            self.ws.send(send_pic_msg(wx_id=self.room_id if self.is_room else self.wx_id,
                                        content=os.path.join(os.path.abspath(cache_dir), filename)))
            time.sleep(1.0)
            if isCached:
                logging.info("Image cached! Name: " + cache_dir + filename)
            else:
                os.remove(cache_dir + filename)
        except ChatbotError as CE:
            self.reply += CE.__str__()
            self.ws.send(send_txt_msg(text_string=self.reply.strip(), wx_id=self.room_id if self.is_room else self.wx_id))

class SdiImgTask:
    def __init__(self, ws, prompt, negivate_prompt, chatbot, wx_id, room_id, is_room):
        self.ws = ws
        self.prompt = prompt
        self.negivate_prompt = negivate_prompt
        self.bot = chatbot
        self.wx_id = wx_id
        self.room_id = room_id
        self.is_room = is_room
        self.reply = ""

    def play(self):
        logging.info("ask:" + self.prompt)
        try:
            image_base64 = self.bot.image_create_sdi(prompt=self.prompt, negivate_prompt=self.negivate_prompt)
            source_str = base64.urlsafe_b64decode(image_base64)
            filename = self.wx_id + "_" + self.room_id + "_" + getid() + ".jpg"
            if not os.path.exists(".cache/"):
                os.makedirs(cache_dir)
            with open(cache_dir + filename, "wb") as file_object:
                file_object.write(source_str)
            file_object.close()

            self.ws.send(send_pic_msg(wx_id=self.room_id if self.is_room else self.wx_id,
                                        content=os.path.join(os.path.abspath(cache_dir), filename)))
            time.sleep(1.0)
            if isCached:
                logging.info("Image cached! Name: " + cache_dir + filename)
            else:
                os.remove(cache_dir + filename)
        except ChatbotError as CE:
            self.reply += CE.__str__()
            self.ws.send(send_txt_msg(text_string=self.reply.strip(), wx_id=self.room_id if self.is_room else self.wx_id))

class NormalTask:
    def __init__(self, ws, prompt, reply, wx_id, room_id, is_room, is_citation):
        self.ws = ws
        self.prompt = prompt
        self.reply = reply
        self.wx_id = wx_id
        self.room_id = room_id
        self.is_room = is_room
        self.is_citation = is_citation

    def play(self):
        time.sleep(0.5)
        logging.info("reply: " + self.reply)

        if self.is_citation:
            self.reply = self.prompt + "\n- - - - - - - - - -\n" + self.reply.strip()
        self.ws.send(send_txt_msg(text_string=self.reply.strip(), wx_id=self.room_id if self.is_room else self.wx_id))

class ScheduleTask:
    def __init__(self, ws, content, reply, wx_id, room_id, is_room, cron):
        self.ws = ws
        self.content = content
        self.reply = reply
        self.wx_id = wx_id
        self.room_id = room_id
        self.is_room = is_room
        self.cron = cron

    def play(self):
        logging.info("cron:" + self.cron + " 当前时间：" + datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + "发送内容:" + self.reply)
        self.ws.send(send_txt_msg(text_string=self.reply.strip(), wx_id=self.room_id if self.is_room else self.wx_id))

class ImgTask:
    def __init__(self, ws, prompt, wx_id, room_id, is_room, version):
        self.ws = ws
        self.prompt = prompt
        self.wx_id = wx_id
        self.room_id = room_id
        self.is_room = is_room
        self.version = version

        self.img_ws = None
        self.wssRq = {
            "session_hash": "".join(random.sample(string.ascii_lowercase + string.digits, 11)),
            "fn_index": 3
        }
        self.times = 0

        if version == "2.1":
            self.img_host = "ws://" + API_URL_v21
        elif version == "1.5":
            self.img_host = "wss://" + API_URL_v15

    def on_open(self, img_ws):
        self.times += 1
        img_ws.send(json.dumps(self.wssRq))

    def on_message(self, img_ws, message):
        msg = json.loads(message)

        if msg["msg"] == "queue_full":
            if self.times < 5:
                # raise
                err = ChatbotError("ConnectionError", "Public API of Stable Diffusion V2.1 is busy, try it later", -2)
                send_txt_msg(text_string=err.__str__(), wx_id=self.room_id if self.is_room else self.wx_id)
            else:
                self.times += 1
                img_ws.send(json.dumps(self.wssRq))

        elif msg["msg"] == "send_data":
            process = {
                "data": [self.prompt[0], "" if len(self.prompt) == 1 else self.prompt[1], 9],
                "fn_index": 3
            }
            img_ws.send(json.dumps(process))

        elif msg["msg"] == "process_starts":
            logging.info(message)

        elif msg["msg"] == "process_completed":
            for item in msg["output"]["data"][0]:
                source_str = base64.urlsafe_b64decode(item[23:])
                filename = self.wx_id + "_" + self.room_id + "_" + getid() + ".jpg"
                if not os.path.exists(".cache/"):
                    os.makedirs(cache_dir)
                with open(cache_dir + filename, "wb") as file_object:
                    file_object.write(source_str)
                file_object.close()

                self.ws.send(send_pic_msg(wx_id=self.room_id if self.is_room else self.wx_id,
                                          content=os.path.join(os.path.abspath(cache_dir), filename)))
                time.sleep(1.0)
                if isCached:
                    logging.info("Image cached! Name: " + cache_dir + filename)
                else:
                    os.remove(cache_dir + filename)

    def on_error(self, img_ws, error):
        logging.info(error)

    def on_close(self, img_ws):
        logging.info("Stable Diffusion V" + self.version + " arts are done!")

    def play(self):
        self.img_ws = websocket.WebSocketApp(self.img_host,
                                             on_open=self.on_open,
                                             on_message=self.on_message,
                                             on_error=self.on_error,
                                             on_close=self.on_close,
                                             )
        self.img_ws.keep_running = False
        self.img_ws.run_forever()



import logging
from typing import Iterable
from flask import Flask, abort
from flask import request
import jsonpath
import json
import traceback

from basic.task import NormalTask
from multithread.threads import nrm_que
from client.wxclient import ws
from shared.shared import webHooKSecret

app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def do_webhook():
    logging.info("request.headers: %s", request.headers)
    authorization = request.headers.get('Authorization')
    if authorization is None:
        authorization = request.args.get("key")
    if authorization is None or authorization != webHooKSecret:
        abort(403) 
    try:
        if request.method == "POST":
            msg_title_field = request.args.get("msg_title_field")
            msg_content_field = request.args.get("msg_content_field")
            if msg_title_field is None:
                msg_title_field = 'title'
            if msg_content_field is None:
                msg_content_field = 'content'
            content_type = request.headers.get('Content-Type')
            if "multipart/form-data" in content_type:
                form_data = dict(request.form)
                # files_data = dict(request.files)
                res, wx_id, room_id = parse_request(msg_title_field, msg_content_field, form_data)
                res = str(res)
                wx_id = str(wx_id)
                room_id = str(room_id)
            elif "application/json" in content_type:
                # request.get_data() # 原始的数据
                input_dict = request.get_json()
                logging.info("request body: %s", input_dict)
                res, wx_id, room_id = parse_request(msg_title_field, msg_content_field, input_dict)

            elif "application/x-www-form-urlencoded" in content_type:
                input_dict = request.form
                res, wx_id, room_id = parse_request(msg_title_field, msg_content_field, input_dict)
                # request.values.get("content")
            else:
                logging.warning(request.get_data())
                abort(500)

        print('url: %s , script_root: %s , path: %s , base_url: %s , url_root : %s' % (
            request.url, request.script_root, request.path, request.base_url, request.url_root))
        if wx_id is None:
            wx_id = request.args.get('wx_id')
        if room_id is None:
            room_id = request.args.get('room_id')
        if wx_id is None and room_id is None:
            return json.dumps({"code": -1, "msg":"please set receiver", "data": 0})
        nm = NormalTask(ws, "", res, wx_id, room_id, room_id is not None and len(room_id) > 0, False)
        nrm_que.put(nm)
        return json.dumps({"code": 0, "msg":"success", "data": res})
    except:
        err_msg = 'url: %s, err_msg: %s' % (request.url, (str(traceback.format_exc())))
        logging.error(err_msg)
        return json.dumps({"code": -1, "msg":"failed", "data": 0})

def parse_request(msg_title_field, msg_content_field, input_dict):
    res = ''
    try:
        titles = jsonpath.jsonpath(input_dict, msg_title_field)
        contents = jsonpath.jsonpath(input_dict, msg_content_field)
        if isinstance(titles, Iterable) and isinstance(contents, Iterable) :
            for title, content in zip(titles, contents):
                res += "=================\n"
                res += title
                res += "\n"
                res += content
                res += "\n\n"
    except:
        err_msg = 'parse_request error , err_msg: %s' % (str(traceback.format_exc()))
        logging.error(err_msg)
        res =  json.dumps(input_dict, indent = 4, ensure_ascii= False)
    wx_id = input_dict.get('wx_id')
    room_id = input_dict.get('room_id')
    if len(res) == 0:
        title = input_dict.get(msg_title_field)
        if title is not None:
            res += title + "\n"
        content = input_dict.get(msg_content_field)
        if content is not None:
            res += content + "\n"
        if len(res) == 0:
            res =  json.dumps(input_dict, indent = 4, ensure_ascii= False)
    return res, wx_id, room_id
    
@app.route('/uptime/webhook', methods=['POST'])
def do_uptime():
    logging.info("request.headers: %s", request.headers)
    authorization = request.headers.get('Authorization')
    if authorization is None:
        authorization = request.args.get("key")
    if authorization is None or authorization != webHooKSecret:
        abort(403) 
    try:
        if request.method == "POST":
            content_type = request.headers.get('Content-Type')
            if "multipart/form-data" in content_type:
                form_data = dict(request.form)
                # files_data = dict(request.files)

                heartbeat = str(form_data.get('heartbeat'))
                monitor = str(form_data.get('monitor'))
                msg = str(form_data.get('msg'))
                wx_id = str(form_data.get('wx_id'))
                room_id = str(form_data.get('room_id'))
                res = ''
                if heartbeat is not None:
                    logging.info("heartbeat: %s", heartbeat)
                if monitor is not None:
                    logging.info("monitor: %s", monitor)
                    res +=  monitor.get('name')
                    res += "\n\n"
                if msg is not None:
                    res += msg
            elif "application/json" in content_type:
                # request.get_data() # 原始的数据
                input_dict = request.get_json()
                heartbeat = input_dict.get('heartbeat')
                monitor = input_dict.get('monitor')
                msg = input_dict.get('msg')
                wx_id = input_dict.get('wx_id')
                room_id = input_dict.get('room_id')
                res = ''
                if heartbeat is not None:
                    logging.info("heartbeat: %s", heartbeat)
                if monitor is not None:
                    logging.info("monitor: %s", monitor)
                    res +=  monitor.get('name')
                    res += "\n\n"
                if msg is not None:
                    res += msg

            elif "application/x-www-form-urlencoded" in content_type:
                input_dict = request.form
                heartbeat = input_dict.get('heartbeat')
                monitor = input_dict.get('monitor')
                msg = input_dict.get('msg')
                wx_id = input_dict.get('wx_id')
                room_id = input_dict.get('room_id')
                res = ''
                if heartbeat is not None:
                    logging.info("heartbeat: %s", heartbeat)
                if monitor is not None:
                    logging.info("monitor: %s", monitor)
                    res +=  monitor.get('name')
                    res += "\n\n"
                if msg is not None:
                    res += msg
            else:
                print(request.get_data())

        print('url: %s , script_root: %s , path: %s , base_url: %s , url_root : %s' % (
            request.url, request.script_root, request.path, request.base_url, request.url_root))
        if wx_id is None:
            wx_id = request.args.get('wx_id')
        if room_id is None:
            room_id = request.args.get('room_id')
        if wx_id is None and room_id is None:
            return json.dumps({"code": -1, "msg":"please set receiver", "data": 0})
        nm = NormalTask(ws, "", res, wx_id, room_id, room_id is not None and len(room_id) > 0, False)
        nrm_que.put(nm)
        return json.dumps({"code": 0, "msg":"success", "data": res})
    except:
        err_msg = 'url: %s, err_msg: %s' % (request.url, (str(traceback.format_exc())))
        print(err_msg)
        return json.dumps({"code": -1, "msg":"failed", "data": 0})
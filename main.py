import signal
import threading
from client.wxclient import ws
import logging
import logging.config
import yaml
from yaml.loader import SafeLoader
from webhook.webhook import app
from gevent import pywsgi
import os

def handler():
    logging("监听到关闭信号 关闭ws....")
    ws.close()

def setup_logging(default_path='.config/logger_config.yaml', default_level=logging.INFO):
    path = default_path
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.load(f, SafeLoader)
            logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)

if __name__ == "__main__":
    log_path = 'logs'
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    setup_logging()
    wst = threading.Thread(target=ws.run_forever, kwargs={"ping_interval": 15})
    wst.daemon = True
    wst.start()
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGHUP, handler)

    server = pywsgi.WSGIServer(('0.0.0.0', 6006), app)
    server.serve_forever()


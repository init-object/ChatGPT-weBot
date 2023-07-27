from client.wxclient import ws
import logging
import logging.config
import yaml
from yaml.loader import SafeLoader
import os

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
    ws.run_forever(ping_interval=15)

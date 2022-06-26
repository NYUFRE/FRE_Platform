import subprocess
import threading
import time
import warnings
from sys import platform

from flask import render_template
from sqlalchemy.exc import SAWarning

from system.services.sim_trading.client import client_config

warnings.simplefilter(action='ignore', category=SAWarning)


def start_server_process():
    cmd = "( python.exe server.py )" if platform == "win32" else "python server.py"
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True)
    while True:
        output = process.stdout.readline()
        if client_config.server_tombstone:
            return

        if output and not client_config.server_ready:
            print(output.strip())
            time.sleep(5)
            client_config.server_ready = True


def sim_server_up_service():
    if not client_config.server_ready:
        client_config.server_tombstone = False
        server_thread = threading.Thread(target=(start_server_process))
        server_thread.start()
        print("Launching Server")

        while not client_config.server_ready:
            pass

    return render_template("sim_launch_server.html")
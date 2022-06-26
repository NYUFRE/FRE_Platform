import os
import os
import warnings

from flask import render_template
from sqlalchemy.exc import SAWarning

warnings.simplefilter(action='ignore', category=SAWarning)


def hf_cleaning_data_service():
    import subprocess
    project_root = os.path.join(os.path.dirname(os.path.realpath(__file__)), "system")
    cleaning_process_path = os.path.join(os.path.join(project_root, "hf_trading"), "Capstone_Project")
    os.chdir(os.path.join(project_root, "hf_trading"))
    subprocess.run(cleaning_process_path, shell=True, check=True)
    # subprocess.call("/Users/yirenwu/Desktop/nyu_class/Fall_2021/research/Capstone_Project/cmake-build-debug/Capstone_Project")
    return render_template("hf_cleaning_data.html")
import warnings
from flask import render_template
from sqlalchemy.exc import SAWarning
from system import process_list
from system.services.utility.helpers import get_python_pid

warnings.simplefilter(action='ignore', category=SAWarning)


def root_service():
    process_list.update(get_python_pid())
    return render_template('index.html')

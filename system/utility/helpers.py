import os
import sys
from typing import List, Set

import requests
import urllib.parse

from sys import platform
from flask import flash, redirect, render_template, session
from functools import wraps
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError


def error_page(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s

    error_code = 'error code: ' + str(code)
    flash('ERROR! ' + message, error_code)
    return render_template("error_page.html"), code


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return error_page(e.name, e.code)


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""

    # Contact API
    try:
        api_key = os.environ.get("API_KEY")
        response = requests.get(
            f"https://cloud-sse.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={api_key}")
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        return {
            "name": quote["companyName"],
            "price": float(quote["latestPrice"]),
            "symbol": quote["symbol"]
        }
    except (KeyError, TypeError, ValueError):
        return None


def usd(value):
    """Format value as USD."""
    if value is None:
        value = 0
    return f"${value:,.2f}"

  
def get_python_pid() -> Set[int]:
    process_list = set()

    if platform == "win32":
        with os.popen('wmic process get description, processid') as ps:
            output = ps.read()
            target_process = "python"
            for line in output.splitlines():
                line = line.strip()
                if target_process in str(line):
                    process_list.add(int(line.split(' ', 1)[1].strip()))


    # Mac
    if platform == "darwin" or platform == "linux":
        with os.popen("""ps aux | awk -v user=$(whoami) '$1==user' | grep python | awk '{print $2}'""") as ps:
            output = ps.read().split("\n")
            for pid in output:
                if len(pid) > 0:
                    process_list.add(int(pid))

    return process_list


class FREWriter:
    """A simple logging class for FRE platform."""
    def __init__(self, stdout, filename):
        self.stdout = stdout
        self.logfile = open(filename, 'a')

    def write(self, text):
        self.stdout.write(text)
        self.logfile.write(text)

    def close(self):
        self.stdout.close()
        self.logfile.close()

    def flush(self):
        pass


sys.stdout = FREWriter(sys.stdout, 'FRE_Platform.log')
sys.stderr = FREWriter(sys.stderr, 'FRE_Platform.log')

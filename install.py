# This script is meant to solve installation issues
#  by providing more conditions.

import subprocess
import sys
import platform

common =  [
    "bcrypt==3.2.0",
    "blinker==1.4",
    "cachelib==0.1.1",
    "certifi==2020.6.20",
    "cffi==1.14.4",
    "chardet==3.0.4",
    "click==7.1.2",
    "convertdate==2.2.1",
    "cycler==0.10.0",
    "dnspython==2.0.0",
    "email-validator==1.1.2",
    "fields==5.0.0",
    "Flask==1.1.2",
    "Flask-Bcrypt==0.7.1",
    "Flask-Login==0.5.0",
    "Flask-Mail==0.9.1",
    "Flask-Session==0.3.2",
    "Flask-SQLAlchemy==2.4.4",
    "Flask-Uploads==0.2.1",
    "Flask-WTF==0.14.3",
    "holidays==0.10.3",
    "idna==2.10",
    "itsdangerous==1.1.0",
    "Jinja2==2.11.2",
    "kiwisolver==1.2.0",
    "korean-lunar-calendar==0.2.1",
    "MarkupSafe==1.1.1",
    "matplotlib==3.4.3",
    "numpy==1.20.1",
    "pandas==1.0.5",
    "pandas-market-calendars==1.6.1",
    "passlib==1.7.2",
    "patsy==0.5.1",
    "Pillow==7.2.0",
    "plotly==4.14.3",
    "pycparser==2.20",
    "PyMeeus==0.3.7",
    "pyparsing==2.4.7",
    "python-dateutil==2.8.1",
    "pytz==2020.1",
    "QuantLib==1.22",
    "requests==2.24.0",
    "retrying==1.3.3",
    "scipy==1.7.1",  # Previous scipy version: 1.5.2
    "six==1.15.0",
    "SQLAlchemy==1.3.18",
    "statsmodels==0.11.1",
    "texttable==1.6.2",
    "toolz==0.11.1",
    "trading-calendars==2.1.0",
    "urllib3==1.25.9",
    "Werkzeug==1.0.1",
    "WTForms==2.3.3",
    "yahoo_earnings_calendar==0.6.0",
    "yfinance==0.1.63",
    "tqdm==4.62.1",
    "pyportfolioopt==1.4.2",
    "beautifulsoup4==4.10.0",  # BeautifulSoup for web crawling
]

windows = [
    "TA_Lib-0.4.21-cp38-cp38-win_amd64.whl",
]

darwin = [  # Mac OS
    "TA_Lib==0.4.21",
]

linux = [
    "TA_Lib==0.4.21",
]

def install(packages):
    for p in packages:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', p])

if __name__ == '__main__':
    python_version = platform.python_version()

    if sys.version_info.major != 3:
        sys.stderr.write("Installing packages requires python3 (currently running %s).\n" % python_version)
        sys.exit(1)

    if sys.version_info.minor == 9:
        sys.stderr.write("python3.9 is incompatible with certain packages. Please switch to a lower python3 version.\n")
        sys.exit(1)

    install(common)
    host_platform = platform.system()

    if host_platform == 'Windows':
        install(windows)
    if host_platform == 'Darwin':
        install(darwin)
    if host_platform == 'Linux':
        install(linux)

# This script is meant to solve installation issues
#  by providing more conditions.

import subprocess
import sys
import platform

common =  [
    "arch==7.0.0",
    "bcrypt==4.2.0",
    "beautifulsoup4==4.12.3",
    "blinker==1.8.2",
    "cachelib==0.13.10",
    "certifi==2024.8.30",
    "cffi==1.17.1",
    "chardet==5.2.0",
    "click==8.1.7",
    "convertdate==2.4.0",
    "cycler==0.12.1",
    "dnspython==2.6.1",
    "email-validator==2.2.0",
    "fields==5.0.0",
    "Flask==3.0.3",
    "Flask-Bcrypt==1.0.1",
    "Flask-Login==0.6.3",
    "Flask-Mail==0.10.0",
    "Flask-Session==0.8.0",
    "Flask-SQLAlchemy==3.1.1",
    "Flask-Uploads==0.2.1",
    "Flask-WTF==1.2.1",
    "holidays==0.56",
    "idna==3.8",
    "itsdangerous==2.2.0",
    "Jinja2==3.1.4",
    "Keras==3.5.0",
    "kiwisolver==1.4.7",
    "korean-lunar-calendar==0.3.1",
    "MarkupSafe==2.1.5",
    "matplotlib==3.9.2",
    "numpy==2.1.1",
    "pandas==2.2.2",
    "pandas-market-calendars==4.4.1",
    "passlib==1.7.4",
    "patsy==0.5.6",
    "pdfkit==1.0.0",
    "Pillow==10.4.0",
    "plotly==5.24.1",
    "pycparser==2.22",
    "PyMeeus==0.5.12",
    "pyparsing==3.1.4",
    "pyportfolioopt==1.5.5",
    "python-dateutil==2.9.0"
    "pytz==2024.2",
    "QuantLib==1.35",
    "requests==2.32.3",
    "retrying==1.3.4",
    "scikit-learn==1.5.2",
    "scipy==1.14.1",
    "six==1.16.0",
    "SQLAlchemy==2.0.34",
    "statsmodels==0.14.2",
    "tensorflow==2.17.0",
    "texttable==1.7.0",
    "toolz==0.12.1",
    "trading-calendars==2.1.1",
    "urllib3==2.2.3",
    "Werkzeug==3.0.4",
    "WTForms==3.1.2",
    "yahoo_earnings_calendar==0.6.0",
    "yfinance==0.2.43",
    "tqdm==4.66.5",
    "nltk==3.9.1",
    "snscrape==0.7.0.20230622",
    "emoji==2.12.1",
    "PyAlgoTrade==0.20"

]

windows = [
    "ta_lib-0.4.28-cp311-cp311-win_amd64.whl",
]

darwin = [  # Mac OS
    "TA_Lib==0.4.28",
]

linux = [
    "TA_Lib==0.4.28",
]

def install(packages):
    for p in packages:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', p])

if __name__ == '__main__':
    python_version = platform.python_version()

    if sys.version_info.major != 3:
        sys.stderr.write("Installing packages requires python3 (currently running %s).\n" % python_version)
        sys.exit(1)

    if sys.version_info.minor == 12:
        sys.stderr.write("python3.12 is incompatible with certain packages. Please switch to a lower python3 version.\n")
        sys.exit(1)

    install(common)
    host_platform = platform.system()

    if host_platform == 'Windows':
        install(windows)
    if host_platform == 'Darwin':
        install(darwin)
    if host_platform == 'Linux':
        install(linux)

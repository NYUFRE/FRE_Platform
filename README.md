# FRE Platform #
* *Environment* run as a Python vritual env
* *Author:* Song Tang <st290@nyu.edu>.  
* *Details:* FRE Platform has Flask web interface, historical and realtime market data feeds, integrated databases, messaging framework, and stock market simulation. It supports trading model plugin and machine learning logic development.

## Requirements
* Python 3.x
* bcrypt==3.2.0
* blinker==1.4
* cachelib==0.1.1
* certifi==2020.6.20
* cffi==1.14.4
* chardet==3.0.4
* click==7.1.2
* convertdate==2.2.1
* cycler==0.10.0
* dnspython==2.0.0
* email-validator==1.1.2
* fields==5.0.0
* Flask==1.1.2
* Flask-Bcrypt==0.7.1
* Flask-Login==0.5.0
* Flask-Mail==0.9.1
* Flask-Session==0.3.2
* Flask-SQLAlchemy==2.4.4
* Flask-Uploads==0.2.1
* Flask-WTF==0.14.3
* holidays==0.10.3
* idna==2.10
* itsdangerous==1.1.0
* Jinja2==2.11.2
* kiwisolver==1.2.0
* korean-lunar-calendar==0.2.1
* MarkupSafe==1.1.1
* matplotlib==3.3.0
* numpy==1.19.1
* pandas==1.0.5
* pandas-market-calendars==1.6.1
* passlib==1.7.2
* patsy==0.5.1
* Pillow==7.2.0
* pycparser==2.20
* PyMeeus==0.3.7
* pyparsing==2.4.7
* python-dateutil==2.8.1
* pytz==2020.1
* requests==2.24.0
* scipy==1.5.2
* six==1.15.0
* SQLAlchemy==1.3.18
* statsmodels==0.11.1
* texttable==1.6.2
* toolz==0.11.1
* trading-calendars==2.1.0
* urllib3==1.25.9
* Werkzeug==1.0.1
* WTForms==2.3.3

## Installing Requirements
```
pip install -r requirements.txt
```

## Run Project
### With Docker
```sh
cd ./docker
docker-compose up --build
```

### Without Docker
```sh
Please modify file path in fre_client/client.cfg from SocketConnectHost=acceptor to SocketConnectHost=<Your IP>
```
```sh
cd ./fre_server
python server.py -cfg server.cfg
```
```sh
cd ./fre_client
python client.py -cfg client.cfg
```



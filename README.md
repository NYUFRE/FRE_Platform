# FRE Platform #
* *Environment* run as a Python vritual env
* *Authors* Song Tang <st290@nyu.edu>, Qijia Lou <qijia.lou@nyu.edu>, Zicheng He <zh1345@nyu.edu>, Albert Lee <al3406@nyu.edu>, Xiao Liu <xl2951@nyu.edu>, Koda Song <ks5416@nyu.edu>, Jiaxin Zhang <jz3796@nyu.edu> 
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
Either build from source or pull from docker cloud repository.

Build from local source code:
```sh
docker build -t fre .
```
Pull from docker repository
```sh
docker pull <repository>/<image name>
```
Run single instance 
```sh
docker run --name test -p 5001:5000 -v "<instance folder>":/app/instance -d fre python app.py
```
Arguments explain:

`--name test`: Name container to test

`-p` 5001: 5000: mapping host 5001 port to container 5000 port. host 5001 port is an arbitrary choice, can be any port as long as it is available. (Mac may request perm to use some ports)

`-v`:  "<instance folder>":/app/instance mapping host direactory to container direactory

`-d`: run as daemon

`fre`: image name, if pulled from docker repository, this should be <repository name>/<image name>

`python app.py`: run "python app.py" in this container

Helpful docker cmd:

sh into a running container: `docker exec -it <container name> bash`

show log: `docker logs <container name>`

show all local image: `docker images`

show all containers: `docker ps -a`

stop container: `docker stop <container name>`

remove container: `docker rm <container name>`
(stop doesn't release the resource, rm is required if you want to permanently close the container)

remove local image: `docker rmi <image name>`

### Potential further improvements for containerizing this project 
Although it is possible  to run multi-processes in one docker container, it is generally discouraged. 

From [Docker 
documentation](https://docs.docker.com/config/containers/multi-service_container/)

> It is generally recommended that you separate areas of concern by using one service per container. 
> That service may fork into multiple processes (for example, Apache web server starts multiple worker processes). 
> It’s ok to have multiple processes, but to get the most benefit out of Docker, avoid one container 
> being responsible for multiple aspects of your overall application. You can connect multiple containers 
>using user-defined networks and shared volumes.  

A further improvement could be decoupling server from client code and make server a long running daemon process.


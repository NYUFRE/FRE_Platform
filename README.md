# FRE Platform #
* *Established connection by* [FIX protocol](https://www.fixtrading.org/standards/)  
* *Author:* Song Tang <st290@nyu.edu>.  
* *Details:* [Configuration for quickfix](http://www.quickfixengine.org/quickfix/doc/html/configuration.html)  

## Requirements
* Python 3.x
* [QuickFIX Engine 1.15.1](http://www.quickfixengine.org/)

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



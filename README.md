# FRE Platform #
* *Environment* run in a Python vritual env or Docker container
* *Authors* Song Tang <st290@nyu.edu>, Qijia Lou <qijia.lou@nyu.edu>, Zicheng He <zh1345@nyu.edu>, Albert Lee <al3406@nyu.edu>, Xiao Liu <xl2951@nyu.edu>, Koda Song <ks5416@nyu.edu>, Jiaxin Zhang <jz3796@nyu.edu> 
* *Details:* FRE Platform has Flask web interface, historical and realtime market data feeds, integrated databases, messaging framework, and stock market simulation. It supports trading model plugin and machine learning logic development.


## Launch FRE Platform
### With Virtual Env
After clone the FRE_Platform repo from Github, create the virtualenv directory in FRE_Platform
```
python -m venv venv

You may need to use to python3 instead of python, please run python -V to verify your version before doing this.
```
Activate the virtual env
```
.\venv\Scripts\activate

If you are using MAC computer, using

source venv/bin/activate

```
Install the required packages (Run Python -V to check the Python version in your virtual env, version 3.8 or 3.9 is preferred)
```
python install.py
```
Create the instance directory in FRE_Platform and load flask.cfg into the instance directory

Set PYTHONPATH pointing to your FRE_Platform such as
```
set PYTHONPATH="C:\NYUFRE\FRE_Platform\FRE_Platform"
```
Launch the platform
```
python app.py
```
Stop the platform by Ctrl-C and deactivate the virtualenv
```
.\venv\Script\deactivate.bat 
```

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

## Git Instructions
Fork a repo to your own account

Create a directory called NYUFRE and Clone FRE_Platform Remote Repo
```
git clone https://github.com/NYUFRE/FRE_Platform
```
Add upstream repo
```
git remote add upstream https://github.com/NYUFRE/FRE_Platform
```
Sync with upstream(recommend doing it every time before checking out a new branch) 
```
git fetch upstream
```

Check status of your current branch, should be master
```
cd FRE_Platform
git status
```
Sync your local repo with the remote repo
```
git pull
```
Create a working branch for your changes 
```
git checkout -b feature/feature-name
```
Diff between your changes and the original
```
git diff
```
Add your changes to the staging area
```
git add some_file.py
# or simply 
git add .
```
Commit your changes
```
git commit -m "Add feature-xyz"
```
Push your change to the remote repo
```
git push -u origin feature/feature-name
```
Create a Pull Request on Github
## Issue report
From upstream repo's [GitHub Issue](https://github.com/NYUFRE/FRE_Platform/issues)
## Documentation
[FRE Platform Documentation](https://nyufre.github.io/FRE_Platform/)

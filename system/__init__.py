#################
#### imports ####
#################
 
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail

import os
from tempfile import mkdtemp

from system.utility.helpers import usd
from flask_session import Session

from system.market_data.fre_market_data import IEXMarketData
from system.market_data.fre_market_data import EODMarketData
from system.database.fre_database import FREDatabase


################
#### config ####
################

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('flask.cfg')
app.config["TEMPLATES_AUTO_RELOAD"] = True

os.environ["IEX_API_KEY"] = app.config['IEX_API_KEY']
os.environ["EOD_API_KEY"] = app.config['EOD_API_KEY']

# Make sure API key is set
if not os.environ.get("IEX_API_KEY"):
    raise RuntimeError("IEX_API_KEY not set")

if not os.environ.get("EOD_API_KEY"):
    raise RuntimeError("EOD_API_KEY not set")

# Ensure responses not cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

database = FREDatabase(app.config["SQLALCHEMY_DATABASE_URI"])
iex_market_data = IEXMarketData(os.environ.get("IEX_API_KEY"))
eod_market_data = EODMarketData(os.environ.get("EOD_API_KEY"), database)

process_list = []

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

 
from system.portfolio.models import User
 
@login_manager.user_loader
def load_user(user_id):
    return User.query.filter(User.user_id == int(user_id)).first()



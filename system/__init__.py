#################
#### imports ####
#################
 
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail
#####from flask_uploads import UploadSet, IMAGES, configure_uploads

#from flask import Flask, redirect, render_template, request, session, url_for, make_response
#from flask_session import Session
#from werkzeug.security import check_password_hash, generate_password_hash

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

os.environ["IEX_API_KEY"] = "sk_6ced41d910224dd384355b65b085e529"
os.environ["EOD_API_KEY"] = "5ba84ea974ab42.45160048"

# Make sure API key is set
if not os.environ.get("IEX_API_KEY"):
    raise RuntimeError("IEX_API_KEY not set")

if not os.environ.get("EOD_API_KEY"):
    raise RuntimeError("EOD_API_KEY not set")
 
app = Flask(__name__, instance_relative_config=True)
#app = Flask(__name__)
app.config.from_pyfile('flask.cfg')
app.config["TEMPLATES_AUTO_RELOAD"] = True


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

database = FREDatabase()
iex_market_data = IEXMarketData(os.environ.get("IEX_API_KEY"))
eod_market_data = EODMarketData(os.environ.get("EOD_API_KEY"), database)

process_list = []

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "users.login"
 
# Configure the image uploading via Flask-Uploads
####images = UploadSet('images', IMAGES)
####configure_uploads(app, images)
 
from system.portfolio.models import User
 
@login_manager.user_loader
def load_user(user_id):
    return User.query.filter(User.id == int(user_id)).first()
 
####################
#### blueprints ####
####################
 
####### from project.users.views import users_blueprint
####### from project.recipes.views import recipes_blueprint
 
# register the blueprints
####### app.register_blueprint(users_blueprint)
####### app.register_blueprint(recipes_blueprint)

############################
#### custom error pages ####
############################
 
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
 
 
@app.errorhandler(403)
def page_not_found(e):
    return render_template('403.html'), 403
 
 
@app.errorhandler(410)
def page_not_found(e):
    return render_template('410.html'), 410


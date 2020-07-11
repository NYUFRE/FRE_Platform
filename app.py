from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy import Table

from flask import Flask, flash, redirect, jsonify, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp

import time
import csv
import os
import urllib.request

from helpers import apology, login_required, lookup, usd



#from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
#from werkzeug.security import check_password_hash, generate_password_hash



os.environ["API_KEY"] = "sk_6ced41d910224dd384355b65b085e529"

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
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

# Configure CS50 Library to use SQLite database
#db = SQL("sqlite:///finance.db")

engine = create_engine('sqlite:///finance.db')
conn = engine.connect()
conn.execute("PRAGMA foreign_keys = ON")

# MetaData is a container object that keeps together many different features of a database 
metadata = MetaData()
metadata.reflect(bind=engine)

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    #display what the user currently own, in other words, the info in the portfolio table 
    #use the id--the primary key, to find username 
    result = engine.execute('SELECT*FROM users WHERE id=:id', id=session['user_id'])
    row = result.fetchall()
    cash = row[0]['cash']
    #define username
    user = row[0]["username"]
    
    #look for the rows in the portfolio table by username--get all the purchase/sale data under the user who is currently logged in 
    result = engine.execute("SELECT * FROM portfolio WHERE username=:username", username=user)
    user_portfolio = result.fetchall()
    #if the user has made purchase/sale, get the data, put it in the dict, and display it on index 
    if len(user_portfolio) > 0: 
        #create the dict 
        dict={}
        dict['Symbol']=[]
        dict['Name']=[]
        dict['Shares']=[]
        dict['Price']=[]
        dict['Total']=[]
    
        #if the user has made purchase/sale, get the data, put it in the dict, and display it on index 
        result = engine.execute('SELECT*FROM portfolio WHERE username=:username', username=user)
        rows = result.fetchall()
        #calculate the total amount of money
        t = 0
        
        #make the for loop 
        for row in rows:
            #append--add the parameter to the list, in this case, dict["Symbol"]
            #this for loop adds all the ['key'] values in rows to the cooresponding dict, which are displayed on index 
            dict['Symbol'].append(row['symbol'])
            dict['Shares'].append(row['shares'])
            
            #for every symbol, look up the price 
            symbol=row['symbol']
            quote = lookup(symbol)
            price=quote["price"]
            
            #calculate the total of each purchase:
            #for each row, grab the number of shares, and multiply it by the price 
            shares=row['shares']
            total=price*shares
            
            #add all the totals together 
            t=t + total
            
            #continue to append the parameters into the dict 
            dict['Name'].append(quote['name'])
            dict['Price'].append(usd(quote['price']))
            dict['Total'].append(usd(total))
        
        #add the final total to cash=the total value of the stocks and the cash--the total value of the user's property
        t = t + cash
        
        #the variable length--how many row there are 
        length=len(dict['Symbol'])
        
        #return to the index and display the info about the stocks currently owned by the user, cash and the total 
        #pass on the variables so that the html file can 'see' and display them
        return render_template('index.html',dict=dict,t=t,cash=cash,length=length)
        
    #if the user has not made any purchase, then the length will be zero, the total will be cash, and the dict will be empty
    else:
        return render_template("index.html",length=0,cash=cash,t=cash,dict=[])

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method=="POST":
        symbol = request.form.get('symbol')
        shares = int(request.form.get('shares'))
        #quote is a dictionary 
        quote = lookup(symbol)
        id=session['user_id']
        
        if not symbol:
            return apology('Symbol can not be blank!')
        if not quote:
            return apology("symbol does not exist")
        if not shares > 0:
            return apology("Shares must be positive!")
        if not shares:
            return apology("Shares cannot be blank!!")
            
        #price=value, use the dict--quote to match up the values 'price'
        # ["name"] is used for dict in python 
        price = quote['price']
        result = engine.execute("SELECT * FROM users WHERE id=:id", id=session['user_id'])
        rows = result.fetchall()
        cash = rows[0]["cash"]
        username = rows[0]['username']
        total= price*shares
        transacted=time.strftime("%H:%M:%S %d/%m/%Y")
        
        #ensure that the user can afford the stocks 
        if total>cash:
            return apology("Sorry, too many stocks!")
        #if the user can afford, update the cash and insert the purchase data into the history table 
        else:
            cash=cash-total
            engine.execute("UPDATE users set cash=:cash where id=:id", cash=cash,id=session['user_id'])
            
            engine.execute("INSERT INTO history (symbol,shares,price,transacted,id)values (:symbol,:shares,:price,:transacted,:id)",symbol=symbol,shares=shares,price=price,transacted=transacted,id=id)
 
            #check if the user alreay owinns a certain stock
            result=engine.execute("SELECT*FROM portfolio Where username=:username And symbol=:symbol",username=username,symbol=symbol)
            user_portfolio=result.fetchall()   
            #if the user has this kind of stock, update the shares 
            if len(user_portfolio)>0:
                old_shares=user_portfolio[0]['shares']
                final_shares=old_shares+shares
                engine.execute('UPDATE portfolio set shares=:shares where username=:username AND symbol=:symbol',username=username,symbol=symbol,shares=final_shares)
           
            #if the user does not own this stock, insert a new row 
            else:
                engine.execute("INSERT INTO portfolio (username,shares,symbol) values (:username,:shares,:symbol)",username=username,symbol=symbol,shares=shares)
        #the "output" of the function--dircect the user to the index page, where the info is displayed 
        return redirect(url_for("index"))
    else:
        return render_template("buy.html")
        
    #get variables symbol and shares
    #symbol --> price and other stuff
    #check portfolio table to see if symbol already exists
    
    #price * shares
    #check to see if cash is enough
    #apology too many shares
    #INSERT or UPDATE number of shares / row, remember username

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    
    """Sell shares of stock."""
    if request.method=="POST":
        #call the symbol from the form as the user submit it
        symbol = request.form.get('symbol')
        shares=request.form.get('shares')
        #define the username by id
        #the username will be used as the key to look up the stock in the portfolio table
        id=session['user_id']
        result = engine.execute("SELECT * FROM users WHERE id=:id", id=id)
        rows = result.fetchall()
        username = rows[0]['username']
        #use the username and the symbol input by the user to see if the user owns that stock
        result=engine.execute('SELECT*FROM portfolio Where symbol=:symbol AND username=:username',symbol=symbol,username=username)
        #if there is no row, the user does not own this stock, then return an apology
        row = result.fetchall()
        if not symbol:
            return apology("Symbol cannot be blank!")
        if not shares:
            return apology("Shares cannot be blank!")
        if len(row)==0:
            return apology ("This stock does not exist in your account")
        
        def RepresentsInt(shares):
            try: 
                int(shares)
                return True
            except ValueError:
                return False
                
        #since the data type is text in the html, change it into inetger here
        if RepresentsInt(request.form.get('shares')):
            shares1 = int(request.form.get('shares'))
        else:
            return apology("Shares must be an integer!")
            
        if shares1<0:
            return apology('Shares must be positive!')
        
        #if there is a row (only one row since we are updating the data), take the symbol, old number of shares, and old cash from the table 
        symbol=row[0]["symbol"]
        shares2=row[0]["shares"]
        cash = rows[0]['cash']
        #calculate the new cash 
        shares3=shares2-shares1
        
        #if the user wants to sell more shares than she owns, return an apology 
        if shares1>shares2:
                return apology ("Too many stocks!")
        
        #since the symbol exists, use this to look up the current price 
        quote = lookup(symbol)
        price=quote["price"]
        #calculate the amount of money the user makes by selling the stocks 
        total=price*shares1
        #calculate the new_cash, which will be used to update the cash in the users table 
        new_cash=cash+total
        #get the negative value for history 
        shares4=0-shares1
        #get the time for history
        transacted=time.strftime("%H:%M:%S %d/%m/%Y")

        #insert the data into the history table
        engine.execute("INSERT INTO history (symbol,shares,price,transacted,id)values (:symbol,:shares,:price,:transacted,:id)",symbol=symbol,shares=shares4,price=price,transacted=transacted,id=id)

        #if the user is selling all the stocks of one kind that she has, delete that row in the portfolio table and update the cash in the users table 
        if shares3==0:
            engine.execute ("DELETE FROM portfolio WHERE username=:username AND symbol=:symbol",symbol=symbol,username=username)
            engine.execute("UPDATE users SET cash=:new_cash WHERE username=:username AND id=:id",id=id,username=username,new_cash=new_cash)
            
        #if the user is not selling all she has, update the data 
        if shares1<shares2:
            engine.execute("UPDATE portfolio set shares=:shares3 WHERE username=:username AND symbol=:symbol",symbol=symbol,username=username,shares3=shares3)
            engine.execute("UPDATE users SET cash=:new_cash WHERE username=:username AND id=:id",id=id,username=username,new_cash=new_cash)
        
        #after the user making a sale, return to the index page, and let the user see the change in the shares, cash and total (both the total for that stock and t)
        return redirect(url_for("index"))  
            
            
    else:
        return render_template("sell.html")

    
@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    id=session["user_id"]
    rows=engine.execute("SELECT*FROM history WHERE id=:id",id=id)
    #if len(rows)==0:
    #    return ("No history!")
            
    dict={}
    dict['Symbol']=[]
    dict['Shares']=[]                        
    dict['Price']=[]
    dict['transacted']=[]
            
    for row in rows:
        dict['Symbol'].append(row["symbol"])
        dict['Shares'].append(row["shares"])
        dict['Price'].append(row["price"])
        dict['transacted'].append(row["transacted"])           
        
    length=len(dict['Symbol'])
        
    return render_template("history.html",length=length,dict=dict)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        result = engine.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))
        rows = result.fetchall()
        # Ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("invalid username and/or password", 403)
        #if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
        #    return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    #return redirect("/")
    return redirect(url_for("login"))


#GET allows the user to get to the register page, while POST allows the data to be inserted into the database 
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    #if the user is not sending any input, return to the register page.  By doing so, we ensure the user is inputting username and password 
    if request.method=='POST':
        #request.form.get ("a") is slightly safer than request.form ["a"] when a exists 
        if not request.form.get ("username"):
            return apology("Missing Username")
    
        #if the username already exists    
        result = engine.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
        rows = result.fetchall()
        if len(rows) != 0:
            return apology("This username already exists")
    
        #if the password is blank:
        if not request.form.get ("password"):
            return apology("Missing password!")
        
        #if the password and the confirmation don't match 
        #for line250, both request.form.get["paswsword"] and quest.form("password") will work 
        if request.form.get("password")!=request.form.get("confirmation"):
            return apology("Passwords do not match!")
        else:
        #save the password as hash, encrypt it.  If anyone hacks into the database, he/she won't be able to see all the passwords

            hash=pwd_context.encrypt(request.form.get("password"))
            
            engine.execute("INSERT INTO users (username,hash) values(:username,:password)",username=request.form.get("username"),password=hash)
    
        #in this case, you are sure the username exists in the table, so stick with request.form.get("username")
        result = engine.execute("SELECT * FROM users WHERE username=:username", username=request.form.get('username'))
        rows = result.fetchall()
        # remember which user has logged in
        #session is the temporary memory.  The user info in stored in session.  Once the user log out, the session info may disappear 
        session["user_id"] = rows[0]["id"]
        
        #if the user completes the register without any mistake, she will be redirected to the index page.
        return redirect (url_for("index"))
        
        #if the method is not POST (which allows the user to input data into the user table), return to the register page 
        #in what case can the method be GET or whatever besides POST?
        
    else: return render_template ("register.html")

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    return render_template("ajax.html")

#get to the yahoo page 
@app.route("/get_quote")
def get_quote():
    url = "http://download.finance.yahoo.com/d/quotes.csv?f=snl1&s={}".format(request.args.get("symbol"))
    webpage = urllib.request.urlopen(url)
    #read the data, decode whatever yahoo gives back, breaks down the form into lines and then break down the line into words
    datareader = csv.reader(webpage.read().decode("utf-8").splitlines())
    row = next(datareader)
    return jsonify({"name": row[1], "price": float(row[2]), "symbol": row[0].upper()})
    # if not url:
    #     return apology('Symbol does not exist!')

# def quote():
#     if request.method=='POST':
#         #which form is symbol stored in?
#         symbol = request.form.get('symbol')
        
#         #calls the lookup function in helpers.py
#         #lookup is the function specified in helpers.py
#         #We are imputting the variabel symbol into the lookup function and assigning the output to be the variable quote 
#         quote = lookup(symbol)
        
#         #ensure the symbol ecists 
#         if not quote:
#             return apology("symbol does not exist")
            
#         #tells variable price to get the value from the ['price'] dict we got 
#         price = quote['price']
        
#         #change the unit to usd 
#         price=usd(price)
        
#         #tells the variable'name' to get the value from the dict ["name"] we got from quote
#         name = quote['name']
        
#         #successfully got all the variables, direct the user to quoted.html, pass on all the variables that will be displayed in quoted 
#         return render_template("quoted.html", price=price, symbol=symbol, name=name)
        
#         #if the method is not POST, return to quote.html
#     else:
#         return render_template("quote.html")

'''
def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
'''

if __name__ == "__main__":
        app.run()

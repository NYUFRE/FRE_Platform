
import warnings
import os
from flask import render_template, request, flash
from sqlalchemy.exc import SAWarning
from system import database
import pandas as pd
from system.services.twitter_sentiment_analysis.tsa_service import tsa_res, MLmodel, DataFetching, SentimentAnalyzer
from system.services.twitter_sentiment_analysis.Utils import *


warnings.simplefilter(action='ignore', category=SAWarning)


def tsa_builder_service():

    pulldownlist = [ 'K-Neighbors', 'Logistic-Regression', 'Neural-Network', 'Random-Forest', 'Support-Vector-Machine']
    modes = ['RealCase', 'Demo']
    default_start  = "2020-01-01"
    default_end = "2022-07-01"


    if request.method == "POST":
        model_ = request.form.get('model')
        startdate_ = request.form.get('startdate')
        enddate_ = request.form.get('enddate')
        MODE = request.form.get('mode')

        d0 = datetime.strptime(startdate_, "%Y-%m-%d")
        d1 = datetime.strptime(enddate_, "%Y-%m-%d")
        delta = d1 - d0
        
        if delta.days <= 365:
            flash(" :(  Date range must be greater than 365 days!")
            return render_template(
                "tsa_builder.html", 
                default_start = default_start,
                default_end = default_end,
                pulldownlist = pulldownlist,
                mlres = tsa_res.ml_res,  
                modes = modes
            )
        else:
            pass
        # using differenet data based on mode
        if MODE == 'Demo':
            # getting path ready!!
            curr = os.path.dirname(os.path.realpath(__file__))
            curr_p = os.path.abspath(os.path.join(curr, os.pardir))
            curr_pp = os.path.abspath(os.path.join(curr_p, os.pardir))
            path0 = os.path.join(curr_pp, "csv")
            path1 = os.path.join(path0, "twitter_demo.csv")
            # get data
            data = pd.read_csv(path1)
            data['Label'] = data['Adj_close'].diff().apply(lambda x: 0 if x<0 else 1).shift(-1)
            data.dropna(inplace=True)
            y = data['Label']
            X = data.drop(['Label','Adj_close','Date'], axis=1)

        elif MODE == 'RealCase' :

            prefix = "test"
            tb_TWTS = prefix + "Tweets"
            tb_MSFT = prefix + "MSFT"
            tb_ST = prefix + "Sentiments"
            tb_GS = prefix + "GroupSentiments"
            # DBhelper = db_helper(database.conn)

            if not (database.check_table_exists(tb_GS) and database.check_table_exists(tb_MSFT)):
                flash("Database empty, now loading data from internet")
                # loading data from web
                params_tweets = {
                    'Keywords': '#MSFT OR $MSFT',
                    'Start' : startdate_ + "T00:00:00Z",
                    'End' : enddate_ + "T00:00:00Z",
                    'Tweets_Limit' : None,
                }
                tweets_fetcher = DataFetching(params_tweets)
                tweets_analyzer = SentimentAnalyzer()

                flash("Downloading tweets...")
                if tweets_fetcher.data_download(): print("Tweets downloaded!")
                flash("Downlading Stocks...") 
                if tweets_fetcher.data_downlaod_stock(ticker='MSFT', start=startdate_ , end=enddate_):  print("Stocks downloaded!")
                tweets_fetcher.data_stock.rename(columns = {'Adj Close': 'Adj_close'}, inplace = True)
                flash("Analyzing...")
                if tweets_analyzer.analyze(tweets_fetcher.data): print("Analyzed!")
                
                # GS: group sentiments
                data_GS = refreq(tweets_analyzer.data, 'Datetime_utc', regroup_columns=['Likes', 'RetweetCount', 'QuoteCount', 'pos', 'neg', 'neu', 'compound'])
                data_GS.insert(0, 'Date', data_GS.index)
                data_GS.reset_index(drop=True, inplace=True)
                # print(data_GS)
                # print(data_GS.dtypes)
                # persist data into db
                sql_create_TWTS = f'''
                    Create Table if not exists {tb_TWTS} (
                        ID              integer     Primary Key Not Null,
                        Datetime_utc    text        Not Null,
                        Username        text        Not Null,
                        Url             text        Not Null,
                        Text            text        Not  Null,
                        Likes           integer     Not Null,
                        RetweetCount    integer     Not Null,
                        QuoteCount      integer     Not Null
                    )
                '''
                sql_create_ST = f'''
                    Create Table if not exists {tb_ST} (
                        ID              integer     Primary Key Not Null,
                        Datetime_utc    text        Not Null,
                        Likes           integer     Not Null,
                        RetweetCount    integer     Not Null,
                        QuoteCount      integer     Not Null,
                        pos             integer     Not Null,
                        neg             integer     Not Null,
                        neu             integer     Not Null,
                        compound        integer     Not Null,
                        FOREIGN KEY (ID) REFERENCES {tb_TWTS}(ID)
                    )
                '''
                sql_create_GS = f'''
                    Create Table if not exists {tb_GS} (
                        Date            text        Primary Key Not Null,
                        Likes           integer     Not Null,
                        RetweetCount    integer     Not Null,
                        QuoteCount      integer     Not Null,
                        pos             integer     Not Null,
                        neg             integer     Not Null,
                        neu             integer     Not Null,
                        compound        integer     Not Null
                    )
                '''
                sql_create_MSFT = f'''
                    Create Table if not exists {tb_MSFT} (
                        Date        text        Primary Key Not Null,
                        Open        real        Not Null,
                        High        real        Not Null,
                        Low         real        Not Null,
                        Close       real        Not Null,
                        Adj_close   real        Not Null,
                        Volume      integer     Not Null
                    )
                '''
                sql_insert_TWTS = f'''
                        Insert into 
                        {tb_TWTS}(ID, Datetime_utc, Username, Url, Text, Likes, RetweetCount, QuoteCount)
                        Values(?, ?, ?, ?, ?, ?, ?, ?)
                '''
                sql_insert_ST = f'''
                        Insert into 
                        {tb_ST}(ID, Datetime_utc, Likes, RetweetCount, QuoteCount, pos, neg, neu, compound)
                        Values(?, ?, ?, ?, ?, ?, ?, ?, ?)
                '''
                sql_insert_GS = f'''
                        Insert into 
                        {tb_GS}(Date, Likes, RetweetCount, QuoteCount, pos, neg, neu, compound)
                        Values(?, ?, ?, ?, ?, ?, ?, ?)
                '''
                sql_insert_MSFT = f'''
                        Insert into 
                        {tb_MSFT}(Date, Open, High, Low, Close, Adj_close, Volume)
                        Values(?, ?, ?, ?, ?, ?, ?)
                '''

                # create tables
                database.execute_sql_statement(sql_create_TWTS, change=True)
                database.execute_sql_statement(sql_create_ST, change=True)
                database.execute_sql_statement(sql_create_GS, change=True)
                database.execute_sql_statement(sql_create_MSFT, change=True)
                # persist data into database
                index_flg = False
                tweets_fetcher.data.to_sql(tb_TWTS, con=database.engine, if_exists='append', index=index_flg)
                tweets_fetcher.data_stock.to_sql(tb_MSFT, con=database.engine, if_exists='append', index=index_flg)
                tweets_analyzer.data.to_sql(tb_ST, con=database.engine, if_exists='append', index=index_flg)
                data_GS.to_sql(tb_GS, con=database.engine, if_exists='append', index=index_flg)

                flash("Database loaded! Please now run again to see the ML results")
                return render_template(
                    "tsa_builder.html", 
                    default_start = default_start,
                    default_end = default_end,
                    pulldownlist = pulldownlist, 
                    mlres = tsa_res.ml_res, 
                    modes = modes
                )
            
            # data loaded start to fetch from database
            flash("Database ready, now fetching data...")
            # have data and posted
            sql_select_data = f'''
            SELECT 
                gs.Date, gs.pos, gs.neg, gs.neu, gs.compound,  gs.Likes, gs.RetweetCount, gs.QuoteCount, m.Adj_close  
            from 
                {tb_GS} gs inner join {tb_MSFT} m on gs.Date = m.Date 
            ORDER by gs.Date ASC ;
            '''
            data = database.execute_sql_statement(sql_select_data)
            # processing
            data['Label'] = data['Adj_close'].diff().apply(lambda x: 0 if x<0 else 1).shift(-1)
            data.dropna(inplace=True)
            y = data['Label']
            X = data.drop(['Label','Adj_close','Date'], axis=1)

        # data fetching done, training models
        flash("Data fetched, start machine learning training...")
        
        if str(model_) == 'Support-Vector-Machine':
            params  = {
                'kernel': 'rbf',
                'C' : 0.5,
                'degree': 5
            }
            clf = MLmodel(model_, params, X, y)
            clf.fit()

        if str(model_) == 'Neural-Network':
            params  = {
                'layers': (2,2),
                'activation' : 'relu',
                'solver': 'adam',
                'alpha': 1,
                'random_state' : 10
            }
            clf = MLmodel(model_, params, X, y)
            clf.fit()

        if str(model_) == 'Random-Forest':
            params  = {
                'n_estimators' : 100,
                'max_depth' : 5,
                'criterion' : 'entropy',
                'random_state' : 10
            }
            clf = MLmodel(model_, params, X, y)
            clf.fit()
        
        if str(model_) == 'Logistic-Regression':
            params  = {
                'penalty' : 'l2',
                'C' : 0.01,
                'dual' : False,
                'random_state' : 10
            }
            clf = MLmodel(model_, params, X, y)
            clf.fit()

        if str(model_) == 'K-Neighbors':
            params  = {
                'n_neighbors' : 7,
                'weights' : 'distance',
                'algorithm' : 'auto',
                'leaf_size' : 40,
                'p' : 1
            }
            clf = MLmodel(model_, params, X, y)
            clf.fit()
        
        
        flash("Built successful! Everything is ready to go!")
        tsa_res.data = data
        tsa_res.ml_res = clf.res
        tsa_res.clf = clf
        tsa_res.MODE = MODE
        tsa_res.isBuilt = True
        return render_template(
            "tsa_builder.html", 
            default_start = default_start,
            default_end = default_end,
            pulldownlist = pulldownlist, 
            mlres = tsa_res.ml_res, 
            modes = modes
        )
    else:
        return render_template(
            "tsa_builder.html", 
            default_start = default_start,
            default_end = default_end,
            pulldownlist = pulldownlist,
            mlres = tsa_res.ml_res,  
            modes = modes
        )
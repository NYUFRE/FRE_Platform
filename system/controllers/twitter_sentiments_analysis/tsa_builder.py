
import warnings

from flask import render_template, request, flash
from sqlalchemy.exc import SAWarning
from system.services.twitter_sentiment_analysis.tsa_service import tsa_res, MLmodel
from system import database

warnings.simplefilter(action='ignore', category=SAWarning)


def tsa_builder_service():

    pulldownlist_ = ['Support-Vector-Machine', 'Random-Forest']
    
    emptyres = {
        'model' : None,
        'fbeta': None,
        'f1_score': None, 
        'accuracy_train': None,
        'cross_val': None
    }

    spot_ = 0

    if request.method == "POST":
        spot_input = int(request.form.get('spot'))
        model_ = request.form.get('model')
        spot_ = spot_input + 1

        tb1 = 'GroupSentiments'
        tb2 = 'MSFT'
        if database.check_table_empty(tb1) or database.check_table_empty(tb2):
            print(f"database {tb1} or {tb2} Empty")
            return render_template("tsa_builder.html", spot = spot_, pulldownlist = pulldownlist_, mlres = emptyres)
        else:
            # have data and posted
            sql_select_data = '''
            SELECT 
                gs.Date, gs.Likes, gs.RetweetCount, gs.QuoteCount, gs.pos, gs.neg, gs.neu, gs.compound, m.Adj_close  
            from 
                GroupSentiments gs inner join MSFT m on gs.Date = m.Date 
            ORDER by gs.Date ASC ;
            '''
            data = database.execute_sql_statement(sql_select_data)
            data['Label'] = data['Adj_close'].diff().apply(lambda x: 0 if x<0 else 1).shift(-1)
            data.dropna(inplace=True)
            y = data['Label']
            X = data.drop(['Label','Adj_close','Date'], axis=1)
            
            print(X.head())
            print(X.dtypes)
            print(y.head())
            print(y.dtypes)

            if str(model_) == 'Support-Vector-Machine':
                params  = {
                    'kernel': 'rbf',
                    'C' : 0.5,
                    'degree': 5
                }
                clf = MLmodel(model_, params, X, y)
                clf.fit()

        tsa_res.demo_deg = spot_
        return render_template("tsa_builder.html", spot = spot_, pulldownlist = pulldownlist_, mlres = clf.res)
    else:
        return render_template("tsa_builder.html", spot = spot_, pulldownlist = pulldownlist_, mlres = emptyres)
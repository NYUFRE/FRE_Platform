
from cgi import test
import string
from sklearn import svm, metrics
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import cross_val_score, KFold, train_test_split
import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import snscrape.modules.twitter as sntwitter
# from Util import timer_runtime, txt_cleaner
from system.services.twitter_sentiment_analysis.Utils import timer_runtime, txt_cleaner
import yfinance as yf




class DataFetching:

    def __init__(self, params) -> None:
        self.start =  params['Start']
        self.end = params['End']
        self.keywords = params['Keywords'] 
        self.tweetsLimit = params['Tweets_Limit'] # could be numer of True False
        self.data = None #pd.Dataframe
        self.data_stock = None #Stock data : MSFT
    
    def data_to_csv(self, file_name_extend = 'MSFT') -> int:
        self.data.to_csv("tweets_" + file_name_extend + "_" + self.start[0:10] + "_" + self.end[0:10] + ".csv")
        return 1
    

    def data_downlaod_stock(self, ticker = 'MSFT', start='2010-01-01', end = '2022-07-15') -> int:
        '''
        Download stock data
        '''
        self.data_stock = yf.download(ticker, start, end)
        self.data_stock.insert(0, 'Date', self.data_stock.index)
        self.data_stock.reset_index(drop = True, inplace = True)
        return 1


    @timer_runtime
    def data_download(self) -> int:
        """
        This function download tweets data using snscrape and populate self.data attributes.
        self.data is a pd.Dataframe obj
        
        return: Dataframe with 
                index: natural index from 0 to n
                columns: ['Datetime_utc', 'Username', 'Url', 'Text', 'Likes','RetweetCount','QuoteCount']
        """
        query = self.keywords + ' lang:en since:' +  self.start + ' until:' + self.end + '-filter:replies' 
        print("The query is : \n ", query)
        # Populate DB
        tweets_list = []
        res = sntwitter.TwitterSearchScraper(query).get_items()
        for i,tweet in enumerate(res):
            if self.tweetsLimit:
                if i > self.tweetsLimit:
                    break
            if i % 600 == 0: # normally there are 600 twees/day
                print('Now @', tweet.date)
            tweet_clean = txt_cleaner(tweet.content)
            datetime = tweet.date.strftime("%Y-%m-%d %H:%M:%S")
            tweets_list.append((
                datetime, tweet.user.username, tweet.url,
                tweet_clean, tweet.likeCount, tweet.retweetCount, tweet.quoteCount))

        #Creating a dataframe from the tweets list above 
        self.data = pd.DataFrame(tweets_list, columns=['Datetime_utc', 'Username', 'Url', 'Text', 'Likes','RetweetCount','QuoteCount'])
        self.data.drop_duplicates(subset='Datetime_utc', keep='first', inplace=True)
        # self.data = self.data.astype({'Likes':str, 'RetweetCount':str, 'QuoteCount': str})

        print(f"# of raw records: {len(tweets_list)}")
        print(f"# of pertained records: {len(self.data)}")
        print(f"# of removed duplicates records:{len(tweets_list) - len(self.data)}")
        return 1




class SentimentAnalyzer:

    def __init__(self) -> None:
        self.data = None # sentiments


    @timer_runtime
    def analyze(self, data: pd.DataFrame) -> int:
        '''
        This function perform sentiment analysis on each tweets
        
        data: columns should be ['Datetime_utc', 'Username', 'Url', 'Text', 'Likes','RetweetCount','QuoteCount']
        returns: populate self.sentiments with a sentiments dataframe
                index: natural index, from 0 to N
                columns: ['Datetime_utc', 'Likes','RetweetCount','QuoteCount', 'pos', 'neg', 'neu', 'compound']
        '''
        def score(tweet: str) -> list:
            ''' output sentiment socre '''
            scores = SentimentIntensityAnalyzer().polarity_scores(tweet)
            return [scores['pos'], scores['neg'], scores['neu'], scores['compound']]

        def helper(tweet: tuple):
            return [tweet[0], tweet[4], tweet[5], tweet[6]] + score(tweet[3]) 

        scores_all = [ ]
        count = 0
        for tweet in data.to_records(index=False):
            if count % 600 == 0: # normally there are 600 twees/day
                print('Now @', tweet[0])
            scores_all.append(helper(tweet))
            count += 1
        self.data = pd.DataFrame(data = scores_all, columns=['Datetime_utc', 'Likes','RetweetCount','QuoteCount', 'pos', 'neg', 'neu', 'compound'])
        
        return 1




class MLmodel:
    def __init__(self, model: string, params: dict, X, y ,  test_ratio = 0.25, random_seed = 10, kfoldnum = 5) -> None:
        if X is not None and y is not None:
            self.X_train, self.X_test, self.y_train, self.y_test  = train_test_split(X, y, test_size=test_ratio, random_state=random_seed)
        self.model = model
        self.params = params
        self.test_ratio = test_ratio
        self.res = None
        self.seed = random_seed
        self.kfold_num = kfoldnum
        self.classifier = None
        self.X = X
        self.y = y

    def svm_clf(self) -> None:
        clf = svm.SVC(
            kernel  = self.params['kernel'], 
            C       = self.params['C'],
            degree  = self.params['degree'],
            probability = True
        )

        clf.fit(self.X_train, self.y_train)
        self.classifier = clf
        y_train_pred = clf.predict(self.X_train)
        y_test_pred = clf.predict(self.X_test)

        self.res = {
            'model' : self.model,
            'fbeta': metrics.fbeta_score(self.y_test, y_test_pred, beta = 0.5),
            'f1_score': metrics.f1_score(self.y_test, y_test_pred), 
            'accuracy_train': metrics.accuracy_score(self.y_train, y_train_pred),
            'cross_val': cross_val_score(clf, self.X, self.y, cv = KFold(self.kfold_num)).mean()
        }
        return None
    
    def NN_clf(self) -> None:
        clf = MLPClassifier(
            hidden_layer_sizes     = self.params['layers'], 
            activation                  = self.params['activation'],
            solver                      = self.params['solver'],
            alpha                       = self.params['alpha'],
            random_state                = self.params['random_state']
        )

        clf.fit(self.X_train, self.y_train)
        self.classifier = clf
        y_train_pred = clf.predict(self.X_train)
        y_test_pred = clf.predict(self.X_test)

        self.res = {
            'model' : self.model,
            'fbeta': metrics.fbeta_score(self.y_test, y_test_pred, beta = 0.5),
            'f1_score': metrics.f1_score(self.y_test, y_test_pred), 
            'accuracy_train': metrics.accuracy_score(self.y_train, y_train_pred),
            'cross_val': cross_val_score(clf, self.X, self.y, cv = KFold(self.kfold_num)).mean()
        }
        return None


    def RandomForest_clf(self) -> None:
        clf = RandomForestClassifier(
            n_estimators            = self.params['n_estimators'],
            max_depth               = self.params['max_depth'],
            criterion               = self.params['criterion'],
            random_state            = self.params['random_state']
        )

        clf.fit(self.X_train, self.y_train)
        self.classifier = clf
        y_train_pred = clf.predict(self.X_train)
        y_test_pred = clf.predict(self.X_test)

        self.res = {
            'model' : self.model,
            'fbeta': metrics.fbeta_score(self.y_test, y_test_pred, beta = 0.5),
            'f1_score': metrics.f1_score(self.y_test, y_test_pred), 
            'accuracy_train': metrics.accuracy_score(self.y_train, y_train_pred),
            'cross_val': cross_val_score(clf, self.X, self.y, cv = KFold(self.kfold_num)).mean()
        }
        return None

    def LogisticRegression_clf(self) -> None:
        clf = LogisticRegression(
            penalty                 = self.params['penalty'],
            C                       = self.params['C'],
            dual                    = self.params['dual'],
            random_state            = self.params['random_state']
        )

        clf.fit(self.X_train, self.y_train)
        self.classifier = clf
        y_train_pred = clf.predict(self.X_train)
        y_test_pred = clf.predict(self.X_test)

        self.res = {
            'model' : self.model,
            'fbeta': metrics.fbeta_score(self.y_test, y_test_pred, beta = 0.5),
            'f1_score': metrics.f1_score(self.y_test, y_test_pred), 
            'accuracy_train': metrics.accuracy_score(self.y_train, y_train_pred),
            'cross_val': cross_val_score(clf, self.X, self.y, cv = KFold(self.kfold_num)).mean()
        }
        return None

    def KNN(self) -> None:
        clf = KNeighborsClassifier(
            n_neighbors                 = self.params['n_neighbors'],
            weights                      = self.params['weights'],
            algorithm                    = self.params['algorithm'],
            leaf_size            = self.params['leaf_size']
        )

        clf.fit(self.X_train, self.y_train)
        self.classifier = clf
        y_train_pred = clf.predict(self.X_train)
        y_test_pred = clf.predict(self.X_test)

        self.res = {
            'model' : self.model,
            'fbeta': metrics.fbeta_score(self.y_test, y_test_pred, beta = 0.5),
            'f1_score': metrics.f1_score(self.y_test, y_test_pred), 
            'accuracy_train': metrics.accuracy_score(self.y_train, y_train_pred),
            'cross_val': cross_val_score(clf, self.X, self.y, cv = KFold(self.kfold_num)).mean()
        }
        return None



    def fit(self):
        if self.model == 'Support-Vector-Machine':
            return self.svm_clf()
        if self.model == 'Neural-Network':
            return self.NN_clf()
        if self.model == 'Random-Forest':
            return self.RandomForest_clf()
        if self.model == 'Logistic-Regression':
            return self.LogisticRegression_clf()
        if self.model == 'K-Neighbors':
            return self.KNN()
            






class Results:
    def __init__(self):
        
        self.data = None
        self.demo_deg = None
        self.MODE = "Demo" # default demo
        self.isBuilt = False
        self.isPlot = False
        self.ml_res = {
            'model' : None,
            'fbeta': None,
            'f1_score': None, 
            'accuracy_train': None,
            'cross_val': None
        }

        self.clf = MLmodel(
            model   = '',
            params  = {},
            X       = None,
            y       = None
        )
        # data for ploting in the lab
        self.labplotX = None
        self.labplotXname = None


tsa_res = Results()




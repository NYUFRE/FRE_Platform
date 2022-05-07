import datetime
import json
import os
import urllib.request

import numpy as np
import pandas as pd

from sklearn import preprocessing
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans, DBSCAN
import itertools

        
def find_clusters(return_df, fund_df, fund_cat):
    N_PRIN_COMPONENTS = 50
    pca = PCA(n_components=N_PRIN_COMPONENTS)
    pca.fit(return_df)

    X = [pca.components_.T]
    for cat in fund_cat:
        X.append(fund_df[cat].values[:, np.newaxis])

    X = np.hstack(tuple(X))
    X = preprocessing.StandardScaler().fit_transform(X)
    
    epsilon = 0.1
    max_epsilon = 0.1
    max_cluster_num = 0

    while epsilon < 5:
        clf = DBSCAN(eps=epsilon, min_samples=2)

        clf.fit(X)
        labels = clf.labels_
        n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
        if n_clusters_ > max_cluster_num:
            max_cluster_num = n_clusters_
            max_epsilon = epsilon
        epsilon+=0.1

#    print(f'Best Epsilon: {max_epsilon}')
    
    clf = DBSCAN(eps=max_epsilon, min_samples=2)

    clf.fit(X)
    labels = clf.labels_
    n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
#    print("\nClusters discovered: %d" % n_clusters_)

    clustered = clf.labels_
        
    clustered_series = pd.Series(index=return_df.columns, data=clustered.flatten())
    clustered_series_all = pd.Series(index=return_df.columns, data=clustered.flatten())
    clustered_series = clustered_series[clustered_series != -1]
    
    cluster_dict = {}
    for i in range(0, n_clusters_):
        cur_cluster = list(clustered_series[clustered_series==i].index)
        cluster_dict[str(i)] = cur_cluster
    
    return cluster_dict, max_epsilon

# price_data: df that contains price data for all stocks
# pairs: list of all pairs to evaluate
def backtest(price_data, pairs):
    all_trade = pd.DataFrame(columns = ['stock1','stock2','money return','sharpe ratio','wins', 'loses'],index = range(0,len(pairs)))
    for i in range(0,len(pairs)):
        stock1 = pairs[i][0]
        stock2 = pairs[i][1]
        result = trade(price_data[stock1], price_data[stock2],30,5)
        all_trade['stock1'][i] = stock1
        all_trade['stock2'][i] = stock2
        all_trade['money return'][i] = result[0]
        all_trade['sharpe ratio'][i] = result[1]
        all_trade['wins'][i] = result[2]
        all_trade['loses'][i] = result[3]
        
#    all_trade = all_trade.replace([np.inf, -np.inf],np.nan).dropna()
    all_trade = all_trade.replace([np.inf, -np.inf],np.nan)
    return all_trade

# Trade using a simple strategy
def trade(S1, S2, window1, window2):
    
    # If window length is 0, algorithm doesn't make sense, so exit
    if (window1 == 0) or (window2 == 0):
        return 0
    
    # Compute rolling mean and rolling standard deviation
    ratios = S1/S2
    ma1 = ratios.rolling(window=window1,
                               center=False).mean()
    ma2 = ratios.rolling(window=window2,
                               center=False).mean()
    std = ratios.rolling(window=window2,
                        center=False).std()
    zscore = (ma1 - ma2)/std
    
    # Simulate trading
    # Start with no money and no positions
    money = 0
    countS1 = 0
    countS2 = 0
    wins = 0
    loses = 0
    
    money_list =[money]
    for i in range(len(ratios)):
        # Sell short if the z-score is > 1
        if zscore[i] < -1:
            money += S1[i] - S2[i] * ratios[i]
            countS1 -= 1
            countS2 += ratios[i]
            #print('Selling Ratio %s %s %s %s'%(money, ratios[i], countS1,countS2))
        # Buy long if the z-score is < -1
        elif zscore[i] > 1:
            money -= S1[i] - S2[i] * ratios[i]
            countS1 += 1
            countS2 -= ratios[i]
            #print('Buying Ratio %s %s %s %s'%(money,ratios[i], countS1,countS2))
        # Clear positions if the z-score between -.5 and .5
        elif abs(zscore[i]) < 0.75:
            money += S1[i] * countS1 + S2[i] * countS2
            countS1 = 0
            countS2 = 0
            #print('Exit pos %s %s %s %s'%(money,ratios[i], countS1,countS2))
        money_list.append(money)
        if money_list[i] > money_list[i-1]:
            wins += 1
        elif money_list[i] < money_list[i-1]:
            loses += 1
        
    with np.errstate(divide='ignore', invalid='ignore'):
        return_list = np.diff(money_list) / money_list[:-1]
    return_list[return_list == np.inf] = 0
    return_list[return_list == -np.inf] = 0
    return_list = np.nan_to_num(return_list)
#     print('Sharpe Ratio: ' + str((return_list.mean()-0.02865)/return_list.std()*(252**0.5)))
    sharpe_ratio = (return_list.mean()-0)/return_list.std()*(252**0.5)
    
    return [money, sharpe_ratio, wins, loses]


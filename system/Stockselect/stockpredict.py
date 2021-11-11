import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pandas import read_csv
import math
from keras.models import Sequential
from keras.layers import Bidirectional
from keras.layers import Dense
from keras.layers import LSTM
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from keras.layers.core import Dense, Activation, Dropout
import time #helper libraries
from datetime import datetime
from datetime import timedelta
import os
import sys
import subprocess
import matplotlib.pyplot as plt
import datetime as dt
import matplotlib.dates as mdates
import plotly.graph_objects as go
import plotly.express as px


def extract_database_rf(database):
    """
    Extract the us10y price data from the database to calculate the average risk free rate.
    """
    stock_select = f"""
                    SELECT *
                    FROM us10y
                    ;
                    """
    rf_df = database.execute_sql_statement(stock_select)
    rf_df = rf_df.set_index('date')
    rf_df.index = pd.to_datetime(rf_df.index)
    return rf_df
import pandas as pd
from datetime import datetime
from time import time
import re
from nltk.tokenize import word_tokenize
import emoji
import pytz
import sqlite3


def remove_substrings(text, to_replace, replace_with=""):
    """
    Remove (or replace) substrings from a text.
    Args:
        text (str): raw text to preprocess
        to_replace (iterable or str): substrings to remove/replace
        replace_with (str): defaults to an empty string but
            you replace substrings with a token.
    """
    if isinstance(to_replace, str):
        to_replace = [to_replace]

    for x in to_replace:
        text = text.replace(x, replace_with)
    return text

# def remove_emoji(text):
#     return remove_substrings(text, emoji.UNICODE_EMOJI["en"])


stopwords = ["for", "on", "an", "a", "of", "and", "in", "the", "to", "from"]

def txt_cleaner(text):
    """
    Clean the input text. It will do the cleaning job for tweets, such as Removing @mentions,
    #hastags, hyperlinks and etc.
    """
    text = emoji.demojize(text)
    text = re.sub('@[A-Za-z0–9]+', '', text) #Removing @mentions
    text = re.sub('\$[A-Za-z0–9]+', '', text) #Removing @mentions
    text = re.sub("#[A-Za-z0-9_]+","", text) # Removing #hastags
    text = re.sub('RT[\s]+', '', text) # Removing RT
    text = re.sub("\n", '', text) # Removing newline symbol
    text = re.sub("(?:\@|http?\://|https?\://|www)\S+", "", text)
    text = re.sub("[^A-Za-z0-9,.?!]"," ", text) # Filtering non-alphanumeric characters
    text = word_tokenize(text)
    text = [w for w in text if w.lower() not in stopwords]
    text = " ".join(w for w in text)
    return text


def utc_to_est(utc_time: str, fmt = "%Y-%m-%d %H:%M:%S") -> str:
    '''
    Convert time from UTC to EST. Time str should be of format "%Y-%m-%d %H:%M:%S" 
    (such as 2021-12-30 18:54:58 --> 2021-12-30 13:54:58) 
    '''
    t = utc_time.split('+')[0]
    t = datetime.strptime(utc_time, fmt)
    est = pytz.timezone('US/Eastern')
    utc = pytz.utc
    t_tz = t.replace(tzinfo=utc)
    return t_tz.astimezone(est).strftime(fmt)

def time_converter(time: str) -> str:
    '''
    convert UTC time : 2021-12-30 23:51:35+00:00 to EST time of the format 2021-12-30 23:51:35
    '''
    t = time.split('+')[0]
    return utc_to_est(t)

def timer_runtime(func):
    def wrapper(*args, **kwargs):
        t1 = time()
        result = func(*args, **kwargs)
        t2 = time()
        print(f'Function {func.__name__!r} executed in {(t2-t1):.4f}s')
        return result
    return wrapper


def refreq(data: pd.DataFrame, key_column: str, freq='D', regroup_columns = list) -> pd.DataFrame:
    '''
    This function does refrequence to the data based on the key_column, usually key_column is datetime string, could be secondly
    and use then convert to daily by sum() function
    '''
    data[key_column] = pd.to_datetime(data[key_column])
    res = data.groupby(pd.Grouper(key= key_column, axis=0, freq=freq))[regroup_columns].sum()
    return res




class db_helper:

    def __init__(self, engine) -> None:
        self.engine = engine
    

    # def check_table_exist(self, tbname):
    #     cursor = self.conn.cursor()
    #     sql_check = f''' 
    #     SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{tbname}' 
    #     '''
    #     cursor.execute(sql_check)
    #     if cursor.fetchone()[0]==1 : 
    #         return True
    #     else:
    #         return False

    def check_table_exist(self, tbname):
        sql_check = f''' 
        SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{tbname}' 
        '''
        res = self.engine.execute(sql_check)
        if res.fetchone()[0]==1 : 
            return True
        else:
            return False
        
    @timer_runtime
    def insert_many(self, data: pd.DataFrame, tbname: str, sql_insertmany: str) -> int:
        '''
        This funciton pertain the data into database (with index)
        data: pd.Dataframe
        '''
        data_str = data.astype(dtype=str)

        print(f'Table {tbname} existed. Appending values... ')
        self.engine.executemany(sql_insertmany, list(data_str.to_records(index=True)) )
       
        return 1
    
    
    
    
    
    # @timer_runtime
    # def insert_many(self, data: pd.DataFrame, tbname: str, sql_insertmany: str) -> int:
    #     '''
    #     This funciton pertain the data into database (with index)
    #     data: pd.Dataframe
    #     '''
    #     data_str = data.astype(dtype=str)
    #     # connection = sqlite3.connect(dbname)
    #     cursor = self.conn.cursor()
    #     flg_table = False
    #     sql_check = f''' 
    #     SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{tbname}' 
    #     '''
       
    #     # check table existance
    #     cursor.execute(sql_check)
    #     if cursor.fetchone()[0]==1 : 
    #         flg_table = True
            
    #     # if table exist, execute
    #     if flg_table:
    #         print(f'Table {tbname} existed. Appending values... ')
    #         cursor.executemany(sql_insertmany, list(data_str.to_records(index=True)) )
    #     else:
    #         print(f"Warning: table {tbname} not existed!")
    #         return 0
    #     self.conn.commit()
    #     self.conn.close()
    #     return 1
# -*- coding: utf-8 -*
# !/usr/bin/env python3
import sys
sys.path.append('../')

from ai_trading.ga_portfolio_selection import *
from ai_trading.ga_portfolio_back_test import *
from ai_trading.ga_portfolio_probation_test import *

if __name__ == "__main__":
    #create_populate_tables()
    #build_ga_model()
    ga_back_test()
    ga_back_test_plot()
    ga_probation_test()
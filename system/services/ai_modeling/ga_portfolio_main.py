# -*- coding: utf-8 -*
# !/usr/bin/env python3
import os
import sys

from system import FREDatabase, EODMarketData
from system.services.ai_modeling.ga_portfolio_back_test import ga_back_test_plot, ga_back_test
from system.services.ai_modeling.ga_portfolio_probation_test import ga_probation_test
from system.services.ai_modeling.ga_portfolio_select import build_ga_model, create_populate_tables

sys.path.append('../../')

database = FREDatabase()
eod_market_data = EODMarketData(os.environ.get("EOD_API_KEY"), database)

if __name__ == "__main__":
    create_populate_tables()
    build_ga_model(database)
    ga_back_test(database)
    ga_back_test_plot()
    ga_probation_test(database)
# -*- coding: utf-8 -*
# !/usr/bin/env python3
import sys
sys.path.append('../')

os.environ["EOD_API_KEY"] = "5ba84ea974ab42.45160048"

if not os.environ.get("EOD_API_KEY"):
    raise RuntimeError("EOD_API_KEY not set")

database = FREDatabase()
eod_market_data = EODMarketData(os.environ.get("EOD_API_KEY"), database)

if __name__ == "__main__":
    create_populate_tables()
    build_ga_model(database)
    ga_back_test(database)
    ga_back_test_plot()
    ga_probation_test(database)
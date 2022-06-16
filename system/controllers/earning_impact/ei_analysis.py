import warnings
from datetime import datetime

from flask import flash, render_template, request
from sqlalchemy.exc import SAWarning

from system.services.earnings_impact.earnings_impact import earnings_impact_data, BootStrap, group_to_array, \
    slice_period_group, load_calendar_from_database, load_returns, local_earnings_calendar_exists

warnings.simplefilter(action='ignore', category=SAWarning)

from system import database


def ei_analysis_service():
    if not local_earnings_calendar_exists():
        flash("Local earnings calendar does not exist. Click Calculate to download data. " + \
              f"The whole process would take {25}~{30} minutes", 'info')

    input = {'date_from': '20190901', 'date_to': '20191201'}
    BeatInfo, MeatInfo, MissInfo = [], [], []
    if request.method == "POST":
        returns = load_returns()
        SPY_component = database.get_sp500_symbols()
        table = load_calendar_from_database(SPY_component)

        date_from = request.form.get('date_from')
        date_from = str(date_from)
        date_to = request.form.get('date_to')
        date_to = str(date_to)
        input['date_from'] = date_from
        input['date_to'] = date_to

        # Check validity of input dates
        if datetime.strptime(input['date_to'], '%Y%m%d') <= datetime.strptime(input['date_from'], '%Y%m%d') or \
                datetime.strptime(input['date_to'], '%Y%m%d') > datetime.now():
            flash("Error! Invalid End Date")
            return render_template("ei_analysis.html", BeatInfo=BeatInfo, MeatInfo=MeatInfo, MissInfo=MissInfo,
                                   input=input)

        # returns = get_returns(SPY_component)

        try:
            miss, meet, beat, earnings_calendar = slice_period_group(table, date_from, date_to)
        except ValueError as e:
            flash(str(e), 'error')
            return render_template("ei_analysis.html", BeatInfo=BeatInfo, MeatInfo=MeatInfo, MissInfo=MissInfo,
                                   input=input)

        miss_arr, meet_arr, beat_arr = group_to_array(miss, meet, beat, earnings_calendar, returns)
        miss_arr, meet_arr, beat_arr = BootStrap(miss_arr), BootStrap(meet_arr), BootStrap(beat_arr)

        for i in [0, 9, 19, 29, 39, 49, 59]:
            BeatInfo.append('%.2f%%' % (beat_arr[i] * 100))
            MeatInfo.append('%.2f%%' % (meet_arr[i] * 100))
            MissInfo.append('%.2f%%' % (miss_arr[i] * 100))
        earnings_impact_data.Beat = beat_arr
        earnings_impact_data.Meet = meet_arr
        earnings_impact_data.Miss = miss_arr

    return render_template("ei_analysis.html", BeatInfo=BeatInfo, MeatInfo=MeatInfo, MissInfo=MissInfo, input=input)

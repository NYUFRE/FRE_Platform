import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import warnings


from flask import flash, redirect, url_for, render_template, session, request
from sqlalchemy.exc import SAWarning

from system import database, iex_market_data, eod_market_data
from system.services.VaR.VaR_Calculator import VaR
from system.services.utility.helpers import usd

warnings.simplefilter(action='ignore', category=SAWarning)

class Bond:
    def __init__(self, coupon: float, ytm: float, price: float, maturdate: str, freq: str):
        self.coupon = coupon
        self.ytm = ytm
        self.price = price
        self.matdate = datetime.strptime(maturdate, '%Y-%m-%d')
        freq_dict = {
            'Semi-Annual': 6,
            'Monthly': 1
        }
        self.last = self.matdate
        self.monthsinprd = freq_dict[freq]
        today = datetime.today()
        while self.last > today:
            self.last = self.last + relativedelta(months=-self.monthsinprd)
        self.accrueddays = (today - self.last).days

    def analysis(self):
        ret = []
        today = datetime.today()
        next = self.last + relativedelta(months=+self.monthsinprd)
        daysinprd = (next - self.last).days
        prdinyr = 12 / self.monthsinprd
        self.accruedinterest = self.coupon / prdinyr * self.accrueddays / daysinprd
        self.fullprice = self.price + self.accruedinterest
        ret.append(['Accrued Interest', round(self.accruedinterest, 2)])
        ret.append(['Full Price', round(self.fullprice, 2)])

        pv_cf_sum = 0
        y_pv_sum = 0
        yp_pv_sum = 0
        while next <= self.matdate:
            nom_cf = self.coupon / prdinyr
            if next == self.matdate:
                nom_cf += 100
            cnt = (next - today).days / 365.0
            pv_cf = nom_cf / pow((1 + self.ytm / 100 / prdinyr), prdinyr * cnt)
            pv_cf_sum += pv_cf
            y_pv_sum += pv_cf * cnt
            yp_pv_sum += cnt * nom_cf * (cnt + 1.0 / prdinyr) / pow((1 + self.ytm / 100 / prdinyr), prdinyr * cnt + 2)
            next = next + relativedelta(months=+self.monthsinprd)

        self.macdur = y_pv_sum / pv_cf_sum
        ret.append(['Macaulay Duration', round(self.macdur, 4)])
        self.moddur = self.macdur / (1 + self.ytm / 100 / prdinyr)
        ret.append(['Modified Duration', round(self.moddur, 4)])
        self.convexity = yp_pv_sum / self.fullprice / 100
        ret.append(['Convexity', round(self.convexity, 4)])
        return ret

    def yield_curve_change(self, delta_y: float):
        self.analysis()
        delta_price = (-delta_y*self.moddur+0.5*delta_y*delta_y*self.convexity)*self.fullprice/100.0
        return self.fullprice+delta_price


def fixed_income_bond_info_service():
    bond = request.form.get('bond_name')
    info = eod_market_data.get_bond_data(bond)
    new_bond = Bond(float(info['Coupon']), float(info['YieldToMaturity']), float(info['Price']),
                             info['Maturity_Date'], info['IssueData']['CouponPaymentFrequency'])
    analysis = new_bond.analysis()
    save = request.form.get('save')
    if save:
        alias = request.form.get('alias')
        uid = session['user_id']
        now = datetime.today()
        saveddate = now.strftime("%Y/%m/%d %H:%M:%S")
        if not alias:
            alias = bond
        existed = database.save_bond(uid, alias, bond, new_bond.coupon, new_bond.ytm, new_bond.fullprice,
                           new_bond.accruedinterest, new_bond.price, info['Maturity_Date'], info['IssueData']['CouponPaymentFrequency'], saveddate)
        if existed:
            flash('ERROR! Repetitive Alias.', 'error')
        else:
            flash('Saved!', 'message')
    return render_template("fixed_income_bond_info.html", name=bond, info=info, anal=analysis)
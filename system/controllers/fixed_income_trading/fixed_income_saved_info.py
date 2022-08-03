import time
import warnings

from flask import flash, render_template, session, request
from sqlalchemy.exc import SAWarning
from system.controllers.fixed_income_trading.fixed_income_bond_info import Bond

from system import database
from system.controllers.fixed_income_trading.fixed_income_saved import fixed_income_saved_service

warnings.simplefilter(action='ignore', category=SAWarning)


def fixed_income_saved_info_service():
    res = []
    if request.method == "POST":
        uid = session['user_id']
        alias = request.form.get('alias')
        alias_ptfl = request.form.get('alias_ptfl')

        if alias != '' and alias_ptfl != '':
            flash("ERROR! Please choose only one security.", 'error')
            return fixed_income_saved_service()
        elif alias == '' and alias_ptfl == '':
            flash("ERROR! Please choose a security.", 'error')
            return fixed_income_saved_service()

        if alias != '':
            type = 'bond'
            name, coupon, ytm, price, maturdate, freq = database.get_bond_via_alias(uid, alias)
            bond = Bond(coupon, ytm, price, maturdate, freq)
            res.append(['Name', name])
            res.append(['Coupon', coupon])
            res.append(['Yield To Maturity', ytm])
            res.append(['Price', price])
            res.append(['Maturity Date', maturdate])
            res.append(['Frequency', freq])

            analysis = bond.analysis()
            for item in analysis:
                res.append(item)

        else:
            type = 'ptfl'
            alias = alias_ptfl
            data = database.get_bond_ptfl_via_alias(uid, alias_ptfl)
            res.append(['Alias', data['mb'], data['hb1'], data['hb2']])
            res.append(['Action', data['mb_action'], data['h_action'], data['h_action']])
            res.append(['Weight', data['w0'], data['w1'], data['w2']])
            res.append(['Full Price', data['mb_fullprice'], data['hb1_fullprice'], data['hb2_fullprice']])
            res.append(['Market Value', data['mb_mv'], data['hb1_mv'], data['hb2_mv']])
            res.append(['Face Value', data['mb_fv'], data['hb1_fv'], data['hb2_fv']])


    return render_template("fixed_income_saved_info.html", res = res, type = type, alias = alias)
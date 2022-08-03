import time
import warnings

from flask import flash, redirect, url_for, render_template, session, request
from sqlalchemy.exc import SAWarning
from system.controllers.fixed_income_trading.fixed_income_bond_info import Bond
from system.controllers.fixed_income_trading.fixed_income_ptfl_result import create_bond

from system import database, iex_market_data
from system.controllers.fixed_income_trading.fixed_income_yield_sim import fixed_income_yield_sim_setup_service
from system.services.VaR.VaR_Calculator import VaR
from system.services.utility.helpers import usd

warnings.simplefilter(action='ignore', category=SAWarning)


def fixed_income_yield_sim_result_service():
    res = []
    if request.method == "POST":
        uid = session['user_id']
        alias = request.form.get('alias')
        alias_ptfl = request.form.get('alias_ptfl')
        symbol = request.form.get('symbol')
        yc_str = request.form.get('yc')
        if yc_str == '':
            flash("ERROR! Please enter yield change value.", 'error')
            return fixed_income_yield_sim_setup_service()

        elif alias == '' and alias_ptfl == '':
            flash("ERROR! Please choose a security.", 'error')
            return fixed_income_yield_sim_setup_service()

        elif alias != '' and alias_ptfl != '':
            flash("ERROR! Please choose only one security.", 'error')
            return fixed_income_yield_sim_setup_service()

        if symbol == "inc": sym = 1
        else: sym = -1

        yc = float(yc_str)/100.0*sym

        if alias != '':
            type = 'bond'
            name, coupon, ytm, price, maturdate, freq = database.get_bond_via_alias(uid, alias)
            bond = Bond(coupon, ytm, price, maturdate, freq)
            new_full_price = bond.yield_curve_change(yc)
            new_flat_price = new_full_price - bond.accruedinterest
            res.append(['Alias', alias])
            res.append(['Bond Name', name])
            res.append(['Yield Change', str(round(yc*100, 2))+'bp'])
            res.append(['Original Full Price', round(bond.fullprice,2)])
            res.append(['Original Flat Price', round(bond.price,2)])
            res.append(['New Full Price', round(new_full_price,2)])
            res.append(['New Flat Price', round(new_flat_price,2)])
            res.append(['Price Change', round(new_flat_price-bond.price, 2)])

        else:
            type = 'ptfl'
            data = database.get_bond_ptfl_via_alias(uid, alias_ptfl)
            mb = create_bond(uid, data['mb'])
            hb1 = create_bond(uid, data['hb1'])
            hb2 = create_bond(uid, data['hb2'])

            mb_new_fullprice = mb.yield_curve_change(yc)
            hb1_new_fullprice = hb1.yield_curve_change(yc)
            hb2_new_fullprice = hb2.yield_curve_change(yc)

            mb_delta_fullprice = mb_new_fullprice-mb.fullprice
            hb1_delta_fullprice = hb1_new_fullprice - hb1.fullprice
            hb2_delta_fullprice = hb2_new_fullprice - hb2.fullprice

            mb_new_mv = data['mb_fv']*mb_new_fullprice/100
            hb1_new_mv = data['hb1_fv'] * hb1_new_fullprice / 100
            hb2_new_mv = data['hb2_fv'] * hb2_new_fullprice / 100

            mb_delta_mv = mb_new_mv-data['mb_mv']
            hb1_delta_mv = hb1_new_mv - data['hb1_mv']
            hb2_delta_mv = hb2_new_mv - data['hb2_mv']

            res.append(['Alias', data['mb'], data['hb1'], data['hb2']])
            res.append(['Action', data['mb_action'], data['h_action'], data['h_action']])
            res.append(['Original Full Price', mb.fullprice, hb1.fullprice, hb2.fullprice])
            res.append(['New Full Price', mb_new_fullprice, hb1_new_fullprice, hb2_new_fullprice])
            res.append(['Full Price Change', mb_delta_fullprice, hb1_delta_fullprice, hb2_delta_fullprice])
            res.append(['Original Market Value', data['mb_mv'], data['hb1_mv'], data['hb2_mv']])
            res.append(['New Market Value', mb_new_mv, hb1_new_mv, hb2_new_mv])
            res.append(['Market Value Change', mb_delta_mv, hb1_delta_mv, hb2_delta_mv])

            return_list = []
            for row in res:
                ret_row = []
                for item in row:
                    if isinstance(item, float):
                        ret_row.append(round(item, 2))
                    else:
                        ret_row.append(item)
                return_list.append(ret_row)

            res = return_list



    return render_template("fixed_income_yield_curve_result.html", res = res, type = type)
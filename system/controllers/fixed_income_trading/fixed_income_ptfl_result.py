import time
import warnings

from flask import flash, redirect, url_for, render_template, session, request
from sqlalchemy.exc import SAWarning
from datetime import datetime, timedelta

from system import database, iex_market_data
from system.services.VaR.VaR_Calculator import VaR
from system.services.utility.helpers import usd
from system.controllers.fixed_income_trading.fixed_income_bond_info import Bond

warnings.simplefilter(action='ignore', category=SAWarning)

def create_bond(uid, alias):
    name, coupon, ytm, price, maturdate, freq = database.get_bond_via_alias(uid, alias)
    return Bond(coupon, ytm, price, maturdate, freq)

def hedge(mb: Bond, hbs, action, fv):
    mb.analysis()
    w = []
    hb1 = hbs[0]
    hb1.analysis()
    hb2 = hbs[1]
    hb2.analysis()
    w1 = (mb.moddur-hb2.moddur)/(hb1.moddur-hb2.moddur)
    w2 = 1-w1
    if action == "long":
        hedging_action = "short"
    else:
        hedging_action = "long"

    mb_mv = mb.fullprice/100*fv
    res = {
        'w0': "100%",
        'w1': str(round(w1*100,2))+"%",
        'w2': str(round(w2*100,2))+"%",
        'mb_action': action,
        'h_action': hedging_action,
        'mb_fullprice': round(mb.fullprice,2),
        'hb1_fullprice': round(hb1.fullprice,2),
        'hb2_fullprice': round(hb2.fullprice,2),
        'mb_mv': round(mb_mv,2),
        'hb1_mv': round(mb_mv * w1,2),
        'hb2_mv': round(mb_mv * w2,2),
        'mb_fv': round(fv,2),
        'hb1_fv': round(mb_mv * w1 / hb1.fullprice*100,2),
        'hb2_fv': round(mb_mv * w2 / hb2.fullprice * 100,2)
    }
    return res



def fixed_income_ptfl_result_service():
    uid = session['user_id']
    action = request.form.get('action')
    fv_str = request.form.get('fv')
    mb = request.form.get('mb')
    hb = []
    if request.form.get('hb1')!='': hb.append(request.form.get('hb1'))
    if request.form.get('hb2')!='': hb.append(request.form.get('hb2'))

    works = False
    if mb == '':
        flash('ERROR! Please choose a main bond.', 'error')
    elif fv_str == '':
        flash('ERROR! Please enter a face value.', 'error')
    elif len(hb)<2:
        flash('ERROR! Please choose two hedging bonds.', 'error')

    elif hb[0] == hb[1]:
        flash('ERROR! Hedging bond must differ from each other.', 'error')
    else:
        fv = float(fv_str)
        if fv == 0:
            flash('ERROR! Face Value cannot be zero.', 'error')
        else:
            works = True
            for bond in hb:
                if bond == mb:
                    flash('ERROR! Hedging bond must differ from main bond.', 'error')
                    works = False
                    break


    if works:
        mb_bond = create_bond(uid, mb)
        hb_bonds = []
        for bond in hb:
            hb_bonds.append(create_bond(uid, bond))

        if (mb_bond.matdate-hb_bonds[0].matdate).days*(mb_bond.matdate-hb_bonds[1].matdate).days>0:
            flash('ERROR! Maturity date of the main bond cannot be earlier or later than both hedging bonds.', 'error')
            works = False
        else:
            hedging_result = hedge(mb_bond, hb_bonds, action, fv)

    if not works:
        saved_bond = database.get_saved_bonds(uid)
        return render_template("fixed_income_ptfl.html", res=saved_bond)

    save = request.form.get('save')
    if save:
        alias = request.form.get('alias')
        uid = session['user_id']
        now = datetime.today()
        saveddate = now.strftime("%Y/%m/%d %H:%M:%S")
        if not alias:
            alias = mb+'+'+hb[0]+'+'+hb[1]

        existed = database.save_bond_ptfl(uid,alias, mb, hb[0], hb[1], hedging_result['w0'], hedging_result['w1'], hedging_result['w2'], hedging_result['mb_action'], hedging_result['h_action'],
                                          hedging_result['mb_fullprice'], hedging_result['hb1_fullprice'], hedging_result['hb2_fullprice'], hedging_result['mb_mv'], hedging_result['hb1_mv'], hedging_result['hb2_mv'],
                                          hedging_result['mb_fv'], hedging_result['hb1_fv'], hedging_result['hb2_fv'],saveddate)
        if existed:
            flash('ERROR! Repetitive Alias.', 'error')
        else:
            flash('Saved!', 'message')

    return render_template("fixed_income_ptfl_result.html", mb = mb, hb = hb, action = action, res=hedging_result)
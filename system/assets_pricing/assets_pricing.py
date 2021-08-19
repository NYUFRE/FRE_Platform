import datetime
import json
import os
import urllib.request

import QuantLib as ql
import pandas as pd


class AssetPricingResult:
    def __init__(self):
        self.xvalue = []
        self.call = []
        self.put = []
        self.xparameter = ""
        self.yparameter = ""
        self.yield_curve = None
        self.discount_curve = None
        self.curve_benchmark = ""

    def get_yield_curve(self):
        return self._yield_curve

    def get_discount_curve(self):
        return self._discount_curve


asset_pricing_result = AssetPricingResult()

def pricing_european(curr:float, strike:float, days:int, rf:float, div:float, vol:float):
    """
    Calculate European option value and greek using analytic(Black Scholes) pricing engine. Assume constant
    risk free rate, divdend rate and volatility. Using Actual/Actual day convention and NYSE calendar.
    Day convention choice: https://www.quantlib.org/reference/group__daycounters.html
    Calendar choice: https://www.quantlib.org/reference/group__calendars.html

    :param curr, strike, days, rf, div, vol:
    :type float, float, int, float, float, float:
    :return: call_option_result, put_option_result
    :rtype: dict[Str, float], dict[Str, float]
    """
    call = {}
    put = {}

    today = ql.Date().todaysDate()
    maturity = today + ql.Period(days, ql.Days)

    europeanExercise = ql.EuropeanExercise(maturity)
    putpayoff = ql.PlainVanillaPayoff(ql.Option.Put, strike)
    callpayoff = ql.PlainVanillaPayoff(ql.Option.Call, strike)
    europeanPutOption = ql.VanillaOption(putpayoff, europeanExercise)
    europeanCallOption = ql.VanillaOption(callpayoff, europeanExercise)

    riskFreeTS = ql.YieldTermStructureHandle(ql.FlatForward(today, rf, ql.ActualActual()))
    dividendTS = ql.YieldTermStructureHandle(ql.FlatForward(today, div, ql.ActualActual()))
    volatility = ql.BlackVolTermStructureHandle(ql.BlackConstantVol(today, ql.UnitedStates(ql.UnitedStates.NYSE),
                                                                    vol, ql.ActualActual()))
    initialValue = ql.QuoteHandle(ql.SimpleQuote(curr))
    process = ql.BlackScholesMertonProcess(initialValue, dividendTS, riskFreeTS, volatility)

    europeanPutOption.setPricingEngine(ql.AnalyticEuropeanEngine(process))
    europeanCallOption.setPricingEngine(ql.AnalyticEuropeanEngine(process))

    call["Value"] = round(europeanCallOption.NPV(),4)
    call["Delta"] = round(europeanCallOption.delta(), 4)
    call["Gamma"] = round(europeanCallOption.gamma(), 4)
    call["Vega"] = round(europeanCallOption.vega(), 4)
    call["Rho"] = round(europeanCallOption.rho(), 4)
    call["Theta"] = round(europeanCallOption.theta(), 4)
    put["Value"] = round(europeanPutOption.NPV(), 4)
    put["Delta"] = round(europeanPutOption.delta(), 4)
    put["Gamma"] = round(europeanPutOption.gamma(), 4)
    put["Vega"] = round(europeanPutOption.vega(), 4)
    put["Rho"] = round(europeanPutOption.rho(), 4)
    put["Theta"] = round(europeanPutOption.theta(), 4)

    return call, put

def pricing_american(curr:float, strike:float, days:int, rf:float, div:float, vol:float):
    """
    Calculate American option value and greek using Finite Difference Black Scholes pricing engine with time grid at
    2000 and space grid at 200. Assume constant risk free rate, divdend rate and volatility. Using Actual/Actual day
    convention and NYSE calendar.
    Day convention choice: https://www.quantlib.org/reference/group__daycounters.html
    Calendar choice: https://www.quantlib.org/reference/group__calendars.html

    :param curr, strike, days, rf, div, vol:
    :type float, float, int, float, float, float:
    :return: call_option_result, put_option_result
    :rtype: dict[Str, float], dict[Str, float]
    """
    call = {}
    put = {}

    today = ql.Date().todaysDate()
    maturity = today + ql.Period(days, ql.Days)

    putpayoff = ql.PlainVanillaPayoff(ql.Option.Put, strike)
    callpayoff = ql.PlainVanillaPayoff(ql.Option.Call, strike)
    americanExercise = ql.AmericanExercise(today, maturity)
    americanPutOption = ql.VanillaOption(putpayoff, americanExercise)
    americanCallOption = ql.VanillaOption(callpayoff, americanExercise)

    riskFreeTS = ql.YieldTermStructureHandle(ql.FlatForward(today, rf, ql.ActualActual()))
    dividendTS = ql.YieldTermStructureHandle(ql.FlatForward(today, div, ql.ActualActual()))
    volatility = ql.BlackVolTermStructureHandle(ql.BlackConstantVol(today, ql.UnitedStates(ql.UnitedStates.NYSE),
                                                                    vol, ql.ActualActual()))
    initialValue = ql.QuoteHandle(ql.SimpleQuote(curr))
    process = ql.BlackScholesMertonProcess(initialValue, dividendTS, riskFreeTS, volatility)

    tGrid, xGrid = 2000, 200

    americanCallOption.setPricingEngine(ql.FdBlackScholesVanillaEngine(process, tGrid, xGrid))
    americanPutOption.setPricingEngine(ql.FdBlackScholesVanillaEngine(process, tGrid, xGrid))

    call["Value"] = round(americanCallOption.NPV(),4)
    call["Delta"] = round(americanCallOption.delta(),4)
    call["Gamma"] = round(americanCallOption.gamma(),4)
    call["Theta"] = round(americanCallOption.theta(),4)
    call["Vega"] = "N/A"
    call["Rho"] = "N/A"
    put["Value"] = round(americanPutOption.NPV(),4)
    put["Delta"] = round(americanPutOption.delta(),4)
    put["Gamma"] = round(americanPutOption.gamma(),4)
    put["Theta"] = round(americanPutOption.theta(),4)
    put["Vega"] = "N/A"
    put["Rho"] = "N/A"

    return call, put

def pricing_fixedratebond(faceValue:float, todayDate:str, issueDate:str, maturityDate:str, frequency:str,
                          couponRate:float, discountRate:float):
    """
    Calculate fixed rate bond price using discount cash flow pricing engine.
    Assume constant risk free rate, and calculation follow 30/360 day convention with government bond calendar.
    Simple compounding for coupon payment, continuous compounding for discounting
    Day convention choice: https://www.quantlib.org/reference/group__daycounters.html
    Calendar choice: https://www.quantlib.org/reference/group__calendars.html

    :param faceValue, todayDate, issueDate, maturityDate, frequency, couponRate, discountRate:
    :type float, str, str, str, str, float, float:
    :return: bond_result
    :rtype: dict[Str, float]
    """
    today = ql.Date(todayDate, "%Y-%m-%d")
    issue = ql.Date(issueDate, "%Y-%m-%d")
    ql.Settings.instance().evaluationDate = today
    crv = ql.FlatForward(min(today,issue),discountRate,ql.Thirty360())
    yts = ql.YieldTermStructureHandle(crv)
    bondEngine = ql.DiscountingBondEngine(yts)
    fixedRateBond = ql.FixedRateBond(0, ql.UnitedStates(ql.UnitedStates.GovernmentBond),
                                     faceValue,
                                     issue,
                                     ql.Date(maturityDate, "%Y-%m-%d"),
                                     ql.Period(frequency),
                                     [couponRate],
                                     ql.Thirty360())
    fixedRateBond.setPricingEngine(bondEngine)

    bond_result = {}
    bond_result["NPV"] = round(fixedRateBond.NPV(), 4)
    bond_result["cleanPrice"] = round(fixedRateBond.cleanPrice(),4)
    bond_result["dirtyPrice"] = round(fixedRateBond.dirtyPrice(),4)
    bond_result["accruedAmount"] = round(fixedRateBond.accruedAmount(),4)
    bond_result["bondYield"] = round(fixedRateBond.bondYield(ql.ActualActual(),ql.Compounded, ql.Annual),4)
    bond_result["previousCouponRate"] = round(fixedRateBond.previousCouponRate(),4)
    bond_result["nextCouponRate"] = round(fixedRateBond.nextCouponRate(),4)
    return bond_result

def pricing_cds(nominal:float, spread:float, startDate:str, maturityDate:str, frequency:str,
                discountRate:float, recoveryRate:float, hazardRate:float):
    """
    Calculate Credit Default Swap using mid point CDS pricing engine.
    Assume constant discount rate, recovery rate, harzard rate. Calculation follow Actual365Fixed day convention and
    payment is transferred at 20th of payment month.
    Day convention choice: https://www.quantlib.org/reference/group__daycounters.html
    Payment date choice: https://www.quantlib.org/reference/struct_quant_lib_1_1_date_generation.html

    :param nominal, spread, startDate, maturityDate, frequency, discountRate, recoveryRate, hazardRate:
    :type float, float, str, str, str, float, float, float:
    :return: seller, buyer
    :rtype: dict[Str, float], dict[Str, float]
    """
    start = ql.Date(startDate, "%Y-%m-%d")
    maturity = ql.Date(maturityDate, "%Y-%m-%d")
    ql.Settings.instance().evaluationDate = start

    risk_free_rate = ql.YieldTermStructureHandle(ql.FlatForward(start, discountRate, ql.Actual360()))

    probability = ql.DefaultProbabilityTermStructureHandle(
        ql.FlatHazardRate(start, ql.QuoteHandle(ql.SimpleQuote(hazardRate)), ql.Actual360())
    )

    cdsSchedule = ql.MakeSchedule(start, maturity, ql.Period(frequency),
                                      calendar = ql.TARGET(), convention=ql.Following,
                                      terminalDateConvention=ql.Unadjusted, rule=ql.DateGeneration.TwentiethIMM)
    cds_seller = ql.CreditDefaultSwap(ql.Protection.Seller, nominal, spread/10000, cdsSchedule, ql.Following, ql.Actual360())
    cds_buyer = ql.CreditDefaultSwap(ql.Protection.Buyer, nominal, spread/10000, cdsSchedule, ql.Following, ql.Actual360())
    engine = ql.MidPointCdsEngine(probability, recoveryRate, risk_free_rate)
    cds_seller.setPricingEngine(engine)
    cds_buyer.setPricingEngine(engine)

    seller = {}
    buyer = {}
    seller["fair spread"] = round(cds_seller.fairSpread(),4)
    seller["NPV"] = round(cds_seller.NPV(),4)
    seller["default leg"] = round(cds_seller.defaultLegNPV(),4)
    seller["coupon leg"] = round(cds_seller.couponLegNPV(),4)
    buyer["fair spread"] = round(cds_buyer.fairSpread(),4)
    buyer["NPV"] = round(cds_buyer.NPV(),4)
    buyer["default leg"] = round(cds_buyer.defaultLegNPV(),4)
    buyer["coupon leg"] = round(cds_buyer.couponLegNPV(),4)

    return seller, buyer

def get_libor(libor_term: str, start: str, end: str, api:str):
    commonurl = "https://eodhistoricaldata.com/api/eod/LIBORUSD"
    liborurl = libor_term +".MONEY?"
    startURL = f'from={start}'
    endURL = f'to={end}'
    apiKeyURL = f'api_token={api}'
    completeURL = commonurl + liborurl + startURL + "&" + endURL + "&" + apiKeyURL + "&fmt=json"
    print(completeURL)
    with urllib.request.urlopen(completeURL) as req:
        data = json.load(req)
        return data

def get_bond_rate(bond_term: str, start: str, end: str, api:str):
    commonurl = "https://eodhistoricaldata.com/api/eod/US"
    bondurl = bond_term +".GBOND?"
    startURL = f'from={start}'
    endURL = f'to={end}'
    apiKeyURL = f'api_token={api}'
    completeURL = commonurl + bondurl + startURL + "&" + endURL + "&" + apiKeyURL + "&fmt=json"
    print(completeURL)
    with urllib.request.urlopen(completeURL) as req:
        data = json.load(req)
        return data

def build_yield_curve(benchmark: str, date = None, combine = False):
    "Build yield curve at date based on benchmark data"

    if combine:
        libor_term_list = ["1W", "1M", "2M", "3M", "6M", "12M"]
        bond_term_list = ["3Y", "5Y", "10Y"]
    else:
        libor_term_list = ["1W", "1M", "2M", "3M", "6M", "12M"]
        bond_term_list = ["1M", "3M", "6M", "1Y", "3Y", "5Y", "10Y"]
    instructment = []
    if date == None:
        date_datetime_object = datetime.datetime.today()
    else:
        date_datetime_object = datetime.datetime.strptime(date, "%Y-%m-%d")
    last_week_date = date_datetime_object - datetime.timedelta(days=7)

    helpers = ql.RateHelperVector()

    fixingDays = 1
    calendar = ql.TARGET()
    convention = ql.ModifiedFollowing
    endOfMonth = False
    dayCounter = ql.Actual360()

    if combine:
        for libor_term in libor_term_list:
            libor_last_day = get_libor(libor_term, last_week_date.strftime("%Y-%m-%d"), date_datetime_object.strftime("%Y-%m-%d"), os.environ.get("EOD_API_KEY"))[-1]
            instructment.append(("Libor", libor_term, libor_last_day["adjusted_close"]))
        for bond_term in bond_term_list:
            bond_last_day = get_bond_rate(bond_term, last_week_date.strftime("%Y-%m-%d"), date_datetime_object.strftime("%Y-%m-%d"), os.environ.get("EOD_API_KEY"))[-1]
            instructment.append(("US Treasury", bond_term, bond_last_day["adjusted_close"]))
    else:
        if benchmark == "Libor":
            for libor_term in libor_term_list:
                libor_last_day = get_libor(libor_term, last_week_date.strftime("%Y-%m-%d"), date_datetime_object.strftime("%Y-%m-%d"), os.environ.get("EOD_API_KEY"))[-1]
                instructment.append(("Libor", libor_term, libor_last_day["adjusted_close"]))
        else:
            for bond_term in bond_term_list:
                bond_last_day = get_bond_rate(bond_term, last_week_date.strftime("%Y-%m-%d"), date_datetime_object.strftime("%Y-%m-%d"), os.environ.get("EOD_API_KEY"))[-1]
                instructment.append(("US Treasury", bond_term, bond_last_day["adjusted_close"]))
    print(instructment)

    for instructment, term, rate in instructment:
        if instructment == "Libor":
            libor_index = ql.Libor("MyIndex", ql.Period(term), 2, ql.USDCurrency(), calendar, dayCounter)
            helpers.append(ql.DepositRateHelper(rate/100, libor_index))
        else:
            helpers.append(ql.DepositRateHelper(rate/100, ql.Period(term), fixingDays, calendar, convention, endOfMonth, dayCounter))

    discount_curve = ql.PiecewiseLogLinearDiscount(fixingDays, ql.TARGET(), helpers, dayCounter)
    yield_curve = ql.PiecewiseLinearZero(fixingDays, ql.TARGET(), helpers, dayCounter)
    return yield_curve, discount_curve

def pricing_swap(nominal:float, startDate:str, frequency, tenor, fixed_rate):
    """
    Calculate vanilla interest rate swap using discount swap pricing engine.
    THe yield curve is built on Libor rate only, if the tenor is less than one year. Otherwise, it is built on treasury
    yield only
    Calculation follows Actual/360 day convention for floating rate payment, and 30/360 day count convention for fixed
    rate payment.
    Day convention choice: https://www.quantlib.org/reference/group__daycounters.html

    :param nominal, startDate, frequency, tenor, fixed_rate:
    :type float, str, str, str, float:
    :return: swap_result, swap_history
    :rtype: dict[Str, float], dataframe
    """
    swap_result = {}
    spread = 0
    forward_start = ql.Period(0, ql.Days)

    valuationDate = ql.Date(startDate, "%Y-%m-%d")
    ql.Settings.instance().evaluationDate = valuationDate

    qlfrequency = ql.Period(frequency, ql.Months)
    qltenor = ql.Period(tenor, ql.Months)
    if qltenor > ql.Period("1y"):
        yield_curve, discount_curve = build_yield_curve(benchmark="US Treasury", date = startDate, combine=False)
    else:
        yield_curve, discount_curve = build_yield_curve(benchmark="Libor", date = startDate, combine=False)
    yts = ql.RelinkableYieldTermStructureHandle()
    yts.linkTo(discount_curve)
    engine = ql.DiscountingSwapEngine(yts)
    index = ql.USDLibor(qlfrequency, yts)

    swap_with_different_payment_schedule = ql.MakeVanillaSwap(qltenor, index, fixed_rate, forward_start,
                                                              Nominal=nominal, pricingEngine=engine, swapType=ql.VanillaSwap.Payer)
    swap = ql.VanillaSwap(
        ql.VanillaSwap.Payer, nominal,
        swap_with_different_payment_schedule.floatingSchedule(), fixed_rate, ql.Thirty360(),
        swap_with_different_payment_schedule.floatingSchedule(), index, spread, ql.Actual360()
    )
    swap.setPricingEngine(engine)

    swap_result["fairRate"] = round(swap.fairRate(), 4)
    swap_result["NPV"] = round(swap.NPV(), 4)


    swap_history = pd.DataFrame({
                                 'nominal': cf.nominal(),
                                 'accrualStartDate': cf.accrualStartDate().ISO(),
                                 'accrualEndDate': cf.accrualEndDate().ISO(),
                                 'float rate': round(cf.rate(), 4),
                                 'float amount': round(cf.amount(), 4),
                             } for cf in map(ql.as_coupon, swap.leg(1)))
    swap_history["fixed rate"] = [round(cf.rate(), 4) for cf in map(ql.as_coupon, swap.leg(0))]
    swap_history["fixed amount"] = [round(-cf.amount(), 4) for cf in map(ql.as_coupon, swap.leg(0))]
    return swap_result, swap_history

def pricing_fra(notional:float, valuationDate:str, effective_months_from_valuation, termination_months_from_valuation, fixed_rate):
    """
    Calculate interest rate swap using discount swap pricing engine.
    THe yield curve is built on Libor rate only, if the tenor is less than one year. Otherwise, it is built on treasury
    yield only
    Calculation follows Actual/360 day convention for floating rate payment, and 30/360 day count convention for fixed
    rate payment.
    Day convention choice: https://www.quantlib.org/reference/group__daycounters.html

    :param nominal, startDate, frequency, tenor, fixed_rate:
    :type float, str, str, str, float:
    :return: swap_result, swap_history
    :rtype: dict[Str, float], dataframe
    """
    fra_result = {}
    qlValuationDate = ql.Date(valuationDate, "%Y-%m-%d")
    ql.Settings.instance().evaluationDate = qlValuationDate

    yts =  ql.RelinkableYieldTermStructureHandle()
    yield_curve, discount_curve = build_yield_curve(benchmark="Libor", date = valuationDate, combine=False)
    yts.linkTo(discount_curve)

    libor_term = str(termination_months_from_valuation - effective_months_from_valuation) + "m"
    index = ql.USDLibor(ql.Period(libor_term), yts)
    fra_calendar = index.fixingCalendar()
    fra_day_convention = index.businessDayConvention()
    fra_day_counter = index.dayCounter()

    start_date = fra_calendar.advance(qlValuationDate, int(effective_months_from_valuation), ql.Months, fra_day_convention)
    termination_date = fra_calendar.advance(qlValuationDate, int(termination_months_from_valuation), ql.Months, fra_day_convention)

    fra = ql.ForwardRateAgreement(start_date, termination_date, ql.Position.Long, fixed_rate, notional, index, yts)

    fra_result["NPV"] = round(fra.NPV(), 4)
    fra_result["forwardRate"] = fra.forwardRate()
    fra_result["sportValue"] = round(fra.spotValue(), 4)
    fra_result["forwardValue"] = round(fra.forwardValue(), 4)
    fra_result["impliedYield"] = fra.impliedYield(fra.spotValue(), fra.forwardValue(), qlValuationDate, compoundingConvention=ql.Continuous, dayCounter=fra_day_counter)
    fra_result["marketZeroRate"] = yts.zeroRate(termination_date, fra_day_counter, ql.Continuous)

    return fra_result
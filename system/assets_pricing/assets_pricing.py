import QuantLib as ql


class AssetPricingResult:
    def __init__(self):
        self.xvalue = []
        self.call = []
        self.put = []
        self.xparameter = ""
        self.yparameter = ""


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
    crv = ql.FlatForward(min(today,issue),discountRate,ql.Actual365Fixed())
    yts = ql.YieldTermStructureHandle(crv)
    bondEngine = ql.DiscountingBondEngine(yts)
    fixedRateBond = ql.FixedRateBond(2, ql.UnitedStates(ql.UnitedStates.GovernmentBond),
                                     faceValue,
                                     issue,
                                     ql.Date(maturityDate, "%Y-%m-%d"),
                                     ql.Period(frequency),
                                     [couponRate],
                                     ql.Actual365Fixed())
    fixedRateBond.setPricingEngine(bondEngine)

    bond_result = {}
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
    Payment data choice: https://www.quantlib.org/reference/struct_quant_lib_1_1_date_generation.html

    :param nominal, spread, startDate, maturityDate, frequency, discountRate, recoveryRate, hazardRate:
    :type float, float, str, str, str, float, float, float:
    :return: seller, buyer
    :rtype: dict[Str, float], dict[Str, float]
    """
    start = ql.Date(startDate, "%Y-%m-%d")
    maturity = ql.Date(maturityDate, "%Y-%m-%d")
    ql.Settings.instance().evaluationDate = start

    risk_free_rate = ql.YieldTermStructureHandle(ql.FlatForward(start, discountRate, ql.Actual365Fixed()))

    probability = ql.DefaultProbabilityTermStructureHandle(
        ql.FlatHazardRate(start, ql.QuoteHandle(ql.SimpleQuote(hazardRate)), ql.Actual360())
    )

    cdsSchedule = ql.MakeSchedule(start, maturity, ql.Period(frequency),
                                      calendar = ql.TARGET(), convention=ql.Following,
                                      terminalDateConvention=ql.Unadjusted, rule=ql.DateGeneration.TwentiethIMM)
    cds_seller = ql.CreditDefaultSwap(ql.Protection.Seller, nominal, spread/10000, cdsSchedule, ql.Following, ql.Actual365Fixed())
    cds_buyer = ql.CreditDefaultSwap(ql.Protection.Buyer, nominal, spread/10000, cdsSchedule, ql.Following, ql.Actual365Fixed())
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
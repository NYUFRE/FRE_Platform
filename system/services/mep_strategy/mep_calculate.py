def calculate_PSAR(hprices, lprices):
    assert(len(hprices) == len(lprices))
    assert(type(hprices) == type(lprices))

    PSAR_list = []
    AF_init = .02
    AF_stride = .02
    AF_max = .2

    PSAR = lprices[0]
    EP = hprices[0]
    EMP = EP-PSAR
    AF = AF_init
    DTA = EMP*AF
    trend=Trend.BULL

    PSAR_list.append(PSAR)

    PSAR_prev = PSAR
    EP_prev = EP
    EMP_prev = EMP
    AF_prev = AF
    DTA_prev = DTA
    trend_prev = trend

    for hp, lp in zip(hprices[1:], lprices[1:]):
        # Update PSAR
        if trend_prev == Trend.BULL and PSAR_prev + DTA_prev > lp:
            PSAR = EP_prev
        elif trend_prev == Trend.BEAR and PSAR_prev + DTA_prev < hp:
            PSAR = EP_prev
        else:
            PSAR = PSAR_prev + DTA_prev

        # Update trend
        if PSAR < hp:
            trend = Trend.BULL
        else:
            trend = Trend.BEAR

        # Update EP
        if trend == Trend.BULL and hp > EP_prev:
            EP = hp
        elif trend == Trend.BEAR and lp < EP_prev:
            EP = lp
        else:
            EP = EP_prev

        # Update AF
        if trend == trend_prev:
            if (trend == Trend.BULL and EP > EP_prev) or (trend == Trend.BEAR and EP < EP_prev):
                AF = min(AF_max, AF_prev+AF_stride)
            else:
                AF = AF_prev
        else:
            AF = AF_init

        # Update EMP
        EMP = EP - PSAR

        # Update DTA
        DTA = EMP * AF

        # Save PSAR
        PSAR_list.append(PSAR)

        # Update prev
        PSAR_prev = PSAR
        EP_prev = EP
        EMP_prev = EMP
        AF_prev = AF
        DTA_prev = DTA
        trend_prev = trend

    if type(hprices) == pd.core.series.Series:
        return pd.Series(data=PSAR_list, index=hprices.index)

    return np.array(PSAR_list, dtype=float)


def calculate_exponential_moving_average(xs, window_size=200, smoothing=2):
    multiplier = smoothing / (1 + window_size)

    ema_list = [ xs[0], ]
    for i in range(1, len(xs)):
        ema = multiplier * xs[i] + (1 - multiplier) * ema_list[-1]
        ema_list.append(ema)

    if type(xs) == pd.core.series.Series:
        return pd.Series(data=ema_list, index=xs.index)

    return np.array(ema_list)


def calculate_moving_average_convergence_divergence(xs):
    ema12 = calculate_EMA(xs, window_size=12)
    ema26 = calculate_EMA(xs, window_size=26)

    return ema12 - ema26


def calculate_moving_average_convergence_divergence_signal(xs):
    macds = calculate_MACD(xs)
    macd9 = calculate_EMA(macds, window_size=9)

    return macd9


calculate_EMA = calculate_exponential_moving_average
calculate_MACD = calculate_moving_average_convergence_divergence
calculate_MACD_signal = calculate_moving_average_convergence_divergence_signal

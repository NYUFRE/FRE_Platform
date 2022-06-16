import warnings

from flask import flash, render_template, request
from sqlalchemy.exc import SAWarning
from system import iex_market_data

warnings.simplefilter(action='ignore', category=SAWarning)


def quote_service():
    if request.method == 'POST':
        if not request.form.get("symbol"):
            flash('ERROR! symbol missing.', 'error')
            return render_template("get_quote.html")

        # Get quote data from IEX, quoted prices (Ask & Bid) are different from the latest price
        quote, error = iex_market_data.get_quote(request.form.get("symbol"))
        price, error = iex_market_data.get_price(request.form.get("symbol"))

        if len(error) > 0 or len(price) == 0 or len(quote) == 0:
            flash('ERROR! Invalid symbol.', 'error')
            return render_template("get_quote.html")
        else:
            quote['Latest Price'] = price['price']
            return render_template("quote.html", dict=quote)

    else:
        return render_template("get_quote.html")
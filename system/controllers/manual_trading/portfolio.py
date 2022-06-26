import json
import warnings

import plotly
import plotly.express as px
import plotly.graph_objs as go
from flask import render_template, session
from sqlalchemy.exc import SAWarning

from system import database, iex_market_data
from system.services.utility.helpers import error_page, usd

warnings.simplefilter(action='ignore', category=SAWarning)


def portfolio_service():
    portfolio = database.get_portfolio(session['user_id'])

    cash = portfolio['cash']
    total = cash

    length = len(portfolio['symbol'])

    # Initializing Chart
    labels = ['Cash']
    sizes = [1.0]

    # When holding stocks
    if length > 0:
        for i in range(len(portfolio['symbol'])):
            # Get the latest price for each holding stocks
            price, error = iex_market_data.get_price(portfolio['symbol'][i])
            if len(error) > 0:
                return error_page(error)
            portfolio['name'][i] = price['name']
            portfolio['price'][i] = price['price']
            portfolio['pnl'][i] = (price['price'] - portfolio['avg_cost'][i]) * portfolio['shares'][i]
            cost = price['price'] * portfolio['shares'][i]
            portfolio['total'][i] = cost
            total += cost
        # Calculate proportion
        for i in range(len(portfolio['symbol'])):
            portfolio['proportion'][i] = "{:.2%}".format(portfolio['total'][i] / total)
        cash_proportion = "{:.2%}".format(cash / total)

        # Pie Chart Plot
        labels = portfolio['symbol'] + ['Cash']
        sizes = portfolio['proportion'] + [cash_proportion]
        sizes = [float(num[:-1]) for num in sizes]
        graph_values = [{'labels': labels, 'values': sizes, 'type': 'pie', 'textinfo': 'label+percent',
                         'insidetextfont': {'color': '#FFFFFF', 'size': '14'},
                         'textfont': {'color': '#FFFFFF', 'size': '14'},
                         'hole': '.6', 'marker': {'colors': px.colors.qualitative.Bold}}]
        layout = {'title': '<b>Portfolio Holdings</b>'}

        # PnL Bar_plot
        trace2 = go.Bar(x=portfolio['symbol'], y=portfolio['pnl'], marker={'color': px.colors.qualitative.Bold},
                        width=0.5, opacity=0.85, text=portfolio['pnl'], textposition='auto', texttemplate='%{text:.2f}')
        layout2 = dict(title="<b>Portfolio Unrealized PnL</b>", xaxis=dict(title="Symbol"), yaxis=dict(title="PnL"), )
        pnl_plot = [trace2]
        fig = go.Figure(data=pnl_plot, layout=layout2)
        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        return render_template('portfolio.html', dict=portfolio, total=usd(total), cash=usd(cash),
                               cash_proportion=cash_proportion, length=length, graph_values=graph_values, layout=layout,
                               graphJSON=graphJSON)

    # Only cash
    else:
        # Method 2 with plotly
        graph_values = [{
            'labels': labels,
            'values': sizes,
            'type': 'pie',
            'textinfo': 'label+percent',
            'insidetextfont': {'color': '#FFFFFF',
                               'size': '14'},
            'textfont': {'color': '#FFFFFF',
                         'size': '14'},
            'hole': '.6',
            'marker': {'colors': px.colors.qualitative.Bold}
        }]
        layout = {'title': '<b>Portfolio Holdings</b>'}
        return render_template("portfolio.html", dict=[], total=usd(cash), cash=usd(cash), cash_proportion="100%",
                               length=0, graph_values=graph_values, layout=layout)
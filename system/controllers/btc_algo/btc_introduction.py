from flask import render_template


def btc_introduction_service():
    """
    Return the introduction page for the BTC algorithm.
    """
    return render_template('btc_introduction.html')

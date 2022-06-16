import warnings

from flask import flash, render_template, request
from sqlalchemy.exc import SAWarning
from system import database
from system.services.VaR.VaR_Calculator import VaR, set_risk_threshold, var_data

warnings.simplefilter(action='ignore', category=SAWarning)


def risk_management_service():
    database.create_table(['risk_threshold'])
    params = {'method': "", 'confidence_level': 99, 'period': 1}
    threshold = {'enable_threshold': None, 'confidence_threshold': 99, 'period_threshold': 1, 'var_threshold': 10} \
        if len(database.execute_sql_statement("SELECT * FROM risk_threshold").to_dict('r')) == 0 \
        else database.execute_sql_statement("SELECT * FROM risk_threshold").to_dict('r')[0]
    result = {'var': 0, 'es': 0, 'var_hist': None}

    if request.method == 'POST':
        # Get parameters from form
        form_input = request.form
        ### VaR params
        params['method'] = form_input.get('VaR_methods')
        params['confidence_level'] = form_input.get('confidence_level')
        params['period'] = form_input.get('period')
        ### VaR thresholds
        threshold['enable_threshold'] = form_input.get('enable_threshold')
        threshold['confidence_threshold'] = form_input.get('confidence_threshold')
        threshold['period_threshold'] = form_input.get('period_threshold')
        threshold['var_threshold'] = form_input.get('var_threshold')

        # Set threshold
        set_risk_threshold(database, threshold)
        threshold = {'enable_threshold': None, 'confidence_threshold': 99, 'period_threshold': 1, 'var_threshold': 10} \
            if len(database.execute_sql_statement("SELECT * FROM risk_threshold").to_dict('r')) == 0 \
            else database.execute_sql_statement("SELECT * FROM risk_threshold").to_dict('r')[0]

        # Calculate VAR and return value
        port_var = VaR(int(params['confidence_level']), int(params['period']))
        if params['method'] == 'hist_sim':
            result['var'], result['es'], result['var_hist'] = port_var.historical_simulation_method()
        elif params['method'] == 'garch':
            result['var'], result['es'], result['var_hist'] = port_var.GARCH_method()
        elif params['method'] == 'EVT':
            result['var'], result['es'], result['var_hist'] = port_var.extreme_value_method()
        elif params['method'] == 'caviar_sav':
            result['var'], result['es'], result['var_hist'] = port_var.caviar_SAV()
        elif params['method'] == 'caviar_as':
            result['var'], result['es'], result['var_hist'] = port_var.caviar_AS()
        else:
            flash("Invalid method selected")
        # Populate VaR_data for plotting
        if result['var_hist'] is not None:
            var_data.date = result['var_hist'].index[-1000:]
            var_data.port_returns = result['var_hist']['port_returns'][-1000:]
            var_data.VaR = result['var_hist']['VaR'][-1000:]

        # Rendering webpage
        return render_template('risk_management.html', params=params, threshold=threshold, result=result)
    else:
        return render_template('risk_management.html', params=params, threshold=threshold, result=result)
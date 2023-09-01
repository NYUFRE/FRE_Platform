from system.controllers.algotrade.yahoo_finance import download_yahoo_finance_data
from system.controllers.algotrade.trading_strategy import Stock
from system.controllers.algotrade.trading_strategy import build_strategy, run_strategy, plot_strategy, optimize_strategy


class Stock:
	def __init__(self, symbol, start_date, end_date):
		self.symbol = symbol
		self.start_date = start_date
		self.end_date = end_date

if __name__ == '__main__':

	def print_menu(menu):
		for key in menu.keys():
			print (key, '--', menu[key] )

	spy = Stock('spy', '2010-01-01', '2023-08-31')
	ibm = Stock('ibm', '2023-01-01', '2023-08-31')
	orcl = Stock('orcl', '2000-01-01', '2000-12-31')
	tsla = Stock('tsla', '2010-01-01', '2023-08-31')
	ibm_list = [Stock('ibm', '2020-01-01', '2020-12-31'), Stock('ibm', '2021-01-01', '2021-12-31'), Stock('ibm', '2022-01-01', '2022-12-31')]

	menu_options = {
		1: 'Retrive Stock Daily Price Data',
		2: 'Build Simple Strategy',
		3: 'Build SMA Strategy',
		4: 'Build SMA RSI Strategy',
		5: 'Simulate SMA Trading',
		6: 'Plot SMA Crossover',
		7: 'Optimize SMA RSI Strategy',
		0: 'Exit'
	}

	submenu_options = {
		1: spy.symbol.upper() + ' ' + spy.start_date + ' to ' + spy.end_date,
		2: ibm.symbol.upper() + ' ' + ibm.start_date + ' to ' + ibm.end_date,
		3: orcl.symbol.upper() + ' ' + orcl.start_date + ' to ' + orcl.end_date,
		4: tsla.symbol.upper() + ' ' + tsla.start_date + ' to ' + tsla.end_date,
		5: ibm_list[0].symbol.upper() + ' ' + ibm_list[0].start_date + ' to ' + ibm_list[2].end_date,
		0: 'Exit'
	}
	while(True):
		print_menu(menu_options)
		option = 0
		try:
			print('Enter your choice: ')
			option = int(input())
		except:
			print('Wrong input. Please enter a number ...')
		if option == 1:
			while (True):
				print('Retrieve Yahoo Finance Data...')
				print_menu(submenu_options)
				sub_option = 0
				try:
					print('Enter your choice for retrieving Yahoo Finance data: ')
					sub_option = int(input())
				except:
					print('Wrong input. Please eter a correct choice')
				if sub_option == 1:
					download_yahoo_finance_data(spy.symbol, spy.start_date, spy.end_date)
					break
				elif sub_option == 2:
					download_yahoo_finance_data(ibm.symbol, ibm.start_date, ibm.end_date)
					break
				elif sub_option == 3:
					download_yahoo_finance_data(orcl.symbol, orcl.start_date, orcl.end_date)
					break
				elif sub_option == 4:
					download_yahoo_finance_data(tsla.symbol, tsla.start_date, tsla.end_date)
					break
				elif sub_option == 5:
					for stock in ibm_list:
						download_yahoo_finance_data(stock.symbol, stock.start_date, stock.end_date)
					break
				elif sub_option == 0:
					break
				else:
					print('Wrong input. Please eter a correct choice')
		elif option == 2:
			build_strategy(spy, 'simple')
		elif option == 3:
			build_strategy(spy, 'sma')
		elif option == 4:
			build_strategy(spy, 'sma_rsi')
		elif option == 5:
			run_strategy(orcl, 'sma_trading', 15)
		elif option == 6:
			plot_strategy(ibm, 'sma_crossover', 20)
		elif option == 7:
			optimize_strategy(ibm_list, 'sma_rsi')
		elif option == 0:
			print('Thanks for using AlgoTrade Testing Program!')
			exit()
		else:
			print('Invalid option. Please enter a number between 0 and 6.')


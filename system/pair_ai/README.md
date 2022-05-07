# Pairs Selection with Unsupervised Learning #
* *Environment* run in a Python vritual env or Docker container
* *Author* Felix Lyu <sl8580@nyu.edu>
* *Supervisor* Song Tang <st290@nyu.edu>
* *Details:* Felix Lyu's Capstone Project. The work is based on Jonathan Larkins' "Paris Trading with Machine Learning". The program uses DBSCAN to find possible pairs for trading within the S&P500 pool. Back testsing is conducted to find best paris in terms of sharpe ratio, and probation testing is then conducted to be assessed against SPY.

## To Use The Model
### With Virtual Env
After logging onto FRE Platform, go to the student projects and select "PairsTradingWithAI".

Enter the start date and end date for the training. The default range of the database starts with 2019-01-01.

Enter the end date of the back test. The start date is the end of the training date, which can't be changed.

Select the fundamental information to be included in the training. Notice that the menu supports multiple selection. For Mac, press command for multiple selection. For Windows, press ctrl.

Click on the Run Model to initiate the training, back testing and probation testing.

### Potential further improvements:
1. Stricter date checking to prevent end dates before start date.
2. Implement a calendar dropdown for easier date entering.
3. Allow different pairs trading strategy.
4. Plot a graph for the trades for better visual comparison with SPY.

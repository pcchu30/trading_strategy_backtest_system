# trading_strategy_backtest_system
**trading_strategy_backtest_system** is a Python-based event-driven backtesting simulation engine, which has been
developed to backtest my own machine learning trading strategies.

**TradingSession** is the key class, and its member method, **_run_session()**, carries out
an infinite while loop that polls the events queue. The loop continue until the event
queue has been emptied. The **_run_session()** is shown below.

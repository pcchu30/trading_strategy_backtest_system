# trading_strategy_backtest_system
**trading_strategy_backtest_system** is a Python-based event-driven backtesting simulation engine, which has been
developed to backtest my own machine learning trading strategies.
## TradingSession
**TradingSession** is the key class, and its member method, **_run_session()**, carries out
an infinite while loop that polls the events queue. The loop continue until the event
queue has been emptied. The **_run_session()** is shown below.

```python
 def _run_session(self):
        """
        Carries out an infinite while loop that polls the
        events queue and directs each event to either the
        strategy component of the execution handler. The
        loop continue until the event queue has been
        emptied.
        """
        if self.session_type == "backtest":
            print("Running Backtest...")
        else:
            print("Running Realtime Session until %s" % self.end_session_time)
        # Queue, block is false, return an item if one is immediately available,
        # else raise the Empty exception
        while self._continue_loop_condition():
            try:
                event = self.events_queue.get(False)
            except queue.Empty:
                self.price_handler.stream_next()
            else:
                if event is not None:
                    if (
                        event.type == EventType.TICK or
                        event.type == EventType.BAR
                    ):
                        self.cur_time = event.time
                        self.strategy.calculate_signals(event)
                        self.portfolio_handler.update_portfolio_value()
                        # update equity curve
                        self.statistics.update(event.time, self.portfolio_handler)
                    elif event.type == EventType.SIGNAL:
                        self.portfolio_handler.on_signal(event)
                    elif event.type == EventType.ORDER:
                        self.execution_handler.execute_order(event)
                    elif event.type == EventType.FILL:
                        self.portfolio_handler.on_fill(event)
                    else:
                        raise NotImplemented("Unsupported event.type '%s'" % event.type)
```
## UML Class Diagram

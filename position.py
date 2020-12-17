from numpy import sign

# replace seven // with /

class Position(object):
    def __init__(
        self, action, ticker, init_quantity,
        init_price, init_commission,
        bid, ask
    ):
        """
        Set up the initial "account" of the Position to be
        zero for most items, with the exception of the initial
        purchase/sale.

        Then calculate the initial values and finally update the
        market value of the transaction.
        """
        assert init_quantity > 0, "Invalid quantity"

        self.action = action
        self.ticker = ticker
        # change from self.quantity to self.position
        self.position = 0
        self.init_price = init_price
        self.init_commission = init_commission

        self.realised_pnl = 0
        self.unrealised_pnl = 0

        self.buys = 0
        self.sells = 0
        self.avg_bot = 0
        self.avg_sld = 0
        self.total_bot = 0
        self.total_sld = 0
        self.total_commission = init_commission

        self._calculate_initial_value(init_quantity)
        self.update_market_value(bid, ask)

    def reset(self, action, init_quantity, init_price, init_commission):
        assert init_quantity > 0, "Invalid quantity"

        self.action = action
        self.position = 0
        self.init_price = init_price
        self.init_commission = init_commission

        self.unrealised_pnl = 0

        self.buys = 0
        self.sells = 0
        self.avg_bot = 0
        self.avg_sld = 0
        self.total_bot = 0
        self.total_sld = 0
        self.total_commission = init_commission

        self._calculate_initial_value(init_quantity)

    def _calculate_initial_value(self, init_quantity):
        """
        Depending upon whether the action was a buy or sell ("BOT"
        or "SLD") calculate the average bought cost, the total bought
        cost, the average price and the cost basis.

        Finally, calculate the net total with and without commission.
        """
        assert init_quantity > 0, "Invalid quantity"

        if self.action == "BOT":
            self.buys = init_quantity
            # means avg_bot_price
            self.avg_bot = self.init_price
            self.total_bot = self.buys * self.avg_bot
            self.avg_price = (self.init_price * init_quantity + self.init_commission) / init_quantity
            self.cost_basis = init_quantity * self.avg_price
        else:  # action == "SLD"
            self.sells = init_quantity
            self.avg_sld = self.init_price
            self.total_sld = self.sells * self.avg_sld
            self.avg_price = (self.init_price * init_quantity - self.init_commission) / init_quantity
            self.cost_basis = -init_quantity * self.avg_price
        self.net = self.buys - self.sells
        self.position = self.net
        self.net_total = self.total_sld - self.total_bot
        self.net_incl_comm = self.net_total - self.init_commission

    def update_market_value(self, bid, ask):
        """
        The market value is tricky to calculate as we only have
        access to the top of the order book through Interactive
        Brokers, which means that the true redemption price is
        unknown until executed.

        However, it can be estimated via the mid-price of the
        bid-ask spread. Once the market value is calculated it
        allows calculation of the unrealised and realised profit
        and loss of any transactions.
        """
        midpoint = (bid + ask) / 2
        #self.market_value = self.quantity * midpoint * sign(self.net)
        self.market_value = self.position * midpoint
        self.unrealised_pnl = self.market_value - self.cost_basis

    def transact_shares(self, action, quantity, price, commission):
        """
        Calculates the adjustments to the Position that occur
        once new shares are bought and sold.

        Takes care to update the average bought/sold, total
        bought/sold, the cost basis and PnL calculations,
        as carried out through Interactive Brokers TWS.
        """
        assert quantity > 0, "Invalid quantity"
        assert price > 0, "Invalid price"
        assert commission >= 0, "Invalid commission"

        self.total_commission += commission

        # Adjust total bought and sold
        if action == "BOT":
            self.avg_bot = (
                self.avg_bot * self.buys + price * quantity
            ) / (self.buys + quantity)
            if self.action != "SLD":  # Increasing long position
                self.avg_price = (
                    self.avg_price * self.buys + price * quantity + commission
                ) / (self.buys + quantity) # important
                self.buys += quantity
                self.total_bot = self.buys * self.avg_bot
            elif self.action == "SLD":  # Closed partial positions out
                if abs(quantity) <= abs(self.position):
                    self.realised_pnl += quantity * ( self.avg_price - price
                    ) - commission  # Adjust realised PNL, short selling
                    self.buys += quantity
                    self.total_bot = self.buys * self.avg_bot
                else:
                    newPos = self.position + quantity
                    self.realised_pnl += self.position * (
                            price - self.avg_price        # short selling, close position
                    ) - commission*(abs(self.position)/abs(quantity))  # improve by ratio
                    # open new long position
                    self.reset("BOT", newPos, price, commission*(abs(newPos)/abs(quantity)))
                    return
            # self.buys += quantity
            # self.total_bot = self.buys * self.avg_bot

        # action == "SLD"
        else:
            self.avg_sld = (
                self.avg_sld * self.sells + price * quantity
            ) / (self.sells + quantity)
            if self.action != "BOT":  # Increasing short position
                self.avg_price = ( self.avg_price * self.sells + price * quantity - commission
                ) / (self.sells + quantity)          # important
                self.sells += quantity
                self.total_sld = self.sells * self.avg_sld
                #self.unrealised_pnl -= commission
            elif self.action == "BOT":  # Closed partial positions out
                if abs(quantity) <= abs(self.position):
                    self.realised_pnl += quantity * ( price - self.avg_price
                    ) - commission       # Update realised PNL, long position
                    self.sells += quantity
                    self.total_sld = self.sells * self.avg_sld
                else:
                    newPos = abs(self.position - quantity)
                    self.realised_pnl += self.position * (price - self.avg_price # close long
                    ) - commission * (abs(self.position) / abs(quantity))  # improve by ratio
                    # open new short position
                    self.reset("SLD", newPos, price, commission * (abs(newPos) / abs(quantity)))
                    return

            # self.sells += quantity
            # self.total_sld = self.sells * self.avg_sld

        # Adjust net values, including commissions
        self.net = self.buys - self.sells
        self.position = self.net
        self.net_total = self.total_sld - self.total_bot
        self.net_incl_comm = self.net_total - self.total_commission

        # Adjust average price and cost basis
        self.cost_basis = self.position * self.avg_price

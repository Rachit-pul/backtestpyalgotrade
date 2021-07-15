from __future__ import print_function

from pyalgotrade import strategy
from pyalgotrade import plotter, bar
from pyalgotrade.barfeed import csvfeed
from pyalgotrade.technical import vwap, macd, cross
from pyalgotrade.stratanalyzer import sharpe
from pyalgotrade import broker as basebroker
from pyalgotrade.stratanalyzer import returns, trades, drawdown



class vWap(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, vWapPeriod):
        super(vWap, self).__init__(feed)
        self.__instrument = instrument
        self.vwapperiod = 20
        self.__vWap = vwap.VWAP(feed[instrument], vWapPeriod)
        self.__macd = macd.MACD(feed[instrument].getCloseDataSeries(),12,26,9)
    
    def getvWap(self):
        return self.__vWap

    def getMacd(self):
        return self.__macd


    def onOrderUpdated(self, order):
        if order.isBuy():
            orderType = "Buy"
        else:
            orderType = "Sell"
        self.info("%s order %d updated - Status: %s" % (
            orderType, order.getId(), basebroker.Order.State.toString(order.getState())
        ))

    def onBars(self, bars):
        _vwap = self.__vWap[-1]
        _macd = self.__macd[-1]
        _macdsignal = self.__macd.getSignal()[-1]
        if _vwap is None or _macd is None:
            return

        shares = self.getBroker().getShares(self.__instrument)
        bar = bars[self.__instrument]
        if shares == 0 and bar.getClose() > _vwap and cross.cross_above(self.__macd,self.__macd.getSignal()):
            sharesToBuy = 1
            self.info("Placing buy market order for %s shares" % sharesToBuy)
            self.marketOrder(self.__instrument, sharesToBuy)
        elif shares > 0 and (bar.getClose() < _vwap):
            self.info("Placing sell market order for %s shares" % shares)
            self.marketOrder(self.__instrument, -1*shares)



#driver code

def main(plot =True):
    instrument = "nif"
    vWapPeriod = 20

    # Download the bars.
    feed = csvfeed.GenericBarFeed(bar.Frequency.DAY)
    feed.addBarsFromCSV("nif", "NIFTY-I-EODmin.csv",skipMalformedBars= True)


    strat = vWap(feed, instrument, vWapPeriod)

    # returnsAnalyzer = returns.Returns()
    # strat.attachAnalyzer(returnsAnalyzer)
    drawDownAnalyzer = drawdown.DrawDown()
    strat.attachAnalyzer(drawDownAnalyzer)
    tradesAnalyzer = trades.Trades()
    strat.attachAnalyzer(tradesAnalyzer)

    if plot:
        plt = plotter.StrategyPlotter(strat, True, True, True)
        plt.getInstrumentSubplot(instrument).addDataSeries("VWAP", strat.getvWap())


    strat.run()

    print("")
    print("Total trades: %d" % (tradesAnalyzer.getCount()))
    if tradesAnalyzer.getCount() > 0:
        profits = tradesAnalyzer.getAll()
        print("Avg. profit: $%2.f" % (profits.mean()))
        print("Profits std. dev.: $%2.f" % (profits.std()))
        print("Max. profit: $%2.f" % (profits.max()))
        print("Min. profit: $%2.f" % (profits.min()))

    print("")
    print("Profitable trades: %d" % (tradesAnalyzer.getProfitableCount()))
    if tradesAnalyzer.getProfitableCount() > 0:
        profits = tradesAnalyzer.getProfits()
        print("Avg. profit: $%2.f" % (profits.mean()))
        print("Profits std. dev.: $%2.f" % (profits.std()))
        print("Max. profit: $%2.f" % (profits.max()))
        print("Min. profit: $%2.f" % (profits.min()))


    print("")
    print("Unprofitable trades: %d" % (tradesAnalyzer.getUnprofitableCount()))
    if tradesAnalyzer.getUnprofitableCount() > 0:
        losses = tradesAnalyzer.getLosses()
        print("Avg. loss: $%2.f" % (losses.mean()))
        print("Losses std. dev.: $%2.f" % (losses.std()))
        print("Max. loss: $%2.f" % (losses.min()))
        print("Min. loss: $%2.f" % (losses.max()))
    strat.info("Final portfolio value: $%.2f" % strat.getResult())


# Plot the strategy.

    if plot:
        plt.plot()


if __name__ == "__main__":
    main(True)
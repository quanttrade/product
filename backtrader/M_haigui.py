# -*- coding: utf-8 -*-
"""
Created on Sat Feb 25 10:39:07 2023
量化投资4：基于backtrader实现多股回测-复杂多股回测

@author: adair2019
"""

from __future__ import (absolute_import, division, print_function,unicode_literals)
import datetime
import backtrader as bt
import pandas as pd
from backtrader_plotting import Bokeh
from backtrader_plotting.schemes import Tradimo

class TestSizer(bt.Sizer):
    params = (('stake', 1),)
    def _getsizing(self, comminfo, cash, data, isbuy):
        if isbuy:
            return self.p.stake
        else:
            position = self.broker.getposition(data)
            if not position.size:
                return 0
            else:
                return position.size
        return self.p.stake

class TestStrategy(bt.Strategy):
    params = ( ('maperiod', 15),  ('printlog', False), )
    def log(self, txt, dt=None, doprint=False):
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):

        self.dataclose = dict()
        self.datahigh = dict()
        self.datalow = dict()
        self.order = dict()
        self.buyprice = dict()
        self.buycomm = dict()
        self.buytime = dict()
        self.DonchianHi = dict()
        self.DonchianLo = dict()
        self.TR = dict()
        self.ATR = dict()
        self.CrossoverHi = dict()
        self.CrossoverLo = dict()
        for data in self.datas:
             self.dataclose[data._name] = data.close
             self.datahigh[data._name] = data.high
             self.datalow[data._name] = data.low
             self.order[data._name] = None
             self.buyprice[data._name] = 0
             self.buycomm[data._name] = 0
             self.buytime[data._name] = 0
        # # 参数计算，唐奇安通道上轨、唐奇安通道下轨、ATR
             self.DonchianHi[data._name] = bt.indicators.Highest(data.high(-1), period=20, subplot=False)
             self.DonchianLo[data._name] = bt.indicators.Lowest(data.low(-1), period=10, subplot=False)
             self.TR[data._name] = bt.indicators.Max((data.high - data.low), abs(data.close(-1) - data.high), abs(data.close(-1) - data.low))
             self.ATR[data._name] = bt.indicators.SimpleMovingAverage(self.TR[data._name], period=14, subplot=False)
        # 唐奇安通道上轨突破、唐奇安通道下轨突破
             self.CrossoverHi[data._name] = bt.ind.CrossOver(data.close, self.DonchianHi[data._name], subplot=False)
             self.CrossoverLo[data._name] = bt.ind.CrossOver(data.close, self.DonchianLo[data._name], subplot=False)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Stock: %s, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.data._name,
                     order.executed.price,
                     order.executed.value,
                     order.executed.comm))
                self.buyprice[order.data._name] = order.executed.price
                self.buycomm[order.data._name] = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Stock: %s, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.data._name,
                          order.executed.price,
                          order.executed.value,
                          order.executed.comm))
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
            return

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' % (trade.pnl, trade.pnlcomm))

    def next(self):
        for data in self.datas:
        #入场
            if self.CrossoverHi[data._name] > 0 and self.buytime[data._name] == 0:
                newstake = self.broker.getvalue() * 0.01 / self.ATR[data._name]
                print("test position ATR %.2f" % self.ATR[data._name][0])
                print("test position CrossoverHi %d" % self.CrossoverHi[data._name][0])
                newstake = int(newstake/ 100) * 15
                self.sizer.p.stake = newstake
                self.buytime[data._name] = 1
                self.order[data._name] = self.buy(data = data)
        #加仓
            elif self.dataclose[data._name] >self.buyprice[data._name]+0.5*self.ATR[data._name] and self.buytime[data._name] > 0 and self.buytime[data._name] < 5:
                newstake = self.broker.getvalue() * 0.01 / self.ATR[data._name]
                newstake = int(newstake / 100) * 15
                self.sizer.p.stake = newstake
                self.order[data._name] = self.buy(data = data)
                self.buytime[data._name] = self.buytime[data._name] + 1
        #出场
            elif self.CrossoverLo[data._name] < 0 and self.buytime[data._name] > 0:
                self.order[data._name] = self.sell(data = data)
                self.buytime[data._name] = 0
                print("出场")
        #止损
            elif self.dataclose[data._name] < (self.buyprice[data._name] - 2*self.ATR[data._name]) and self.buytime[data._name] > 0:
                self.order[data._name] = self.sell(data = data)
                self.buytime[data._name] = 0
                print("止损")
            else:
                continue

    def stop(self):
        self.log('(MA Period %2d) Ending Value %.2f' % (self.params.maperiod, self.broker.getvalue()), doprint=True)
if __name__ == '__main__':
    stock_list = ['000001.SZ', '000002.SZ', '000063.SZ', '002024.SZ', '000166.SZ']
    # 创建主控制器
    cerebro = bt.Cerebro()
    # 加入策略
    cerebro.addstrategy(TestStrategy)
    # 准备股票日线数据，输入到backtrader
    for stock in stock_list:
        datapath = ('C:/quant_test/tushare/' + stock + '.csv')
        print('testorder %s' % stock)
        dataframe = pd.read_csv(datapath, index_col=0, parse_dates=True)
        #dataframe['openinterest'] = 0
        data = bt.feeds.PandasData(dataname=dataframe,
                                   fromdate=datetime.datetime(2019, 1, 1),
                                   todate=datetime.datetime(2019, 12, 31)
                                   )
        cerebro.adddata(data, name=stock)
    # broker设置资金、手续费
    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.001)
    # 设置买入策略
    cerebro.addsizer(TestSizer)
    cerebro.run()
    # 曲线绘图输出
    cerebro.plot()
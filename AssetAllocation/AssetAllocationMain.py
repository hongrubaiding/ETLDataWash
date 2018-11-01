# -- coding: utf-8 --

'''
    大类资产配研究，基于卖方研报的优化改进
'''

import pandas as pd
import numpy as np
from WindPy import w
from datetime import datetime
import AssetAllocation.IndexAllocation as IA
import matplotlib.pyplot as plt
import matplotlib

matplotlib.rcParams['font.sans-serif'] = ['SimHei']
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['axes.unicode_minus'] = False

class AssetAllocationMain:
    def __init__(self):
        self.assetIndex = self.getParam()
        self.startDate = '2006-01-01'
        self.endDate = '2017-06-01'  # datetime.today()
        '''equal_weight
        min_variance,
        risk_parity，
        max_diversification，
        mean_var,
        target_maxdown,
        target_risk
         '''
        self.method = 'target_maxdown'                         #大类资产配置模型

    def getParam(self):
        # 获取初始参数
        assetIndex = {}  # 大类资产指数
        assetIndex['000016.SH'] = u'上证50'
        assetIndex['000300.SH'] = u'沪深300'
        assetIndex['000905.SH'] = u'中证500'
        assetIndex['SPX.GI'] = u'标普500'
        assetIndex['CBA00601.CS'] = u'中债国债总财富指数'
        assetIndex['AU9999.SGE'] = u'黄金9999'
        return assetIndex

    def getHisData(self):
        # 本地或wind获取大类资产历史数据
        try:
            indexDataDf = pd.read_excel('indexDataDf.xlsx')
            print('本地读取indexDataDf')
            return indexDataDf
        except:
            print('wind读取indexDataDf')
            w.start()
            indexData = w.wsd(codes=list(self.assetIndex.keys()), fields=['close'], beginTime=self.startDate,
                              endTime=self.endDate)
            if indexData.ErrorCode != 0:
                print('wind获取指数数据失败，错误代码：', indexData.ErrorCode)
                return

            indexDataDf = pd.DataFrame(indexData.Data, index=indexData.Codes, columns=indexData.Times).T
            writer = pd.ExcelWriter('indexDataDf.xlsx')
            indexDataDf.to_excel(writer)
            writer.save()

    def calcAssetAllocation(self, indexDataDf):
        indexReturnDf = (indexDataDf - indexDataDf.shift(1)) / indexDataDf.shift(1)

        pofolioList= []         #组合业绩表现
        weightList = []         #组合各时间持仓
        for k in range(250,indexReturnDf.shape[0],21):
            datestr = datetime.strftime(indexReturnDf.index.tolist()[k], '%Y-%m-%d')
            print('回测时间：', datestr)
            tempReturnDF = indexReturnDf.iloc[k-250:k]
            weight = IA.get_smart_weight(tempReturnDF, method=self.method, wts_adjusted=False)
            tempPorfolio = (weight*indexReturnDf.iloc[k:k+21]).sum(axis=1)
            weight.name = datestr

            pofolioList.append(tempPorfolio)
            weightList.append(weight)
        totalPofolio =pd.concat(pofolioList,axis=0)
        totalPofolio.name = 'portfolio'
        weightDf = pd.concat(weightList,axis=1)

        fig = plt.figure(figsize=(16,12))
        ax1 = fig.add_subplot(211)
        weightDf = weightDf.T

        color = ['r', 'g', 'b', 'y', 'k', 'c',]
        for i in range(weightDf.shape[1]):
            ax1.bar(weightDf.index.tolist(), weightDf.ix[:, i], color=color[i], bottom=weightDf.ix[:, :i].sum(axis=1))

        labels = [self.assetIndex[code] for code in weightDf.columns.tolist()]
        ax1.legend(labels=labels, loc='best')
        for tick in ax1.get_xticklabels():
            tick.set_rotation(90)
        ax2 = fig.add_subplot(212)

        aa = pd.concat([totalPofolio,indexReturnDf['000300.SH']],axis=1,join='inner')
        self.calcRiskReturn(aa)
        # totalPofolioAccReturn.plot(ax=ax2)
        (1+aa).cumprod().plot(ax=ax2)
        plt.title(self.method)
        plt.savefig('C:\\Users\\lenovo\\Desktop\\大类资产配置走势图\\'+self.method)
        # plt.show()

    def calcRiskReturn(self,tempDf):
        dicResult = {}
        assetAnnualReturn = tempDf.mean()*250
        assetStd = tempDf.std()*np.sqrt(250)

        def MaxDrawdown(return_list):
            '''最大回撤率'''
            return_list = (return_list + 1).cumprod()
            return_list = return_list.values
            i = np.argmax(np.maximum.accumulate(return_list) - return_list)
            if i == 0:
                return 0
            j = np.argmax(return_list[:i])
            result = (return_list[j] - return_list[i]) / return_list[j]
            return result
        assetMaxDown = tempDf.dropna().apply(MaxDrawdown)
        assetCalmar = assetAnnualReturn/assetMaxDown
        assetSharp = (assetAnnualReturn)/assetStd
        def formatData(tempSe,flagP = True):
            tempDic = tempSe.to_dict()
            if flagP:
                # for key,value in tempDic.items():
                #     aa = round(value,4)
                #     bb = aa*100
                #     aaaa = round(bb,4)
                #     cc = str(bb)+'%'
                result = {key:str(round(round(value,4)*100,2))+'%' for key,value in tempDic.items()}
            else:
                result = {key: round(value, 2) for key, value in tempDic.items()}
            return result

        dicResult[u'年化收益'] = formatData(assetAnnualReturn)
        dicResult[u'年化波动'] = formatData(assetStd)
        dicResult[u'最大回撤'] = formatData(assetMaxDown)
        dicResult[u'夏普比率'] = formatData(assetSharp,flagP=False)
        dicResult[u'卡玛比率'] = formatData(assetCalmar,flagP=False)
        df = pd.DataFrame(dicResult).T
        df.rename(columns={'000300.SH':u'沪深300','portfolio':u'投资组合'},inplace=True)
        df.to_excel('C:\\Users\\lenovo\\Desktop\\大类资产配置结果\\'+self.method+'.xls')


    def plotFigure(self):
        pass


    def calcMain(self):
        #主函数入口
        indexDataDf = self.getHisData()

        #组合业绩回测
        self.calcAssetAllocation(indexDataDf)


if __name__ == '__main__':
    AssetAllocationDemo = AssetAllocationMain()
    AssetAllocationDemo.calcMain()
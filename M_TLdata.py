# -*- coding: utf-8 -*-
#2016年开始有数据
#需要做修正
#截面调用
#下载通联数据
'''
t = pd.date_range('2016-08-11','2021-08-11').tolist()
    t = [str(i)[:10].replace('-','') for i in t]
    elist = []    
    X = []
    for sub_t in tqdm(t):
        fn = os.path.join(data_dir,'%s.csv' % sub_t)
        if not os.path.exists(fn):
            try:
        		#方式1，直接调取数据，不做任何处理
                url1 = 'https://api.datayes.com/data/v1//api/alternative/getIndRotaFactors.json?field=&industryname=&periodDate=%s&beginDate=&endDate=' % (sub_t)
                code, result = client.getData(url1)#调用getData函数获取数据，数据以字符串的形式返回
                if code==200:
                    if eval(result)['retCode']==1:
                        pd_data=pd.DataFrame(eval(result)['data'])
                        #pd_data.to_csv(fn)
                        X.append(pd_data)
                else:
                    print (code)
                    print (result)
            except:
                elist.append(sub_t)

'''

from tqdm import tqdm
import pandas as pd
from dataapi_win36 import Client
import os
from yq_toolsS45 import get_symbol_A,engine



data_dir = 'S80_data_dir_sec'
if not os.path.exists(data_dir):
    os.mkdir(data_dir)
    
tickers =get_symbol_A()
tickers = [i for i in tickers if i[0] in ['0','3','6']]
    
client = Client()
client.init('80a07af514496f7d1e0c5d20608924f9e20e8976864f96271aebe374f49e46eb')


def tref_split(tref,r=20):
    t0_1=[]
    tt_1=[]
    i=0    
    T = len(tref)
    while i <=T-1:
        j=i+r-1
        if j>T-1:
            j=T-1
        if i>T-1:
            i=T-1
        t0_1.append(tref[i])
        tt_1.append(tref[j])
        i=i+r       
    return t0_1,tt_1

def list_connect(tref,num=3):
    x =[]
    while len(tref)>0:
        tmp = tref[:num]
        x.append(','.join(tmp))
        tref = tref[num:]
    return x

#行业底层因子表
def get_getIndRotaFactors_his():
    indu_info = ['交通运输', '休闲服务', '传媒', '公用事业', '农林牧渔', '化工',
         '医药生物', '商业贸易', '国防军工', '家用电器', '建筑材料', '建筑装饰', '房地产',
         '有色金属', '机械设备', '汽车', '电子', '电气设备', '纺织服装', '综合', '计算机',
         '轻工制造', '通信', '采掘', '钢铁', '银行', '非银金融', '食品饮料']
    elist = []    
    X = []
    for sub_t in tqdm(indu_info):
        try:
    		#方式1，直接调取数据，不做任何处理
            url1 = '''https://api.datayes.com/data/v1//api/alternative/getIndRotaFactors.json?field=&industryname=%s&periodDate=&beginDate=&endDate=''' % (sub_t)
            code, result = client.getData(url1)#调用getData函数获取数据，数据以字符串的形式返回
            if code==200:
                if eval(result)['retCode']==1:
                    pd_data=pd.DataFrame(eval(result)['data'])
                    #pd_data.to_csv(fn)
                    X.append(pd_data)
            else:
                print (code)
                print (result)
        except:
            elist.append(sub_t)
    X=pd.concat(X)
    X.to_csv('getIndRotaFactors.csv')
#行业合成因子表 最近5年
def get_getIndRotaComfactor_his():
    indu_info = ['交通运输', '休闲服务', '传媒', '公用事业', '农林牧渔', '化工',
         '医药生物', '商业贸易', '国防军工', '家用电器', '建筑材料', '建筑装饰', '房地产',
         '有色金属', '机械设备', '汽车', '电子', '电气设备', '纺织服装', '综合', '计算机',
         '轻工制造', '通信', '采掘', '钢铁', '银行', '非银金融', '食品饮料']
    elist = []    
    X = []
    for sub_t in tqdm(indu_info):
        try:
    		#方式1，直接调取数据，不做任何处理
            url1 = '''https://api.datayes.com/data/v1//api/alternative/getIndRotaComfactor.json?field=&industryname=%s&periodDate=&beginDate=&endDate=''' % (sub_t)
            code, result = client.getData(url1)#调用getData函数获取数据，数据以字符串的形式返回
            if code==200:
                if eval(result)['retCode']==1:
                    pd_data=pd.DataFrame(eval(result)['data'])
                    #pd_data.to_csv(fn)
                    X.append(pd_data)
            else:
                print (code)
                print (result)
        except:
            elist.append(sub_t)
    X=pd.concat(X)
    X.to_csv('getIndRotaComfactor.csv')
#A股公司专利数据
def getASharePatents_his():
    elist = []    
    X = []
    for sub_t in tqdm(tickers):
        try:
    		#方式1，直接调取数据，不做任何处理
            url1 = 'https://api.datayes.com/data/v1//api/alternative/getASharePatents.json?field=&beginDate=&endDate=&ticker=%s&secID=' % (sub_t)
            code, result = client.getData(url1)#调用getData函数获取数据，数据以字符串的形式返回
            if code==200:
                if eval(result)['retCode']==1:
                    pd_data=pd.DataFrame(eval(result)['data'])
                    #pd_data.to_csv(fn)
                    X.append(pd_data)
            else:
                print (code)
                print (result)
        except:
            elist.append(sub_t)
    X=pd.concat(X)
    X.to_csv('getASharePatents_his.csv')
#A股公司及子公司专利数据
def getASharePatents1_his():
    elist = []    
    X = []
    tickers1 = list_connect(tickers,10)
    for sub_t in tqdm(tickers1):
        try:
    		#方式1，直接调取数据，不做任何处理
            url1 = 'https://api.datayes.com/data/v1//api/alternative/getASharePatents1.json?field=&beginDate=&endDate=&ticker=%s&secID=' % (sub_t)
            code, result = client.getData(url1)#调用getData函数获取数据，数据以字符串的形式返回
            if code==200:
                if eval(result)['retCode']==1:
                    pd_data=pd.DataFrame(eval(result)['data'])
                    #pd_data.to_csv(fn)
                    X.append(pd_data)
            else:
                print (code)
                print (result)
        except:
            elist.append(sub_t)
    X=pd.concat(X)
    X.to_csv('getASharePatents1_his.csv')

#分行业招聘数据统计表
def getIndustryRecruStats_his():
    t = pd.date_range('2017-01-01','2021-08-11').tolist()
    t = [str(i)[:10].replace('-','') for i in t]
    t1,t2 = tref_split(t,30)
    elist = []    
    X = []
    for sub_t1,sub_t2 in tqdm(zip(t1,t2)):
        try:
    		#方式1，直接调取数据，不做任何处理
            url1 = 'https://api.datayes.com/data/v1//api/alternative/getIndustryRecruStats.json?field=&industryName=&beginDate=%s&endDate=%s' % (sub_t1,sub_t2)
            code, result = client.getData(url1)#调用getData函数获取数据，数据以字符串的形式返回
            if code==200:
                if eval(result)['retCode']==1:
                    pd_data=pd.DataFrame(eval(result)['data'])
                    #pd_data.to_csv(fn)
                    X.append(pd_data)
            else:
                print (code)
                print (result)
        except:
            elist.append(sub_t1)
    X=pd.concat(X)
    X.to_csv('getIndustryRecruStats_his.csv')

#活跃招聘链接数统计表
def getRecruitmentActiveUrlNum():
    t = pd.date_range('2019-02-28','2021-08-11').tolist()
    t = [str(i)[:10].replace('-','') for i in t]
    t1,t2 = tref_split(t,90)
    elist = []    
    X = []
    for sub_t1,sub_t2 in tqdm(zip(t1,t2)):
        try:
    		#方式1，直接调取数据，不做任何处理
            url1 = 'https://api.datayes.com/data/v1//api/alternative/getRecruitmentActiveUrlNum.json?field=&beginDate=%s&endDate=%s' % (sub_t1,sub_t2)
            code, result = client.getData(url1)#调用getData函数获取数据，数据以字符串的形式返回
            if code==200:
                if eval(result)['retCode']==1:
                    pd_data=pd.DataFrame(eval(result)['data'])
                    #pd_data.to_csv(fn)
                    X.append(pd_data)
            else:
                print (code)
                print (result)
        except:
            elist.append(sub_t1)
    X=pd.concat(X)
    X.to_csv('getRecruitmentActiveUrlNum.csv')
#上市公司招聘数据统计表
def getListcompanyRecruitmentStats_his():
    t = pd.date_range('2017-01-01','2021-08-11').tolist()
    t = [str(i)[:10].replace('-','') for i in t]
    t1,t2 = tref_split(t,20)
    elist = []    
    X = []
    for sub_t1,sub_t2 in tqdm(zip(t1,t2)):
        try:
    		#方式1，直接调取数据，不做任何处理
            url1 = 'https://api.datayes.com/data/v1//api/alternative/getListcompanyRecruitmentStats.json?field=&city=&tickerSymbol=&beginDate=%s&endDate=%s' % (sub_t1,sub_t2)
            code, result = client.getData(url1)#调用getData函数获取数据，数据以字符串的形式返回
            if code==200:
                if eval(result)['retCode']==1:
                    pd_data=pd.DataFrame(eval(result)['data'])
                    #pd_data.to_csv(fn)
                    X.append(pd_data)
            else:
                print (code)
                print (result)
        except:
            elist.append(sub_t1)
    X=pd.concat(X)
    X.to_csv('getListcompanyRecruitmentStats_his.csv')
#招聘衍生数据汇总表
def getRecruitmentAllStats_his():
    t = pd.date_range('2017-01-01','2021-08-11').tolist()
    t = [str(i)[:10].replace('-','') for i in t]
    t1,t2 = tref_split(t,10)
    elist = []    
    X = []
    for sub_t1,sub_t2 in tqdm(zip(t1,t2)):
        try:
    		#方式1，直接调取数据，不做任何处理
            url1 = 'https://api.datayes.com/data/v1//api/alternative/getRecruitmentAllStats.json?field=&&beginDate=%s&endDate=%s' % (sub_t1,sub_t2)
            code, result = client.getData(url1)#调用getData函数获取数据，数据以字符串的形式返回
            if code==200:
                if eval(result)['retCode']==1:
                    pd_data=pd.DataFrame(eval(result)['data'])
                    #pd_data.to_csv(fn)
                    X.append(pd_data)
            else:
                print (code)
                print (result)
        except:
            elist.append(sub_t1)
    X=pd.concat(X)
    X.to_csv('getRecruitmentAllStats_his.csv')        
#线上电商数据衍生表
def getElecBusinessDeri():
    t = pd.date_range('2017-01-31','2021-08-11').tolist()
    t = [str(i)[:10].replace('-','') for i in t]
    t1,t2 = tref_split(t,10)
    elist = []    
    X = []
    for sub_t1,sub_t2 in tqdm(zip(t1,t2)):
        try:
    		#方式1，直接调取数据，不做任何处理
            url1 = '/api/alternative/getElecBusinessDeri.json?field=&secID=&ticker=&platform=&brand=&beginDate=%s&endDate=%s' % (sub_t1,sub_t2)
            code, result = client.getData(url1)#调用getData函数获取数据，数据以字符串的形式返回
            if code==200:
                if eval(result)['retCode']==1:
                    pd_data=pd.DataFrame(eval(result)['data'])
                    #pd_data.to_csv(fn)
                    X.append(pd_data)
            else:
                print (code)
                print (result)
        except:
            elist.append(sub_t1)
    X=pd.concat(X)
    X.to_csv('getElecBusinessDeri.csv')      
#超预期事件   Need Privilege 没有权限
def getEventSurprise():
    t = pd.date_range('2011-01-04','2021-08-11').tolist()
    t = [str(i)[:10].replace('-','') for i in t]
    t1,t2 = tref_split(t,20)
    elist = []    
    X = []
    for sub_t1,sub_t2 in tqdm(zip(t1,t2)):
        try:
    		#方式1，直接调取数据，不做任何处理
            url1 = 'https://api.datayes.com/data/v1//api/event/getEventSurprise.json?field=&endDateRep=&initID=&noticeType=&noticeTypeComb=&publishDate=&ticker=&traBegDate=%s&traEndDate=%s' % (sub_t1,sub_t2)
            code, result = client.getData(url1)#调用getData函数获取数据，数据以字符串的形式返回
            if code==200:
                if eval(result)['retCode']==1:
                    pd_data=pd.DataFrame(eval(result)['data'])
                    #pd_data.to_csv(fn)
                    X.append(pd_data)
            else:
                print (code)
                print (result)
        except:
            elist.append(sub_t1)
    X=pd.concat(X)
    X.to_csv('getEventSurprise.csv')      
#限售股解禁事件 无权限
def getEventShareFloat():
    t = pd.date_range('2011-01-04','2021-08-11').tolist()
    t = [str(i)[:10].replace('-','') for i in t]
    t1,t2 = tref_split(t,20)
    elist = []    
    X = []
    for sub_t1,sub_t2 in tqdm(zip(t1,t2)):
        try:
    		#方式1，直接调取数据，不做任何处理
            url1 = 'https://api.datayes.com/data/v1//api/event/getEventShareFloat.json?field=&floatBegDate=&floatEndDate=&groupIdType=&initID=&predGroup=&publishDate=&ticker=&traBegDate=%s&traEndDate=%s' % (sub_t1,sub_t2)
            code, result = client.getData(url1)#调用getData函数获取数据，数据以字符串的形式返回
            if code==200:
                if eval(result)['retCode']==1:
                    pd_data=pd.DataFrame(eval(result)['data'])
                    #pd_data.to_csv(fn)
                    X.append(pd_data)
            else:
                print (code)
                print (result)
        except:
            elist.append(sub_t1)
    X=pd.concat(X)
    X.to_csv('getEventShareFloat.csv')  

#事件数据表 无权限
def getEventData():
    t = pd.date_range('2011-01-04','2021-08-11').tolist()
    t = [str(i)[:10].replace('-','') for i in t]
    t1,t2 = tref_split(t,20)
    elist = []    
    X = []
    for sub_t1,sub_t2 in tqdm(zip(t1,t2)):
        try:
    		#方式1，直接调取数据，不做任何处理
            url1 = 'https://api.datayes.com/data/v1//api/event/getEventData.json?field=&beginDate=%s&endDate=%s&endWindow=&eventID=&initID=&startWindow=&status=' % (sub_t1,sub_t2)
            code, result = client.getData(url1)#调用getData函数获取数据，数据以字符串的形式返回
            if code==200:
                if eval(result)['retCode']==1:
                    pd_data=pd.DataFrame(eval(result)['data'])
                    #pd_data.to_csv(fn)
                    X.append(pd_data)
            else:
                print (code)
                print (result)
        except:
            elist.append(sub_t1)
    X=pd.concat(X)
    X.to_csv('getEventData.csv')  

#getPartyID 公司基本信息 并保存
def getPartyID():
    sql_tmp = 'select distinct(secShortName) from equget'
    tick_name = pd.read_sql(sql_tmp,engine)
    tick_name = tick_name.secShortName.tolist()
    url0 = 'https://api.datayes.com/data/v1//api/master/getPartyID.json?field=&partyName=%s'
    X = []
    elist=[]
    for sub_t in tqdm(tick_name):
        url1 = url0 % sub_t
        try:
            code, result = client.getData(url1)#调用getData函数获取数据，数据以字符串的形式返回
            if code==200:
                if eval(result)['retCode']==1:
                    pd_data=pd.DataFrame(eval(result)['data'])
                    #pd_data.to_csv(fn)
                    X.append(pd_data)
            else:
                print (code)
                print (result)
        except:
            elist.append(sub_t)
    X=pd.concat(X)
    X.to_csv('getPartyID.csv') 
    
#事件描述表  无权限
#验证名为问题，确实是数据很少，占用了太多调用次数，单个和合并下载到数据相同
def getEventDesc():
    id_info = pd.read_pickle('getPartyID.pkl')
    id_info = id_info.partyID.astype(str).unique().tolist()
    id_info = list_connect(id_info,10)
    url0 = 'https://api.datayes.com/data/v1//api/event/getEventDesc.json?field=&eventID=&isFactor=&eventIDParent=%s&eventNameCN=&eventNameEN=&eventType='
    X = []
    elist=[]
    for sub_t in tqdm(id_info):
        url1 = url0 % sub_t
        try:
            code, result = client.getData(url1)#调用getData函数获取数据，数据以字符串的形式返回
            if code==200:
                if eval(result)['retCode']==1:
                    pd_data=pd.DataFrame(eval(result)['data'])
                    #pd_data.to_csv(fn)
                    X.append(pd_data)
            else:
                print (code)
                print (result)
        except:
            elist.append(sub_t)
    X=pd.concat(X)
    X.to_csv('getEventDesc.csv') 
   
#事件收益表  很特殊，无法基于常规方法获取 https://apidoc.datayes.com/app/APIDetail/3760  无权限
def getEventWinReturn():
    id_info = pd.read_pickle('getPartyID.pkl')
    id_info = id_info.partyID.astype(str).unique().tolist()
    id_info = list_connect(id_info,30)
    #url0 = 'https://api.datayes.com/data/v1//api/event/getEventDesc.json?field=&eventID=&isFactor=&eventIDParent=%s&eventNameCN=&eventNameEN=&eventType='
    url0 = 'https://api.datayes.com/data/v1//api/event/getEventWinReturn.json?field=&eventID=%s&holdingDays=&rtnType=&status=&year=ALL'
    X = []
    elist=[]
    for sub_t in tqdm(id_info):
        url1 = url0 % sub_t
        try:
            code, result = client.getData(url1)#调用getData函数获取数据，数据以字符串的形式返回
            if code==200:
                if eval(result)['retCode']==1:
                    pd_data=pd.DataFrame(eval(result)['data'])
                    #pd_data.to_csv(fn)
                    X.append(pd_data)
            else:
                print (code)
                print (result)
        except:
            elist.append(sub_t)
    X=pd.concat(X)
    X.to_csv('getEventWinReturn.csv')

#接口名getSingleCompanyProduct 接口中文名查询单个上市公司或产品的相关属性 无权限
#接口名getProductIndicData 接口中文名查询产品对应的指标数据 无权限
#接口名getCompanyProductRelation 接口中文名获取公司-产品的树形连接关系 无权限
#接口名getCompanyIndicData 接口中文名查询公司对应的指标数据 无权限
#接口名getSingleIndustryChain 接口中文名查询产品的产业链 无权限
#接口名getProductCompanyRelation 接口中文名获取产品-公司的树形连接关系 无权限


        
    
if __name__ == "__main__":
    #验证名为问题，确实是数据很少，占用了太多调用次数，单个和合并下载到数据相同
    id_info = pd.read_pickle('getPartyID.pkl')
    id_info = id_info.partyID.astype(str).unique().tolist()
    id_info = list_connect(id_info,30)
    #url0 = 'https://api.datayes.com/data/v1//api/event/getEventDesc.json?field=&eventID=&isFactor=&eventIDParent=%s&eventNameCN=&eventNameEN=&eventType='
    url0 = 'https://api.datayes.com/data/v1//api/event/getEventWinReturn.json?field=&eventID=%s&holdingDays=&rtnType=&status=&year=ALL'
    X = []
    elist=[]
    for sub_t in tqdm(id_info):
        url1 = url0 % sub_t
        try:
            code, result = client.getData(url1)#调用getData函数获取数据，数据以字符串的形式返回
            if code==200:
                if eval(result)['retCode']==1:
                    pd_data=pd.DataFrame(eval(result)['data'])
                    #pd_data.to_csv(fn)
                    X.append(pd_data)
            else:
                print (code)
                print (result)
        except:
            elist.append(sub_t)
    X=pd.concat(X)
    X.to_csv('getEventWinReturn.csv')  
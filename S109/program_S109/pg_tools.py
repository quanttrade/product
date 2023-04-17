# -*- coding: utf-8 -*-
"""
Created on Sun Jun 14 15:38:07 2020

@author: adair2019
"""

#import json
import os
from sqlalchemy import create_engine
import pandas as pd
import psycopg2
import time
import json

tt = time.strftime("%Y%m%d", time.localtime())

#must be set before using

with open('para.json','r',encoding='utf-8') as f:
    para = json.load(f)
    
#pn = para['yuqerdata_dir']
#user_name = para['mysql_para']['user_name']
pass_wd = para['mysql_para']['pass_wd']
#port = para['mysql_para']['port']
user_name = 'postgres'
#pass_wd = 'liudehua'
port = 5432
#host = '192.168.2.111'
host = 'localhost'
def create_db(db_name,host=host):
    engine = create_engine('postgresql+psycopg2://postgres:%s@%s/%s' % (pass_wd,host,db_name))
    return engine


db_name1 = 'yuqerdata'
engine = create_db(db_name1)

db_name3 = 'S26'
engineS26 = create_db(db_name3)

db_name_gta_web = 'gta_web'
engine_gtaweb = create_db(db_name_gta_web)

db_name_yq_datacub1 = 'yuqer_cubdata'
engine_yq_datacub1 = create_db(db_name_yq_datacub1)

engine_yq_S19factors = create_db('factors_com')
engine_tdx =create_db('pytdx_data')
engine_akshare =create_db('aksharedata')
engine_futuredata = create_db('futuredata')
eg_plg = create_db('polygon')


def get_file_name(file_dir,file_type):
    L=[]
    L_s = []   
    for root, dirs, files in os.walk(file_dir):  
        for file in files:  
            if os.path.splitext(file)[1] == file_type:  
                L.append(os.path.join(root, file))  
                L_s.append(file)
    return L,L_s

def add_0(x):
    if isinstance(x,int):
        x= '%0.6d' % x
    else:
        x=x.rjust(6,'0')
    return x

#added on 2020/3/28 S19
def remove_datacube_attr(x):
    x=x[0:6]
    return x

def read_yuqer_datacube_data(fn):
    x = pd.read_csv(fn,index_col=0)
    x = x.stack().reset_index()
    x.rename(columns={x.columns[0]:'tradingdate',x.columns[1]:'symbol',x.columns[2]:'f_val'},inplace=True)
    x['symbol'] = x['symbol'].apply(remove_datacube_attr)
    _,sub_fn = os.path.split(fn)
    info = sub_fn.split('.')
    info=info[0]
    return x,info

def create_table(db_name,tn_name,var_name,var_type,key_str):
    db_name = db_name.lower()
    tn_name = tn_name.lower()
    #check 
    x=pd.read_sql('select datname from pg_database;',engine)
    x= x[x.columns[0]].tolist()
    x1=[]
    for sub_x in x:
        x1.append(sub_x.lower())
    if not db_name.lower() in x1:
        do_sql_order('CREATE DATABASE %s;' % db_name,'yuqerdata')
    #连接本地数据库
    #db = pymysql.connect("localhost",user_name,pass_wd,db_name)
    db = psycopg2.connect(database=db_name,user="postgres",password=pass_wd,host="localhost",port="5432")
    #创建游标
    cursor = db.cursor()
    #创建
    var_info=''
    for id,sub_var in enumerate(var_name):
        var_info=var_info + sub_var + ' ' + var_type[id] + ','
    var_info = var_info[:-1]    
    if len(key_str)>0:
        sql = 'CREATE TABLE  "%s"(%s,primary key(%s));' % (tn_name,var_info,key_str)    
    else:
        sql = 'CREATE TABLE  "%s"(%s);' % (tn_name,var_info)  

    try:
        # 执行SQL语句
        cursor.execute(sql)
        print("创建数据库成功")
    except Exception as e:
        print("创建数据库失败：case%s"%e)
    finally:
        #关闭游标连接
        cursor.close()
        # 关闭数据库连接
        db.close()


def create_table2023(db_name,tn_name,var_name,var_type,key_str=[]):
    #连接本地数据库
    db = psycopg2.connect(database=db_name,user="postgres",password=pass_wd,host="localhost",port="5432")
    #创建游标
    cursor = db.cursor()
    #创建
    var_info=''
    for id,sub_var in enumerate(var_name):
        var_info=var_info + sub_var + ' ' + var_type[id] + ','
    var_info = var_info[:-1]    
    if len(key_str)>0:
        sql = 'CREATE TABLE  "%s"(%s,primary key(%s));' % (tn_name,var_info,key_str)    
    else:
        sql = 'CREATE TABLE  "%s"(%s);' % (tn_name,var_info)  

    try:
        # 执行SQL语句
        cursor.execute(sql)
        db.commit()
        print("创建数据库成功")
    except Exception as e:
        print("创建数据库失败：case%s"%e)
    finally:
        #关闭游标连接
        cursor.close()
        # 关闭数据库连接
        db.close()

        
def do_sql_order(order_str,db_name):
    #db = pymysql.connect("localhost",user_name,pass_wd,db_name)
    db = psycopg2.connect(database=db_name,user="postgres",password=pass_wd,host="localhost",port="5432")
    #创建游标
    cursor = db.cursor()
    try:
        # 执行SQL语句
        cursor.execute(order_str)
        db.commit()
        db.close()
        print("执行postgresql命令成功")
    except Exception as e:
        print("执行postgresql命令失败：case%s"%e)
        print(order_str)
    finally:
        #关闭游标连接
        cursor.close()
        # 关闭数据库连接
        db.close()
        
        
def get_table_names(eg):
    sql_tmp = '''SELECT tablename, schemaname, tableowner
    FROM pg_catalog.pg_tables
    WHERE schemaname != 'pg_catalog'
    AND schemaname != 'information_schema'
    ORDER BY tablename ASC;'''
    tns = pd.read_sql(sql_tmp,eg)
    tns = tns.tablename.tolist()  
    return tns

def get_us_daytick(ticker,t0,tt):
    sql_str = '''select * from usastock_day where ticker = '%s' 
        and "tradeDate">='%s' and "tradeDate"<='%s' order by "tradeDate"'''
    x = pd.read_sql(sql_str % (ticker,t0,tt),eg_plg)
    return x
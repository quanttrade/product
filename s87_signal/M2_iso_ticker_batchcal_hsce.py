# -*- coding: utf-8 -*-
"""
Created on Mon Nov 22 09:43:49 2021

@author: adair-9960
"""

import os
import multiprocessing
num_core = int(multiprocessing.cpu_count())
N=100
#N=1

def get_file_name(file_dir,file_type):
    L=[]
    L_s = []
    for root, dirs, files in os.walk(file_dir):
        for file in files:
            if os.path.splitext(file)[1] == file_type:
                L.append(os.path.join(root, file))
                L_s.append(file)
    return L,L_s


#num_core = 50
def run_single(info):
    sub_p1,sub_p2,sub_p3 = info
    try:
        os.system('python M1_deap_iso_single_ticker.py %s %s %s' % (sub_p1,sub_p2,sub_p3))
    except:
        print(sub_p1)




if __name__ == "__main__":

    index_code = 'hsce'
    pn0 = 'pklresult_%s' % index_code
    if not os.path.exists(pn0):
        os.mkdir(pn0)

    _,L_s = get_file_name('csv_%s' % index_code,'.csv')
    L_s = [i for i in L_s if i.__contains__(index_code)]

    tickers = [i.replace(index_code+'-','')[:-4] for i in L_s]

    #tickers = tickers[:1]

    p1 = []
    p2 =[]
    p3 = []
    for sub_ticker in tickers:
        for i in range(N):
            p1.append(index_code)
            p2.append(sub_ticker)
            p3.append('%0.3d' % i)


    if num_core>len(p1):
        num_core = len(p1)

    pool = multiprocessing.Pool(num_core)
    pool.map(run_single,zip(p1,p2,p3))
    pool.close()
    pool.join()


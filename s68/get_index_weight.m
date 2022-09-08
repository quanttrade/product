function sub_symbol_pool = get_index_weight(t,index_pool)
    sql_str3 = ['select symbol,weight from yuqerdata.IdxCloseWeightGet ',...
            'where tradingdate = ''%s'' and ticker = ''%s'''];
    sql_str1= ['select tradingdate from yuqerdata.IdxCloseWeightGet ',...
            'where tradingdate < ''%s'' and ticker = ''%s'' order by tradingdate desc limit 1'];
    sub_t = fetchmysql(sprintf(sql_str1,t,index_pool),2);
    sub_symbol_pool = fetchmysql(sprintf(sql_str3,sub_t{1},index_pool),2);
end
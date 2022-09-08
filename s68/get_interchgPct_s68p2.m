function [sub_r,sub_t_u,sub_symbol_u] = get_interchgPct_s68p2(sub_t1,sub_t2,sub_symbol)
    sub_symbol_u = sub_symbol;
    sub_symbol = sprintf('"%s"',strjoin(sub_symbol,'","'));
    sql_str = ['select symbol,tradeDate,closePrice/preClosePrice-1 from yuqerdata.yq_dayprice ',...
        'where tradeDate > ''%s'' and tradeDate <=''%s'' and symbol in (%s) and chgPct is not null order by tradeDate'];
    sub_x = fetchmysql(sprintf(sql_str,sub_t1,sub_t2,sub_symbol),2);
    
    %[~,ia] = intersect(sub_x(:,1),sub_symbol_pool(:,1));
    %sub_x = sub_x(ia,:);
       
    %ÖØ×é
    
    sub_t_u = unique(sub_x(:,2));
    T_sub_t_u = length(sub_t_u);
    T_sub_symbol = length(sub_symbol_u);
    sub_r = zeros(T_sub_symbol,T_sub_t_u);
    for j = 1:T_sub_t_u
        sub_sub_x = sub_x(strcmp(sub_x(:,2),sub_t_u(j)),[1,3]);
        [~,ia,ib] = intersect(sub_symbol_u,sub_sub_x(:,1));
        sub_r(ia,j) = cell2mat(sub_sub_x(ib,2));
    end
end
function [sub_r,sub_t_u,sub_symbol_u] = get_interchgPct_US(sub_t1,sub_t2,sub_symbol)
    if nargin < 3
        sub_symbol = [];
    end
%     sql_str = ['select symbol,tradeDate,chgPct from yuqerdata.yq_dayprice ',...
%         'where tradeDate >= ''%s'' and tradeDate <=''%s'' and chgPct is not null order by tradeDate'];
    if isempty(sub_symbol)
        sql_str = ['select symbol,tradingdate,closeprice_adj from us_stock.us_stock_daytick ',...
            'where tradingdate >= ''%s'' and tradingdate <=''%s'' order by tradingdate'];
        sub_x = fetchmysql(sprintf(sql_str,sub_t1,sub_t2),2);
    else
        sub_symbol = sprintf('"%s"',strjoin(sub_symbol,'","'));
        sql_str = ['select symbol,tradingdate,closeprice_adj from us_stock.us_stock_daytick ',...
            'where tradingdate >= ''%s'' and tradingdate <=''%s'' and symbol in (%s) order by tradingdate'];
        sub_x = fetchmysql(sprintf(sql_str,sub_t1,sub_t2,sub_symbol),2);
    end
    %ÖØ×é
    sub_t_u = unique(sub_x(:,2));
    sub_symbol_u = unique(sub_x(:,1));
    T_sub_t_u = length(sub_t_u);
    T_sub_symbol = length(sub_symbol_u);
    sub_p = nan(T_sub_symbol,T_sub_t_u);
    for j = 1:T_sub_t_u
        sub_sub_x = sub_x(strcmp(sub_x(:,2),sub_t_u(j)),[1,3]);
        [~,ia,ib] = intersect(sub_symbol_u,sub_sub_x(:,1));
        sub_p(ia,j) = cell2mat(sub_sub_x(ib,2));
    end
    
    sub_p = sub_p';
    sub_p = fillmissing(sub_p,'previous');
    sub_r = zeros(size(sub_p));
    sub_r(2:end,:) = sub_p(2:end,:) ./sub_p(1:end-1,:)-1;
    sub_r = fillmissing(sub_r,'constant',0)';
    
end
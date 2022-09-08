function [sub_r,sub_t_u,sub_symbol_u] = get_interchgPct_ISO(sub_t1,sub_t2,index_id,sub_symbol)
    if nargin < 4
        sub_symbol=[];
    end
    
    index0_pool = {'as51','hsce','hsi','topix','twse','kosdaq', 'kospi',... 
                'msci', 'ndx', 'nifty', 'nky', 'RTY', 'set50', 'sx5e','ukx', 'xin9i'};
    tmp = {'AS51','HSCEI','HSI','TPX','TWSE','KOSDAQ','KOSPI2','TAMSCI','NDX',...
        'NIFTY','NKY','RTY','SET50','SX5E','UKX','XIN9I'};
    index0_pool2 =containers.Map(index0_pool,tmp);
    if isempty(sub_symbol)
        sql_str = ['select ticker,tradeDate,closePrice from data_pro.main_index_s68 ',...
            'where index_id = "%s" and ticker!="%s" and tradeDate >= ''%s'' and tradeDate <=''%s'' order by tradeDate'];
        sub_x = fetchmysql(sprintf(sql_str,index_id,index0_pool2(index_id),sub_t1,sub_t2),2);
    else
        sub_symbol = sprintf('"%s"',strjoin(sub_symbol,'","'));
        sql_str = ['select ticker,tradeDate,closePrice from data_pro.main_index_s68 ',...
            'where index_id = "%s" and tradeDate >= ''%s'' and tradeDate <=''%s'' and ticker in (%s) order by tradeDate'];
        sub_x = fetchmysql(sprintf(sql_str,index_id,sub_t1,sub_t2,sub_symbol),2);
    end
       
    %重组
    sub_t_u = unique(sub_x(:,2));
    %特殊符号清除
    sub_x(:,1) = cellfun(@(x) replace(x,'/','_'),sub_x(:,1),'UniformOutput',false);
    sub_x(:,1) = cellfun(@(x) replace(x,'-','_'),sub_x(:,1),'UniformOutput',false);
    
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
    sub_r(isinf(sub_r)) = 0;    
end
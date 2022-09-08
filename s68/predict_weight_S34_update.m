function [wp,sub_symbol_pool] = predict_weight_S34_update(tref,window,index_pool,index_num)
    sql_str = 'select symbol,chgPct from yuqerdata.yq_dayprice where tradeDate = ''%s'' and chgPct is not null ';
    sql_str2 = ['select tradingdate from yuqerdata.IdxCloseWeightGet ',...
                'where tradingdate >= ''%s'' and ticker = ''%s''  order by tradingdate limit 1'];
    sql_str3 = ['select symbol,weight from yuqerdata.IdxCloseWeightGet ',...
            'where tradingdate = ''%s'' and ticker = ''%s'''];
    sql_str1= ['select tradingdate from yuqerdata.IdxCloseWeightGet ',...
            'where tradingdate < ''%s'' and ticker = ''%s'' order by tradingdate desc limit 1'];
    sub_t = fetchmysql(sprintf(sql_str1,tref{end},index_pool),2);
    if isempty(sub_t)
        sub_t = fetchmysql(sprintf(sql_str2,tref{1},index_pool),2);
    end
    sub_symbol_pool = fetchmysql(sprintf(sql_str3,sub_t{1},index_pool),2);

    tref = tref(end-window+1:end);
    %获取收益率数据
    sub_t1 = tref{1};
    sub_t2 = tref{end};
    [sub_r,~,sub_symbol_u] = get_interchgPct(sub_t1,sub_t2);
    X = zeros(size(sub_symbol_pool,1),length(tref));
    [~,ia,ib] = intersect(sub_symbol_pool(:,1),sub_symbol_u);
    X(ia,:) = sub_r(ib,:);
    %}
    %load temp_data
    p = 30;
    lamada = 1e7;
    %lamada = 0;
    max_w = 0.1;
    X = X';
    w0 = cell2mat(sub_symbol_pool(:,end));
    w0 = w0/sum(w0);
    r = X*w0;

    %f = 1/window*(r-X*w)+0.5*ones(1,index_num)*log(1+w/p)/log(1+0.2/p);
    fun = @(w) 1/window*sum((r-X*w).^2)+lamada*ones(1,index_num)*log(1+w/p)/log(1+max_w/p);

    options = optimoptions('fmincon');
    options.MaxFunctionEvaluations = 30000;
    warning('off')
    wp = fmincon(fun,w0,[],[],ones(1,index_num),1,zeros(index_num,1),ones(index_num,1)*max_w,[],options);
    warning('on');
    
end
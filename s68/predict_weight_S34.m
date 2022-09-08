function [wp,sub_symbol_pool] = predict_weight_S34(tref,window,index_pool,index_num,print_sel)
    if nargin < 5
        print_sel = true;
    end
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
    T = length(tref);
    X = zeros(index_num,T); %每日收益 
    re = cell(T,1);
    parfor i = 1:T    
        sub_r = fetchmysql(sprintf(sql_str,tref{i}),2);
        [~,ia,ib] = intersect(sub_symbol_pool(:,1),sub_r(:,1));
        %X(ia,i)= cell2mat(sub_r(ib,2));
        re{i} = {ia,cell2mat(sub_r(ib,2))};
        if print_sel
            sprintf('%d-%d',i,T)
        end
    end
    for i = 1:T
        ia = re{i}{1};
        sub_r  = re{i}{2};
        X(ia,i)= sub_r;
    end
    %}
    %load temp_data
    p = 0.5;
    lamada = 1e7;
    max_w = 0.1;
    X = X';
    w0 = cell2mat(sub_symbol_pool(:,end));
    w0 = w0/sum(w0);
    r = X*w0;

    %f = 1/window*(r-X*w)+0.5*ones(1,index_num)*log(1+w/p)/log(1+0.2/p);
    fun = @(w) 1/window*sum((r-X*w).^2)+lamada*ones(1,index_num)*log(1+w/p)/log(1+max_w/p);

    options = optimoptions('fmincon');
    options.MaxFunctionEvaluations = 30000;

    wp = fmincon(fun,w0,[],[],ones(1,index_num),1,zeros(index_num,1),ones(index_num,1)*max_w,[],options);
end
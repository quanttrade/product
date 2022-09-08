function [wp,sub_symbol_pool,OK] = predict_weight_S34_update4(tref,window,index_pool)
    
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
    if isempty(sub_t)
        wp=[];
        OK=true;
        sub_symbol_pool = [];
        return
    end
    sub_symbol_pool = fetchmysql(sprintf(sql_str3,sub_t{1},index_pool),2);

    tref = tref(end-window+1:end);
    %获取收益率数据
    sub_t1 = tref{1};
    sub_t2 = tref{end};
    [sub_r,sub_t_u,sub_symbol_u] = get_interchgPct(sub_t1,sub_t2);
    [~,ia,ib] = intersect(tref,sub_t_u);
    tref = tref(ia);
    sub_r = sub_r(:,ib);
    X = zeros(size(sub_symbol_pool,1),length(tref));
    [~,ia,ib] = intersect(sub_symbol_pool(:,1),sub_symbol_u);
    X(ia,:) = sub_r(ib,:);
    %}
    %load temp_data
    %lamada = 0;
    max_w = 0.1;
    X = X';
    w0 = cell2mat(sub_symbol_pool(:,end));
    w0 = w0/sum(w0);
    r = X*w0;
    
    %lasso 弹性网选股步骤
    [b,FitInfo] = lasso(X,r,'CV',5,'Alpha',0.75);
    %[b,FitInfo] = lasso(X,r,'CV',5);
    wp = b(:,FitInfo.Index1SE);
        
    wp(wp<0) = 0;
    id = wp>0;
    %非线性优化步骤
    if ~(any(id))
        wp=[];
        OK=true;
    else
        X2 = X(:,id);
    
        %f = 1/window*(r-X*w)+0.5*ones(1,index_num)*log(1+w/p)/log(1+0.2/p);
        fun = @(w) 1/window*sum((r-X2*w).^2);

        options = optimoptions('fmincon','Display','off');
        options.MaxFunctionEvaluations = 30000;
        warning('off')
        wp1 = fmincon(fun,w0(id),[],[],ones(1,sum(id)),1,zeros(sum(id),1),ones(sum(id),1)*max_w,[],options);
        wp(:) = 0;
        wp(id) = wp1;
        OK = false;
    end
    
    
end
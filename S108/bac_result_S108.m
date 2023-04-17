clear
[~,tmp] = dos('python bac_toolS108.py');
sprintf('%s',tmp)
if ~strcmp(tmp(1:13),'S108因数据原因停止计算')
    sql_tmp ='select index_id,mID,tradeDate,r_long,r_short,r_long-r_short from s37.s108_return order by tradeDate';
    X = fetchmysql(sql_tmp,2);

    index_pool = {'A','000300','000905'};
    mID = {'f','tgd','tgd_skew'};

    para = cell(3,1);
    for i = 1:3
        tmp = mID';
        tmp(:,2) = index_pool(i);
        para{i} = tmp';
    end
    para = [para{:}]';
    para = para(:,[2,1]);


    T = size(para,1);
    H = zeros(T,1);
    Y = cell(T,1);
    info = Y;
    leg_str = {'long','short','long-short'};
    for i = 1:T
        x = X(strcmp(X(:,1),para(i,1)) & strcmp(X(:,2),para(i,2)),3:end);
        tref = cellstr(datestr(datenum(x(:,1)),'yyyymmdd'));
        x = cell2mat(x(:,2:end));
        x(:,end) = x(:,end)/2;
        y_re = cumprod(1+x);
        H(i) = bacFigure(y_re,tref,strjoin(para(i,:),'-'),leg_str);
        info{i} = cellfun(@(x) [x,'-',strjoin(para(i,:),'-')],leg_str,'UniformOutput',false);
        Y{i} = array2cell_adair(y_re);
    end

    info = [info{:}];
    Y = [Y{:}];
    report_adair(sprintf('S108计算结果%s',tref{end}),H,Y,info);
end
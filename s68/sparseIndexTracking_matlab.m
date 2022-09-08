%使用matlab查找数据，并将数据整理为R需要的csv格式
%R读入CSV数据，计算权重，并将数据写到CSV
%matlab读取CSV，载入结果 ，输出
function [wp,sub_symbol_pool,OK] = sparseIndexTracking_matlab(tref,window,index_pool,id)
    if nargin < 4
        id = 1;
    end
%tref = yq_methods.get_tradingdate('2012-01-01','2019-04-02');
%window = 125;
%index_pool = '000016';
    pn0=pwd;
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
    else
        OK = false;
    end
    
    sub_symbol_pool = fetchmysql(sprintf(sql_str3,sub_t{1},index_pool),2);
    tref = tref(end-window+1:end);
    
    %写入参数
    key_str = tref{end};
    %key_str(strfind(key_str,'-')) = [];
    fn1 = sprintf('%s_%s_X.csv',index_pool,key_str);
    fn2 = sprintf('%s_%s_r.csv',index_pool,key_str);
    fn1 = fullfile(fullfile(pn0,'R_relate'),fn1);
    fn2 = fullfile(fullfile(pn0,'R_relate'),fn2);
    fn3 = fullfile(fullfile(pn0,'R_relate'),sprintf('%s_%s',index_pool,key_str));
    %fn_re = fullfile(fullfile(pn0,'R_relate'),sprintf('%s_%s_w_%d.csv',index_pool,key_str,id));
    fn_re = fullfile(fullfile(pn0,'R_relate'),sprintf('%s_%s_w_%d.mat',index_pool,key_str,id));
    
    %获取收益率数据
    sub_t1 = tref{1};
    sub_t2 = tref{end};
    [sub_r,~,sub_symbol_u] = get_interchgPct(sub_t1,sub_t2);
    X = zeros(size(sub_symbol_pool,1),length(tref));
    [~,ia,ib] = intersect(sub_symbol_pool(:,1),sub_symbol_u);
    if isempty(ia)
        wp=[];
        OK=true;
        sub_symbol_pool = [];
        return
    end
    
    X(ia,:) = sub_r(ib,:);

    X = X';
    w0 = cell2mat(sub_symbol_pool(:,end));
    w0 = w0/sum(w0);
    r = X*w0;
    
    x_var = cellfun(@(x) sprintf('V%s',x),sub_symbol_pool(:,1)','UniformOutput',false);
    X = [tref,num2cell(X)];
    X_var = [{'X'},x_var];
    y = [tref,num2cell(r)];
    y_var = {'X','r'};
    X = cell2table(X,'VariableNames',X_var);
    y = cell2table(y,'VariableNames',y_var);
    if ~exist(fn1,'file')>0
        writetable(X,fn1)
        pause(1);
    end
    if ~exist(fn2,'file')>0
        writetable(y,fn2)
        pause(1);
    end
    
    fn_R = fullfile(fullfile(pn0,'R_relate'),'M_calw3.R');
    %system('Rscript "D:/worksPool/works2020/SOME/S34/program/R_relate/M_calw2.R" D:/worksPool/works2020/SOME/S34/program/R_relate/2019-04-02 2')
    system(sprintf('Rscript "%s" "%s" %d',fn_R,fn3,id));
    %w = readtable(fn_re);
    w = load(fn_re);
    wp = w.w;
end
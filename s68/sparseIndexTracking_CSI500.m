%使用matlab查找数据，并将数据整理为R需要的csv格式
%R读入CSV数据，计算权重，并将数据写到CSV
%matlab读取CSV，载入结果 ，输出
%因为无法找到所有日期的sp500的成分股权重，默认使用等权重来执行
%CSI500策略
function [wp,sub_symbol_pool,OK] = sparseIndexTracking_CSI500(tref,r,window,index_pool,id,sub_key2)
    if nargin < 5
        id = 1;
    end
    if nargin < 6
        sub_key2 = 'csi500';
    end
    pn0=pwd;
    %写入参数
    key_str = tref{end};
    %key_str(strfind(key_str,'-')) = [];
    fn1 = sprintf('%s_%s_%s_X.csv',sub_key2,index_pool,key_str);
    fn2 = sprintf('%s_%s_%s_r.csv',sub_key2,index_pool,key_str);
    fn1 = fullfile(fullfile(pn0,'R_relate'),fn1);
    fn2 = fullfile(fullfile(pn0,'R_relate'),fn2);
    fn3 = fullfile(fullfile(pn0,'R_relate'),sprintf('%s_%s_%s',sub_key2,index_pool,key_str));
    %fn_re = fullfile(fullfile(pn0,'R_relate'),sprintf('%s_%s_w_%d.csv',index_pool,key_str,id));
    fn_re = fullfile(fullfile(pn0,'R_relate'),sprintf('%s_%s_%s_w_%d.mat',sub_key2,index_pool,key_str,id));
    fn_re_symbol = fullfile(fullfile(pn0,'R_relate'),sprintf('%s_%s_%s_symbol_%d.mat',sub_key2,index_pool,key_str,id));
        
    if exist(fn_re,'file')
        w = load(fn_re);
        wp = w.w;
        sub_symbol_pool = load(fn_re_symbol);
        sub_symbol_pool = sub_symbol_pool.sub_symbol_pool;
    else
        sub_symbol_pool = yq_methods.get_index_pool(index_pool,tref{end});%这个地方容易出错。
        save(fn_re_symbol,'sub_symbol_pool');
        tref = tref(end-window+1:end);
        r = r(end-window+1:end); %reference index
        r(1) = 0;%读入数据，第一个的收益是0，所以ref也必须为0
        %获取收益率数据
        sub_t1 = tref{1};
        sub_t2 = tref{end};
        [sub_r,sub_t_u,sub_symbol_u] = get_interchgPct(sub_t1,sub_t2);
        sub_r(:,1) = 0;
        X = zeros(size(sub_symbol_pool,1),length(tref));
        [~,ia,ib] = intersect(sub_symbol_pool(:,1),sub_symbol_u);
        if isempty(ia)
            wp=[];
            OK=true;
            sub_symbol_pool = [];
            return
        end

        [~,ia1,ib1] = intersect(tref,sub_t_u);

        X(ia,ia1) = sub_r(ib,ib1);

        X = X';
        x_var = cellfun(@(x) sprintf('V%s',x),sub_symbol_pool(:,1)','UniformOutput',false);
        x_var = cellfun(@(x) replace(x,'.','_'),x_var,'UniformOutput',false);
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

        fn_R = fullfile(fullfile(pn0,'R_relate'),'M_calwUS.R');
        %system('Rscript "D:/worksPool/works2020/SOME/S34/program/R_relate/M_calw2.R" D:/worksPool/works2020/SOME/S34/program/R_relate/2019-04-02 2')
        system(sprintf('Rscript "%s" "%s" %d',fn_R,fn3,id));
        %w = readtable(fn_re);
        w = load(fn_re);
        wp = w.w;
    end
end
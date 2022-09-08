%使用matlab查找数据，并将数据整理为R需要的csv格式
%R读入CSV数据，计算权重，并将数据写到CSV
%matlab读取CSV，载入结果 ，输出
%因为无法找到所有日期的sp500的成分股权重，默认使用等权重来执行
%CSI500策略
function [wp,sub_symbol_pool,OK] = sparseIndexTracking_indexISO(tref,r,window,index_pool,id)
    if nargin < 5
        id = 1;
    end
    pn0=pwd;
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
    fn_re_symbol = fullfile(fullfile(pn0,'R_relate'),sprintf('%s_%s_symbol_%d.mat',index_pool,key_str,id));
    if exist(fn_re,'file')
        w = load(fn_re);
        wp = w.w;
        sub_symbol_pool = load(fn_re_symbol);
        sub_symbol_pool = sub_symbol_pool.sub_symbol_pool;
        
        if strcmpi(index_pool,'HSI')
            sub_symbol_pool=cellfun(@(x) sprintf('%0.5d',str2double(x)),sub_symbol_pool,'UniformOutput',false);
        elseif any(strcmpi(index_pool,{'topix','twse','hsce','msci','nky'}))
            sub_symbol_pool=cellfun(@(x) sprintf('%0.4d',str2double(x)),sub_symbol_pool,'UniformOutput',false);
        elseif any(strcmpi(index_pool,{'kosdaq','kospi','xin9i'}))
            sub_symbol_pool=cellfun(@(x) sprintf('%0.6d',str2double(x)),sub_symbol_pool,'UniformOutput',false);
        end
    else
        tref = tref(max(end-window+1,1):end);
        r = r(max(end-window+1,1):end); %reference index
        r(1) = 0;%读入数据，第一个的收益是0，所以ref也必须为0
        %获取收益率数据
        sub_t1 = tref{1};
        sub_t2 = tref{end};
        [sub_r,sub_t_u,sub_symbol_u] = get_interchgPct_ISO(sub_t1,sub_t2,index_pool);
        %特殊符号清除
        sub_symbol_u = cellfun(@(x) replace(x,'/','_'),sub_symbol_u,'UniformOutput',false);
        sub_symbol_u = cellfun(@(x) replace(x,'-','_'),sub_symbol_u,'UniformOutput',false);
        sub_symbol_pool = sub_symbol_u;
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
        save(fn_re_symbol,'sub_symbol_pool');
    end
end
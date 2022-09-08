clear
pn = 'S68para_pool';
max_symbol_sel = 40;
index_pool = {'000905','000300'};

pos_re = [];
H = zeros(2,1);
for i0 = 1:2
    index_sel = index_pool{i0};
    dos(sprintf('python S68P2.py %s %d',index_sel,max_symbol_sel));
    key_str = sprintf('%s_%0.2d_',index_sel,max_symbol_sel);
    title_str = sprintf('%s-%0.2d',index_sel,max_symbol_sel);
    fns = dir(fullfile(pn,sprintf('%s*.csv',key_str)));
    fns = sort({fns.name})';
    tref_model = cellfun(@(x) x(length(key_str)+1:end-4),fns,'UniformOutput',false);

    T_tref_inter = length(fns);
    w = cell(T_tref_inter,1);
    for i = 1:T_tref_inter
        x = readtable(fullfile(pn,fns{i}));
        x= table2cell(x);
        x(:,1) = cellfun(@(x) sprintf('%0.6d',x),x(:,1),'UniformOutput',false);
        w{i} = x;
    end
    W = containers.Map(tref_model,w);


    sql_tmp = 'select tradeDate,CHGPct from yuqerdata.yq_index where symbol = "%s" and tradeDate>"%s" order by tradeDate';
    index = fetchmysql(sprintf(sql_tmp,index_sel,tref_model{1}),2);
    r = zeros(size(index));
    r(:,1) = cell2mat(index(:,2));
    re = cell(T_tref_inter,1);
    sub_pos = cell(T_tref_inter,1);
    parfor i = 1:T_tref_inter
        sub_t1 = tref_model{i};
        if eq(i,T_tref_inter)
            sub_t2 = index{end,1};
        else
            sub_t2 = tref_model{i+1};
        end
        x = W(sub_t1);
        sub_symbol = x(:,1);
        sub_w = cell2mat(x(:,2));
        
        tmp = cell(length(sub_w),2);
        tmp(:,1) = {title_str};
        tmp(:,2) = {sub_t1};
        sub_pos{i} = [tmp,sub_symbol,num2cell(sub_w)]';
                        
        [sub_r,sub_t_u,sub_symbol_u] = get_interchgPct_s68p2(sub_t1,sub_t2,sub_symbol);

        sub_index = sub_r' * sub_w;
        re{i} = {sub_index,sub_t_u};
    end
    tmp = [sub_pos{:}];
    pos_re = cat(1,pos_re,{tmp});
    for i = 1:T_tref_inter
        sub_index = re{i}{1};
        sub_t_u = re{i}{2};
        [~,ia,ib] = intersect(index(:,1),sub_t_u,'stable');
        r(ia,2) = sub_index(ib);
    end
    t_str = index(:,1);
    T = length(t_str);
    h = figure;
    yc = cumprod(1+r);
    plot(yc,'LineWidth',2);
    set(gca,'xlim',[0,T]);
    set(gca,'XTick',floor(linspace(1,T,15)));
    set(gca,'XTickLabel',t_str(floor(linspace(1,T,15))));
    set(gca,'XTickLabelRotation',90)    
    setpixelposition(gcf,[223,365,1345,420]);
    legend({'指数','增强指数S68P2'},'location','best')
    title(title_str);
    H(i0) = h;
    sprintf('Track RMSE of curve %s is %0.4f%%',index_sel,rms(yc(:,2)-yc(:,1))*100)
    sprintf('Track RMSE of return %s is %0.4f%%',index_sel,rms(r(:,2)-r(:,1))*100)
end
pos_re = [pos_re{:}]';
dir1 =fullfile(pwd, '计算结果');
sub_re = pos_re;
sub_re = cell2table(sub_re,'VariableNames',{'indexMethod','dealDate','symbol','weight'});
writetable(sub_re,fullfile(dir1,'S68P2选择成分股权重.csv'));

fn0=fullfile(dir1,'S68P2回测曲线.doc');
obj_wd = wordcom(fn0);
for i = 1:length(H)
    obj_wd.pasteFigure(H(i),index_pool{i});
end
obj_wd.CloseWord();

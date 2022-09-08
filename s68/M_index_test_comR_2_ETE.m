%加入R计算权重
%全部指数参与计算
close all
index_str = '000300-沪深300';
temp = strsplit(index_str,',');
index_info = cellfun(@(x) strsplit(x,'-'),temp,'UniformOutput',false);
w_sel = 1;
print_sel = true;
write_doc_sel = true;
window = 125;
t1 = '2012-01-01';
t2 = '2020-01-13';

symbol_pool_all = cellfun(@(x) x{1},index_info,'UniformOutput',false);
symbol_pool_info = cellfun(@(x) x{2},index_info,'UniformOutput',false);
T_symbol_pool_all = length(symbol_pool_all);
if write_doc_sel
    obj_w = wordcom(fullfile(pwd,'ETE_all.doc'));
end
sta_re = [];
for pool_id = 1:T_symbol_pool_all
    index_pool=symbol_pool_all{pool_id};
    title_str = symbol_pool_info{pool_id};
    
    %%{                
    %日期
    sql_str_index = ['SELECT tradeDate,closeIndex FROM yuqerdata.yq_index where symbol = ''%s'' ',...
    'and tradeDate >=''%s'' and tradeDate<=''%s'' order by tradeDate'];

    y_index = fetchmysql(sprintf(sql_str_index,index_pool,t1,t2),2);
    tref = y_index(:,1);
    %tref = yq_methods.get_tradingdate('2012-01-01','2019-04-02');
    if length(tref)<1000
        continue
    end
    %月底日期
    tref_num = datenum(tref);
    %获取月底日期
    %last day for the month
    month_index = month(tref_num);
    month_cut = [0;find(diff(month_index))];
    month_cut = [month_cut(1:end-1)+1,month_cut(2:end)];
    month_cut_date1 = tref(month_cut(:,1));
    month_cut_date2 = tref(month_cut(:,2));
    T = length(month_cut_date2);
    re = cell(T,1);
    [~,~,OK] = sparseIndexTracking_matlab(tref(1:month_cut(end,2)),window,index_pool,w_sel);
    if OK
        continue
    end
    L = zeros(T,1);
    for i = 12:6:T-6

        sub_tref = tref(month_cut(i-12+1,2)+1:month_cut(i,2));
        [wp,sub_symbol_pool] = sparseIndexTracking_matlab(sub_tref,window,index_pool,w_sel);
        w0 = cell2mat(sub_symbol_pool(:,2));
        %获取未来一个月的收益
        sub_t1 = month_cut_date1{i+1};
        sub_t2 = month_cut_date2{i+6};
        ind = month_cut(i+1,1):month_cut(i+6,2);

        [sub_r,sub_t_u,sub_symbol_u] = get_interchgPct(sub_t1,sub_t2);
        [~,ia,ib] = intersect(sub_symbol_pool(:,1),sub_symbol_u);
        sub_r0 = zeros(length(w0),length(ind));
        sub_r0(ia,:) = sub_r(ib,:);

        re{i} = {ind,sub_r0,w0,wp}; 
        L(i) = sum(wp>1e-6);

        if print_sel
            sprintf('%d-%d %d:%d',i,T,pool_id,T_symbol_pool_all)
        end
    end
    %%%%%%%%%%%%
    r = zeros(length(tref),2);
    id0 = 0;
    for i = 1:T
        if ~isempty(re{i})

            sub_re = re{i};
            sub_ind = sub_re{1};
            sub_r0 = sub_re{2};
            w0 = sub_re{3}/100;
            wp = sub_re{4};
            
            sub_r1 = mean(sub_r0)';
            %sub_r1 = sub_r0'*w0;
            sub_r2 = sub_r0'*wp;
            r(sub_ind,:) = [sub_r1,sub_r2];

            if eq(id0,0)
                id0 =sub_ind(1);
            end
        end
    end
    
    r = r(id0:end,:);
    r(1,:) = 0;%第一天收益设定为0
    tref = tref(id0:end);
    y_index = cell2mat(y_index(id0:end,2));
    r(2:end,1) = y_index(2:end)./y_index(1:end-1)-1;%指数收益使用实际指数数据
    y_c = cumprod(1+r);
    
    t_str = tref;
    T=length(t_str);
    h=figure;
    plot(y_c-1,'LineWidth',2);
    set(gca,'xlim',[0,T]);
    set(gca,'XTick',floor(linspace(1,T,15)));
    set(gca,'XTickLabel',t_str(floor(linspace(1,T,15))));
    set(gca,'XTickLabelRotation',90)    
    setpixelposition(gcf,[223,365,1345,420]);
    legend({'指数','增强指数'})
    title(title_str);
    if write_doc_sel
    obj_w.pasteFigure(h,title_str)
    end
    h=figure;
    bar(r(:,2)-r(:,1),'LineWidth',2);
    set(gca,'xlim',[0,T]);
    set(gca,'XTick',floor(linspace(1,T,15)));
    set(gca,'XTickLabel',t_str(floor(linspace(1,T,15))));
    set(gca,'XTickLabelRotation',90)    
    setpixelposition(gcf,[223,365,1345,420]);
    %legend({'增强指数-原指数 收益'})
    title(title_str);
    if write_doc_sel
    obj_w.pasteFigure(h,title_str)
    end
    
    h=figure;
    plot(cumprod(1+r(:,2)-r(:,1))-1,'LineWidth',2);
    set(gca,'xlim',[0,T]);
    set(gca,'XTick',floor(linspace(1,T,15)));
    set(gca,'XTickLabel',t_str(floor(linspace(1,T,15))));
    set(gca,'XTickLabelRotation',90)    
    setpixelposition(gcf,[223,365,1345,420]);
    %legend({'增强指数-原指数 收益曲线'})
    title(title_str);
    if write_doc_sel
    obj_w.pasteFigure(h,title_str)
    end
    %统计曲线参数
    [v1,v_str] = curve_static(y_c(:,1));
    [v2,~] = curve_static(y_c(:,2));
    tb_str2 = sprintf('增%s',title_str);
    sub_re = [{title_str,tb_str2};num2cell([v1',v2'])];
    
    sta_re = cat(2,sta_re,sub_re);
end
CloseWord(obj_w)
if ~isempty(sta_re)
    sta_re = [[{''};v_str'],sta_re];
end
save('ETE_method.mat','sta_re')
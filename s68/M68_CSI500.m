clear
%SP500 uqer_index "SPX";成分
index_str = 'CSI500';
%temp = strsplit(index_str,',');
%index_info = cellfun(@(x) strsplit(x,'-'),temp,'UniformOutput',false);
w_sel = 2;
track_name = containers.Map(1:4,{'ETE','DR','HETE','HDR'});
print_sel = true;
write_doc_sel = false;
window = 242;
t1 = '2010-01-01';
t2 = datestr(now,'yyyy-mm-dd');

index0 = '000905';
symbol_pool_all = {'000905','000300'};
symbol_pool_info = {'csi500-csi500','csi500-csi300'};
T_symbol_pool_all = length(symbol_pool_all);
if write_doc_sel
    obj_w = wordcom(fullfile(pwd,'ETE_all.doc'));
end
sta_re = [];
for pool_id = 1:T_symbol_pool_all
    index_pool=symbol_pool_all{pool_id};
    title_str = [symbol_pool_info{pool_id},'-',track_name(w_sel)];
    %%{                
    %日期
    sql_str_index = ['SELECT tradeDate,closeIndex FROM yuqerdata.yq_index where symbol = ''%s'' ',...
    'and tradeDate >=''%s'' and tradeDate<=''%s'' order by tradeDate'];
    y_index = fetchmysql(sprintf(sql_str_index,index0,t1,t2),2);
    
    tref = y_index(:,1);
    y_r = cell2mat(y_index(:,2));
    y_r(2:end) =y_r(2:end)./y_r(1:end-1)-1;
    y_r(1) = 0;
    %tref = yq_methods.get_tradingdate('2012-01-01','2019-04-02');
    %月底日期
    tref_num = datenum(tref);
    %获取月底日期
    %last day for the month
    month_index = month(tref_num);
    month_cut = unique([0;find(diff(month_index))]);
    month_cut = [month_cut(1:end-1)+1,month_cut(2:end)];
    month_cut_date1 = tref(month_cut(:,1));
    month_cut_date2 = tref(month_cut(:,2));
    T = length(month_cut_date2);
    re = cell(T,1);
    L = zeros(T,1);
    i_pool = 12:3:T;
    T2 = length(i_pool);
    parfor i0 = 1:T2
        i = i_pool(i0);
        sub_tref = tref(1:month_cut(i,2));
        sub_y = y_r(1:month_cut(i,2));
        [wp,sub_symbol_pool] = sparseIndexTracking_CSI500(sub_tref,sub_y,window,index_pool,w_sel);
        [~,ia] = sort(wp,'descend');
        wp(ia(41:end)) = 0;
        wp = wp./sum(wp);
        %获取未来月的收益
        sub_t1 = month_cut_date1{i+1};
        tmp = min(T,i+3);
        sub_t2 = month_cut_date2{tmp};
        ind = month_cut(i+1,1):month_cut(tmp,2);
        if eq(i,i_pool(end))
            tmp = length(tref);
            sub_t2 = tref{tmp};
            ind = month_cut(i+1,1):tmp;
        end
        
        if isempty(ind)
            continue
        end
        [sub_r,sub_t_u,sub_symbol_u] = get_interchgPct(sub_t1,sub_t2);
        [~,ia,ib] = intersect(sub_symbol_pool(:,1),sub_symbol_u);
        [~,ia1,ib1] = intersect(tref(ind),sub_t_u);
        sub_r0 = zeros(length(wp),length(ind));
        sub_r0(ia,ia1) = sub_r(ib,ib1);
        w0 = y_r(ind);
        w0(1) = 0;

        re{i0} = {ind,sub_r0,w0,wp}; 
        %L(i) = sum(wp>1e-6);

        if print_sel
            sprintf('%d-%d %d:%d',i0,T2,pool_id,T_symbol_pool_all)
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
            %sub_r2 = sub_r0'*wp;
            wp_all = bsxfun(@times,cumprod(1+sub_r0'),wp');
            %中间需要加一个3个月后再平衡步骤            
            %sub_r2 = (cumprod(1+sub_r0')-1)*wp;
            sub_r2 = sum(sub_r0'.*wp_all,2);
            r(sub_ind,:) = [sub_r1,sub_r2];

            if eq(id0,0)
                id0 =sub_ind(1);
            end
        end
    end
    r0=r;
    r = r0(id0:end,:);
    r(1,:) = 0;%第一天收益设定为0
    tref1 = tref(id0:end);
    y_index = cell2mat(y_index(id0:end,2));
    r(2:end,1) = y_index(2:end)./y_index(1:end-1)-1;%指数收益使用实际指数数据
    y_c = cumprod(1+r);
    
    t_str = tref1;
    T=length(t_str);
    h=figure;
    plot(y_c,'LineWidth',2);
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
    plot(cumprod(1+r(:,2)-r(:,1)),'LineWidth',2);
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
    save(title_str,'tref1','r');
end
if write_doc_sel
CloseWord(obj_w)
end
if ~isempty(sta_re)
    sta_re = [[{''};v_str'],sta_re];
end
save('ETE_method.mat','sta_re')
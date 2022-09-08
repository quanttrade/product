track_name = containers.Map(1:2,{'ETE','DR'});
print_sel = true;
window = 242;
t1 = '2010-01-01';
t2 = datestr(now,'yyyy-mm-dd');
index0_pool = {'as51','hsce','hsi','topix','twse','kosdaq', 'kospi',... 
    'msci', 'ndx', 'nifty', 'nky', 'RTY', 'set50', 'sx5e','ukx', 'xin9i'};
tmp = {'AS51','HSCEI','HSI','TPX','TWSE','KOSDAQ','KOSPI2','TAMSCI','NDX',...
    'NIFTY','NKY','RTY','SET50','SX5E','UKX','XIN9I'};
index0_pool2 =containers.Map(index0_pool, tmp);
%max_num = [200,50,52,2185,914];%how many to keep? just as pre
T_symbol_pool_all = length(index0_pool);
bac_re = [];
pos_re = [];
for pool_id = 1:T_symbol_pool_all
    key_str=['iso-',index0_pool{pool_id}];
    fn1 = fullfile('计算结果',sprintf('%s_bac_re.mat',key_str));
    fn2 = fullfile('计算结果',sprintf('%s_pos_re.mat',key_str));
    if exist(fn1,'file') && exist(fn2,'file')
        tmp_bac_re = load(fn1);
        tmp_bac_re = tmp_bac_re.RE;

        tmp_pos_re = load(fn2);
        tmp_pos_re = tmp_pos_re.POS;
    else
        tmp_bac_re = cell(2,1);
        tmp_pos_re = cell(2,1);
    end
    RE = tmp_bac_re;
    POS = tmp_pos_re;
    for w_sel = 1:2
        sub_sub_re = RE{w_sel};
        sub_sub_pos = POS{w_sel};
        index0 = index0_pool{pool_id};
        title_str = [index0,'-',track_name(w_sel)];
        sql_key = index0_pool2(index0);
        %%{                
        %日期
        sql_str_index = ['SELECT tradeDate,closePrice FROM data_pro.main_index_s68 where index_id = ''%s'' ',...
        'and ticker="%s" and tradeDate >=''%s'' and tradeDate<=''%s'' order by tradeDate'];
        y_index = fetchmysql(sprintf(sql_str_index,index0,sql_key,t1,t2),2);

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
        m_end=is_month_end(tref_num(end));
        month_cut = unique([0;find(diff(month_index));length(month_index)]);
        month_cut = [month_cut(1:end-1)+1,month_cut(2:end)];

        month_cut_date1 = tref(month_cut(:,1));
        month_cut_date2 = tref(month_cut(:,2));
        T = length(month_cut_date2);
        re = cell(T,1);
        if m_end
            i_pool = 12:3:T;
        else
            i_pool = 12:3:(T-1);
        end
        %i_pool = 12:3:T;
        T2 = length(i_pool);
        if isempty(sub_sub_pos)
            i0_0=1;
        else
            tmp=cellfun(@isempty,sub_sub_pos);
            tmp = sub_sub_pos(~tmp);
            if ~isempty(tmp)
                %tmp = tmp_bac_re(strcmp(tmp_bac_re(:,1),title_str),:);
                tmp = tmp{end}(:,end);
                tmp = tmp(2);
                [~,~,ia] = intersect(tmp,month_cut_date2);
                i0_0 = max(ia);
                i0_0 = i0_0+1;
            else
                i0_0 = 1;
            end
        end

        sub_pos = cell(T2,1);
        tmp=sub_sub_re;
        re(1:length(tmp)) = tmp;
        tmp = sub_sub_pos;
        sub_pos(1:length(tmp)) = tmp;


        parfor i0 = i0_0:T2
            i = i_pool(i0);
            if i+1 > T
                continue
            end
            sub_tref = tref(1:month_cut(i,2));
            sub_y = y_r(1:month_cut(i,2));
            [wp,sub_symbol_pool] = sparseIndexTracking_indexISO(sub_tref,sub_y,window,index0,w_sel);
            [~,ia] = sort(wp,'descend');
            tmp_num = sum(wp>0);
            ia = ia(1:tmp_num);
            wp = wp(ia);
            wp = wp./sum(wp);
            sub_symbol_pool = sub_symbol_pool(ia);

            tmp = cell(length(wp),2);
            tmp(:,1) = {title_str};
            tmp(:,2) = sub_tref(end);
            sub_pos{i0} = [tmp,sub_symbol_pool,num2cell(wp)]';

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
            [sub_r,sub_t_u,sub_symbol_u] = get_interchgPct_ISO(sub_t1,sub_t2,index0,sub_symbol_pool);
            sub_r(abs(sub_r)>2) = 0;
            [~,ia,ib] = intersect(sub_symbol_pool(:,1),sub_symbol_u);
            [~,ia1,ib1] = intersect(tref(ind),sub_t_u);
            sub_r0 = zeros(length(wp),length(ind));
            sub_r0(ia,ia1) = sub_r(ib,ib1);
            w0 = y_r(ind);
            w0(1) = 0;

            re{i0} = {ind,sub_r0,w0,wp}; 
            %L(i) = sum(wp>1e-6);

            if print_sel
                sprintf('%s %d-%d %d:%d',index0,i0,T2,pool_id,T_symbol_pool_all)
            end
        end
        RE{w_sel} = re;
        POS{w_sel} = sub_pos;
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
        id0 = max(id0,1);
        r = r0(id0:end,:);
        r(1,:) = 0;%第一天收益设定为0
        tref1 = tref(id0:end);
        y_index = cell2mat(y_index(id0:end,2));
        r(2:end,1) = y_index(2:end)./y_index(1:end-1)-1;%指数收益使用实际指数数据
        tmp = [tref1,tref1,num2cell(r)];
        tmp(:,1) = {title_str};
        bac_re = cat(1,bac_re,{tmp'});
        tmp = [sub_pos{:}];
        pos_re = cat(1,pos_re,{tmp});
    end
    save(fn1,'RE');
    save(fn2,'POS');
end
bac_re = [bac_re{:}]';
pos_re = [pos_re{:}]';
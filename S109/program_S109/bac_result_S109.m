clear
disp('开始更新因子、股票池、回测曲线');
disp('第一部分需要60-100s');
dos('python bac_toolS109.py');
disp('第二部分需要0-159s');
dos('python bac_toolS109P2.py');
disp('第三部分需要0-380s');
dos('python M_backtest_S109_month.py');

disp('第四部分 写入曲线及曲线参数');
sql_tmp ='select fac_name,pre,pool,tradeDate,l,s,ls from s37.s109_return order by tradeDate';

X = fetchmysql(sql_tmp,2);
X_pre = cell2mat(X(:,2));

fac_name = unique(X(:,1));
pre_num = unique(X_pre);
pool = unique(X(:,3));

para = cell(size(fac_name));
for i = 1:length(pre_num)
    tmp = fac_name;
    tmp(:,2) = {pre_num(i)};
    tmp1 = cell(size(pool));
    for j = 1:length(pool)
        sub_tmp = tmp;
        sub_tmp(:,3) = pool(j);
        tmp1{j} = sub_tmp';
    end
    para{i} = [tmp1{:}];
end
para = [para{:}]';

T = size(para,1);
H = zeros(T,1);
Y = cell(T,1);
info = Y;
%leg_str = {'long','short','longshort'};
leg_str = {'longshort'};
info_dic = containers.Map([0,1,2],{'原始因子','市值中性化','全部风格中性化'});
for i = 1:T
    x = X(strcmp(X(:,1),para(i,1)) & eq(X_pre,para{i,2}) & strcmp(X(:,3),para(i,3)),[4,end]);
    tref = cellstr(datestr(datenum(x(:,1)),'yyyymmdd'));
    x = cell2mat(x(:,2:end));
    x(:,end) = x(:,end)/2;
    y_re = cumprod(1+x);
    tmp = [para{i,1},'-',info_dic(para{i,2}),'-',para{i,3}];
    
    H(i) = bacFigure(y_re,tref,tmp,leg_str);
    info{i} = cellfun(@(x) [x,'-',tmp],leg_str,'UniformOutput',false);
    Y{i} = array2cell_adair(y_re);
end

info = [info{:}];
Y = [Y{:}];
L = cell(size(Y));
L(:)= {12};
report_adair(sprintf('S109计算结果%s',tref{end}),H,Y,info,L);

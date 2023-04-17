clear
close all
disp('更新因子');
dos('python bac_toolS112.py')
%%%%%%%%%
disp('写入曲线及曲线参数');
[~,~,X] = xlsread('S112_back.xlsx');
X = X(2:end,:);
fac_name = X(:,end);
tref_all = X(:,2);
X = cell2mat(X(:,[3,7]));
fac_name_u = unique(fac_name);
T = length(fac_name_u);
H = zeros(T,1);
Y = cell(T,1);
info = Y;
leg_str = {'long','short','longshort'};
%leg_str = {'longshort'};
L = cell(T,1);

fee = 2/1000;
t_tmp = '1990-01-01';
for i = 1:T
    ind = strcmp(fac_name,fac_name_u(i));
    x = X(ind,:);
    x = [x,(x(:,1)-x(:,end))/2] - fee;
    tref = tref_all(ind,:);
    if datenum(tref{end})>datenum(t_tmp)
        t_tmp = tref{end};
    end
    y_re = cumprod(1+x);
    tmp = fac_name_u{i};
    
    H(i) = bacFigure(y_re,tref,tmp,leg_str);
    info{i} = cellfun(@(x) [x,'-',tmp],leg_str,'UniformOutput',false);
    Y{i} = array2cell_adair(y_re);
    if contains(tmp,'2d')
        L{i} = repmat(244/2,1,3);
    else
        L{i} = repmat(244/2,1,3);
    end
    L{i} = round(L{i});
end

info = [info{:}];
Y = [Y{:}];
L = [L{:}];
L = num2cell(L);
report_adair(sprintf('S112计算结果%s',t_tmp),H,Y,info,L);

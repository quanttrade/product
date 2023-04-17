clear


[~,~,x] = xlsread('结果统计.xlsx');

tref = cellstr(datestr(datenum(x(2:end,1)),'yyyymmdd'));
X = cell2mat(x(2:end,2:end));
T = size(X,2);

H = zeros(T,1);
Y = cell(T,1);
info = x(1,2:end);

ind = zeros(T,1);
for i = 1:T
    y_re = cumprod(1+X(:,i));
    H(i) = bacFigure(y_re,tref,info{i},[]);
    Y{i} = y_re;
end

report_adair('S102_',H,Y,info);
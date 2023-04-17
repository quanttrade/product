clear
[~,~,x] = xlsread('data0.xlsx');
t = x(:,1);
y = x(:,3);

ind = cellfun(@isnumeric,t);
t(ind) = [];

ind = cellfun(@(x) strcmp(x(1),'2'),t);
t = t(ind);

ind = cellfun(@isnumeric,y);
y(ind) = [];

y = cellfun(@(x) replace(replace(x,'×Ü¹²:',''),',',''),y,'UniformOutput',false);
y = cellfun(@str2double,y);



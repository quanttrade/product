%因子验证
%作图


clear

t_all = {'20160107', '20130301', '20130311'};
T = 3;
X = cell(T,1);
for i = 1:T
    t = t_all{i};
    x = xlsread(sprintf('%s.xlsx',t));
    X{i} = x;
end

h = figure;

subplot(1,2,1);
for i = 1:T
    tmp = histogram(X{i}(:,1),'Normalization','pdf');
    %tmp(2).Color = tmp(1).FaceColor
    if eq(i,1)
        hold on
    end
end
legend(t_all);
title('上涨')

subplot(1,2,2)
for i = 1:T
    tmp = histogram(X{i}(:,2),'Normalization','pdf');
    %tmp(2).Color = tmp(1).FaceColor
    if eq(i,1)
        hold on
    end
end
title('下跌')
legend(t_all);
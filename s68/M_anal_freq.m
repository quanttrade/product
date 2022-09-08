clear
[~,~,x] = xlsread(fullfile('计算结果','S68换仓频率对比20210620.xlsx'));

fre = x(2:end,1);
m_id = x(2:end,2);

id = 3;
y = cell2mat(x(2:end,id));
t_str = x(1,id);


m_id_u = unique(m_id);
fre_u = unique(fre);

Y = zeros(length(m_id_u),length(fre_u));

for i = 1:length(m_id_u)
    ind1 = strcmp(m_id,m_id_u(i));
    for j = 1:length(fre_u)
        ind2 = strcmp(fre,fre_u(j));
        
        ind3 = ind1 & ind2;
        Y(i,j) = y(ind3);
    end
end


bar(Y)
set(gca,'XTick',1:length(Y),'XTickLabel',m_id,'XTickLabelRotation',30);
legend(fre_u,'NumColumns',2)
title(t_str);
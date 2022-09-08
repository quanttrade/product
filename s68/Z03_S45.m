clear
obj=bac_result_S68();
[bac_re,pos_re] = obj.update_CSI();
index = unique(bac_re(:,1));
T = length(index);
title_str = {'指数','指数增强','long-short'};
H = zeros(T,1);
yc=cell(T,1);
yc_t=cell(T,1);
for i = 1:T
    sub_x = strcmp(bac_re(:,1),index(i));
    sub_x = bac_re(sub_x,2:end);
    tref = sub_x(:,1);
    r = cell2mat(sub_x(:,2:end));
    r(:,3) = r(:,2)-r(:,1);
    sub_yc = cumprod(1+r);
    h = obj.figure_S53(sub_yc,tref,index{i},title_str);
    H(i) = h;
    yc{i} = {tref,sub_yc(:,3)};
    tmp = cellfun(@(x) [x,'-',index{i}],title_str,'UniformOutput',false);
    yc_t{i} = tmp{end};
end


save dataZX03_S68 yc_t yc
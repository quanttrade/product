%近期2周的结果
clear

N_keep=22*3;
obj = bac_result_S68();

[bac_re1,pos_re1] = obj.update_SP500();
[bac_re2,pos_re2] = obj.update_CSI();
[bac_re3,pos_re3] = obj.update_indexISO();

bac_re = [bac_re1;bac_re2;bac_re3];
pos_re = {pos_re1,pos_re2,pos_re3};
key_strs = {'SP500','CSI','indexISO'};
%save pos_re
dir1 =fullfile(pwd, '计算结果');
if ~exist(dir1,'dir')
    mkdir(dir1);
end
for i = 1:3
    sub_re = pos_re{i};
    sub_re = cell2table(sub_re,'VariableNames',{'indexMethod','dealDate','symbol','weight'});
    writetable(sub_re,fullfile(dir1,sprintf('S68P1选择成分股权重-%s-%s.csv',key_strs{i},datestr(now,'yyyy-mm-dd'))));
end
index = unique(bac_re(:,1));
T = length(index);
title_str = {'指数','指数增强','long-short'};
H = zeros(T,1);
yc=cell(T,1);
yc_t=cell(T,1);
for i = 1:T
    sub_x = strcmp(bac_re(:,1),index(i));
    sub_x = bac_re(sub_x,2:end);
    
    sub_x = sub_x(end-N_keep:end,:);
    tref = sub_x(:,1);
    r = cell2mat(sub_x(:,2:end));
    %adair update
    r(eq(r(:,2),0),:) = 0;
    
    r(:,3) = r(:,2)-r(:,1);
    r(1,:) = 0;
    sub_yc = cumprod(1+r);
    h = obj.figure_S53(sub_yc,tref,index{i},title_str);
    H(i) = h;
    yc{i} = {sub_yc(:,1),sub_yc(:,2),sub_yc(:,3)};
    tmp = cellfun(@(x) [x,'-',index{i}],title_str,'UniformOutput',false);
    yc_t{i} = tmp;
end
yc = [yc{:}];
yc_t = [yc_t{:}];
sta_re = obj.curve_static_batch(yc,yc_t);

fn0=fullfile(dir1,sprintf('S68P1近期回测曲线%s.doc',datestr(now,'yyyy-mm-dd')));
fn2=fullfile(dir1,sprintf('S68P1近期曲线参数%s.xlsx',datestr(now,'yyyy-mm-dd')));
obj_wd = wordcom(fn0);
for i = 1:length(H)
    obj_wd.pasteFigure(H(i),index{i});
end
obj_wd.CloseWord();
xlstocsv_adair(fn2,sta_re); 
%lasso 弹性网选股步骤
clear
obj=bac_result_S68();
[bac_re3,pos_re3] = obj.update_indexISO();

bac_re = bac_re3;
pos_re = pos_re3;
key_strs = {'SP500','CSI','indexISO'};
%save pos_re
dir1 =fullfile(pwd, '计算结果');
if ~exist(dir1,'dir')
    mkdir(dir1);
end
for i = 3
    sub_re = pos_re;
    sub_re = cell2table(sub_re,'VariableNames',{'indexMethod','dealDate','symbol','weight'});
    writetable(sub_re,fullfile(dir1,sprintf('S68P1选择成分股权重-%s-%s.csv',key_strs{i},datestr(now,'yyyy-mm-dd'))));
end

index = unique(bac_re(:,1));


ind1 = 1:length(index);
ind1 = reshape(ind1,4,length(ind1)/4)';
T = size(ind1,1);
H = zeros(T,1);
yc=cell(T,1);
yc_t=cell(T,1);
for i = 1:T
    tmp_ind = ind1(i,:);
    tmp1 = cell(4,1);
    for j = 1:4
        sub_x = strcmp(bac_re(:,1),index(ind1(i,j)));
        sub_x = bac_re(sub_x,2:end);
        tref = sub_x(:,1);
        r = cell2mat(sub_x(:,2:end));
        r(:,3) = r(:,2)-r(:,1);
        sub_yc = cumprod(1+r);
        tmp1{j} =sub_yc(:,end);
    end
    
    tmp1 = [tmp1{:}];
    title_str = index{tmp_ind(1)};
    title_str = split(title_str,'-');
    title_str = title_str{1};
    h = obj.figure_S53(tmp1,tref,title_str,index(tmp_ind));
    H(i) = h;
    yc{i} = {tmp1(:,1),tmp1(:,2),tmp1(:,3),tmp1(:,4)};
    
    yc_t{i} = index(tmp_ind);
end
yc = [yc{:}];
yc_t = [yc_t{:}];
sta_re = obj.curve_static_batch(yc,yc_t);

fn0=fullfile(dir1,sprintf('支线03-S68P1回测曲线%s.doc',datestr(now,'yyyy-mm-dd')));
fn2=fullfile(dir1,sprintf('支线03-S68P1曲线参数%s.xlsx',datestr(now,'yyyy-mm-dd')));
obj_wd = wordcom(fn0);
for i = 1:length(H)
    obj_wd.pasteFigure(H(i));
end
obj_wd.CloseWord();
xlstocsv_adair(fn2,sta_re); 
%{
sub_r sub_symbol_u*sub_t_u
sub_t_u n * 1
sub_symbol_u n*1
%}
function [sub_r,sub_t_u,sub_symbol_u] = get_interchgPct_us_polygon(sub_t1,sub_t2,sub_symbol)
    sprintf('开始载入polygon-阶段数据—%s-%s',sub_t1,sub_t2)
    T = length(sub_symbol);
    X = cell(T,1);
    ind = zeros(T,1);
    parfor i = 1:T
        tmp_symbol = sub_symbol{i};
        obj=yq_methods();
        x=get_polygon_chg(obj,tmp_symbol,sub_t1,sub_t2);
        if ~isempty(x)
            x = x(:,[3,7]);
            %v = zeros(size(sub_t_u));
            %[~,ia,ib] = intersect(sub_t_u,x(:,1));
            %v(ia) = cell2mat(x(ib,end));
            X{i} = x;
            ind(i) = 1;
        end
        %sprintf('get data of %s',tmp_symbol)
    end
    ind = eq(ind,1);
    X = X(ind);
    sub_symbol_u = sub_symbol(ind);
    sub_t_u = cellfun(@(x) x(:,1),X,'UniformOutput',false);
    sub_t_u = cellfun(@(x) x',sub_t_u,'UniformOutput',false);
    sub_t_u = unique([sub_t_u{:}])';
    T = length(sub_symbol_u);
    sub_r = cell(T,1);
    parfor i = 1:T
        x = X{i};
        tmp= cell2mat(x(:,2));
        
        tmp(2:end) = tmp(2:end)./tmp(1:end-1)-1;
        tmp(1) = 0;
        tmp(isnan(tmp)) = 0;
        x(:,2) = num2cell(tmp);
        
        v = zeros(size(sub_t_u));
        [~,ia,ib] = intersect(sub_t_u,x(:,1));
        v(ia) = cell2mat(x(ib,end));
        sub_r{i} = v;
    end
    sub_r = [sub_r{:}]';
    sprintf('完成载入polygon-阶段数据—%s-%s',sub_t1,sub_t2)
end
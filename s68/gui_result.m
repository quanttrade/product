function gui_result(y,t_str)
h = figure;
h.MenuBar='None';
y(cellfun(@isnumeric,y)) = cellfun(@(x) num2str(x,4),y(cellfun(@isnumeric,y)),'UniformOutput',false);
t = uitable(h,'Data',y,'unit','normalized','Position',[0,0,1,1]);
%temp = num2cell(1:13);
%temp = cellfun(@(x) sprintf('f%0.2d',x),temp,'UniformOutput',false);
%t.ColumnName = temp;

h.Name=sprintf('%s',t_str);
h.NumberTitle = 'off';
end
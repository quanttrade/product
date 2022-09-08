clear
x1 = load('SP500-ETE.mat');
x2 = load('SP500-DR.mat');
x1.tref1 = x1.tref1(datenum(x1.tref1)<=datenum(2015,12,31));
[tref1,ia,ib] = intersect(x1.tref1,x2.tref1);
r = [x1.r(ia,:),x2.r(ib,end)];
y_c = cumprod(1+r);
t_str = tref1;
T=length(t_str);
h=figure;
plot(y_c,'LineWidth',2);
set(gca,'xlim',[0,T]);
set(gca,'XTick',floor(linspace(1,T,15)));
set(gca,'XTickLabel',t_str(floor(linspace(1,T,15))));
set(gca,'XTickLabelRotation',90)    
setpixelposition(gcf,[223,365,1345,420]);
legend({'S&P 500 Full-Replication','ALAIT-ETE','ALAIT-DR'},'Location','best')
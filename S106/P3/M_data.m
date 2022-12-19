clear
%x = readtable('tmp.csv');
load tmp.mat

ind = eq(x.price_new_low,1);
plot(x.min,'o-')
hold on
plot(find(ind),x.min(ind),'*')


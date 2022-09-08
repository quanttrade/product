function m_end=is_month_end(t0)
%t0 = datenum(2021,2,26);
tmp = datevec(t0);
tmp2 = eomday(tmp(1),tmp(2));
tmp = datenum([tmp(1:2),tmp2]);
tmp1 = weekday(t0+1:tmp);
if isempty(tmp1)
    m_end=true;
else
    if all(eq(tmp1,7) |eq(tmp1,1))
        m_end = true;
    else
        m_end = false;
    end
end
import sys, numpy as np, pandas as pd
sys.path.insert(0,'.')
from arcframe import to_sn
tr=pd.read_csv('oi/tracks_hourly.csv',parse_dates=['time_utc'])
tr=tr[(tr.lat<-32.8)&(tr.lat>-37)&(tr.lon>91)&(tr.lon<96)].copy()
s,n=to_sn(tr.lon.values,tr.lat.values); tr['s']=s; tr['n']=n
tr.to_csv('oi/tracks_sn.csv',index=False)
tr['day']=tr.time_utc.dt.strftime('%Y-%m-%d')
g=tr.groupby(['leg','day']).agg(N=('s','size'),s_min=('s','min'),s_max=('s','max'),n_min=('n','min'),n_max=('n','max'),sog_med=('sog_kts','median'))
pd.set_option('display.width',200); print(g.round(1).to_string())

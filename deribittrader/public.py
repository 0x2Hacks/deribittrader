import json
import urllib.request
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import interpolate
from mpl_toolkits import mplot3d
from matplotlib.ticker import FuncFormatter
from mpl_toolkits.mplot3d import Axes3D

base_url = "https://deribit.com/api/v2/public/"

def request(url):
    with urllib.request.urlopen(base_url+url) as u:
        data = json.loads(u.read().decode())
    return data

def get_all_options():
    data = request("get_instruments?currency=BTC&kind=option&expired=false")
    data = pd.DataFrame(data['result']).set_index('instrument_name')
    data['creation_date'] = pd.to_datetime(data['creation_timestamp'], unit='ms')
    data['expiration_date'] = pd.to_datetime(data['expiration_timestamp'], unit='ms')
    return data

def get_all_active_options():
    active_options = get_all_options()
    price = get_tick_data('BTC-PERPETUAL')['last_price'][0]
    pc = active_options.index.str.strip().str[-1]
    active_options['m'] = np.log(active_options['strike']/price)
    active_options.loc[pc=='P','m'] = -active_options['m']
    active_options['t'] = (active_options['expiration_date']-pd.Timestamp.today()).dt.days
    active_options = active_options.query('m>0 & m<.3 & t<91 & t>7').sort_values('t')
    return active_options

def get_tick_data(instrument_name):
    data = request(f"ticker?instrument_name={instrument_name}")
    data = pd.json_normalize(data['result'])
    data.index = [instrument_name]
    return data

def get_option_data():
    options = get_all_active_options()
    res = []
    for o in options.index:
        res.append(get_tick_data(o))
    res = pd.concat(res)
    res['strike'] = options['strike']
    res['t'] = options['t']
    res['m'] = options['m']
    return res

def plot_curve():
    option_data = get_option_data().sort_values(['t','strike'])
    price = get_tick_data('BTC-PERPETUAL')['last_price'][0]
    x = option_data['strike']
    y = option_data['t']
    z = option_data['mark_iv']/100
    xyz = pd.DataFrame({'x':x,'y':y,'z':z})
    xyz = xyz.set_index('x')
    gp = xyz['z'].groupby(xyz['y'])
    res = {}
    for g in gp.groups.keys():
        res[g] = gp.get_group(g)
    res = pd.DataFrame(res)
    res.plot()
    plt.savefig("curve.png")
    return xyz

xyz = plot_curve()
print(xyz)
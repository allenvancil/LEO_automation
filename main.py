from scatter_plots_PL133 import scatter_plot_temp
from scatter_plots_PL133 import data_ranges
import pandas as pd 



col = 6

dataset = 'scope_log_11-06'

df = pd.read_csv(f'../data/{dataset}.csv')


###### df.columns   ###########################
###  [0 - 'Timestamp', 1 - 'Vppin', 2 - 'Vppout', 3 - 't-delay', 4 - 'TIE mean', 5 - 'TIE sigma', 6 - 'TIE min', 7 - 'TIE max', 8 - 'jitter_time_interval', 9 - 'temp', 10 - 'device']


################ setup to plot and copy plot to plots folder  ######################################

## def scatter_plot_temp(df, outpt, save_path=None, show=True):



path = f'../plots/{dataset}_{df.columns[col]}.png'  ## folder that plot will go to 

scatter_plt  = scatter_plot_temp(df, col, path, True)


min, max, range = data_ranges(df, col)

print(f'minumum {df.columns[col]} value is: {min}')
print(f'maximum {df.columns[col]} value is: {max}')
print(f'{df.columns[col]} range is: {range}')

vals = {
    'min': min,
    'max': max,
    'range': range
}

vals = pd.DataFrame([vals])

vals.to_csv(f'../plots/{dataset}_{df.columns[col]}.csv')

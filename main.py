from scatter_plots_PL133 import scatter_plot_temp
from scatter_plots_PL133 import data_ranges
import pandas as pd 


col_in = 1
col_out = 6
dte = '11-20'

dataset = 'DA_10MHz_squar_10-20prev'

df = pd.read_csv(f'../data/{dataset}.csv')
print("the dataset is = ")
print(df.head())
print("The input = ")
print(df.columns[col_in])
print("The output = ")
print(df.columns[col_out])



"""
0 Timestamp
1 Vppin
2 Vppout
3 t-delay
4 TIE sigma
5 3xsig
6 clkin_n_mV
7 N_jitter
8 jitter_time_interval
9 temp
10 device

"""
############### setup to plot and copy plot to plots folder  ######################################

# def scatter_plot_temp(df,inpt,outpt, save_path=None, show=True):



path = f'../plots/{df.columns[col_in]}_{df.columns[col_out]}_{dte}.png'  ## folder that plot will go to 

scatter_plt  = scatter_plot_temp(df,col_in,col_out, path, True)


min, max, range = data_ranges(df, col_out)

print(f'minumum {df.columns[col_out]} value is: {min}')
print(f'maximum {df.columns[col_out]} value is: {max}')
print(f'{df.columns[col_out]} range is: {range}')

vals = {
    'min': min,
    'max': max,
    'range': range
}

vals = pd.DataFrame([vals])

vals.to_csv(f'../plots/{df.columns[col_out]}_vs_{df.columns[col_in]}_{dte}.csv')

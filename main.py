from scatter_plots_PL133 import scatter_plot_temp
import pandas as pd 

df = pd.read_csv('../data/scope_log_11-06.csv')

scatter_plt = scatter_plot_temp(df, 4)
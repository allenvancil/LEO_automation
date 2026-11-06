import csv
import os
import time
from datetime import datetime

import pyvisa


# create a new CSV file with headers if it doesn't exist 
SCOPE_IP      = "192.168.0.90"
TEMPERATURE   = "25"              # degree C, need to manually input for every temp change
DEVICE    =  "LMK00105_A"          # device name, need to manually input for every device change,  input in row in the CSV file

CSV_PATH      = "scope_log.csv"     # appended to (created if missing)
SHOT_DIR      = "scope_shots"       # screen shots will be saved here

TIMEBASE_S_PER_DIV = 100e-9          # <-- set up the jitter time/div, most scopes 10 div of entire display, so 100 ns/div = 1 us window, 50 ns/div = 500 ns window, etc.
SCOPE_HDIVS        = 10             # 6 Series has 10 horizontal divisions

MEAS_SLOTS = {
    "Vpp_input_ch1":      1,        # Vpp_in on CH1
    "Vpp_output_ch2":     2,        # Vpp_out on CH2
    "delta_t_markers":    3,        # Δt between marker 1 & marker 2 (e.g. DELay)
    "jitter":             4,        # need to measure TIE sigma
    "jitter_min":         5,        # need to measure TIE min
    "jitter_max":         6,         # need to measure TIE max
       }      

######  JITTER MEASUREMENTS  ######
    # TIE measurements are typically done on a clock signal, so you may need to set up the scope to measure TIE on the appropriate channel.
    # The exact commands will depend on your scope model and its capabilities.

JITTER_SOURCE_CH = 2                 # channel to measure jitter on (CH2 = DUT output)
JITTER_TYPES = {
    "jitter":  "TIE",               # TIE jitter, measured over the set window
}

# CSV columns, in order, matching your request.
CSV_COLUMNS = [
    "Timestamp",
    "Vppin",
    "Vppout",
    "t-delay",
    "TIE sigma",
    "TIE min",
    "TIE max",
    "temp",       # the manual label you typed above
    "device"      # the manual label you typed above
]

TEK_NAN = 9.9e37   # Tektronix "no valid measurement" sentinel

#####   connect to the scope   #####
def connect(ip):
    rm = pyvisa.ResourceManager("@py")
    inst = rm.open_resource(f"TCPIP::{ip}::INSTR")
    inst.timeout = 20000
    inst.read_termination = "\n"
    inst.write_termination = "\n"
    return inst


def set_timebase(inst, s_per_div):
    """
    Set the horizontal timescale, then read back the ACTUAL value and return
    the full-screen acquisition window = scale * divisions. The jitter
    measurement window follows this directly.
    """
    inst.write(f"HORizontal:SCAle {s_per_div}")
    actual = float(inst.query("HORizontal:SCAle?").strip())   # actual s/div
    window = actual * SCOPE_HDIVS
    print(f"  timebase = {actual:g} s/div  ->  window = {window:g} s "
          f"({window*1e3:g} ms)")
    return window

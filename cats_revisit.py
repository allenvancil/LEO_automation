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
ACQ_SECONDS   = 5

JITTER_TIME_PERDIV = 100e-6          # <-- set up the jitter time/div, most scopes 10 div of entire display, so 100 ns/div = 1 us window, 50 ns/div = 500 ns window, etc.
SCOPE_HDIVS        = 10             # 6 Series has 10 horizontal divisions

MEAS_SLOTS = {
    "Vpp_input_ch1":      1,        # Vpp_in on CH1
    "Vpp_output_ch2":     2,        # Vpp_out on CH2
    "delta_t_markers":    3,        # Δt between marker 1 & marker 2 (e.g. DELay)
    "jitter":             4,        # need to measure TIE sigma, min, max, mean
       }      

######  JITTER MEASUREMENTS  ######
    # TIE measurements are typically done on a clock signal, so you may need to set up the scope to measure TIE on the appropriate channel.
    # The exact commands will depend on your scope model and its capabilities.

JITTER_SOURCE_CH = 2                # channel to measure jitter on (CH2 = DUT output)
JITTER_TYPES = [
    "jitter_mean", 
    "jitter_sigma", 
    "jitter_min",
    "jitter_max"
]

# CSV columns, in order, matching your request.
CSV_COLUMNS = [
    "Timestamp",
    "Vppin",
    "Vppout",
    "t-delay",
    "TIE mean",
    "TIE sigma",
    "TIE min",
    "TIE max",
    "jitter_time_interval",
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


def set_timebase(inst):
    """
    The purpose of this function is to record the current time window, print to terminal, and store it to return to after jitter measurements.
    
    """
    
    actual = float(inst.query("HORizontal:SCAle?").strip())   # actual s/div
    window = actual * SCOPE_HDIVS
    
    ## just printing to terminal preestblished time intveral
    print(f"  timebase = {actual:g} s/div  ->  window = {window:g} s "
          f"({window*1e3:g} ms)")
    return window

## this function read the preset measurement slot (1 - vppin, 2 - vppout, 3 - t-delay, etc) and input nan for failed
# measurements.

def read_meas(inst, slot):
    """Read a MEAS slot's current mean; map Tek's 9.9E37 sentinel to NaN."""
    try:
        raw = float(inst.query(
            f"MEASUrement:MEAS{slot}:RESUlts:CURRentacq:MEAN?").strip())
    except Exception as e:
        print(f"  ! MEAS{slot} read failed: {e}")
        return float("nan")
    if abs(raw) >= TEK_NAN * 0.99:
        return float("nan")
    return raw

## inputting nan to csv if not measure value

def fmt(v):
    """Format a value for CSV: blank-friendly NaN."""
    return "NaN" if v != v else f"{v:.6g}"

## this takes a screenshot of the intial display setup 

def take_screenshot(inst, path):
    """Save a PNG of the current scope display (waveforms, markers, meas)."""
    remote = "C:/Temp_shot.png"
    inst.write(f'FILESystem:DELEte "{remote}"')   # clear any stale file
    inst.query("*ESR?")                           # swallow possible error bit
    inst.write(f'SAVE:IMAGe "{remote}"')
    inst.query("*OPC?")                           # SAVE:IMAGe is OPC-generating
    saved = inst.timeout
    inst.timeout = 60000
    try:
        inst.write(f'FILESystem:READFile "{remote}"')
        img = inst.read_raw()
    finally:
        inst.timeout = saved
    with open(path, "wb") as f:
        f.write(img)
    inst.write(f'FILESystem:DELEte "{remote}"')


### Jitter setup ##############################
"""
jitter aquisition needs:
1. change time window to predecided interval, will give good gaussian-dist
2. hold for 5 sec to get suffient data points
3. query TIE in measurment slot 4, get sigma, min, max, and mean
4. write there in a csv in columns 5, 6, 7, 8

inst --> connection function

"""
## change time interval to predetermined jitter time window

def jitter_time_window(inst, time_window):

    ## set the time window for jitter measurement

    inst.write(f"HORizontal:SCAle {time_window}")
    inst.query("*OPC?")
    print(f"  time window = {time_window}")
    return time_window * SCOPE_HDIVS

## queries the TIE measurement from slot 4, setup in inital phase

def jitter_setup(inst):
    m = "MEASUrement:MEAS1"

    # 1. Set up TIE measurement
    m = f"MEASUrement:MEAS{MEAS_SLOTS['jitter']}"
# remove DELete:ALL, ADDMEAS, and SOUrce1 lines
    inst.query("*OPC?")

    # 2. Clear stats, run for ACQ_SECONDS, stop
    inst.write("ACQuire:STOPAfter RUNSTop")
    inst.write("ACQuire:STATE STOP")
    inst.write("CLEAR")
    inst.query("*OPC?")
    inst.write("ACQuire:STATE RUN")
    print(f"Collecting for {ACQ_SECONDS}s...")  ###  this tell how long jitter stat pts taken
    time.sleep(ACQ_SECONDS)
    inst.write("ACQuire:STATE STOP")
    inst.query("*OPC?")

    # 3. Query stats
    base = f"{m}:RESUlts:ALLAcqs"
    mean_v = float(inst.query(f"{base}:MEAN?"))
    sigma  = float(inst.query(f"{base}:STDDev?"))
    min_v  = float(inst.query(f"{base}:MINimum?"))
    max_v  = float(inst.query(f"{base}:MAXimum?"))
    print(f"TIE mean  : {mean_v*1e12:.3f} ps")
    print(f"TIE sigma : {sigma*1e12:.3f} ps")
    print(f"TIE min   : {min_v*1e12:.3f} ps")
    print(f"TIE max   : {max_v*1e12:.3f} ps")
    

    return mean_v, sigma, min_v, max_v

## run take screenshot function to record jitter window

## return to time interval window to inital value

def return_init_time_interval(inst, window):
    """
    Restore the horizontal timebase so the acquisition window equals `window` (seconds).
    `window` is the value returned by set_timebase().
    """
    s_per_div = window / SCOPE_HDIVS
    inst.write(f"HORizontal:SCAle {s_per_div}")
    inst.query("*OPC?")
    actual = float(inst.query("HORizontal:SCAle?").strip())
    restored = actual * SCOPE_HDIVS
    print(f"  timebase restored = {actual:g} s/div  ->  window = {restored:g} s "
          f"({restored*1e3:g} ms)")
    return restored


####### Operation functions complete################################

######### Sequence function##########################################
"""
1. manually step up intial scope window
2. connect to scope, save init time interval, set up csv
3. take initial screenshot
4. take measurement in slots 1, 2, 3 (Vppin, Vppout, t-delay)
5. change time interval for jitter measurements
6. take jitter measurements and screenshot
7. return to initial time interval
"""
def main():
    
    ## making directory for screenshots
    os.makedirs(SHOT_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # connect to scope
    inst = connect(SCOPE_IP)
    print("Connected:", inst.query("*IDN?").strip())
    time.sleep(2)
    
    def _safe(txt):
        return "".join(c if (c.isalnum() or c == "-") else "_" for c in txt).strip("_") 
    
    ## save initial time interval, query asking what is the current time interval in s/div
    original_tb = float(inst.query("HORizontal:SCAle?").strip())
    print(f"  original timebase = {original_tb:g} s/div (will restore on exit)")
    time.sleep(2)
    
    #########  this only measures the initial 3 slots (Vppin, Vppout, t-delay) and screenshot #################
    vals = {}
    for name, slot in MEAS_SLOTS.items():
        if name in JITTER_TYPES:
            continue                      # jitter is measured in Stage 2
        vals[name] = read_meas(inst, slot)  #output of above function
        print(f"  {name:22s} = {fmt(vals[name])}")
    time.sleep(2)
        
    # Input voltage = the MEASURED CH1 Vpp (at the original timebase).
    input_voltage = (f"{vals['Vpp_input_ch1']:.3f} Vpp"
                     if vals['Vpp_input_ch1'] == vals['Vpp_input_ch1']
                     else "NaN Vpp")
    
## lable screenshot with Vppin, temp, timestamp
    before_tag = f"{_safe(input_voltage)}_{_safe(TEMPERATURE)}"
    before_path = os.path.join(SHOT_DIR, f"bfr_{before_tag}_{ts}.png")
    take_screenshot(inst, before_path)
    print("Screenshot (before) ->", before_path)
    
    time.sleep(2)
############################################################################################
        # ========================================================================
    # STAGE 2 -- JITTER timebase: change the window, measure ONLY jitter.
    # ========================================================================
    
    ## will set preestablished jitter time window, print in terminal
    jitter_window_s = jitter_time_window(inst, JITTER_TIME_PERDIV)
    vals["jitter_time_interval"] = jitter_window_s    # give time interval value
    time.sleep(2)
    
    results = jitter_setup(inst)          # runs once: (mean, sigma, min, max)
    for name, value in zip(JITTER_TYPES, results):
        vals[name] = value
    ## print jitter stats to terminal
    for name, v in vals.items():
        print(f"  {name:22s} = {fmt(v)}")
        
    ## take screenshot of jitter window
    cond_tag = f"{_safe(input_voltage)}_{_safe(TEMPERATURE)}"
    after_path = os.path.join(SHOT_DIR, f"shot_{cond_tag}_{ts}_after.png")
    take_screenshot(inst, after_path)
    print("Screenshot (after)  ->", after_path)
    time.sleep(2)
    
    ### creating and/or appending measurement in vals to csv
    new_file = not os.path.exists(CSV_PATH)   ## CSV_PATH = "scope_log.csv"
    
    with open(CSV_PATH, "a", newline="") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(CSV_COLUMNS)
        w.writerow([
            ts,
            fmt(vals["Vpp_input_ch1"]),
            fmt(vals["Vpp_output_ch2"]),
            fmt(vals["delta_t_markers"]),
            fmt(vals["jitter_mean"]),
            fmt(vals["jitter_sigma"]),
            fmt(vals["jitter_min"]),
            fmt(vals["jitter_max"]),
            fmt(vals["jitter_time_interval"]),
            TEMPERATURE,
            DEVICE,
        ])
        print(f"Row appended -> {CSV_PATH}")
        
    
    inst.write(f"HORizontal:SCAle {original_tb}")
    print(f"  timebase restored to {original_tb:g} s/div")
    
    inst.close()

if __name__ == "__main__":
    main()
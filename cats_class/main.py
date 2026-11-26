import csv, os, time
from datetime import datetime
from scope import Scope, MEAS_SLOTS, JITTER_TYPES
from power_supply import PowerSupply
from signal_gen import SignalGen
from dmm import DMM
from pprint import pprint

################## Inital conditions #################################
# inputs adjusted often
SCREEN_SHOT_DIR = "../ss_10MHz_11-25"
CSV_PATH = "../log_10MHz_11-25.csv"
ACQ_SECONDS = 10
JITTER_TIME_PERDIV = 1e-6




TC_TYPE = "K"  # thermocouple type
DUT = "LMK00105"
PSU_CH = 2

# ... TEMPERATURE, DEVICE, CSV_PATH, SHOT_DIR, CLKIN_N as before ...
CSV_COLUMNS = ["timestamp", 
               "Vpp_in", 
               "Vpp_out", 
               "t-delay", 
               "jitter_sigma", 
               "jitter_3sigma", 
               "N-samples",
               "clk_n_VDC", 
               "temp", 
               "jitter_min",
               "jitter_max", 
               "range",
               "DUT"]

# specify instruments in use --
SCOPE_ON = True
PSU_ON = True
SGEN_ON = True
DMM_ON   = True


SCOPE_IP = "192.168.0.90"   # scope
PSU_IP   = "192.168.0.122"   # clk_n pwr supply
AFG_IP   = "192.168.0.184"   # sig gen 
DMM_IP  = "192.168.0.123"   # dmm, Tc




## puts NAN is if no value
def fmt(v):
    return "NaN" if v != v else f"{v:.6g}"

#########################################################################

######### Sequence function   ##########################################
"""
1. manually step up intial scope window
2. a. connect to scope, 
   b. save init time interval, 
   c. take measurement in slots 1, 2, 3 (Vppin, Vppout, t-delay)
   d. set up csv
3. take initial screenshot
4. take measurement in slots 1, 2, 3 (Vppin, Vppout, t-delay)
5. change time interval for jitter measurements
6. take jitter measurements and screenshot
7. return to initial time interval
"""



def main():
# make timestamp with date and time
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    
# 2a. connect to devices if present

    scope = Scope(SCOPE_IP) if SCOPE_ON else None
    psu   = PowerSupply(PSU_IP, PSU_CH) if PSU_ON else None
    afg   = SignalGen(AFG_IP) if SGEN_ON else None
    dmm   = DMM(DMM_IP) if DMM_ON else None

    for dev in (scope, psu, afg, dmm):
        if dev:
            dev.connect()
            time.sleep(2)
            print(f"connected to {dev}")
        else:
            print(f"  ! connection failed for {dev}")
    if dmm:
        dmm.setup_temperature(f"{TC_TYPE}")  # confirm Tc type
        
    print()
    print("finished connecting instruments...")
    time.sleep(1)
    print()      
# 2b. set up initial timebase
    original_tb = scope.get_timebase()  # save initial, manually set timebase to return to at finish.
    print(f"  original timebase = {original_tb:g} s/div")
    time.sleep(1)
    print()

# 2c. take measurement in slots 1, 2, 3 (Vppin, Vppout, t-delay);
# so vals for loop up to this point has vppin, vppout, t-delay, <skip jitter>, temp, clk_n_VDC
    vals = {}
    for name, slot in MEAS_SLOTS.items():
        if name == "jitter":
            continue
        vals[name] = scope.read_meas(slot)
    vals["temperature"] = dmm.read_temperature() if dmm else float("nan")
    time.sleep(2)
    print('connected to dmm...')
    print()
    vals["clk_n_VDC"] = psu.read_voltage() if psu else float("nan")
    time.sleep(2)
    print('connected to psu...')
    print()
    
# 2d. set up screen shot directory
   
    if not os.path.exists(SCREEN_SHOT_DIR):
            os.makedirs(SCREEN_SHOT_DIR)
            
    before_path = os.path.join(SCREEN_SHOT_DIR, f"before_{ts}.png")
    after_path  = os.path.join(SCREEN_SHOT_DIR, f"after_{ts}.png")
    print()
    print('created ss folder...')
    time.sleep(2)
    

# 3. take inital screenshot 
    scope.take_screenshot(before_path)          # build before_path as you do now
    print()
    print("took inital screen shot")
    print()
# 4. 
    vals["jitter_time_interval"] = scope.set_timebase(JITTER_TIME_PERDIV)  
    
# results from measure_jitter() output = mean, sigma, min, max, N
    results = scope.measure_jitter(ACQ_SECONDS)
    for name, value in zip(JITTER_TYPES, results):
        vals[name] = value
    vals['jitter_3sigma'] = vals["jitter_sigma"] * 3
    vals['range'] = vals['jitter_max'] - vals['jitter_min']
#vals at this point should be = Vppin, Vppout, t-delay, temp, clk_n, mean, sigma, min, max, N, 3sigma, range
    
        
    print()
    print('this is the vals measurement set = ')
    print()
    pprint(vals)
# prints vals dict to terminal...

# takes a screenshot of jitter measurement time window
    scope.take_screenshot(after_path)
    
    # ... CSV writing exactly as you have it ...
    
    print()
    print("appending vals measurements to csv...")
    print()
    time.sleep(1)
    
    #create summary csv  
    new_file = not os.path.exists(CSV_PATH)     
    with open(CSV_PATH, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        if new_file:
    # write headers
            writer.writerow(CSV_COLUMNS)
    #write data
        writer.writerow([
            ts,
            fmt(vals["Vpp_input_ch1"]),
            fmt(vals["Vpp_output_ch2"]),
            fmt(vals["t_delay"]),
            fmt(vals["jitter_sigma"]),
            fmt(vals["jitter_3sigma"]),
            fmt(vals["sample_size"]),
            fmt(vals["clk_n_VDC"]),
            fmt(vals["temperature"]),
            fmt(vals["jitter_min"]),
            fmt(vals["jitter_max"]),
            fmt(vals["range"]),
            DUT
        ])
      
    print(f"Row appended -> {CSV_PATH}")
    print()
    scope.run()
    scope.set_timebase(original_tb)
    
    
    for dev in (scope, psu, afg, dmm):
           if dev:
               dev.close()

if __name__ == "__main__":
    main()
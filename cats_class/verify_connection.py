# check_connections.py
from scope import Scope
from power_supply import PowerSupply
from signal_gen import SignalGen
from dmm import DMM
import time

SCOPE_ON = True
PSU_ON   = True
SGEN_ON  = True
DMM_ON   = True

SCOPE_IP = "192.168.0.90"   # scope
PSU_IP   = "192.168.0.122"   # clk_n pwr supply
AFG_IP   = "192.168.0.184"   # sig gen 
DMM_IP  = "192.168.0.123"   # dmm, Tc

devices = {
    "Scope": Scope(SCOPE_IP)       if SCOPE_ON else None,
    "PSU":   PowerSupply(PSU_IP, 2)   if PSU_ON   else None,
    "AFG":   SignalGen(AFG_IP)     if SGEN_ON  else None,
    "DMM":   DMM(DMM_IP)           if DMM_ON   else None,
}

for name, dev in devices.items():
    if dev is None:
        print(f"{name:6s} skipped")
        continue
    try:
        dev.connect()                 # connect() already prints *IDN?
        print(f"{name:6s} OK")
        
        if name == "DMM":
            dev.setup_temperature("K")
            time.sleep(5)
            print("the temp is  = \n", dev.read_temperature())
        if name == "PSU":
            time.sleep(2)
            print("the psu voltage  = \n", dev.read_voltage())
        if name == "AFG":
            time.sleep(2)
            print("the freq is  = \n", dev.read_freq())
            print("the amp is  = \n", dev.read_amplitude())
        
        dev.close()
    except Exception as e:
        print(f"{name:6s} FAILED ({dev.ip}): {e}")
        
        

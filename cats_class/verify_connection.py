# check_connections.py
from scope import Scope
from power_supply import PowerSupply
from signal_gen import SignalGen
from dmm import DMM

SCOPE_ON = True
PSU_ON   = False
SGEN_ON  = False
DMM_ON   = False

SCOPE_IP = "192.168.0.90"
PSU_IP   = "192.168.0.91"
AFG_IP   = "192.168.0.92"
DMM_IP   = "192.168.0.93"

devices = {
    "Scope": Scope(SCOPE_IP)       if SCOPE_ON else None,
    "PSU":   PowerSupply(PSU_IP)   if PSU_ON   else None,
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
        dev.close()
    except Exception as e:
        print(f"{name:6s} FAILED ({dev.ip}): {e}")
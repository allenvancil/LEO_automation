import time
from main import main
from scope import Scope
from power_supply import PowerSupply
from signal_gen import SignalGen
from dmm import DMM

RUNS = 5
T_INTERVAL = 60 *.5  #time in sec
TC_TYPE = "T"
PSU_CH = 1
CONDITIONS = [               # (AFG amplitude Vpp, clkin* VDC)
    (1.297, .950),           # V_high: find Vpp on siggen gives 1.9Vpp on scope, find highest clkin* VDC stable output 
    (.881, .533)             # V_low: find lowest Vpp on siggen that give stable output, find highest clkin* VDC stable output
]

#------------------- specify instruments in use ------------------------
SCOPE_ON = True
PSU_ON = True
SGEN_ON = True
DMM_ON   = True


SCOPE_IP = "192.168.0.90"   # scope
PSU_IP   = "192.168.0.122"   # clk_n pwr supply
AFG_IP   = "192.168.0.184"   # sig gen 
DMM_IP  = "192.168.0.123"   # dmm, Tc


scope = Scope(SCOPE_IP) if SCOPE_ON else None
psu   = PowerSupply(PSU_IP, PSU_CH) if PSU_ON else None
afg   = SignalGen(AFG_IP) if SGEN_ON else None
dmm   = DMM(DMM_IP) if DMM_ON else None
#------------------  Finished specifying devices  -------------------------------------
print()
print("connecting to instruments...")
print()
for dev in (scope, psu, afg, dmm):
    if dev:
        dev.connect()
        time.sleep(2)
        print(f"connected to {dev}")
        time.sleep(2)
    else:
        print(f"  ! connection failed for {dev}")
if dmm:
    dmm.setup_temperature(f"{TC_TYPE}")  # confirm Tc type
    print(f"Using {TC_TYPE} type thermocouple")
    time.sleep(1)
    
print()
print("finished connecting instruments...")
time.sleep(1)


# --------------------------- change sig gen and psu  ---------------------------------------
try:
    for siggen_amp, clkin_vdc in CONDITIONS:
        if afg and psu:
            afg.set_amplitude(siggen_amp)
            psu.set_voltage(clkin_vdc)
            print(f"Set AFG = {siggen_amp} Vpp, PSU = {clkin_vdc} V")
            time.sleep(5)
# ------------  runs the main script once parameters initalized-----------------------------
        for i in range(RUNS):
            print()
            print(f"---------- start Run {i+1} of {RUNS} ----------")
            print()
            main(scope, psu, afg, dmm)
            print()
            if i < RUNS - 1:
                print(f"The next run will start in {T_INTERVAL} seconds")
                time.sleep(T_INTERVAL)
                    
            else:
                print(f"Finshed runs for {siggen_amp} Vpp, {clkin_vdc} VDC ----------")
                print(f"wait {T_INTERVAL} for next RUN or finish...")
                time.sleep(T_INTERVAL)
        
finally:
    for dev in (scope, psu, afg, dmm):
        if dev:
            dev.close()
            print()
            print(f"closed {dev}")
            time.sleep(2)
print()
print("All done!")
print()

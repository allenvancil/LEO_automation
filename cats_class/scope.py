import time
import pyvisa

TEK_NAN = 9.9e37
SCOPE_HDIV = 10

MEAS_SLOTS = {
    "Vpp_input_ch1": 1,
    "Vpp_output_ch2": 2,
    "t_delay": 3,
    "jitter" : 4
}

JITTER_TYPES = [
    "jitter_mean",
    "jitter_sigma",
    "jitter_min",
    "jitter_max",
    "sample_size"
]

class Scope:
    def __init__(self, ip):
        self.ip = ip
        self.inst = None
        
# connect to scope

    def connect(self):
        rm = pyvisa.ResourceManager("@py")
        self.inst = rm.open_resource(f"TCPIP::{self.ip}::INSTR")
        self.inst.timeout = 20000
        self.inst.read_termination = "\n"
        self.inst.write_termination = "\n"
        print("Connected:", self.inst.query("*IDN?").strip())
        
    def close(self):
        self.inst.close()
        
    def get_timebase(self):
        return float(self.inst.query("HORizontal:SCAle?").strip())
    
    def set_timebase(self, s_per_div):
        self.inst.write(f"HORizontal:SCAle {s_per_div}")  # input from main.py as JITTER_TIME_PERDIV init, then from "original_tb"
        self.inst.query("*OPC?")
        print(f"  timebase = {s_per_div:g} s/div")
        jitter_time_interval = s_per_div * SCOPE_HDIV
        return jitter_time_interval          # SCOPE_HDIVS input from main.py 
    
    def read_meas(self, slot):
        try:
            raw = float(self.inst.query(
                f"MEASUrement:MEAS{slot}:RESUlts:CURRentacq:MEAN?").strip())
        except Exception as e:
            print(f"  ! MEAS{slot} read failed: {e}")
            return float("nan")
        return float("nan") if abs(raw) >= TEK_NAN * 0.99 else raw

    def take_screenshot(self, path):
        remote = "C:/Temp_shot.png"
        self.inst.write(f'FILESystem:DELEte "{remote}"')
        self.inst.query("*ESR?")
        self.inst.write(f'SAVE:IMAGe "{remote}"')
        self.inst.query("*OPC?")
        saved = self.inst.timeout
        self.inst.timeout = 60000
        try:
            self.inst.write(f'FILESystem:READFile "{remote}"')
            img = self.inst.read_raw()
        finally:
            self.inst.timeout = saved
        with open(path, "wb") as f:
            f.write(img)
        self.inst.write(f'FILESystem:DELEte "{remote}"')

    def measure_jitter(self, acq_seconds):
        base = f"MEASUrement:MEAS{MEAS_SLOTS['jitter']}:RESUlts:ALLAcqs"
        self.inst.write("ACQuire:STOPAfter RUNSTop")
        self.inst.write("ACQuire:STATE STOP")
        self.inst.write("CLEAR")
        self.inst.query("*OPC?")
        self.inst.write("ACQuire:STATE RUN")
        print(f"Collecting for {acq_seconds}s...")
        time.sleep(acq_seconds)
        self.inst.write("ACQuire:STATE STOP")
        self.inst.query("*OPC?")
        mean_v = float(self.inst.query(f"{base}:MEAN?"))
        sigma  = float(self.inst.query(f"{base}:STDDev?"))
        min_v  = float(self.inst.query(f"{base}:MINimum?"))
        max_v  = float(self.inst.query(f"{base}:MAXimum?"))
        n      = int(float(self.inst.query(f"{base}:POPUlation?")))
        print()
        print(f"TIE sigma: {sigma*1e12:.3f} ps  (n={n})")
        time.sleep(2)
        return mean_v, sigma, min_v, max_v, n

    def run(self):
        self.inst.write("ACQuire:STATE RUN")
# power_supply.py
import pyvisa

class PowerSupply:
    def __init__(self, ip):
        self.ip = ip
        self.inst = None

    def connect(self):
        rm = pyvisa.ResourceManager("@py")
        self.inst = rm.open_resource(f"TCPIP::{self.ip}::INSTR")
        self.inst.read_termination = "\n"
        self.inst.write_termination = "\n"
        print("Connected:", self.inst.query("*IDN?").strip())

    def set_voltage(self, volts):
        self.inst.write(f"VOLT {volts}")
        
    def read_voltage(self):
        try:
            return float(self.inst.query("MEAS:VOLT?").strip())
        except:
            return float("nan")
        
    def read_current(self):
        try:
            return float(self.inst.query("MEAS:CURR?").strip())
        except:
            return float("nan")

    def output(self, on):
        self.inst.write("OUTP ON" if on else "OUTP OFF")

    def close(self):
        self.inst.close()
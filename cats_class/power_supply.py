# power_supply.py
import pyvisa

class PowerSupply:
    def __init__(self, ip, channel=1):
        self.ip = ip
        self.ch = f"(@{channel})"     # (@1) or (@2)
        self.inst = None

    def connect(self):
        rm = pyvisa.ResourceManager("@py")
        self.inst = rm.open_resource(f"TCPIP::{self.ip}::INSTR")
        self.inst.read_termination = "\n"
        self.inst.write_termination = "\n"
        print("Connected:", self.inst.query("*IDN?").strip())

    def set_voltage(self, volts):
        self.inst.write(f"VOLT {volts},{self.ch}")

    def read_voltage(self):
        try:
            return float(self.inst.query(f"MEAS:VOLT? {self.ch}").strip())
        except Exception:
            return float("nan")

    def read_current(self):
        try:
            return float(self.inst.query(f"MEAS:CURR? {self.ch}").strip())
        except Exception:
            return float("nan")

    def output(self, on):
        self.inst.write(f"OUTP {'ON' if on else 'OFF'},{self.ch}")

    def close(self):
        self.inst.close()
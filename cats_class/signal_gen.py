# signal_gen.py
import pyvisa

class SignalGen:
    def __init__(self, ip):
        self.ip = ip
        self.inst = None

    def connect(self):
        rm = pyvisa.ResourceManager("@py")
        self.inst = rm.open_resource(f"TCPIP::{self.ip}::INSTR")
        self.inst.read_termination = "\n"
        self.inst.write_termination = "\n"
        print("Connected:", self.inst.query("*IDN?").strip())

    def set_frequency(self, hz):
        self.inst.write(f"SOURce1:FREQuency {hz}")

    def set_amplitude(self, vpp):
        self.inst.write(f"SOURce1:VOLTage {vpp}")
        
    def read_freq(self):
        return float(self.inst.query("SOURce1:FREQuency?").strip())
    
    def read_amplitude(self):
        return float(self.inst.query("SOURce1:VOLTage?").strip())

    def output(self, on):
        self.inst.write("OUTPut1 ON" if on else "OUTPut1 OFF")

    def close(self):
        self.inst.close()
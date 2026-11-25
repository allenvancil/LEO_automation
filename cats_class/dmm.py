import pyvisa

class DMM:
    def __init__(self, ip):
        self.ip = ip
        self.inst = None

    def connect(self):
        rm = pyvisa.ResourceManager("@py")
        self.inst = rm.open_resource(f"TCPIP::{self.ip}::INSTR")
        self.inst.timeout = 10000
        self.inst.read_termination = "\n"
        self.inst.write_termination = "\n"
        print("Connected:", self.inst.query("*IDN?").strip())

    def setup_temperature(self, tc_type="K"):
        self.inst.write('SENS:FUNC "TEMP"')
        self.inst.write("SENS:TEMP:TRAN TC")              # thermocouple
        self.inst.write(f"SENS:TEMP:TC:TYPE {tc_type}")   # K, J, T, etc.
        self.inst.write("SENS:TEMP:UNIT CELS")  # units in Celsius

    def read_temperature(self):
        try:
            return float(self.inst.query("READ?").strip())
        except Exception as e:
            print(f"  ! DMM read failed: {e}")
            return float("nan")

    def close(self):
        self.inst.close()
# pip install pyvisa pyvisa-py
import time
import pyvisa

SCOPE_IP = "192.168.1.10"  # <-- change to your Series 6 scope IP
MEAS_SLOT = 1              # MEAS1 assumed to be TIE
SOURCE_CH = "CH1"
ACQ_SECONDS = 5
SCOPE_IMG_PATH = "C:/Temp/screenshot.png"
PC_IMG_PATH = "screenshot.png"

def main():
    rm = pyvisa.ResourceManager()
    scope = rm.open_resource(f"TCPIP::{SCOPE_IP}::INSTR")
    scope.timeout = 15000
    scope.chunk_size = 1024 * 1024
    scope.encoding = "latin-1"

    print(scope.query("*IDN?").strip())

    # 1. Ensure scope is running
    scope.write("ACQuire:STATE RUN")

    # 2. Setup TIE measurement on MEAS slot
    m = f"MEASUrement:MEAS{MEAS_SLOT}"
    scope.write(f"{m}:TYPE TIE")
    scope.write(f"{m}:SOURCE {SOURCE_CH}")
    scope.write(f"{m}:STATE ON")
    scope.query("*OPC?")

    # 3. Clear stats and collect for 5 seconds
    scope.write("MEASUrement:STATIstics:RESET")
    scope.query("*OPC?")
    print(f"Collecting for {ACQ_SECONDS}s...")
    time.sleep(ACQ_SECONDS)

    # 4. Query sigma / min / max
    sigma = scope.query(f"{m}:RESUlts:ALLAcqs:STDdev?").strip()
    min_v = scope.query(f"{m}:RESUlts:ALLAcqs:MINimum?").strip()
    max_v = scope.query(f"{m}:RESUlts:ALLAcqs:MAXimum?").strip()
    mean_v = scope.query(f"{m}:RESUlts:ALLAcqs:MEAN?").strip()

    print(f"TIE mean  : {mean_v} s")
    print(f"TIE sigma : {sigma} s")
    print(f"TIE min   : {min_v} s")
    print(f"TIE max   : {max_v} s")

    # 5. Screenshot to scope disk, then transfer to PC
    scope.write("SAVE:IMAGE:FILEFormat PNG")
    scope.write("SAVE:IMAGE:INCLUDESCreen ON")
    scope.write(f'SAVE:IMAGE "{SCOPE_IMG_PATH}"')
    scope.query("*OPC?")

    scope.write("HARDCopy:PORT FILE")
    scope.write(f'HARDCopy:FILENAMe "{SCOPE_IMG_PATH}"')
    scope.write("HARDCopy STARt")
    scope.query("*OPC?")
    time.sleep(1)

    raw = scope.query_binary_values(
        f'FILESystem:READFile "{SCOPE_IMG_PATH}"',
        datatype="B",
        container=bytearray
    )
    with open(PC_IMG_PATH, "wb") as f:
        f.write(raw)

    print(f"Saved screenshot to {PC_IMG_PATH}")
    scope.close()

if __name__ == "__main__":
    main()
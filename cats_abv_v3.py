#!/usr/bin/env python3
###############################################################################
# Scope Capture — simple, standalone CSV + screenshot logger
#
# Reads the measurements you ALREADY set up on the Tek MSO68B, appends one row
# to a CSV, and saves a screenshot labelled with the input voltage + temp you
# type in by hand below. No sig-gen / DMM control — scope only.
#
# Run (over SSH on the NUC):   python3 scope_capture.py
# Each run appends ONE row to scope_log.csv and saves ONE screenshot.
###############################################################################

import csv
import os
import time
from datetime import datetime

import pyvisa

# ============================================================================
#  EDIT THESE BY HAND EACH RUN
# ============================================================================
SCOPE_IP      = "192.168.0.90"      # MSO68B
# INPUT_VOLTAGE is no longer entered by hand -- it is taken from the
# measured CH1 Vpp at run time. Only TEMPERATURE is still manual.
TEMPERATURE   = "25 C"              # <-- type the temperature you set
CSV_PATH      = "scope_log.csv"     # appended to (created if missing)
SHOT_DIR      = "scope_shots"       # screenshots saved here

# Jitter measurement WINDOW is driven by the horizontal timescale you set
# here. The 6 Series has 10 horizontal divisions, so:
#     window = TIMEBASE_S_PER_DIV * 10
# e.g. 1e-3 s/div -> 10 ms window. Change this knob to change the window;
# the "jitter time interval" column reports the ACTUAL window read back
# from the scope, and TIE jitter is measured over that span.
TIMEBASE_S_PER_DIV = 100e-9          # <-- set your jitter window here (1ms/div = 10ms)
SCOPE_HDIVS        = 10             # 6 Series has 10 horizontal divisions

# Which scope MEASUrement slot (MEAS<n>) holds each quantity.
# Set these to match the measurements/markers you configured on the scope.
MEAS_SLOTS = {
    "Vpp_input_ch1":      1,        # PK2Pk on CH1
    "Vpp_output_ch2":     2,        # PK2Pk on CH2
    "delta_t_markers":    3,        # Δt between marker 1 & marker 2 (e.g. DELay)
    "jitter":             4,        # TIE jitter RMS over the measurement window
}
# NOTE: "jitter time interval" is NOT a scope measurement -- it is the
# measurement WINDOW (timescale * divisions), reported from the timebase.

# --- Jitter setup -----------------------------------------------------------
# MSO68B firmware FV 2.14.3 accepts TIE and CCJitter, but NOT the generic
# "JITTer" type (diagnostic confirmed: 141 Invalid enumeration). The script
# configures these two slots itself so the type is always valid.
#   "jitter"               -> CCJitter  (cycle-to-cycle jitter)
#   "jitter_time_interval" -> TIE       (time interval error)
JITTER_SOURCE_CH = 2                 # channel to measure jitter on (CH2 = DUT output)
JITTER_TYPES = {
    "jitter":  "TIE",               # TIE jitter, measured over the set window
}

# CSV columns, in order, matching your request.
CSV_COLUMNS = [
    "Timestamp",
    "Vpp_input (ch1)",
    "Vpp_output (CH2)",
    "delta t between markers",
    "jitter",
    "jitter time interval",
    "input_voltage",       # the manual label you typed above
    "temperature",         # the manual label you typed above
]
# ============================================================================

TEK_NAN = 9.9e37   # Tektronix "no valid measurement" sentinel


def connect(ip):
    rm = pyvisa.ResourceManager("@py")
    inst = rm.open_resource(f"TCPIP::{ip}::INSTR")
    inst.timeout = 20000
    inst.read_termination = "\n"
    inst.write_termination = "\n"
    return inst


def set_timebase(inst, s_per_div):
    """
    Set the horizontal timescale, then read back the ACTUAL value and return
    the full-screen acquisition window = scale * divisions. The jitter
    measurement window follows this directly.
    """
    inst.write(f"HORizontal:SCAle {s_per_div}")
    actual = float(inst.query("HORizontal:SCAle?").strip())   # actual s/div
    window = actual * SCOPE_HDIVS
    print(f"  timebase = {actual:g} s/div  ->  window = {window:g} s "
          f"({window*1e3:g} ms)")
    return window


def read_meas(inst, slot):
    """Read a MEAS slot's current mean; map Tek's 9.9E37 sentinel to NaN."""
    try:
        raw = float(inst.query(
            f"MEASUrement:MEAS{slot}:RESUlts:CURRentacq:MEAN?").strip())
    except Exception as e:
        print(f"  ! MEAS{slot} read failed: {e}")
        return float("nan")
    if abs(raw) >= TEK_NAN * 0.99:
        return float("nan")
    return raw


def fmt(v):
    """Format a value for CSV: blank-friendly NaN."""
    return "NaN" if v != v else f"{v:.6g}"


def take_screenshot(inst, path):
    """Save a PNG of the current scope display (waveforms, markers, meas)."""
    remote = "C:/Temp_shot.png"
    inst.write(f'FILESystem:DELEte "{remote}"')   # clear any stale file
    inst.query("*ESR?")                           # swallow possible error bit
    inst.write(f'SAVE:IMAGe "{remote}"')
    inst.query("*OPC?")                           # SAVE:IMAGe is OPC-generating
    saved = inst.timeout
    inst.timeout = 60000
    try:
        inst.write(f'FILESystem:READFile "{remote}"')
        img = inst.read_raw()
    finally:
        inst.timeout = saved
    with open(path, "wb") as f:
        f.write(img)
    inst.write(f'FILESystem:DELEte "{remote}"')


def label_scope(inst, text):
    """Put the manual input-voltage/temperature label on the screen."""
    text = text[:30]                              # keep it short
    # Uses CH1's label; moves it to a fixed bottom-center spot each run.
    inst.write(f'CH1:LABel:NAMe "{text}"')
    inst.write("CH1:LABel:FONT:SIZE 24")
    inst.write("CH1:LABel:XPOS 0")
    inst.write("CH1:LABel:YPOS -4")


def setup_amp_meas(inst):
    """
    Ensure the Vpp (PK2Pk) and delay measurements exist as on-screen MEAS
    badges so they show up in the screenshot. ADDMEAS creates the slot if it
    is not already present; setting TYPe/SOUrce makes it a visible measurement.
    """
    # Vpp input on CH1
    inst.write(f"MEASUrement:ADDMEAS MEAS{MEAS_SLOTS['Vpp_input_ch1']}")
    inst.write(f"MEASUrement:MEAS{MEAS_SLOTS['Vpp_input_ch1']}:TYPe PK2Pk")
    inst.write(f"MEASUrement:MEAS{MEAS_SLOTS['Vpp_input_ch1']}:SOUrce1 CH1")
    # Vpp output on CH2
    inst.write(f"MEASUrement:ADDMEAS MEAS{MEAS_SLOTS['Vpp_output_ch2']}")
    inst.write(f"MEASUrement:MEAS{MEAS_SLOTS['Vpp_output_ch2']}:TYPe PK2Pk")
    inst.write(f"MEASUrement:MEAS{MEAS_SLOTS['Vpp_output_ch2']}:SOUrce1 CH2")
    inst.query("*ESR?")      # clear/confirm (Tek-safe, no hang)


def setup_jitter(inst):
    """
    Configure the two jitter MEAS slots with valid types for this firmware.

    IMPORTANT (MSO68B FW 2.14.3): statistics are ALWAYS ON -- there is NO
    enable command. Every STATIstics:* keyword returns 113 (undefined header).
    Jitter RMS comes from RESUlts:ALLAcqs:STDDev? after several acquisitions.
    """
    for name, mtype in JITTER_TYPES.items():
        slot = MEAS_SLOTS[name]
        inst.write(f"MEASUrement:ADDMEAS MEAS{slot}")          # ensure slot exists
        inst.write(f"MEASUrement:MEAS{slot}:TYPe {mtype}")     # CCJitter / TIE
        inst.write(f"MEASUrement:MEAS{slot}:SOUrce1 CH{JITTER_SOURCE_CH}")
    inst.query("*ESR?")      # clear/confirm (no hang -- Tek-safe)


def populate_stats(inst, n_acq: int = 20, timeout_s: float = 5.0):
    """
    Run several single-sequence acquisitions so the all-acquisitions statistics
    buffer fills. ALLAcqs:STDDev? needs population > 0; a single acquisition
    leaves it empty (that was the earlier NaN).
    """
    for _ in range(n_acq):
        inst.write("ACQuire:STOPAfter SEQuence")
        inst.write("ACQuire:STATE ON")
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            if inst.query("ACQuire:STATE?").strip() in ("0", "OFF"):
                break
            time.sleep(0.05)


def read_jitter_rms(inst, slot):
    """
    Read jitter RMS from stats over ALL acquisitions. Confirmed working on this
    firmware (returned e.g. 412.68e-15 s). Map Tek's 9.9E37 sentinel to NaN.
    """
    try:
        raw = float(inst.query(
            f"MEASUrement:MEAS{slot}:RESUlts:ALLAcqs:STDDev?").strip())
    except Exception as e:
        print(f"  ! MEAS{slot} jitter read failed: {e}")
        return float("nan")
    if abs(raw) >= TEK_NAN * 0.99:
        return float("nan")
    return raw


def main():
    os.makedirs(SHOT_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    inst = connect(SCOPE_IP)
    print("Connected:", inst.query("*IDN?").strip())

    def _safe(txt):
        return "".join(c if (c.isalnum() or c == "-") else "_" for c in txt).strip("_")

    # Remember the scope's current timebase so we can restore it on exit --
    # we only widen it temporarily for the jitter stage.
    original_tb = float(inst.query("HORizontal:SCAle?").strip())
    print(f"  original timebase = {original_tb:g} s/div (will restore on exit)")

    # Make sure the Vpp input/output + delay measurements are shown on screen.
    setup_amp_meas(inst)

    # ========================================================================
    # STAGE 1 -- ORIGINAL timebase: read everything EXCEPT jitter.
    # The marker delay (Δt) depends on the horizontal timescale, so it MUST be
    # measured at your original timebase, BEFORE we widen the window for jitter.
    # ========================================================================
    time.sleep(0.3)                       # let measurements settle
    vals = {}
    for name, slot in MEAS_SLOTS.items():
        if name in JITTER_TYPES:
            continue                      # jitter is measured in Stage 2
        vals[name] = read_meas(inst, slot)

    # Input voltage = the MEASURED CH1 Vpp (at the original timebase).
    input_voltage = (f"{vals['Vpp_input_ch1']:.3f} Vpp"
                     if vals['Vpp_input_ch1'] == vals['Vpp_input_ch1']
                     else "NaN Vpp")

    # Label + "BEFORE" screenshot at the original timebase (shows Vpp + Δt).
    label_scope(inst, f"{input_voltage}  {TEMPERATURE}")
    time.sleep(0.2)
    before_tag = f"{_safe(input_voltage)}_{_safe(TEMPERATURE)}"
    before_path = os.path.join(SHOT_DIR, f"bfr_{before_tag}_{ts}.png")
    take_screenshot(inst, before_path)
    print("Screenshot (before) ->", before_path)

    # ========================================================================
    # STAGE 2 -- JITTER timebase: change the window, measure ONLY jitter.
    # ========================================================================
    jitter_window_s = set_timebase(inst, TIMEBASE_S_PER_DIV)
    vals["jitter_time_interval"] = jitter_window_s    # the window, not a reading

    setup_jitter(inst)
    populate_stats(inst, n_acq=20)        # fill the all-acqs stats buffer
    for name in JITTER_TYPES:
        vals[name] = read_jitter_rms(inst, MEAS_SLOTS[name])

    for name, v in vals.items():
        print(f"  {name:22s} = {fmt(v)}")

    # "AFTER" screenshot: jitter window + populated jitter measurement.
    cond_tag = f"{_safe(input_voltage)}_{_safe(TEMPERATURE)}"
    after_path = os.path.join(SHOT_DIR, f"shot_{cond_tag}_{ts}_after.png")
    take_screenshot(inst, after_path)
    print("Screenshot (after)  ->", after_path)

    # Append one row to the CSV (write header if the file is new).
    new_file = not os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(CSV_COLUMNS)
        w.writerow([
            ts,
            fmt(vals["Vpp_input_ch1"]),
            fmt(vals["Vpp_output_ch2"]),
            fmt(vals["delta_t_markers"]),
            fmt(vals["jitter"]),
            fmt(vals["jitter_time_interval"]),
            input_voltage,
            TEMPERATURE,
        ])
    print(f"Row appended -> {CSV_PATH}")

    # Restore the scope to the timebase it had when we started.
    inst.write(f"HORizontal:SCAle {original_tb}")
    print(f"  timebase restored to {original_tb:g} s/div")

    inst.close()


if __name__ == "__main__":
    main()

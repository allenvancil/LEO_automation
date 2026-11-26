


CONDITIONS = [
    # (AFG amplitude Vpp, PSU voltage V)
    (2.0, 1.20),
    (1.5, 1.00),
]
RUNS_PER_CONDITION = 5
INTERVAL_S = 5 * 60
SETTLE_S = 10            # let the DUT settle after a change


def set_conditions(vpp, volts):
    afg = SignalGen(AFG_IP)
    psu = PowerSupply(PSU_IP, PSU_CH)
    afg.connect(); psu.connect()

    afg.set_amplitude(vpp)
    afg.output(True)
    psu.set_voltage(volts)
    psu.output(True)
    print(f"Set AFG = {vpp} Vpp, PSU = {volts} V")

    afg.close(); psu.close()
    time.sleep(SETTLE_S)


if __name__ == "__main__":
    for vpp, volts in CONDITIONS:
        set_conditions(vpp, volts)
        for i in range(RUNS_PER_CONDITION):
            start = time.time()
            print(f"\n===== {vpp} Vpp / {volts} V : run {i+1} of {RUNS_PER_CONDITION} =====")
            try:
                main()
            except Exception as e:
                print(f"Run failed: {e}")
            if i < RUNS_PER_CONDITION - 1:
                wait = INTERVAL_S - (time.time() - start)
                if wait > 0:
                    time.sleep(wait)
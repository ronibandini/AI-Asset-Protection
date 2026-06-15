# Rubik Pi 3 - PIR + RCWL-0516 + MLX90614
# Roni Bandini @RoniBandini

import time
import smbus
from periphery import GPIO

PIR_GPIO    = 652
RCWL_GPIO   = 558

MLX90614_ADDR = 0x5A
MLX90614_REG_AMBIENT = 0x06
MLX90614_REG_OBJECT  = 0x07

I2C_BUS = 1


def _read_temp(bus, reg):
    raw = bus.read_word_data(MLX90614_ADDR, reg)
    return raw * 0.02 - 273.15


def read_sensors():
    """
    Single-shot sensor read. Opens GPIO/I2C, samples once, closes.
    Returns a dict:
        {
            "pir":      bool,   # PIR motion state
            "microwave": bool,  # RCWL-0516 microwave motion state
            "ambient":  float,  # ambient temperature in °C
            "object":   float,  # object (wrist/watch) temperature in °C
        }
    ambient and object are None if the MLX90614 cannot be read.
    """
    pir  = GPIO(PIR_GPIO,  "in")
    rcwl = GPIO(RCWL_GPIO, "in")
    bus  = smbus.SMBus(I2C_BUS)

    try:
        pir_state  = pir.read()
        rcwl_state = rcwl.read()

        try:
            ambient = _read_temp(bus, MLX90614_REG_AMBIENT)
            obj     = _read_temp(bus, MLX90614_REG_OBJECT)
        except Exception as e:
            print(f"  MLX90614 error: {e}")
            ambient = None
            obj     = None

        return {
            "pir":       pir_state,
            "microwave": rcwl_state,
            "ambient":   ambient,
            "object":    obj,
        }

    finally:
        pir.close()
        rcwl.close()
        bus.close()


# ── Standalone monitor mode ──────────────────────────────────────────────────────

if __name__ == "__main__":
    last_pir  = False
    last_rcwl = False

    print("Monitoring sensors...")
    print("CTRL-C to stop")

    try:
        while True:
            s = read_sensors()

            if s["pir"] and not last_pir:
                print("🔥 PIR motion detected")

            if s["microwave"] and not last_rcwl:
                print("📡 RCWL-0516 motion detected")

            last_pir  = s["pir"]
            last_rcwl = s["microwave"]

            if s["ambient"] is not None:
                print(f"Ambient: {s['ambient']:.1f}°C | Object: {s['object']:.1f}°C")

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping")

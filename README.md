# 🏛️ Multimodal AI Asset Protection

**Computer Vision + Environmental Sensors + AI Agent for Museum Asset Protection**

**Roni Bandini**
June 2026
MIT License

---

## 📖 Overview

Traditional asset protection systems often rely on a single sensing modality, such as a Passive Infrared (PIR) motion detector. While inexpensive and widely deployed, PIR-based systems are prone to false positives caused by temperature fluctuations, reflections, electrical noise, and environmental conditions.

This project explores a different approach: combining **computer vision**, **environmental sensing**, and an **AI reasoning agent** running entirely on a low-cost edge AI computer.

The prototype continuously monitors a valuable object—in this case, an Omega wristwatch—and evaluates sensor data, object position, operating hours, and environmental conditions to determine the most appropriate response.

No cloud processing is required.

---

## ✨ Features

* 🎥 Object detection using Edge Impulse
* 👁️ Continuous asset monitoring
* 📍 Position tracking inside the camera frame
* 🌡️ Non-contact temperature monitoring
* 🚶 Human presence detection
* 🤖 AI-based reasoning with OpenClaw
* 🔒 Fully local processing
* ⚡ Runs on Qualcomm AI hardware
* 📲 Telegram and WhatsApp notifications

---

## 🏗️ System Architecture

```text
                   ┌─────────────┐
                   │ PIR Sensor  │
                   └──────┬──────┘
                          │

                   ┌─────────────┐
                   │ RCWL-0516   │
                   └──────┬──────┘
                          │

                   ┌─────────────┐
                   │ MLX90614    │
                   └──────┬──────┘
                          │

                   ┌─────────────┐
                   │ USB Camera  │
                   └──────┬──────┘
                          │

                ┌────────────────────┐
                │     Rubik Pi 3     │
                │ Edge Impulse Model │
                └─────────┬──────────┘
                          │

                ┌────────────────────┐
                │      OpenClaw      │
                │     AI Agent       │
                └─────────┬──────────┘
                          │

      ┌────────────┬────────────┬────────────┬────────────┐
      │ Log Event  │ Maintenance│  Security  │ Authorities│
      └────────────┴────────────┴────────────┴────────────┘
```

---

## 🧩 Components

| Component    | Purpose                          |
| ------------ | -------------------------------- |
| Edge Impulse | Object detection                 |
| OpenClaw     | AI reasoning and decision making |
| Rubik Pi 3   | Edge AI execution                |
| PIR Sensor   | Motion detection                 |
| RCWL-0516    | Microwave presence detection     |
| MLX90614     | Infrared temperature monitoring  |
| USB Camera   | Visual monitoring                |

---

## 🖥️ Hardware

### Rubik Pi 3

| Specification    | Value                       |
| ---------------- | --------------------------- |
| SoC              | Qualcomm Dragonwing QCS6490 |
| CPU Architecture | ARM64 / AArch64             |
| AI Accelerator   | Hexagon NPU                 |
| GPU              | Adreno 643                  |
| AI Performance   | Up to 12 TOPS               |
| RAM              | 8 GB LPDDR4x                |
| Storage          | 128 GB UFS 2.2              |
| Dimensions       | 100 × 75 mm                 |

---

## 📦 Bill of Materials

| Qty | Item                        |
| --- | --------------------------- |
| 1   | Thundercomm Rubik Pi 3      |
| 1   | Active Cooler               |
| 1   | USB-C PD Power Supply       |
| 1   | Logitech USB Camera         |
| 1   | PIR Motion Sensor           |
| 1   | RCWL-0516 Microwave Sensor  |
| 1   | MLX90614 Temperature Sensor |
| 20  | Dupont Jumper Wires         |

---

## 🔍 Sensors

### PIR Sensor

Detects motion by measuring changes in infrared radiation emitted by surrounding objects.

### RCWL-0516 Microwave Sensor

Unlike PIR sensors, the RCWL-0516 is an active sensor that emits microwave energy and detects changes in the reflected signal.

Advantages:

* Works in hot environments
* Detects movement regardless of temperature
* Less affected by ambient heat

### MLX90614 Infrared Temperature Sensor

Provides:

* Object temperature
* Ambient temperature

The sensor can detect:

* Human contact
* Object removal
* Tampering attempts

by comparing the watch surface temperature against ambient conditions.

---

## 🤖 AI Decision Making

OpenClaw receives:

* Asset presence
* Asset coordinates
* Motion events
* Human presence detection
* Temperature changes
* Museum operating hours

Example reasoning:

```text
IF
    Watch missing
    AND museum closed
    AND motion detected
    AND human presence detected

THEN
    Potential security incident
```

Possible actions:

| Action                 | Description              |
| ---------------------- | ------------------------ |
| 📝 Log Event           | Record incident          |
| 🔧 Notify Maintenance  | Possible equipment issue |
| 👮 Notify Security     | Security review required |
| 🚨 Contact Authorities | High-confidence incident |

---

## 🧠 Edge Impulse Training

### Dataset

| Parameter      | Value          |
| -------------- | -------------- |
| Images         | 80+            |
| Resolution     | 96×96          |
| Labels         | Bounding Boxes |
| Training Split | 90 / 10        |
| Epochs         | 70             |
| Learning Rate  | 0.001          |

### Workflow

1. Create project
2. Upload images
3. Label watch
4. Create Impulse
5. Train model
6. Test performance
7. Deploy to Rubik Pi 3

---

## ⚙️ Installation

### System Packages

```bash
sudo apt update

sudo apt-get install \
libportaudio2 \
libportaudiocpp0 \
portaudio19-dev \
--break-system-packages

sudo apt install python3-pyaudio
sudo apt install selinux-utils
sudo apt install fswebcam -y
sudo apt install -y sox libsox-fmt-all
sudo apt install python3-smbus
sudo apt install gpiod
```

### Python Packages

```bash
pip3 install edge_impulse_linux \
-i https://pypi.python.org/simple \
--break-system-packages

pip3 install "opencv-python>=4.5.1.48,<5" \
--break-system-packages
```

---

## 📷 Camera Verification

```bash
lsusb
```

```bash
ls /dev/video*
```

```bash
fswebcam -d /dev/video0 \
-r 1280x720 \
--no-banner test.jpg
```

---

## 🌡️ Verify Temperature Sensor

```bash
i2cdetect -a -y -r 1
```

---

## 🚀 Deploy Edge Impulse Model

```bash
sudo edge-impulse-linux-runner
```

Select the **quantized model**.

> Qualcomm's Hexagon NPU supports quantized models. Float32 models will execute on the CPU.

Typical performance:

```text
boundingBoxes 2ms. []
boundingBoxes 3ms. [{"label":"watch","value":0.70}]
```

---

## 🦞 OpenClaw

Install:

```bash
curl -fsSL https://openclaw.ai/install.sh | bash
```

Configure:

* OpenAI
* Anthropic
* Ollama
* Telegram
* WhatsApp

Telegram pairing:

```bash
openclaw pairing approve telegram XXXXX
```

---

## ⚙️ Configuration

```python
WATCH_DEFAULT_X = 32
WATCH_DEFAULT_Y = 40

WATCH_POSITION_THRESHOLD_PCT = 20

CONFIDENCE_THRESHOLD = 0.85

MUSEUM_OPEN_HOUR = 9
MUSEUM_CLOSE_HOUR = 18

DEFAULT_OBJECT_TEMP = 22.0
DEFAULT_AMBIENT_TEMP = 22.0

TEMP_THRESHOLD_PCT = 15
```

---

## 📈 Example Output

```text
AI Asset Protection
Roni Bandini, Oct 2025, Argentina

Museum hours            → 09:00 – 18:00
Watch default position  → X:32 Y:40
Confidence threshold    → 0.85
Object temp default     → 22.0°C
Ambient temp default    → 22.0°C

Stop with CTRL-C
```

---

## 🔒 Why Multimodal Security?

A camera alone can be fooled.

A PIR sensor alone can generate false positives.

A temperature sensor alone lacks context.

By combining:

* Computer Vision
* Temperature Monitoring
* Microwave Detection
* Motion Detection
* AI Reasoning

the system can make significantly more informed decisions than any individual sensor.

---

## 📚 References

* Edge Impulse
* OpenClaw
* Rubik Pi 3
* MLX90614
* RCWL-0516

---

## 📄 License

MIT License

Copyright (c) 2026 Roni Bandini


# 🎙️ Voice Control Mode Guide

## Overview

Control the smart dustbin using voice commands instead of object detection. Simply say "plastic" or "paper" to open the corresponding bin.

## Features

- **Voice Recognition:** Uses Google Speech Recognition API
- **Text-to-Speech:** Announces bin actions
- **Same Hardware:** Uses the same ESP8266 servo setup as the camera version
- **Background Processing:** Voice commands trigger non-blocking bin operations
- **Statistics:** Tracks successful and failed commands

## Requirements

Install voice control dependencies:

```powershell
cd "E:\minor project\try 1"
python -m pip install SpeechRecognition pyaudio pyttsx3 requests
```

**Note:** On Windows, if `pyaudio` installation fails, download the wheel file from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio) and install:

```powershell
pip install PyAudio‑0.2.13‑cp311‑cp311‑win_amd64.whl
```

## Hardware Setup

Uses the same ESP8266 + servo setup as `smart_dustbin_smooth.py`:
- **Servo 1 (Paper/Green bin):** Connected to GPIO pin configured in ESP8266
- **Servo 2 (Plastic/Blue bin):** Connected to GPIO pin configured in ESP8266
- **ESP8266 IP:** `192.168.138.133` (update in script if different)

## Usage

### 1. Start Voice Control

```powershell
python smart_dustbin_voice.py
```

### 2. Speak Commands

- Say **"plastic"** to open the plastic bin
- Say **"paper"** to open the paper bin
- Press **Ctrl+C** to exit

### 3. What Happens

When you say a command:
1. 🎤 Microphone captures your voice
2. 🔄 Google Speech Recognition processes the audio
3. 📝 Script identifies "plastic" or "paper" keyword
4. 🗑️ Corresponding bin opens for 6 seconds
5. 🔒 Bin closes automatically
6. 🔊 Text-to-speech announces the action

## Commands

| Voice Command | Action |
|---------------|--------|
| "plastic" | Opens plastic bin (blue) |
| "paper" | Opens paper bin (green) |

## Tips

- **Speak clearly** and wait for the "Listening..." prompt
- **Quiet environment** improves recognition accuracy
- **Internet required** for Google Speech Recognition API
- **Microphone permissions** must be granted to Python/Terminal
- If recognition fails, the script will prompt you to try again

## Demo Mode

If ESP8266 is not connected, the script runs in **DEMO MODE**:
- Commands are printed to console
- No actual servo control
- Useful for testing voice recognition without hardware

## Configuration

Edit `smart_dustbin_voice.py` to customize:

```python
# ESP8266 IP address
ESP8266_HOST = "192.168.138.133"

# Servo angles
SERVO1_OPEN_ANGLE = 0      # Paper bin open
SERVO1_CLOSE_ANGLE = 180   # Paper bin close
SERVO2_OPEN_ANGLE = 180    # Plastic bin open
SERVO2_CLOSE_ANGLE = 0     # Plastic bin close

# Wait time for waste to drop
WASTE_DROP_DELAY = 6  # seconds
```

## Troubleshooting

### Microphone Not Detected

```powershell
# List available microphones
python -c "import speech_recognition as sr; print(sr.Microphone.list_microphone_names())"
```

If your microphone is not the default, update the script:

```python
# Use specific microphone by index
microphone = sr.Microphone(device_index=1)
```

### Recognition Errors

- **"Could not understand audio":** Speak more clearly or reduce background noise
- **"Request error":** Check internet connection (Google API requires internet)
- **"No speech detected":** Increase timeout or check microphone volume

### PyAudio Installation Issues (Windows)

If `pip install pyaudio` fails:

1. Download wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
2. Match your Python version (e.g., `cp311` = Python 3.11)
3. Install: `pip install PyAudio‑0.2.13‑cp311‑cp311‑win_amd64.whl`

### Text-to-Speech Not Working

- Windows: Uses built-in SAPI voices (should work by default)
- If TTS fails, the script continues without audio feedback (console output still works)

## Statistics

When you exit (Ctrl+C), the script shows session statistics:

```
📊 Session Statistics:

PAPER:
  Total commands: 5
  Successful: 4
  Failed: 1

PLASTIC:
  Total commands: 3
  Successful: 3
  Failed: 0
```

## Comparison: Voice vs Camera Mode

| Feature | Voice Mode | Camera Mode |
|---------|-----------|-------------|
| Input | Microphone | Camera |
| Detection | Speech Recognition | YOLO Object Detection |
| Accuracy | Depends on clarity | Depends on lighting/training |
| Speed | ~2-3 seconds | Real-time |
| Internet | Required (Google API) | Not required |
| Hands-free | Yes | Yes (automatic) |

## Next Steps

- Combine both modes: Use voice for manual control and camera for automatic detection
- Add more commands: "metal", "glass", "organic"
- Offline speech recognition: Use `vosk` or `pocketsphinx` instead of Google API
- Custom wake word: Add "dustbin" prefix (e.g., "dustbin plastic")

## Example Session

```
================================================================================
SMART DUSTBIN - VOICE CONTROL
Say 'plastic' or 'paper' to open the corresponding bin
================================================================================

📡 ESP8266 Configuration:
  Host: 192.168.138.133
  Servo 1 (Paper): Open=0°, Close=180°
  Servo 2 (Plastic): Open=180°, Close=0°
  Waste drop delay: 6s

================================================================================
TESTING ESP8266 CONNECTION...
================================================================================

Testing connection to http://192.168.138.133...
✅ Connected! ESP8266 responded: 200

================================================================================
🎙️  VOICE CONTROL ACTIVE
================================================================================

Commands:
  - Say 'plastic' to open plastic bin
  - Say 'paper' to open paper bin
  - Press Ctrl+C to exit

🔊 Voice control ready. Say plastic or paper to open bin.

🎤 Listening... (say 'plastic' or 'paper')
🔄 Processing...
📝 You said: 'plastic bottle'

================================================================================
🗑️  PLASTIC DETECTED
================================================================================
✅ PLASTIC bin opened (180°)
🔊 plastic bin opened
⏳ Waiting 6s for waste to drop...
✅ PLASTIC bin closed (0°)
🔊 plastic bin closed
✅ Ready for next command
```

## Support

- For hardware setup, see `ESP32_SETUP_GUIDE.md`
- For camera mode, see `SMOOTH_MODE_GUIDE.md`
- For training details, see `FRESH_TRAINING_STATUS.md`

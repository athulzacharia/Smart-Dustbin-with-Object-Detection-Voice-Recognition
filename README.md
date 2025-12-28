# Smart Dustbin with Object Detection & Voice Recognition

**Overview**

- **Purpose:** Detect waste types (paper, plastic, etc.) from camera images and control a smart dustbin (open lid, count items, announce status).
- **Main scripts:** `smart_dustbin_smooth.py` (main app), `webcam_fresh.py` (demo), `train_roboflow.py` + `data_roboflow.yaml` (training).

**Quick Start**

- Install dependencies:

```powershell
cd "E:\minor project\try 1"
python -m pip install -r requirements.txt
```

- Run the main application:

```powershell
python smart_dustbin_smooth.py
```

- Run the webcam demo:

```powershell
python webcam_fresh.py
```

**How It Works (Simple)**

- **1. Capture:** Camera takes an image (frame).
- **2. Detect:** The model finds objects and returns rectangles (bounding boxes) with labels and confidence scores.
- **3. Filter:** The app removes overlapping/duplicate boxes (Non-Maximum Suppression).
- **4. Decide:** If confidence is high enough, the app maps the detected class to an action (e.g., open lid for plastic).
- **5. Act & Report:** The bin performs the action and can log or speak the result.

**Key Concepts (Plain English)**

- **Confidence:** How sure the model is (0–1). We ignore low-confidence detections (example: < 0.25).
- **Bounding box:** Rectangle around a detected object.
- **NMS (Non-Maximum Suppression):** Keeps the best rectangle when many overlap the same object.
- **mAP:** Score used during training to measure detection quality.

**Simple Rules Used by the App**

- **Confidence threshold:** Ignore detections below ~0.25.
- **Temporal smoothing:** Require the same detection in 2–3 consecutive frames before acting (reduces false triggers).
- **Priority rule:** If multiple valid classes appear, choose the highest-confidence one or use a defined priority list.

**Training & Updating the Model**

- Add labeled images and update `data_roboflow.yaml`.
- Train with `train_roboflow.py` (see file for exact usage).
- Trained weights appear in `runs/train/<name>/weights/best.pt`.

**Practical Tips**

- Use steady lighting and clear camera views for best results.
- Add examples of confusing cases to the training data to reduce mistakes.
- For embedded devices, use a smaller model or run inference on a server.

**Files You Care About**

- `smart_dustbin_smooth.py` — Main runtime (inference + behavior).
- `webcam_fresh.py` — Simple demo to test detection.
- `train_roboflow.py` & `data_roboflow.yaml` — Training pipeline configuration.
- `CLEANUP_SUMMARY.md` — Project cleanup notes.
- `requirements.txt` — Python dependencies.

**Where to Change Behavior**

- Edit thresholds and smoothing in `smart_dustbin_smooth.py`.
- Change class-to-action mapping in the main script to customize bin behavior.

## 📁 Final Clean Structure:

```
d:\minor project\try 1\
│
├── 📱 Applications
│   ├── smart_dustbin_smooth.py      ⭐ Main (recommended)
│   ├── smart_dustbin_esp32.py       Alternative
│   └── webcam_fresh.py              Demo
│
├── 🎓 Training
│   ├── train_roboflow.py
│   └── data_roboflow.yaml
│
├── 📚 Documentation
│   ├── README_NEW.md                ⭐ Updated README
│   ├── SMOOTH_MODE_GUIDE.md
│   ├── ESP32_SETUP_GUIDE.md
│   ├── FRESH_TRAINING_STATUS.md
│   └── CLEANUP_PLAN.md
│
├── ⚙️ Configuration
│   ├── requirements.txt
│   ├── .gitignore
│   └── cleanup.ps1
│
├── 🤖 Model & Results
│   └── runs/
│       └── train/
│           └── roboflow_fresh/
│               └── weights/
│                   ├── best.pt      ⭐ Your model
│                   └── last.pt
│
└── 🐍 Environment
    └── .venv/                        Python packages
```

---

"""
Fresh Webcam Inference - Roboflow Trained Model
High-accuracy real-time detection for smart dustbin
"""
from ultralytics import YOLO
import cv2
import time

print("="*80)
print("SMART DUSTBIN - FRESH MODEL")
print("Paper and Plastic Bottle Detection")
print("="*80)

# Load the NEW trained model
model = YOLO('runs/train/roboflow_fresh/weights/best.pt')

print(f"\n✓ Model loaded: Fresh Roboflow trained model")
print(f"  Classes: {model.names}")
print(f"  Expected confidence: 70-85%")

# Open webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

print(f"\n✓ Webcam opened")
print(f"\n{'='*80}")
print("CONTROLS:")
print("  SPACE - Pause/Resume")
print("  Q     - Quit")
print("="*80)
print("\nStarting detection...\n")

fps_time = time.time()
frame_count = 0
paused = False

# Detection settings - HIGHER confidence for better accuracy
CONF_THRESHOLD = 0.60  # 60% confidence (vs previous 25%)
MIN_SIZE = 0.03        # 3% of frame (filter tiny objects)

# Bin colors
BIN_COLORS = {
    'paper': (0, 255, 0),         # GREEN bin
    'plastic bottle': (255, 0, 0) # BLUE bin (BGR format)
}

while True:
    if not paused:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Run inference
        results = model(frame, conf=CONF_THRESHOLD, verbose=False)
        
        # Get detections
        boxes = results[0].boxes
        
        # Calculate FPS
        frame_count += 1
        if frame_count % 10 == 0:
            fps = 10 / (time.time() - fps_time)
            fps_time = time.time()
        else:
            fps = 0
        
        # Process detections
        detections = {'paper': [], 'plastic bottle': []}
        
        for box in boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            class_name = model.names[cls]
            
            xyxy = box.xyxy[0].cpu().numpy()
            x1, y1, x2, y2 = map(int, xyxy)
            
            # Calculate size
            width = x2 - x1
            height = y2 - y1
            area = width * height
            frame_area = frame.shape[0] * frame.shape[1]
            size_ratio = area / frame_area
            
            # Filter by size (ignore tiny detections)
            if size_ratio < MIN_SIZE:
                continue
            
            detections[class_name].append({
                'box': (x1, y1, x2, y2),
                'conf': conf,
                'size': size_ratio
            })
        
        # Draw detections
        for class_name, items in detections.items():
            color = BIN_COLORS[class_name]
            
            for item in items:
                x1, y1, x2, y2 = item['box']
                conf = item['conf']
                
                # Draw bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
                
                # Draw label with confidence
                label = f"{class_name.upper()}: {conf:.0%}"
                
                # Label background
                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
                cv2.rectangle(frame, (x1, y1 - 35), (x1 + label_size[0] + 10, y1), color, -1)
                
                # Label text
                cv2.putText(frame, label, (x1 + 5, y1 - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                
                # Bin indicator
                if class_name == 'paper':
                    bin_text = "-> GREEN BIN"
                else:
                    bin_text = "-> BLUE BIN"
                
                cv2.putText(frame, bin_text, (x1, y2 + 25),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Status overlay
        overlay_h = 120
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (frame.shape[1], overlay_h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # Title
        cv2.putText(frame, "SMART DUSTBIN - FRESH MODEL", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Stats
        paper_count = len(detections['paper'])
        plastic_count = len(detections['plastic bottle'])
        
        cv2.putText(frame, f"Paper: {paper_count} | Plastic: {plastic_count}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        if fps > 0:
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Confidence threshold indicator
        cv2.putText(frame, f"Confidence: >{CONF_THRESHOLD:.0%}", (frame.shape[1] - 250, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        cv2.imshow('Smart Dustbin - Fresh Model', frame)
    
    # Handle keys
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord(' '):
        paused = not paused
        if paused:
            print("⏸️  PAUSED - Press SPACE to resume")
        else:
            print("▶️  RESUMED")

cap.release()
cv2.destroyAllWindows()

print("\n" + "="*80)
print("DETECTION STOPPED")
print("="*80)

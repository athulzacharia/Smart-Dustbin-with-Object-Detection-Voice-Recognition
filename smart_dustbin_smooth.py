"""
Smart Dustbin - Smooth Experience Version
Camera feed never freezes - predictions shown as overlays
"""
from ultralytics import YOLO
import cv2
import time
import requests
import threading

print("="*80)
print("SMART DUSTBIN - SMOOTH EXPERIENCE")
print("Non-blocking servo control with live camera feed")
print("="*80)

# ESP8266 Web Server Configuration
ESP8266_HOST = "192.168.138.133"
ESP8266_PORT = 80

# Servo control endpoints with angle parameters
SERVO1_URL = f"http://{ESP8266_HOST}/servo1"  # Paper (Green bin)
SERVO2_URL = f"http://{ESP8266_HOST}/servo2"  # Plastic (Blue bin)

# Servo angles (adjust based on your setup)
# Servo 1 (Paper): Open=0°, Close=180°
# Servo 2 (Plastic): Open=180°, Close=0°
SERVO1_OPEN_ANGLE = 0
SERVO1_CLOSE_ANGLE = 180
SERVO2_OPEN_ANGLE = 180
SERVO2_CLOSE_ANGLE = 0

# Wait time for waste to drop
WASTE_DROP_DELAY = 6  # seconds

print(f"\n📡 ESP8266 Configuration:")
print(f"  Host: {ESP8266_HOST}")
print(f"  Port: {ESP8266_PORT}")
print(f"  Servo 1 URL: {SERVO1_URL}")
print(f"  Servo 2 URL: {SERVO2_URL}")
print(f"  Servo 1: Open={SERVO1_OPEN_ANGLE}°, Close={SERVO1_CLOSE_ANGLE}°")
print(f"  Servo 2: Open={SERVO2_OPEN_ANGLE}°, Close={SERVO2_CLOSE_ANGLE}°")
print(f"  Waste drop delay: {WASTE_DROP_DELAY}s")

# Test ESP8266 connection
print(f"\n{'='*80}")
print("TESTING ESP8266 CONNECTION...")
print("="*80)

DEMO_MODE = False
ESP8266_CONNECTED = False

try:
    print(f"\nTesting connection to http://{ESP8266_HOST}...")
    response = requests.get(f"http://{ESP8266_HOST}", timeout=3)
    print(f"✅ Connected! ESP8266 responded: {response.status_code}")
    ESP8266_CONNECTED = True
    
except requests.exceptions.Timeout:
    print(f"❌ Connection timeout - ESP8266 not responding")
    print(f"   Make sure ESP8266 is powered on and connected to network")
    ESP8266_CONNECTED = False
    
except requests.exceptions.ConnectionError:
    print(f"❌ Connection failed - Cannot reach {ESP8266_HOST}")
    print(f"   Check:")
    print(f"   1. ESP8266 IP address is correct ({ESP8266_HOST})")
    print(f"   2. ESP8266 and laptop are on same network")
    print(f"   3. ESP8266 web server is running")
    ESP8266_CONNECTED = False
    
except Exception as e:
    print(f"❌ Error: {e}")
    ESP8266_CONNECTED = False

if not ESP8266_CONNECTED:
    print(f"\n⚠️  Running in DEMO MODE (no servo control)")
    print(f"   Commands will be printed but not sent to ESP8266")
    DEMO_MODE = True
else:
    DEMO_MODE = False

# Load model
print(f"\n{'='*80}")
print("LOADING DETECTION MODEL...")
print("="*80)

model = YOLO('runs/train/roboflow_fresh/weights/best.pt')

print(f"\n✓ Model loaded")
print(f"  Classes: {model.names}")
print(f"  mAP: 88.18%")

# Open webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

print(f"\n✓ Webcam opened")

print(f"\n{'='*80}")
print("CONTROLS:")
print("  SPACE - Pause/Resume")
print("  Q     - Quit")
print("  1     - Test Servo 1 (manual)")
print("  2     - Test Servo 2 (manual)")
print("="*80)
print("\nStarting detection...\n")

# Detection settings
CONF_THRESHOLD = 0.60
MIN_SIZE = 0.03
MAX_SIZE = 1.0

# Timing settings
SERVO_OPERATION_TIME = 4.0
COOLDOWN_TIME = 0.5

# Bin colors
BIN_COLORS = {
    'paper': (0, 255, 0),         # GREEN
    'plastic bottle': (255, 0, 0) # BLUE
}

# State management
paused = False
frame_count = 0
fps_time = time.time()
fps = 0
session_start_time = time.time()

# Statistics
stats = {
    'paper': {'count': 0, 'success': 0, 'failed': 0, 'confidences': [], 'response_times': []},
    'plastic bottle': {'count': 0, 'success': 0, 'failed': 0, 'confidences': [], 'response_times': []}
}

# Servo operation state (shared between threads)
servo_state = {
    'active': False,
    'class_name': None,
    'start_time': 0,
    'message': '',
    'countdown': 0
}
servo_lock = threading.Lock()

def send_http_request_async(url, class_name):
    """Send HTTP request in background thread with angle control"""
    global servo_state
    
    # Determine angles based on servo (paper=servo1, plastic=servo2)
    if class_name == 'paper':
        open_angle = SERVO1_OPEN_ANGLE
        close_angle = SERVO1_CLOSE_ANGLE
        bin_name = "GREEN BIN (Servo 1)"
    else:  # plastic bottle
        open_angle = SERVO2_OPEN_ANGLE
        close_angle = SERVO2_CLOSE_ANGLE
        bin_name = "BLUE BIN (Servo 2)"
    
    if DEMO_MODE:
        print(f"\n🎬 DEMO MODE: Would send:")
        print(f"   Open: GET {url}?angle={open_angle}")
        print(f"   Wait {WASTE_DROP_DELAY} seconds...")
        print(f"   Close: GET {url}?angle={close_angle}")
        with servo_lock:
            stats[class_name]['success'] += 1
    else:
        operation_start = time.time()
        try:
            # Step 1: Open the bin lid
            open_url = f"{url}?angle={open_angle}"
            print(f"\n📤 Opening bin: {open_url}")
            response = requests.get(open_url, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ Lid opened! (Servo at {open_angle}°)")
                
                # Wait for waste to drop
                print(f"⏳ Waiting for waste to drop ({WASTE_DROP_DELAY}s)...")
                time.sleep(WASTE_DROP_DELAY)
                
                # Step 2: Close the bin lid
                close_url = f"{url}?angle={close_angle}"
                print(f"📤 Closing bin: {close_url}")
                response = requests.get(close_url, timeout=5)
                
                if response.status_code == 200:
                    print(f"✅ Lid closed! (Servo at {close_angle}°)")
                    operation_time = time.time() - operation_start
                    with servo_lock:
                        stats[class_name]['success'] += 1
                        stats[class_name]['response_times'].append(operation_time)
                else:
                    print(f"⚠️  Close failed: {response.status_code}")
                    with servo_lock:
                        stats[class_name]['failed'] += 1
            else:
                print(f"⚠️  ESP8266 responded with status: {response.status_code}")
                with servo_lock:
                    stats[class_name]['failed'] += 1
                    
        except Exception as e:
            print(f"❌ Error: {e}")
            with servo_lock:
                stats[class_name]['failed'] += 1

def trigger_servo(class_name):
    """Trigger servo operation in background"""
    global servo_state
    
    # Check if already processing
    with servo_lock:
        if servo_state['active']:
            print(f"⚠️  Servo already active, skipping...")
            return
        
        # Mark as active
        servo_state['active'] = True
        servo_state['class_name'] = class_name
        servo_state['start_time'] = time.time()
        stats[class_name]['count'] += 1
    
    # Determine URL
    url = SERVO1_URL if class_name == 'paper' else SERVO2_URL
    
    # Send HTTP request in background thread
    request_thread = threading.Thread(target=send_http_request_async, args=(url, class_name))
    request_thread.daemon = True
    request_thread.start()
    
    # Update countdown in main loop

def update_servo_state():
    """Update servo operation state"""
    global servo_state
    
    with servo_lock:
        if servo_state['active']:
            elapsed = time.time() - servo_state['start_time']
            total_time = SERVO_OPERATION_TIME + COOLDOWN_TIME
            
            if elapsed < SERVO_OPERATION_TIME:
                # Servo operating
                remaining = SERVO_OPERATION_TIME - elapsed
                servo_state['countdown'] = int(remaining) + 1
                servo_state['message'] = f"SERVO OPERATING... {servo_state['countdown']}s"
            elif elapsed < total_time:
                # Cooldown
                servo_state['countdown'] = 0
                servo_state['message'] = "COOLDOWN..."
            else:
                # Done
                servo_state['active'] = False
                servo_state['message'] = "READY FOR NEXT DETECTION"
                print(f"✅ Ready for next detection\n")
                return False
            return True
    return False

# Main loop
while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Calculate FPS
    frame_count += 1
    if frame_count % 10 == 0:
        fps = 10 / (time.time() - fps_time)
        fps_time = time.time()
    
    # Update servo state
    update_servo_state()
    
    # Run detection (always, even during servo operation)
    if not paused:
        results = model(frame, conf=CONF_THRESHOLD, verbose=False)
        boxes = results[0].boxes
        
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
            
            # Size filtering
            if size_ratio < MIN_SIZE or size_ratio > MAX_SIZE:
                continue
            
            detections[class_name].append({
                'box': (x1, y1, x2, y2),
                'conf': conf,
                'size': size_ratio
            })
        
        # Find best detection
        best_detection = None
        best_conf = 0
        
        for class_name, items in detections.items():
            for item in items:
                if item['conf'] > best_conf:
                    best_conf = item['conf']
                    best_detection = (class_name, item)
        
        # Trigger servo if detection found and not already processing
        if best_detection and not servo_state['active']:
            class_name, item = best_detection
            emoji = "🟢" if class_name == 'paper' else "🔵"
            servo_num = "1" if class_name == 'paper' else "2"
            print(f"\n{emoji} {class_name.upper()} DETECTED → Triggering Servo {servo_num}...")
            # Track confidence for evaluation
            with servo_lock:
                stats[class_name]['confidences'].append(item['conf'])
            trigger_servo(class_name)
        
        # Draw detections
        for class_name, items in detections.items():
            color = BIN_COLORS[class_name]
            
            for item in items:
                x1, y1, x2, y2 = item['box']
                conf = item['conf']
                
                # Bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
                
                # Label
                label = f"{class_name.upper()}: {conf:.0%}"
                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
                cv2.rectangle(frame, (x1, y1 - 35), (x1 + label_size[0] + 10, y1), color, -1)
                cv2.putText(frame, label, (x1 + 5, y1 - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    # Status overlay (top bar)
    overlay_h = 140
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (frame.shape[1], overlay_h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
    
    # Title
    cv2.putText(frame, "SMART DUSTBIN - SMOOTH MODE", (15, 35),
               cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
    
    # ESP8266 status
    esp_status = "DEMO MODE" if DEMO_MODE else f"ESP8266: {ESP8266_HOST}"
    status_color = (0, 165, 255) if DEMO_MODE else (0, 255, 0)
    cv2.putText(frame, esp_status, (15, 70),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
    
    # Stats
    total_paper = stats['paper']['count']
    total_plastic = stats['plastic bottle']['count']
    cv2.putText(frame, f"Paper: {total_paper} | Plastic: {total_plastic}", (15, 105),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # FPS and State
    state_text = "PAUSED" if paused else servo_state.get('message', 'READY')
    if servo_state['active']:
        state_color = (0, 255, 255)  # Yellow when processing
    elif paused:
        state_color = (0, 165, 255)  # Orange when paused
    else:
        state_color = (0, 255, 0)    # Green when ready
    
    cv2.putText(frame, f"FPS: {fps:.1f} | {state_text}", (frame.shape[1] - 450, 35),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, state_color, 2)
    
    # Servo operation popup (center of screen)
    if servo_state['active']:
        popup_w, popup_h = 600, 200
        center_x = frame.shape[1] // 2
        center_y = frame.shape[0] // 2
        x1 = center_x - popup_w // 2
        y1 = center_y - popup_h // 2
        x2 = x1 + popup_w
        y2 = y1 + popup_h
        
        # Semi-transparent background
        popup_overlay = frame.copy()
        cv2.rectangle(popup_overlay, (x1, y1), (x2, y2), (0, 0, 0), -1)
        cv2.addWeighted(popup_overlay, 0.8, frame, 0.2, 0, frame)
        
        # Border
        class_name = servo_state['class_name']
        border_color = BIN_COLORS[class_name]
        cv2.rectangle(frame, (x1, y1), (x2, y2), border_color, 5)
        
        # Prediction text
        prediction_text = class_name.upper()
        servo_num = "1 (GREEN)" if class_name == 'paper' else "2 (BLUE)"
        
        cv2.putText(frame, prediction_text, (x1 + 50, y1 + 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, border_color, 3)
        
        cv2.putText(frame, f"Servo {servo_num} Activated", (x1 + 50, y1 + 120),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        
        # Countdown
        if servo_state['countdown'] > 0:
            cv2.putText(frame, f"{servo_state['countdown']}s", (x1 + 50, y1 + 165),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 2)
    
    # Show frame
    cv2.imshow('Smart Dustbin', frame)
    
    # Keyboard controls
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('q'):
        break
    elif key == ord(' '):
        paused = not paused
        print(f"{'⏸️  Paused' if paused else '▶️  Resumed'}")
    elif key == ord('1'):
        if not servo_state['active']:
            print(f"\n🧪 MANUAL TEST: Servo 1 (Paper)")
            trigger_servo('paper')
    elif key == ord('2'):
        if not servo_state['active']:
            print(f"\n🧪 MANUAL TEST: Servo 2 (Plastic)")
            trigger_servo('plastic bottle')

# Cleanup
cap.release()
cv2.destroyAllWindows()

# Calculate session duration
session_duration = time.time() - session_start_time

# Session summary with evaluation metrics in table format
print(f"\n{'='*80}")
print("SESSION SUMMARY - EVALUATION METRICS")
print("="*80)

# Session Information Table
print(f"\n{'='*80}")
print("📊 SESSION INFORMATION")
print("="*80)
print(f"{'Metric':<30} {'Value':<20}")
print("-"*80)
print(f"{'Duration':<30} {session_duration:.1f}s ({session_duration/60:.1f} min)")
print(f"{'Total Frames Processed':<30} {frame_count}")
if session_duration > 0:
    print(f"{'Average FPS':<30} {frame_count/session_duration:.1f}")
print("="*80)

# Calculate metrics for each class
total_detections = stats['paper']['count'] + stats['plastic bottle']['count']
total_success = stats['paper']['success'] + stats['plastic bottle']['success']
total_failed = stats['paper']['failed'] + stats['plastic bottle']['failed']
total_operations = total_success + total_failed

# Detection Statistics Table
print(f"\n{'='*80}")
print("🎯 DETECTION STATISTICS")
print("="*80)
print(f"{'Class':<15} {'Detections':<15} {'Success':<15} {'Failed':<15} {'Rate':<15}")
print("-"*80)

# Paper row
paper_rate = f"{(stats['paper']['success'] / (stats['paper']['success'] + stats['paper']['failed']) * 100):.1f}%" if (stats['paper']['success'] + stats['paper']['failed']) > 0 else "N/A"
print(f"{'🟢 Paper':<15} {stats['paper']['count']:<15} {stats['paper']['success']:<15} {stats['paper']['failed']:<15} {paper_rate:<15}")

# Plastic row
plastic_rate = f"{(stats['plastic bottle']['success'] / (stats['plastic bottle']['success'] + stats['plastic bottle']['failed']) * 100):.1f}%" if (stats['plastic bottle']['success'] + stats['plastic bottle']['failed']) > 0 else "N/A"
print(f"{'🔵 Plastic':<15} {stats['plastic bottle']['count']:<15} {stats['plastic bottle']['success']:<15} {stats['plastic bottle']['failed']:<15} {plastic_rate:<15}")

# Total row
total_rate = f"{(total_success / total_operations * 100):.1f}%" if total_operations > 0 else "N/A"
print("-"*80)
print(f"{'TOTAL':<15} {total_detections:<15} {total_success:<15} {total_failed:<15} {total_rate:<15}")
print("="*80)

# Confidence Metrics Table
print(f"\n{'='*80}")
print("📈 CONFIDENCE METRICS")
print("="*80)
print(f"{'Class':<15} {'Average':<15} {'Minimum':<15} {'Maximum':<15} {'Count':<15}")
print("-"*80)

# Paper confidence
if stats['paper']['confidences']:
    paper_avg = sum(stats['paper']['confidences']) / len(stats['paper']['confidences'])
    paper_min = min(stats['paper']['confidences'])
    paper_max = max(stats['paper']['confidences'])
    paper_cnt = len(stats['paper']['confidences'])
    print(f"{'🟢 Paper':<15} {f'{paper_avg:.1%}':<15} {f'{paper_min:.1%}':<15} {f'{paper_max:.1%}':<15} {paper_cnt:<15}")
else:
    print(f"{'🟢 Paper':<15} {'N/A':<15} {'N/A':<15} {'N/A':<15} {'0':<15}")

# Plastic confidence
if stats['plastic bottle']['confidences']:
    plastic_avg = sum(stats['plastic bottle']['confidences']) / len(stats['plastic bottle']['confidences'])
    plastic_min = min(stats['plastic bottle']['confidences'])
    plastic_max = max(stats['plastic bottle']['confidences'])
    plastic_cnt = len(stats['plastic bottle']['confidences'])
    print(f"{'🔵 Plastic':<15} {f'{plastic_avg:.1%}':<15} {f'{plastic_min:.1%}':<15} {f'{plastic_max:.1%}':<15} {plastic_cnt:<15}")
else:
    print(f"{'🔵 Plastic':<15} {'N/A':<15} {'N/A':<15} {'N/A':<15} {'0':<15}")

# Overall confidence
all_confidences = stats['paper']['confidences'] + stats['plastic bottle']['confidences']
if all_confidences:
    overall_avg = sum(all_confidences) / len(all_confidences)
    overall_min = min(all_confidences)
    overall_max = max(all_confidences)
    overall_cnt = len(all_confidences)
    print("-"*80)
    print(f"{'OVERALL':<15} {f'{overall_avg:.1%}':<15} {f'{overall_min:.1%}':<15} {f'{overall_max:.1%}':<15} {overall_cnt:<15}")

print("="*80)

# Response Time Table
print(f"\n{'='*80}")
print("⚡ SERVO RESPONSE TIME (seconds)")
print("="*80)
print(f"{'Class':<15} {'Average':<15} {'Minimum':<15} {'Maximum':<15} {'Count':<15}")
print("-"*80)

# Paper response time
if stats['paper']['response_times']:
    paper_avg_rt = sum(stats['paper']['response_times']) / len(stats['paper']['response_times'])
    paper_min_rt = min(stats['paper']['response_times'])
    paper_max_rt = max(stats['paper']['response_times'])
    paper_cnt_rt = len(stats['paper']['response_times'])
    print(f"{'🟢 Paper':<15} {f'{paper_avg_rt:.2f}s':<15} {f'{paper_min_rt:.2f}s':<15} {f'{paper_max_rt:.2f}s':<15} {paper_cnt_rt:<15}")
else:
    print(f"{'🟢 Paper':<15} {'N/A':<15} {'N/A':<15} {'N/A':<15} {'0':<15}")

# Plastic response time
if stats['plastic bottle']['response_times']:
    plastic_avg_rt = sum(stats['plastic bottle']['response_times']) / len(stats['plastic bottle']['response_times'])
    plastic_min_rt = min(stats['plastic bottle']['response_times'])
    plastic_max_rt = max(stats['plastic bottle']['response_times'])
    plastic_cnt_rt = len(stats['plastic bottle']['response_times'])
    print(f"{'🔵 Plastic':<15} {f'{plastic_avg_rt:.2f}s':<15} {f'{plastic_min_rt:.2f}s':<15} {f'{plastic_max_rt:.2f}s':<15} {plastic_cnt_rt:<15}")
else:
    print(f"{'🔵 Plastic':<15} {'N/A':<15} {'N/A':<15} {'N/A':<15} {'0':<15}")

# Overall response time
all_response_times = stats['paper']['response_times'] + stats['plastic bottle']['response_times']
if all_response_times:
    overall_avg_rt = sum(all_response_times) / len(all_response_times)
    overall_min_rt = min(all_response_times)
    overall_max_rt = max(all_response_times)
    overall_cnt_rt = len(all_response_times)
    print("-"*80)
    print(f"{'OVERALL':<15} {f'{overall_avg_rt:.2f}s':<15} {f'{overall_min_rt:.2f}s':<15} {f'{overall_max_rt:.2f}s':<15} {overall_cnt_rt:<15}")

print("="*80)

# Overall Performance Summary Table
print(f"\n{'='*80}")
print("🏆 OVERALL PERFORMANCE SUMMARY")
print("="*80)
print(f"{'Metric':<40} {'Value':<20}")
print("-"*80)
print(f"{'Total Waste Items Detected':<40} {total_detections}")
print(f"{'Total Servo Operations':<40} {total_operations}")

if total_operations > 0:
    success_rate = (total_success / total_operations) * 100
    failure_rate = (total_failed / total_operations) * 100
    print(f"{'Success Rate':<40} {success_rate:.1f}% ({total_success}/{total_operations})")
    print(f"{'Failure Rate':<40} {failure_rate:.1f}% ({total_failed}/{total_operations})")
    
if total_detections > 0 and total_operations > 0:
    accuracy = (total_success / total_detections) * 100
    print(f"{'System Accuracy':<40} {accuracy:.1f}%")

if all_confidences:
    overall_avg_conf = sum(all_confidences) / len(all_confidences)
    print(f"{'Average Detection Confidence':<40} {overall_avg_conf:.1%}")

if all_response_times:
    overall_avg_response = sum(all_response_times) / len(all_response_times)
    print(f"{'Average Servo Response Time':<40} {overall_avg_response:.2f}s")

if session_duration > 0 and total_success > 0:
    throughput = total_success / (session_duration / 60)
    print(f"{'Throughput (items/minute)':<40} {throughput:.2f}")

print("="*80)

print(f"\n✓ Smart dustbin session ended")
print("="*80)

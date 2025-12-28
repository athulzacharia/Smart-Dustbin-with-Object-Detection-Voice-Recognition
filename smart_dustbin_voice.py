"""
Smart Dustbin - Voice Control Version
Control bin by voice commands: "plastic" or "paper"
"""
import speech_recognition as sr
import pyttsx3
import requests
import threading
import time

print("="*80)
print("SMART DUSTBIN - VOICE CONTROL")
print("Say 'plastic' or 'paper' to open the corresponding bin")
print("="*80)

# ESP8266 Web Server Configuration
ESP8266_HOST = "192.168.138.133"
ESP8266_PORT = 80

# Servo control endpoints
SERVO1_URL = f"http://{ESP8266_HOST}/servo1"  # Paper (Green bin)
SERVO2_URL = f"http://{ESP8266_HOST}/servo2"  # Plastic (Blue bin)

# Servo angles
SERVO1_OPEN_ANGLE = 0
SERVO1_CLOSE_ANGLE = 180
SERVO2_OPEN_ANGLE = 180
SERVO2_CLOSE_ANGLE = 0

# Wait time for waste to drop
WASTE_DROP_DELAY = 6  # seconds

print(f"\n📡 ESP8266 Configuration:")
print(f"  Host: {ESP8266_HOST}")
print(f"  Servo 1 (Paper): Open={SERVO1_OPEN_ANGLE}°, Close={SERVO1_CLOSE_ANGLE}°")
print(f"  Servo 2 (Plastic): Open={SERVO2_OPEN_ANGLE}°, Close={SERVO2_CLOSE_ANGLE}°")
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
    ESP8266_CONNECTED = False
    
except requests.exceptions.ConnectionError:
    print(f"❌ Connection failed - Cannot reach {ESP8266_HOST}")
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

# Initialize speech recognition
recognizer = sr.Recognizer()
microphone = sr.Microphone()

# Initialize text-to-speech
engine = pyttsx3.init()
engine.setProperty('rate', 150)  # Speed of speech

# Statistics
stats = {
    'paper': {'count': 0, 'success': 0, 'failed': 0},
    'plastic': {'count': 0, 'success': 0, 'failed': 0}
}

# Servo state
servo_lock = threading.Lock()
servo_state = {
    'active': False,
    'class_name': None,
    'start_time': 0,
    'countdown': 0,
    'message': 'READY'
}

# Timing constants
SERVO_OPERATION_TIME = WASTE_DROP_DELAY  # Time for waste to drop
COOLDOWN_TIME = 2  # Cooldown after operation

def speak(text):
    """Text-to-speech output"""
    print(f"🔊 {text}")
    try:
        engine.say(text)
        engine.runAndWait()
    except:
        pass  # Ignore TTS errors

def control_servo(url, open_angle, close_angle, class_name):
    """Control servo: open, wait, close"""
    try:
        # Open servo
        open_url = f"{url}?angle={open_angle}"
        if not DEMO_MODE:
            response = requests.get(open_url, timeout=2)
            if response.status_code == 200:
                print(f"✅ {class_name.upper()} bin opened ({open_angle}°)")
                speak(f"{class_name} bin opened")
            else:
                print(f"❌ Failed to open {class_name} bin")
                return False
        else:
            print(f"[DEMO] Would open {class_name} bin to {open_angle}°")
            speak(f"{class_name} bin opened")
        
        # Wait for waste to drop
        print(f"⏳ Waiting {WASTE_DROP_DELAY}s for waste to drop...")
        time.sleep(WASTE_DROP_DELAY)
        
        # Close servo
        close_url = f"{url}?angle={close_angle}"
        if not DEMO_MODE:
            response = requests.get(close_url, timeout=2)
            if response.status_code == 200:
                print(f"✅ {class_name.upper()} bin closed ({close_angle}°)")
                speak(f"{class_name} bin closed")
            else:
                print(f"❌ Failed to close {class_name} bin")
                return False
        else:
            print(f"[DEMO] Would close {class_name} bin to {close_angle}°")
            speak(f"{class_name} bin closed")
        
        return True
        
    except Exception as e:
        print(f"❌ Servo control error: {e}")
        return False

def send_servo_command_async(url, open_angle, close_angle, class_name):
    """Send servo commands in background thread"""
    global servo_state
    
    try:
        success = control_servo(url, open_angle, close_angle, class_name)
        
        with servo_lock:
            if success:
                stats[class_name]['success'] += 1
                servo_state['message'] = f"{class_name.upper()} bin operation complete"
            else:
                stats[class_name]['failed'] += 1
                servo_state['message'] = f"{class_name.upper()} bin operation failed"
                
    except Exception as e:
        print(f"❌ Error: {e}")
        with servo_lock:
            stats[class_name]['failed'] += 1
    
    finally:
        # Cooldown
        time.sleep(COOLDOWN_TIME)
        with servo_lock:
            servo_state['active'] = False
            servo_state['message'] = 'READY FOR NEXT COMMAND'
        print(f"✅ Ready for next command\n")

def trigger_bin(class_name):
    """Trigger bin operation in background"""
    global servo_state
    
    # Check if already processing
    with servo_lock:
        if servo_state['active']:
            print(f"⚠️  Bin already active, please wait...")
            speak("Please wait, bin is already in use")
            return
        
        # Mark as active
        servo_state['active'] = True
        servo_state['class_name'] = class_name
        servo_state['start_time'] = time.time()
        stats[class_name]['count'] += 1
    
    # Determine servo parameters
    if class_name == 'paper':
        url = SERVO1_URL
        open_angle = SERVO1_OPEN_ANGLE
        close_angle = SERVO1_CLOSE_ANGLE
    else:  # plastic
        url = SERVO2_URL
        open_angle = SERVO2_OPEN_ANGLE
        close_angle = SERVO2_CLOSE_ANGLE
    
    # Send command in background thread
    thread = threading.Thread(
        target=send_servo_command_async,
        args=(url, open_angle, close_angle, class_name)
    )
    thread.daemon = True
    thread.start()

def listen_for_command():
    """Listen for voice command and return recognized text"""
    with microphone as source:
        print("\n🎤 Listening... (say 'plastic' or 'paper')")
        
        # Adjust for ambient noise
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)
            
            # Recognize speech using Google Speech Recognition
            text = recognizer.recognize_google(audio).lower()
            
            # Only return if valid command detected
            if 'plastic' in text or 'paper' in text:
                print(f"📝 Detected: '{text}'")
                return text
            else:
                # Invalid command - stay quiet and continue listening
                return None
            
        except sr.WaitTimeoutError:
            # No speech detected - stay quiet and continue listening
            return None
            
        except sr.UnknownValueError:
            # Could not understand - stay quiet and continue listening
            return None
            
        except sr.RequestError as e:
            print(f"❌ Speech recognition error: {e}")
            return None

def process_command(text):
    """Process voice command and trigger appropriate bin"""
    if not text:
        return
    
    # Check for keywords (text already validated in listen_for_command)
    if 'plastic' in text:
        print(f"\n{'='*80}")
        print("🗑️  PLASTIC DETECTED")
        print("="*80)
        trigger_bin('plastic')
        
    elif 'paper' in text:
        print(f"\n{'='*80}")
        print("📄 PAPER DETECTED")
        print("="*80)
        trigger_bin('paper')

# Main loop
print(f"\n{'='*80}")
print("🎙️  VOICE CONTROL ACTIVE")
print("="*80)
print("\nCommands:")
print("  - Say 'plastic' to open plastic bin")
print("  - Say 'paper' to open paper bin")
print("  - Press Ctrl+C to exit")
print()

speak("Voice control ready. Say plastic or paper to open bin.")

try:
    while True:
        # Listen for command
        command_text = listen_for_command()
        
        # Process command
        process_command(command_text)
        
        # Small delay before next listen
        time.sleep(0.5)
        
except KeyboardInterrupt:
    print(f"\n\n{'='*80}")
    print("SHUTTING DOWN...")
    print("="*80)
    
    print("\n📊 Session Statistics:")
    for class_name in ['paper', 'plastic']:
        total = stats[class_name]['count']
        success = stats[class_name]['success']
        failed = stats[class_name]['failed']
        print(f"\n{class_name.upper()}:")
        print(f"  Total commands: {total}")
        print(f"  Successful: {success}")
        print(f"  Failed: {failed}")
    
    speak("Goodbye")
    print("\n✅ Voice control stopped")

#!/usr/bin/env python
"""
Kor'tana Voice Chat Interface
Speak with Kor'tana using your microphone and speakers
"""

import sys
import asyncio
import base64
from pathlib import Path

# Setup paths
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
load_dotenv()

print("\n" + "=" * 80)
print("🎤 KOR'TANA - VOICE CHAT")
print("=" * 80 + "\n")

# Check dependencies
try:
    import pyaudio
    from pydub import AudioSegment
    from pydub.playback import play
    import io
    print("✅ Audio libraries loaded\n")
except ImportError as e:
    print(f"❌ Missing audio library: {e}")
    print("\nInstall with:")
    print("  pip install pyaudio pydub")
    print("\nNote: On Windows, you may need to install PyAudio separately:")
    print("  pip install pipwin")
    print("  pipwin install pyaudio")
    sys.exit(1)

try:
    from kortana.brain import ChatEngine
    from kortana.config import load_config
    from kortana.voice import STTService, TTSService, VoiceChatOrchestrator
    
    config_path = Path(__file__).parent / "kortana.yaml"
    settings = load_config(str(config_path))
    
    chat_engine = ChatEngine(settings)
    orchestrator = VoiceChatOrchestrator(
        chat_engine=chat_engine,
        stt_service=STTService(),
        tts_service=TTSService()
    )
    print("✅ Kor'tana voice system initialized!\n")
    
except Exception as e:
    print(f"❌ Error initializing Kor'tana: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Audio settings
CHUNK = 1024
FORMAT = pyaudio.paFloat32
CHANNELS = 1
RATE = 16000  # 16kHz for speech recognition
RECORD_SECONDS = 10  # Max recording length

def record_audio(duration: int = RECORD_SECONDS) -> bytes:
    """Record audio from microphone"""
    p = pyaudio.PyAudio()
    
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )
    
    print("🎤 Recording... (speak now, press Ctrl+C to stop)")
    frames = []
    
    try:
        for _ in range(0, int(RATE / CHUNK * duration)):
            data = stream.read(CHUNK)
            frames.append(data)
    except KeyboardInterrupt:
        print("⏹️  Recording stopped")
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # Convert frames to bytes
    audio_bytes = b''.join(frames)
    return audio_bytes

def play_audio(audio_b64: str):
    """Play audio response"""
    try:
        audio_bytes = base64.b64decode(audio_b64)
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
        print("🔊 Playing response...\n")
        play(audio)
    except Exception as e:
        print(f"⚠️  Could not play audio: {e}\n")

async def voice_chat():
    """Main voice chat loop"""
    print("Commands:")
    print("  - Speak naturally (10 second max per turn)")
    print("  - Press Ctrl+C to stop recording")
    print("  - Type 'quit' and press Enter to exit\n")
    
    session_id = None
    
    while True:
        try:
            input("\nPress Enter to start speaking (or type 'quit' to exit)... ")
            
            if session_id is None:
                # Get username on first turn
                user_name = input("Your name: ").strip() or "User"
            else:
                user_name = None
            
            # Record audio
            audio_bytes = record_audio()
            
            if not audio_bytes:
                print("No audio recorded, try again.\n")
                continue
            
            print("\n⏳ Processing...\n")
            
            # Process voice through orchestrator
            result = await orchestrator.process_voice_turn(
                audio_bytes=audio_bytes,
                session_id=session_id,
                user_id="voice_user",
                user_name=user_name,
                return_audio=True
            )
            
            session_id = result["session_id"]
            
            # Display transcript and response
            print(f"You said: {result['transcript']}")
            print(f"\nKor'tana: {result['response']}\n")
            
            # Play audio response if available
            if result.get("response_audio_b64"):
                play_audio(result["response_audio_b64"])
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(voice_chat())

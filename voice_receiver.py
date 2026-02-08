"""
Discord Voice Receiver for Kor'tana
Handles voice input from Discord users
"""

import asyncio
import io
import discord
from discord import opus


class VoiceReceiver(discord.VoiceClient):
    """Custom voice client that receives and processes audio"""
    
    def __init__(self, client, channel, voice_orchestrator):
        super().__init__(client, channel)
        self.voice_orchestrator = voice_orchestrator
        self.listening = True
        self.user_audio_buffers = {}
        
    async def on_voice_receive(self, user, data):
        """Called when audio data is received from a user"""
        if not self.listening or user.bot:
            return
            
        # Accumulate audio data
        if user.id not in self.user_audio_buffers:
            self.user_audio_buffers[user.id] = {
                'user': user,
                'audio': io.BytesIO(),
                'last_packet': asyncio.get_event_loop().time()
            }
        
        buffer_info = self.user_audio_buffers[user.id]
        buffer_info['audio'].write(data)
        buffer_info['last_packet'] = asyncio.get_event_loop().time()
        
    async def start_listening(self):
        """Start processing accumulated audio"""
        while self.listening:
            await asyncio.sleep(1)  # Check every second
            
            current_time = asyncio.get_event_loop().time()
            
            # Process buffers that haven't received audio in 1 second
            for user_id, buffer_info in list(self.user_audio_buffers.items()):
                if current_time - buffer_info['last_packet'] > 1.0:
                    audio_bytes = buffer_info['audio'].getvalue()
                    
                    if len(audio_bytes) > 0:
                        # Process the audio
                        await self.process_user_audio(
                            buffer_info['user'],
                            audio_bytes
                        )
                    
                    # Clear buffer
                    del self.user_audio_buffers[user_id]
    
    async def process_user_audio(self, user, audio_bytes):
        """Process received audio through voice orchestrator"""
        try:
            # Use voice orchestrator to process
            result = await self.voice_orchestrator.process_voice_turn(
                audio_bytes=audio_bytes,
                user_id=str(user.id),
                user_name=user.display_name,
                return_audio=True
            )
            
            if result.get('response_audio_b64'):
                # Play response audio back
                import base64
                response_audio = base64.b64decode(result['response_audio_b64'])
                await self.play_audio_response(response_audio)
                
        except Exception as e:
            print(f"Error processing voice from {user.name}: {e}")
    
    async def play_audio_response(self, audio_bytes):
        """Play audio response in the voice channel"""
        # Discord.py audio playing
        audio_source = discord.FFmpegPCMAudio(
            io.BytesIO(audio_bytes),
            pipe=True
        )
        self.play(audio_source)
        
        # Wait for audio to finish
        while self.is_playing():
            await asyncio.sleep(0.1)

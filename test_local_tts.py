"""Test local TTS (edge-tts)"""
import asyncio
from aionos.api.voice_synthesis import VoiceSynthesizer

async def test():
    synth = VoiceSynthesizer()
    print(f"Mode: {'CLOUD' if synth.use_cloud else 'LOCAL'}")
    print(f"Voice: {synth.voice_name}")
    
    audio = await synth.speak("AION OS online. Security threat detected.")
    if audio:
        print(f"✅ Audio generated: {len(audio):,} bytes")
        # Save to file for verification
        with open("test_audio.mp3", "wb") as f:
            f.write(audio)
        print("   Saved to test_audio.mp3")
    else:
        print("❌ Audio generation failed")

asyncio.run(test())

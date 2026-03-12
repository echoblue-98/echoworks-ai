"""
AION OS — Voice Synthesis Module (Hybrid: Local + Cloud)
Real-time voice alerts and narration for law firm intelligence platform.

Supports:
1. LOCAL (default): edge-tts (Microsoft's neural TTS, runs locally, no API key)
2. CLOUD (optional): ElevenLabs (requires ELEVENLABS_API_KEY)

Set VOICE_MODE=cloud in .env to use ElevenLabs, otherwise defaults to local.
"""

import os
import base64
import logging
import asyncio
import tempfile
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger("aionos.voice")

# Try to load from .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Check for local TTS availability
try:
    import edge_tts
    LOCAL_TTS_AVAILABLE = True
except ImportError:
    LOCAL_TTS_AVAILABLE = False
    logger.info("edge-tts not installed. Run: pip install edge-tts")

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1"
VOICE_MODE = os.environ.get("VOICE_MODE", "local").lower()  # "local" or "cloud"

# Voice presets (ElevenLabs cloud voices)
VOICES = {
    "adam": "pNInz6obpgDQGcFmaJgB",      # Professional male
    "josh": "TxGEqnHWrfWFTfGW9XjX",      # Deep male
    "rachel": "21m00Tcm4TlvDq8ikWAM",    # Professional female
    "domi": "AZnzlk1XvdvUeBnXmlld",      # Assertive female
    "arnold": "VR6AewLTigWG4xSOukaG",    # Powerful male
}

# Local edge-tts voices (Microsoft neural TTS, runs 100% locally)
LOCAL_VOICES = {
    "guy": "en-US-GuyNeural",             # Professional male news voice
    "christopher": "en-US-ChristopherNeural", # Authoritative male
    "eric": "en-US-EricNeural",           # Rational male news voice
    "brian": "en-US-BrianNeural",         # Approachable male
    "jenny": "en-US-JennyNeural",         # Professional female
    "aria": "en-US-AriaNeural",           # Confident female
    "ava": "en-US-AvaNeural",             # Friendly female
}

DEFAULT_VOICE = "arnold"  # Powerful, commanding presence (cloud)
DEFAULT_LOCAL_VOICE = "christopher"  # Authoritative male (local)
DEFAULT_MODEL = "eleven_turbo_v2_5"  # Free tier compatible


@dataclass
class VoiceSettings:
    stability: float = 0.25       # Lower = more dramatic variation
    similarity_boost: float = 0.85 # Voice fidelity
    style: float = 0.8            # High expressiveness
    use_speaker_boost: bool = True


class VoiceSynthesizer:
    """
    Hybrid voice synthesis for AION OS alerts and narration.
    
    Modes:
    - LOCAL (default): Uses edge-tts (Microsoft neural TTS). 100% sovereign.
    - CLOUD: Uses ElevenLabs API. Higher quality but requires API key.
    
    Usage:
        synth = VoiceSynthesizer()
        audio_bytes = await synth.speak("Alert. Threat detected.")
        # Send audio_bytes to frontend for playback
    """
    
    def __init__(self, api_key: Optional[str] = None, voice: str = DEFAULT_VOICE, 
                 mode: Optional[str] = None):
        self.api_key = api_key or ELEVENLABS_API_KEY
        self.mode = mode or VOICE_MODE
        
        # Determine which TTS to use
        if self.mode == "cloud" and self.api_key:
            self.use_cloud = True
            self.voice_id = VOICES.get(voice, VOICES[DEFAULT_VOICE])
            self.voice_name = voice
            logger.info(f"VoiceSynthesizer: CLOUD mode (ElevenLabs, voice={voice})")
        elif LOCAL_TTS_AVAILABLE:
            self.use_cloud = False
            self.voice_id = LOCAL_VOICES.get(voice, LOCAL_VOICES[DEFAULT_LOCAL_VOICE])
            self.voice_name = voice if voice in LOCAL_VOICES else DEFAULT_LOCAL_VOICE
            logger.info(f"VoiceSynthesizer: LOCAL mode (edge-tts, voice={self.voice_name}) — 100% sovereign")
        else:
            self.use_cloud = False
            self.voice_id = None
            self.voice_name = None
            logger.warning("VoiceSynthesizer: No TTS available. Install edge-tts: pip install edge-tts")
        
        self.settings = VoiceSettings()
        self.enabled = self.use_cloud or LOCAL_TTS_AVAILABLE
        self._session = None
    
    async def _get_session(self):
        """Lazy-load aiohttp session"""
        if self._session is None:
            import aiohttp
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self):
        """Close the HTTP session"""
        if self._session:
            await self._session.close()
            self._session = None
    
    async def speak(self, text: str, voice: Optional[str] = None) -> Optional[bytes]:
        """
        Convert text to speech audio bytes.
        
        Args:
            text: Text to synthesize
            voice: Optional voice override
            
        Returns:
            MP3 audio bytes, or None if synthesis fails
        """
        if not self.enabled:
            logger.debug(f"Voice disabled, skipping: {text[:50]}...")
            return None
        
        if self.use_cloud:
            return await self._speak_cloud(text, voice)
        else:
            return await self._speak_local(text, voice)
    
    async def _speak_local(self, text: str, voice: Optional[str] = None) -> Optional[bytes]:
        """Local TTS using edge-tts (100% sovereign, no cloud)"""
        try:
            voice_id = LOCAL_VOICES.get(voice, self.voice_id) if voice else self.voice_id
            
            # edge-tts: use save() to temp file (most reliable method)
            communicate = edge_tts.Communicate(text, voice_id)
            
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name
            
            await communicate.save(tmp_path)
            
            with open(tmp_path, "rb") as f:
                audio_bytes = f.read()
            
            import os
            os.unlink(tmp_path)
            
            if audio_bytes and len(audio_bytes) > 100:
                logger.info(f"[LOCAL TTS] Generated {len(audio_bytes)} bytes for: {text[:30]}...")
                return audio_bytes
            return None
        except Exception as e:
            logger.error(f"Local TTS failed: {e}")
            return None
    
    async def _speak_cloud(self, text: str, voice: Optional[str] = None) -> Optional[bytes]:
        """Cloud TTS using ElevenLabs API"""
        voice_id = VOICES.get(voice, self.voice_id) if voice else self.voice_id
        
        url = f"{ELEVENLABS_API_URL}/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        payload = {
            "text": text,
            "model_id": DEFAULT_MODEL,
            "voice_settings": {
                "stability": self.settings.stability,
                "similarity_boost": self.settings.similarity_boost,
                "style": self.settings.style,
                "use_speaker_boost": self.settings.use_speaker_boost
            }
        }
        
        try:
            session = await self._get_session()
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    audio_bytes = await response.read()
                    logger.info(f"Generated {len(audio_bytes)} bytes of audio for: {text[:30]}...")
                    return audio_bytes
                else:
                    error_text = await response.text()
                    logger.error(f"ElevenLabs API error {response.status}: {error_text}")
                    return None
        except Exception as e:
            logger.error(f"Voice synthesis failed: {e}")
            return None
    
    async def speak_base64(self, text: str, voice: Optional[str] = None) -> Optional[str]:
        """
        Convert text to speech and return as base64 string (for WebSocket transport).
        """
        audio_bytes = await self.speak(text, voice)
        if audio_bytes:
            return base64.b64encode(audio_bytes).decode('utf-8')
        return None
    
    def format_alert(self, pattern: str, severity: str, user: str = "") -> str:
        """Format a security alert for voice synthesis — dramatic, urgent delivery"""
        severity_words = {
            "critical": "CRITICAL BREACH",
            "high": "HIGH PRIORITY",
            "medium": "SECURITY ALERT",
            "low": "ADVISORY"
        }
        prefix = severity_words.get(severity.lower(), "ALERT")
        
        # Clean up pattern name for speech
        pattern_spoken = pattern.replace("_", " ").replace("-", " ").title()
        
        msg = f"{prefix}. {pattern_spoken}."
        if user:
            user_name = user.split("@")[0].replace(".", " ").replace("_", " ").title()
            msg += f" Subject: {user_name}. Immediate response required."
        else:
            msg += " Engaging countermeasures."
        
        return msg
    
    def format_doc_analysis(self, risk_score: int, risk_level: str, 
                           clauses: int, red_flags: int) -> str:
        """Format document analysis result for voice synthesis"""
        if risk_score >= 80:
            intro = "Document Intelligence has flagged a CRITICAL threat."
        elif risk_score >= 50:
            intro = "Contract analysis reveals significant risk exposure."
        else:
            intro = "Document scan complete."
        
        return (
            f"{intro} "
            f"Risk assessment: {risk_score} out of 100. "
            f"{clauses} contractual provisions analyzed. "
            f"{red_flags} predatory elements identified. Review recommended."
        )
    
    def format_scenario_start(self, name: str) -> str:
        """Format scenario start announcement"""
        return f"Initiating threat simulation. {name}. All sensors active."
    
    def format_scenario_complete(self, detected: bool) -> str:
        """Format scenario completion announcement"""
        if detected:
            return "Threat neutralized. AION successfully identified and contained the attack vector."
        return "Simulation complete. No breaches detected. Continuing surveillance."
    
    def format_event(self, event_type: str, user: str, event_num: int, total: int) -> str:
        """Format security event for voice narration"""
        event_spoken = event_type.replace("_", " ").lower()
        user_name = user.split("@")[0].replace(".", " ").replace("_", " ")
        return f"Event {event_num} of {total}. {event_spoken}. User: {user_name}."
    
    def format_analysis_start(self, model: str) -> str:
        """Format analysis start announcement"""
        return f"Engaging sovereign AI. Deep forensic analysis in progress."
    
    def format_analysis_complete(self, risk_score: int, latency_ms: float) -> str:
        """Format analysis complete announcement"""
        if risk_score >= 80:
            level = "CRITICAL"
        elif risk_score >= 50:
            level = "ELEVATED"
        else:
            level = "NOMINAL"
        return f"Analysis complete. Risk level: {level}. Score: {risk_score}. Processed in {int(latency_ms)} milliseconds."
    
    def format_boot(self) -> str:
        """Format system boot announcement"""
        return "AION OS online. Law firm security intelligence platform activated. All systems operational."


# Singleton instance
_synthesizer: Optional[VoiceSynthesizer] = None


def get_voice_synthesizer(api_key: Optional[str] = None, voice: str = DEFAULT_VOICE) -> VoiceSynthesizer:
    """Get or create the voice synthesizer singleton"""
    global _synthesizer
    if _synthesizer is None:
        _synthesizer = VoiceSynthesizer(api_key=api_key, voice=voice)
    return _synthesizer


async def cleanup_voice():
    """Cleanup voice synthesizer resources"""
    global _synthesizer
    if _synthesizer:
        await _synthesizer.close()
        _synthesizer = None

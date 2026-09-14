# Architecture

## Database Schema
- **None:** The application runs entirely locally in-memory without persistent storage. Chat history is stored in memory (`self.messages`) and managed dynamically to prevent overflow (retains the latest 6 messages plus the system prompt).

## API Endpoints Exposed and Used
- **Exposed:** None. This is a local CLI/voice application.
- **Used:** 
  - `ollama` (Local API/Socket): Used to interact with the local `qwen2.5:3b` model for generating sarcastic therapy responses.

## Key Business Logic Rules
- **Crisis Detection:** A hardcoded regular expression (`CRISIS_K`) intercepts any messages containing suicidal or self-harm keywords. If triggered, the bot immediately halts generation of standard AI responses and provides official crisis resources (`CRISIS_M`) verbatim.
- **Persona Preservation:** A playful, sarcastic tone is strictly enforced. The LLM is injected with a system instruction before every turn to resist "in context drift" where it might otherwise revert to a sterile, helpful AI.
- **Barge-In Interruption:** When playing text-to-speech audio, a continuous microphone listener monitors the input using WebRTC VAD. If speech is detected for >0.5s while the bot is talking, the current TTS playback is aborted and the system immediately transitions back to the listening state.
- **Rules Compliance:** Punctuation and spacing within the codebase conform to specific styling guidelines (e.g., spaces inside parentheses/brackets). Backups of core files are strictly managed.

## Current Feature Status
- **Local Chained Audio Pipeline:** Implemented. Connects `pyaudio`, `faster-whisper` (STT), `ollama` (LLM), and `piper-tts` (TTS).
- **Crisis Overrides:** Implemented.
- **Text-based Interface:** The original `bad.py` remains intact as a fallback/text-only implementation.

## Known Issues / Constraints
- **Audio Threading:** The local barge-in implementation relies on stopping the PyAudio stream instantly. This requires a stable microphone and speaker configuration without significant loopback. Echo cancellation is not natively implemented.
- **Python Compatibility:** The pipeline specifically requires Python 3.11, as newer experimental "free-threaded" features in 3.13/3.14 break native compiling for audio libraries (`pyaudio`, `webrtcvad`).
- **Latency:** Because this is a chained pipeline (Listen -> Transcribe -> Stream LLM -> Stream TTS), latency depends heavily on the local CPU/GPU performance (specifically for Whisper and Ollama).

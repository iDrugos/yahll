"""
Wake Word Listener — continuous "hey yahll" detection.
Uses sounddevice for audio capture + faster-whisper (tiny) for transcription.
Runs in a background daemon thread. Zero API keys required.
"""
import io
import os
import wave
import tempfile
import threading
import numpy as np

# Sample rate and chunk duration
SAMPLE_RATE = 16000
CHUNK_SECONDS = 2
CHUNK_SAMPLES = SAMPLE_RATE * CHUNK_SECONDS

# Wake phrases to detect (fuzzy — any substring match)
_WAKE_PHRASES = ["hey yahll", "hey yall", "heyyal", "yahll", "yall", "hey y"]


class WakeWordListener:
    """
    Listens for the wake word "hey yahll" in the background.

    Usage:
        listener = WakeWordListener(on_wake=my_callback)
        listener.start()
        ...
        listener.stop()
    """

    def __init__(self, on_wake: callable, model_size: str = "tiny"):
        self.on_wake = on_wake
        self.model_size = model_size
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._whisper = None

    def _get_whisper(self):
        """Lazy-load Whisper tiny model (separate from the base model in app.py)."""
        if self._whisper is None:
            from faster_whisper import WhisperModel
            try:
                self._whisper = WhisperModel(
                    self.model_size, device="cuda", compute_type="float16"
                )
            except Exception:
                self._whisper = WhisperModel(
                    self.model_size, device="cpu", compute_type="int8"
                )
        return self._whisper

    def start(self):
        """Start listening in a background daemon thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._listen_loop, daemon=True, name="yahll-wakeword"
        )
        self._thread.start()

    def stop(self):
        """Stop the listener and wait for the thread to finish."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

    def _listen_loop(self):
        """Main loop: record 2-sec chunks, transcribe, check for wake word."""
        try:
            import sounddevice as sd
        except ImportError:
            print("[wakeword] sounddevice not installed — wake word disabled")
            return

        # Pre-load the whisper model before entering the hot loop
        try:
            model = self._get_whisper()
        except Exception as e:
            print(f"[wakeword] Failed to load Whisper model: {e}")
            return

        print("[wakeword] Listening for 'hey yahll'...")

        while not self._stop_event.is_set():
            try:
                # Record a 2-second chunk
                audio = sd.rec(
                    CHUNK_SAMPLES,
                    samplerate=SAMPLE_RATE,
                    channels=1,
                    dtype="int16",
                    blocking=True,
                )

                if self._stop_event.is_set():
                    break

                # Check if audio has any energy (skip silence)
                energy = np.abs(audio).mean()
                if energy < 100:
                    continue

                # Write to temp WAV for Whisper
                transcript = self._transcribe_chunk(audio, model)

                if not transcript:
                    continue

                # Check for wake word
                lower = transcript.lower().strip()
                if any(phrase in lower for phrase in _WAKE_PHRASES):
                    print(f"[wakeword] Wake word detected: '{transcript.strip()}'")
                    try:
                        self.on_wake()
                    except Exception as e:
                        print(f"[wakeword] on_wake callback error: {e}")

            except Exception as e:
                if not self._stop_event.is_set():
                    print(f"[wakeword] Error in listen loop: {e}")
                    # Brief pause before retrying
                    self._stop_event.wait(1.0)

    def _transcribe_chunk(self, audio: np.ndarray, model) -> str:
        """Transcribe a numpy audio chunk using faster-whisper."""
        tmp_path = None
        try:
            # Write chunk as WAV to a temp file
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".wav"
            ) as tmp:
                tmp_path = tmp.name
                with wave.open(tmp, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)  # int16 = 2 bytes
                    wf.setframerate(SAMPLE_RATE)
                    wf.writeframes(audio.tobytes())

            # Transcribe with Whisper tiny
            segments, _ = model.transcribe(
                tmp_path, language="en", beam_size=1, vad_filter=True
            )
            return " ".join(seg.text for seg in segments)

        except Exception:
            return ""
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

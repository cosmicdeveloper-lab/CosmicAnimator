# src/cosmicanimator/application/narration/tts.py

"""
Text-to-Speech (TTS) integration for Manim scenes using Coqui TTS.

This module provides:
- `VoiceScene`: a base scene with locked-in Coqui TTS configuration.
- `start_voiceover`: a context manager to simplify narration handling.
"""

from __future__ import annotations
from contextlib import contextmanager
from typing import Optional, Union
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.coqui import CoquiService
from cosmicanimator.core.theme import current_theme as t


class VoiceScene(VoiceoverScene):
    """
    Base scene class that locks in Coqui TTS configuration.

    Once configured with `.configure_voice(...)`, the speech service
    cannot be overridden unless explicitly allowed.
    """

    _voice_locked: bool = False

    def configure_voice(
        self,
        service: Optional[CoquiService] = None,
        *,
        model: Optional[str] = None,
        speaker: Optional[Union[str, int]] = None,
        **coqui_kwargs,
    ) -> None:
        """
        Configure the Coqui TTS voice for this scene.

        Parameters
        ----------
        service : Optional[CoquiService], default=None
            Existing CoquiService to reuse. If None, a new one is created.
        model : Optional[str], default=None
            TTS model name. Falls back to theme defaults if not provided.
        speaker : str | int, optional
            Speaker identifier (string name or index).
        **coqui_kwargs :
            Extra keyword arguments passed to `CoquiService`.

        Notes
        -----
        - If a service is created, the speaker is resolved by index or name.
        - Locks the voice configuration to prevent accidental overrides.
        """
        # Fallback to theme defaults if not provided
        speaker = speaker or t.get_speaker()
        model = model or t.get_tts_model()

        if service is None:
            if model:
                coqui_kwargs["model_name"] = model

            service = CoquiService(**coqui_kwargs)

            # Resolve speaker by name or index
            if isinstance(speaker, str):
                try:
                    idx = list(service.tts.speakers).index(speaker)
                    service.speaker_idx = idx
                    try:
                        service.speaker = service.tts.speakers[idx]
                    except Exception:
                        pass
                except ValueError:
                    print(f"[configure_voice] WARNING: speaker '{speaker}' not found")
            elif isinstance(speaker, int):
                service.speaker_idx = speaker
                speakers = list(getattr(service.tts, "speakers", [])) or []
                if 0 <= speaker < len(speakers):
                    service.speaker = speakers[speaker]

            # Log active configuration
            active_model = getattr(service.tts, "model_name", None)
            print(f"[voice] model={active_model}  speaker_name={speaker}")

        self._voice_locked = True
        super().set_speech_service(service)

    def set_speech_service(self, service: CoquiService):
        """
        Override of `VoiceoverScene.set_speech_service`.

        Prevents overwriting the locked voice configuration.
        """
        if getattr(self, "_voice_locked", False):
            print("[set_speech_service] blocked override (voice already configured).")
            return
        return super().set_speech_service(service)


@contextmanager
def start_voiceover(scene: VoiceoverScene, text: str):
    """
    Context manager for starting a voiceover narration.

    Parameters
    ----------
    scene : VoiceoverScene
        The scene in which the narration is played.
    text : str
        The narration text to synthesize.

    Yields
    ------
    tracker : manim_voiceover.tracker.VoiceoverTracker
        Voiceover tracker object to synchronize animation with audio.
    """
    with scene.voiceover(text=text) as tracker:
        yield tracker

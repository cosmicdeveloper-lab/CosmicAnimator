# src/cosmicanimator/application/narration/tts.py

"""
Text-to-Speech (TTS) integration for Manim scenes using **Azure TTS**.

This module provides:
- `VoiceScene`: a base scene with locked-in Azure TTS configuration.
- `start_voiceover`: a context manager to simplify narration handling.

Notes
-----
- Requires environment variables for Azure:
  AZURE_SPEECH_KEY, AZURE_SPEECH_REGION
- Voice names look like: "en-US-JennyNeural", "en-GB-RyanNeural", etc.
"""

from __future__ import annotations
from contextlib import contextmanager
from typing import Optional, Union, Any, Dict
import os
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.azure import AzureService
from cosmicanimator.core.theme import current_theme as t
from dotenv import load_dotenv
load_dotenv()


class VoiceScene(VoiceoverScene):
    """
    Base scene class that locks in Azure TTS configuration.

    Once configured with `.configure_voice(...)`, the speech service
    cannot be overridden unless explicitly allowed.
    """

    _voice_locked: bool = False

    def configure_voice(
        self,
        service: Optional[AzureService] = None,
        *,
        # Backward-compat with Coqui-based call sites:
        speaker: Optional[Union[str, int]] = None,  # treated as 'voice' if str
        # Azure-native options:
        voice: Optional[str] = None,
        style: Optional[str] = None,
        role: Optional[str] = None,
        **azure_kwargs: Any,
    ) -> None:
        """
        Configure the Azure TTS voice for this scene.

        Parameters
        ----------
        service : Optional[AzureService], default=None
            Existing AzureService to reuse. If None, a new one is created.
        speaker : str | int, optional
            If str, treated as Azure 'voice' (e.g., "en-US-JennyNeural").
            If int, ignored (Azure voices are name-based).
        voice : str, optional
            Azure voice name (e.g., "en-US-JennyNeural"). If not provided,
            falls back to theme defaults or a sane built-in.
        style : str, optional
            Azure speaking style (e.g., "general", "newscast", ...).
        role : str, optional
            Azure speaking role (if supported by the selected voice).
        **azure_kwargs :
            Extra keyword args forwarded to `AzureService`.

        Notes
        -----
        - Locks the voice configuration to prevent accidental overrides.
        - Environment variables AZURE_SPEECH_KEY and AZURE_SPEECH_REGION must
          be set for authentication.
        """
        # Resolve voice preference (theme -> provided)
        # `t.get_speaker()` is reused to store a default Azure voice name.
        resolved_voice = (
            voice
            or (speaker if isinstance(speaker, str) else None)
            or getattr(t, "get_speaker", lambda: None)()
            or "en-US-JennyNeural"
        )

        # Optionally allow theme to provide default style via t.get_tts_style()
        if style is None and hasattr(t, "get_speaker_style"):
            try:
                style = t.get_speaker_style()
            except Exception:
                pass

        if service is None:
            # Create a fresh Azure service
            service = AzureService(
                voice=resolved_voice,
                style=style,
                role=role,
                **azure_kwargs,
            )
        else:
            # Update basic properties on a provided service (best-effort)
            # Not all fields may be mutable depending on manim-voiceover version.
            try:
                if resolved_voice:
                    service.voice = resolved_voice
                if style is not None:
                    service.style = style
                if role is not None:
                    service.role = role
                # Apply any extra kwargs as attributes if present
                for k, v in azure_kwargs.items():
                    if hasattr(service, k):
                        setattr(service, k, v)
            except Exception:
                # Non-fatal: continue with provided service as-is
                pass

            print(f"[voice] (existing AzureService) voice={getattr(service, 'voice', None)} style={getattr(service, 'style', None)} role={getattr(service, 'role', None)}")

        # Log active configuration
        print(
            "[voice] Azure configured:"
            f" voice={getattr(service, 'voice', None)}"
            f" style={getattr(service, 'style', None)}"
            f" role={getattr(service, 'role', None)}"
        )

        self._voice_locked = True
        super().set_speech_service(service)

    def set_speech_service(self, service: AzureService):
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

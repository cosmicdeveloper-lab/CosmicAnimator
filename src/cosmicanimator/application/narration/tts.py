# src/cosmoanimator/adapters/tts.py
"""
Voiceover base scene and configuration helpers.

Defines:
- `VoiceScene`: extension of VoiceoverScene with stricter Coqui voice setup
- `start_voiceover`: contextmanager wrapper for inline narration

Features:
- Explicit model + speaker selection
- Resolves string speakers ("p233") into numeric indices
- Locks voice service to prevent silent override later
"""

from contextlib import contextmanager
from typing import Optional, Union
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.coqui import CoquiService


class VoiceScene(VoiceoverScene):
    """
    Base scene with locked-in Coqui TTS configuration.

    Use `.configure_voice(...)` once at the start of a scene.
    Prevents accidental overrides (e.g. from Orchestra).
    """

    _voice_locked: bool = False  # prevents reassign after first configure

    def configure_voice(
        self,
        service: Optional[CoquiService] = None,
        *,
        model: Optional[str] = "tts_models/en/vctk/vits",
        speaker: Optional[Union[str, int]] = "p245",  # string (e.g "p245") or int index
        speaker_idx: Optional[int] = None,           # takes priority if both given
        language_idx: Optional[int] = None,
        **coqui_kwargs,
    ) -> None:
        """
        Configure and lock a Coqui voice service.

        Parameters
        ----------
        service : CoquiService, optional
            Explicit prebuilt service. If None, one is created.
        model : str, default="tts_models/en/vctk/vits"
            Model identifier string.
        speaker : str | int, default="p233"
            Preferred speaker, either a string name (like "p230")
            or an integer index. If both `speaker` and `speaker_idx` are
            provided, `speaker_idx` wins.
        speaker_idx : int, optional
            Explicit speaker index.
        language_idx : int, optional
            Optional language index for multilingual models.
        **coqui_kwargs
            Extra arguments forwarded to `CoquiService`.

        Notes
        -----
        - If `speaker` is a string, it tries to resolve it to an index
          against `service.tts.speakers`.
        - After setup, voice service is locked (`_voice_locked=True`)
          to prevent silent overrides later.
        """
        if service is None:
            if model:
                coqui_kwargs["model_name"] = model

            # Accept both int speaker or explicit speaker_idx
            if isinstance(speaker, int) and speaker_idx is None:
                speaker_idx = speaker
            if speaker_idx is not None:
                coqui_kwargs["speaker_idx"] = int(speaker_idx)
            if language_idx is not None:
                coqui_kwargs["language_idx"] = int(language_idx)

            service = CoquiService(**coqui_kwargs)

            # If speaker provided as a string, resolve it
            if isinstance(speaker, str):
                try:
                    idx = list(service.tts.speakers).index(speaker)
                    service.speaker_idx = idx
                    try:
                        service.speaker = service.tts.speakers[idx]  # some versions support this
                    except Exception:
                        pass
                except ValueError:
                    print(
                        f"[configure_voice] WARNING: speaker '{speaker}' not found in: "
                        f"{service.tts.speakers[:10]}..."
                    )

            # Debug print for active voice
            active_model = getattr(service.tts, "model_name", None)
            active_idx = getattr(service, "speaker_idx", None)
            speakers = list(getattr(service.tts, "speakers", [])) or []
            active_name = (
                speakers[active_idx]
                if speakers and isinstance(active_idx, int) and 0 <= active_idx < len(speakers)
                else None
            )
            print(f"[voice] model={active_model} speaker_idx={active_idx} speaker_name={active_name}")

        # Lock and set
        self._voice_locked = True
        super().set_speech_service(service)

    def set_speech_service(self, service):
        """
        Guarded override of speech service.

        Blocks replacing the voice service after it’s been configured
        once via `configure_voice`.
        """
        if getattr(self, "_voice_locked", False):
            print("[set_speech_service] blocked override (voice already configured).")
            return
        return super().set_speech_service(service)


@contextmanager
def start_voiceover(scene: VoiceoverScene, text: str):
    """
    Contextmanager wrapper for `scene.voiceover`.
    """
    with scene.voiceover(text=text) as tracker:
        yield tracker

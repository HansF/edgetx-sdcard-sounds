#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AzureVoiceJob:
    csv_file: str
    voice: str
    langdir: str
    pitch: str | None = None
    rate: str | None = None

    @property
    def csv_path(self) -> Path:
        return Path(self.csv_file)


@dataclass(frozen=True)
class ElevenLabsVoiceJob:
    """One ElevenLabs voice pack. langdir is the SOUNDS/ folder ("nl", "nl-emma/SCRIPTS")."""

    csv_file: str
    voice_id: str
    langdir: str
    model: str = "eleven_multilingual_v2"
    language: str = "en"        # ISO 639-1, sent to models that accept language_code
    stt_language: str = "eng"   # ISO 639-3, for the transcription check
    stability: float = 0.75
    similarity: float = 0.8
    style: float = 0.0
    speed: float = 1.0

    @property
    def csv_path(self) -> Path:
        return Path(self.csv_file)


@dataclass(frozen=True)
class GladosVoiceJob:
    csv_file: str
    langdir: str

    @property
    def csv_path(self) -> Path:
        return Path(self.csv_file)


AZURE_VOICE_JOBS: tuple[AzureVoiceJob, ...] = (
    AzureVoiceJob("./voices/cs-CZ.csv", "cs-CZ-VlastaNeural", "cz"),
    AzureVoiceJob("./voices/da_DK.csv", "da-DK-ChristelNeural", "da"),
    AzureVoiceJob("./voices/da_DK_scripts.csv", "da-DK-ChristelNeural", "da/SCRIPTS"),
    AzureVoiceJob("./voices/de-DE.csv", "de-DE-KatjaNeural", "de"),
    AzureVoiceJob("./voices/en-GB.csv", "en-IE-EmilyNeural", "en", rate="1.10"),
    AzureVoiceJob("./voices/en-GB_scripts.csv", "en-IE-EmilyNeural", "en/SCRIPTS", rate="1.10"),
    AzureVoiceJob("./voices/en-GB.csv", "en-GB-LibbyNeural", "en_gb-libby"),
    AzureVoiceJob("./voices/en-GB_scripts.csv", "en-GB-LibbyNeural", "en_gb-libby/SCRIPTS"),
    AzureVoiceJob("./voices/en-GB.csv", "en-GB-RyanNeural", "en_gb-ryan"),
    AzureVoiceJob("./voices/en-GB_scripts.csv", "en-GB-RyanNeural", "en_gb-ryan/SCRIPTS"),
    AzureVoiceJob("./voices/en-US.csv", "en-US-GuyNeural", "en_us-guy"),
    AzureVoiceJob("./voices/en-US_scripts.csv", "en-US-GuyNeural", "en_us-guy/SCRIPTS"),
    AzureVoiceJob("./voices/en-US.csv", "en-US-MichelleNeural", "en_us-michelle"),
    AzureVoiceJob("./voices/en-US_scripts.csv", "en-US-MichelleNeural", "en_us-michelle/SCRIPTS"),
    AzureVoiceJob("./voices/en-US.csv", "en-US-SaraNeural", "en_us-sara"),
    AzureVoiceJob("./voices/en-US_scripts.csv", "en-US-SaraNeural", "en_us-sara/SCRIPTS"),
    AzureVoiceJob("./voices/es-CL.csv", "es-CL-CatalinaNeural", "es_cl-catalina"),
    AzureVoiceJob("./voices/es-ES.csv", "es-ES-ElviraNeural", "es"),
    AzureVoiceJob("./voices/fr-FR.csv", "fr-FR-DeniseNeural", "fr"),
    AzureVoiceJob("./voices/it-IT.csv", "it-IT-ElsaNeural", "it"),
    AzureVoiceJob("./voices/it-IT_scripts.csv", "it-IT-ElsaNeural", "it/SCRIPTS"),
    AzureVoiceJob("./voices/ja-JP.csv", "ja-JP-NanamiNeural", "jp"),
    AzureVoiceJob("./voices/ja-JP_scripts.csv", "ja-JP-NanamiNeural", "jp/SCRIPTS"),
    AzureVoiceJob("./voices/pt-PT.csv", "pt-BR-FranciscaNeural", "pt"),
    AzureVoiceJob("./voices/ru-RU.csv", "ru-RU-SvetlanaNeural", "ru"),
    AzureVoiceJob("./voices/sv-SE.csv", "sv-SE-SofieNeural", "se", pitch="dn10%", rate="0.9"),
    AzureVoiceJob("./voices/sv-SE_scripts.csv", "sv-SE-SofieNeural", "se/SCRIPTS", pitch="dn10%", rate="0.9"),
    AzureVoiceJob("./voices/uk-UA.csv", "uk-UA-OstapNeural", "ua-ostap"),
    AzureVoiceJob("./voices/uk-UA.csv", "uk-UA-PolinaNeural", "ua-polina"),
    AzureVoiceJob("./voices/zh-CN.csv", "zh-CN-XiaoxiaoNeural", "cn"),
    AzureVoiceJob("./voices/zh-TW.csv", "zh-TW-HsiaoChenNeural", "tw"),
    AzureVoiceJob("./voices/zh-HK.csv", "zh-HK-HiuGaaiNeural", "hk", rate="0.9"),
)


GLADOS_VOICE_JOBS: tuple[GladosVoiceJob, ...] = (
    GladosVoiceJob("./voices/en-GB.csv", "en_gb-glados"),
    GladosVoiceJob("./voices/en-GB_scripts.csv", "en_gb-glados/SCRIPTS"),
)


# ElevenLabs voices. The Dutch ones come from the ElevenLabs voice library
# (Hans Claesen: Flemish male narrator; Emma: standard Dutch female), Daniel is a premade voice.
_NL = dict(language="nl", stt_language="nld")
ELEVENLABS_VOICE_JOBS: tuple[ElevenLabsVoiceJob, ...] = (
    ElevenLabsVoiceJob("./voices/nl-NL.csv", "s7Z6uboUuE4Nd8Q2nye6", "nl", **_NL),
    ElevenLabsVoiceJob("./voices/nl-NL_scripts.csv", "s7Z6uboUuE4Nd8Q2nye6", "nl/SCRIPTS", **_NL),
    ElevenLabsVoiceJob("./voices/nl-NL.csv", "OlBRrVAItyi00MuGMbna", "nl-emma", **_NL),
    ElevenLabsVoiceJob("./voices/nl-NL_scripts.csv", "OlBRrVAItyi00MuGMbna", "nl-emma/SCRIPTS", **_NL),
    ElevenLabsVoiceJob("./voices/en-GB.csv", "onwK4e9ZLuTAKqWW03F9", "en_gb-daniel"),
    ElevenLabsVoiceJob("./voices/en-GB_scripts.csv", "onwK4e9ZLuTAKqWW03F9", "en_gb-daniel/SCRIPTS"),
    # regional voices from the library: Flemish female, Australian, Scottish
    ElevenLabsVoiceJob("./voices/nl-NL.csv", "ANHrhmaFeVN0QJaa0PhL", "nl-petra", **_NL),
    ElevenLabsVoiceJob("./voices/nl-NL_scripts.csv", "ANHrhmaFeVN0QJaa0PhL", "nl-petra/SCRIPTS", **_NL),
    ElevenLabsVoiceJob("./voices/en-US.csv", "aEO01A4wXwd1O8GPgGlF", "en_au-arabella"),
    ElevenLabsVoiceJob("./voices/en-US_scripts.csv", "aEO01A4wXwd1O8GPgGlF", "en_au-arabella/SCRIPTS"),
    ElevenLabsVoiceJob("./voices/en-GB.csv", "U5UjeJMsOvyhYhXfZdvZ", "en_sc-adam"),
    ElevenLabsVoiceJob("./voices/en-GB_scripts.csv", "U5UjeJMsOvyhYhXfZdvZ", "en_sc-adam/SCRIPTS"),
    # regional voices, round two: Irish English, Swiss German, Belgian and Quebec French, Mexican Spanish
    ElevenLabsVoiceJob("./voices/en-GB.csv", "qwaVDEGNsBllYcZO1ZOJ", "en_ie-patrick"),
    ElevenLabsVoiceJob("./voices/en-GB_scripts.csv", "qwaVDEGNsBllYcZO1ZOJ", "en_ie-patrick/SCRIPTS"),
    ElevenLabsVoiceJob("./voices/de-DE.csv", "GgV5QStPLpmkN7FOHJtY", "de_ch-peter", language="de", stt_language="deu"),
    ElevenLabsVoiceJob("./voices/fr-FR.csv", "HDc7042zGcc1SdpT2m1U", "fr_be-christophe", language="fr", stt_language="fra"),
    ElevenLabsVoiceJob("./voices/fr-FR.csv", "FVQMzxJGPUBtfz1Azdoy", "fr_ca-danielle", language="fr", stt_language="fra"),
    ElevenLabsVoiceJob("./voices/es-ES.csv", "gbTn1bmCvNgk0QEAVyfM", "es_mx-enrique", language="es", stt_language="spa"),
    ElevenLabsVoiceJob("./voices/es-ES_scripts.csv", "gbTn1bmCvNgk0QEAVyfM", "es_mx-enrique/SCRIPTS", language="es", stt_language="spa"),
    # round three: British female (premade Alice), European Portuguese
    ElevenLabsVoiceJob("./voices/en-GB.csv", "Xb7hH8MSUJpSbSDYk0k2", "en_gb-alice"),
    ElevenLabsVoiceJob("./voices/en-GB_scripts.csv", "Xb7hH8MSUJpSbSDYk0k2", "en_gb-alice/SCRIPTS"),
    ElevenLabsVoiceJob("./voices/pt-PT.csv", "aLFUti4k8YKvtQGXv0UO", "pt_pt-paulo", language="pt", stt_language="por"),
    # Polish (Sarah) was generated by hand with the old script; kept out so it is never re-billed.
)

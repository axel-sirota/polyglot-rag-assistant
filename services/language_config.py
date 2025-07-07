"""
Language configuration for Deepgram Nova models in LiveKit Polyglot RAG Assistant
Author: Claude Code
Date: 2025-07-07

This module provides comprehensive language support configuration for Deepgram Nova-3 and Nova-2 models.
"""

from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Definitive language mapping for Deepgram Nova models
DEEPGRAM_LANGUAGE_MAP = {
    # Nova-3 English-only mode (best for English)
    "en": {"model": "nova-3", "language": "en"},
    "en-US": {"model": "nova-3", "language": "en"},
    "en-GB": {"model": "nova-3", "language": "en"},
    "en-AU": {"model": "nova-3", "language": "en"},
    "en-IN": {"model": "nova-3", "language": "en"},
    "en-NZ": {"model": "nova-3", "language": "en"},
    
    # Languages supported by both Nova-3 multi and Nova-2
    # For single-language use, Nova-2 is recommended for better accuracy
    "es": {"model": "nova-2", "language": "es"},
    "es-ES": {"model": "nova-2", "language": "es"},
    "es-419": {"model": "nova-2", "language": "es-419"},
    "fr": {"model": "nova-2", "language": "fr"},
    "fr-CA": {"model": "nova-2", "language": "fr-CA"},
    "de": {"model": "nova-2", "language": "de"},
    "it": {"model": "nova-2", "language": "it"},
    "pt": {"model": "nova-2", "language": "pt"},
    "pt-BR": {"model": "nova-2", "language": "pt-BR"},
    "pt-PT": {"model": "nova-2", "language": "pt"},
    "nl": {"model": "nova-2", "language": "nl"},
    "hi": {"model": "nova-2", "language": "hi"},
    "ja": {"model": "nova-2", "language": "ja"},
    "ko": {"model": "nova-2", "language": "ko"},
    
    # Languages only supported by Nova-2 (not in Nova-3 multi)
    "zh": {"model": "nova-2", "language": "zh"},
    "zh-CN": {"model": "nova-2", "language": "zh-CN"},
    "zh-TW": {"model": "nova-2", "language": "zh-TW"},
    "ar": {"model": "nova-2", "language": "ar"},
    "ru": {"model": "nova-2", "language": "ru"},
    "tr": {"model": "nova-2", "language": "tr"},
    "pl": {"model": "nova-2", "language": "pl"},
    "uk": {"model": "nova-2", "language": "uk"},
    "cs": {"model": "nova-2", "language": "cs"},
    "sv": {"model": "nova-2", "language": "sv"},
    "da": {"model": "nova-2", "language": "da"},
    "no": {"model": "nova-2", "language": "no"},
    "fi": {"model": "nova-2", "language": "fi"},
    "id": {"model": "nova-2", "language": "id"},
    "ms": {"model": "nova-2", "language": "ms"},
    "th": {"model": "nova-2", "language": "th"},
    "vi": {"model": "nova-2", "language": "vi"},
    "he": {"model": "nova-2", "language": "he"},
    "el": {"model": "nova-2", "language": "el"},
    "ro": {"model": "nova-2", "language": "ro"},
    "hu": {"model": "nova-2", "language": "hu"},
    "bg": {"model": "nova-2", "language": "bg"},
    "ca": {"model": "nova-2", "language": "ca"},
    
    # Special case: multilingual/code-switching
    "multi": {"model": "nova-3", "language": "multi"},
    "multilingual": {"model": "nova-3", "language": "multi"},
}

# Languages NOT supported by either Nova model
UNSUPPORTED_LANGUAGES = {
    # Major African Languages (except Arabic which IS supported)
    "sw": "Swahili",
    "yo": "Yoruba", 
    "ig": "Igbo",
    "ha": "Hausa",
    "am": "Amharic",
    "om": "Oromo",
    "ti": "Tigrinya",
    "zu": "Zulu",
    "xh": "Xhosa",
    "af": "Afrikaans",
    "so": "Somali",
    "rw": "Kinyarwanda",
    "mg": "Malagasy",
    "ln": "Lingala",
    
    # Major Asian Languages (not in Nova)
    "bn": "Bengali/Bangla",
    "ur": "Urdu",
    "pa": "Punjabi",
    "gu": "Gujarati",
    "mr": "Marathi",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "si": "Sinhala",
    "ne": "Nepali",
    "my": "Burmese/Myanmar",
    "km": "Khmer/Cambodian",
    "lo": "Lao",
    "ka": "Georgian",
    "hy": "Armenian",
    "az": "Azerbaijani",
    "kk": "Kazakh",
    "ky": "Kyrgyz",
    "uz": "Uzbek",
    "tg": "Tajik",
    "mn": "Mongolian",
    "bo": "Tibetan",
    
    # European Languages (not in Nova)
    "is": "Icelandic",
    "ga": "Irish Gaelic",
    "gd": "Scottish Gaelic",
    "cy": "Welsh",
    "eu": "Basque",
    "gl": "Galician",
    "mt": "Maltese",
    "sq": "Albanian",
    "mk": "Macedonian",
    "sr": "Serbian",
    "hr": "Croatian",
    "bs": "Bosnian",
    "sl": "Slovenian",
    "sk": "Slovak",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "et": "Estonian",
    
    # Middle Eastern Languages (except Arabic, Hebrew, Turkish)
    "fa": "Persian/Farsi",
    "ps": "Pashto",
    "ku": "Kurdish",
    
    # Pacific Languages
    "tl": "Tagalog/Filipino",
    "ceb": "Cebuano",
    "haw": "Hawaiian",
    "mi": "Māori",
    "sm": "Samoan",
    "to": "Tongan",
    "fj": "Fijian",
    
    # Native American Languages
    "nv": "Navajo",
    "chr": "Cherokee",
    "iu": "Inuktitut",
    "oj": "Ojibwe",
    "cr": "Cree",
    "qu": "Quechua",
    "gn": "Guarani",
    
    # Constructed Languages
    "eo": "Esperanto",
    "ia": "Interlingua",
    "vo": "Volapük",
    
    # Creoles and Pidgins
    "ht": "Haitian Creole",
    "jam": "Jamaican Patois",
    "tpi": "Tok Pisin",
    "pap": "Papiamento",
    
    # Other Major Languages
    "yi": "Yiddish",
    "fo": "Faroese",
    "lb": "Luxembourgish",
    "rm": "Romansh",
    "co": "Corsican",
    "oc": "Occitan",
    "br": "Breton",
    "ast": "Asturian",
    "an": "Aragonese"
}

# List of all supported language codes for UI display
SUPPORTED_LANGUAGE_CODES = sorted(list(DEEPGRAM_LANGUAGE_MAP.keys()))

# Human-readable language names for UI
LANGUAGE_NAMES = {
    "en": "English",
    "en-US": "English (US)",
    "en-GB": "English (UK)",
    "en-AU": "English (Australian)",
    "en-IN": "English (Indian)",
    "en-NZ": "English (New Zealand)",
    "es": "Spanish",
    "es-ES": "Spanish (Spain)",
    "es-419": "Spanish (Latin America)",
    "fr": "French",
    "fr-CA": "French (Canadian)",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "pt-BR": "Portuguese (Brazilian)",
    "pt-PT": "Portuguese (European)",
    "nl": "Dutch",
    "hi": "Hindi",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
    "zh-CN": "Chinese (Simplified)",
    "zh-TW": "Chinese (Traditional)",
    "ar": "Arabic",
    "ru": "Russian",
    "tr": "Turkish",
    "pl": "Polish",
    "uk": "Ukrainian",
    "cs": "Czech",
    "sv": "Swedish",
    "da": "Danish",
    "no": "Norwegian",
    "fi": "Finnish",
    "id": "Indonesian",
    "ms": "Malay",
    "th": "Thai",
    "vi": "Vietnamese",
    "he": "Hebrew",
    "el": "Greek",
    "ro": "Romanian",
    "hu": "Hungarian",
    "bg": "Bulgarian",
    "ca": "Catalan",
    "multi": "Multilingual",
    "multilingual": "Multilingual (Code-switching)"
}


def get_deepgram_config(language_code: str, is_codeswitching: bool = False) -> Optional[Dict[str, str]]:
    """
    Get the optimal Deepgram model and language configuration.
    
    Args:
        language_code: BCP-47 language code (e.g., "es", "en-US", "zh-CN")
        is_codeswitching: Whether the audio contains multiple languages
    
    Returns:
        Dict with "model" and "language" keys for Deepgram configuration,
        or None if language is not supported
    """
    # If code-switching/multilingual is needed, always use Nova-3 multi
    if is_codeswitching or language_code in ["multi", "multilingual"]:
        return {"model": "nova-3", "language": "multi"}
    
    # Check if language is unsupported
    if language_code in UNSUPPORTED_LANGUAGES:
        logger.warning(f"Language '{language_code}' ({UNSUPPORTED_LANGUAGES[language_code]}) is not supported by Deepgram Nova")
        return None
    
    # Try exact match first
    if language_code in DEEPGRAM_LANGUAGE_MAP:
        return DEEPGRAM_LANGUAGE_MAP[language_code]
    
    # Try base language code (e.g., "es" from "es-MX")
    base_language = language_code.split("-")[0]
    if base_language in DEEPGRAM_LANGUAGE_MAP:
        logger.info(f"Using base language '{base_language}' for '{language_code}'")
        return DEEPGRAM_LANGUAGE_MAP[base_language]
    
    # Check if it's an unsupported base language
    if base_language in UNSUPPORTED_LANGUAGES:
        logger.warning(f"Language '{base_language}' ({UNSUPPORTED_LANGUAGES[base_language]}) is not supported by Deepgram Nova")
        return None
    
    # Unknown language - log warning
    logger.warning(f"Unknown language code '{language_code}' - not in supported or unsupported lists")
    return None


def is_language_supported(language_code: str) -> bool:
    """
    Check if a language is supported by Deepgram Nova models.
    
    Args:
        language_code: BCP-47 language code
    
    Returns:
        True if supported, False otherwise
    """
    config = get_deepgram_config(language_code)
    return config is not None


def get_language_name(language_code: str) -> str:
    """
    Get the human-readable name for a language code.
    
    Args:
        language_code: BCP-47 language code
    
    Returns:
        Human-readable language name
    """
    if language_code in LANGUAGE_NAMES:
        return LANGUAGE_NAMES[language_code]
    
    if language_code in UNSUPPORTED_LANGUAGES:
        return UNSUPPORTED_LANGUAGES[language_code]
    
    # Try base language
    base_language = language_code.split("-")[0]
    if base_language in LANGUAGE_NAMES:
        return f"{LANGUAGE_NAMES[base_language]} ({language_code})"
    
    if base_language in UNSUPPORTED_LANGUAGES:
        return UNSUPPORTED_LANGUAGES[base_language]
    
    return language_code.upper()


def get_supported_languages_for_ui() -> list[Tuple[str, str]]:
    """
    Get a list of supported languages for UI dropdowns.
    
    Returns:
        List of tuples (language_code, display_name) sorted by display name
    """
    languages = []
    for code in SUPPORTED_LANGUAGE_CODES:
        # Skip duplicate entries for base languages
        if "-" in code and code.split("-")[0] in SUPPORTED_LANGUAGE_CODES:
            continue
        languages.append((code, get_language_name(code)))
    
    # Sort by display name, but keep English first
    english_langs = [(c, n) for c, n in languages if c.startswith("en")]
    other_langs = [(c, n) for c, n in languages if not c.startswith("en")]
    
    english_langs.sort(key=lambda x: x[1])
    other_langs.sort(key=lambda x: x[1])
    
    return english_langs + other_langs


def log_language_configuration(language_code: str, config: Optional[Dict[str, str]]):
    """
    Log detailed language configuration for debugging.
    
    Args:
        language_code: The requested language code
        config: The resulting Deepgram configuration (or None)
    """
    if config:
        logger.info(f"🌐 Language Configuration:")
        logger.info(f"   Requested: {language_code} ({get_language_name(language_code)})")
        logger.info(f"   Deepgram Model: {config['model']}")
        logger.info(f"   Deepgram Language: {config['language']}")
        if config['model'] == 'nova-3' and config['language'] == 'multi':
            logger.info(f"   Supports: English, Spanish, French, German, Italian, Portuguese, Dutch, Hindi, Japanese, Korean")
        elif config['model'] == 'nova-3' and config['language'] == 'en':
            logger.info(f"   Optimized for: English-only speech")
        else:
            logger.info(f"   Optimized for: {get_language_name(language_code)} speech")
    else:
        logger.warning(f"❌ Language Not Supported:")
        logger.warning(f"   Requested: {language_code} ({get_language_name(language_code)})")
        logger.warning(f"   This language is not supported by Deepgram Nova models")
        logger.warning(f"   Consider using 'multi' mode for mixed-language support")
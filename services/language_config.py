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


# Flight assistant greetings for all supported languages
FLIGHT_ASSISTANT_GREETINGS = {
    # English variants
    "en": "Hello! I'm your multilingual flight search assistant. How can I help you find flights today?",
    "en-US": "Hello! I'm your multilingual flight search assistant. How can I help you find flights today?",
    "en-GB": "Hello! I'm your multilingual flight search assistant. How can I help you find flights today?",
    "en-AU": "G'day! I'm your multilingual flight search assistant. How can I help you find flights today?",
    "en-IN": "Hello! I'm your multilingual flight search assistant. How can I help you find flights today?",
    "en-NZ": "Kia ora! I'm your multilingual flight search assistant. How can I help you find flights today?",
    
    # Spanish variants
    "es": "¡Hola! Soy tu asistente multilingüe de búsqueda de vuelos. ¿Cómo puedo ayudarte a encontrar vuelos hoy?",
    "es-ES": "¡Hola! Soy tu asistente multilingüe de búsqueda de vuelos. ¿Cómo puedo ayudarte a encontrar vuelos hoy?",
    "es-419": "¡Hola! Soy tu asistente multilingüe de búsqueda de vuelos. ¿Cómo puedo ayudarte a encontrar vuelos hoy?",
    
    # French variants
    "fr": "Bonjour! Je suis votre assistant multilingue de recherche de vols. Comment puis-je vous aider à trouver des vols aujourd'hui?",
    "fr-CA": "Bonjour! Je suis votre assistant multilingue de recherche de vols. Comment puis-je vous aider à trouver des vols aujourd'hui?",
    
    # German
    "de": "Hallo! Ich bin Ihr mehrsprachiger Flugsuche-Assistent. Wie kann ich Ihnen heute bei der Flugsuche helfen?",
    
    # Italian
    "it": "Ciao! Sono il tuo assistente multilingue per la ricerca di voli. Come posso aiutarti a trovare voli oggi?",
    
    # Portuguese variants
    "pt": "Olá! Sou seu assistente multilíngue de busca de voos. Como posso ajudá-lo a encontrar voos hoje?",
    "pt-BR": "Olá! Sou seu assistente multilíngue de busca de voos. Como posso ajudá-lo a encontrar voos hoje?",
    "pt-PT": "Olá! Sou o seu assistente multilingue de pesquisa de voos. Como posso ajudá-lo a encontrar voos hoje?",
    
    # Dutch
    "nl": "Hallo! Ik ben uw meertalige vluchtzoekassistent. Hoe kan ik u vandaag helpen met het vinden van vluchten?",
    
    # Hindi
    "hi": "नमस्ते! मैं आपका बहुभाषी उड़ान खोज सहायक हूं। आज मैं आपको उड़ानें खोजने में कैसे मदद कर सकता हूं?",
    
    # Japanese
    "ja": "こんにちは！私はあなたの多言語フライト検索アシスタントです。今日はどのようにフライトを探すお手伝いをしましょうか？",
    
    # Korean
    "ko": "안녕하세요! 저는 다국어 항공편 검색 도우미입니다. 오늘 항공편을 찾는 데 어떻게 도와드릴까요?",
    
    # Chinese variants
    "zh": "你好！我是您的多语言航班搜索助手。今天我如何帮助您寻找航班？",
    "zh-CN": "你好！我是您的多语言航班搜索助手。今天我如何帮助您寻找航班？",
    "zh-TW": "你好！我是您的多語言航班搜尋助手。今天我如何幫助您尋找航班？",
    
    # Arabic
    "ar": "مرحباً! أنا مساعدك متعدد اللغات للبحث عن الرحلات الجوية. كيف يمكنني مساعدتك في العثور على رحلات اليوم؟",
    
    # Russian
    "ru": "Здравствуйте! Я ваш многоязычный помощник по поиску рейсов. Как я могу помочь вам найти рейсы сегодня?",
    
    # Turkish
    "tr": "Merhaba! Ben çok dilli uçuş arama asistanınızım. Bugün size uçuş bulmada nasıl yardımcı olabilirim?",
    
    # Polish
    "pl": "Cześć! Jestem twoim wielojęzycznym asystentem wyszukiwania lotów. Jak mogę pomóc ci znaleźć loty dzisiaj?",
    
    # Ukrainian
    "uk": "Привіт! Я ваш багатомовний помічник з пошуку рейсів. Як я можу допомогти вам знайти рейси сьогодні?",
    
    # Czech
    "cs": "Ahoj! Jsem váš vícejazyčný asistent pro vyhledávání letů. Jak vám mohu dnes pomoci najít lety?",
    
    # Swedish
    "sv": "Hej! Jag är din flerspråkiga flygsökningsassistent. Hur kan jag hjälpa dig att hitta flyg idag?",
    
    # Danish
    "da": "Hej! Jeg er din flersprogede flysøgningsassistent. Hvordan kan jeg hjælpe dig med at finde fly i dag?",
    
    # Norwegian
    "no": "Hei! Jeg er din flerspråklige flysøkassistent. Hvordan kan jeg hjelpe deg med å finne flyreiser i dag?",
    
    # Finnish
    "fi": "Hei! Olen monikielinen lentohakuavustajasi. Miten voin auttaa sinua löytämään lentoja tänään?",
    
    # Indonesian
    "id": "Halo! Saya asisten pencarian penerbangan multibahasa Anda. Bagaimana saya bisa membantu Anda menemukan penerbangan hari ini?",
    
    # Malay
    "ms": "Halo! Saya pembantu carian penerbangan berbilang bahasa anda. Bagaimana saya boleh membantu anda mencari penerbangan hari ini?",
    
    # Thai
    "th": "สวัสดี! ฉันเป็นผู้ช่วยค้นหาเที่ยวบินหลายภาษาของคุณ วันนี้ฉันจะช่วยคุณค้นหาเที่ยวบินอย่างไรดี?",
    
    # Vietnamese
    "vi": "Xin chào! Tôi là trợ lý tìm kiếm chuyến bay đa ngôn ngữ của bạn. Hôm nay tôi có thể giúp bạn tìm chuyến bay như thế nào?",
    
    # Hebrew
    "he": "שלום! אני העוזר הרב-לשוני שלך לחיפוש טיסות. איך אוכל לעזור לך למצוא טיסות היום?",
    
    # Greek
    "el": "Γεια σας! Είμαι ο πολύγλωσσος βοηθός αναζήτησης πτήσεών σας. Πώς μπορώ να σας βοηθήσω να βρείτε πτήσεις σήμερα;",
    
    # Romanian
    "ro": "Bună! Sunt asistentul tău multilingv pentru căutarea zborurilor. Cum vă pot ajuta să găsiți zboruri astăzi?",
    
    # Hungarian
    "hu": "Helló! Én vagyok a többnyelvű repüléskereső asszisztensed. Hogyan segíthetek ma repülőjegyeket találni?",
    
    # Bulgarian
    "bg": "Здравейте! Аз съм вашият многоезичен асистент за търсене на полети. Как мога да ви помогна да намерите полети днес?",
    
    # Catalan
    "ca": "Hola! Sóc el teu assistent multilingüe de cerca de vols. Com et puc ajudar a trobar vols avui?",
    
    # Multilingual
    "multi": "Hello! Hola! Bonjour! 你好! I'm your multilingual flight search assistant. I can help you find flights in many languages. What language would you prefer?",
    "multilingual": "Hello! Hola! Bonjour! 你好! I'm your multilingual flight search assistant. I can help you find flights in many languages. What language would you prefer?"
}


def get_greeting(language_code: str) -> str:
    """
    Get the appropriate greeting for a given language.
    
    Args:
        language_code: BCP-47 language code
        
    Returns:
        The greeting message in the specified language, or English as fallback
    """
    # Try exact match first
    if language_code in FLIGHT_ASSISTANT_GREETINGS:
        return FLIGHT_ASSISTANT_GREETINGS[language_code]
    
    # Try base language
    base_language = language_code.split("-")[0]
    if base_language in FLIGHT_ASSISTANT_GREETINGS:
        return FLIGHT_ASSISTANT_GREETINGS[base_language]
    
    # Default to English
    return FLIGHT_ASSISTANT_GREETINGS["en"]


# Welcome back messages for reconnecting users
FLIGHT_ASSISTANT_WELCOME_BACK = {
    # English variants
    "en": "Welcome back! I'm still here. How can I continue helping you with your flight search?",
    "en-US": "Welcome back! I'm still here. How can I continue helping you with your flight search?",
    "en-GB": "Welcome back! I'm still here. How can I continue helping you with your flight search?",
    "en-AU": "Welcome back, mate! I'm still here. How can I continue helping you with your flight search?",
    "en-IN": "Welcome back! I'm still here. How can I continue helping you with your flight search?",
    "en-NZ": "Welcome back! I'm still here. How can I continue helping you with your flight search?",
    
    # Spanish variants
    "es": "¡Bienvenido de nuevo! Sigo aquí. ¿Cómo puedo seguir ayudándote con tu búsqueda de vuelos?",
    "es-ES": "¡Bienvenido de nuevo! Sigo aquí. ¿Cómo puedo seguir ayudándote con tu búsqueda de vuelos?",
    "es-419": "¡Bienvenido de nuevo! Sigo aquí. ¿Cómo puedo seguir ayudándote con tu búsqueda de vuelos?",
    
    # French variants
    "fr": "Bon retour! Je suis toujours là. Comment puis-je continuer à vous aider avec votre recherche de vol?",
    "fr-CA": "Bon retour! Je suis toujours là. Comment puis-je continuer à vous aider avec votre recherche de vol?",
    
    # German
    "de": "Willkommen zurück! Ich bin immer noch hier. Wie kann ich Ihnen weiterhin bei Ihrer Flugsuche helfen?",
    
    # Italian
    "it": "Bentornato! Sono ancora qui. Come posso continuare ad aiutarti con la ricerca del volo?",
    
    # Portuguese variants
    "pt": "Bem-vindo de volta! Ainda estou aqui. Como posso continuar ajudando com sua busca de voos?",
    "pt-BR": "Bem-vindo de volta! Ainda estou aqui. Como posso continuar ajudando com sua busca de voos?",
    "pt-PT": "Bem-vindo de volta! Ainda estou aqui. Como posso continuar a ajudá-lo com a sua pesquisa de voos?",
    
    # Dutch
    "nl": "Welkom terug! Ik ben er nog steeds. Hoe kan ik u verder helpen met uw vluchtzoekopdracht?",
    
    # Hindi
    "hi": "वापस आने का स्वागत है! मैं अभी भी यहाँ हूँ। मैं आपकी उड़ान खोज में कैसे मदद कर सकता हूँ?",
    
    # Japanese
    "ja": "おかえりなさい！まだここにいます。フライト検索を続けるお手伝いをしましょうか？",
    
    # Korean
    "ko": "다시 오신 것을 환영합니다! 아직 여기 있습니다. 항공편 검색을 계속 도와드릴까요?",
    
    # Chinese variants
    "zh": "欢迎回来！我还在这里。我如何继续帮助您搜索航班？",
    "zh-CN": "欢迎回来！我还在这里。我如何继续帮助您搜索航班？",
    "zh-TW": "歡迎回來！我還在這裡。我如何繼續幫助您搜尋航班？",
    
    # Arabic
    "ar": "مرحباً بعودتك! ما زلت هنا. كيف يمكنني الاستمرار في مساعدتك في البحث عن رحلتك؟",
    
    # Russian
    "ru": "С возвращением! Я все еще здесь. Как я могу продолжить помогать вам с поиском рейсов?",
    
    # Turkish
    "tr": "Tekrar hoş geldiniz! Hala buradayım. Uçuş aramanızda size nasıl yardımcı olmaya devam edebilirim?",
    
    # Polish
    "pl": "Witamy ponownie! Wciąż tu jestem. Jak mogę dalej pomóc w wyszukiwaniu lotów?",
    
    # Ukrainian
    "uk": "З поверненням! Я все ще тут. Як я можу продовжити допомагати вам з пошуком рейсів?",
    
    # Czech
    "cs": "Vítejte zpět! Pořád jsem tady. Jak vám mohu dále pomoci s vyhledáváním letů?",
    
    # Swedish
    "sv": "Välkommen tillbaka! Jag är fortfarande här. Hur kan jag fortsätta hjälpa dig med din flygsökning?",
    
    # Danish
    "da": "Velkommen tilbage! Jeg er stadig her. Hvordan kan jeg fortsætte med at hjælpe dig med din flysøgning?",
    
    # Norwegian
    "no": "Velkommen tilbake! Jeg er fortsatt her. Hvordan kan jeg fortsette å hjelpe deg med flysøket ditt?",
    
    # Finnish
    "fi": "Tervetuloa takaisin! Olen edelleen täällä. Miten voin jatkaa lentohaun avustamista?",
    
    # Indonesian
    "id": "Selamat datang kembali! Saya masih di sini. Bagaimana saya bisa terus membantu pencarian penerbangan Anda?",
    
    # Malay
    "ms": "Selamat kembali! Saya masih di sini. Bagaimana saya boleh terus membantu carian penerbangan anda?",
    
    # Thai
    "th": "ยินดีต้อนรับกลับมา! ฉันยังอยู่ที่นี่ วันนี้ฉันจะช่วยค้นหาเที่ยวบินต่อได้อย่างไร?",
    
    # Vietnamese
    "vi": "Chào mừng trở lại! Tôi vẫn ở đây. Tôi có thể tiếp tục giúp bạn tìm kiếm chuyến bay như thế nào?",
    
    # Hebrew
    "he": "ברוך שובך! אני עדיין כאן. איך אוכל להמשיך לעזור לך בחיפוש הטיסות שלך?",
    
    # Greek
    "el": "Καλώς ήρθατε πίσω! Είμαι ακόμα εδώ. Πώς μπορώ να συνεχίσω να σας βοηθώ με την αναζήτηση πτήσης;",
    
    # Romanian
    "ro": "Bine ați revenit! Sunt încă aici. Cum vă pot ajuta în continuare cu căutarea zborului?",
    
    # Hungarian
    "hu": "Üdvözlöm újra! Még mindig itt vagyok. Hogyan segíthetek tovább a repülőjegy keresésében?",
    
    # Bulgarian
    "bg": "Добре дошли отново! Все още съм тук. Как мога да продължа да ви помагам с търсенето на полети?",
    
    # Catalan
    "ca": "Benvingut de nou! Encara sóc aquí. Com puc continuar ajudant-te amb la cerca de vols?",
    
    # Multilingual
    "multi": "Welcome back! Bon retour! ¡Bienvenido! 欢迎回来! I'm still here to help you in any language you prefer.",
    "multilingual": "Welcome back! Bon retour! ¡Bienvenido! 欢迎回来! I'm still here to help you in any language you prefer."
}


def get_welcome_back_message(language_code: str) -> str:
    """
    Get the appropriate welcome back message for a given language.
    
    Args:
        language_code: BCP-47 language code
        
    Returns:
        The welcome back message in the specified language, or English as fallback
    """
    # Try exact match first
    if language_code in FLIGHT_ASSISTANT_WELCOME_BACK:
        return FLIGHT_ASSISTANT_WELCOME_BACK[language_code]
    
    # Try base language
    base_language = language_code.split("-")[0]
    if base_language in FLIGHT_ASSISTANT_WELCOME_BACK:
        return FLIGHT_ASSISTANT_WELCOME_BACK[base_language]
    
    # Default to English
    return FLIGHT_ASSISTANT_WELCOME_BACK["en"]
"""
Text normalizer for profanity detection — V4.1.

Goal: reduce a message to a canonical form so bypass tricks all collapse
to the same string that is then matched against the dictionary.

Bypass tricks handled
---------------------
1. Arabic diacritics (tashkeel) stripped.
2. All Arabic letter-variant forms unified → canonical base letter.
3. Zero-width / invisible Unicode chars stripped (ZWJ, ZWNJ, ZWSP, soft-hyphen, etc.).
4. Punctuation, symbols, and decorative chars stripped (users insert ., -, *, _ between letters).
5. Spaces removed entirely (catches spaced-out: ك ل ب → كلب).
6. Consecutive repeated characters collapsed to one (كللللب → كلب).
7. Common Latin → Arabic lookalike substitutions (e.g. "8" → ب-like, "v" → ف).
8. Lowercased so Latin mixed-in is case-insensitive.

Usage
-----
    from utils.profanity.normalizer import normalize
    normalized_text = normalize(raw_message_text)
"""

from __future__ import annotations

import re
import unicodedata

# ---------------------------------------------------------------------------
# 1. Arabic diacritics (tashkeel + extended marks)
# ---------------------------------------------------------------------------
_DIACRITICS_RE = re.compile(
    r"[\u0610-\u061A"   # Arabic sign ... letters
    r"\u064B-\u065F"    # fathatan → wavy hamza below (standard tashkeel)
    r"\u0670"           # superscript alef
    r"\u06D6-\u06DC"    # small high ligature → small high meem
    r"\u06DF-\u06E4"    # small high rounded zero → small high madda
    r"\u06E7\u06E8"
    r"\u06EA-\u06ED"    # empty centre low → arabic small low meem
    r"]",
    re.UNICODE,
)

# ---------------------------------------------------------------------------
# 2. Zero-width & invisible Unicode characters
# ---------------------------------------------------------------------------
_INVISIBLE_RE = re.compile(
    r"[\u200B-\u200F"   # ZWSP, ZWN-joiner, ZW-joiner, LRM, RLM
    r"\u202A-\u202F"    # LRE, RLE, PDF, LRO, RLO, NNBSP
    r"\u2060-\u2064"    # WJ, function application, ...
    r"\uFEFF"           # BOM / ZWNBSP
    r"\u00AD"           # soft hyphen
    r"]",
    re.UNICODE,
)

# ---------------------------------------------------------------------------
# 3. Arabic letter normalization map
#    Variant/decorated forms → single canonical base character.
# ---------------------------------------------------------------------------
_ARABIC_NORM: dict[str, str] = {
    # Alef variants → plain alef
    "\u0623": "\u0627",  # أ → ا
    "\u0625": "\u0627",  # إ → ا
    "\u0622": "\u0627",  # آ → ا
    "\u0671": "\u0627",  # ٱ → ا
    "\u0672": "\u0627",  # ٲ → ا
    "\u0673": "\u0627",  # ٳ → ا
    "\u0675": "\u0627",  # ٵ → ا
    # Taa marbuta → haa
    "\u0629": "\u0647",  # ة → ه
    # Alef maqsura → yaa
    "\u0649": "\u064A",  # ى → ي
    # Waw variants
    "\u0624": "\u0648",  # ؤ → و
    # Yaa variants
    "\u0626": "\u064A",  # ئ → ي
    "\u06CC": "\u064A",  # Farsi yeh → yaa
    "\u0649": "\u064A",  # alef maqsura again
    # Kaf variants
    "\u06A9": "\u0643",  # Farsi kaf → Arabic kaf
    "\u06AA": "\u0643",  # swash kaf
    # Heh variants
    "\u06BE": "\u0647",  # heh doachashmee
    "\u06C1": "\u0647",  # heh goal
    "\u06C3": "\u0629",  # teh marbuta goal → normalize like teh marbuta → haa
    # Waw with hamza above and below
    "\u0676": "\u0648",  # ٶ → و
    "\u0677": "\u0648",  # ٷ → و
}
_ARABIC_NORM_TABLE = str.maketrans(_ARABIC_NORM)

# ---------------------------------------------------------------------------
# 4. Common Latin/numeral → Arabic lookalike substitution
#    Handles cases where users mix in ASCII chars to bypass detection.
# ---------------------------------------------------------------------------
_LATIN_SUB: dict[str, str] = {
    # digits that resemble Arabic letters
    "3": "ع",   # 3 for ع (very common in Arabizi)
    "5": "خ",   # 5 for خ
    "7": "ح",   # 7 for ح
    "8": "ق",   # less common but seen
    "9": "ص",   # 9 for ص
    "2": "ء",   # 2 for glottal stop / hamza
    "6": "ط",   # 6 for ط
    "4": "ة",   # 4 sometimes used for ة (→ normalizes to ه)
    "0": "و",   # 0 for و
    # Latin letters used in Arabizi
    "a": "ا",
    "e": "ي",
    "i": "ي",
    "o": "و",
    "u": "و",
    "k": "ك",
    "t": "ت",
    "d": "د",
    "s": "س",
    "z": "ز",
    "f": "ف",
    "q": "ق",
    "l": "ل",
    "m": "م",
    "n": "ن",
    "h": "ه",
    "b": "ب",
    "j": "ج",
    "r": "ر",
    "w": "و",
    "y": "ي",
    "v": "ف",
    "p": "ب",   # no P in Arabic; map to ب
    "x": "كس",  # sometimes used phonetically
    "c": "ك",
    "g": "ج",
}
_LATIN_SUB_TABLE = str.maketrans(_LATIN_SUB)

# ---------------------------------------------------------------------------
# 5. Punctuation / symbol / non-Arabic-non-alpha stripper
#    Applied AFTER letter substitution — removes separator chars that were
#    injected between letters (e.g. "ك.ل.ب" → "كلب").
# ---------------------------------------------------------------------------
#  Keep Arabic letters, Arabic-Indic digits, and nothing else.
_KEEP_RE = re.compile(r"[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]", re.UNICODE)

# ---------------------------------------------------------------------------
# 6. Collapse repeated characters (3+ in a row → 1)
# ---------------------------------------------------------------------------
_REPEATED_RE = re.compile(r"(.)\1{2,}", re.UNICODE)


def normalize(text: str) -> str:
    """
    Return the canonical normalized form of *text* for profanity matching.
    Both the dictionary words and incoming messages are normalized with this
    function before comparison.
    """
    # Step 1: strip diacritics
    text = _DIACRITICS_RE.sub("", text)

    # Step 2: strip invisible chars
    text = _INVISIBLE_RE.sub("", text)

    # Step 3: normalize Arabic letter variants
    text = text.translate(_ARABIC_NORM_TABLE)

    # Step 4: lowercase (for any Latin chars still present)
    text = text.lower()

    # Step 5: substitute Arabizi digits/Latin → Arabic equivalents
    text = text.translate(_LATIN_SUB_TABLE)

    # Step 6: strip everything that is NOT an Arabic character
    #         (punctuation, spaces, emoji, leftover Latin, etc.)
    text = _KEEP_RE.sub("", text)

    # Step 7: collapse repeated chars (كللللب → كلب)
    text = _REPEATED_RE.sub(r"\1", text)

    return text


def normalize_word(word: str) -> str:
    """Convenience wrapper — identical to normalize() but name conveys single-word intent."""
    return normalize(word)

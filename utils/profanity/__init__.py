"""
Profanity detection package — V4.1.

Public surface
--------------
    from utils.profanity import ProfanityEngine

    engine = ProfanityEngine()          # singleton — import once, reuse forever
    matched = engine.check(text, custom_words=["كلمة1", "كلمة2"])
    # → matched word string | None
"""

from utils.profanity.engine import ProfanityEngine

__all__ = ["ProfanityEngine"]

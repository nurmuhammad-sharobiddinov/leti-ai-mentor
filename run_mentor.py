"""Yangi spec (CLAUDE_CODE_SPEC.md) bo'yicha matematika mentor botini ishga tushiradi.

Loyiha ildizidan:  python run_mentor.py
(Ekvivalent:        python -m leti_math_mentor.bot)
"""
import asyncio

from leti_math_mentor.bot import main

if __name__ == "__main__":
    asyncio.run(main())

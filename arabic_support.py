# -*- coding: utf-8 -*-
"""
Kivy لا يدعم تشكيل الحروف العربية واتجاه الكتابة (RTL) تلقائياً كما تفعل المتصفحات،
لذلك نستخدم مكتبتي arabic_reshaper و python-bidi لتحويل أي نص عربي إلى الشكل الصحيح
قبل عرضه في أي Label أو Button.

الاستخدام: بدلاً من Label(text="مرحبا") اكتب Label(text=ar("مرحبا"))
"""
import arabic_reshaper
from bidi.algorithm import get_display

FONT_PATH = "assets/fonts/NotoNaskhArabic-Regular.ttf"


def ar(text):
    """يحوّل نصاً عربياً (أو مختلطاً) إلى شكل قابل للعرض الصحيح في Kivy"""
    if text is None:
        return ""
    text = str(text)
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text

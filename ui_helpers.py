# -*- coding: utf-8 -*-
"""أدوات مساعدة مشتركة بين شاشات التطبيق"""
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import OneLineListItem, TwoLineListItem, ThreeLineListItem
from arabic_support import ar
import database as db


def format_money(amount, symbol=""):
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        amount = 0.0
    txt = f"{amount:,.2f}"
    return f"{txt} {symbol}".strip()


def get_base_currency():
    conn = db.get_connection()
    row = conn.execute("SELECT * FROM currencies WHERE is_base=1 LIMIT 1").fetchone()
    conn.close()
    return row


def show_snackbar(text):
    from kivymd.uix.snackbar import Snackbar
    Snackbar(text=ar(text), duration=2.2).open()


def confirm_dialog(text, on_confirm):
    """صندوق حوار لتأكيد عملية حذف أو إجراء حرج"""
    dialog = None

    def _confirm(*a):
        dialog.dismiss()
        on_confirm()

    def _cancel(*a):
        dialog.dismiss()

    dialog = MDDialog(
        title=ar("تأكيد"),
        text=ar(text),
        buttons=[
            MDFlatButton(text=ar("إلغاء"), on_release=_cancel),
            MDRaisedButton(text=ar("تأكيد"), on_release=_confirm),
        ],
    )
    dialog.open()


def form_dialog(title, field_specs, on_submit, initial=None, on_delete=None):
    """
    نافذة نموذج عامة لإدخال/تعديل بيانات.
    field_specs: قائمة من (key, label_ar)
    on_submit: دالة تستقبل dict {key: value}
    on_delete: دالة اختيارية بدون معطيات؛ إن وُجدت يظهر زر "حذف" في النافذة (للتعديل)
    """
    initial = initial or {}
    content = MDBoxLayout(orientation="vertical", spacing="10dp", size_hint_y=None,
                          padding=("10dp", "10dp", "10dp", "10dp"))
    content.bind(minimum_height=content.setter("height"))

    text_fields = {}
    for key, label in field_specs:
        tf = MDTextField(
            text=str(initial.get(key, "")),
            hint_text=ar(label),
            halign="right",
        )
        content.add_widget(tf)
        text_fields[key] = tf

    dialog = None

    def _submit(*a):
        values = {k: tf.text for k, tf in text_fields.items()}
        ok = on_submit(values)
        if ok is not False:
            dialog.dismiss()

    def _cancel(*a):
        dialog.dismiss()

    def _delete(*a):
        dialog.dismiss()
        confirm_dialog("هل أنت متأكد من الحذف؟ لا يمكن التراجع.", on_delete)

    buttons = [MDFlatButton(text=ar("إلغاء"), on_release=_cancel)]
    if on_delete:
        buttons.append(MDFlatButton(text=ar("حذف"), theme_text_color="Custom",
                                     text_color=(0.86, 0.15, 0.15, 1), on_release=_delete))
    buttons.append(MDRaisedButton(text=ar("حفظ"), on_release=_submit))

    dialog = MDDialog(
        title=ar(title),
        type="custom",
        content_cls=content,
        buttons=buttons,
    )
    dialog.open()


def make_list_item(primary, secondary=None, tertiary=None, on_release=None):
    """يبني عنصر قائمة (سطر واحد أو أكثر) بنص عربي منسق بشكل صحيح"""
    if tertiary is not None:
        item = ThreeLineListItem(text=ar(primary), secondary_text=ar(secondary or ""),
                                  tertiary_text=ar(tertiary))
    elif secondary is not None:
        item = TwoLineListItem(text=ar(primary), secondary_text=ar(secondary))
    else:
        item = OneLineListItem(text=ar(primary))
    if on_release:
        item.bind(on_release=on_release)
    return item

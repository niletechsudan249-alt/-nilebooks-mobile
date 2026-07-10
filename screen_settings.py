# -*- coding: utf-8 -*-
"""الإعدادات: اسم الشركة وإدارة العملات - نسخة الموبايل"""
from kivy.uix.screenmanager import Screen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFloatingActionButton
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList
from kivymd.uix.floatlayout import FloatLayout

import database as db
from arabic_support import ar
from ui_helpers import make_list_item, form_dialog, show_snackbar


class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "settings"

        root = FloatLayout()
        self.scroll = MDScrollView()
        self.root_box = MDBoxLayout(orientation="vertical", spacing="14dp", padding="14dp",
                                     size_hint_y=None)
        self.root_box.bind(minimum_height=self.root_box.setter("height"))
        self.scroll.add_widget(self.root_box)
        root.add_widget(self.scroll)

        fab = MDFloatingActionButton(icon="plus", pos_hint={"left": 0.03, "bottom": 0.03},
                                      md_bg_color=(0.14, 0.39, 0.92, 1))
        fab.bind(on_release=lambda *a: self.add_currency())
        root.add_widget(fab)
        self.add_widget(root)

    def on_pre_enter(self, *a):
        self.build_ui()

    def build_ui(self):
        self.root_box.clear_widgets()
        self.root_box.add_widget(MDLabel(text=ar("الإعدادات"), font_style="H5", halign="right",
                                          size_hint_y=None, height="40dp"))

        self.company_field = MDTextField(hint_text=ar("اسم الشركة"),
                                          text=db.get_setting("company_name", ""), halign="right")
        self.root_box.add_widget(self.company_field)

        save_btn = MDRaisedButton(text=ar("حفظ بيانات الشركة"), size_hint_x=1,
                                  md_bg_color=(0.14, 0.39, 0.92, 1))
        save_btn.bind(on_release=lambda *a: self.save_company())
        self.root_box.add_widget(save_btn)

        self.root_box.add_widget(MDLabel(text=ar("العملات وأسعار الصرف"), bold=True, halign="right",
                                          size_hint_y=None, height="30dp"))

        self.currency_list = MDList()
        self.root_box.add_widget(self.currency_list)
        self.refresh_currencies()

    def refresh_currencies(self):
        self.currency_list.clear_widgets()
        conn = db.get_connection()
        rows = conn.execute("SELECT * FROM currencies ORDER BY is_base DESC, code").fetchall()
        conn.close()
        for r in rows:
            base_tag = " (أساسية)" if r["is_base"] else ""
            secondary = f'سعر التحويل: {r["rate_to_base"]}'
            item = make_list_item(f'{r["code"]} - {r["name"]}{base_tag}', secondary,
                                   on_release=lambda inst, cid=r["id"]: self.edit_currency(cid))
            self.currency_list.add_widget(item)

    def save_company(self):
        db.set_setting("company_name", self.company_field.text.strip())
        show_snackbar("تم حفظ بيانات الشركة")

    def add_currency(self):
        fields = [("code", "رمز العملة (مثل USD)"), ("name", "اسم العملة"),
                  ("symbol", "علامة العملة"), ("rate_to_base", "سعر التحويل للعملة الأساسية")]

        def submit(values):
            if not values["code"].strip() or not values["name"].strip():
                show_snackbar("الرمز والاسم مطلوبان")
                return False
            try:
                rate = float(values["rate_to_base"] or 1)
            except ValueError:
                show_snackbar("سعر التحويل يجب أن يكون رقماً")
                return False
            conn = db.get_connection()
            try:
                conn.execute(
                    "INSERT INTO currencies (code, name, symbol, rate_to_base, is_base) VALUES (?,?,?,?,0)",
                    (values["code"].strip().upper(), values["name"].strip(),
                     values["symbol"].strip(), rate))
                conn.commit()
            except Exception as e:
                show_snackbar(f"تعذر إضافة العملة: {e}")
                conn.close()
                return False
            conn.close()
            self.refresh_currencies()
            return True

        form_dialog("إضافة عملة", fields, submit)

    def edit_currency(self, cid):
        conn = db.get_connection()
        c = conn.execute("SELECT * FROM currencies WHERE id=?", (cid,)).fetchone()
        conn.close()
        if not c:
            return
        fields = [("code", "رمز العملة"), ("name", "اسم العملة"),
                  ("symbol", "علامة العملة"), ("rate_to_base", "سعر التحويل للعملة الأساسية")]

        def submit(values):
            try:
                rate = float(values["rate_to_base"] or 1)
            except ValueError:
                show_snackbar("سعر التحويل يجب أن يكون رقماً")
                return False
            conn = db.get_connection()
            conn.execute("UPDATE currencies SET code=?, name=?, symbol=?, rate_to_base=? WHERE id=?",
                         (values["code"].strip().upper(), values["name"].strip(),
                          values["symbol"].strip(), rate, cid))
            conn.commit()
            conn.close()
            self.refresh_currencies()
            return True

        def do_delete():
            conn = db.get_connection()
            row = conn.execute("SELECT is_base FROM currencies WHERE id=?", (cid,)).fetchone()
            if row and row["is_base"]:
                show_snackbar("لا يمكن حذف العملة الأساسية")
                conn.close()
                return
            conn.execute("DELETE FROM currencies WHERE id=?", (cid,))
            conn.commit()
            conn.close()
            self.refresh_currencies()
            show_snackbar("تم الحذف")

        form_dialog("تعديل العملة", fields, submit, initial=dict(c), on_delete=do_delete)

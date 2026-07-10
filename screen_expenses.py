# -*- coding: utf-8 -*-
"""تسجيل المصاريف والإيرادات الأخرى - نسخة الموبايل"""
from kivy.uix.screenmanager import Screen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import MDList
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.button import MDFloatingActionButton
from kivymd.uix.floatlayout import FloatLayout

import database as db
from arabic_support import ar
from ui_helpers import make_list_item, format_money, form_dialog, show_snackbar


class ExpensesIncomeScreen(Screen):
    def __init__(self, kind="expense", **kwargs):
        super().__init__(**kwargs)
        self.kind = kind
        self.table_name = "expenses" if kind == "expense" else "incomes"
        self.name = "expenses" if kind == "expense" else "incomes"

        root = FloatLayout()
        main_box = MDBoxLayout(orientation="vertical")
        self.scroll = MDScrollView()
        self.list_widget = MDList()
        self.scroll.add_widget(self.list_widget)
        main_box.add_widget(self.scroll)
        root.add_widget(main_box)

        fab = MDFloatingActionButton(icon="plus", pos_hint={"left": 0.03, "bottom": 0.03},
                                      md_bg_color=(0.14, 0.39, 0.92, 1))
        fab.bind(on_release=lambda *a: self.add_entry())
        root.add_widget(fab)
        self.add_widget(root)

    def on_pre_enter(self, *a):
        self.refresh()

    def refresh(self):
        self.list_widget.clear_widgets()
        conn = db.get_connection()
        rows = conn.execute(f"SELECT * FROM {self.table_name} ORDER BY date DESC, id DESC").fetchall()
        conn.close()
        for r in rows:
            secondary = f'{r["date"]}   |   {r["category"] or "-"}'
            item = make_list_item(f'{r["description"] or "بدون وصف"} - {format_money(r["amount"])}',
                                   secondary,
                                   on_release=lambda inst, eid=r["id"]: self.edit_entry(eid))
            self.list_widget.add_widget(item)

    def add_entry(self):
        fields = [("date", "التاريخ (سنة-شهر-يوم)"), ("category", "التصنيف"),
                  ("description", "الوصف"), ("amount", "المبلغ")]
        initial = {"date": db.now_date()}

        def submit(values):
            try:
                amount = float(values["amount"] or 0)
            except ValueError:
                show_snackbar("المبلغ يجب أن يكون رقماً")
                return False
            if amount <= 0:
                show_snackbar("المبلغ يجب أن يكون أكبر من صفر")
                return False
            conn = db.get_connection()
            conn.execute(
                f"INSERT INTO {self.table_name} (date, category, description, amount) VALUES (?,?,?,?)",
                (values["date"].strip() or db.now_date(), values["category"].strip(),
                 values["description"].strip(), amount))
            conn.commit()
            conn.close()
            self.refresh()
            show_snackbar("تمت الإضافة")
            return True

        title = "إضافة مصروف" if self.kind == "expense" else "إضافة إيراد"
        form_dialog(title, fields, submit, initial=initial)

    def edit_entry(self, eid):
        conn = db.get_connection()
        row = conn.execute(f"SELECT * FROM {self.table_name} WHERE id=?", (eid,)).fetchone()
        conn.close()
        if not row:
            return
        fields = [("date", "التاريخ"), ("category", "التصنيف"),
                  ("description", "الوصف"), ("amount", "المبلغ")]

        def submit(values):
            try:
                amount = float(values["amount"] or 0)
            except ValueError:
                show_snackbar("المبلغ يجب أن يكون رقماً")
                return False
            conn = db.get_connection()
            conn.execute(
                f"UPDATE {self.table_name} SET date=?, category=?, description=?, amount=? WHERE id=?",
                (values["date"].strip(), values["category"].strip(),
                 values["description"].strip(), amount, eid))
            conn.commit()
            conn.close()
            self.refresh()
            show_snackbar("تم التحديث")
            return True

        def do_delete():
            conn = db.get_connection()
            conn.execute(f"DELETE FROM {self.table_name} WHERE id=?", (eid,))
            conn.commit()
            conn.close()
            self.refresh()
            show_snackbar("تم الحذف")

        title = "تعديل مصروف" if self.kind == "expense" else "تعديل إيراد"
        form_dialog(title, fields, submit, initial=dict(row), on_delete=do_delete)

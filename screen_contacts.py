# -*- coding: utf-8 -*-
"""إدارة العملاء والموردين - نفس المكوّن يخدم الاثنين"""
from kivy.uix.screenmanager import Screen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import MDList
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.button import MDFloatingActionButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.floatlayout import FloatLayout

import database as db
from arabic_support import ar
from ui_helpers import make_list_item, format_money, form_dialog, show_snackbar


class ContactsScreen(Screen):
    def __init__(self, entity_type="customers", **kwargs):
        super().__init__(**kwargs)
        self.entity_type = entity_type
        self.table_name = "customers" if entity_type == "customers" else "suppliers"
        self.name = entity_type  # 'customers' or 'suppliers'

        root = FloatLayout()
        main_box = MDBoxLayout(orientation="vertical")

        search_box = MDBoxLayout(size_hint_y=None, height="50dp", padding="8dp")
        self.search_field = MDTextField(
            hint_text=ar("بحث..."), halign="right")
        self.search_field.bind(text=lambda *a: self.refresh())
        search_box.add_widget(self.search_field)
        main_box.add_widget(search_box)

        self.scroll = MDScrollView()
        self.list_widget = MDList()
        self.scroll.add_widget(self.list_widget)
        main_box.add_widget(self.scroll)
        root.add_widget(main_box)

        fab = MDFloatingActionButton(icon="plus", pos_hint={"left": 0.03, "bottom": 0.03},
                                      md_bg_color=(0.14, 0.39, 0.92, 1))
        fab.bind(on_release=lambda *a: self.add_contact())
        root.add_widget(fab)

        self.add_widget(root)

    def on_pre_enter(self, *a):
        self.refresh()

    def refresh(self):
        self.list_widget.clear_widgets()
        conn = db.get_connection()
        search = f"%{self.search_field.text.strip()}%"
        rows = conn.execute(
            f"SELECT * FROM {self.table_name} WHERE name LIKE ? ORDER BY name", (search,)
        ).fetchall()
        conn.close()
        for r in rows:
            secondary = f'{r["phone"] or "-"}   |   الرصيد: {format_money(r["balance"])}'
            item = make_list_item(r["name"], secondary,
                                   on_release=lambda inst, cid=r["id"]: self.edit_contact(cid))
            self.list_widget.add_widget(item)

    def get_all(self):
        conn = db.get_connection()
        rows = conn.execute(f"SELECT id, name FROM {self.table_name} ORDER BY name").fetchall()
        conn.close()
        return rows

    def add_contact(self):
        fields = [("name", "الاسم"), ("phone", "الهاتف"), ("address", "العنوان"),
                  ("balance", "الرصيد الافتتاحي"), ("notes", "ملاحظات")]

        def submit(values):
            if not values["name"].strip():
                show_snackbar("الاسم مطلوب")
                return False
            try:
                balance = float(values["balance"] or 0)
            except ValueError:
                show_snackbar("الرصيد يجب أن يكون رقماً")
                return False
            conn = db.get_connection()
            conn.execute(
                f"INSERT INTO {self.table_name} (name, phone, address, balance, notes) VALUES (?,?,?,?,?)",
                (values["name"].strip(), values["phone"].strip(), values["address"].strip(),
                 balance, values["notes"].strip()))
            conn.commit()
            conn.close()
            self.refresh()
            show_snackbar("تم الإضافة")
            return True

        title = "إضافة عميل" if self.entity_type == "customers" else "إضافة مورد"
        form_dialog(title, fields, submit)

    def edit_contact(self, cid):
        conn = db.get_connection()
        c = conn.execute(f"SELECT * FROM {self.table_name} WHERE id=?", (cid,)).fetchone()
        conn.close()
        if not c:
            return
        fields = [("name", "الاسم"), ("phone", "الهاتف"), ("address", "العنوان"),
                  ("balance", "الرصيد"), ("notes", "ملاحظات")]

        def submit(values):
            try:
                balance = float(values["balance"] or 0)
            except ValueError:
                show_snackbar("الرصيد يجب أن يكون رقماً")
                return False
            conn = db.get_connection()
            conn.execute(
                f"UPDATE {self.table_name} SET name=?, phone=?, address=?, balance=?, notes=? WHERE id=?",
                (values["name"].strip(), values["phone"].strip(), values["address"].strip(),
                 balance, values["notes"].strip(), cid))
            conn.commit()
            conn.close()
            self.refresh()
            show_snackbar("تم التحديث")
            return True

        def do_delete():
            conn = db.get_connection()
            conn.execute(f"DELETE FROM {self.table_name} WHERE id=?", (cid,))
            conn.commit()
            conn.close()
            self.refresh()
            show_snackbar("تم الحذف")

        title = "تعديل عميل" if self.entity_type == "customers" else "تعديل مورد"
        form_dialog(title, fields, submit, initial=dict(c), on_delete=do_delete)

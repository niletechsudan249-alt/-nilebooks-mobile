# -*- coding: utf-8 -*-
"""إدارة المنتجات والمخزون - نسخة الموبايل"""
from kivy.uix.screenmanager import Screen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import MDList
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.button import MDFloatingActionButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.floatlayout import FloatLayout

import database as db
from arabic_support import ar
from ui_helpers import make_list_item, format_money, form_dialog, confirm_dialog, show_snackbar


class ProductsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "products"
        self.selected_id = None

        root = FloatLayout()

        main_box = MDBoxLayout(orientation="vertical")

        search_box = MDBoxLayout(size_hint_y=None, height="50dp", padding="8dp")
        self.search_field = MDTextField(hint_text=ar("بحث عن منتج..."), halign="right")
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
        fab.bind(on_release=lambda *a: self.add_product())
        root.add_widget(fab)

        self.add_widget(root)

    def on_pre_enter(self, *a):
        self.refresh()

    def refresh(self):
        self.list_widget.clear_widgets()
        conn = db.get_connection()
        search = f"%{self.search_field.text.strip()}%"
        rows = conn.execute(
            "SELECT * FROM products WHERE is_active=1 AND name LIKE ? ORDER BY name", (search,)
        ).fetchall()
        conn.close()

        for r in rows:
            low = r["quantity"] <= r["min_quantity"]
            secondary = f'الكمية: {r["quantity"]}   |   سعر البيع: {format_money(r["sale_price"])}'
            if low:
                secondary = "⚠ " + secondary
            item = make_list_item(r["name"], secondary,
                                   on_release=lambda inst, pid=r["id"]: self.open_product_menu(pid))
            self.list_widget.add_widget(item)

    def open_product_menu(self, product_id):
        self.selected_id = product_id
        conn = db.get_connection()
        p = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
        conn.close()
        if not p:
            return
        self._edit_product(dict(p))

    def add_product(self):
        fields = [
            ("name", "اسم المنتج"), ("sku", "الكود (اختياري)"), ("unit", "الوحدة"),
            ("purchase_price", "سعر الشراء"), ("sale_price", "سعر البيع"),
            ("quantity", "الكمية الحالية"), ("min_quantity", "الحد الأدنى للتنبيه"),
        ]

        def submit(values):
            if not values["name"].strip():
                show_snackbar("اسم المنتج مطلوب")
                return False
            try:
                purchase_price = float(values["purchase_price"] or 0)
                sale_price = float(values["sale_price"] or 0)
                quantity = float(values["quantity"] or 0)
                min_quantity = float(values["min_quantity"] or 0)
            except ValueError:
                show_snackbar("الرجاء إدخال أرقام صحيحة")
                return False
            conn = db.get_connection()
            conn.execute(
                "INSERT INTO products (name, sku, unit, purchase_price, sale_price, quantity, min_quantity) "
                "VALUES (?,?,?,?,?,?,?)",
                (values["name"].strip(), values["sku"].strip(), values["unit"].strip() or "قطعة",
                 purchase_price, sale_price, quantity, min_quantity))
            conn.commit()
            conn.close()
            self.refresh()
            show_snackbar("تم إضافة المنتج")
            return True

        form_dialog("إضافة منتج", fields, submit)

    def _edit_product(self, initial):
        fields = [
            ("name", "اسم المنتج"), ("sku", "الكود (اختياري)"), ("unit", "الوحدة"),
            ("purchase_price", "سعر الشراء"), ("sale_price", "سعر البيع"),
            ("quantity", "الكمية الحالية"), ("min_quantity", "الحد الأدنى للتنبيه"),
        ]
        pid = initial["id"]

        def submit(values):
            try:
                purchase_price = float(values["purchase_price"] or 0)
                sale_price = float(values["sale_price"] or 0)
                quantity = float(values["quantity"] or 0)
                min_quantity = float(values["min_quantity"] or 0)
            except ValueError:
                show_snackbar("الرجاء إدخال أرقام صحيحة")
                return False
            conn = db.get_connection()
            conn.execute(
                "UPDATE products SET name=?, sku=?, unit=?, purchase_price=?, sale_price=?, "
                "quantity=?, min_quantity=? WHERE id=?",
                (values["name"].strip(), values["sku"].strip(), values["unit"].strip() or "قطعة",
                 purchase_price, sale_price, quantity, min_quantity, pid))
            conn.commit()
            conn.close()
            self.refresh()
            show_snackbar("تم تحديث المنتج")
            return True

        def do_delete():
            conn = db.get_connection()
            conn.execute("UPDATE products SET is_active=0 WHERE id=?", (pid,))
            conn.commit()
            conn.close()
            self.refresh()
            show_snackbar("تم حذف المنتج")

        form_dialog("تعديل المنتج", fields, submit, initial=initial, on_delete=do_delete)

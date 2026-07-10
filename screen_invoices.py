# -*- coding: utf-8 -*-
"""
فواتير المبيعات والمشتريات - نسخة الموبايل
كل نوع (sale/purchase) له شاشة قائمة + شاشة محرر مشتركة الكود
"""
from kivy.uix.screenmanager import Screen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import MDList
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.button import MDFloatingActionButton, MDRaisedButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.floatlayout import FloatLayout
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.toolbar import MDTopAppBar

import database as db
from arabic_support import ar
from ui_helpers import make_list_item, format_money, show_snackbar, confirm_dialog


class InvoiceListScreen(Screen):
    def __init__(self, kind="sale", manager_app=None, **kwargs):
        super().__init__(**kwargs)
        self.kind = kind
        self.app_ref = manager_app
        self.name = "sales" if kind == "sale" else "purchases"
        self.invoice_table = "sales_invoices" if kind == "sale" else "purchase_invoices"
        self.contact_table = "customers" if kind == "sale" else "suppliers"
        self.contact_field = "customer_id" if kind == "sale" else "supplier_id"

        root = FloatLayout()
        main_box = MDBoxLayout(orientation="vertical")

        self.scroll = MDScrollView()
        self.list_widget = MDList()
        self.scroll.add_widget(self.list_widget)
        main_box.add_widget(self.scroll)
        root.add_widget(main_box)

        fab = MDFloatingActionButton(icon="plus", pos_hint={"left": 0.03, "bottom": 0.03},
                                      md_bg_color=(0.14, 0.39, 0.92, 1))
        fab.bind(on_release=lambda *a: self.open_new_invoice())
        root.add_widget(fab)
        self.add_widget(root)

    def on_pre_enter(self, *a):
        self.refresh()

    def refresh(self):
        self.list_widget.clear_widgets()
        conn = db.get_connection()
        rows = conn.execute(f"""
            SELECT inv.*, c.name as contact_name FROM {self.invoice_table} inv
            LEFT JOIN {self.contact_table} c ON inv.{self.contact_field} = c.id
            ORDER BY inv.date DESC, inv.id DESC
        """).fetchall()
        conn.close()
        for r in rows:
            remaining = r["total"] - r["paid"]
            secondary = f'{r["contact_name"] or "-"}   |   {r["date"]}'
            tertiary = f'الإجمالي: {format_money(r["total"])}   المتبقي: {format_money(remaining)}'
            item = make_list_item(r["invoice_number"], secondary, tertiary,
                                   on_release=lambda inst, iid=r["id"]: self.open_invoice(iid))
            self.list_widget.add_widget(item)

    def open_new_invoice(self):
        editor = self.app_ref.get_invoice_editor(self.kind)
        editor.load_invoice(None)
        self.app_ref.sm.current = editor.name

    def open_invoice(self, invoice_id):
        editor = self.app_ref.get_invoice_editor(self.kind)
        editor.load_invoice(invoice_id)
        self.app_ref.sm.current = editor.name


class InvoiceEditorScreen(Screen):
    def __init__(self, kind="sale", manager_app=None, **kwargs):
        super().__init__(**kwargs)
        self.kind = kind
        self.app_ref = manager_app
        self.name = "sale_editor" if kind == "sale" else "purchase_editor"
        self.invoice_table = "sales_invoices" if kind == "sale" else "purchase_invoices"
        self.items_table = "sales_invoice_items" if kind == "sale" else "purchase_invoice_items"
        self.contact_table = "customers" if kind == "sale" else "suppliers"
        self.contact_field = "customer_id" if kind == "sale" else "supplier_id"
        self.contact_label = "العميل" if kind == "sale" else "المورد"

        self.invoice_id = None
        self.items = []
        self.selected_contact_id = None
        self.selected_product = None

        root = MDBoxLayout(orientation="vertical")

        title = "فاتورة بيع" if kind == "sale" else "فاتورة شراء"
        toolbar = MDTopAppBar(title=ar(title), left_action_items=[
            ["arrow-right", lambda x: self.go_back()]])
        root.add_widget(toolbar)

        body_scroll = MDScrollView()
        body = MDBoxLayout(orientation="vertical", spacing="10dp", padding="14dp",
                           size_hint_y=None)
        body.bind(minimum_height=body.setter("height"))
        body_scroll.add_widget(body)
        root.add_widget(body_scroll)

        self.invoice_number_field = MDTextField(hint_text=ar("رقم الفاتورة"), halign="right")
        body.add_widget(self.invoice_number_field)

        self.date_field = MDTextField(hint_text=ar("التاريخ (سنة-شهر-يوم)"), halign="right")
        body.add_widget(self.date_field)

        self.contact_button = MDRaisedButton(text=ar(f"اختر {self.contact_label}"), size_hint_x=1)
        self.contact_button.bind(on_release=self.open_contact_menu)
        body.add_widget(self.contact_button)
        self.contact_menu = None

        body.add_widget(MDLabel(text=ar("إضافة صنف"), halign="right", bold=True,
                                size_hint_y=None, height="30dp"))

        self.product_button = MDRaisedButton(text=ar("اختر منتج"), size_hint_x=1)
        self.product_button.bind(on_release=self.open_product_menu)
        body.add_widget(self.product_button)
        self.product_menu = None

        qty_price_box = MDBoxLayout(size_hint_y=None, height="50dp", spacing="8dp")
        self.qty_field = MDTextField(hint_text=ar("الكمية"), halign="right", text="1")
        self.price_field = MDTextField(hint_text=ar("السعر"), halign="right", text="0")
        qty_price_box.add_widget(self.price_field)
        qty_price_box.add_widget(self.qty_field)
        body.add_widget(qty_price_box)

        add_item_btn = MDRaisedButton(text=ar("+ إضافة للفاتورة"), size_hint_x=1)
        add_item_btn.bind(on_release=lambda *a: self.add_item())
        body.add_widget(add_item_btn)

        body.add_widget(MDLabel(text=ar("عناصر الفاتورة"), halign="right", bold=True,
                                size_hint_y=None, height="30dp"))

        self.items_box = MDBoxLayout(orientation="vertical", size_hint_y=None, spacing="4dp")
        self.items_box.bind(minimum_height=self.items_box.setter("height"))
        body.add_widget(self.items_box)

        self.total_label = MDLabel(text=ar("الإجمالي: 0.00"), halign="right", font_style="H6",
                                   size_hint_y=None, height="36dp")
        body.add_widget(self.total_label)

        self.paid_field = MDTextField(hint_text=ar("المبلغ المدفوع"), halign="right", text="0")
        body.add_widget(self.paid_field)

        save_btn = MDRaisedButton(text=ar("حفظ الفاتورة"), size_hint_x=1,
                                  md_bg_color=(0.14, 0.39, 0.92, 1))
        save_btn.bind(on_release=lambda *a: self.save_invoice())
        body.add_widget(save_btn)

        self.add_widget(root)

    def go_back(self):
        self.app_ref.sm.current = self.name.replace("_editor", "s") if self.kind == "sale" \
            else "purchases"

    def load_invoice(self, invoice_id):
        self.invoice_id = invoice_id
        self.items = []
        self.selected_contact_id = None
        self.selected_product = None
        self.items_box.clear_widgets()
        self.qty_field.text = "1"
        self.price_field.text = "0"
        self.paid_field.text = "0"
        self.contact_button.text = ar(f"اختر {self.contact_label}")
        self.product_button.text = ar("اختر منتج")

        if invoice_id:
            conn = db.get_connection()
            inv = conn.execute(f"SELECT * FROM {self.invoice_table} WHERE id=?", (invoice_id,)).fetchone()
            items = conn.execute(f"SELECT * FROM {self.items_table} WHERE invoice_id=?",
                                  (invoice_id,)).fetchall()
            contact = None
            cid = inv[self.contact_field]
            if cid:
                contact = conn.execute(f"SELECT name FROM {self.contact_table} WHERE id=?", (cid,)).fetchone()
            conn.close()
            self.invoice_number_field.text = inv["invoice_number"]
            self.date_field.text = inv["date"]
            self.paid_field.text = str(inv["paid"])
            if contact:
                self.selected_contact_id = cid
                self.contact_button.text = ar(contact["name"])
            for it in items:
                self.items.append(dict(it))
        else:
            conn = db.get_connection()
            prefix = "S" if self.kind == "sale" else "P"
            count = conn.execute(f"SELECT COUNT(*) c FROM {self.invoice_table}").fetchone()["c"]
            conn.close()
            self.invoice_number_field.text = f"{prefix}-{count + 1:05d}"
            self.date_field.text = db.now_date()

        self._render_items()

    def open_contact_menu(self, button):
        conn = db.get_connection()
        rows = conn.execute(f"SELECT id, name FROM {self.contact_table} ORDER BY name").fetchall()
        conn.close()
        items = [{"text": ar(r["name"]),
                  "on_release": lambda x=r: self._select_contact(x)} for r in rows]
        if not items:
            show_snackbar(f"لا يوجد {self.contact_label} مسجل بعد، أضِفه أولاً من الشاشة المخصصة")
            return
        self.contact_menu = MDDropdownMenu(caller=button, items=items, width_mult=4)
        self.contact_menu.open()

    def _select_contact(self, row):
        self.selected_contact_id = row["id"]
        self.contact_button.text = ar(row["name"])
        if self.contact_menu:
            self.contact_menu.dismiss()

    def open_product_menu(self, button):
        conn = db.get_connection()
        rows = conn.execute("SELECT * FROM products WHERE is_active=1 ORDER BY name").fetchall()
        conn.close()
        items = [{"text": ar(r["name"]),
                  "on_release": lambda x=r: self._select_product(x)} for r in rows]
        if not items:
            show_snackbar("لا توجد منتجات مسجلة بعد")
            return
        self.product_menu = MDDropdownMenu(caller=button, items=items, width_mult=4)
        self.product_menu.open()

    def _select_product(self, row):
        self.selected_product = dict(row)
        self.product_button.text = ar(row["name"])
        price = row["sale_price"] if self.kind == "sale" else row["purchase_price"]
        self.price_field.text = str(price)
        if self.product_menu:
            self.product_menu.dismiss()

    def add_item(self):
        if not self.selected_product:
            show_snackbar("يرجى اختيار منتج أولاً")
            return
        try:
            qty = float(self.qty_field.text)
            price = float(self.price_field.text)
        except ValueError:
            show_snackbar("الكمية والسعر يجب أن يكونا أرقاماً")
            return
        if qty <= 0:
            show_snackbar("الكمية يجب أن تكون أكبر من صفر")
            return
        if self.kind == "sale" and qty > self.selected_product["quantity"]:
            show_snackbar(f'الكمية المتاحة {self.selected_product["quantity"]} فقط')
            return

        self.items.append({
            "product_id": self.selected_product["id"],
            "product_name": self.selected_product["name"],
            "quantity": qty, "unit_price": price, "total": qty * price,
        })
        self._render_items()

    def _render_items(self):
        self.items_box.clear_widgets()
        for idx, it in enumerate(self.items):
            row = MDBoxLayout(size_hint_y=None, height="40dp")
            lbl = MDLabel(text=ar(f'{it["product_name"]}  x{it["quantity"]}  =  {format_money(it["total"])}'),
                         halign="right")
            row.add_widget(lbl)
            del_btn = MDIconButton(icon="close", theme_text_color="Custom",
                                   text_color=(0.86, 0.15, 0.15, 1))
            del_btn.bind(on_release=lambda inst, i=idx: self._remove_item(i))
            row.add_widget(del_btn)
            self.items_box.add_widget(row)
        total = sum(it["total"] for it in self.items)
        self.total_label.text = ar(f"الإجمالي: {format_money(total)}")

    def _remove_item(self, idx):
        self.items.pop(idx)
        self._render_items()

    def save_invoice(self):
        if not self.items:
            show_snackbar("أضف صنفاً واحداً على الأقل")
            return
        if not self.invoice_number_field.text.strip():
            show_snackbar("رقم الفاتورة مطلوب")
            return
        try:
            paid = float(self.paid_field.text or 0)
        except ValueError:
            show_snackbar("المبلغ المدفوع يجب أن يكون رقماً")
            return

        total = sum(it["total"] for it in self.items)
        conn = db.get_connection()

        if self.invoice_id:
            # حذف الفاتورة القديمة وإرجاع الكميات، ثم إعادة الإنشاء (أبسط وأكثر أماناً)
            old_items = conn.execute(f"SELECT * FROM {self.items_table} WHERE invoice_id=?",
                                      (self.invoice_id,)).fetchall()
            for it in old_items:
                if it["product_id"]:
                    delta = it["quantity"] if self.kind == "sale" else -it["quantity"]
                    conn.execute("UPDATE products SET quantity = quantity + ? WHERE id=?",
                                 (delta, it["product_id"]))
            conn.execute(f"DELETE FROM {self.items_table} WHERE invoice_id=?", (self.invoice_id,))
            conn.execute(f"DELETE FROM {self.invoice_table} WHERE id=?", (self.invoice_id,))

        cur = conn.execute(
            f"INSERT INTO {self.invoice_table} (invoice_number, {self.contact_field}, date, total, paid) "
            "VALUES (?,?,?,?,?)",
            (self.invoice_number_field.text.strip(), self.selected_contact_id,
             self.date_field.text.strip() or db.now_date(), total, paid))
        new_invoice_id = cur.lastrowid

        for it in self.items:
            conn.execute(
                f"INSERT INTO {self.items_table} (invoice_id, product_id, product_name, quantity, unit_price, total) "
                "VALUES (?,?,?,?,?,?)",
                (new_invoice_id, it["product_id"], it["product_name"], it["quantity"],
                 it["unit_price"], it["total"]))
            if it["product_id"]:
                delta = -it["quantity"] if self.kind == "sale" else it["quantity"]
                conn.execute("UPDATE products SET quantity = quantity + ? WHERE id=?",
                             (delta, it["product_id"]))

        remaining = total - paid
        if self.selected_contact_id and remaining != 0:
            sign = 1 if self.kind == "sale" else -1
            conn.execute(f"UPDATE {self.contact_table} SET balance = balance + ? WHERE id=?",
                         (remaining * sign, self.selected_contact_id))

        conn.commit()
        conn.close()
        show_snackbar("تم حفظ الفاتورة")
        self.go_back()

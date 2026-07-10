# -*- coding: utf-8 -*-
"""تقارير مالية مبسطة - نسخة الموبايل (فلترة بتاريخ + ملخص أرقام)"""
from kivy.uix.screenmanager import Screen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextField

import database as db
from arabic_support import ar
from ui_helpers import format_money


class ReportsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "reports"

        self.scroll = MDScrollView()
        self.root_box = MDBoxLayout(orientation="vertical", spacing="12dp", padding="14dp",
                                     size_hint_y=None)
        self.root_box.bind(minimum_height=self.root_box.setter("height"))
        self.scroll.add_widget(self.root_box)
        self.add_widget(self.scroll)

    def on_pre_enter(self, *a):
        self.build_ui()

    def build_ui(self):
        self.root_box.clear_widgets()
        self.root_box.add_widget(MDLabel(text=ar("التقارير المالية"), font_style="H5",
                                          halign="right", size_hint_y=None, height="40dp"))

        today = db.now_date()
        first_of_month = today[:8] + "01"

        filter_box = MDBoxLayout(size_hint_y=None, height="50dp", spacing="8dp")
        self.from_field = MDTextField(hint_text=ar("من"), text=first_of_month, halign="right")
        self.to_field = MDTextField(hint_text=ar("إلى"), text=today, halign="right")
        filter_box.add_widget(self.to_field)
        filter_box.add_widget(self.from_field)
        self.root_box.add_widget(filter_box)

        run_btn = MDRaisedButton(text=ar("عرض التقرير"), size_hint_x=1,
                                 md_bg_color=(0.14, 0.39, 0.92, 1))
        run_btn.bind(on_release=lambda *a: self.run_report())
        self.root_box.add_widget(run_btn)

        self.results_box = MDBoxLayout(orientation="vertical", spacing="10dp", size_hint_y=None)
        self.results_box.bind(minimum_height=self.results_box.setter("height"))
        self.root_box.add_widget(self.results_box)

        self.run_report()

    def run_report(self):
        self.results_box.clear_widgets()
        d_from, d_to = self.from_field.text.strip(), self.to_field.text.strip()

        conn = db.get_connection()
        total_sales = conn.execute(
            "SELECT COALESCE(SUM(total),0) t FROM sales_invoices WHERE date BETWEEN ? AND ?",
            (d_from, d_to)).fetchone()["t"]
        total_purchases = conn.execute(
            "SELECT COALESCE(SUM(total),0) t FROM purchase_invoices WHERE date BETWEEN ? AND ?",
            (d_from, d_to)).fetchone()["t"]
        total_expenses = conn.execute(
            "SELECT COALESCE(SUM(amount),0) t FROM expenses WHERE date BETWEEN ? AND ?",
            (d_from, d_to)).fetchone()["t"]
        total_incomes = conn.execute(
            "SELECT COALESCE(SUM(amount),0) t FROM incomes WHERE date BETWEEN ? AND ?",
            (d_from, d_to)).fetchone()["t"]
        conn.close()

        net = (total_sales + total_incomes) - (total_purchases + total_expenses)

        rows = [
            ("المبيعات", total_sales, (0.14, 0.39, 0.92, 1)),
            ("المشتريات", total_purchases, (0.85, 0.47, 0.02, 1)),
            ("المصاريف", total_expenses, (0.86, 0.15, 0.15, 1)),
            ("الإيرادات الأخرى", total_incomes, (0.09, 0.64, 0.29, 1)),
            ("الصافي", net, (0.09, 0.64, 0.29, 1) if net >= 0 else (0.86, 0.15, 0.15, 1)),
        ]
        for label, value, color in rows:
            card = MDCard(orientation="horizontal", padding="12dp", size_hint_y=None, height="56dp",
                          elevation=1, radius=[8])
            card.add_widget(MDLabel(text=format_money(value), halign="left", text_color=color, bold=True))
            card.add_widget(MDLabel(text=ar(label), halign="right"))
            self.results_box.add_widget(card)

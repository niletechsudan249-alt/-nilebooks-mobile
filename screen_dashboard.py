# -*- coding: utf-8 -*-
"""لوحة التحكم: ملخص سريع للمبيعات والمشتريات والمصاريف والأرباح"""
from kivy.uix.screenmanager import Screen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView

import database as db
from arabic_support import ar
from ui_helpers import format_money, get_base_currency


class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "dashboard"
        self.scroll = MDScrollView()
        self.root_box = MDBoxLayout(orientation="vertical", spacing="12dp", padding="14dp",
                                     size_hint_y=None)
        self.root_box.bind(minimum_height=self.root_box.setter("height"))
        self.scroll.add_widget(self.root_box)
        self.add_widget(self.scroll)

    def on_pre_enter(self, *a):
        self.refresh()

    def refresh(self):
        self.root_box.clear_widgets()

        title = MDLabel(text=ar("لوحة التحكم"), font_style="H5", halign="right",
                         size_hint_y=None, height="40dp")
        self.root_box.add_widget(title)

        base = get_base_currency()
        symbol = base["symbol"] if base else ""
        conn = db.get_connection()
        total_sales = conn.execute("SELECT COALESCE(SUM(total),0) t FROM sales_invoices").fetchone()["t"]
        total_purchases = conn.execute("SELECT COALESCE(SUM(total),0) t FROM purchase_invoices").fetchone()["t"]
        total_expenses = conn.execute("SELECT COALESCE(SUM(amount),0) t FROM expenses").fetchone()["t"]
        total_incomes = conn.execute("SELECT COALESCE(SUM(amount),0) t FROM incomes").fetchone()["t"]
        low_stock = conn.execute(
            "SELECT COUNT(*) c FROM products WHERE quantity <= min_quantity AND is_active=1"
        ).fetchone()["c"]
        conn.close()

        profit = (total_sales + total_incomes) - (total_purchases + total_expenses)

        cards_data = [
            ("إجمالي المبيعات", total_sales, (0.14, 0.39, 0.92, 1)),
            ("إجمالي المشتريات", total_purchases, (0.85, 0.47, 0.02, 1)),
            ("إجمالي المصاريف", total_expenses, (0.86, 0.15, 0.15, 1)),
            ("صافي الربح التقديري", profit, (0.09, 0.64, 0.29, 1) if profit >= 0 else (0.86, 0.15, 0.15, 1)),
        ]

        for label, value, color in cards_data:
            card = MDCard(orientation="vertical", padding="14dp", size_hint_y=None, height="90dp",
                          elevation=1, radius=[10])
            card.add_widget(MDLabel(text=ar(label), halign="right", theme_text_color="Secondary",
                                    size_hint_y=None, height="24dp"))
            card.add_widget(MDLabel(text=format_money(value, symbol), halign="right",
                                    font_style="H6", size_hint_y=None, height="32dp",
                                    text_color=color))
            self.root_box.add_widget(card)

        if low_stock > 0:
            warn_card = MDCard(orientation="vertical", padding="12dp", size_hint_y=None, height="50dp",
                               md_bg_color=(0.996, 0.953, 0.780, 1), radius=[8])
            warn_card.add_widget(MDLabel(
                text=ar(f"⚠ يوجد {low_stock} صنف وصل للحد الأدنى من المخزون"),
                halign="right", theme_text_color="Custom", text_color=(0.57, 0.25, 0.05, 1)))
            self.root_box.add_widget(warn_card)

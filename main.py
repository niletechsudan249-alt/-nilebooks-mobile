# -*- coding: utf-8 -*-
"""
Nilebooks - نسخة الموبايل (Android)
تطبيق حسابات كامل: فواتير بيع/شراء، مخزون، عملاء وموردون، مصاريف، تقارير، عملات متعددة
"""
import os
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, NoTransition
from kivy.uix.boxlayout import BoxLayout
from kivymd.app import MDApp
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.navigationdrawer import MDNavigationLayout, MDNavigationDrawer
from kivymd.uix.list import OneLineIconListItem, IconLeftWidget
from kivymd.uix.boxlayout import MDBoxLayout

import database as db
from arabic_support import ar, FONT_PATH

from screen_dashboard import DashboardScreen
from screen_products import ProductsScreen
from screen_contacts import ContactsScreen
from screen_invoices import InvoiceListScreen, InvoiceEditorScreen
from screen_expenses import ExpensesIncomeScreen
from screen_reports import ReportsScreen
from screen_settings import SettingsScreen

NAV_ITEMS = [
    ("dashboard", "لوحة التحكم", "view-dashboard"),
    ("products", "المنتجات والمخزون", "package-variant"),
    ("sales", "فواتير المبيعات", "receipt"),
    ("purchases", "فواتير المشتريات", "cart"),
    ("customers", "العملاء", "account-group"),
    ("suppliers", "الموردون", "truck"),
    ("expenses", "المصاريف", "cash-minus"),
    ("incomes", "إيرادات أخرى", "cash-plus"),
    ("reports", "التقارير", "chart-bar"),
    ("settings", "الإعدادات", "cog"),
]


class NilebooksApp(MDApp):
    def build(self):
        self.title = "Nilebooks"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"

        # تسجيل خط عربي يدعم كل الحروف بشكل صحيح (يجب توفر الملف في assets/fonts)
        font_full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), FONT_PATH)
        if os.path.exists(font_full_path):
            LabelBase.register(name="Roboto", fn_regular=font_full_path)
        self.theme_cls.font_styles["H5"][0] = "Roboto"

        # قاعدة البيانات تُحفظ في مجلد بيانات التطبيق الخاص بالهاتف
        db.set_db_dir(self.user_data_dir)
        db.init_db()

        self.sm = ScreenManager(transition=NoTransition())
        self._invoice_editors = {}

        self.sm.add_widget(DashboardScreen())
        self.sm.add_widget(ProductsScreen())
        self.sm.add_widget(InvoiceListScreen(kind="sale", manager_app=self))
        self.sm.add_widget(InvoiceListScreen(kind="purchase", manager_app=self))
        self.sm.add_widget(ContactsScreen(entity_type="customers"))
        self.sm.add_widget(ContactsScreen(entity_type="suppliers"))
        self.sm.add_widget(ExpensesIncomeScreen(kind="expense"))
        self.sm.add_widget(ExpensesIncomeScreen(kind="income"))
        self.sm.add_widget(ReportsScreen())
        self.sm.add_widget(SettingsScreen())

        return self._build_root_layout()

    def get_invoice_editor(self, kind):
        """ينشئ محرر الفاتورة عند أول استخدام فقط، ويعيد استخدامه لاحقاً"""
        if kind not in self._invoice_editors:
            editor = InvoiceEditorScreen(kind=kind, manager_app=self)
            self._invoice_editors[kind] = editor
            self.sm.add_widget(editor)
        return self._invoice_editors[kind]

    def _build_root_layout(self):
        nav_layout = MDNavigationLayout()

        main_box = MDBoxLayout(orientation="vertical")
        self.toolbar = MDTopAppBar(
            title=ar("Nilebooks"),
            left_action_items=[["menu", lambda x: self.open_drawer()]],
        )
        main_box.add_widget(self.toolbar)
        main_box.add_widget(self.sm)

        nav_layout.add_widget(main_box)

        self.drawer = MDNavigationDrawer()
        drawer_box = MDBoxLayout(orientation="vertical")
        from kivymd.uix.list import MDList
        drawer_list = MDList()
        for key, label, icon in NAV_ITEMS:
            item = OneLineIconListItem(text=ar(label))
            item.add_widget(IconLeftWidget(icon=icon))
            item.bind(on_release=lambda inst, k=key: self.switch_screen(k))
            drawer_list.add_widget(item)
        drawer_box.add_widget(drawer_list)
        self.drawer.add_widget(drawer_box)
        nav_layout.add_widget(self.drawer)

        return nav_layout

    def open_drawer(self):
        self.drawer.set_state("open")

    def switch_screen(self, key):
        self.sm.current = key
        self.drawer.set_state("close")


def main():
    NilebooksApp().run()


if __name__ == "__main__":
    main()

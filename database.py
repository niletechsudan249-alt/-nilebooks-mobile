# -*- coding: utf-8 -*-
"""قاعدة بيانات SQLite محلية على الهاتف (نفس مخطط نسخة سطح المكتب لتسهيل التوافق مستقبلاً)"""
import sqlite3
import os
from datetime import datetime

DB_NAME = "nilebooks_mobile.db"
_db_dir_override = None


def set_db_dir(path):
    """تُستدعى من main.py عند بدء التطبيق لتحديد مجلد بيانات الهاتف (user_data_dir الخاص بـ KivyMD)"""
    global _db_dir_override
    _db_dir_override = path


def get_db_path():
    base_dir = _db_dir_override or os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, DB_NAME)


def get_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY, value TEXT)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS currencies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        symbol TEXT,
        rate_to_base REAL NOT NULL DEFAULT 1.0,
        is_base INTEGER NOT NULL DEFAULT 0)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        sku TEXT,
        unit TEXT DEFAULT 'قطعة',
        purchase_price REAL NOT NULL DEFAULT 0,
        sale_price REAL NOT NULL DEFAULT 0,
        quantity REAL NOT NULL DEFAULT 0,
        min_quantity REAL NOT NULL DEFAULT 0,
        is_active INTEGER NOT NULL DEFAULT 1)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, phone TEXT, address TEXT,
        balance REAL NOT NULL DEFAULT 0, notes TEXT)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, phone TEXT, address TEXT,
        balance REAL NOT NULL DEFAULT 0, notes TEXT)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS sales_invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT NOT NULL, customer_id INTEGER, date TEXT NOT NULL,
        total REAL NOT NULL DEFAULT 0, paid REAL NOT NULL DEFAULT 0, notes TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers(id))""")

    cur.execute("""CREATE TABLE IF NOT EXISTS sales_invoice_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_id INTEGER NOT NULL,
        product_id INTEGER, product_name TEXT NOT NULL,
        quantity REAL NOT NULL, unit_price REAL NOT NULL, total REAL NOT NULL,
        FOREIGN KEY (invoice_id) REFERENCES sales_invoices(id) ON DELETE CASCADE)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS purchase_invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT NOT NULL, supplier_id INTEGER, date TEXT NOT NULL,
        total REAL NOT NULL DEFAULT 0, paid REAL NOT NULL DEFAULT 0, notes TEXT,
        FOREIGN KEY (supplier_id) REFERENCES suppliers(id))""")

    cur.execute("""CREATE TABLE IF NOT EXISTS purchase_invoice_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_id INTEGER NOT NULL,
        product_id INTEGER, product_name TEXT NOT NULL,
        quantity REAL NOT NULL, unit_price REAL NOT NULL, total REAL NOT NULL,
        FOREIGN KEY (invoice_id) REFERENCES purchase_invoices(id) ON DELETE CASCADE)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT NOT NULL,
        category TEXT, description TEXT, amount REAL NOT NULL)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS incomes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT NOT NULL,
        category TEXT, description TEXT, amount REAL NOT NULL)""")

    conn.commit()
    seed_defaults(conn)
    conn.close()


def seed_defaults(conn):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) c FROM currencies")
    if cur.fetchone()["c"] == 0:
        cur.execute("INSERT INTO currencies (code,name,symbol,rate_to_base,is_base) VALUES (?,?,?,?,?)",
                    ("SAR", "ريال سعودي", "ر.س", 1.0, 1))
        cur.execute("INSERT INTO currencies (code,name,symbol,rate_to_base,is_base) VALUES (?,?,?,?,?)",
                    ("USD", "دولار أمريكي", "$", 3.75, 0))
        conn.commit()
    cur.execute("SELECT COUNT(*) c FROM settings")
    if cur.fetchone()["c"] == 0:
        cur.execute("INSERT INTO settings (key,value) VALUES ('company_name','شركتي')")
        conn.commit()


def get_setting(key, default=None):
    conn = get_connection()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key, value):
    conn = get_connection()
    conn.execute(
        "INSERT INTO settings (key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value))
    conn.commit()
    conn.close()


def now_date():
    return datetime.now().strftime("%Y-%m-%d")

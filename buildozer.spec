[app]
title = Nilebooks
package.name = nilebooks
package.domain = com.nilebooks

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,db
source.include_patterns = assets/fonts/*.ttf

version = 1.0.0

requirements = python3,kivy==2.3.0,kivymd==1.2.0,arabic-reshaper,python-bidi,sqlite3

orientation = portrait
fullscreen = 0

# icon.filename = %(source.dir)s/assets/icon.png
# (أضف ملف أيقونة PNG مربع 512x512 هنا وفعّل السطر أعلاه لتخصيص شعار التطبيق)

android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

android.api = 34
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1

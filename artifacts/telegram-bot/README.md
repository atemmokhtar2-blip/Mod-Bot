# بوت الإشراف العربي — النسخة 3

بوت إشراف احترافي لمجموعات Telegram مبني بـ Python، aiogram 3، وPostgreSQL.

---

## النشر على Zeabur

### 1. أنشئ مشروعاً جديداً على Zeabur

ادخل إلى [zeabur.com](https://zeabur.com) → **New Project**.

### 2. أضف خدمة PostgreSQL

داخل المشروع: **Add Service → Database → PostgreSQL**.

بعد الإنشاء، انسخ **Internal Connection String** من تبويب Connection.

### 3. أضف خدمة البوت

**Add Service → Git → اختر المستودع**.

Zeabur يكتشف `requirements.txt` و`zbpack.json` تلقائياً.

### 4. اضبط متغيرات البيئة

في تبويب **Variables** لخدمة البوت:

| المتغير | القيمة |
|---------|--------|
| `TELEGRAM_BOT_TOKEN` | توكن البوت من @BotFather |
| `DATABASE_URL` | Internal Connection String من خدمة PostgreSQL |
| `DATABASE_SSL` | `false` (الشبكة الداخلية لا تحتاج SSL) |
| `LOG_LEVEL` | `INFO` |

> **ملاحظة:** إذا استخدمت قاعدة بيانات خارجية (Supabase، Neon، إلخ) اضبط `DATABASE_SSL=true`.

### 5. انشر

اضغط **Deploy** — Zeabur سيثبّت الاعتماديات ويشغّل `python main.py` تلقائياً.

---

## الصلاحيات المطلوبة في المجموعة

أضف البوت مشرفاً مع الصلاحيات التالية:
- حذف الرسائل
- حظر الأعضاء
- تقييد الأعضاء
- تثبيت الرسائل

---

## متغيرات البيئة الكاملة

| المتغير | مطلوب | الوصف |
|---------|-------|-------|
| `TELEGRAM_BOT_TOKEN` | ✅ | من @BotFather |
| `DATABASE_URL` | ✅ | رابط اتصال PostgreSQL |
| `DATABASE_SSL` | ❌ | `true` لقواعد البيانات الخارجية، `false` للشبكة الداخلية |
| `LOG_LEVEL` | ❌ | `INFO` افتراضياً |

---

## هيكل المشروع

```
artifacts/telegram-bot/
├── main.py                     # نقطة الدخول
├── config.py                   # إعدادات متغيرات البيئة
├── requirements.txt            # الاعتماديات
├── zbpack.json                 # إعدادات Zeabur
├── database/
│   ├── models.py               # نماذج SQLAlchemy (9 جداول)
│   ├── connection.py           # محرك async + جلسة
│   └── repository.py          # جميع عمليات قاعدة البيانات
├── bot/
│   ├── handlers/
│   │   ├── start.py            # /start → لوحة التحكم
│   │   ├── group_events.py     # أحداث المجموعة
│   │   ├── message_filter.py   # الإشراف التلقائي
│   │   ├── admin_commands.py   # /ban /mute /warn ...
│   │   └── callbacks.py        # ردود الأزرار المضمنة
│   ├── keyboards/builder.py    # جميع لوحات المفاتيح
│   ├── middlewares/            # حقن جلسة قاعدة البيانات
│   ├── filters/                # فلاتر الأذونات
│   ├── services/               # منطق الأعمال
│   └── strings/ar.py           # جميع النصوص بالعربية
└── utils/
    ├── logger.py               # إعداد التسجيل
    └── helpers.py              # أدوات مساعدة
```

---

## جداول قاعدة البيانات

| الجدول | الغرض |
|--------|-------|
| users | جميع مستخدمي Telegram المعروفين |
| groups | المجموعات المسجّلة |
| channels | القنوات المسجّلة |
| admins | صلاحيات المشرفين لكل مجموعة |
| group_settings | إعدادات كل مجموعة |
| filters | فلاتر كل مجموعة مع الإجراء المطلوب |
| warnings | عدادات التحذيرات لكل مستخدم/مجموعة |
| logs | سجل تدقيق لجميع الأحداث |
| statistics | إحصائيات يومية لكل مجموعة |

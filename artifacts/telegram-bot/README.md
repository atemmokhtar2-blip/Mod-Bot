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

## النشر على Vercel (وضع Webhook)

> يعمل البوت افتراضياً بنظام Long Polling (`python main.py`) — مناسب لـ Replit وZeabur.
> للنشر على **Vercel** يجب التبديل إلى نظام **Webhook** بدلاً من Polling، لأن Vercel لا يدعم عمليات طويلة الأمد.

### 1. جهّز قاعدة بيانات PostgreSQL خارجية

Vercel لا يوفر قاعدة بيانات. استخدم [Neon](https://neon.tech) أو [Supabase](https://supabase.com) (كلاهما يوفر PostgreSQL مجاني)، ثم انسخ رابط الاتصال (Connection String).

### 2. اربط المستودع بـ Vercel

في [vercel.com](https://vercel.com) → **Add New Project** → اختر المستودع. لا حاجة لأي إعداد بناء (Build) — Vercel يكتشف `api/webhook.py` و`requirements.txt` تلقائياً بفضل `vercel.json` الموجود في هذا المجلد.

### 3. أضف متغيرات البيئة في Vercel

في **Project Settings → Environment Variables**:

| المتغير | القيمة |
|---------|--------|
| `TELEGRAM_BOT_TOKEN` | توكن البوت من @BotFather |
| `DATABASE_URL` | رابط الاتصال من Neon/Supabase |
| `DATABASE_SSL` | `true` (قواعد البيانات الخارجية تتطلب SSL) |
| `BOT_OWNER_IDS` | رقمك التعريفي على Telegram (أو أكثر، مفصولة بفواصل) |
| `AI_KEY_ENCRYPTION_KEY` | مفتاح تشفير Fernet (32 بايت urlsafe-base64) — يجب أن يكون **نفس القيمة** المستخدمة في أي بيئة أخرى تشغّل البوت على نفس قاعدة البيانات، وإلا سيتعذّر فكّ تشفير مفاتيح Gemini المخزّنة |
| `WEBHOOK_SECRET` | نص عشوائي لتوثيق أن الطلبات قادمة من Telegram فعلاً |
| `LOG_LEVEL` | `INFO` |

### 4. انشر المشروع

اضغط **Deploy**. بعد اكتمال النشر ستحصل على رابط مثل `https://your-app.vercel.app`.

### 5. فعّل الـ Webhook

من بيئة تحتوي على نفس متغيرات البيئة (مثل هذا الـ Replit، أو محلياً):

```bash
python scripts/setup_webhook.py --url https://your-app.vercel.app/api/webhook
```

### الرجوع إلى Long Polling

```bash
python scripts/setup_webhook.py --delete
python main.py
```

> ⚠️ لا تشغّل Webhook و Long Polling في نفس الوقت على نفس التوكن — Telegram يسمح بمصدر واحد فقط لاستقبال التحديثات.

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
| `BOT_OWNER_IDS` | ✅ | رقم/أرقام Telegram لمالكي البوت (مفصولة بفواصل) — هم الوحيدون القادرون على إدارة مفاتيح Gemini |
| `AI_KEY_ENCRYPTION_KEY` | ✅* | مفتاح Fernet لتشفير مفاتيح Gemini المخزّنة في قاعدة البيانات. مطلوب فقط عند استخدام ميزة الذكاء الاصطناعي |
| `WEBHOOK_SECRET` | ❌ | مطلوب فقط في وضع Vercel/Webhook — يوثّق أن الطلبات قادمة من Telegram |
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

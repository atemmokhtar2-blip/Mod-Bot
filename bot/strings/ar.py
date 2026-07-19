"""
Arabic UI strings — single source of truth for every user-facing message.
Version 4: Advanced Settings & Administration.

Usage:
    from bot.strings.ar import S
    await message.reply(S.cmd_ban_missing_target)
"""

from __future__ import annotations


class S:
    # ─── General ────────────────────────────────────────────────────────────
    yes = "نعم"
    no = "لا"
    back = "⬅️ رجوع"
    confirm = "✅ تأكيد"
    cancel = "❌ إلغاء"
    enabled = "مفعّل"
    disabled = "معطّل"
    success = "✅ تم بنجاح"
    error = "❌ حدث خطأ"
    not_found = "❌ لم يُعثر على العنصر."
    no_permission = "🚫 ليس لديك صلاحية لهذا الإجراء."
    unknown = "غير معروف"

    on  = "🟢"
    off = "🔴"

    no_permission_cb = "⛔ ليس لديك صلاحية لاستخدام أدوات الإدارة."
    owner_only_cb    = "⛔ هذا الإجراء متاح لمالك المجموعة فقط."
    keyboard_expired = "⚠️ انتهت صلاحية هذه الواجهة، يرجى فتح لوحة التحكم مرة أخرى."

    # ─── /start & Home ──────────────────────────────────────────────────────
    start_greeting = (
        "╔══════════════════╗\n"
        "      🔱 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 🔱\n"
        "╚══════════════════╝\n\n"
        "👋 أهلاً، <b>{name}</b>!\n\n"
        "أنا بوت <b>𝟕 •</b> 🤖\n"
        "اخترت خدمة قوية لإدارة مجموعاتك.\n\n"
        "{status}\n\n"
        "─── ❖ ── ✦ ── ❖ ───"
    )
    start_has_groups = "📋 أنت تدير <b>{count}</b> مجموعة. اختر مجموعة للبدء:"
    start_no_groups = (
        "📌 لا توجد مجموعات مرتبطة بعد.\n\n"
        "أضفني إلى مجموعتك ومنحني صلاحيات <b>المشرف</b>،\n"
        "ثم اضغط على زر <b>➕ إدارة هذه المجموعة</b> داخل المجموعة."
    )

    home_title = (
        "𖠇 ─── 𝐇𝐎𝐌𝐄 𝐏𝐀𝐍𝐄𝐋 ─── 𖠇\n\n"
        "👋 أهلاً، <b>{name}</b>!\n"
        "┌ 𝐆𝐑𝐎𝐔𝐏 𖤱 <b>{group}</b> 𖦴\n"
        "└ 𝐒𝐓𝐀𝐓𝐔𝐒 𖤱 <b>Active</b> 𖦴\n\n"
        "─── ❖ ── ✦ ── ❖ ───"
    )
    home_title_no_group = (
        "════════════════════\n"
        "🏠 <b>الرئيسية</b>\n\n"
        "أهلاً، <b>{name}</b>!\n"
        "════════════════════"
    )

    # ─── Main Menu buttons ───────────────────────────────────────────────────
    btn_home       = "🏠 الرئيسية"
    btn_groups     = "📋 مجموعاتي"
    btn_protection = "🛡️ الحماية"
    btn_members    = "👥 إدارة الأعضاء"
    btn_admins     = "👮 إدارة المشرفين"
    btn_channels   = "📢 إدارة القنوات"
    btn_settings   = "⚙️ الإعدادات"
    btn_help       = "❓ المساعدة"
    btn_back       = "⬅️ رجوع"
    btn_cancel     = "🔙 رجوع"

    # ─── V5: Updates channel & Donations ─────────────────────────────────────
    btn_updates_channel  = "📢 قناة التحديثات"
    updates_channel_url  = "https://t.me/h7h7h7Updates"
    btn_donate           = "💎 دعم البوت"

    btn_stats = "📊 الإحصائيات"
    btn_logs  = "📜 السجل"

    # ─── Group panel ────────────────────────────────────────────────────────
    group_panel_title = (
        "════════════════════\n"
        "🏠 <b>{title}</b>\n\n"
        "اختر قسماً للإدارة:\n"
        "════════════════════"
    )
    no_groups_yet = (
        "════════════════════\n"
        "📋 <b>لا توجد مجموعات مرتبطة</b>\n\n"
        "أضفني إلى مجموعة ومنحني صلاحيات <b>المشرف</b>،\n"
        "ثم اضغط على زر <b>➕ إدارة هذه المجموعة</b>.\n"
        "════════════════════"
    )
    groups_title = (
        "════════════════════\n"
        "📋 <b>مجموعاتي</b>\n\n"
        "اختر مجموعة للإدارة:\n"
        "════════════════════"
    )

    btn_mod              = "🛡️ الحماية"
    btn_panel_members    = "👥 إدارة الأعضاء"
    btn_panel_admins     = "👮 إدارة المشرفين"
    btn_panel_settings   = "⚙️ الإعدادات"
    btn_panel_stats      = "📊 الإحصائيات"
    btn_panel_logs       = "📜 السجل"
    btn_panel_back       = "⬅️ مجموعاتي"

    # ─── Group activation (V3) ───────────────────────────────────────────────
    btn_manage_group = "➕ إدارة هذه المجموعة"
    bot_activation_msg = (
        "══════════════════\n"
        "		»» تم تفعيل البوت بنجاح\n\n\n"
        "لإدارة هذه المجموعة اضغط على الزر الموجود بالأسفل.\n\n"
        "h7h7h7_bot\n"
        "════════════════════"
    )
    group_linked = (
        "════════════════════\n"
        "✅ <b>تم ربط المجموعة بنجاح</b>\n\n"
        "المجموعة: <b>{title}</b>\n\n"
        "يمكنك الآن التحكم الكامل بالمجموعة من هنا.\n"
        "════════════════════"
    )

    # ─── Moderation section ──────────────────────────────────────────────────
    mod_title = "🛡️ <b>𝐌𝐎𝐃𝐄𝐑𝐀𝐓𝐈𝐎𝐍 — {title}</b>"
    btn_filters = "🔍 الفلاتر ({active}/{total} مفعّل)"
    btn_actions = "⚡ إجراءات الفلاتر"
    btn_warn_limit = "⚠️ حد التحذيرات"

    filters_title = "🔍 <b>فلاتر الإشراف</b>\n\nاضغط لتفعيل/تعطيل الفلتر:"
    filter_actions_title = "⚡ <b>إجراءات الفلاتر</b>\n\nاختر فلتراً لضبط إجراءه:"
    filter_edit_action_title = "⚡ <b>إجراء: {name}</b>\n\nالحالي: <b>{action}</b>"

    # ─── V3 Protection Menu ──────────────────────────────────────────────────
    protection_title = (
        "𖠇 ─── 𝐏𝐑𝐎𝐓𝐄𝐂𝐓𝐈𝐎𝐍 ─── 𖠇\n\n"
        "┌ 𝐆𝐑𝐎𝐔𝐏 𖤱 <b>{title}</b> 𖦴\n"
        "└ 𝐅𝐈𝐋𝐓𝐄𝐑𝐒 𖤱 <b>Active</b> 𖦴\n\n"
        "{filters}\n"
        "─── ❖ ── ✦ ── ❖ ───"
    )
    btn_auto_protect_on  = "🟢 التفعيل التلقائي"
    btn_auto_protect_off = "🔴 التفعيل التلقائي"
    auto_protect_enabled_msg  = "✅ تم تفعيل الحماية التلقائية — جميع الفلاتر مفعّلة."
    auto_protect_disabled_msg = "🔴 تم إيقاف الحماية التلقائية — جميع الفلاتر معطّلة."

    # Filter labels (all 14)
    filter_bad_words        = "فلترة الكلمات المسيئة"
    filter_insults          = "فلترة الشتائم"
    filter_spam             = "فلترة السبام"
    filter_flood            = "فلترة السبام"
    filter_duplicates       = "فلترة التكرار"
    filter_advertisement    = "فلترة الإعلانات"
    filter_telegram_links   = "فلترة الروابط"
    filter_external_links   = "فلترة الروابط الخارجية"
    filter_excessive_emojis = "فلترة الإيموجي الزائد"
    filter_repeated_chars   = "فلترة الحروف المكررة"
    filter_long_messages    = "فلترة الرسائل الطويلة"
    # V4
    filter_forwarded        = "فلترة إعادة التوجيه"
    filter_mass_mention     = "فلترة المنشن الجماعي"
    filter_hashtag          = "فلترة الهاشتاج"

    # Action labels
    action_ignore = "👁️ تجاهل"
    action_delete = "❌ حذف الرسالة"
    action_warn   = "⚠️ تحذير"
    action_mute   = "🔇 كتم"
    action_kick   = "👢 طرد"
    action_ban    = "🚫 حظر"

    action_set_ok = "✅ تم ضبط إجراء <b>{filter}</b> على <b>{action}</b>."

    # ─── V4 Settings Center ──────────────────────────────────────────────────
    v4_settings_title = (
        "𖠇 ─── 𝐒𝐄𝐓𝐓𝐈𝐍𝐆𝐒 ─── 𖠇\n\n"
        "┌ 𝐆𝐑𝐎𝐔𝐏 𖤱 <b>{title}</b> 𖦴\n"
        "└ 𝐂𝐎𝐍𝐅𝐈𝐆 𖤱 <b>Active</b> 𖦴\n\n"
        "اختر القسم الذي تريد تعديله:\n\n"
        "─── ❖ ── ✦ ── ❖ ───"
    )

    btn_v4_protection   = "🛡️ إعدادات الحماية"
    btn_v4_punishments  = "⚠️ إعدادات العقوبات"
    btn_v4_permissions  = "👮 صلاحيات المشرفين"
    btn_v4_welcome      = "📝 رسالة الترحيب"
    btn_v4_goodbye      = "👋 رسالة المغادرة"
    btn_v4_media        = "🔒 إعدادات الوسائط"
    btn_v4_channel      = "📢 إعدادات القناة"
    btn_v4_language     = "🌍 اللغة"
    btn_v4_reset        = "♻️ إعادة ضبط الإعدادات"

    # ─── V4 Protection Settings ──────────────────────────────────────────────
    v4_protection_title = (
        "═══════════════\n"
        "🛡️ <b>إعدادات الحماية</b>\n\n"
        "المجموعة: <b>{title}</b>\n\n"
        "اضغط على أي فلتر لتفعيله أو تعطيله:\n"
        "═══════════════"
    )

    # ─── V4 Punishment Settings ──────────────────────────────────────────────
    v4_punishments_title = (
        "═══════════════\n"
        "⚠️ <b>إعدادات العقوبات</b>\n\n"
        "المجموعة: <b>{title}</b>\n\n"
        "اختر فلتراً لضبط عقوبته:\n"
        "═══════════════"
    )
    v4_punishment_filter_title = (
        "═══════════════\n"
        "⚠️ <b>عقوبة: {filter_name}</b>\n\n"
        "العقوبة الحالية: <b>{current}</b>\n\n"
        "اختر العقوبة الجديدة:\n"
        "═══════════════"
    )
    v4_punishment_set = "✅ تم ضبط عقوبة <b>{filter}</b> على <b>{action}</b>."

    # ─── V4 Admin Permissions ────────────────────────────────────────────────
    v4_permissions_title = (
        "═══════════════\n"
        "👮 <b>صلاحيات المشرفين</b>\n\n"
        "المجموعة: <b>{title}</b>\n\n"
        "⚠️ ملاحظة: التعديل متاح لمالك المجموعة فقط.\n\n"
        "اضغط على الصلاحية لتفعيلها أو تعطيلها:\n"
        "═══════════════"
    )
    v4_perm_toggled = "✅ تم تعديل الصلاحية."

    perm_delete        = "حذف الرسائل"
    perm_ban           = "حظر الأعضاء"
    perm_unban         = "رفع الحظر"
    perm_mute          = "كتم الأعضاء"
    perm_unmute        = "رفع الكتم"
    perm_pin           = "تثبيت الرسائل"
    perm_unpin         = "إلغاء التثبيت"
    perm_warn          = "إدارة التحذيرات"
    perm_edit_settings = "تعديل الإعدادات"
    perm_manage_admins = "إدارة المشرفين"

    # ─── V4 Welcome Message ──────────────────────────────────────────────────
    v4_welcome_title = (
        "═══════════════\n"
        "📝 <b>رسالة الترحيب</b>\n\n"
        "المجموعة: <b>{title}</b>\n\n"
        "الحالة: <b>{status}</b>\n\n"
        "النص الحالي:\n<i>{text}</i>\n\n"
        "المتغيرات المتاحة:\n"
        "<code>{{الاسم}}</code> • <code>{{اسم_المجموعة}}</code> • <code>{{اسم_المستخدم}}</code>\n"
        "═══════════════"
    )
    btn_v4_welcome_toggle = "{status} تفعيل رسالة الترحيب"
    btn_v4_welcome_edit   = "✏️ تعديل النص"
    btn_v4_welcome_preview = "👁️ معاينة"

    welcome_edit_prompt = (
        "═══════════════\n"
        "✏️ <b>تعديل رسالة الترحيب</b>\n\n"
        "النص الحالي:\n<i>{current}</i>\n\n"
        "أرسل النص الجديد.\n"
        "المتغيرات المتاحة:\n"
        "<code>{{الاسم}}</code> — الاسم الأول\n"
        "<code>{{اسم_المجموعة}}</code> — اسم المجموعة\n"
        "<code>{{اسم_المستخدم}}</code> — اليوزر\n"
        "═══════════════"
    )
    welcome_updated = "✅ تم تحديث رسالة الترحيب!\n\nمعاينة:\n<i>{text}</i>"
    welcome_preview = "👁️ <b>معاينة رسالة الترحيب:</b>\n\n{text}"

    # ─── V4 Goodbye Message ──────────────────────────────────────────────────
    v4_goodbye_title = (
        "═══════════════\n"
        "👋 <b>رسالة المغادرة</b>\n\n"
        "المجموعة: <b>{title}</b>\n\n"
        "الحالة: <b>{status}</b>\n\n"
        "النص الحالي:\n<i>{text}</i>\n\n"
        "المتغيرات المتاحة:\n"
        "<code>{{الاسم}}</code> • <code>{{اسم_المجموعة}}</code> • <code>{{اسم_المستخدم}}</code>\n"
        "═══════════════"
    )
    btn_v4_goodbye_toggle  = "{status} تفعيل رسالة المغادرة"
    btn_v4_goodbye_edit    = "✏️ تعديل النص"
    btn_v4_goodbye_preview = "👁️ معاينة"

    goodbye_edit_prompt = (
        "═══════════════\n"
        "✏️ <b>تعديل رسالة المغادرة</b>\n\n"
        "النص الحالي:\n<i>{current}</i>\n\n"
        "أرسل النص الجديد.\n"
        "المتغيرات المتاحة:\n"
        "<code>{{الاسم}}</code> — الاسم الأول\n"
        "<code>{{اسم_المجموعة}}</code> — اسم المجموعة\n"
        "<code>{{اسم_المستخدم}}</code> — اليوزر\n"
        "═══════════════"
    )
    goodbye_updated = "✅ تم تحديث رسالة المغادرة!\n\nمعاينة:\n<i>{text}</i>"
    goodbye_preview = "👁️ <b>معاينة رسالة المغادرة:</b>\n\n{text}"

    # ─── V4 Media Settings ───────────────────────────────────────────────────
    v4_media_title = (
        "═══════════════\n"
        "🔒 <b>إعدادات الوسائط</b>\n\n"
        "المجموعة: <b>{title}</b>\n\n"
        "اضغط على أي نوع لقفله أو فتحه:\n"
        "═══════════════"
    )
    v4_media_locked   = "✅ تم قفل {media_type}."
    v4_media_unlocked = "✅ تم فتح {media_type}."
    v4_media_blocked  = "🔒 <a href=\"tg://user?id={uid}\">{name}</a> — هذا النوع من الوسائط محظور."

    media_photos    = "📷 الصور"
    media_video     = "🎥 الفيديو"
    media_audio     = "🎵 الصوتيات"
    media_documents = "📄 الملفات"
    media_stickers  = "🎭 الملصقات"
    media_gifs      = "🎬 GIF"
    media_polls     = "📊 الاستفتاءات"
    media_locations = "📍 المواقع"
    media_voice     = "🎤 الرسائل الصوتية"

    # ─── V4 Channel Settings ─────────────────────────────────────────────────
    v4_channel_title = (
        "═══════════════\n"
        "📢 <b>إعدادات القناة</b>\n\n"
        "القناة: <b>{title}</b>\n\n"
        "اختر إجراءً:\n"
        "═══════════════"
    )
    v4_channel_no_channels = (
        "═══════════════\n"
        "📢 <b>إعدادات القناة</b>\n\n"
        "لا توجد قنوات مربوطة.\n"
        "📌 أضفني إلى قناة كمشرف لتظهر هنا.\n"
        "═══════════════"
    )
    btn_v4_ch_info    = "ℹ️ معلومات القناة"
    btn_v4_ch_verify  = "✅ التحقق من الصلاحيات"
    btn_v4_ch_pin     = "📌 تثبيت آخر منشور"
    btn_v4_ch_post    = "📝 إرسال رسالة"
    btn_v4_ch_delete  = "🗑️ حذف آخر منشور"

    v4_ch_info_text = (
        "═══════════════\n"
        "📢 <b>معلومات القناة</b>\n\n"
        "🆔 المعرّف: <code>{channel_id}</code>\n"
        "📛 الاسم: {title}\n"
        "🔗 اليوزر: {username}\n"
        "═══════════════"
    )
    v4_ch_verify_ok   = "✅ البوت يملك الصلاحيات الكاملة في هذه القناة."
    v4_ch_verify_fail = "⚠️ البوت لا يملك كامل الصلاحيات. تحقق من إعدادات المشرف."
    v4_ch_pin_ok      = "✅ تم تثبيت آخر منشور."
    v4_ch_pin_fail    = "❌ تعذّر التثبيت. تحقق من صلاحياتي."
    v4_ch_delete_ok   = "✅ تم حذف آخر منشور."
    v4_ch_delete_fail = "❌ تعذّر الحذف. تحقق من صلاحياتي."

    # ─── V4 Language ─────────────────────────────────────────────────────────
    v4_language_title = (
        "═══════════════\n"
        "🌍 <b>اللغة</b>\n\n"
        "المجموعة: <b>{title}</b>\n\n"
        "اللغة الحالية: <b>{current}</b>\n\n"
        "اختر اللغة:\n"
        "═══════════════"
    )
    v4_language_set = "✅ تم تغيير اللغة إلى <b>{lang}</b>."

    lang_ar = "🇸🇦 العربية"
    lang_en = "🇺🇸 English"

    # ─── V4 Reset Settings ───────────────────────────────────────────────────
    v4_reset_confirm = (
        "═══════════════\n"
        "♻️ <b>إعادة ضبط الإعدادات</b>\n\n"
        "⚠️ هل أنت متأكد من إعادة جميع إعدادات المجموعة؟\n\n"
        "سيتم إعادة ضبط:\n"
        "• جميع الفلاتر\n"
        "• رسائل الترحيب والمغادرة\n"
        "• إعدادات الوسائط\n"
        "• حد التحذيرات\n"
        "• العقوبات\n\n"
        "⛔ هذا الإجراء لا يمكن التراجع عنه!\n"
        "═══════════════"
    )
    v4_reset_done = (
        "════════════════════\n"
        "♻️ <b>تمت إعادة الضبط</b>\n\n"
        "✅ تم إعادة جميع إعدادات المجموعة إلى الوضع الافتراضي.\n"
        "════════════════════"
    )

    # ─── Settings (legacy — kept for backwards compat) ────────────────────────
    settings_title = (
        "═══════════════\n"
        "⚙️ <b>الإعدادات</b>\n\n"
        "المجموعة: <b>{title}</b>\n"
        "═══════════════"
    )

    btn_settings_protection  = "🛡️ الحماية"
    btn_settings_punishments = "⚠️ العقوبات"
    btn_settings_welcome     = "📝 الترحيب"
    btn_settings_permissions = "👮 الصلاحيات"
    btn_settings_notifications = "🔔 الإشعارات"
    btn_settings_stats_cfg   = "📊 الإحصائيات"

    btn_welcome_toggle      = "📝 الترحيب: {status}"
    btn_welcome_edit        = "✏️ تعديل نص الترحيب"
    btn_logs_toggle         = "📋 سجل الأحداث: {status}"
    btn_warn_limit_setting  = "⚠️ حد التحذيرات"
    btn_punishment          = "🔨 العقوبة التلقائية"

    warn_limit_prompt = "⚠️ حد التحذيرات الحالي: <b>{current}</b>\n\nأرسل رقماً من 1 إلى 20:"
    warn_limit_invalid = "❌ أرسل رقماً صحيحاً بين 1 و 20."
    warn_limit_set = "✅ تم ضبط حد التحذيرات على <b>{limit}</b>."

    punishment_title = "🔨 <b>العقوبة التلقائية</b>\n\nتُطبَّق عند الوصول لحد التحذيرات:"
    punishment_mute = "🔇 كتم"
    punishment_kick = "👢 طرد"
    punishment_ban  = "🚫 حظر"
    punishment_set  = "✅ تم ضبط العقوبة التلقائية على <b>{p}</b>."

    # ─── Members section ─────────────────────────────────────────────────────
    members_title = (
        "════════════════════\n"
        "👥 <b>إدارة الأعضاء</b>\n\n"
        "استخدم الأوامر للإجراءات:\n"
        "<code>/ban /mute /warn /info</code>\n\n"
        "أو استخدم الأزرار أدناه:\n"
        "════════════════════"
    )
    btn_member_ban         = "🚫 حظر"
    btn_member_unban       = "✅ رفع الحظر"
    btn_member_mute        = "🔇 كتم ساعة"
    btn_member_unmute      = "🔊 رفع الكتم"
    btn_member_warn        = "⚠️ تحذير"
    btn_member_reset_warns = "🔄 إعادة التحذيرات"
    btn_member_history     = "📋 سجل التحذيرات"

    confirm_ban   = "⚠️ <b>تأكيد الحظر</b>\n\nهل أنت متأكد من حظر هذا المستخدم؟"
    confirm_mute  = "⚠️ <b>تأكيد الكتم</b>\n\nهل أنت متأكد من كتم هذا المستخدم لمدة ساعة؟"
    confirm_kick  = "⚠️ <b>تأكيد الطرد</b>\n\nهل أنت متأكد من طرد هذا المستخدم؟"
    confirm_reset = "⚠️ <b>تأكيد إعادة التحذيرات</b>\n\nهل أنت متأكد من إعادة تعيين جميع التحذيرات؟"
    confirm_yes   = "✅ نعم"
    confirm_no    = "❌ إلغاء"

    member_banned       = "✅ تم حظر العضو."
    member_ban_fail     = "❌ تعذّر حظر العضو."
    member_unbanned     = "✅ تم رفع الحظر."
    member_unban_fail   = "❌ تعذّر رفع الحظر."
    member_muted        = "✅ تم كتم العضو لمدة ساعة."
    member_mute_fail    = "❌ تعذّر كتم العضو."
    member_unmuted      = "✅ تم رفع الكتم."
    member_unmute_fail  = "❌ تعذّر رفع الكتم."
    member_warned       = "✅ تحذير {count}/{limit}."
    member_warned_punished = "✅ تحذير {count}/{limit} — تم تطبيق العقوبة التلقائية."
    member_warns_reset  = "✅ تم إعادة تعيين التحذيرات."

    # ─── Admins section ─────────────────────────────────────────────────────
    admins_title = (
        "════════════════════\n"
        "👮 <b>إدارة المشرفين</b>\n"
        "════════════════════"
    )
    admins_no_extra = (
        "════════════════════\n"
        "👮 <b>إدارة المشرفين</b>\n\n"
        "لا يوجد مشرفون إضافيون مسجّلون في البوت.\n"
        "📌 يمكن لمشرفي تيليغرام استخدام جميع الأوامر.\n"
        "════════════════════"
    )

    # ─── Channels ────────────────────────────────────────────────────────────
    channels_title = (
        "════════════════════\n"
        "📢 <b>إدارة القنوات</b>\n"
        "════════════════════"
    )
    channels_none = (
        "════════════════════\n"
        "📢 <b>إدارة القنوات</b>\n\n"
        "لا توجد قنوات مربوطة.\n"
        "📌 أضفني إلى قناة كمشرف لتظهر هنا.\n"
        "════════════════════"
    )
    btn_ch_post = "📝 إرسال رسالة"
    btn_ch_pin  = "📌 تثبيت آخر منشور"
    btn_ch_back = "⬅️ قنواتي"

    # ─── Statistics ──────────────────────────────────────────────────────────
    stats_title        = "📊 <b>الإحصائيات — {title}</b>"
    stats_no_data      = "📊 لا توجد إحصائيات مسجّلة بعد."
    stats_total_members = "👥 إجمالي الأعضاء"
    stats_messages     = "💬 الرسائل اليوم"
    stats_deleted      = "🗑️ الرسائل المحذوفة"
    stats_muted        = "🔇 المكتومون اليوم"
    stats_banned       = "🚫 المحظورون اليوم"
    stats_warned       = "⚠️ المحذّرون اليوم"
    stats_last_7       = "📅 <b>آخر 7 أيام:</b>"

    # ─── Logs ─────────────────────────────────────────────────────────────────
    logs_title = "📜 <b>سجل الأحداث</b>"
    logs_none  = "📜 لا توجد أحداث مسجّلة بعد."

    log_user_joined      = "انضمام عضو"
    log_user_left        = "مغادرة عضو"
    log_user_banned      = "حظر مستخدم"
    log_user_unbanned    = "رفع حظر"
    log_user_muted       = "كتم مستخدم"
    log_user_unmuted     = "رفع كتم"
    log_user_warned      = "تحذير"
    log_message_deleted  = "حذف رسالة"
    log_message_pinned   = "تثبيت رسالة"
    log_message_unpinned = "إلغاء تثبيت"
    log_settings_changed = "تغيير الإعدادات"
    log_filter_triggered = "تفعّل فلتر"
    log_bot_added        = "إضافة البوت"
    log_bot_removed      = "إزالة البوت"

    # ─── Help ────────────────────────────────────────────────────────────────
    help_text = (
        "════════════════════\n\n"
        "📖 <b>دليل الاستخدام</b>\n\n"
        "━━━━━━━━━━━━━━\n\n"
        "🚀 <b>كيفية البدء</b>\n\n"
        "1️⃣ أضف البوت إلى المجموعة.\n"
        "2️⃣ امنحه صلاحيات المشرف.\n"
        "3️⃣ اضغط على <b>➕ إدارة هذه المجموعة</b>.\n"
        "4️⃣ ابدأ في تخصيص إعدادات الحماية.\n\n"
        "━━━━━━━━━━━━━━\n\n"
        "👮 <b>أوامر الإدارة</b>\n\n"
        "<code>/ban</code> — حظر مستخدم (بالرد)\n"
        "<code>/unban</code> — رفع الحظر\n"
        "<code>/mute [مدة]</code> — كتم (مثال: 2h أو 30m)\n"
        "<code>/unmute</code> — رفع الكتم\n"
        "<code>/warn [سبب]</code> — تحذير مستخدم\n"
        "<code>/resetwarns</code> — إعادة تعيين التحذيرات\n"
        "<code>/del</code> — حذف رسالة (بالرد عليها)\n"
        "<code>/pin</code> — تثبيت رسالة\n"
        "<code>/unpin</code> — إلغاء التثبيت\n"
        "<code>/info</code> — عرض معلومات المستخدم\n\n"
        "━━━━━━━━━━━━━━\n\n"
        "⚙️ <b>لوحة التحكم</b>\n\n"
        "يمكنك التحكم الكامل بالمجموعة من خلال\n"
        "المحادثة الخاصة مع البوت باستخدام الأزرار التفاعلية.\n\n"
        "━━━━━━━━━━━━━━\n\n"
        "💬 <b>الدعم</b>\n\n"
        "سيتم إضافة بيانات التواصل مع المطور لاحقًا.\n\n"
        "════════════════════"
    )

    # ─── Auto-moderation notifications ───────────────────────────────────────
    auto_flood         = "🌊 <a href=\"tg://user?id={uid}\">{name}</a> — تم الكشف عن فيضان رسائل."
    auto_duplicate     = "🔁 <a href=\"tg://user?id={uid}\">{name}</a> — رسالة مكررة."
    auto_telegram_link = "🔗 <a href=\"tg://user?id={uid}\">{name}</a> — روابط تيليغرام ممنوعة."
    auto_external_link = "🌐 <a href=\"tg://user?id={uid}\">{name}</a> — روابط خارجية ممنوعة."
    auto_advertisement = "📣 <a href=\"tg://user?id={uid}\">{name}</a> — إعلان غير مسموح."
    auto_emoji         = "😂 <a href=\"tg://user?id={uid}\">{name}</a> — رموز تعبيرية زائدة."
    auto_repeated      = "🔤 <a href=\"tg://user?id={uid}\">{name}</a> — أحرف مكررة."
    auto_long_msg      = "📜 <a href=\"tg://user?id={uid}\">{name}</a> — الرسالة طويلة جداً."
    auto_bad_word      = "🤬 <a href=\"tg://user?id={uid}\">{name}</a> — كلمة محظورة."
    # V4
    auto_forwarded     = "↩️ <a href=\"tg://user?id={uid}\">{name}</a> — إعادة التوجيه ممنوعة."
    auto_mass_mention  = "📢 <a href=\"tg://user?id={uid}\">{name}</a> — منشن جماعي ممنوع."
    auto_hashtag       = "#️⃣ <a href=\"tg://user?id={uid}\">{name}</a> — هاشتاق ممنوع."
    auto_ai_text       = "🧠 <a href=\"tg://user?id={uid}\">{name}</a> — محتوى مخالف (تم رصده بالذكاء الاصطناعي)."
    auto_ai_image      = "🧠 <a href=\"tg://user?id={uid}\">{name}</a> — صورة مخالفة (تم رصدها بالذكاء الاصطناعي)."

    auto_warn_notice   = "⚠️ تحذير <b>{count}/{limit}</b> — {reason}"
    auto_punished      = "⚠️ <a href=\"tg://user?id={uid}\">{name}</a> وصل لحد التحذيرات — تم تطبيق العقوبة التلقائية."
    auto_muted         = "🔇 تم كتم <a href=\"tg://user?id={uid}\">{name}</a>."

    # ─── Admin command responses ──────────────────────────────────────────────
    cmd_need_target      = "❌ قم بالرد على رسالة المستخدم أو أدخل معرّفه."
    cmd_ban_ok           = "🚫 تم حظر {mention}{reason}."
    cmd_ban_fail         = "❌ تعذّر الحظر. تحقق من صلاحياتي."
    cmd_unban_ok         = "✅ تم رفع الحظر عن <b>{name}</b>."
    cmd_unban_fail       = "❌ تعذّر رفع الحظر."
    cmd_mute_ok          = "🔇 تم كتم {mention} لمدة <b>{duration}</b>{reason}."
    cmd_mute_fail        = "❌ تعذّر الكتم. تحقق من صلاحياتي."
    cmd_unmute_ok        = "🔊 تم رفع الكتم عن <b>{name}</b>."
    cmd_unmute_fail      = "❌ تعذّر رفع الكتم."
    cmd_warn_ok          = "⚠️ {mention} — تحذير <b>{count}/{limit}</b>.{reason}"
    cmd_warn_punished    = "⚠️ {mention} — تحذير <b>{limit}/{limit}</b> وتم تطبيق العقوبة التلقائية.{reason}"
    cmd_reason_prefix    = "\n📝 السبب: {reason}"
    cmd_resetwarns_ok    = "🔄 تم إعادة تعيين التحذيرات لـ <b>{name}</b>."
    cmd_del_need_reply   = "❌ قم بالرد على الرسالة التي تريد حذفها."
    cmd_del_fail         = "❌ تعذّر حذف الرسالة."
    cmd_pin_need_reply   = "❌ قم بالرد على الرسالة التي تريد تثبيتها."
    cmd_pin_fail         = "❌ تعذّر التثبيت."
    cmd_unpin_need_reply = "❌ قم بالرد على الرسالة التي تريد إلغاء تثبيتها."
    cmd_unpin_fail       = "❌ تعذّر إلغاء التثبيت."
    cmd_info_fail        = "❌ تعذّر تحديد المستخدم."

    cmd_info_text = (
        "𖠇 ─── 𝖡𝖮𝖳 𝖨𝖭𝖥𝖮 ─── 𖠇\n\n"
        "┌ 𝐔𝐒𝐄𝐑 𖤱 {name} 𖦴\n"
        "├ 𝐔𝐒𝐄𝐑𝐍𝐀𝐌𝐄 𖤱 {username} 𖦴\n"
        "├ 𝐒𝐓𝐀𝐓𝐔𝐒 𖤱 {status} 𖦴\n"
        "├ 𝐖𝐀𝐑𝐍𝐒 𖤱 <code>{warns}</code> 𖦴\n"
        "├ 𝐋𝐀𝐒𝐓 𝐖𝐀𝐑𝐍 𖤱 {last_warn} 𖦴\n"
        "└ 𝐈𝐃 𖤱 <code>{uid}</code> 𖦴\n\n"
        "─── ❖ ── ✦ ── ❖ ───"
    )

    # ─── Group events ─────────────────────────────────────────────────────────
    bot_joined_msg = (
        "👋 شكراً لإضافتي!\n\n"
        "أنا بوت <b>𝟕 •</b>\n"
        "امنحني صلاحيات <b>المشرف</b> لأتمكن من حماية المجموعة.\n\n"
        "استخدم /start في المحادثة الخاصة لفتح لوحة التحكم."
    )

    # ─── Warnings History ─────────────────────────────────────────────────────
    warn_history_title = "📋 <b>سجل التحذيرات</b>\n\n"
    warn_history_none  = "لا توجد تحذيرات مسجّلة."
    warn_history_entry = "• <b>{date}</b> — {reason} (بواسطة {actor})\n"

    # ─── V4.1 Custom Word List commands ───────────────────────────────────────
    wordlist_addword_usage = (
        "📝 <b>إضافة كلمة محظورة</b>\n\n"
        "الاستخدام: <code>/addword كلمة</code>\n\n"
        "مثال: <code>/addword حمار</code>"
    )
    wordlist_removeword_usage = (
        "🗑️ <b>إزالة كلمة محظورة</b>\n\n"
        "الاستخدام: <code>/removeword كلمة</code>\n\n"
        "مثال: <code>/removeword حمار</code>"
    )
    wordlist_word_too_short = (
        "❌ الكلمة قصيرة جداً (أقل من حرفين بعد التطبيع).\n"
        "أضف كلمة أطول."
    )
    wordlist_word_too_long = (
        "❌ الكلمة طويلة جداً (الحد الأقصى 100 حرف)."
    )
    wordlist_limit_reached = (
        "⚠️ وصلت إلى الحد الأقصى من الكلمات المخصصة (500 كلمة).\n"
        "احذف بعض الكلمات أولاً."
    )
    wordlist_added = "✅ تمت إضافة الكلمة: <code>{word}</code> إلى القائمة المحظورة."
    wordlist_already_exists = "⚠️ الكلمة <code>{word}</code> موجودة بالفعل في القائمة."
    wordlist_removed = "✅ تمت إزالة الكلمة: <code>{word}</code> من القائمة المحظورة."
    wordlist_not_found = "❌ الكلمة <code>{word}</code> غير موجودة في القائمة المخصصة."
    wordlist_empty = (
        "📋 قائمة الكلمات المحظورة المخصصة فارغة.\n\n"
        "أضف كلمات باستخدام: <code>/addword كلمة</code>"
    )
    wordlist_list_header = (
        "════════════════════\n"
        "📋 <b>الكلمات المحظورة المخصصة</b>\n\n"
        "إجمالي الكلمات المخصصة: <b>{count}</b>\n"
        "الكلمات المدمجة (مكتبة البوت): <b>{builtin}</b>\n\n"
        "قائمة الكلمات المخصصة:\n"
    )
    wordlist_list_truncated = "\n<i>… وأكثر من ذلك — يعرض {shown} من {total}</i>"
    wordlist_cleared = "♻️ تم مسح <b>{count}</b> كلمة مخصصة محظورة."

    # ─── V5: Donations (Telegram Stars ⭐) ──────────────────────────────────────
    donate_title = (
        "════════════════════\n"
        "💎 <b>دعم البوت</b>\n\n"
        "مساهمتك تساعدنا على الاستمرار في تطوير البوت وإضافة مميزات جديدة! 🚀\n\n"
        "اختر عدد نجوم تيليغرام ⭐ التي تريد التبرع بها، أو اضغط إلغاء:\n"
        "════════════════════"
    )
    btn_donate_amount   = "⭐ {amount}"
    btn_donate_cancel   = "❌ إلغاء"

    donate_cancelled = (
        "════════════════════\n"
        "❌ <b>تم إلغاء عملية الدعم</b>\n\n"
        "لا بأس، يمكنك دعم البوت في أي وقت تريده! 💙\n"
        "════════════════════"
    )

    donate_invoice_title       = "دعم مشروع بوت الإدارة 💎"
    donate_invoice_description = "شكراً لدعمك! تبرعك بـ {amount} ⭐ يساهم في استمرار تطوير البوت وتحسينه."
    donate_invoice_label       = "دعم البوت ({amount} ⭐)"
    donate_invoice_failed      = "❌ تعذّر إنشاء فاتورة الدعم. حاول مرة أخرى لاحقاً."

    donate_precheckout_ok = "✅"

    donate_thanks = (
        "════════════════════\n"
        "🎉 <b>شكراً لدعمك الكريم!</b>\n\n"
        "تم استلام تبرعك بمقدار <b>{amount} ⭐</b> بنجاح.\n"
        "دعمك يساهم في استمرار المشروع وتطويره باستمرار. 💙\n\n"
        "🙏 نقدّر ثقتك بنا.\n"
        "════════════════════"
    )

    # ─── V6: AI Protection (Gemini) ─────────────────────────────────────────────
    filter_ai_text  = "🧠 تحليل الرسائل بالذكاء الاصطناعي"
    filter_ai_image = "🧠 تحليل الصور بالذكاء الاصطناعي"

    btn_v4_ai = "🧠 الذكاء الاصطناعي"

    # V7 panel: simpler header — buttons show all sub-settings.
    ai_settings_title = (
        "════════════════════\n"
        "🧠 <b>نظام الحماية بالذكاء الاصطناعي</b>\n\n"
        "المجموعة: <b>{title}</b>\n\n"
        "📊 حالة النظام: {system_status}\n"
        "════════════════════"
    )

    btn_ai_toggle          = "{status} تفعيل الذكاء الاصطناعي"
    btn_ai_analyze_msgs    = "{status} 📝 تحليل الرسائل"
    btn_ai_analyze_images  = "{status} 🖼️ تحليل الصور"
    btn_ai_analyze_links   = "{status} 🔗 تحليل الروابط"
    btn_ai_sensitivity     = "🎯 مستوى الحساسية: {level}"
    btn_ai_actions         = "⚡ الإجراءات"
    btn_ai_status          = "📊 حالة النظام"

    # V7 — multi-action selection panel
    ai_actions_title = (
        "════════════════════\n"
        "⚡ <b>إجراءات الذكاء الاصطناعي</b>\n\n"
        "عند اكتشاف محتوى مخالف يُطبَّق كل إجراء مفعّل تلقائياً.\n"
        "يمكن تفعيل أكثر من إجراء في آنٍ واحد.\n"
        "════════════════════"
    )
    btn_ai_action_delete   = "{status} 🗑️ حذف الرسالة"
    btn_ai_action_warn     = "{status} ⚠️ تحذير"
    btn_ai_action_mute     = "{status} 🔇 كتم"
    btn_ai_action_ban      = "{status} 🚫 حظر"

    # V7 — 3-state system status
    ai_status_retrying     = "🟡 جاري إعادة المحاولة"

    # ─── RC1: 🧪 Live Gemini test button ─────────────────────────────────────
    btn_ai_test        = "🧪 اختبار Gemini"
    ai_test_running    = "⏳ جارٍ اختبار الاتصال بـ Gemini…"
    ai_test_no_keys    = "❌ لا توجد مفاتيح Gemini مفعّلة للاختبار."
    ai_test_result_ok  = (
        "════════════════════\n"
        "🧪 <b>نتيجة اختبار Gemini</b>\n\n"
        "الحالة: 🟢 يعمل بشكل طبيعي\n"
        "زمن الاستجابة: <b>{latency_ms} ms</b>\n"
        "النموذج: <code>{model}</code>\n"
        "المفتاح النشط: <code>{key_mask}</code>\n"
        "المفاتيح المفعّلة: <b>{active_keys}</b>\n"
        "════════════════════"
    )
    ai_test_result_fail = (
        "════════════════════\n"
        "🧪 <b>نتيجة اختبار Gemini</b>\n\n"
        "الحالة: 🔴 فشل الاتصال\n"
        "السبب: {error}\n"
        "════════════════════"
    )

    # V7 — link violation notification
    auto_ai_links = "🔗 <a href=\"tg://user?id={uid}\">{name}</a> — رابط مخالف (تم رصده بالذكاء الاصطناعي)."

    ai_sensitivity_title = (
        "════════════════════\n"
        "🎛️ <b>مستوى حساسية الذكاء الاصطناعي</b>\n\n"
        "منخفضة: يتصرف فقط عند تأكد عالٍ جداً (أقل عدد إجراءات).\n"
        "متوسطة: توازن بين الدقة والحساسية (موصى بها).\n"
        "عالية: يتصرف عند أدنى شك (أكثر عدد إجراءات، وقد يزيد الإنذارات الخاطئة).\n"
        "════════════════════"
    )
    ai_sensitivity_low    = "🟢 منخفضة"
    ai_sensitivity_medium = "🟡 متوسطة"
    ai_sensitivity_high   = "🔴 عالية"

    ai_status_title = (
        "════════════════════\n"
        "📊 <b>حالة نظام الذكاء الاصطناعي</b>\n\n"
        "المفاتيح المفعّلة: <b>{enabled_keys}</b> / {total_keys}\n"
        "الحالة العامة: {overall_status}\n"
        "════════════════════"
    )
    ai_status_ok       = "🟢 يعمل بشكل طبيعي"
    ai_status_no_keys  = "🔴 لا توجد مفاتيح Gemini مفعّلة — الذكاء الاصطناعي متوقف مؤقتاً"

    # ─── V6: Bot-owner Gemini key-manager commands ──────────────────────────────
    ai_admin_not_owner = "❌ هذا الأمر مخصص لمالك البوت فقط."
    ai_admin_addkey_usage = (
        "📝 <b>إضافة مفتاح Gemini API</b>\n\n"
        "الاستخدام: <code>/addaikey المفتاح [تسمية اختيارية]</code>\n\n"
        "⚠️ سيتم حذف رسالتك تلقائياً بعد الإضافة لحماية المفتاح."
    )
    ai_admin_key_added = "✅ تم إضافة مفتاح Gemini جديد (#{key_id}) بنجاح."
    ai_admin_key_added_dm_fallback = (
        "✅ تم إضافة مفتاح Gemini جديد (#{key_id}) بنجاح.\n"
        "⚠️ تعذّر حذف رسالتك التي تحتوي على المفتاح — يُفضّل حذفها يدوياً الآن."
    )
    ai_admin_no_keys = "📭 لا توجد أي مفاتيح Gemini مسجّلة بعد. أضف واحداً باستخدام <code>/addaikey</code>."
    ai_admin_keys_list_header = "🔑 <b>مفاتيح Gemini API</b>\n\n"
    ai_admin_key_row = (
        "#{id} — {status} | {health}\n"
        "🏷️ {label}\n"
        "🔒 {masked}\n"
        "📊 استخدام: {usage} | ✅ نجاح: {success} | ❌ فشل: {failure}\n"
        "────────────────────\n"
    )
    ai_admin_key_status_enabled  = "🟢 مفعّل"
    ai_admin_key_status_disabled = "🔴 معطّل"
    ai_admin_togglekey_usage = "الاستخدام: <code>/togglekey رقم_المفتاح</code>"
    ai_admin_key_not_found = "❌ لا يوجد مفتاح بهذا الرقم."
    ai_admin_key_enabled = "✅ تم تفعيل المفتاح #{key_id}."
    ai_admin_key_disabled = "🔴 تم تعطيل المفتاح #{key_id}."
    ai_admin_delkey_usage = "الاستخدام: <code>/delkey رقم_المفتاح</code>"
    ai_admin_key_deleted = "🗑️ تم حذف المفتاح #{key_id}."
    ai_admin_aistatus = (
        "📊 <b>حالة نظام الذكاء الاصطناعي (عام)</b>\n\n"
        "إجمالي المفاتيح: <b>{total}</b>\n"
        "المفاتيح المفعّلة: <b>{enabled}</b>\n"
    )

    # ─── V7.1: Gemini key-manager — inline wizard (bot-owner only) ──────────────
    btn_ai_key_manager = "🧠 إدارة مفاتيح Gemini"
    btn_ai_add_key     = "➕ إضافة مفتاح"
    btn_ai_del_key     = "❌ حذف مفتاح"
    btn_ai_count_only  = "📋 عرض عدد المفاتيح فقط"
    btn_confirm_delete = "❌ نعم، احذف"

    ai_setup_wizard_title = (
        "════════════════════\n"
        "🧠 <b>إعداد Gemini</b>\n\n"
        "لم يتم العثور على أي مفتاح Gemini.\n\n"
        "يرجى إضافة مفتاح API للبدء.\n"
        "════════════════════"
    )

    ai_setup_addkey_prompt = (
        "📝 أرسل الآن مفتاح Gemini API كرسالة نصية.\n\n"
        "⚠️ سيتم حذف رسالتك تلقائياً بعد الحفظ لحماية المفتاح."
    )
    ai_setup_addkey_invalid = "❌ هذا لا يبدو مفتاح API صالحاً. أرسل المفتاح فقط بدون أي نص إضافي."
    ai_setup_key_saved = "✅ تم حفظ مفتاح Gemini بنجاح."
    ai_setup_key_saved_dm_fallback = (
        "✅ تم حفظ مفتاح Gemini بنجاح.\n"
        "⚠️ تعذّر حذف رسالتك التي تحتوي على المفتاح — يُفضّل حذفها يدوياً الآن."
    )

    ai_setup_manager_title = (
        "════════════════════\n"
        "🧠 <b>إدارة مفاتيح Gemini</b>\n\n"
        "عدد المفاتيح: <b>{total}</b> (🟢 {enabled} مفعّل)\n\n"
        "{key_list}"
        "════════════════════"
    )
    ai_setup_key_line = "🔑 {label}\n{status} | {health} {masked}\n"
    ai_setup_key_label_default = "مفتاح #{id}"

    ai_setup_delmenu_title = "اختر مفتاحاً لحذفه:"
    ai_setup_delmenu_empty = "📭 لا توجد أي مفاتيح لحذفها."
    ai_setup_delconfirm_title = "⚠️ هل أنت متأكد من حذف المفتاح #{key_id}؟\nلا يمكن التراجع عن هذا الإجراء."
    ai_setup_key_deleted = "🗑️ تم حذف المفتاح بنجاح."

    ai_setup_count_only = "📋 عدد مفاتيح Gemini المسجّلة: <b>{total}</b>\n🟢 المفعّلة منها: <b>{enabled}</b>"

    ai_setup_not_owner = "❌ إدارة مفاتيح Gemini متاحة لمالك البوت فقط."

    # ─── V7.2: Live Gemini key validation (real test request before saving) ────
    ai_setup_verifying   = "⏳ جارٍ التحقق من المفتاح مع Gemini..."
    ai_key_verified_ok   = "✅ تم التحقق من المفتاح بنجاح."
    ai_key_invalid_gemini  = "❌ مفتاح Gemini غير صالح."
    # Specific validation failure reasons
    ai_key_err_api_invalid = "❌ مفتاح API غير صالح — تحقق من المفتاح في Google AI Studio."
    ai_key_err_quota       = "❌ تجاوز حصة API أو معدل الطلبات — انتظر قليلاً ثم حاول مرة أخرى."
    ai_key_err_permission  = "❌ المفتاح لا يملك الصلاحية — تحقق من إعدادات المشروع في Google Cloud."
    ai_key_err_model       = "❌ النموذج المطلوب غير متاح لهذا المفتاح — تحقق من مستوى الاشتراك."
    ai_key_err_network     = "❌ خطأ في الاتصال بـ Gemini — تحقق من الإنترنت وحاول مجدداً."
    ai_key_err_unknown     = "❌ فشل التحقق من المفتاح: {detail}"

    # ─── V7.2: AI profile screening (username/display-name/description) ────────
    auto_ai_profile_blocked = "🚫 تم إزالة عضو بسبب اسم مستخدم/اسم عرض مخالف (تم رصده بالذكاء الاصطناعي)."
    btn_ai_toggle_profiles = "{status} 👤 فحص الأسماء والملفات الشخصية"

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

    # ─── /start & Home ──────────────────────────────────────────────────────
    start_greeting = (
        "════════════════════\n"
        "👋 أهلاً، <b>{name}</b>!\n\n"
        "أنا <b>بوت الإدارة الاحترافي</b> 🤖\n"
        "اخترت خدمة قوية لإدارة مجموعاتك.\n\n"
        "{status}\n"
        "════════════════════"
    )
    start_has_groups = "📋 أنت تدير <b>{count}</b> مجموعة. اختر مجموعة للبدء:"
    start_no_groups = (
        "📌 لا توجد مجموعات مرتبطة بعد.\n\n"
        "أضفني إلى مجموعتك ومنحني صلاحيات <b>المشرف</b>،\n"
        "ثم اضغط على زر <b>➕ إدارة هذه المجموعة</b> داخل المجموعة."
    )

    home_title = (
        "════════════════════\n"
        "🏠 <b>الرئيسية</b>\n\n"
        "أهلاً، <b>{name}</b>!\n"
        "📋 المجموعة الحالية: <b>{group}</b>\n"
        "════════════════════"
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
        "════════════════════\n\n"
        "🎉 <b>تم تفعيل البوت بنجاح</b>\n\n"
        "شكرًا لإضافتي إلى هذه المجموعة.\n\n"
        "🛡️ أصبحت الآن جاهزًا لإدارة المجموعة وحمايتها.\n\n"
        "لإدارة هذه المجموعة اضغط على الزر الموجود بالأسفل.\n\n"
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
    mod_title = "🛡️ <b>الإشراف — {title}</b>"
    btn_filters = "🔍 الفلاتر ({active}/{total} مفعّل)"
    btn_actions = "⚡ إجراءات الفلاتر"
    btn_warn_limit = "⚠️ حد التحذيرات"

    filters_title = "🔍 <b>فلاتر الإشراف</b>\n\nاضغط لتفعيل/تعطيل الفلتر:"
    filter_actions_title = "⚡ <b>إجراءات الفلاتر</b>\n\nاختر فلتراً لضبط إجراءه:"
    filter_edit_action_title = "⚡ <b>إجراء: {name}</b>\n\nالحالي: <b>{action}</b>"

    # ─── V3 Protection Menu ──────────────────────────────────────────────────
    protection_title = (
        "═══════════════\n"
        "🛡️ <b>الحماية</b>\n\n"
        "{filters}"
        "═══════════════"
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
        "═══════════════\n"
        "⚙️ <b>الإعدادات</b>\n\n"
        "المجموعة: <b>{title}</b>\n\n"
        "اختر القسم الذي تريد تعديله:\n"
        "═══════════════"
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
        "════════════════════\n"
        "👤 <b>معلومات المستخدم</b>\n\n"
        "🆔 المعرّف: <code>{uid}</code>\n"
        "📛 الاسم: {name}\n"
        "🔗 اليوزر: {username}\n"
        "🏷️ الحالة: {status}\n"
        "⚠️ التحذيرات: <b>{warns}</b>\n"
        "📅 آخر تحذير: {last_warn}\n"
        "════════════════════"
    )

    # ─── Group events ─────────────────────────────────────────────────────────
    bot_joined_msg = (
        "👋 شكراً لإضافتي!\n\n"
        "أنا <b>بوت الإدارة الاحترافي</b> 🤖\n"
        "امنحني صلاحيات <b>المشرف</b> لأتمكن من حماية المجموعة.\n\n"
        "استخدم /start في المحادثة الخاصة لفتح لوحة التحكم."
    )

    # ─── Warnings History ─────────────────────────────────────────────────────
    warn_history_title = "📋 <b>سجل التحذيرات</b>\n\n"
    warn_history_none  = "لا توجد تحذيرات مسجّلة."
    warn_history_entry = "• <b>{date}</b> — {reason} (بواسطة {actor})\n"

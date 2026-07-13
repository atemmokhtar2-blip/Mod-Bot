"""
Arabic UI strings — single source of truth for every user-facing message.
Version 3: Professional UX & Security Update.

Usage:
    from bot.strings.ar import S
    await message.reply(S.cmd_ban_missing_target)

Future: swap this module with a different language module to support i18n.
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

    # V3: status circle indicators
    on  = "🟢"
    off = "🔴"

    # V3: security denial — shown to non-admins pressing management buttons
    no_permission_cb = "⛔ ليس لديك صلاحية لاستخدام أدوات الإدارة."

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

    # kept for backwards-compat with old callback paths
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

    # Filter labels (also used in protection menu)
    filter_bad_words      = "فلترة الكلمات المسيئة"
    filter_insults        = "فلترة الشتائم"
    filter_spam           = "فلترة السبام"
    filter_flood          = "فلترة الفيضان"
    filter_duplicates     = "فلترة التكرار"
    filter_advertisement  = "فلترة الإعلانات"
    filter_telegram_links = "فلترة الروابط"
    filter_external_links = "فلترة الروابط الخارجية"
    filter_excessive_emojis = "فلترة الرموز الزائدة"
    filter_repeated_chars = "فلترة الأحرف المكررة"
    filter_long_messages  = "فلترة الرسائل الطويلة"

    # Action labels
    action_ignore = "👁️ تجاهل"
    action_delete = "🗑️ حذف"
    action_warn   = "⚠️ تحذير"
    action_mute   = "🔇 كتم"
    action_kick   = "👢 طرد"
    action_ban    = "🚫 حظر"

    action_set_ok = "✅ تم ضبط إجراء <b>{filter}</b> على <b>{action}</b>."

    # ─── Settings ────────────────────────────────────────────────────────────
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

    welcome_edit_prompt = (
        "✏️ <b>تعديل رسالة الترحيب</b>\n\n"
        "الحالية:\n<i>{current}</i>\n\n"
        "أرسل النص الجديد.\n"
        "يمكنك استخدام: <code>{{first_name}}</code> <code>{{username}}</code> <code>{{group_name}}</code>"
    )
    welcome_updated = "✅ تم تحديث رسالة الترحيب!\n\nمعاينة:\n<i>{text}</i>"

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

    # V3: Confirmation prompts
    confirm_ban   = "⚠️ <b>تأكيد الحظر</b>\n\nهل أنت متأكد من حظر هذا المستخدم؟"
    confirm_mute  = "⚠️ <b>تأكيد الكتم</b>\n\nهل أنت متأكد من كتم هذا المستخدم لمدة ساعة؟"
    confirm_kick  = "⚠️ <b>تأكيد الطرد</b>\n\nهل أنت متأكد من طرد هذا المستخدم؟"
    confirm_reset = "⚠️ <b>تأكيد إعادة التحذيرات</b>\n\nهل أنت متأكد من إعادة تعيين جميع التحذيرات؟"
    confirm_yes   = "✅ نعم، تأكيد"
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

    # Event type labels
    log_user_joined     = "انضمام عضو"
    log_user_left       = "مغادرة عضو"
    log_user_banned     = "حظر مستخدم"
    log_user_unbanned   = "رفع حظر"
    log_user_muted      = "كتم مستخدم"
    log_user_unmuted    = "رفع كتم"
    log_user_warned     = "تحذير"
    log_message_deleted = "حذف رسالة"
    log_message_pinned  = "تثبيت رسالة"
    log_message_unpinned = "إلغاء تثبيت"
    log_settings_changed = "تغيير الإعدادات"
    log_filter_triggered = "تفعّل فلتر"
    log_bot_added       = "إضافة البوت"
    log_bot_removed     = "إزالة البوت"

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

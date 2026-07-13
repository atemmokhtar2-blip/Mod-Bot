"""
Arabic UI strings — single source of truth for every user-facing message.

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
    back = "🔙 رجوع"
    confirm = "✅ تأكيد"
    cancel = "❌ إلغاء"
    enabled = "✅ مفعّل"
    disabled = "❌ معطّل"
    success = "✅ تم بنجاح"
    error = "❌ حدث خطأ"
    not_found = "❌ لم يُعثر على العنصر."
    no_permission = "🚫 ليس لديك صلاحية لهذا الإجراء."
    unknown = "غير معروف"

    # ─── /start & Home ──────────────────────────────────────────────────────
    start_greeting = (
        "👋 أهلاً، <b>{name}</b>!\n\n"
        "أنا <b>بوت الإدارة الاحترافي</b> 🤖\n"
        "اخترت خدمة قوية لإدارة مجموعاتك.\n\n"
        "{status}"
    )
    start_has_groups = "أنت تدير <b>{count}</b> مجموعة. اختر مجموعة للبدء:"
    start_no_groups = (
        "لا توجد مجموعات بعد.\n"
        "أضفني إلى مجموعتك ومنحني صلاحيات <b>المشرف</b> للبدء."
    )

    home_title = "🏠 <b>الرئيسية</b>\n\nأهلاً، <b>{name}</b>!"

    # ─── Main Menu buttons ───────────────────────────────────────────────────
    btn_home = "🏠 الرئيسية"
    btn_groups = "👥 مجموعاتي"
    btn_protection = "🛡️ الحماية"
    btn_members = "👥 الأعضاء"
    btn_admins = "👮 المشرفون"
    btn_channels = "📢 القنوات"
    btn_settings = "⚙️ الإعدادات"
    btn_stats = "📊 الإحصائيات"
    btn_logs = "📜 السجل"
    btn_help = "❓ المساعدة"
    btn_back = "🔙 رجوع"

    # ─── Group panel ────────────────────────────────────────────────────────
    group_panel_title = "🏠 <b>{title}</b>\n\nاختر قسماً:"
    no_groups_yet = (
        "📋 لا توجد مجموعات مسجّلة بعد.\n\n"
        "أضفني إلى مجموعة ومنحني صلاحيات <b>المشرف</b>."
    )
    groups_title = "📋 <b>مجموعاتي</b>\n\nاختر مجموعة للإدارة:"

    btn_mod = "🛡️ الإشراف"
    btn_panel_members = "👥 الأعضاء"
    btn_panel_admins = "👮 المشرفون"
    btn_panel_settings = "⚙️ الإعدادات"
    btn_panel_stats = "📊 الإحصائيات"
    btn_panel_logs = "📜 السجل"
    btn_panel_back = "🔙 مجموعاتي"

    # ─── Moderation section ──────────────────────────────────────────────────
    mod_title = "🛡️ <b>الإشراف — {title}</b>"
    btn_filters = "🔍 الفلاتر ({active}/{total} مفعّل)"
    btn_actions = "⚡ إجراءات الفلاتر"
    btn_warn_limit = "⚠️ حد التحذيرات"

    filters_title = "🔍 <b>فلاتر الإشراف</b>\n\nاضغط لتفعيل/تعطيل الفلتر:"
    filter_actions_title = "⚡ <b>إجراءات الفلاتر</b>\n\nاختر فلتراً لضبط إجراءه:"
    filter_edit_action_title = "⚡ <b>إجراء: {name}</b>\n\nالحالي: <b>{action}</b>"

    # Filter labels
    filter_bad_words = "🤬 كلمات مسيئة"
    filter_insults = "😡 الإهانات"
    filter_spam = "📨 السبام"
    filter_flood = "🌊 الفيضان"
    filter_duplicates = "🔁 الرسائل المكررة"
    filter_advertisement = "📣 الإعلانات"
    filter_telegram_links = "🔗 روابط تيليغرام"
    filter_external_links = "🌐 الروابط الخارجية"
    filter_excessive_emojis = "😂 الرموز الزائدة"
    filter_repeated_chars = "🔤 الأحرف المكررة"
    filter_long_messages = "📜 الرسائل الطويلة"

    # Action labels
    action_ignore = "👁️ تجاهل"
    action_delete = "🗑️ حذف"
    action_warn = "⚠️ تحذير"
    action_mute = "🔇 كتم"
    action_kick = "👢 طرد"
    action_ban = "🚫 حظر"

    action_set_ok = "✅ تم ضبط إجراء <b>{filter}</b> على <b>{action}</b>."

    # ─── Settings ────────────────────────────────────────────────────────────
    settings_title = "⚙️ <b>الإعدادات — {title}</b>"

    btn_settings_protection = "🛡️ الحماية"
    btn_settings_punishments = "⚠️ العقوبات"
    btn_settings_welcome = "📝 الترحيب"
    btn_settings_permissions = "👮 الصلاحيات"
    btn_settings_notifications = "🔔 الإشعارات"
    btn_settings_stats_cfg = "📊 الإحصائيات"

    btn_welcome_toggle = "📝 الترحيب: {status}"
    btn_welcome_edit = "✏️ تعديل نص الترحيب"
    btn_logs_toggle = "📋 سجل الأحداث: {status}"
    btn_warn_limit_setting = "⚠️ حد التحذيرات"
    btn_punishment = "🔨 العقوبة التلقائية"

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
    punishment_ban = "🚫 حظر"
    punishment_set = "✅ تم ضبط العقوبة التلقائية على <b>{p}</b>."

    # ─── Members section ─────────────────────────────────────────────────────
    members_title = (
        "👥 <b>الأعضاء</b>\n\n"
        "استخدم الأوامر للإجراءات:\n"
        "/ban /mute /warn /info\n"
        "أو استخدم الأزرار أدناه:"
    )
    btn_member_ban = "🚫 حظر"
    btn_member_unban = "✅ رفع الحظر"
    btn_member_mute = "🔇 كتم ساعة"
    btn_member_unmute = "🔊 رفع الكتم"
    btn_member_warn = "⚠️ تحذير"
    btn_member_reset_warns = "🔄 إعادة التحذيرات"
    btn_member_history = "📋 سجل التحذيرات"

    member_banned = "✅ تم حظر العضو."
    member_ban_fail = "❌ تعذّر حظر العضو."
    member_unbanned = "✅ تم رفع الحظر."
    member_unban_fail = "❌ تعذّر رفع الحظر."
    member_muted = "✅ تم كتم العضو لمدة ساعة."
    member_mute_fail = "❌ تعذّر كتم العضو."
    member_unmuted = "✅ تم رفع الكتم."
    member_unmute_fail = "❌ تعذّر رفع الكتم."
    member_warned = "✅ تحذير {count}/{limit}."
    member_warned_punished = "✅ تحذير {count}/{limit} — تم تطبيق العقوبة التلقائية."
    member_warns_reset = "✅ تم إعادة تعيين التحذيرات."

    # ─── Admins section ─────────────────────────────────────────────────────
    admins_title = "👮 <b>المشرفون</b>"
    admins_no_extra = (
        "👮 لا يوجد مشرفون إضافيون مسجّلون في البوت.\n"
        "يمكن لمشرفي تيليغرام استخدام جميع الأوامر."
    )

    # ─── Channels ────────────────────────────────────────────────────────────
    channels_title = "📢 <b>القنوات</b>"
    channels_none = "📢 لا توجد قنوات مربوطة.\n\nأضفني إلى قناة كمشرف."
    btn_ch_post = "📝 إرسال رسالة"
    btn_ch_pin = "📌 تثبيت آخر تغريدة"
    btn_ch_back = "🔙 قنواتي"

    # ─── Statistics ──────────────────────────────────────────────────────────
    stats_title = "📊 <b>الإحصائيات — {title}</b>"
    stats_no_data = "📊 لا توجد إحصائيات مسجّلة بعد."
    stats_total_members = "👥 إجمالي الأعضاء"
    stats_messages = "💬 الرسائل اليوم"
    stats_deleted = "🗑️ الرسائل المحذوفة"
    stats_muted = "🔇 المكتومون اليوم"
    stats_banned = "🚫 المحظورون اليوم"
    stats_warned = "⚠️ المحذّرون اليوم"
    stats_last_7 = "📅 <b>آخر 7 أيام:</b>"

    # ─── Logs ─────────────────────────────────────────────────────────────────
    logs_title = "📜 <b>سجل الأحداث</b>"
    logs_none = "📜 لا توجد أحداث مسجّلة بعد."

    # Event type labels
    log_user_joined = "انضمام عضو"
    log_user_left = "مغادرة عضو"
    log_user_banned = "حظر مستخدم"
    log_user_unbanned = "رفع حظر"
    log_user_muted = "كتم مستخدم"
    log_user_unmuted = "رفع كتم"
    log_user_warned = "تحذير"
    log_message_deleted = "حذف رسالة"
    log_message_pinned = "تثبيت رسالة"
    log_message_unpinned = "إلغاء تثبيت"
    log_settings_changed = "تغيير الإعدادات"
    log_filter_triggered = "تفعّل فلتر"
    log_bot_added = "إضافة البوت"
    log_bot_removed = "إزالة البوت"

    # ─── Help ────────────────────────────────────────────────────────────────
    help_text = (
        "❓ <b>المساعدة</b>\n\n"
        "<b>البدء</b>\n"
        "1. أضف البوت إلى مجموعتك\n"
        "2. منحه صلاحيات <b>المشرف</b>\n"
        "3. استخدم /start في المحادثة الخاصة\n\n"
        "<b>أوامر المشرف (داخل المجموعة)</b>\n"
        "/ban — حظر مستخدم (رد أو @اسم)\n"
        "/unban — رفع الحظر\n"
        "/mute [مدة] — كتم (مثال: 2h أو 30m)\n"
        "/unmute — رفع الكتم\n"
        "/warn [سبب] — تحذير مستخدم\n"
        "/resetwarns — إعادة تعيين التحذيرات\n"
        "/del — حذف رسالة (بالرد عليها)\n"
        "/pin — تثبيت رسالة\n"
        "/unpin — إلغاء التثبيت\n"
        "/info — عرض معلومات المستخدم\n\n"
        "<b>لوحة التحكم</b>\n"
        "استخدم /start في المحادثة الخاصة لفتح لوحة التحكم."
    )

    # ─── Auto-moderation notifications ───────────────────────────────────────
    auto_flood = "🌊 <a href=\"tg://user?id={uid}\">{name}</a> — تم الكشف عن فيضان رسائل."
    auto_duplicate = "🔁 <a href=\"tg://user?id={uid}\">{name}</a> — رسالة مكررة."
    auto_telegram_link = "🔗 <a href=\"tg://user?id={uid}\">{name}</a> — روابط تيليغرام ممنوعة."
    auto_external_link = "🌐 <a href=\"tg://user?id={uid}\">{name}</a> — روابط خارجية ممنوعة."
    auto_advertisement = "📣 <a href=\"tg://user?id={uid}\">{name}</a> — إعلان غير مسموح."
    auto_emoji = "😂 <a href=\"tg://user?id={uid}\">{name}</a> — رموز تعبيرية زائدة."
    auto_repeated = "🔤 <a href=\"tg://user?id={uid}\">{name}</a> — أحرف مكررة."
    auto_long_msg = "📜 <a href=\"tg://user?id={uid}\">{name}</a> — الرسالة طويلة جداً."
    auto_bad_word = "🤬 <a href=\"tg://user?id={uid}\">{name}</a> — كلمة محظورة."
    auto_warn_notice = "⚠️ تحذير <b>{count}/{limit}</b> — {reason}"
    auto_punished = "⚠️ <a href=\"tg://user?id={uid}\">{name}</a> وصل لحد التحذيرات — تم تطبيق العقوبة التلقائية."
    auto_muted = "🔇 تم كتم <a href=\"tg://user?id={uid}\">{name}</a>."

    # ─── Admin command responses ──────────────────────────────────────────────
    cmd_need_target = "❌ قم بالرد على رسالة المستخدم أو أدخل معرّفه."
    cmd_ban_ok = "🚫 تم حظر {mention}{reason}."
    cmd_ban_fail = "❌ تعذّر الحظر. تحقق من صلاحياتي."
    cmd_unban_ok = "✅ تم رفع الحظر عن <b>{name}</b>."
    cmd_unban_fail = "❌ تعذّر رفع الحظر."
    cmd_mute_ok = "🔇 تم كتم {mention} لمدة <b>{duration}</b>{reason}."
    cmd_mute_fail = "❌ تعذّر الكتم. تحقق من صلاحياتي."
    cmd_unmute_ok = "🔊 تم رفع الكتم عن <b>{name}</b>."
    cmd_unmute_fail = "❌ تعذّر رفع الكتم."
    cmd_warn_ok = "⚠️ {mention} — تحذير <b>{count}/{limit}</b>.{reason}"
    cmd_warn_punished = "⚠️ {mention} — تحذير <b>{limit}/{limit}</b> وتم تطبيق العقوبة التلقائية.{reason}"
    cmd_reason_prefix = "\n📝 السبب: {reason}"
    cmd_resetwarns_ok = "🔄 تم إعادة تعيين التحذيرات لـ <b>{name}</b>."
    cmd_del_need_reply = "❌ قم بالرد على الرسالة التي تريد حذفها."
    cmd_del_fail = "❌ تعذّر حذف الرسالة."
    cmd_pin_need_reply = "❌ قم بالرد على الرسالة التي تريد تثبيتها."
    cmd_pin_fail = "❌ تعذّر التثبيت."
    cmd_unpin_need_reply = "❌ قم بالرد على الرسالة التي تريد إلغاء تثبيتها."
    cmd_unpin_fail = "❌ تعذّر إلغاء التثبيت."
    cmd_info_fail = "❌ تعذّر تحديد المستخدم."

    cmd_info_text = (
        "👤 <b>معلومات المستخدم</b>\n\n"
        "🆔 المعرّف: <code>{uid}</code>\n"
        "📛 الاسم: {name}\n"
        "🔗 اليوزر: {username}\n"
        "🏷️ الحالة: {status}\n"
        "⚠️ التحذيرات: <b>{warns}</b>\n"
        "📅 آخر تحذير: {last_warn}"
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
    warn_history_none = "لا توجد تحذيرات مسجّلة."
    warn_history_entry = "• <b>{date}</b> — {reason} (بواسطة {actor})\n"

from database import get_db
import os
import time
from functools import wraps
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters
)

from werkzeug.security import check_password_hash
from student import student_start, register_student_handlers,student_handler


# ======================================================
# إعدادات
# ======================================================


TOKEN = os.environ.get("TOKEN")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

LOGIN_USERNAME, LOGIN_PASSWORD = range(2)
CREATE_SUBJECT_NAME = 100

PAGE_SIZE = 8
RATE_LIMIT_SECONDS = 1.2


# ======================================================
# الاتصال بقاعدة البيانات
# ======================================================



# ======================================================
# Rate Limit
# ======================================================

def rate_limit(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        now = time.time()
        last = context.user_data.get("last_request", 0)

        if now - last < RATE_LIMIT_SECONDS:
            return

        context.user_data["last_request"] = now
        return await func(update, context)

    return wrapper


# ======================================================
# أدوات مساعدة
# ======================================================

def back_button():
    return [[InlineKeyboardButton("⬅ رجوع", callback_data="back")]]

def is_logged(update):
    user = get_logged_user_by_id(update.effective_user.id)
    return user is not None

def get_logged_user_by_id(telegram_id):
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE telegram_id=%s",
        (telegram_id,)
    ).fetchone()
    conn.close()
    return user

# ======================================================
# نظام التنقل الذكي (Stack)
# ======================================================

def init_stack(context):
    if "nav_stack" not in context.user_data:
        context.user_data["nav_stack"] = []


def push_stack(context, callback_data):
    init_stack(context)
    context.user_data["nav_stack"].append(callback_data)


def pop_stack(context):
    init_stack(context)
    if context.user_data["nav_stack"]:
        return context.user_data["nav_stack"].pop()
    return "main"
# ======================================================
# START (طلاب)
# ======================================================

@rate_limit
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await student_start(update, context, get_db)


# ======================================================
# LOGIN
# ======================================================

async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔐 أدخل اسم المستخدم:")
    return LOGIN_USERNAME


async def login_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["login_username"] = update.message.text.strip()
    await update.message.reply_text("🔑 أدخل كلمة المرور:")
    return LOGIN_PASSWORD


async def login_password(update: Update, context: ContextTypes.DEFAULT_TYPE):

    username = context.user_data.get("login_username")
    password = update.message.text.strip()

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE username=%s",
        (username,)
    ).fetchone()

    if not user:
        conn.close()
        await update.message.reply_text("❌ اسم المستخدم غير موجود.")
        return ConversationHandler.END

    if not check_password_hash(user["password"], password):
        conn.close()
        await update.message.reply_text("❌ كلمة المرور غير صحيحة.")
        return ConversationHandler.END

    conn.execute(
        "UPDATE users SET telegram_id=%s WHERE id=%s",
        (update.effective_user.id, user["id"])
    )
    conn.commit()
    conn.close()

    context.user_data["logged_in"] = True
    context.user_data["user_id"] = user["id"]

    await update.message.reply_text("✅ تم تسجيل الدخول بنجاح.")
    await show_admin_panel(update, context)

    return ConversationHandler.END


# ======================================================
# لوحة التحكم
# ======================================================

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("📎 رفع ملف", callback_data="upload_file")],
        [InlineKeyboardButton("➕ إنشاء مادة", callback_data="create_subject")],
        [InlineKeyboardButton("📚 موادي", callback_data="my_subjects")],
        [InlineKeyboardButton("🚪 تسجيل خروج", callback_data="logout")],
        [InlineKeyboardButton("⬅ رجوع للرئيسية", callback_data="student_main")]
    ]

    await update.message.reply_text(
        "🎛 لوحة التحكم:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ======================================================
# استقبال الملفات
# ======================================================

async def receive_file(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # 1️⃣ تأكد أن المستخدم مسجل دخول
    if not is_logged(update):
        return

    subject_id = context.user_data.get("upload_subject")

    # 2️⃣ تأكد أنه اختار مادة قبل إرسال الملف
    if not subject_id:
        await update.message.reply_text("⚠ اختر المادة أولاً من لوحة التحكم.")
        return

    user = get_logged_user_by_id(update.effective_user.id)
    if not user:
        return

    conn = get_db()

    # 3️⃣ تحقق أمني: هل يملك صلاحية الرفع لهذه المادة؟
    allowed = conn.execute("""
        SELECT s.id
        FROM subjects s
        JOIN levels l ON s.level_id = l.id
        JOIN user_permissions up ON up.level_id = l.id
        WHERE s.id=%s AND up.user_id=%s
    """, (subject_id, user["id"])).fetchone()

    if not allowed:
        conn.close()
        await update.message.reply_text("⛔ لا تملك صلاحية رفع ملفات لهذه المادة.")
        return

    # 4️⃣ تحديد نوع الملف المرسل
    file = (
        update.message.document
        or update.message.video
        or (update.message.photo[-1] if update.message.photo else None)
    )

    if not file:
        conn.close()
        return

    telegram_file = await context.bot.get_file(file.file_id)

    file_name = getattr(file, "file_name", f"{file.file_id}.dat")
    save_path = os.path.join(UPLOAD_FOLDER, file_name)

    # 5️⃣ تحميل الملف للسيرفر
    await telegram_file.download_to_drive(save_path)

    mime = getattr(file, "mime_type", "unknown")
    size = getattr(file, "file_size", 0)

    # 6️⃣ حفظه في قاعدة البيانات
    conn.execute("""
        INSERT INTO contents
        (title, description, type, file_path, file_size, mime_type, subject_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        file_name,
        "",
        "file",
        save_path,
        size,
        mime,
        subject_id
    ))

    conn.commit()
    conn.close()

    # 7️⃣ تنظيف الحالة
    context.user_data.pop("upload_subject", None)

    # 8️⃣ رسالة نجاح + أزرار
    await update.message.reply_text(
        "✅ تم رفع الملف بنجاح.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📎 رفع ملف آخر", callback_data="upload_file")],
            [InlineKeyboardButton("🎛 لوحة التحكم", callback_data="admin_panel")]
        ])
    )

async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # إذا المستخدم في وضع إنشاء مادة
    if context.user_data.get("creating_subject"):

        subject_name = update.message.text.strip()

        if not subject_name:
            await update.message.reply_text("❌ اسم المادة غير صالح.")
            return

        user = get_logged_user_by_id(update.effective_user.id)
        if not user:
            return

        conn = get_db()

        # هنا تحتاج تحدد المستوى الذي ستُنشأ فيه المادة
        # مؤقتاً سنأخذ أول مستوى مرتبط بالمستخدم
        level = conn.execute("""
            SELECT l.id
            FROM levels l
            JOIN user_permissions up ON up.level_id = l.id
            WHERE up.user_id=%s
            LIMIT 1
        """, (user["id"],)).fetchone()

        if not level:
            await update.message.reply_text("❌ لا يوجد مستوى مرتبط بك.")
            conn.close()
            return

        conn.execute("""
            INSERT INTO subjects (name, level_id)
            VALUES (%s, %s)
        """, (subject_name, level["id"]))

        conn.commit()
        conn.close()

        # إلغاء وضع الإنشاء
        context.user_data.pop("creating_subject")

        await update.message.reply_text(
            "✅ تم إنشاء المادة بنجاح.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎛 الرجوع للوحة التحكم", callback_data="admin_panel")]
            ])
        )

async def render_admin_panel(query, context):
    keyboard = [
        [InlineKeyboardButton("📎 رفع ملف", callback_data="upload_file")],
        [InlineKeyboardButton("📚 موادي", callback_data="my_subjects")],
        [InlineKeyboardButton("⬅ رجوع", callback_data="admin_panel")]
    ]

    await query.edit_message_text(
        "🎛 لوحة التحكم:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def render_my_subjects(query, context, conn):
    user = get_logged_user_by_id(query.from_user.id)

    subjects = conn.execute("""
        SELECT s.*
        FROM subjects s
        JOIN levels l ON s.level_id=l.id
        JOIN user_permissions up ON up.level_id=l.id
        WHERE up.user_id=%s
    """, (user["id"],)).fetchall()

    if not subjects:
        await query.edit_message_text("لا توجد مواد مرتبطة بك.")
        return

    keyboard = [
        [InlineKeyboardButton(s["name"], callback_data=f"subject_{s['id']}")]
        for s in subjects
    ]

    keyboard.append([InlineKeyboardButton("⬅ رجوع", callback_data="admin_panel")])

    await query.edit_message_text(
        "📚 موادك:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def render_subject_files(query, context, conn, subject_id):

    # 1️⃣ التأكد من أن المستخدم مسجل دخول
    telegram_id = query.from_user.id
    conn2 = get_db()
    user = conn2.execute("SELECT * FROM users WHERE telegram_id=%s",(telegram_id,)
    ).fetchone()
    conn2.close()
    if not user:
        await query.edit_message_text("❌ غير مصرح لك.")
        return

    # 2️⃣ تحقق أمني: هل هذه المادة ضمن صلاحيات المستخدم؟
    allowed = conn.execute("""
        SELECT s.id
        FROM subjects s
        JOIN levels l ON s.level_id = l.id
        JOIN user_permissions up ON up.level_id = l.id
        WHERE s.id=%s AND up.user_id=%s
    """, (subject_id, user["id"])).fetchone()

    if not allowed:
        await query.edit_message_text("⛔ لا تملك صلاحية الوصول لهذه المادة.")
        return

    # 3️⃣ جلب ملفات المادة
    contents = conn.execute(
        "SELECT * FROM contents WHERE subject_id=%s",
        (subject_id,)
    ).fetchall()

    # 4️⃣ إذا لا يوجد ملفات
    if not contents:
        keyboard = [
            [InlineKeyboardButton("⬅ رجوع", callback_data="my_subjects")]
        ]

        await query.edit_message_text(
            "📂 لا توجد ملفات داخل هذه المادة.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # 5️⃣ بناء قائمة الملفات
    keyboard = [
       [
        InlineKeyboardButton(f"📄 {c['title']}", callback_data=f"file_{c['id']}"),
        InlineKeyboardButton("🗑", callback_data=f"delete_file_{c['id']}")
       ]
        for c in contents
    ]

    # 6️⃣ زر الرجوع
    keyboard.append(
        [InlineKeyboardButton("⬅ رجوع", callback_data="my_subjects")]
    )

    await query.edit_message_text(
        "📂 ملفات المادة:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def render_upload_subjects(query, context, conn):
    """
    عرض المواد المسموح للمستخدم رفع ملفات لها
    """

    user = get_logged_user_by_id(query.from_user.id)

    if not user:
        await query.edit_message_text("❌ غير مصرح لك.")
        return

    subjects = conn.execute("""
        SELECT s.*
        FROM subjects s
        JOIN levels l ON s.level_id = l.id
        JOIN user_permissions up ON up.level_id = l.id
        WHERE up.user_id=%s
        ORDER BY s.name
    """, (user["id"],)).fetchall()

    if not subjects:
        await query.edit_message_text(
            "لا توجد مواد مرتبطة بك لرفع الملفات.",
            reply_markup=InlineKeyboardMarkup(back_button())
        )
        return

    # تخزين نقطة الرجوع
    context.user_data["nav_stack"].append("admin_panel")

    keyboard = [
        [
            InlineKeyboardButton(f"📘 {s['name']}",callback_data=f"select_upload_{s['id']}"),
            InlineKeyboardButton("🗑",callback_data=f"delete_subject_{s['id']}")
        ]
        for s in subjects
    ]

    keyboard += back_button()

    await query.edit_message_text(
        "اختر المادة التي تريد رفع ملف لها:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
# ======================================================
# معالج الأزرار
# ======================================================

@rate_limit
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    init_stack(context)

    query = update.callback_query
    await query.answer()
    data = query.data

    # إعطاء الأولوية للطالب
    handled = await student_handler(query, context, get_db)
    if handled:
        return

    conn = get_db()

    # ==================================================
    # لوحة التحكم
    # ==================================================
    if data == "admin_panel":

        context.user_data["nav_stack"] = ["admin_panel"]

        keyboard = [
            [InlineKeyboardButton("📎 رفع ملف", callback_data="upload_file")],
            [InlineKeyboardButton("➕ إنشاء مادة", callback_data="create_subject")],
            [InlineKeyboardButton("📚 موادي", callback_data="my_subjects")],
            [InlineKeyboardButton("🚪 تسجيل خروج", callback_data="logout")]
        ]

        await query.edit_message_text(
        "🎛 لوحة التحكم:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


    # ==================================================
    # عرض مواد المستخدم
    # ==================================================
    elif data == "my_subjects":

        user = get_logged_user_by_id(update.effective_user.id)
        if not user:
            await query.edit_message_text("❌ غير مصرح لك.")
            conn.close()
            return

        context.user_data["nav_stack"].append("admin_panel")

        subjects = conn.execute("""
            SELECT s.*
            FROM subjects s
            JOIN levels l ON s.level_id=l.id
            JOIN user_permissions up ON up.level_id=l.id
            WHERE up.user_id=%s
        """, (user["id"],)).fetchall()

        if not subjects:
            await query.edit_message_text("لا توجد مواد مرتبطة بك.",
                reply_markup=InlineKeyboardMarkup(back_button()))
            conn.close()
            return

        keyboard = [
            [InlineKeyboardButton(s["name"], callback_data=f"subject_{s['id']}")]
            for s in subjects
        ]

        keyboard += back_button()

        await query.edit_message_text(
            "📚 موادك:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


    # ==================================================
    # اختيار مادة لرفع ملف
    # ==================================================
    elif data == "upload_file":
        await render_upload_subjects(query, context, conn)

    # ==================================================
    # تحديد المادة قبل الرفع
    # ==================================================
    elif data.startswith("select_upload_"):

        subject_id = data.split("_")[2]
        context.user_data["upload_subject"] = subject_id
        context.user_data["nav_stack"].append("upload_file")

        await query.edit_message_text(
            "📎 أرسل الآن الملف.",
            reply_markup=InlineKeyboardMarkup(back_button())
        )


    # ==================================================
    # عرض ملفات مادة
    # ==================================================
    elif data.startswith("subject_"):
        subject_id = data.split("_")[1]
        context.user_data["nav_stack"].append("my_subjects")
        await render_subject_files(query, context, conn, subject_id)

    # ==================================================
    # إرسال ملف واحد
    # ==================================================
    elif data.startswith("file_"):

        content_id = data.split("_")[1]

        content = conn.execute(
            "SELECT * FROM contents WHERE id=%s",
            (content_id,)
        ).fetchone()

        if not content:
            await query.answer("الملف غير موجود", show_alert=True)
            conn.close()
            return

        context.user_data["nav_stack"].append(f"subject_{content['subject_id']}")

        file_path = content["file_path"]
        mime = content["mime_type"] or ""

        if not os.path.exists(file_path):
            await query.answer("الملف غير موجود على السيرفر", show_alert=True)
            conn.close()
            return

        await query.edit_message_text("📤 جاري إرسال الملف...")

        with open(file_path, "rb") as f:

            if mime.startswith("image"):
                await context.bot.send_photo(query.message.chat_id, f)

            elif mime.startswith("video"):
                await context.bot.send_video(query.message.chat_id, f)

            else:
                await context.bot.send_document(query.message.chat_id, f)

        await context.bot.send_message(
            query.message.chat_id,
            "⬅ رجوع",
            reply_markup=InlineKeyboardMarkup(back_button())
        )


    # ==================================================
    # زر الرجوع
    # ==================================================
    elif data == "back":

        stack = context.user_data.get("nav_stack", [])

        if not stack:
            await start(update, context)
            conn.close()
            return

        previous = stack.pop()

        if previous == "admin_panel":
            await render_admin_panel(query, context)

        elif previous == "my_subjects":
            await render_my_subjects(query, context, conn)

        elif previous.startswith("subject_"):
            subject_id = previous.split("_")[1]
            await render_subject_files(query, context, conn, subject_id)

        elif previous == "upload_file":
            await render_upload_subjects(query, context, conn)

        else:
            await start(update, context)

        conn.close()
        return
        
       


    # ==================================================
    # تسجيل خروج
    # ==================================================
    elif data == "logout":

        telegram_id = update.effective_user.id
        conn.execute(
            "UPDATE users SET telegram_id=NULL WHERE telegram_id=%s",
            (telegram_id,)
        )
        conn.commit()

        context.user_data.clear()

        await query.edit_message_text("🚪 تم تسجيل الخروج بنجاح.")
    
    # ==================================================
# الرجوع للرئيسية
# ==================================================
    elif data == "main":

        context.user_data["nav_stack"] = []

        colleges = conn.execute("SELECT * FROM colleges").fetchall()

        keyboard = [
            [InlineKeyboardButton(c["name"], callback_data=f"college_{c['id']}")]
            for c in colleges
        ]

        await query.edit_message_text(
            "📚 اختر الكلية:",
           reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data == "create_subject":

        await query.edit_message_text("✏ أرسل اسم المادة الجديدة:",reply_markup=InlineKeyboardMarkup(back_button()))

        context.user_data["creating_subject"] = True
        conn.close()
        return

    elif data.startswith("delete_file_"):

        content_id = data.split("_")[2]

        content = conn.execute("SELECT * FROM contents WHERE id=%s",(content_id,)).fetchone()

        if not content:
            await query.answer("الملف غير موجود", show_alert=True)
            return

        file_path = content["file_path"]

        if os.path.exists(file_path):
            os.remove(file_path)

        conn.execute("DELETE FROM contents WHERE id=%s", (content_id,))
        conn.commit()

        await query.edit_message_text("✅ تم حذف الملف بنجاح.",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅ رجوع", callback_data=f"subject_{content['subject_id']}")]]))



    elif data.startswith("delete_subject_"):

        subject_id = data.split("_")[2]

        files = conn.execute("SELECT * FROM contents WHERE subject_id=%s",(subject_id,) ).fetchall()

        for f in files:
            if os.path.exists(f["file_path"]):
                os.remove(f["file_path"])

        conn.execute("DELETE FROM contents WHERE subject_id=%s", (subject_id,))
        conn.execute("DELETE FROM subjects WHERE id=%s", (subject_id,))
        conn.commit()

        await query.edit_message_text("✅ تم حذف المادة بالكامل.",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅ الرجوع لموادي", callback_data="my_subjects")]]))

    conn.close()



# ======================================================
# تشغيل البوت
# ======================================================

app = (
    ApplicationBuilder()
    .token(TOKEN)
    .connect_timeout(30)
    .read_timeout(60)
    .write_timeout(60)
    .pool_timeout(30)
    .build()
)

login_conv = ConversationHandler(
    entry_points=[CommandHandler("login", login_command)],
    states={
        LOGIN_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_username)],
        LOGIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_password)],
    },
    fallbacks=[],
)

app.add_handler(CommandHandler("start", start))
app.add_handler(login_conv)
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO, receive_file))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_text))
app.add_handler(CommandHandler("student", lambda u, c: student_start(u, c, get_db)))
register_student_handlers(app, get_db)
def start_bot():
    print("Bot started...")
    app.run_polling()
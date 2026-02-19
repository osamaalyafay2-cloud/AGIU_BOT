from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
import os

# ======================================================
# أدوات مساعدة
# ======================================================

async def safe_edit(query, text, keyboard):
    try:
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        pass


# ======================================================
# STUDENT NAVIGATION STACK
# ======================================================

def student_init_stack(context):
    if "student_stack" not in context.user_data:
        context.user_data["student_stack"] = []

def student_push(context, data):
    student_init_stack(context)
    context.user_data["student_stack"].append(data)

def student_reset(context):
    context.user_data["student_stack"] = ["student_main"]

# ======================================================
# START STUDENT
# ======================================================

async def student_start(update, context, get_db):

    student_reset(context)

    conn = get_db()
    colleges = conn.execute("SELECT * FROM colleges").fetchall()
    conn.close()

    keyboard = [
        [InlineKeyboardButton(c["name"], callback_data=f"student_college_{c['id']}")]
        for c in colleges
    ]

    keyboard.append(
        [InlineKeyboardButton("ℹ حول البوت", callback_data="student_about")]
    )

    await update.message.reply_text(
        "🎓 اختر الكلية:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ======================================================
# MAIN HANDLER
# ======================================================

async def student_handler(query, context, get_db):

    await query.answer()
    data = query.data
    conn = get_db()

    # ==================================================
    # رجوع
    # ==================================================
    if data == "student_back":

        stack = context.user_data.get("student_stack", [])

        if len(stack) <= 1:
            student_reset(context)
            data = "student_main"
        else:
            stack.pop()
            data = stack[-1]

    # ==================================================
    # الصفحة الرئيسية
    # ==================================================
    if data == "student_main":

        student_reset(context)

        colleges = conn.execute("SELECT * FROM colleges").fetchall()

        keyboard = [
            [InlineKeyboardButton(c["name"], callback_data=f"student_college_{c['id']}")]
            for c in colleges
        ]

        keyboard.append(
            [InlineKeyboardButton("ℹ حول البوت", callback_data="student_about")]
        )

        await safe_edit(query, "🎓 اختر الكلية:", keyboard)
        conn.close()
        return True

    # ==================================================
    # حول البوت
    # ==================================================
    if data == "student_about":

        keyboard = [[InlineKeyboardButton("⬅ رجوع", callback_data="student_back")]]

        await safe_edit(
            query,
            "📚 نظام أرشفة جامعي\n\n"
            "يسمح لك باختيار الكلية ثم القسم ثم السنة والمستوى "
            "ثم المادة وتحميل الملفات بسهولة.\n\n"
            "تصميم وبرمجة: Eng.Ossama Omar",
            keyboard
        )

        conn.close()
        return True

    # ==================================================
    # الأقسام
    # ==================================================
    if data.startswith("student_college_"):

        student_push(context, data)

        college_id = data.split("_")[2]

        departments = conn.execute(
            "SELECT * FROM departments WHERE college_id=?",
            (college_id,)
        ).fetchall()

        keyboard = [
            [InlineKeyboardButton(d["name"], callback_data=f"student_department_{d['id']}")]
            for d in departments
        ]

        keyboard.append([InlineKeyboardButton("⬅ رجوع", callback_data="student_back")])

        await safe_edit(query, "🏛 اختر القسم:", keyboard)
        conn.close()
        return True

    # ==================================================
    # السنوات
    # ==================================================
    if data.startswith("student_department_"):

        student_push(context, data)

        department_id = data.split("_")[2]

        years = conn.execute(
            "SELECT * FROM years WHERE department_id=?",
            (department_id,)
        ).fetchall()

        keyboard = [
            [InlineKeyboardButton(y["name"], callback_data=f"student_year_{y['id']}")]
            for y in years
        ]

        keyboard.append([InlineKeyboardButton("⬅ رجوع", callback_data="student_back")])

        await safe_edit(query, "📅 اختر السنة:", keyboard)
        conn.close()
        return True

    # ==================================================
    # المستويات
    # ==================================================
    if data.startswith("student_year_"):

        student_push(context, data)

        year_id = data.split("_")[2]

        levels = conn.execute(
            "SELECT * FROM levels WHERE year_id=?",
            (year_id,)
        ).fetchall()

        keyboard = [
            [InlineKeyboardButton(l["name"], callback_data=f"student_level_{l['id']}")]
            for l in levels
        ]

        keyboard.append([InlineKeyboardButton("⬅ رجوع", callback_data="student_back")])

        await safe_edit(query, "📘 اختر المستوى:", keyboard)
        conn.close()
        return True

    # ==================================================
    # المواد
    # ==================================================
    if data.startswith("student_level_"):

        student_push(context, data)

        level_id = data.split("_")[2]

        subjects = conn.execute(
            "SELECT * FROM subjects WHERE level_id=?",
            (level_id,)
        ).fetchall()

        keyboard = [
            [InlineKeyboardButton(s["name"], callback_data=f"student_subject_{s['id']}")]
            for s in subjects
        ]

        keyboard.append([InlineKeyboardButton("⬅ رجوع", callback_data="student_back")])

        await safe_edit(query, "📚 اختر المادة:", keyboard)
        conn.close()
        return True

    # ==================================================
    # الملفات
    # ==================================================
    if data.startswith("student_subject_"):

        student_push(context, data)

        subject_id = data.split("_")[2]

        contents = conn.execute(
            "SELECT * FROM contents WHERE subject_id=?",
            (subject_id,)
        ).fetchall()

        if not contents:
            keyboard = [[InlineKeyboardButton("⬅ رجوع", callback_data="student_back")]]
            await safe_edit(query, "لا توجد ملفات لهذه المادة.", keyboard)
            conn.close()
            return True

        keyboard = [
            [InlineKeyboardButton(f"📄 {c['title']}", callback_data=f"student_file_{c['id']}")]
            for c in contents
        ]

        keyboard.append([InlineKeyboardButton("⬅ رجوع", callback_data="student_back")])

        await safe_edit(query, "📂 اختر الملف:", keyboard)
        conn.close()
        return True

    # ==================================================
    # تحميل ملف
    # ==================================================
    if data.startswith("student_file_"):

        content_id = data.split("_")[2]

        content = conn.execute(
            "SELECT * FROM contents WHERE id=?",
            (content_id,)
        ).fetchone()

        if not content:
            await query.answer("الملف غير موجود", show_alert=True)
            conn.close()
            return True

        file_path = content["file_path"]

        if not file_path or not os.path.exists(file_path):
            await query.answer("الملف غير موجود على السيرفر", show_alert=True)
            conn.close()
            return True

        await safe_edit(query, "📤 جاري إرسال الملف...", [])

        with open(file_path, "rb") as f:
            await context.bot.send_document(query.message.chat_id, f)

        await context.bot.send_message(
            query.message.chat_id,
            "⬅ رجوع",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅ رجوع", callback_data="student_back")]]
            )
        )

        conn.close()
        return True

    conn.close()
    return False


# ======================================================
# REGISTER HANDLER
# ======================================================

def register_student_handlers(app, get_db):

    app.add_handler(
        CallbackQueryHandler(
            lambda update, context: student_handler(update.callback_query, context, get_db),
            pattern="^student_"
        )
    )
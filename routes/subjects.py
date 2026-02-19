from flask import Blueprint, request, redirect, session
from database import get_db
from routes.shared import render

subjects_bp = Blueprint("subjects", __name__)

# ======================================================
# دالة مساعدة لفحص صلاحية المستوى
# ======================================================
def has_level_access(conn, level_id):

    # المشرف العام لديه صلاحية كاملة
    if session.get("role") == "super_admin":
        return True

    allowed = conn.execute("""
        SELECT 1 FROM user_permissions
        WHERE user_id=? AND level_id=?
    """, (session.get("user_id"), level_id)).fetchone()

    return allowed is not None


# ======================================================
# عرض مواد مستوى
# ======================================================
@subjects_bp.route("/level/<int:id>")
def view_level(id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    level = conn.execute(
        "SELECT * FROM levels WHERE id=?",
        (id,)
    ).fetchone()

    if not level:
        conn.close()
        return "العنصر غير موجود"

    # 🔒 منع الدخول المباشر لمستوى خارج الصلاحية
    if not has_level_access(conn, id):
        conn.close()
        return "غير مصرح لك"

    subjects = conn.execute(
        "SELECT * FROM subjects WHERE level_id=?",
        (id,)
    ).fetchall()

    conn.close()

    body = f"""
    <a class="btn open" href="/year/{level['year_id']}">⬅ رجوع</a>
    <a class="btn add" href="/add_subject/{id}">➕ إضافة مادة</a>
    <hr>
    """

    for s in subjects:
        body += f"""
        <div class="card">
        📖 {s['name']}
        <br><br>
        <a class="btn open" href="/subject/{s['id']}">فتح</a>
        <a class="btn edit" href="/edit_subject/{s['id']}">تعديل</a>
        <form method="post" action="/delete_subject/{s['id']}" style="display:inline;">
            <button class="btn delete"
            onclick="return confirm('هل أنت متأكد من الحذف؟')">
            حذف
            </button>
        </form>
        </div>
        """

    return render(level["name"], body)


# ======================================================
# إضافة مادة
# ======================================================
@subjects_bp.route("/add_subject/<int:id>", methods=["GET", "POST"])
def add_subject(id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    level = conn.execute(
        "SELECT * FROM levels WHERE id=?",
        (id,)
    ).fetchone()

    if not level:
        conn.close()
        return "العنصر غير موجود"

    # 🔐 فحص الصلاحية
    if not has_level_access(conn, id):
        conn.close()
        return "غير مصرح لك"

    if request.method == "POST":

        name = request.form.get("name", "").strip()

        if not name:
            conn.close()
            return "يجب إدخال اسم المادة"

        conn.execute(
            "INSERT INTO subjects(name, level_id) VALUES(?,?)",
            (name, id)
        )

        conn.commit()
        conn.close()

        return redirect(f"/level/{id}")

    conn.close()

    return render("إضافة مادة", f"""
    <a class="btn open" href="/level/{id}">⬅ رجوع</a>
    <form method="post">
    الاسم:
    <input name="name" required>
    <button class="btn add">حفظ</button>
    </form>
    """)


# ======================================================
# تعديل مادة
# ======================================================
@subjects_bp.route("/edit_subject/<int:id>", methods=["GET", "POST"])
def edit_subject(id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    subject = conn.execute(
        "SELECT * FROM subjects WHERE id=?",
        (id,)
    ).fetchone()

    if not subject:
        conn.close()
        return "العنصر غير موجود"

    # 🔐 فحص الصلاحية بناءً على مستوى المادة
    if not has_level_access(conn, subject["level_id"]):
        conn.close()
        return "غير مصرح لك"

    if request.method == "POST":

        name = request.form.get("name", "").strip()

        if not name:
            conn.close()
            return "يجب إدخال اسم المادة"

        conn.execute(
            "UPDATE subjects SET name=? WHERE id=?",
            (name, id)
        )

        conn.commit()
        conn.close()

        return redirect(f"/level/{subject['level_id']}")

    conn.close()

    return render("تعديل مادة", f"""
    <form method="post">
    الاسم:
    <input name="name" value="{subject['name']}" required>
    <button class="btn edit">تحديث</button>
    </form>
    """)


# ======================================================
# حذف مادة
# ======================================================
@subjects_bp.route("/delete_subject/<int:id>", methods=["POST"])
def delete_subject(id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    subject = conn.execute(
        "SELECT * FROM subjects WHERE id=?",
        (id,)
    ).fetchone()

    if not subject:
        conn.close()
        return "العنصر غير موجود"

    # 🔐 فحص الصلاحية
    if not has_level_access(conn, subject["level_id"]):
        conn.close()
        return "غير مصرح لك"

    conn.execute(
        "DELETE FROM subjects WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(f"/level/{subject['level_id']}")
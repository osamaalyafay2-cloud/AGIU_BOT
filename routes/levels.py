from flask import Blueprint, request, redirect, session
from database import get_db
from routes.shared import render

levels_bp = Blueprint("levels", __name__)

# ======================================================
# دالة فحص صلاحية العام
# ======================================================
def has_year_access(conn, year_id):

    if session.get("role") == "super_admin":
        return True

    allowed = conn.execute("""
        SELECT 1
        FROM user_permissions
        WHERE user_id=%s AND year_id=%s
    """, (session.get("user_id"), year_id)).fetchone()

    return allowed is not None


# ======================================================
# عرض مستويات عام
# ======================================================
@levels_bp.route("/year/<int:id>")
def view_year(id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    year = conn.execute(
        "SELECT * FROM years WHERE id=%s",
        (id,)
    ).fetchone()

    if not year:
        conn.close()
        return "العنصر غير موجود"

    # 🔒 منع الدخول لعام خارج النطاق
    if not has_year_access(conn, id):
        conn.close()
        return "غير مصرح لك"

    # 👑 المشرف يرى كل المستويات
    if session["role"] == "super_admin":
        levels = conn.execute(
            "SELECT * FROM levels WHERE year_id=%s",
            (id,)
        ).fetchall()
    else:
        # 👤 المستخدم يرى فقط مستوياته
        levels = conn.execute("""
            SELECT l.*
            FROM levels l
            JOIN user_permissions up ON up.level_id = l.id
            WHERE l.year_id=%s AND up.user_id=%s
        """, (id, session["user_id"])).fetchall()

    conn.close()

    body = f"""
    <a class="btn open" href="/department/{year['department_id']}">⬅ رجوع</a>
    """

    # إضافة مستوى فقط للمشرف
    if session["role"] == "super_admin":
        body += f"""
        <a class="btn add" href="/add_level/{id}">➕ إضافة مستوى</a>
        """

    body += "<hr>"

    for l in levels:
        body += f"""
        <div class="card">
        📚 {l['name']}
        <br><br>
        <a class="btn open" href="/level/{l['id']}">فتح</a>
        """

        if session["role"] == "super_admin":
            body += f"""
            <a class="btn edit" href="/edit_level/{l['id']}">تعديل</a>
            <form method="post" action="/delete_level/{l['id']}" style="display:inline;">
                <button class="btn delete"
                onclick="return confirm('هل أنت متأكد؟')">
                حذف
                </button>
            </form>
            """

        body += "</div>"

    return render(year["name"], body)


# ======================================================
# إضافة مستوى (فقط super_admin)
# ======================================================
@levels_bp.route("/add_level/<int:id>", methods=["GET", "POST"])
def add_level(id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "super_admin":
        return "غير مصرح لك"

    conn = get_db()

    year = conn.execute(
        "SELECT * FROM years WHERE id=%s",
        (id,)
    ).fetchone()

    if not year:
        conn.close()
        return "العنصر غير موجود"

    if request.method == "POST":
        conn.execute(
            "INSERT INTO levels(name, year_id) VALUES(%s,%s)",
            (request.form["name"], id)
        )
        conn.commit()
        conn.close()
        return redirect(f"/year/{id}")

    conn.close()

    return render("إضافة مستوى", f"""
    <a class="btn open" href="/year/{id}">⬅ رجوع</a>
    <form method="post">
    الاسم:
    <input name="name" required>
    <button class="btn add">حفظ</button>
    </form>
    """)


# ======================================================
# تعديل مستوى (فقط super_admin)
# ======================================================
@levels_bp.route("/edit_level/<int:id>", methods=["GET", "POST"])
def edit_level(id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "super_admin":
        return "غير مصرح لك"

    conn = get_db()

    level = conn.execute(
        "SELECT * FROM levels WHERE id=%s",
        (id,)
    ).fetchone()

    if not level:
        conn.close()
        return "العنصر غير موجود"

    if request.method == "POST":
        conn.execute(
            "UPDATE levels SET name=%s WHERE id=%s",
            (request.form["name"], id)
        )
        conn.commit()
        conn.close()
        return redirect(f"/year/{level['year_id']}")

    conn.close()

    return render("تعديل مستوى", f"""
    <form method="post">
    الاسم:
    <input name="name" value="{level['name']}" required>
    <button class="btn edit">تحديث</button>
    </form>
    """)


# ======================================================
# حذف مستوى (فقط super_admin)
# ======================================================
@levels_bp.route("/delete_level/<int:id>", methods=["POST"])
def delete_level(id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "super_admin":
        return "غير مصرح لك"

    conn = get_db()

    level = conn.execute(
        "SELECT * FROM levels WHERE id=%s",
        (id,)
    ).fetchone()

    if not level:
        conn.close()
        return "العنصر غير موجود"

    conn.execute("DELETE FROM levels WHERE id=%s", (id,))
    conn.commit()
    conn.close()

    return redirect(f"/year/{level['year_id']}")


# ======================================================
# عرض مواد مستوى
# ======================================================
@levels_bp.route("/level/<int:id>")
def view_level(id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    level = conn.execute(
        "SELECT * FROM levels WHERE id=%s",
        (id,)
    ).fetchone()

    if not level:
        conn.close()
        return "العنصر غير موجود"

    # 🔒 منع الدخول لمستوى خارج النطاق
    if session["role"] != "super_admin":
        allowed = conn.execute("""
            SELECT 1
            FROM user_permissions
            WHERE user_id=%s AND level_id=%s
        """, (session["user_id"], id)).fetchone()

        if not allowed:
            conn.close()
            return "غير مصرح لك"

    subjects = conn.execute(
        "SELECT * FROM subjects WHERE level_id=%s",
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
            onclick="return confirm('هل أنت متأكد؟')">
            حذف
            </button>
        </form>
        </div>
        """

    return render(level["name"], body)
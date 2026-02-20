from flask import Blueprint, request, redirect, session
from database import get_db
from routes.shared import render

levels_bp = Blueprint("levels", __name__)

# ======================================================
# دالة فحص صلاحية العام
# ======================================================

def has_year_access(db, year_id):

    if session.get("role") == "super_admin":
        return True

    allowed = db.execute("""
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

    db = get_db()

    year = db.execute(
        "SELECT * FROM years WHERE id=%s",
        (id,)
    ).fetchone()

    if not year:
        db.close()
        return "العنصر غير موجود"

    if not has_year_access(db, id):
        db.close()
        return "غير مصرح لك"

    if session["role"] == "super_admin":
        levels = db.execute(
            "SELECT * FROM levels WHERE year_id=%s",
            (id,)
        ).fetchall()
    else:
        levels = db.execute("""
            SELECT l.*
            FROM levels l
            JOIN user_permissions up ON up.level_id = l.id
            WHERE l.year_id=%s AND up.user_id=%s
        """, (id, session["user_id"])).fetchall()

    db.close()

    body = f"""
    <a class="btn open" href="/department/{year['department_id']}">⬅ رجوع</a>
    """

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
# إضافة مستوى
# ======================================================

@levels_bp.route("/add_level/<int:id>", methods=["GET", "POST"])
def add_level(id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "super_admin":
        return "غير مصرح لك"

    db = get_db()

    year = db.execute(
        "SELECT * FROM years WHERE id=%s",
        (id,)
    ).fetchone()

    if not year:
        db.close()
        return "العنصر غير موجود"

    if request.method == "POST":
        db.execute(
            "INSERT INTO levels(name, year_id) VALUES(%s,%s)",
            (request.form["name"], id)
        )
        db.commit()
        db.close()
        return redirect(f"/year/{id}")

    db.close()

    return render("إضافة مستوى", f"""
    <a class="btn open" href="/year/{id}">⬅ رجوع</a>
    <form method="post">
    الاسم:
    <input name="name" required>
    <button class="btn add">حفظ</button>
    </form>
    """)


# ======================================================
# تعديل مستوى
# ======================================================

@levels_bp.route("/edit_level/<int:id>", methods=["GET", "POST"])
def edit_level(id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "super_admin":
        return "غير مصرح لك"

    db = get_db()

    level = db.execute(
        "SELECT * FROM levels WHERE id=%s",
        (id,)
    ).fetchone()

    if not level:
        db.close()
        return "العنصر غير موجود"

    if request.method == "POST":
        db.execute(
            "UPDATE levels SET name=%s WHERE id=%s",
            (request.form["name"], id)
        )
        db.commit()
        db.close()
        return redirect(f"/year/{level['year_id']}")

    db.close()

    return render("تعديل مستوى", f"""
    <form method="post">
    الاسم:
    <input name="name" value="{level['name']}" required>
    <button class="btn edit">تحديث</button>
    </form>
    """)


# ======================================================
# حذف مستوى
# ======================================================

@levels_bp.route("/delete_level/<int:id>", methods=["POST"])
def delete_level(id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "super_admin":
        return "غير مصرح لك"

    db = get_db()

    level = db.execute(
        "SELECT * FROM levels WHERE id=%s",
        (id,)
    ).fetchone()

    if not level:
        db.close()
        return "العنصر غير موجود"

    db.execute("DELETE FROM levels WHERE id=%s", (id,))
    db.commit()
    db.close()

    return redirect(f"/year/{level['year_id']}")


# ======================================================
# عرض مواد مستوى
# ======================================================

@levels_bp.route("/level/<int:id>")
def view_level(id):

    if "user_id" not in session:
        return redirect("/login")

    db = get_db()

    level = db.execute(
        "SELECT * FROM levels WHERE id=%s",
        (id,)
    ).fetchone()

    if not level:
        db.close()
        return "العنصر غير موجود"

    if session["role"] != "super_admin":
        allowed = db.execute("""
            SELECT 1
            FROM user_permissions
            WHERE user_id=%s AND level_id=%s
        """, (session["user_id"], id)).fetchone()

        if not allowed:
            db.close()
            return "غير مصرح لك"

    subjects = db.execute(
        "SELECT * FROM subjects WHERE level_id=%s",
        (id,)
    ).fetchall()

    db.close()

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
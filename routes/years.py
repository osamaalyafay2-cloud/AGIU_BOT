from flask import Blueprint, request, redirect, session
from database import get_db
from routes.shared import render

years_bp = Blueprint("years", __name__)

# ======================================================
# أدوات فحص الصلاحيات
# ======================================================

def is_admin():
    return session.get("role") == "super_admin"


def has_department_access(db, department_id):

    if is_admin():
        return True

    allowed = db.execute("""
        SELECT 1
        FROM user_permissions
        WHERE user_id=%s AND department_id=%s
    """, (session.get("user_id"), department_id)).fetchone()

    return allowed is not None


def has_year_access(db, year_id):

    if is_admin():
        return True

    allowed = db.execute("""
        SELECT 1
        FROM user_permissions
        WHERE user_id=%s AND year_id=%s
    """, (session.get("user_id"), year_id)).fetchone()

    return allowed is not None


# ======================================================
# عرض أعوام قسم
# ======================================================

@years_bp.route("/department/<int:id>")
def view_department(id):

    if "user_id" not in session:
        return redirect("/login")

    db = get_db()

    department = db.execute(
        "SELECT * FROM departments WHERE id=%s",
        (id,)
    ).fetchone()

    if not department:
        db.close()
        return "العنصر غير موجود"

    if not has_department_access(db, id):
        db.close()
        return "غير مصرح لك"

    if is_admin():
        years = db.execute(
            "SELECT * FROM years WHERE department_id=%s",
            (id,)
        ).fetchall()
    else:
        years = db.execute("""
            SELECT DISTINCT y.*
            FROM years y
            JOIN user_permissions up ON up.year_id = y.id
            WHERE y.department_id=%s AND up.user_id=%s
        """, (id, session["user_id"])).fetchall()

    db.close()

    body = f"""
    <a class="btn open" href="/college/{department['college_id']}">⬅ رجوع</a>
    """

    if is_admin():
        body += f"""
        <a class="btn add" href="/add_year/{id}">➕ إضافة عام</a>
        """

    body += "<hr>"

    for y in years:
        body += f"""
        <div class="card">
        📅 {y['name']}
        <br><br>
        <a class="btn open" href="/year/{y['id']}">فتح</a>
        """

        if is_admin():
            body += f"""
            <a class="btn edit" href="/edit_year/{y['id']}">تعديل</a>
            <form method="post" action="/delete_year/{y['id']}" style="display:inline;">
                <button class="btn delete"
                onclick="return confirm('هل أنت متأكد من حذف هذا العام؟')">
                حذف
                </button>
            </form>
            """

        body += "</div>"

    return render(department["name"], body)


# ======================================================
# عرض مستويات عام
# ======================================================

@years_bp.route("/year/<int:id>")
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

    if is_admin():
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

    if is_admin():
        body += f"""
        <a class="btn add" href="/add_level/{id}">➕ إضافة مستوى</a>
        <a class="btn edit" href="/edit_year/{year['id']}">✏ تعديل العام</a>
        <form method="post" action="/delete_year/{year['id']}" style="display:inline;">
            <button class="btn delete"
            onclick="return confirm('هل أنت متأكد من حذف هذا العام؟')">
            حذف العام
            </button>
        </form>
        """

    body += "<hr>"

    for l in levels:
        body += f"""
        <div class="card">
        📚 {l['name']}
        <br><br>
        <a class="btn open" href="/level/{l['id']}">فتح</a>
        """

        if is_admin():
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
# إضافة عام
# ======================================================

@years_bp.route("/add_year/<int:id>", methods=["GET", "POST"])
def add_year(id):

    if "user_id" not in session:
        return redirect("/login")

    if not is_admin():
        return "غير مصرح لك"

    if request.method == "POST":

        name = request.form.get("name", "").strip()

        if not name:
            return "يجب إدخال اسم العام"

        db = get_db()
        db.execute(
            "INSERT INTO years(name, department_id) VALUES(%s,%s)",
            (name, id)
        )
        db.commit()
        db.close()

        return redirect(f"/department/{id}")

    return render("إضافة عام", f"""
    <a class="btn open" href="/department/{id}">⬅ رجوع</a>
    <form method="post">
    اسم العام:
    <input name="name" required>
    <button class="btn add">حفظ</button>
    </form>
    """)


# ======================================================
# تعديل عام
# ======================================================

@years_bp.route("/edit_year/<int:id>", methods=["GET", "POST"])
def edit_year(id):

    if "user_id" not in session:
        return redirect("/login")

    if not is_admin():
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

        name = request.form.get("name", "").strip()

        if not name:
            db.close()
            return "يجب إدخال الاسم"

        db.execute(
            "UPDATE years SET name=%s WHERE id=%s",
            (name, id)
        )

        db.commit()
        db.close()

        return redirect(f"/department/{year['department_id']}")

    db.close()

    return render("تعديل عام", f"""
    <form method="post">
    الاسم:
    <input name="name" value="{year['name']}" required>
    <button class="btn edit">تحديث</button>
    </form>
    """)


# ======================================================
# حذف عام
# ======================================================

@years_bp.route("/delete_year/<int:id>", methods=["POST"])
def delete_year(id):

    if "user_id" not in session:
        return redirect("/login")

    if not is_admin():
        return "غير مصرح لك"

    db = get_db()

    year = db.execute(
        "SELECT * FROM years WHERE id=%s",
        (id,)
    ).fetchone()

    if not year:
        db.close()
        return "العنصر غير موجود"

    db.execute("DELETE FROM years WHERE id=%s", (id,))
    db.commit()
    db.close()

    return redirect(f"/department/{year['department_id']}")
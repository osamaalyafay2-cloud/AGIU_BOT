from flask import Blueprint, request, redirect, session
from database import get_db
from routes.shared import render
from psycopg2.extras import RealDictCursor

departments_bp = Blueprint("departments", __name__)

# ======================================================
# أدوات الصلاحيات
# ======================================================

def is_admin():
    return session.get("role") == "super_admin"


def has_department_access(conn, department_id):

    if is_admin():
        return True

    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT 1
        FROM user_permissions
        WHERE user_id=%s AND department_id=%s
    """, (session.get("user_id"), department_id))

    allowed = cursor.fetchone()
    cursor.close()

    return allowed is not None


# ======================================================
# عرض أقسام كلية
# ======================================================

@departments_bp.route("/college/<int:id>")
def view_college(id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT * FROM colleges WHERE id=%s", (id,))
    college = cursor.fetchone()

    if not college:
        cursor.close()
        conn.close()
        return "العنصر غير موجود"

    if is_admin():
        cursor.execute(
            "SELECT * FROM departments WHERE college_id=%s",
            (id,)
        )
    else:
        cursor.execute("""
            SELECT DISTINCT d.*
            FROM departments d
            JOIN user_permissions up ON up.department_id=d.id
            WHERE d.college_id=%s AND up.user_id=%s
        """, (id, session["user_id"]))

    departments = cursor.fetchall()

    cursor.close()
    conn.close()

    body = f"""
    <a class="btn open" href="/">⬅ رجوع</a>
    """

    if is_admin():
        body += f"""
        <a class="btn add" href="/add_department/{id}">➕ إضافة قسم</a>
        """

    body += "<hr>"

    for d in departments:

        body += f"""
        <div class="card">
        📁 {d['name']}
        <br><br>
        <a class="btn open" href="/department/{d['id']}">فتح</a>
        """

        if is_admin():
            body += f"""
            <a class="btn edit" href="/edit_department/{d['id']}">تعديل</a>
            <form method="post" action="/delete_department/{d['id']}" style="display:inline;">
                <button class="btn delete"
                onclick="return confirm('هل أنت متأكد من حذف هذا القسم؟')">
                حذف
                </button>
            </form>
            """

        body += "</div>"

    return render(college["name"], body)


# ======================================================
# عرض أعوام داخل قسم
# ======================================================

@departments_bp.route("/department/<int:id>")
def view_department(id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT * FROM departments WHERE id=%s", (id,))
    department = cursor.fetchone()

    if not department:
        cursor.close()
        conn.close()
        return "العنصر غير موجود"

    if not has_department_access(conn, id):
        cursor.close()
        conn.close()
        return "غير مصرح لك"

    cursor.execute("SELECT * FROM years WHERE department_id=%s", (id,))
    years = cursor.fetchall()

    cursor.close()
    conn.close()

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
# إضافة قسم
# ======================================================

@departments_bp.route("/add_department/<int:id>", methods=["GET", "POST"])
def add_department(id):

    if "user_id" not in session:
        return redirect("/login")

    if not is_admin():
        return "غير مصرح لك"

    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":

        name = request.form.get("name", "").strip()

        if not name:
            cursor.close()
            conn.close()
            return "يجب إدخال اسم القسم"

        cursor.execute(
            "INSERT INTO departments(name,college_id) VALUES(%s,%s)",
            (name, id)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(f"/college/{id}")

    cursor.close()
    conn.close()

    return render("إضافة قسم", f"""
    <a class="btn open" href="/college/{id}">⬅ رجوع</a>
    <form method="post">
    الاسم:
    <input name="name" required>
    <button class="btn add">حفظ</button>
    </form>
    """)


# ======================================================
# تعديل قسم
# ======================================================

@departments_bp.route("/edit_department/<int:id>", methods=["GET", "POST"])
def edit_department(id):

    if "user_id" not in session:
        return redirect("/login")

    if not is_admin():
        return "غير مصرح لك"

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT * FROM departments WHERE id=%s", (id,))
    dept = cursor.fetchone()

    if not dept:
        cursor.close()
        conn.close()
        return "العنصر غير موجود"

    if request.method == "POST":

        name = request.form.get("name", "").strip()

        if not name:
            cursor.close()
            conn.close()
            return "يجب إدخال الاسم"

        cursor.execute(
            "UPDATE departments SET name=%s WHERE id=%s",
            (name, id)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(f"/college/{dept['college_id']}")

    cursor.close()
    conn.close()

    return render("تعديل قسم", f"""
    <form method="post">
    الاسم:
    <input name="name" value="{dept['name']}" required>
    <button class="btn edit">تحديث</button>
    </form>
    """)


# ======================================================
# حذف قسم
# ======================================================

@departments_bp.route("/delete_department/<int:id>", methods=["POST"])
def delete_department(id):

    if "user_id" not in session:
        return redirect("/login")

    if not is_admin():
        return "غير مصرح لك"

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT college_id FROM departments WHERE id=%s", (id,))
    dept = cursor.fetchone()

    if not dept:
        cursor.close()
        conn.close()
        return "العنصر غير موجود"

    cursor.execute("DELETE FROM departments WHERE id=%s", (id,))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(f"/college/{dept['college_id']}")
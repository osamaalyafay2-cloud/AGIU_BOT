from flask import Blueprint, request, redirect, session
from database import get_db
from routes.shared import render
from werkzeug.security import generate_password_hash
from psycopg2.extras import RealDictCursor

admin_users_bp = Blueprint("admin_users", __name__)


# ======================================================
# دالة مساعدة: التحقق من المشرف العام
# ======================================================

def is_admin():
    return session.get("role", "").lower() == "super_admin"


def require_admin():
    if "user_id" not in session:
        return redirect("/login")
    if not is_admin():
        return "غير مصرح لك"


# ======================================================
# عرض المستخدمين
# ======================================================

@admin_users_bp.route("/admin/users")
def users_list():

    check = require_admin()
    if check:
        return check

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    cursor.close()
    conn.close()

    body = """
    <a class="btn add" href="/admin/add_user">➕ إضافة مستخدم</a>
    <a class="btn open" href="/">⬅ رجوع</a>
    <hr>
    """

    for u in users:

        body += f"""
        <div class="card">
        👤 {u['username']} | الدور: {u['role']}
        <br><br>
        <a class="btn edit" href="/admin/edit_user/{u['id']}">تعديل</a>
        """

        if u["role"] == "user":
            body += f"""
            <a class="btn open" href="/admin/permissions/{u['id']}">الصلاحيات</a>
            """

        if u["id"] != session["user_id"]:
            body += f"""
            <form method="post" action="/admin/delete_user/{u['id']}" style="display:inline;">
                <button class="btn delete"
                onclick="return confirm('هل أنت متأكد من الحذف؟')">
                حذف
                </button>
            </form>
            """

        body += "</div>"

    return render("إدارة المستخدمين", body)


# ======================================================
# إضافة مستخدم
# ======================================================

@admin_users_bp.route("/admin/add_user", methods=["GET", "POST"])
def add_user():

    check = require_admin()
    if check:
        return check

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "user")

        if not username or not password:
            return "يجب إدخال اسم المستخدم وكلمة المرور"

        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            "SELECT id FROM users WHERE username=%s",
            (username,)
        )
        existing = cursor.fetchone()

        if existing:
            cursor.close()
            conn.close()
            return "اسم المستخدم موجود مسبقاً"

        hashed = generate_password_hash(password)

        cursor.execute(
            "INSERT INTO users(username,password,role) VALUES(%s,%s,%s)",
            (username, hashed, role)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/admin/users")

    return render("إضافة مستخدم", """
    <a class="btn open" href="/admin/users">⬅ رجوع</a>

    <form method="post">

    اسم المستخدم:
    <input name="username" required>

    كلمة المرور:
    <input type="password" name="password" required>

    الدور:
    <select name="role">
        <option value="user">user</option>
        <option value="super_admin">super_admin</option>
    </select>

    <br><br>
    <button class="btn add">حفظ</button>

    </form>
    """)


# ======================================================
# حذف مستخدم
# ======================================================

@admin_users_bp.route("/admin/delete_user/<int:id>", methods=["POST"])
def delete_user(id):

    check = require_admin()
    if check:
        return check

    if id == session["user_id"]:
        return "لا يمكنك حذف نفسك"

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE id=%s", (id,))
    cursor.execute("DELETE FROM user_permissions WHERE user_id=%s", (id,))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/admin/users")


# ======================================================
# تعديل مستخدم
# ======================================================

@admin_users_bp.route("/admin/edit_user/<int:id>", methods=["GET", "POST"])
def edit_user(id):

    check = require_admin()
    if check:
        return check

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT * FROM users WHERE id=%s", (id,))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        conn.close()
        return "المستخدم غير موجود"

    if request.method == "POST":

        role = request.form.get("role")

        if user["role"] == "super_admin":
            cursor.execute("SELECT COUNT(*) as c FROM users WHERE role='super_admin'")
            admins_count = cursor.fetchone()["c"]

            if admins_count == 1 and role != "super_admin":
                cursor.close()
                conn.close()
                return "لا يمكن إزالة آخر مشرف عام"

        cursor.execute(
            "UPDATE users SET role=%s WHERE id=%s",
            (role, id)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/admin/users")

    cursor.close()
    conn.close()

    return render("تعديل مستخدم", f"""
    <a class="btn open" href="/admin/users">⬅ رجوع</a>

    <form method="post">

    اسم المستخدم:
    <input value="{user['username']}" disabled>

    الدور:
    <select name="role">
        <option value="user" {"selected" if user['role']=="user" else ""}>user</option>
        <option value="super_admin" {"selected" if user['role']=="super_admin" else ""}>super_admin</option>
    </select>

    <br><br>
    <button class="btn edit">تحديث</button>

    </form>
    """)


# ======================================================
# إدارة صلاحيات المستخدم
# ======================================================

@admin_users_bp.route("/admin/permissions/<int:user_id>", methods=["GET", "POST"])
def manage_permissions(user_id):

    check = require_admin()
    if check:
        return check

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        conn.close()
        return "المستخدم غير موجود"

    if user["role"] != "user":
        cursor.close()
        conn.close()
        return "المشرف العام لا يحتاج صلاحيات"

    if request.method == "POST":

        department_id = request.form["department_id"]
        year_id = request.form["year_id"]
        level_id = request.form["level_id"]

        cursor.execute("""
            SELECT id FROM user_permissions
            WHERE user_id=%s AND level_id=%s
        """, (user_id, level_id))

        existing = cursor.fetchone()

        if not existing:
            cursor.execute("""
                INSERT INTO user_permissions(user_id, department_id, year_id, level_id)
                VALUES(%s,%s,%s,%s)
            """, (user_id, department_id, year_id, level_id))
            conn.commit()

        cursor.close()
        conn.close()
        return redirect(f"/admin/permissions/{user_id}")

    cursor.execute("SELECT * FROM departments")
    departments = cursor.fetchall()

    cursor.execute("SELECT * FROM years")
    years = cursor.fetchall()

    cursor.execute("SELECT * FROM levels")
    levels = cursor.fetchall()

    cursor.execute("""
        SELECT up.id, d.name as dept, y.name as year, l.name as level
        FROM user_permissions up
        JOIN departments d ON up.department_id=d.id
        JOIN years y ON up.year_id=y.id
        JOIN levels l ON up.level_id=l.id
        WHERE up.user_id=%s
    """, (user_id,))
    permissions = cursor.fetchall()

    cursor.close()
    conn.close()

    body = f"""
    <a class="btn open" href="/admin/users">⬅ رجوع</a>
    <hr>
    <h3>إضافة صلاحية</h3>
    <form method="post">
    القسم:
    <select name="department_id">
    """

    for d in departments:
        body += f'<option value="{d["id"]}">{d["name"]}</option>'

    body += "</select><br><br>العام:<select name='year_id'>"

    for y in years:
        body += f'<option value="{y["id"]}">{y["name"]}</option>'

    body += "</select><br><br>المستوى:<select name='level_id'>"

    for l in levels:
        body += f'<option value="{l["id"]}">{l["name"]}</option>'

    body += "</select><br><br><button class='btn add'>حفظ</button></form><hr><h3>الصلاحيات الحالية</h3>"

    for p in permissions:
        body += f"""
        <div class="card">
        📌 {p['dept']} → {p['year']} → {p['level']}
        <form method="post" action="/admin/delete_permission/{p['id']}" style="display:inline;">
            <button class="btn delete">حذف</button>
        </form>
        </div>
        """

    return render(f"صلاحيات {user['username']}", body)


# ======================================================
# حذف صلاحية
# ======================================================

@admin_users_bp.route("/admin/delete_permission/<int:id>", methods=["POST"])
def delete_permission(id):

    check = require_admin()
    if check:
        return check

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM user_permissions WHERE id=%s", (id,))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(request.referrer)
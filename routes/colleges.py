from flask import Blueprint, request, redirect, session
from database import get_db
from routes.shared import render

colleges_bp = Blueprint("colleges", __name__)

# =====================================================
# عرض الكليات (لوحة التحكم)
# =====================================================

@colleges_bp.route("/")
def home():

    # حماية الصفحة
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    colleges = conn.execute("SELECT * FROM colleges").fetchall()
    conn.close()

    body = """
    <div style="margin-bottom:15px;">
    """

    # زر إدارة المستخدمين يظهر فقط للمشرف
    if session.get("role") == "super_admin":
        body += """
        <a class="btn add" href="/admin/users">👥 إدارة المستخدمين</a>
        """

    body += """
        <a class="btn open" href="/logout">تسجيل خروج</a>
    </div>
    <hr>
    """

    # فقط المشرف العام يستطيع الإضافة
    if session.get("role") == "super_admin":
        body += """
        <a class="btn add" href="/add_college">➕ إضافة كلية</a>
        <hr>
        """

    for c in colleges:

        body += f"""
        <div class="card">
        🎓 {c['name']}
        <br><br>

        <a class="btn open" href="/college/{c['id']}">فتح</a>
        """

        # صلاحيات المشرف فقط
        if session.get("role") == "super_admin":
            body += f"""
            <a class="btn edit" href="/edit_college/{c['id']}">تعديل</a>
            <form method="post" action="/delete_college/{c['id']}" style="display:inline;">
                <button class="btn delete"
                onclick="return confirm('هل أنت متأكد من الحذف؟')">
                حذف
                </button>
            </form>
            """

        body += "</div>"

    return render("لوحة التحكم", body)


# =====================================================
# إضافة كلية
# =====================================================

@colleges_bp.route("/add_college", methods=["GET", "POST"])
def add_college():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "super_admin":
        return "غير مصرح لك"

    if request.method == "POST":

        name = request.form.get("name", "").strip()

        if not name:
            return "يجب إدخال اسم الكلية"

        conn = get_db()
        conn.execute(
            "INSERT INTO colleges(name) VALUES(?)",
            (name,)
        )
        conn.commit()
        conn.close()

        return redirect("/")

    body = """
    <a class="btn open" href="/">⬅ رجوع</a>
    <form method="post">
        الاسم:
        <input name="name" required>
        <button class="btn add">حفظ</button>
    </form>
    """

    return render("إضافة كلية", body)


# =====================================================
# تعديل كلية
# =====================================================

@colleges_bp.route("/edit_college/<int:id>", methods=["GET", "POST"])
def edit_college(id):

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "super_admin":
        return "غير مصرح لك"

    conn = get_db()

    if request.method == "POST":

        name = request.form.get("name", "").strip()

        if not name:
            conn.close()
            return "يجب إدخال الاسم"

        conn.execute(
            "UPDATE colleges SET name=? WHERE id=?",
            (name, id)
        )
        conn.commit()
        conn.close()

        return redirect("/")

    college = conn.execute(
        "SELECT * FROM colleges WHERE id=?",
        (id,)
    ).fetchone()

    if not college:
        conn.close()
        return "العنصر غير موجود"

    conn.close()

    body = f"""
    <a class="btn open" href="/">⬅ رجوع</a>
    <form method="post">
        الاسم:
        <input name="name" value="{college['name']}" required>
        <button class="btn edit">تحديث</button>
    </form>
    """

    return render("تعديل كلية", body)


# =====================================================
# حذف كلية
# =====================================================

@colleges_bp.route("/delete_college/<int:id>", methods=["POST"])
def delete_college(id):

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "super_admin":
        return "غير مصرح لك"

    conn = get_db()
    conn.execute(
        "DELETE FROM colleges WHERE id=?",
        (id,)
    )
    conn.commit()
    conn.close()

    return redirect("/")
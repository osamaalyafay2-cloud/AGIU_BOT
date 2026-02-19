from flask import Blueprint, request, redirect, session
from database import get_db
from werkzeug.security import check_password_hash

auth_bp = Blueprint("auth", __name__)

# ======================
# تسجيل الدخول
# ======================

@auth_bp.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=%s",
            (username,)
        ).fetchone()
        conn.close()

        # إذا لم يوجد مستخدم
        if not user:
            return "بيانات غير صحيحة"

        # 🔐 فحص كلمة المرور المشفرة
        if not check_password_hash(user["password"], password):
            return "بيانات غير صحيحة"

        session["user_id"] = user["id"]
        session["role"] = user["role"]

        return redirect("/")

    return """
    <h2>تسجيل الدخول</h2>
    <form method="post">
        <input name="username" placeholder="اسم المستخدم"><br><br>
        <input name="password" type="password" placeholder="كلمة المرور"><br><br>
        <button>دخول</button>
    </form>
    """

# ======================
# تسجيل الخروج
# ======================

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
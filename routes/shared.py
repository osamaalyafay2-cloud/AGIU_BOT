from flask import session, redirect
from database import get_db
from psycopg2.extras import RealDictCursor

# ==========================================
# التصميم الموحد
# ==========================================

def render(title, body):

    return f"""
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>

    <style>
    body {{
        font-family:Tahoma;
        background:linear-gradient(135deg,#667eea,#764ba2);
        padding:20px;
        direction:rtl;
    }}

    .box {{
        background:white;
        padding:20px;
        border-radius:10px;
        max-width:1000px;
        margin:auto;
    }}

    .card {{
        background:#f1f2f6;
        padding:15px;
        margin:10px 0;
        border-radius:8px;
    }}

    .btn {{
        padding:6px 12px;
        border-radius:6px;
        text-decoration:none;
        color:white;
        font-size:13px;
        margin-left:5px;
        cursor:pointer;
        border:none;
    }}

    .open{{background:#00b894}}
    .add{{background:#6c5ce7}}
    .edit{{background:#0984e3}}
    .delete{{background:#d63031}}

    input, textarea {{
        width:100%;
        padding:8px;
        margin:5px 0;
    }}

    .topbar {{
        margin-bottom:15px;
        text-align:left;
    }}
    </style>

    </head>
    <body>
    <div class="box">

    <div class="topbar">
        {"👤 مسجل دخول" if "user_id" in session else ""}
        {" | <a href='/logout'>تسجيل خروج</a>" if "user_id" in session else ""}
    </div>

    <h2>{title}</h2>
    {body}
    </div>
    </body>
    </html>
    """


# ==========================================
# حماية الصفحات
# ==========================================

def require_login():
    if "user_id" not in session:
        return redirect("/login")


def require_super_admin():
    if session.get("role") != "super_admin":
        return "غير مصرح لك بالدخول"


# ==========================================
# التحقق من صلاحيات المستخدم
# ==========================================

def check_user_permission(department_id=None, year_id=None, level_id=None):

    if session.get("role") == "super_admin":
        return True

    user_id = session.get("user_id")
    if not user_id:
        return False

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = "SELECT 1 FROM user_permissions WHERE user_id=%s"
    params = [user_id]

    if department_id:
        query += " AND department_id=%s"
        params.append(department_id)

    if year_id:
        query += " AND year_id=%s"
        params.append(year_id)

    if level_id:
        query += " AND level_id=%s"
        params.append(level_id)

    cursor.execute(query, tuple(params))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return row is not None


# ==========================================
# فحص صلاحية المستخدم على مستوى معين
# ==========================================

def has_permission(user_id, level_id):

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT 1
        FROM user_permissions
        WHERE user_id=%s AND level_id=%s
    """, (user_id, level_id))

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return row is not None
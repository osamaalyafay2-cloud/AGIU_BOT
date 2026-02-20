from flask import Blueprint, request, redirect, send_from_directory, current_app, session
from database import get_db
from routes.shared import render
from werkzeug.utils import secure_filename
from psycopg2.extras import RealDictCursor
import os
import time

contents_bp = Blueprint("contents", __name__)

# ==================================================
# دالة مساعدة لفحص صلاحية المستوى
# ==================================================
def has_level_access(conn, level_id):

    if session.get("role") == "super_admin":
        return True

    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT 1 FROM user_permissions
        WHERE user_id=%s AND level_id=%s
    """, (session.get("user_id"), level_id))

    allowed = cursor.fetchone()
    cursor.close()

    return allowed is not None


# ==================================================
# عرض محتوى مادة
# ==================================================
@contents_bp.route("/subject/<int:id>")
def view_subject(id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT * FROM subjects WHERE id=%s", (id,))
    subject = cursor.fetchone()

    if not subject:
        cursor.close()
        conn.close()
        return "العنصر غير موجود"

    if not has_level_access(conn, subject["level_id"]):
        cursor.close()
        conn.close()
        return "غير مصرح لك"

    cursor.execute("SELECT * FROM contents WHERE subject_id=%s", (id,))
    contents = cursor.fetchall()

    cursor.close()
    conn.close()

    body = f"""
    <a class="btn open" href="/level/{subject['level_id']}">⬅ رجوع</a>
    <a class="btn add" href="/add_content/{id}">➕ إضافة محتوى</a>
    <hr>
    """

    for c in contents:

        filename = os.path.basename(c["file_path"])

        body += f"""
        <div class="card">
        📎 {c['title']}
        <br>
        <small>{c['type']}</small>
        <br><br>

        <a class="btn open" href="/uploads/{filename}">فتح</a>
        <a class="btn edit" href="/edit_content/{c['id']}">تعديل</a>
        <form method="post" action="/delete_content/{c['id']}" style="display:inline;">
            <button class="btn delete"
            onclick="return confirm('هل أنت متأكد من الحذف؟')">
            حذف
            </button>
        </form>
        </div>
        """

    return render(subject["name"], body)


# ==================================================
# إضافة محتوى
# ==================================================
@contents_bp.route("/add_content/<int:id>", methods=["GET", "POST"])
def add_content(id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT * FROM subjects WHERE id=%s", (id,))
    subject = cursor.fetchone()

    if not subject:
        cursor.close()
        conn.close()
        return "العنصر غير موجود"

    if not has_level_access(conn, subject["level_id"]):
        cursor.close()
        conn.close()
        return "غير مصرح لك"

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        type_ = request.form.get("type", "").strip()
        file = request.files.get("file")

        if not title or not type_:
            cursor.close()
            conn.close()
            return "يجب إدخال العنوان والنوع"

        if not file or file.filename == "":
            cursor.close()
            conn.close()
            return "يجب اختيار ملف"

        original_name = secure_filename(file.filename)
        ext = os.path.splitext(original_name)[1]
        filename = f"{int(time.time())}{ext}"

        upload_folder = current_app.config["UPLOAD_FOLDER"]
        filepath = os.path.join(upload_folder, filename)

        file.save(filepath)

        file_size = os.path.getsize(filepath)
        mime_type = file.mimetype

        cursor.execute("""
            INSERT INTO contents
            (title, description, type, file_path, file_size, mime_type, subject_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (title, description, type_, filepath, file_size, mime_type, id))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(f"/subject/{id}")

    cursor.close()
    conn.close()

    return render("رفع محتوى", f"""
    <a class="btn open" href="/subject/{id}">⬅ رجوع</a>

    <form method="post" enctype="multipart/form-data">

    العنوان:
    <input name="title" required>

    الوصف:
    <textarea name="description"></textarea>

    النوع:
    <input name="type" required>

    الملف:
    <input type="file" name="file" required>

    <button class="btn add">رفع</button>

    </form>
    """)


# ==================================================
# تعديل محتوى
# ==================================================
@contents_bp.route("/edit_content/<int:id>", methods=["GET", "POST"])
def edit_content(id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT * FROM contents WHERE id=%s", (id,))
    content = cursor.fetchone()

    if not content:
        cursor.close()
        conn.close()
        return "العنصر غير موجود"

    cursor.execute("SELECT * FROM subjects WHERE id=%s", (content["subject_id"],))
    subject = cursor.fetchone()

    if not has_level_access(conn, subject["level_id"]):
        cursor.close()
        conn.close()
        return "غير مصرح لك"

    if request.method == "POST":

        cursor.execute("""
            UPDATE contents
            SET title=%s, description=%s, type=%s
            WHERE id=%s
        """, (
            request.form["title"],
            request.form.get("description", ""),
            request.form["type"],
            id
        ))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(f"/subject/{content['subject_id']}")

    cursor.close()
    conn.close()

    return render("تعديل محتوى", f"""
    <form method="post">

    العنوان:
    <input name="title" value="{content['title']}" required>

    الوصف:
    <textarea name="description">{content['description']}</textarea>

    النوع:
    <input name="type" value="{content['type']}" required>

    <button class="btn edit">تحديث</button>

    </form>
    """)


# ==================================================
# حذف محتوى
# ==================================================
@contents_bp.route("/delete_content/<int:id>", methods=["POST"])
def delete_content(id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT * FROM contents WHERE id=%s", (id,))
    content = cursor.fetchone()

    if not content:
        cursor.close()
        conn.close()
        return "العنصر غير موجود"

    cursor.execute("SELECT * FROM subjects WHERE id=%s", (content["subject_id"],))
    subject = cursor.fetchone()

    if not has_level_access(conn, subject["level_id"]):
        cursor.close()
        conn.close()
        return "غير مصرح لك"

    if os.path.exists(content["file_path"]):
        os.remove(content["file_path"])

    cursor.execute("DELETE FROM contents WHERE id=%s", (id,))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(f"/subject/{content['subject_id']}")


# ==================================================
# تقديم الملفات
# ==================================================
@contents_bp.route("/uploads/<filename>")
def serve_file(filename):

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    file_path = os.path.join(upload_folder, filename)

    if not os.path.exists(file_path):
        return "الملف غير موجود"

    return send_from_directory(upload_folder, filename)
from flask import Flask, request, redirect, send_from_directory
import sqlite3
import os
import time
from werkzeug.utils import secure_filename

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE = os.path.join(BASE_DIR, "university.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# =====================================================
# الاتصال بقاعدة البيانات
# =====================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# =====================================================
# تصميم موحد
# =====================================================

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
    }}

    .open{{background:#00b894}}
    .add{{background:#6c5ce7}}
    .edit{{background:#0984e3}}
    .delete{{background:#d63031}}

    input {{
        width:100%;
        padding:8px;
        margin:5px 0;
    }}
    </style>

    <script>
    function confirmDelete(url)
    {{
        if(confirm("هل أنت متأكد من الحذف؟"))
        {{
            window.location=url
        }}
    }}
    </script>

    </head>
    <body>
    <div class="box">
    <h2>{title}</h2>
    {body}
    </div>
    </body>
    </html>
    """


# =====================================================
# الصفحة الرئيسية - الكليات
# =====================================================

@app.route("/")
def home():

    conn=get_db()
    colleges=conn.execute("SELECT * FROM colleges").fetchall()
    conn.close()

    body="""
    <a class="btn add" href="/add_college">➕ إضافة كلية</a>
    <hr>
    """

    for c in colleges:
        body+=f"""
        <div class="card">
        🎓 {c['name']}
        <br><br>
        <a class="btn open" href="/college/{c['id']}">فتح</a>
        <a class="btn edit" href="/edit_college/{c['id']}">تعديل</a>
        <form method="post" action="/delete_college/{c['id']}" style="display:inline;">
            <button class="btn delete" onclick="return confirm('هل أنت متأكد من الحذف؟')">
             حذف
            </button>
        </form>
        </div>
        """

    return render("لوحة التحكم", body)


@app.route("/add_college",methods=["GET","POST"])
def add_college():

    if request.method=="POST":
        conn=get_db()
        conn.execute("INSERT INTO colleges(name) VALUES(?)",
                     (request.form["name"],))
        conn.commit()
        conn.close()
        return redirect("/")

    return render("إضافة كلية",
    """
    <a class="btn open" href="/">⬅ رجوع</a>
    <form method="post">
    الاسم:
    <input name="name">
    <button class="btn add">حفظ</button>
    </form>
    """)


@app.route("/edit_college/<int:id>",methods=["GET","POST"])
def edit_college(id):

    conn=get_db()

    if request.method=="POST":
        conn.execute("UPDATE colleges SET name=? WHERE id=?",
                     (request.form["name"],id))
        conn.commit()
        conn.close()
        return redirect("/")

    college=conn.execute("SELECT * FROM colleges WHERE id=?",(id,)).fetchone()
    if not college:
       return "العنصر غير موجود"
    conn.close()

    return render("تعديل كلية",
    f"""
    <a class="btn open" href="/">⬅ رجوع</a>
    <form method="post">
    الاسم:
    <input name="name" value="{college['name']}">
    <button class="btn edit">تحديث</button>
    </form>
    """)


@app.route("/delete_college/<int:id>", methods=["POST"])
def delete_college(id):
    conn=get_db()
    conn.execute("DELETE FROM colleges WHERE id=?",(id,))
    conn.commit()
    conn.close()
    return redirect("/")


# =====================================================
# الأقسام
# =====================================================

@app.route("/college/<int:id>")
def view_college(id):

    conn = get_db()

    college = conn.execute(
        "SELECT * FROM colleges WHERE id=?",
        (id,)
    ).fetchone()

    # هنا نضيف التحقق
    if not college:
        conn.close()
        return "العنصر غير موجود"

    departments = conn.execute(
        "SELECT * FROM departments WHERE college_id=?",
        (id,)
    ).fetchall()

    conn.close()

    body=f"""
    <a class="btn open" href="/">⬅ رجوع</a>
    <a class="btn add" href="/add_department/{id}">➕ إضافة قسم</a>
    <hr>
    """

    for d in departments:
        body+=f"""
          <div class="card">
          📁 {d['name']}
          <br><br>

               <a class="btn open" href="/department/{d['id']}">فتح</a>
               <a class="btn edit" href="/edit_department/{d['id']}">تعديل</a>

            <form method="post" action="/delete_department/{d['id']}" style="display:inline;">
                <button class="btn delete" onclick="return confirm('هل أنت متأكد من الحذف؟')">
                  حذف
                </button>
             </form>

            </div>
            """

    return render(college["name"], body)


@app.route("/add_department/<int:id>",methods=["GET","POST"])
def add_department(id):

    if request.method=="POST":
        conn=get_db()
        conn.execute("INSERT INTO departments(name,college_id) VALUES(?,?)",
                     (request.form["name"],id))
        conn.commit()
        conn.close()
        return redirect(f"/college/{id}")

    return render("إضافة قسم",
    f"""
    <a class="btn open" href="/college/{id}">⬅ رجوع</a>
    <form method="post">
    الاسم:
    <input name="name">
    <button class="btn add">حفظ</button>
    </form>
    """)


@app.route("/edit_department/<int:id>",methods=["GET","POST"])
def edit_department(id):

    conn=get_db()

    if request.method=="POST":
        conn.execute("UPDATE departments SET name=? WHERE id=?",
                     (request.form["name"],id))
        conn.commit()
        college_id=conn.execute("SELECT college_id FROM departments WHERE id=?",
                                (id,)).fetchone()["college_id"]
        conn.close()
        return redirect(f"/college/{college_id}")

    dept=conn.execute("SELECT * FROM departments WHERE id=?",(id,)).fetchone()
    if not dept:
        return "العنصر غير موجود"
    conn.close()

    return render("تعديل قسم",
    f"""
    <form method="post">
    الاسم:
    <input name="name" value="{dept['name']}">
    <button class="btn edit">تحديث</button>
    </form>
    """)


@app.route("/delete_department/<int:id>", methods=["POST"])
def delete_department(id):

    conn=get_db()
    row = conn.execute("SELECT college_id FROM departments WHERE id=?",(id,)).fetchone()
    if not row:
        conn.close()
        return "العنصر غير موجود"

    college_id = row["college_id"]
    conn.execute("DELETE FROM departments WHERE id=?",(id,))
    conn.commit()
    conn.close()
    return redirect(f"/college/{college_id}")


# =====================================================
# المستويات
# =====================================================

@app.route("/department/<int:id>")
def view_department(id):

    conn = get_db()

    dept = conn.execute(
        "SELECT * FROM departments WHERE id=?",
        (id,)
    ).fetchone()

    if not dept:
        conn.close()
        return "العنصر غير موجود"

    years = conn.execute(
        "SELECT * FROM years WHERE department_id=?",
        (id,)
    ).fetchall()

    conn.close()

    body = f"""
    <a class="btn open" href="/college/{dept['college_id']}">⬅ رجوع</a>
    <a class="btn add" href="/add_year/{id}">➕ إضافة عام</a>
    <hr>
    """

    for y in years:
        body += f"""
        <div class="card">
        📅 {y['name']}
        <br><br>

        <a class="btn open" href="/year/{y['id']}">فتح</a>
        <a class="btn edit" href="/edit_year/{y['id']}">تعديل</a>

        <form method="post" action="/delete_year/{y['id']}" style="display:inline;">
            <button class="btn delete" onclick="return confirm('هل أنت متأكد من الحذف؟')">
                حذف
            </button>
        </form>

        </div>
        """

    return render(dept["name"], body)


@app.route("/add_year/<int:id>", methods=["GET","POST"])
def add_year(id):

    conn = get_db()

    dept = conn.execute(
        "SELECT * FROM departments WHERE id=?",
        (id,)
    ).fetchone()

    if not dept:
        conn.close()
        return "العنصر غير موجود"

    if request.method == "POST":
        conn.execute(
            "INSERT INTO years(name, department_id) VALUES(?,?)",
            (request.form["name"], id)
        )
        conn.commit()
        conn.close()
        return redirect(f"/department/{id}")

    conn.close()

    return render("إضافة عام",
    f"""
    <a class="btn open" href="/department/{id}">⬅ رجوع</a>
    <form method="post">
    اسم العام:
    <input name="name">
    <button class="btn add">حفظ</button>
    </form>
    """)

@app.route("/edit_year/<int:id>", methods=["GET","POST"])
def edit_year(id):

    conn = get_db()

    if request.method == "POST":
        conn.execute(
            "UPDATE years SET name=? WHERE id=?",
            (request.form["name"], id)
        )
        conn.commit()

        row = conn.execute(
            "SELECT department_id FROM years WHERE id=?",
            (id,)
        ).fetchone()

        if not row:
            conn.close()
            return "العنصر غير موجود"

        department_id = row["department_id"]
        conn.close()
        return redirect(f"/department/{department_id}")

    year = conn.execute(
        "SELECT * FROM years WHERE id=?",
        (id,)
    ).fetchone()

    if not year:
        conn.close()
        return "العنصر غير موجود"

    conn.close()

    return render("تعديل عام",
    f"""
    <form method="post">
    الاسم:
    <input name="name" value="{year['name']}">
    <button class="btn edit">تحديث</button>
    </form>
    """)


@app.route("/delete_year/<int:id>", methods=["POST"])
def delete_year(id):

    conn = get_db()

    row = conn.execute(
        "SELECT department_id FROM years WHERE id=?",
        (id,)
    ).fetchone()

    if not row:
        conn.close()
        return "العنصر غير موجود"

    department_id = row["department_id"]

    conn.execute(
        "DELETE FROM years WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(f"/department/{department_id}")

@app.route("/add_level/<int:id>",methods=["GET","POST"])
def add_level(id):

    conn = get_db()

    year = conn.execute(
        "SELECT * FROM years WHERE id=?",
        (id,)
    ).fetchone()

    if not year:
        conn.close()
        return "العنصر غير موجود"

    if request.method=="POST":
        conn.execute(
            "INSERT INTO levels(name,year_id) VALUES(?,?)",
            (request.form["name"],id)
        )
        conn.commit()
        conn.close()
        return redirect(f"/year/{id}")

    conn.close()

    return render("إضافة مستوى",
    f"""
    <a class="btn open" href="/year/{id}">⬅ رجوع</a>
    <form method="post">
    الاسم:
    <input name="name">
    <button class="btn add">حفظ</button>
    </form>
    """)

@app.route("/edit_level/<int:id>",methods=["GET","POST"])
def edit_level(id):

    conn=get_db()

    if request.method=="POST":
        conn.execute("UPDATE levels SET name=? WHERE id=?",
                     (request.form["name"],id))
        conn.commit()

        row = conn.execute(
            "SELECT year_id FROM levels WHERE id=?",
            (id,)
        ).fetchone()

        if not row:
            conn.close()
            return "العنصر غير موجود"

        year_id = row["year_id"]
        conn.close()
        return redirect(f"/year/{year_id}")

    level=conn.execute("SELECT * FROM levels WHERE id=?",(id,)).fetchone()
    if not level:
        conn.close()
        return "العنصر غير موجود"
    conn.close()

    return render("تعديل مستوى",
    f"""
    <form method="post">
    الاسم:
    <input name="name" value="{level['name']}">
    <button class="btn edit">تحديث</button>
    </form>
    """)

@app.route("/delete_level/<int:id>", methods=["POST"])
def delete_level(id):

    conn=get_db()

    row = conn.execute(
        "SELECT year_id FROM levels WHERE id=?",
        (id,)
    ).fetchone()

    if not row:
        conn.close()
        return "العنصر غير موجود"

    year_id = row["year_id"]

    conn.execute("DELETE FROM levels WHERE id=?",(id,))
    conn.commit()
    conn.close()

    return redirect(f"/year/{year_id}")
# =====================================================
# المواد
# =====================================================

@app.route("/year/<int:id>")
def view_year(id):

    conn = get_db()

    year = conn.execute(
        "SELECT * FROM years WHERE id=?",
        (id,)
    ).fetchone()

    if not year:
        conn.close()
        return "العنصر غير موجود"

    levels = conn.execute(
        "SELECT * FROM levels WHERE year_id=?",
        (id,)
    ).fetchall()

    conn.close()

    body = f"""
    <a class="btn open" href="/department/{year['department_id']}">⬅ رجوع</a>
    <a class="btn add" href="/add_level/{id}">➕ إضافة مستوى</a>
    <hr>
    """

    for l in levels:
        body += f"""
        <div class="card">
        📚 {l['name']}
        <br><br>

        <a class="btn open" href="/level/{l['id']}">فتح</a>
        <a class="btn edit" href="/edit_level/{l['id']}">تعديل</a>

        <form method="post" action="/delete_level/{l['id']}" style="display:inline;">
            <button class="btn delete" onclick="return confirm('هل أنت متأكد من الحذف؟')">
                حذف
            </button>
        </form>

        </div>
        """

    return render(year["name"], body)

@app.route("/level/<int:id>")
def view_level(id):

    conn = get_db()

    level = conn.execute(
        "SELECT * FROM levels WHERE id=?",
        (id,)
    ).fetchone()

    if not level:
        conn.close()
        return "العنصر غير موجود"

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
            <button class="btn delete" onclick="return confirm('هل أنت متأكد من الحذف؟')">
                حذف
            </button>
        </form>

        </div>
        """

    return render(level["name"], body)


@app.route("/add_subject/<int:id>",methods=["GET","POST"])
def add_subject(id):

    if request.method=="POST":
        conn=get_db()
        conn.execute("INSERT INTO subjects(name,level_id) VALUES(?,?)",
                     (request.form["name"],id))
        conn.commit()
        conn.close()
        return redirect(f"/level/{id}")

    return render("إضافة مادة",
    f"""
    <a class="btn open" href="/level/{id}">⬅ رجوع</a>
    <form method="post">
    الاسم:
    <input name="name">
    <button class="btn add">حفظ</button>
    </form>
    """)


@app.route("/edit_subject/<int:id>",methods=["GET","POST"])
def edit_subject(id):

    conn=get_db()

    if request.method == "POST":
        conn.execute("UPDATE subjects SET name=? WHERE id=?",(request.form["name"], id))
        conn.commit()

        row = conn.execute("SELECT level_id FROM subjects WHERE id=?",(id,)
        ).fetchone()

        if not row:
            conn.close()
            return "العنصر غير موجود"

        level_id = row["level_id"]
        conn.close()
        return redirect(f"/level/{level_id}")

    subject=conn.execute("SELECT * FROM subjects WHERE id=?",(id,)).fetchone()
    if not subject:
        return "العنصر غير موجود"
    conn.close()

    return render("تعديل مادة",
    f"""
    <form method="post">
    الاسم:
    <input name="name" value="{subject['name']}">
    <button class="btn edit">تحديث</button>
    </form>
    """)


@app.route("/delete_subject/<int:id>", methods=["POST"])
def delete_subject(id):

    conn=get_db()
    row = conn.execute("SELECT level_id FROM subjects WHERE id=?",(id,)
    ).fetchone()

    if not row:
        conn.close()
        return "العنصر غير موجود"

    level_id = row["level_id"]
    conn.execute("DELETE FROM subjects WHERE id=?",(id,))
    conn.commit()
    conn.close()
    return redirect(f"/level/{level_id}")


# =====================================================
# المحتوى
# =====================================================

@app.route("/subject/<int:id>")
def view_subject(id):

    conn = get_db()
    subject = conn.execute(
        "SELECT * FROM subjects WHERE id=?",
        (id,)
    ).fetchone()

    if not subject:
        conn.close()
        return "العنصر غير موجود"

    contents = conn.execute(
        "SELECT * FROM contents WHERE subject_id=?",
        (id,)
    ).fetchall()

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
        {c['title']}
        <br><br>

        <a class="btn open" href="/uploads/{filename}">فتح</a>
        <a class="btn edit" href="/edit_content/{c['id']}">تعديل</a>

        <form method="post" action="/delete_content/{c['id']}" style="display:inline;">
            <button class="btn delete" onclick="return confirm('هل أنت متأكد من الحذف؟')">
                حذف
            </button>
        </form>

        </div>
        """

    return render(subject["name"], body)

@app.route("/add_content/<int:id>", methods=["GET", "POST"])
def add_content(id):

    conn = get_db()

    # التأكد أن المادة موجودة
    subject = conn.execute(
        "SELECT * FROM subjects WHERE id=?",
        (id,)
    ).fetchone()

    if not subject:
        conn.close()
        return "العنصر غير موجود"

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        type_ = request.form.get("type", "").strip()
        file = request.files.get("file")

        # التحقق من الحقول الأساسية
        if not title or not type_:
            conn.close()
            return "يجب إدخال العنوان والنوع"

        # التحقق من وجود ملف
        if not file or file.filename == "":
            conn.close()
            return "يجب اختيار ملف"

        # تنظيف الاسم
        original_name = secure_filename(file.filename)

        # التأكد أن للملف امتداد
        if "." not in original_name:
            conn.close()
            return "اسم الملف غير صالح"

        ext = os.path.splitext(original_name)[1]

        # توليد اسم فريد
        filename = f"{int(time.time())}{ext}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        # حفظ الملف
        file.save(filepath)

        # معلومات الملف
        file_size = os.path.getsize(filepath)
        mime_type = file.mimetype

        # إدخال في قاعدة البيانات
        conn.execute("""
            INSERT INTO contents
            (title, description, type, file_path, file_size, mime_type, subject_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (title, description, type_, filepath, file_size, mime_type, id)
        )

        conn.commit()
        conn.close()

        return redirect(f"/subject/{id}")

    conn.close()

    return render("رفع محتوى",
    f"""
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

@app.route("/edit_content/<int:id>",methods=["GET","POST"])
def edit_content(id):

    conn=get_db()

    if request.method=="POST":
        conn.execute("""
                        UPDATE contents 
                        SET title=?, description=?, type=? 
                        WHERE id=?
                        """,
                        (request.form["title"],
                        request.form.get("description",""),
                        request.form["type"],
                         id)
                    )
        conn.commit()
        subject_id=conn.execute("SELECT subject_id FROM contents WHERE id=?",
                                (id,)).fetchone()["subject_id"]
        conn.close()
        return redirect(f"/subject/{subject_id}")

    content=conn.execute("SELECT * FROM contents WHERE id=?",(id,)).fetchone()
    if not content:
        return "العنصر غير موجود"
    conn.close()

    return render("تعديل محتوى",
    f"""
    <form method="post">

    العنوان:
    <input name="title" value="{content['title']}">

    الوصف:
    <textarea name="description">{content['description']}</textarea>

    النوع:
    <input name="type" value="{content['type']}">

    <button class="btn edit">تحديث</button>

    </form>
    """)


@app.route("/delete_content/<int:id>", methods=["POST"])
def delete_content(id):

    conn = get_db()

    content = conn.execute(
        "SELECT * FROM contents WHERE id=?",
        (id,)
    ).fetchone()

    # التحقق من وجود العنصر
    if not content:
        conn.close()
        return "العنصر غير موجود"

    subject_id = content["subject_id"]

    # حذف الملف من السيرفر إن وجد
    if os.path.exists(content["file_path"]):
        os.remove(content["file_path"])

    # حذف السجل من قاعدة البيانات
    conn.execute(
        "DELETE FROM contents WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(f"/subject/{subject_id}")


# =====================================================
# الملفات
# =====================================================
@app.route("/uploads/<filename>")
def serve_file(filename):

    conn = get_db()

    row = conn.execute(
        "SELECT * FROM contents WHERE file_path LIKE ?",
        (f"%{filename}",)
    ).fetchone()

    conn.close()

    if not row:
        return "الملف غير موجود"

    return send_from_directory(UPLOAD_FOLDER, filename)


if __name__=="__main__":
    app.run(debug=True)
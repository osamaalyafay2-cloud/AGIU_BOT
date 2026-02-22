from flask import Flask
from config import UPLOAD_FOLDER
import os

from routes.admin_users import admin_users_bp
from routes.colleges import colleges_bp
from routes.departments import departments_bp
from routes.years import years_bp
from routes.levels import levels_bp
from routes.subjects import subjects_bp
from routes.contents import contents_bp
from routes.auth import auth_bp

# ==========================================
# إنشاء تطبيق لوحة الإدارة فقط
# ==========================================

app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = os.environ.get("SECRET_KEY", "super_secret_key")

# ==========================================
# تسجيل Blueprints الخاصة بالإدارة
# ==========================================

app.register_blueprint(auth_bp, url_prefix="/admin")
app.register_blueprint(colleges_bp, url_prefix="/admin")
app.register_blueprint(departments_bp, url_prefix="/admin")
app.register_blueprint(years_bp, url_prefix="/admin")
app.register_blueprint(levels_bp, url_prefix="/admin")
app.register_blueprint(subjects_bp, url_prefix="/admin")
app.register_blueprint(contents_bp, url_prefix="/admin")
app.register_blueprint(admin_users_bp, url_prefix="/admin")

# ==========================================
# صفحة رئيسية بسيطة
# ==========================================

@app.route("/")
def home():
    return "Admin Panel Running Successfully"

# ==========================================
# تشغيل محلي فقط
# ==========================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
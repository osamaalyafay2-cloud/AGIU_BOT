from flask import Flask
from config import UPLOAD_FOLDER
import os

# =====================================================
# استيراد الـ Blueprints
# =====================================================

from routes.admin_users import admin_users_bp
from routes.colleges import colleges_bp
from routes.departments import departments_bp
from routes.years import years_bp
from routes.levels import levels_bp
from routes.subjects import subjects_bp
from routes.contents import contents_bp
from routes.auth import auth_bp


# =====================================================
# إنشاء تطبيق Flask
# =====================================================

def create_app():
    app = Flask(__name__)

    # إعدادات أساسية
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app.secret_key = os.environ.get("SECRET_KEY", "super_secret_key")

    # تسجيل الـ Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(colleges_bp)
    app.register_blueprint(departments_bp)
    app.register_blueprint(years_bp)
    app.register_blueprint(levels_bp)
    app.register_blueprint(subjects_bp)
    app.register_blueprint(contents_bp)
    app.register_blueprint(admin_users_bp)

    return app


# =====================================================
# إنشاء التطبيق للتشغيل عبر Gunicorn
# =====================================================

app = create_app()


# =====================================================
# تشغيل محلي فقط (للتجربة على جهازك)
# =====================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
from flask import Flask
from config import UPLOAD_FOLDER

from routes.admin_users import admin_users_bp
from routes.colleges import colleges_bp
from routes.departments import departments_bp
from routes.years import years_bp
from routes.levels import levels_bp
from routes.subjects import subjects_bp
from routes.contents import contents_bp
from routes.auth import auth_bp

import threading
import os


# ==========================================
# إنشاء التطبيق
# ==========================================

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = os.environ.get("SECRET_KEY", "super_secret_key")


# ==========================================
# تسجيل الـ Blueprints
# ==========================================

app.register_blueprint(auth_bp)
app.register_blueprint(colleges_bp)
app.register_blueprint(departments_bp)
app.register_blueprint(years_bp)
app.register_blueprint(levels_bp)
app.register_blueprint(subjects_bp)
app.register_blueprint(contents_bp)
app.register_blueprint(admin_users_bp)


# ==========================================
# تشغيل البوت في Thread منفصل
# ==========================================

def start_telegram_bot():
    from bot import start_bot
    start_bot()


# نشغّل البوت فقط إذا لم نكن في وضع التطوير المباشر
if os.environ.get("RENDER"):
    threading.Thread(target=start_telegram_bot, daemon=True).start()


# ==========================================
# تشغيل محلي
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)
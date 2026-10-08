from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_file,
    session,
    redirect,
    url_for
)

from flask_sqlalchemy import SQLAlchemy

from datetime import datetime

from functools import wraps

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from sqlalchemy import text

import os
import shutil
import smtplib

from email.mime.text import MIMEText

from utils.speech import speech_to_text

from deepmultilingualpunctuation import PunctuationModel


from gtts import gTTS
from gtts.lang import tts_langs


# =====================================================
# FLASK APP
# =====================================================

app = Flask(__name__)
# =====================================================
# DESKTOP SESSION HISTORY
# =====================================================

import os
import shutil


# Find the correct Windows Desktop
# Supports OneDrive Desktop and normal Desktop

USER_HOME = os.path.expanduser("~")

ONEDRIVE_DESKTOP = os.path.join(
    USER_HOME,
    "OneDrive",
    "Desktop"
)

NORMAL_DESKTOP = os.path.join(
    USER_HOME,
    "Desktop"
)


if os.path.exists(ONEDRIVE_DESKTOP):

    DESKTOP_FOLDER = ONEDRIVE_DESKTOP

else:

    DESKTOP_FOLDER = NORMAL_DESKTOP


SPEECH2TEXT_DESKTOP_FOLDER = os.path.join(
    DESKTOP_FOLDER,
    "Speech2Text"
)


DESKTOP_HISTORY_FILE = os.path.join(
    SPEECH2TEXT_DESKTOP_FOLDER,
    "history.txt"
)
# =====================================================
# CREATE DESKTOP HISTORY FOLDER
# =====================================================

def create_desktop_history_folder():

    try:

        os.makedirs(
            SPEECH2TEXT_DESKTOP_FOLDER,
            exist_ok=True
        )


        if not os.path.exists(
            DESKTOP_HISTORY_FILE
        ):

            with open(
                DESKTOP_HISTORY_FILE,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(
                    "Speech2Text Session History\n"
                )

                file.write(
                    "============================\n\n"
                )


        print(
            "Speech2Text Desktop folder:"
        )

        print(
            SPEECH2TEXT_DESKTOP_FOLDER
        )


    except Exception as e:

        print(
            "ERROR creating Desktop folder:"
        )

        print(e)
   # =====================================================
# SAVE HISTORY TO DESKTOP
# =====================================================

def save_desktop_history(username, source, text):

    try:

        os.makedirs(
            SPEECH2TEXT_DESKTOP_FOLDER,
            exist_ok=True
        )

        with open(
            DESKTOP_HISTORY_FILE,
            "a",
            encoding="utf-8"
        ) as file:

            file.write(
                "----------------------------------------\n"
            )

            file.write(
                f"User: {username}\n"
            )

            file.write(
                f"Source: {source}\n"
            )

            file.write(
                f"Text: {text}\n"
            )

            file.write(
                "----------------------------------------\n\n"
            )

        print("✅ History saved to Desktop.")

    except Exception as e:

        print(
            "❌ Desktop history error:",
            e
        )

app.secret_key = "speech2text-secret-key"

app.config["SESSION_PERMANENT"] = False

import uuid

APP_SESSION_ID = str(uuid.uuid4())

# =====================================================
# DATABASE CONFIGURATION
# =====================================================

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///history.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# =====================================================
# USER TABLE
# =====================================================

class User(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        default="user",
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.now
    )


# =====================================================
# HISTORY TABLE
# =====================================================

class History(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        nullable=True
    )

    text = db.Column(
        db.Text,
        nullable=False
    )

    source = db.Column(
        db.String(50),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.now
    )


# =====================================================
# PUNCTUATION MODEL
# =====================================================

punct_model = PunctuationModel()


# =====================================================
# UPLOAD FOLDER
# =====================================================

UPLOAD_FOLDER = "uploads"

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# =====================================================
# LOGIN REQUIRED DECORATOR
# =====================================================

# =====================================================
# ADMIN REQUIRED DECORATOR
# =====================================================

def admin_required(route_function):

    @wraps(route_function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:

            return redirect(
                url_for("login")
            )

        if session.get("role") != "admin":

            return "Access Denied: Admins Only", 403

        return route_function(
            *args,
            **kwargs
        )

    return wrapper

# =====================================================
# LOGIN REQUIRED
# =====================================================

def login_required(route_function):

    @wraps(route_function)
    def wrapper(*args, **kwargs):

        # Check whether user is logged in
        if "user_id" not in session:

            return redirect(
                url_for("login")
            )


        # Check whether this login was created
        # during the current Flask application run

        if session.get("app_session_id") != APP_SESSION_ID:

            # Clear old login session
            session.clear()

            # Send user back to login
            return redirect(
                url_for("login")
            )


        # User is authenticated
        return route_function(
            *args,
            **kwargs
        )


    return wrapper
# =====================================================
# HOME
# =====================================================

# =====================================================
# HOME PAGE
# =====================================================

@app.route("/")
@login_required
def home():

    return render_template(
        "index.html"
    )


# =====================================================
# LIVE SPEECH
# =====================================================

@app.route("/live")
@login_required
def live():

    return render_template(
        "live.html"
    )


# =====================================================
# UPLOAD AUDIO PAGE
# =====================================================

@app.route("/upload")
@login_required
def upload_page():

    return render_template(
        "upload.html"
    )


# =====================================================
# TEXT TO AUDIO PAGE
# =====================================================

@app.route("/text-to-audio")
@login_required
def text_to_audio():

    from gtts.lang import tts_langs

    languages = tts_langs()

    return render_template(
        "text_to_audio.html",
        languages=languages
    )
# =====================================================
# GENERATE AUDIO
# =====================================================

@app.route("/generate-audio", methods=["POST"])
@login_required
def generate_audio():

    text = request.form.get("text", "").strip()

    language = request.form.get(
        "language",
        "en"
    )

    if not text:

        return jsonify({
            "error": "No text provided."
        }), 400

    try:

        tts = gTTS(
            text=text,
            lang=language,
            slow=False
        )

        file_path = os.path.join(
            "static",
            "generated_speech.mp3"
        )

        tts.save(file_path)

        return send_file(
            file_path,
            mimetype="audio/mpeg"
        )

    except Exception as e:

        print("TTS Error:", e)

        return jsonify({
            "error": str(e)
        }), 500

# =====================================================
# ABOUT
# =====================================================

@app.route("/about")
def about():

    return render_template(
        "about.html"
    )


# =====================================================
# CONTACT
# =====================================================

@app.route("/contact")
def contact():

    return render_template(
        "contact.html"
    )


# =====================================================
# SEND EMAIL
# =====================================================

@app.route(
    "/send_email",
    methods=["POST"]
)
def send_email():

    name = request.form["name"]

    email = request.form["email"]

    subject = request.form["subject"]

    message = request.form["message"]


    # -------------------------------------------------
    # EMAIL SETTINGS
    # -------------------------------------------------

    sender_email = "24711a0566@necn.ac.in"

    app_password = "zlzx wmqe tuyr vjae"

    developer_email = "24711a0566@necn.ac.in"


    # -------------------------------------------------
    # EMAIL TO DEVELOPER
    # -------------------------------------------------

    developer_body = f"""
New Contact Form Submission

---------------------------------

Name : {name}

Email : {email}

Subject : {subject}

Message :

{message}

---------------------------------

Speech To Text Converter Website
"""


    dev_msg = MIMEText(
        developer_body
    )

    dev_msg["Subject"] = (
        f"New Contact: {subject}"
    )

    dev_msg["From"] = sender_email

    dev_msg["To"] = developer_email


    # -------------------------------------------------
    # AUTO REPLY
    # -------------------------------------------------

    user_body = f"""
Dear {name},

Thank you for contacting us.

We have successfully received your message regarding:

"{subject}"

Our team will review your message and get back to you as soon as possible.

Thank you for using our Speech To Text Converter.

Regards,

Kavya Sree
Developer
Speech To Text Converter
"""


    user_msg = MIMEText(
        user_body
    )

    user_msg["Subject"] = (
        "Thank You for Contacting Us"
    )

    user_msg["From"] = sender_email

    user_msg["To"] = email


    try:

        server = smtplib.SMTP(
            "smtp.gmail.com",
            587
        )

        server.starttls()

        server.login(
            sender_email,
            app_password
        )

        server.send_message(
            dev_msg
        )

        server.send_message(
            user_msg
        )

        server.quit()


        return render_template(
            "contact.html",
            success=
            "✅ Your message has been sent successfully! Thank you for contacting us."
        )


    except Exception as e:

        return render_template(
            "contact.html",
            error=
            f"❌ Error: {e}"
        )


# =====================================================
# AUDIO CONVERT
# =====================================================

@app.route(
    "/convert",
    methods=["POST"]
)
@login_required
def convert():

    if "audio" not in request.files:

        return jsonify({

            "text":
            "No audio file uploaded."

        })


    file = request.files["audio"]


    if file.filename == "":

        return jsonify({

            "text":
            "Please select an audio file."

        })


    filepath = os.path.join(

        app.config["UPLOAD_FOLDER"],

        file.filename

    )


    file.save(filepath)


    try:

        converted_text = speech_to_text(
            filepath
        )


        return jsonify({

            "text":
            converted_text

        })


    except Exception as e:

        return jsonify({

            "text":
            f"Error: {e}"

        })


# =====================================================
# LIVE SPEECH PUNCTUATION
# =====================================================

@app.route(
    "/punctuate",
    methods=["POST"]
)
@login_required
def punctuate():

    data = request.get_json()


    if not data or "text" not in data:

        return jsonify({

            "text": ""

        })


    converted_text = data["text"].strip()


    if not converted_text:

        return jsonify({

            "text": ""

        })


    try:

        # Add punctuation

        converted_text = (
            punct_model
            .restore_punctuation(
                converted_text
            )
        )


        # Capitalize first letter

        if converted_text:

            converted_text = (

                converted_text[0].upper()

                + converted_text[1:]

            )


        # Capitalize after punctuation

        import re


        converted_text = re.sub(

            r'([.!?]\s+)([a-z])',

            lambda m:

            m.group(1)

            + m.group(2).upper(),

            converted_text

        )


        # Greeting comma

        converted_text = re.sub(

            r'^(Good morning|Good afternoon|Good evening)\s+everyone',

            r'\1, everyone',

            converted_text,

            flags=re.IGNORECASE

        )


        # Add final full stop

        if (

            converted_text

            and converted_text[-1]

            not in ".!?"

        ):

            converted_text += "."


        return jsonify({

            "text":
            converted_text

        })


    except Exception as e:

        print(
            "Punctuation Error:",
            e
        )


        return jsonify({

            "text":
            converted_text

        })


# =====================================================
# DOWNLOAD MP3
# =====================================================

@app.route(
    "/download-mp3",
    methods=["POST"]
)
@login_required
def download_mp3():

    converted_text = request.form.get(

        "text",
        ""

    ).strip()


    language = request.form.get(

        "language",
        "en"

    )


    if not converted_text:

        return (
            "Please enter some text."
        )


    try:

        tts = gTTS(

            text=converted_text,

            lang=language

        )


        file_path = os.path.join(

            "static",

            "speech.mp3"

        )


        tts.save(
            file_path
        )


        return send_file(

            file_path,

            as_attachment=True,

            download_name=
            "Speech2Text.mp3",

            mimetype=
            "audio/mpeg"

        )


    except Exception as e:

        return (
            f"Error: {str(e)}"
        )


# =====================================================
# REGISTER
# =====================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()


        email = request.form.get(
            "email",
            ""
        ).strip().lower()


        password = request.form.get(
            "password",
            ""
        )


        # Check empty fields

        if (
            not name
            or not email
            or not password
        ):

            return render_template(

                "register.html",

                error=
                "Please fill all fields."

            )


        # Check existing email

        existing_user = (
            User.query
            .filter_by(
                email=email
            )
            .first()
        )


        if existing_user:

            return render_template(

                "register.html",

                error=
                "Email already registered."

            )


        # Create user

        user = User(

            name=name,

            email=email,

            password=
            generate_password_hash(
                password
            ),

            role="user"

        )


        db.session.add(user)

        db.session.commit()
        


        return redirect(
            url_for("login")
        )


    return render_template(
        "register.html"
    )


## =====================================================
# LOGIN
# =====================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()


        password = request.form.get(
            "password",
            ""
        )


        user = (
            User.query
            .filter_by(
                email=email
            )
            .first()
        )


        # =================================================
        # CHECK LOGIN DETAILS
        # =================================================

        if (

            user

            and check_password_hash(

                user.password,

                password

            )

        ):

            # =================================================
            # SAVE LOGIN SESSION
            # =================================================

            session["user_id"] = user.id

            session["app_session_id"] = (
                APP_SESSION_ID
            )

            session["user_name"] = (
                user.name
            )

            session["email"] = (
                user.email
            )

            session["role"] = (
                user.role
            )


            # =================================================
            # CREATE DESKTOP FOLDER AFTER LOGIN
            # =================================================

            create_desktop_history_folder()


            # =================================================
            # ADMIN
            # =================================================

            if user.role == "admin":

                return redirect(
                    url_for(
                        "admin_dashboard"
                    )
                )


            # =================================================
            # NORMAL USER
            # =================================================

            return redirect(
                url_for("home")
            )


        # =================================================
        # INVALID LOGIN
        # =================================================

        return render_template(

            "login.html",

            error=
            "❌ Invalid email or password."

        )


    # =================================================
    # GET LOGIN PAGE
    # =================================================

    return render_template(
        "login.html"
    )


# =====================================================
# LOGOUT
# =====================================================

@app.route("/logout")
def logout():

    # =================================================
    # DELETE ENTIRE SPEECH2TEXT FOLDER
    # =================================================

    try:

        if os.path.exists(SPEECH2TEXT_DESKTOP_FOLDER):

            shutil.rmtree(
                SPEECH2TEXT_DESKTOP_FOLDER
            )

            print(
                "✅ Entire Speech2Text folder deleted."
            )

        else:

            print(
                "Speech2Text folder does not exist."
            )

    except Exception as e:

        print(
            "❌ Error deleting Speech2Text folder:",
            e
        )


    # =================================================
    # CLEAR LOGIN SESSION
    # =================================================

    session.clear()


    # =================================================
    # RETURN TO LOGIN
    # =================================================

    return redirect(
        url_for("login")
    )
# =====================================================
# SAVE HISTORY
# =====================================================

@app.route(
    "/save-history",
    methods=["POST"]
)
@login_required
def save_history():

    data = request.get_json()


    if not data:

        return jsonify({

            "success": False,

            "message":
            "No data received."

        })


    converted_text = data.get(

        "text",
        ""

    ).strip()


    source = data.get(

        "source",

        "Live Speech"

    )


    if not converted_text:

        return jsonify({

            "success": False,

            "message":
            "No text provided."

        })


    # =================================================
    # CHECK DUPLICATE
    # =================================================

    recent_record = (

        History.query

        .filter_by(

            user_id=
            session["user_id"],

            text=
            converted_text,

            source=
            source

        )

        .order_by(

            History.created_at.desc()

        )

        .first()

    )


    if recent_record:

        time_difference = (

            datetime.now()

            - recent_record.created_at

        ).total_seconds()


        if time_difference < 10:

            return jsonify({

                "success": True,

                "message":
                "Already saved to history."

            })

    # =================================================
    # SAVE HISTORY
    # =================================================

    try:

        record = History(

            user_id=
            session["user_id"],

            text=
            converted_text,

            source=
            source

        )


        db.session.add(record)

        db.session.commit()


        # =================================================
        # ALSO SAVE HISTORY TO DESKTOP
        # =================================================

        save_desktop_history(
            session.get("user_name", "User"),
            source,
            converted_text
        )


        return jsonify({

            "success": True,

            "message":
            "Saved to history."

        })


    except Exception as e:

        db.session.rollback()


        return jsonify({

            "success": False,

            "message":
            str(e)

        })


# =====================================================
# HISTORY PAGE
# =====================================================

@app.route("/history")
@login_required
def history():

    records = (

        History.query

        .filter_by(

            user_id=
            session["user_id"]

        )

        .order_by(

            History.created_at.desc()

        )

        .all()

    )


    return render_template(

        "history.html",

        records=records

    )


# =====================================================
# DELETE ONE HISTORY RECORD
# =====================================================

@app.route(
    "/delete-history/<int:id>",
    methods=["POST"]
)
@login_required
def delete_history(id):

    record = (

        History.query

        .filter_by(

            id=id,

            user_id=
            session["user_id"]

        )

        .first()

    )


    if record:

        db.session.delete(
            record
        )

        db.session.commit()


        return jsonify({

            "success": True

        })


    return jsonify({

        "success": False,

        "message":
        "Record not found."

    })

# =====================================================
# ADMIN DELETE HISTORY
# =====================================================

@app.route(
    "/admin/delete-history/<int:id>",
    methods=["POST"]
)
@admin_required
def admin_delete_history(id):

    record = History.query.get(id)

    if not record:

        return jsonify({
            "success": False,
            "message": "History record not found."
        })

    try:

        db.session.delete(record)

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "History deleted successfully."
        })

    except Exception as e:

        db.session.rollback()

        return jsonify({
            "success": False,
            "message": str(e)
        })
# =====================================================
# CLEAR USER HISTORY
# =====================================================

@app.route(
    "/clear-history",
    methods=["POST"]
)
@login_required
def clear_history():

    try:

        (

            History.query

            .filter_by(

                user_id=
                session["user_id"]

            )

            .delete()
            

        )


        db.session.commit()


        return jsonify({

            "success": True

        })


    except Exception as e:

        db.session.rollback()


        return jsonify({

            "success": False,

            "message":
            str(e)

        })


# =====================================================
# ADMIN DASHBOARD
# =====================================================

# =====================================================
# ADMIN DASHBOARD
# =====================================================

@app.route("/admin")
@admin_required
def admin_dashboard():

    return redirect(
        url_for("admin_users")
    )


# =====================================================
# ADMIN USERS PAGE
# =====================================================

@app.route("/admin/users")
@admin_required
def admin_users():

    users = (
        User.query
        .order_by(
            User.created_at.desc()
        )
        .all()
    )

    return render_template(
        "admin_users.html",
        users=users
    )


# =====================================================
# ADMIN HISTORY PAGE
# =====================================================

@app.route("/admin/history")
@admin_required
def admin_history():

    records = (
        History.query
        .order_by(
            History.created_at.desc()
        )
        .all()
    )

    return render_template(
        "admin_history.html",
        records=records
    )

# =====================================================
# DATABASE CREATION + MIGRATION
# =====================================================

with app.app_context():

    # Create tables if they don't exist

    db.create_all()


    # -------------------------------------------------
    # CHECK HISTORY TABLE
    # -------------------------------------------------

    try:

        with db.engine.connect() as connection:

            result = connection.execute(

                text(
                    "PRAGMA table_info(history)"
                )

            )


            columns = [

                row[1]

                for row in result

            ]


            # Add user_id if old database
            # does not have it

            if "user_id" not in columns:

                connection.execute(

                    text(

                        "ALTER TABLE history "
                        "ADD COLUMN user_id INTEGER"

                    )

                )

                connection.commit()


                print(
                    "Added user_id column to history table."
                )


    except Exception as e:

        print(
            "Database migration error:",
            e
        )


    # -------------------------------------------------
    # CREATE DEFAULT ADMIN
    # -------------------------------------------------

    existing_admin = (

        User.query

        .filter_by(

            email=
            "admin@gmail.com"

        )

        .first()

    )


    if not existing_admin:

        admin = User(

            name="Administrator",

            email="admin@gmail.com",

            password=
            generate_password_hash(
                "admin123"
            ),

            role="admin"

        )


        db.session.add(admin)

        db.session.commit()


        print(
            "Default admin account created."
        )


    else:

        print(
            "Admin account already exists."
        )


    print(
        "Database ready!"
    )
# =====================================================
# USER PROFILE
# =====================================================

@app.route("/profile")
@login_required
def profile():

    user = User.query.get(
        session["user_id"]
    )

    if not user:

        return redirect(
            url_for("login")
        )


    total_conversions = History.query.filter_by(
        user_id=user.id
    ).count()


    return render_template(
        "profile.html",
        user=user,
        total_conversions=total_conversions
    )
# =====================================================
# EDIT PROFILE
# =====================================================

@app.route("/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():

    user = User.query.get(
        session["user_id"]
    )

    if not user:
        return redirect(
            url_for("login")
        )


    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()


        if not name:

            return render_template(
                "edit_profile.html",
                user=user,
                error="Name cannot be empty."
            )


        user.name = name

        db.session.commit()


        return redirect(
            url_for("profile")
        )


    return render_template(
        "edit_profile.html",
        user=user
    )
# =====================================================
# CHANGE PASSWORD
# =====================================================

@app.route(
    "/change-password",
    methods=["GET", "POST"]
)
@login_required
def change_password():

    user = User.query.get(
        session["user_id"]
    )

    if not user:
        return redirect(
            url_for("login")
        )


    if request.method == "POST":

        current_password = request.form.get(
            "current_password",
            ""
        )

        new_password = request.form.get(
            "new_password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )


        # Check current password

        if not check_password_hash(
            user.password,
            current_password
        ):

            return render_template(
                "change_password.html",
                error="Current password is incorrect."
            )


        # Check password length

        if len(new_password) < 6:

            return render_template(
                "change_password.html",
                error="New password must contain at least 6 characters."
            )


        # Confirm password

        if new_password != confirm_password:

            return render_template(
                "change_password.html",
                error="New passwords do not match."
            )


        # Save password

        user.password = generate_password_hash(
            new_password
        )

        db.session.commit()


        return redirect(
            url_for("profile")
        )


    return render_template(
        "change_password.html"
    )
# =====================================================
# USER DASHBOARD
# =====================================================

@app.route("/dashboard")
@login_required
def dashboard():

    user = User.query.get(
        session["user_id"]
    )

    if not user:
        return redirect(
            url_for("login")
        )

    # Total conversions
    total_conversions = History.query.filter_by(
        user_id=user.id
    ).count()

    # Live Speech
    live_count = History.query.filter_by(
        user_id=user.id,
        source="Live Speech"
    ).count()

    # Upload Audio
    upload_count = History.query.filter_by(
        user_id=user.id,
        source="Upload Audio"
    ).count()

    # Text to Audio
    text_audio_count = History.query.filter_by(
        user_id=user.id,
        source="Text to Audio"
    ).count()

    # Recent history
    recent_records = History.query.filter_by(
        user_id=user.id
    ).order_by(
        History.id.desc()
    ).limit(5).all()

    return render_template(
        "dashboard.html",
        user=user,
        total_conversions=total_conversions,
        live_count=live_count,
        upload_count=upload_count,
        text_audio_count=text_audio_count,
        recent_records=recent_records
    )
# =====================================================
# RUN APPLICATION
# =====================================================

if __name__ == "__main__":



    app.run(
        debug=True
    )
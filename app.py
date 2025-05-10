import os
import json
import cloudinary
import cloudinary.uploader
import mysql.connector
from mysql.connector import Error
from flask_mail import Mail, Message
from flask import Flask, render_template, request, redirect, url_for, flash, session
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Configuración de subida
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Conexión a base de datos
def dbConnection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host = os.getenv("DB_HOST"),
            port = int(os.getenv("DB_PORT")),
            user = os.getenv("DB_USER"),
            passwd = os.getenv("DB_PASSWORD"),
            database = os.getenv("DB_NAME")
        )
    except Error as e:
        print(f"{e}")
        return None

    return connection

def closeConnection(connection, cursor):
    if connection.is_connected():
        cursor.close()
        connection.close()

# Configuración de subida    
cloudinary.config( 
    cloud_name = os.getenv("CLOUDINARY_USER"), 
    api_key = os.getenv("CLOUDINARY_API_KEY"), 
    api_secret = os.getenv("CLOUDINARY_API_SECRET"),
    secure = True
)

# Configuración de correo
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT"))
app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS") == "True"
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")

mail = Mail(app)

# Traer imagenes desde la base de datos
imagenes = []

def getData(index, database):
    connection = dbConnection()
    cursor = connection.cursor()
    sql = "SELECT * FROM " + f"{database}"
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        data = [result[index] for result in results]
    except:
        data = []
    finally:
        closeConnection(connection, cursor)

    return data

# ========= PÁGINAS PRINCIPALES =========

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/services")
def services():
    return render_template("services.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")
        try:
            msg = Message(
                subject=f"Nuevo mensaje de {name}",
                sender=email,
                recipients=[os.getenv("MAIL_USERNAME")],
                body=f"De: {name} <{email}>\n\n{message}"
            )
            mail.send(msg)
            flash("Tu mensaje fue enviado correctamente. ¡Gracias!", "success")
        except Exception as e:
            print("Error al enviar mensaje:", e)
            flash("Error al enviar mensaje. Intentá más tarde.", "error")
        return redirect(url_for("contact"))
    return render_template("contact.html")

# ========= ADMIN SIMPLE =========

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        clave = request.form.get("clave")
        if clave == os.getenv("ADMIN_KEY"):
            session["autorizado"] = True
            flash("Acceso autorizado ✅", "success")
            return redirect(url_for("home"))
        else:
            flash("Clave incorrecta ❌", "error")
    return render_template("admin.html")

@app.route("/logout")
def logout():
    session.pop("autorizado", None)
    flash("Sesión cerrada", "info")
    return redirect(url_for("home"))

# ========= TESTIMONIOS =========

@app.route("/testimonios")
def testimonios():
    try:
        with open("testimonios.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = []
    return render_template("testimonios.html", testimonios=data, autorizado=session.get("autorizado"))

@app.route("/agregar-testimonio", methods=["GET", "POST"])
def agregar_testimonio():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        mensaje = request.form.get("mensaje")
        if nombre and mensaje:
            try:
                with open("testimonios.json", "r+", encoding="utf-8") as f:
                    data = json.load(f)
                    data.append({"nombre": nombre, "mensaje": mensaje})
                    f.seek(0)
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except FileNotFoundError:
                with open("testimonios.json", "w", encoding="utf-8") as f:
                    json.dump([{"nombre": nombre, "mensaje": mensaje}], f, ensure_ascii=False, indent=2)
            flash("Gracias por compartir tu testimonio ❤️", "success")
            return redirect(url_for("testimonios"))
        else:
            flash("Por favor, completá todos los campos.", "error")
    return render_template("agregar_testimonio.html")

@app.route("/eliminar-testimonio/<int:index>", methods=["POST"])
def eliminar_testimonio(index):
    clave = request.form.get("clave")
    if clave != os.getenv("ADMIN_KEY"):
        flash("Clave incorrecta ❌", "error")
        return redirect(url_for("testimonios"))
    try:
        with open("testimonios.json", "r+", encoding="utf-8") as f:
            data = json.load(f)
            if 0 <= index < len(data):
                data.pop(index)
                f.seek(0)
                f.truncate()
                json.dump(data, f, ensure_ascii=False, indent=2)
                flash("Testimonio eliminado correctamente ✅", "success")
    except Exception as e:
        print("Error eliminando testimonio:", e)
        flash("Ocurrió un error al eliminar.", "error")
    return redirect(url_for("testimonios"))

@app.route("/editar-testimonio/<int:index>", methods=["GET", "POST"])
def editar_testimonio(index):
    try:
        with open("testimonios.json", "r+", encoding="utf-8") as f:
            data = json.load(f)
            if index < 0 or index >= len(data):
                flash("Testimonio no encontrado.", "error")
                return redirect(url_for("testimonios"))
            if request.method == "POST":
                data[index]["nombre"] = request.form.get("nombre")
                data[index]["mensaje"] = request.form.get("mensaje")
                f.seek(0)
                f.truncate()
                json.dump(data, f, ensure_ascii=False, indent=2)
                flash("Testimonio actualizado correctamente ✅", "success")
                return redirect(url_for("testimonios"))
            return render_template("editar_testimonio.html", testimonio=data[index])
    except Exception as e:
        print("Error editando testimonio:", e)
        flash("Error al editar testimonio", "error")
        return redirect(url_for("testimonios"))

# ========= RESULTADOS =========

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/resultados", methods=["GET"])
def resultados():
    imagenes = getData(1, "images")

    return render_template("resultados.html", imagenes=imagenes, autorizado=session.get("autorizado"))

@app.route("/admin/galeria", methods=["GET", "POST"])
def admin_galeria():
    if not session.get("autorizado"):
        return redirect(url_for("admin"))

    imagenes = getData(1, "images")

    if request.method == "POST":
        if 'imagen' not in request.files:
            flash("No se envió ninguna imagen.", "error")
            return redirect(url_for("admin_galeria"))

        file = request.files["imagen"]
        if file.filename == "":
            flash("No seleccionaste ninguna imagen.", "error")
            return redirect(url_for("admin_galeria"))

        if file and allowed_file(file.filename):
            response = cloudinary.uploader.upload(file)
            secure_url = response["secure_url"]

            connection = dbConnection()
            cursor = connection.cursor()
            try:
                sql = """INSERT INTO images (img_url) VALUES (%s)"""
                cursor.execute(sql, (secure_url,))
                connection.commit()

                flash("Imagen subida correctamente ✅", "success")
                imagenes.append(secure_url)
            except:
                connection.rollback()
            finally:
                closeConnection(connection, cursor)

            return redirect(url_for("admin_galeria"))
        else:
            flash("Formato no permitido. Solo PNG, JPG, JPEG y GIF.", "error")

    return render_template("admin_galeria.html", imagenes=imagenes)

@app.route("/admin/galeria/eliminar/<int:index>", methods=["GET", "POST"])
def eliminar_resultado(index):
    if not session.get("autorizado"):
        return redirect(url_for("admin"))

    imagenes = getData(1, "images")
    img_url = imagenes[index - 1]

    connection = dbConnection()
    cursor = connection.cursor()
    try:
        sql = """DELETE FROM images WHERE img_url = %s"""
        cursor.execute(sql, (img_url,))
        connection.commit()

        flash("Imagen eliminada correctamente ✅", "success")
    except Exception as e:
        print("Error eliminando imagen:", e)
        flash("Ocurrió un error al eliminar la imagen.", "error")
    finally:
        closeConnection(connection, cursor)

    return redirect(url_for("admin_galeria"))

@app.route("/faq")
def faq():
    return render_template("faq.html")

# ========= EJECUTAR =========

if __name__ == "__main__":
    app.run(debug=True)
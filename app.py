from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from database import conectar_bd

app = Flask(__name__)
app.secret_key = 'machuelos'  # Necesaria para mostrar mensajes flash


@app.route('/')
def inicio():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        contrasena = request.form['contrasena']
        
        conexion = conectar_bd()
        cursor = conexion.cursor()
        cursor.execute("SELECT rol FROM usuario WHERE correo = %s AND contraseña = %s", (correo, contrasena))
        resultado = cursor.fetchone()

        if resultado:
            rol = resultado[0]
            flash(f"Bienvenido, {rol}", "success")
            return redirect(url_for('dashboard'))  # Redirige a un panel de usuario
        else:
            flash("Correo o contraseña incorrectos", "danger")

        cursor.close()
        conexion.close()

    return render_template('login.html')

# Ruta para la página de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        correo = request.form['correo']
        contrasena = request.form['contrasena']

        conexion = conectar_bd()
        cursor = conexion.cursor()
        try:
            cursor.execute("""
                INSERT INTO usuario (nombre, apellido, correo, contraseña, rol)
                VALUES (%s, %s, %s, %s, 'medico')
            """, (nombre, apellido, correo, contrasena))
            conexion.commit()
            flash("Registro exitoso. Ahora puedes iniciar sesión.", "success")
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash(f"Error: {err}", "danger")
        finally:
            cursor.close()
            conexion.close()

    return render_template('register.html')

# Ruta para el dashboard
@app.route('/dashboard')
def dashboard():
    return "¡Bienvenido al Dashboard del médico!"

if __name__ == '__main__':
    app.run(debug=True)

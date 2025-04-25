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
    return render_template('dashboard.html')

@app.route('/dashboard/pacientes')
def pacientes():
    return render_template('pacientes.html')

@app.route('/dashboard/enfermedades')
def enfermedades():
    return render_template('enfermedades.html')


@app.route('/dashboard/diagnostico')
def diagnostico():
    return render_template('diagnostico.html')

@app.route('/dashboard/pruebas', methods=['GET', 'POST'])
def pruebas_view():
    conexion = conectar_bd()
    cursor = conexion.cursor()

    # Obtener enfermedades
    cursor.execute("SELECT id_enfermedad, nombre_enfermedad FROM enfermedad")
    enfermedades = cursor.fetchall()

    # Obtener pacientes
    cursor.execute("SELECT id_paciente, nombre FROM paciente")
    pacientes = cursor.fetchall()

    # Obtener pruebas
    cursor.execute("SELECT * FROM prueba_laboratorio")
    pruebas_laboratorio = cursor.fetchall()
    cursor.execute("SELECT * FROM prueba_post_mortem")
    pruebas_post_mortem = cursor.fetchall()

    # Manejo de formularios
    if request.method == 'POST':
        if 'agregar_laboratorio' in request.form:
            nombre_prueba = request.form['nombre_prueba_laboratorio']
            descripcion = request.form['descripcion_laboratorio']
            resultado = request.form['resultado_laboratorio']
            id_enfermedad = request.form['id_enfermedad_laboratorio']
            id_paciente = request.form.get('id_paciente_laboratorio') or None

            cursor.execute("""
                INSERT INTO prueba_laboratorio (nombre_prueba, descripcion, resultado, id_enfermedad, id_paciente)
                VALUES (%s, %s, %s, %s, %s)
            """, (nombre_prueba, descripcion, resultado, id_enfermedad, id_paciente))
            conexion.commit()
            flash("Prueba de laboratorio agregada exitosamente.", "success")

        elif 'agregar_postmortem' in request.form:
            nombre_prueba = request.form['nombre_prueba_postmortem']
            descripcion = request.form['descripcion_postmortem']
            resultado = request.form['resultado_postmortem']
            id_enfermedad = request.form['id_enfermedad_postmortem']

            cursor.execute("""
                INSERT INTO prueba_post_mortem (nombre_prueba, descripcion, resultado, id_enfermedad)
                VALUES (%s, %s, %s, %s)
            """, (nombre_prueba, descripcion, resultado, id_enfermedad))
            conexion.commit()
            flash("Prueba post-mortem agregada exitosamente.", "success")

    cursor.close()
    conexion.close()

    return render_template(
        'pruebas.html',
        pruebas_laboratorio=pruebas_laboratorio,
        pruebas_post_mortem=pruebas_post_mortem,
        enfermedades=[{'id_enfermedad': e[0], 'nombre_enfermedad': e[1]} for e in enfermedades],
        pacientes=[{'id_paciente': p[0], 'nombre': p[1]} for p in pacientes]
    )


# Eliminar prueba de laboratorio
@app.route('/eliminar_prueba_laboratorio/<int:id>', methods=['POST'])
def eliminar_prueba_laboratorio(id):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM prueba_laboratorio WHERE id_prueba_laboratorio = %s", (id,))
    conexion.commit()
    cursor.close()
    conexion.close()
    flash("Prueba de laboratorio eliminada.", "success")
    return redirect(url_for('pruebas_view'))

# Eliminar prueba post-mortem
@app.route('/eliminar_prueba_postmortem/<int:id>', methods=['POST'])
def eliminar_prueba_postmortem(id):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM prueba_post_mortem WHERE id_prueba_post = %s", (id,))
    conexion.commit()
    cursor.close()
    conexion.close()
    flash("Prueba post-mortem eliminada.", "success")
    return redirect(url_for('pruebas_view'))








if __name__ == '__main__':
    app.run(debug=True)

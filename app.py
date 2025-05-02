from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

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

@app.route('/dashboard/diagnostico', methods=['GET', 'POST'])
def diagnostico():
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)

    # Obtener datos del formulario si se hizo POST
    enfermedades_probables = []

    if request.method == 'POST':
        paciente_id = request.form['paciente']
        signos = request.form.getlist('signos')
        sintomas = request.form.getlist('sintomas')
        pruebas_laboratorio = request.form.getlist('pruebas_laboratorio')
        pruebas_postmortem = request.form.getlist('pruebas_postmortem')
        observaciones = request.form['observaciones']

        enfermedad_scores = {}

        # Función para contar coincidencias por enfermedad
        def contar_coincidencias(query, items):
            for item in items:
                cursor.execute(query, (item,))
                for row in cursor.fetchall():
                    enf_id = row['id_enfermedad']
                    enfermedad_scores[enf_id] = enfermedad_scores.get(enf_id, 0) + 1

        # Consultas para signos, síntomas, pruebas
        if signos:
            contar_coincidencias("SELECT id_enfermedad FROM enfermedad_signo WHERE id_signo = %s", signos)
        if sintomas:
            contar_coincidencias("SELECT id_enfermedad FROM enfermedad_sintoma WHERE id_sintoma = %s", sintomas)
        if pruebas_laboratorio:
            contar_coincidencias("SELECT id_enfermedad FROM enfermedad_prueba WHERE id_prueba_laboratorio = %s", pruebas_laboratorio)
        if pruebas_postmortem:
            contar_coincidencias("SELECT id_enfermedad FROM enfermedad_pruebapost WHERE id_prueba_post = %s", pruebas_postmortem)

        # Obtener las 3 enfermedades con mayor puntuación
        top_enfermedades = sorted(enfermedad_scores.items(), key=lambda x: x[1], reverse=True)[:3]

        # Guardar los diagnósticos
        for enfermedad_id, puntuacion in top_enfermedades:
            cursor.execute(
                "INSERT INTO diagnostico (id_paciente, id_enfermedad, descripcion_diagnostico) VALUES (%s, %s, %s)",
                (paciente_id, enfermedad_id, observaciones)
            )

        conexion.commit()

        # Obtener nombres de las enfermedades
        for enfermedad_id, _ in top_enfermedades:
            cursor.execute("SELECT nombre_enfermedad FROM enfermedad WHERE id_enfermedad = %s", (enfermedad_id,))
            nombre = cursor.fetchone()
            if nombre:
                enfermedades_probables.append(nombre['nombre_enfermedad'])

        flash("Diagnóstico generado correctamente.", "success")

    # Obtener datos para mostrar el formulario
    cursor.execute("SELECT id_paciente, nombre, apellido, fecha_nacimiento, genero, direccion FROM paciente")
    pacientes = cursor.fetchall()

    cursor.execute("""
        SELECT MIN(id_sintoma) AS id_sintoma, nombre_sintoma
        FROM sintoma
        GROUP BY nombre_sintoma
    """)
    sintomas = cursor.fetchall()

    cursor.execute("""
        SELECT MIN(id_signo) AS id_signo, nombre_signo
        FROM signo
        GROUP BY nombre_signo
    """)
    signos = cursor.fetchall()

    cursor.execute("SELECT id_prueba_laboratorio, nombre_prueba FROM prueba_laboratorio")
    pruebas_laboratorio = cursor.fetchall()

    cursor.execute("SELECT id_prueba_post, nombre_prueba FROM prueba_post_mortem")
    pruebas_postmortem = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template('diagnostico.html',
                           pacientes=pacientes,
                           signos=signos,
                           sintomas=sintomas,
                           pruebas_laboratorio=pruebas_laboratorio,
                           pruebas_postmortem=pruebas_postmortem,
                           enfermedades_probables=enfermedades_probables)



# Ruta para obtener los datos de un paciente por su ID (API)
@app.route('/api/paciente/<int:id>', methods=['GET'])
def get_paciente(id):
    conexion = conectar_bd()
    cursor = conexion.cursor()

    # Obtener datos del paciente
    cursor.execute("SELECT nombre, apellido, fecha_nacimiento, genero, direccion FROM paciente WHERE id_paciente = %s", (id,))
    paciente = cursor.fetchone()
    
    # Si no se encuentra el paciente, devolvemos error
    if not paciente:
        return jsonify({"error": "Paciente no encontrado"}), 404

    # Devolvemos los datos en formato JSON
    paciente_data = {
        "nombre": paciente[0],
        "apellido": paciente[1],
        "fecha_nacimiento": paciente[2].strftime('%Y-%m-%d') if paciente[2] else "",
        "genero": paciente[3],
        "direccion": paciente[4]
    }

    cursor.close()
    conexion.close()

    return jsonify(paciente_data)


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

@app.route('/editar_prueba_laboratorio/<int:id>', methods=['GET', 'POST'])
def editar_prueba_laboratorio(id):
    conexion = conectar_bd()
    cursor = conexion.cursor()

    if request.method == 'POST':
        nombre = request.form['nombre_prueba_laboratorio']
        descripcion = request.form['descripcion_laboratorio']
        resultado = request.form['resultado_laboratorio']
        id_enfermedad = request.form['id_enfermedad_laboratorio']
        id_paciente = request.form.get('id_paciente_laboratorio') or None

        cursor.execute("""
            UPDATE prueba_laboratorio
            SET nombre_prueba = %s, descripcion = %s, resultado = %s, id_enfermedad = %s, id_paciente = %s
            WHERE id_prueba_laboratorio = %s
        """, (nombre, descripcion, resultado, id_enfermedad, id_paciente, id))
        conexion.commit()
        flash("Prueba de laboratorio actualizada.", "success")
        return redirect(url_for('pruebas_view'))
    
    # Si es GET, obtener datos actuales de la prueba
    cursor.execute("SELECT * FROM prueba_laboratorio WHERE id_prueba_laboratorio = %s", (id,))
    prueba = cursor.fetchone()

    cursor.execute("SELECT id_enfermedad, nombre_enfermedad FROM enfermedad")
    enfermedades = cursor.fetchall()
    cursor.execute("SELECT id_paciente, nombre FROM paciente")
    pacientes = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template('editar_laboratorio.html', prueba=prueba, enfermedades=enfermedades, pacientes=pacientes)


@app.route('/editar_prueba_postmortem/<int:id>', methods=['GET', 'POST'])
def editar_prueba_postmortem(id):
    conexion = conectar_bd()
    cursor = conexion.cursor()

    if request.method == 'POST':
        nombre = request.form['nombre_prueba_postmortem']
        descripcion = request.form['descripcion_postmortem']
        resultado = request.form['resultado_postmortem']
        id_enfermedad = request.form['id_enfermedad_postmortem']

        cursor.execute("""
            UPDATE prueba_post_mortem
            SET nombre_prueba = %s, descripcion = %s, resultado = %s, id_enfermedad = %s
            WHERE id_prueba_post = %s
        """, (nombre, descripcion, resultado, id_enfermedad, id))
        conexion.commit()
        flash("Prueba post-mortem actualizada.", "success")
        return redirect(url_for('pruebas_view'))

    cursor.execute("SELECT * FROM prueba_post_mortem WHERE id_prueba_post = %s", (id,))
    prueba = cursor.fetchone()

    cursor.execute("SELECT id_enfermedad, nombre_enfermedad FROM enfermedad")
    enfermedades = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template('editar_postmortem.html', prueba=prueba, enfermedades=enfermedades)


if __name__ == '__main__':
    app.run(debug=True)
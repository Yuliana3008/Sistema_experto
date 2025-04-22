import mysql.connector

# Conectar a la base de datos MySQL
def conectar_bd():
    return mysql.connector.connect(
        host="localhost",
        user="root",              # Cambia esto si tu usuario no es root
        password="machuelos", # Cambia esto si tienes otra contraseña
        database="sistema_experto" # Nombre de tu base de datos
    )

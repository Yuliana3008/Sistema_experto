import mysql.connector

# Conectar a la base de datos MySQL
def conectar_bd():
    return mysql.connector.connect(
        host=" sbcknowledgebase.ct8ocu8yqcht.us-east-2.rds.amazonaws.com",
        user="sbcuser",              # Cambia esto si tu usuario no es root
        password="Ic170799.1", # Cambia esto si tienes otra contraseña
        database="sistema_experto" # Nombre de tu base de datos
    )

 # Verificamos si la conexión fue exitosa
    if connection.is_connected():
        print("Conexión exitosa a la base de datos.")
      


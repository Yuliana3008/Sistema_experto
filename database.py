import mysql.connector

# Conectar a la base de datos MySQL
def conectar_bd():
    return mysql.connector.connect(
        host=" sbcknowledgebase.ct8ocu8yqcht.us-east-2.rds.amazonaws.com",
        user="sbcuser",            
        password="Ic170799.1", 
        database="sistema_experto" 
    )


    if connection.is_connected():
        print("Conexión exitosa a la base de datos.")
      


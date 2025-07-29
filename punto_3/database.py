import sqlite3
import os

def create_connection(db_file):
    """
    Establece una conexión con la base de datos SQLite.

    Args:
        db_file (str): Ruta al archivo de la base de datos SQLite.

    Returns:
        connection object: Objeto de conexión si es exitoso, None en caso de error.
    """
    connection = None
    try:
        os.makedirs(os.path.dirname(db_file), exist_ok=True)
        connection = sqlite3.connect(db_file)
        print(f"Conexión a SQLite exitosa: {db_file}")
    except sqlite3.Error as e:
        print(f"Error al conectar a SQLite: {e}")
    return connection

def execute_query(connection, query, data=None):
    """
    Ejecuta una consulta SQL en la base de datos.

    Args:
        connection (connection object): Objeto de conexión a la base de datos.
        query (str): Consulta SQL a ejecutar.
        data (tuple, optional): Datos a insertar en la consulta (para consultas parametrizadas).

    Returns:
        tuple: Las filas resultantes si la consulta es un SELECT, True para otras operaciones, False en caso de error.
    """
    cursor = connection.cursor()
    try:
        if data:
            cursor.execute(query, data)
        else:
            cursor.execute(query)
        
        if query.strip().upper().startswith("SELECT"):
            return cursor.fetchall()
        connection.commit()
        #print("Consulta ejecutada exitosamente")
        return True
    except sqlite3.Error as e:
        print(f"Error al ejecutar la consulta: {e}")
        return False
    finally:
        cursor.close()

def close_connection(connection):
    """
    Cierra la conexión con la base de datos.

    Args:
        connection (connection object): Objeto de conexión a la base de datos.
    """
    if connection:
        connection.close()
        print("Conexión a SQLite cerrada")

def create_table_saldos_clientes_if_not_exists(connection):
    """
    Crea la tabla `saldos_clientes` en la base de datos si no existe.

    Args:
        connection (connection object): Objeto de conexión a la base de datos.
    """
    create_table_query = """
    CREATE TABLE IF NOT EXISTS saldos_clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        identificacion TEXT NOT NULL,
        fecha DATE,
        saldo DECIMAL
    );
    """
    if execute_query(connection, create_table_query):
        print("Tabla 'saldos_clientes' verificada/creada exitosamente.")

def create_table_retiros_if_not_exists(connection):
    """
    Crea la tabla `retiros` en la base de datos si no existe.

    Args:
        connection (connection object): Objeto de conexión a la base de datos.
    """
    create_table_query = """
    CREATE TABLE IF NOT EXISTS retiros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        identificacion TEXT,
        fecha_retiro DATE
    );
    """
    if execute_query(connection, create_table_query):
        print("Tabla 'retiros' verificada/creada exitosamente.")

def create_debt_streaks_table_if_not_exists(connection):
    """
    Crea la tabla `debt_streaks_results` en la base de datos si no existe.

    Args:
        connection (connection object): Objeto de conexión a la base de datos.
    """
    create_table_query = """
    CREATE TABLE IF NOT EXISTS debt_streaks_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        identificacion TEXT NOT NULL,
        racha INTEGER,
        fecha_fin DATE,
        nivel TEXT
    );
    """
    if execute_query(connection, create_table_query):
        print("Tabla 'debt_streaks_results' verificada/creada exitosamente.") 
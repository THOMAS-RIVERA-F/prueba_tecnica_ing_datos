import sqlite3
import os
from config import DB_FILE

def check_database():
    if not os.path.exists(DB_FILE):
        print(f"El archivo de la base de datos no existe: {DB_FILE}")
        return

    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Verificar tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("\n--- Tablas en la base de datos ---")
        if tables:
            for table in tables:
                print(f"- {table[0]}")
        else:
            print("No se encontraron tablas en la base de datos.")

        # Verificar esquema de saldos_clientes si existe
        if ('saldos_clientes',) in tables:
            print("\n--- Esquema de la tabla saldos_clientes ---")
            cursor.execute("PRAGMA table_info(saldos_clientes);")
            schema = cursor.fetchall()
            for col in schema:
                print(f"- Nombre: {col[1]}, Tipo: {col[2]}, Nulo: {col[3]}, PK: {col[5]}")
        else:
            print("La tabla 'saldos_clientes' no existe.")

    except sqlite3.Error as e:
        print(f"Error al conectar o consultar la base de datos: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_database() 
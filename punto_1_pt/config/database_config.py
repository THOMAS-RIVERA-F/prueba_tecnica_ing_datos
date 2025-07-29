import sqlite3
import os
from datetime import datetime

DATABASE_PATH = 'database/phone_numbers.db'

def create_database():
    """
    Crea la base de datos SQLite y las tablas necesarias si no existen.
    """
    # Crear directorio de base de datos si no existe
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Crear tabla para números de teléfono confiables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS phone_numbers_trusted (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_cliente TEXT NOT NULL,
            nombre TEXT NOT NULL,
            celular TEXT NOT NULL,
            celular_limpio TEXT NOT NULL UNIQUE,
            tipo_numero TEXT NOT NULL,
            fecha_registro TEXT NOT NULL,
            canal_obtencion TEXT NOT NULL,
            consentimiento_contacto BOOLEAN NOT NULL,
            fecha_procesamiento TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Crear tabla para auditoría de procesamiento
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processing_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT NOT NULL,
            total_records_input INTEGER NOT NULL,
            total_records_output INTEGER NOT NULL,
            records_removed INTEGER NOT NULL,
            duplicates_removed INTEGER NOT NULL,
            invalid_numbers_removed INTEGER NOT NULL,
            processing_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL
        )
    ''')
    
    # Crear índices para optimizar consultas
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_celular_limpio ON phone_numbers_trusted(celular_limpio)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_id_cliente ON phone_numbers_trusted(id_cliente)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_fecha_procesamiento ON phone_numbers_trusted(fecha_procesamiento)')
    
    conn.commit()
    conn.close()
    print(f"Base de datos creada exitosamente en: {DATABASE_PATH}")

def get_connection():
    """
    Retorna una conexión a la base de datos SQLite.
    """
    return sqlite3.connect(DATABASE_PATH)

if __name__ == "__main__":
    create_database() 
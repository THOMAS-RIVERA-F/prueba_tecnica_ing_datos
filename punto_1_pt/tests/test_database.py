import pytest
import sqlite3
import os
import tempfile
import sys
import time
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))

from database_config import DATABASE_PATH

class TestDatabase:
    
    @pytest.fixture
    def temp_db(self):
        """Fixture para crear una base de datos temporal para las pruebas"""
        # Crear un archivo temporal para la base de datos de prueba
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db_path = temp_file.name
        temp_file.close()
        
        # Crear la base de datos temporal directamente
        conn = sqlite3.connect(temp_db_path)
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
        
        yield temp_db_path
        
        # Limpiar después de la prueba
        # Esperar un poco para asegurar que todas las conexiones se cierren
        time.sleep(0.1)
        try:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)
        except PermissionError:
            # Si no se puede eliminar, intentar más tarde
            pass
    
    def test_database_creation(self, temp_db):
        """Prueba que la base de datos se cree correctamente"""
        assert os.path.exists(temp_db)
        
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Verificar que las tablas existan
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        assert 'phone_numbers_trusted' in tables
        assert 'processing_audit' in tables
        
        conn.close()
    
    def test_phone_numbers_table_structure(self, temp_db):
        """Prueba la estructura de la tabla phone_numbers_trusted"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(phone_numbers_trusted)")
        columns = [row[1] for row in cursor.fetchall()]
        
        expected_columns = [
            'id', 'id_cliente', 'nombre', 'celular', 'celular_limpio',
            'tipo_numero', 'fecha_registro', 'canal_obtencion',
            'consentimiento_contacto', 'fecha_procesamiento',
            'created_at', 'updated_at'
        ]
        
        for col in expected_columns:
            assert col in columns
        
        conn.close()
    
    def test_insert_phone_number(self, temp_db):
        """Prueba insertar un número de teléfono en la base de datos"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO phone_numbers_trusted 
            (id_cliente, nombre, celular, celular_limpio, tipo_numero, 
             fecha_registro, canal_obtencion, consentimiento_contacto, fecha_procesamiento)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('C0001', 'Cliente Test', '3001234567', '+573001234567', 'móvil',
              '2024-01-01', 'Web', True, '2024-01-01 10:00:00'))
        
        conn.commit()
        
        # Verificar que se insertó correctamente
        cursor.execute("SELECT * FROM phone_numbers_trusted WHERE id_cliente = 'C0001'")
        result = cursor.fetchone()
        
        assert result is not None
        assert result[1] == 'C0001'  # id_cliente
        assert result[2] == 'Cliente Test'  # nombre
        assert result[4] == '+573001234567'  # celular_limpio
        
        conn.close()
    
    def test_unique_constraint_celular_limpio(self, temp_db):
        """Prueba que la restricción UNIQUE en celular_limpio funcione"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Insertar primer registro
        cursor.execute('''
            INSERT INTO phone_numbers_trusted 
            (id_cliente, nombre, celular, celular_limpio, tipo_numero, 
             fecha_registro, canal_obtencion, consentimiento_contacto, fecha_procesamiento)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('C0001', 'Cliente 1', '3001234567', '+573001234567', 'móvil',
              '2024-01-01', 'Web', True, '2024-01-01 10:00:00'))
        
        conn.commit()
        
        # Intentar insertar segundo registro con el mismo celular_limpio
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute('''
                INSERT INTO phone_numbers_trusted 
                (id_cliente, nombre, celular, celular_limpio, tipo_numero, 
                 fecha_registro, canal_obtencion, consentimiento_contacto, fecha_procesamiento)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('C0002', 'Cliente 2', '3001234567', '+573001234567', 'móvil',
                  '2024-01-01', 'Web', True, '2024-01-01 10:00:00'))
            conn.commit()
        
        conn.close()
    
    def test_processing_audit_table(self, temp_db):
        """Prueba la funcionalidad de la tabla de auditoría"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO processing_audit 
            (batch_id, total_records_input, total_records_output, records_removed, 
             duplicates_removed, invalid_numbers_removed, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('batch_001', 100, 85, 15, 5, 10, 'SUCCESS'))
        
        conn.commit()
        
        cursor.execute("SELECT * FROM processing_audit WHERE batch_id = 'batch_001'")
        result = cursor.fetchone()
        
        assert result is not None
        assert result[1] == 'batch_001'  # batch_id
        assert result[2] == 100  # total_records_input
        assert result[3] == 85   # total_records_output
        assert result[8] == 'SUCCESS'  # status (índice corregido)
        
        conn.close()
    
    def test_indexes_exist(self, temp_db):
        """Prueba que los índices se hayan creado correctamente"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        expected_indexes = [
            'idx_celular_limpio',
            'idx_id_cliente', 
            'idx_fecha_procesamiento'
        ]
        
        for idx in expected_indexes:
            assert idx in indexes
        
        conn.close() 
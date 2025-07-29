import pandas as pd
import phonenumbers
import sqlite3
import uuid
from datetime import datetime
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))

from database_config import create_database, get_connection

def clean_phone_numbers(df, phone_column='celular'):
    """
    Limpia y estandariza los números de teléfono en un DataFrame,
    manteniendo las demás columnas intactas.
    - Asegura que la columna de teléfono es string y maneja nulos/vacíos.
    - Estandariza a formato E.164 (+CCNNNNNNNNN) solo para números móviles colombianos válidos.
    - Elimina duplicados y filas con números inválidos/vacíos.
    """
    df_cleaned = df.copy(deep=True)
    df_cleaned = df_cleaned.reset_index(drop=True)

    # Asegurar que la columna de números de teléfono sea de tipo string y manejar valores nulos/vacíos
    df_cleaned[phone_column] = df_cleaned[phone_column].astype(str).fillna('').str.strip()
    df_cleaned = df_cleaned[df_cleaned[phone_column] != '']
    df_cleaned = df_cleaned.reset_index(drop=True)

    # Función para estandarizar el número de teléfono
    def standardize_number(phone_str):
        try:
            parsed_number = phonenumbers.parse(phone_str, "CO")
            if phonenumbers.is_valid_number(parsed_number) and phonenumbers.number_type(parsed_number) == phonenumbers.PhoneNumberType.MOBILE:
                return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
            else:
                return None # No es un número válido o no es móvil
        except phonenumbers.NumberParseException:
            return None # Error de parseo

    df_cleaned['celular_limpio'] = df_cleaned[phone_column].apply(standardize_number)
    df_cleaned = df_cleaned.dropna(subset=['celular_limpio'])
    df_cleaned = df_cleaned.drop_duplicates(subset=['celular_limpio'])
    df_cleaned = df_cleaned.reset_index(drop=True)

    return df_cleaned

def save_to_database(df_cleaned, batch_id, processing_stats):
    """
    Guarda los datos limpios en la base de datos SQLite y registra auditoría.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Agregar fecha de procesamiento
        current_time = datetime.now().isoformat()
        
        # Insertar datos limpios en la tabla principal
        for _, row in df_cleaned.iterrows():
            cursor.execute('''
                INSERT OR REPLACE INTO phone_numbers_trusted 
                (id_cliente, nombre, celular, celular_limpio, tipo_numero, 
                 fecha_registro, canal_obtencion, consentimiento_contacto, fecha_procesamiento)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row['id_cliente'], row['nombre'], row['celular'], row['celular_limpio'],
                row['tipo_numero'], row['fecha_registro'], row['canal_obtencion'],
                bool(row['consentimiento_contacto']), current_time
            ))
        
        # Insertar registro de auditoría
        cursor.execute('''
            INSERT INTO processing_audit 
            (batch_id, total_records_input, total_records_output, records_removed, 
             duplicates_removed, invalid_numbers_removed, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            batch_id,
            processing_stats['total_input'],
            processing_stats['total_output'],
            processing_stats['records_removed'],
            processing_stats['duplicates_removed'],
            processing_stats['invalid_removed'],
            'SUCCESS'
        ))
        
        conn.commit()
        conn.close()
        
        print(f"Datos guardados exitosamente en la base de datos")
        print(f"Registros procesados: {processing_stats['total_output']}/{processing_stats['total_input']}")
        
    except Exception as e:
        print(f"Error al guardar en la base de datos: {e}")
        # Intentar registrar el error en auditoría
        try:
            cursor.execute('''
                INSERT INTO processing_audit 
                (batch_id, total_records_input, total_records_output, records_removed, 
                 duplicates_removed, invalid_numbers_removed, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                batch_id, processing_stats['total_input'], 0, 0, 0, 0, f'ERROR: {str(e)}'
            ))
            conn.commit()
        except:
            pass
        finally:
            if conn:
                conn.close()

def process_phone_data(input_file='input/raw_numeros.csv', output_file='output/cleaned_numeros.csv'):
    """
    Procesa completamente los datos de teléfono: carga, limpia, guarda en CSV y BD.
    """
    # Generar ID único para este lote de procesamiento
    batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    
    print(f"Iniciando procesamiento de datos - Batch ID: {batch_id}")
    
    # Cargar datos crudos
    try:
        raw_df = pd.read_csv(input_file, dtype={'celular': str})
        print(f"Datos cargados: {len(raw_df)} registros desde {input_file}")
    except Exception as e:
        print(f"Error al cargar datos: {e}")
        return
    
    total_input = len(raw_df)
    print(f"\n--- Datos crudos (primeras 5 filas) ---")
    print(raw_df.head())
    
    # Limpiar datos
    print(f"\nIniciando limpieza de datos...")
    cleaned_df = clean_phone_numbers(raw_df, phone_column='celular')
    
    total_output = len(cleaned_df)
    records_removed = total_input - total_output
    
    # Calcular estadísticas detalladas
    # Números inválidos (incluye vacíos y que no pasaron validación)
    df_with_numbers = raw_df[raw_df['celular'].astype(str).str.strip() != '']
    df_with_numbers['celular_test'] = df_with_numbers['celular'].apply(
        lambda x: phonenumbers.format_number(phonenumbers.parse(str(x), "CO"), phonenumbers.PhoneNumberFormat.E164)
        if phonenumbers.is_valid_number(phonenumbers.parse(str(x), "CO")) and 
           phonenumbers.number_type(phonenumbers.parse(str(x), "CO")) == phonenumbers.PhoneNumberType.MOBILE
        else None
    )
    
    valid_numbers = df_with_numbers.dropna(subset=['celular_test'])
    duplicates_removed = len(valid_numbers) - len(valid_numbers.drop_duplicates(subset=['celular_test']))
    invalid_removed = total_input - len(valid_numbers) - duplicates_removed
    
    processing_stats = {
        'total_input': total_input,
        'total_output': total_output,
        'records_removed': records_removed,
        'duplicates_removed': duplicates_removed,
        'invalid_removed': invalid_removed
    }
    
    print(f"\nEstadísticas de procesamiento:")
    print(f"   Registros de entrada: {total_input}")
    print(f"   Registros de salida: {total_output}")
    print(f"   Registros eliminados: {records_removed}")
    print(f"   Duplicados eliminados: {duplicates_removed}")
    print(f"   Números inválidos eliminados: {invalid_removed}")
    
    print(f"\n--- Datos limpios y estandarizados (primeras 5 filas) ---")
    print(cleaned_df.head())
    
    # Guardar en CSV
    try:
        cleaned_df.to_csv(output_file, index=False)
        print(f"Dataset limpio guardado en: {output_file}")
    except Exception as e:
        print(f"Error al guardar CSV: {e}")
    
    # Crear base de datos si no existe
    create_database()
    
    # Guardar en base de datos
    save_to_database(cleaned_df, batch_id, processing_stats)
    
    return cleaned_df, processing_stats

if __name__ == "__main__":
    process_phone_data()

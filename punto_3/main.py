from database import create_connection, close_connection, create_table_saldos_clientes_if_not_exists, create_table_retiros_if_not_exists, create_debt_streaks_table_if_not_exists
from logic import (
    read_excel_data,
    insert_data_into_db,
    insert_retiros_data_into_db,
    classify_debt_levels,
    fill_missing_saldos_with_n0,
    find_longest_debt_streak,
    export_results_to_csv
)
from config import DB_FILE, EXCEL_FILE_PATH, EXCEL_SHEET_HISTORIA, EXCEL_SHEET_RETIROS, CSV_OUTPUT_DIR, CSV_FILE_NAME
import os
import argparse
import pandas as pd

def main():
    parser = argparse.ArgumentParser(description="Procesa saldos de clientes y clasifica niveles de deuda.")
    parser.add_argument('--fecha_base', type=str, help='Fecha base en formato YYYY-MM-DD para el análisis.', required=True)
    parser.add_argument('--min_racha', type=int, default=1, help='Longitud mínima de la racha de deuda.')
    args = parser.parse_args()

    # Eliminar la base de datos existente para volver a crearla
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"Base de datos existente eliminada: {DB_FILE}")

    # 1. Establecer conexión con la base de datos
    conn = create_connection(DB_FILE)

    if conn:
        try:
            # 2. Leer los datos de la hoja 'historia' del archivo Excel y crear la tabla 'saldos_clientes' en la base de datos si no existe
            df_historia = read_excel_data(EXCEL_FILE_PATH, sheet_name=EXCEL_SHEET_HISTORIA)

            if df_historia is not None:
                create_table_saldos_clientes_if_not_exists(conn)
                insert_data_into_db(conn, df_historia)
            else:
                print("No se pudieron leer los datos de la hoja 'historia' del archivo Excel.")

            # 3. Leer los datos de la hoja 'retiros' del archivo Excel
            df_retiros = read_excel_data(EXCEL_FILE_PATH, sheet_name=EXCEL_SHEET_RETIROS)

            if df_retiros is not None:
                create_table_retiros_if_not_exists(conn)
                insert_retiros_data_into_db(conn, df_retiros)
            else:
                print("No se pudieron leer los datos de la hoja 'retiros' del archivo Excel.")

            # Crear la tabla de resultados de rachas
            create_debt_streaks_table_if_not_exists(conn)

            # 4. Rellenar saldos faltantes con N0 y considerar fechas de retiro
            fill_missing_saldos_with_n0(conn, fecha_base=pd.to_datetime(args.fecha_base))

            # 5. Identificar y mostrar las rachas de deuda y obtener los resultados
            results = find_longest_debt_streak(conn, args.fecha_base, args.min_racha)

            # 6. Exportar los resultados a un archivo CSV
            export_results_to_csv(results, CSV_OUTPUT_DIR, CSV_FILE_NAME)

        finally:
            # 4. Cerrar la conexión con la base de datos
            close_connection(conn)
    else:
        print("No se pudo establecer la conexión a la base de datos.")

if __name__ == "__main__":
    main() 
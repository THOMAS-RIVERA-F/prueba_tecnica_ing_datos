import pandas as pd
from database import execute_query, create_debt_streaks_table_if_not_exists
import os
import csv

def read_excel_data(file_path, sheet_name=None):
    """
    Lee los datos del archivo Excel.

    Args:
        file_path (str): Ruta del archivo Excel.
        sheet_name (str, optional): Nombre de la hoja a leer. Si es None, lee la primera hoja.

    Returns:
        DataFrame: DataFrame de pandas con los datos del Excel.
    """
    try:
        if sheet_name:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            print(f"Columnas del archivo Excel: {df.columns.tolist()}")
            print(f"Datos leídos de {file_path} (hoja '{sheet_name}') exitosamente.")
        else:
            df = pd.read_excel(file_path)
            print(f"Columnas del archivo Excel: {df.columns.tolist()}")
            print(f"Datos leídos de {file_path} exitosamente.")
        return df
    except Exception as e:
        print(f"Error al leer el archivo Excel (hoja 'historia'): {e}")
        return None

def get_client_first_appearance_and_retiro_dates(connection):
    query = """
    SELECT
        s.identificacion,
        MIN(s.fecha) as first_appearance_date,
        r.fecha_retiro
    FROM
        saldos_clientes s
    LEFT JOIN
        retiros r ON s.identificacion = r.identificacion
    GROUP BY
        s.identificacion, r.fecha_retiro;
    """
    results = execute_query(connection, query)
    if results:
        return {row[0]: {'first_appearance': pd.to_datetime(row[1]), 'fecha_retiro': pd.to_datetime(row[2]) if row[2] else None} for row in results}
    return {}

def get_all_months_between(start_date, end_date):
    months = []
    current_date = start_date.replace(day=1)
    while current_date <= end_date:
        months.append(current_date)
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    return months

def fill_missing_saldos_with_n0(connection, fecha_base=None):
    print("\n--- Rellenando saldos faltantes con N0 ---")
    client_dates_info = get_client_first_appearance_and_retiro_dates(connection)

    if not fecha_base:
        query_max_date = "SELECT MAX(fecha) FROM saldos_clientes;"
        max_date_result = execute_query(connection, query_max_date)
        if max_date_result and max_date_result[0][0]:
            fecha_base = pd.to_datetime(max_date_result[0][0])
        else:
            print("No se pudo determinar la fecha base. Saliendo del rellenado de saldos.")
            return

    for identificacion, dates_info in client_dates_info.items():
        first_appearance = dates_info['first_appearance']
        fecha_retiro = dates_info['fecha_retiro']

        all_months_for_client = get_all_months_between(first_appearance, fecha_base)

        # Obtener saldos existentes para el cliente
        query_existing_saldos = "SELECT fecha, saldo FROM saldos_clientes WHERE identificacion = ?;"
        existing_saldos_raw = execute_query(connection, query_existing_saldos, (identificacion,))
        existing_saldos = {pd.to_datetime(row[0]).replace(day=1): row[1] for row in existing_saldos_raw}

        for month_date in all_months_for_client:
            # Si el cliente no tiene un saldo para este mes y la fecha_base no es posterior a la fecha_retiro
            if month_date not in existing_saldos:
                should_fill_n0 = True
                if fecha_retiro and month_date > fecha_retiro:
                    should_fill_n0 = False

                if should_fill_n0:
                    # Insertar saldo N0 (0) para el mes faltante
                    insert_query = "INSERT INTO saldos_clientes (identificacion, fecha, saldo) VALUES (?, ?, ?);"
                    if not execute_query(connection, insert_query, (identificacion, month_date.strftime('%Y-%m-%d'), 0)):
                        print(f"Error al insertar saldo N0 para {identificacion} en {month_date.strftime('%Y-%m-%d')}")
    print("Relleno de saldos faltantes completado.")

def get_debt_level_classification_query():
    return """
    SELECT
        identificacion,
        fecha,
        saldo,
        CASE
            WHEN saldo >= 0 AND saldo < 300000 THEN 'N0'
            WHEN saldo >= 300000 AND saldo < 1000000 THEN 'N1'
            WHEN saldo >= 1000000 AND saldo < 3000000 THEN 'N2'
            WHEN saldo >= 3000000 AND saldo < 5000000 THEN 'N3'
            WHEN saldo >= 5000000 THEN 'N4'
            ELSE 'Desconocido'
        END as nivel_deuda
    FROM
        saldos_clientes
    ORDER BY
        identificacion, fecha;
    """

def classify_debt_levels(connection):
    """
    Genera una consulta que clasifica los saldos por niveles de deuda y los muestra.

    Args:
        connection (connection object): Objeto de conexión a la base de datos.
    """
    query = get_debt_level_classification_query()
    results = execute_query(connection, query)
    if results:
        print("\n--- Niveles de Deuda ---")
        for row in results:
            print(f"Identificacion: {row[0]}, Fecha: {row[1]}, Saldo: {row[2]}, Nivel de Deuda: {row[3]}")
    else:
        print("No se encontraron datos para clasificar.")

def find_longest_debt_streak(connection, fecha_base_str, min_racha_length):
    print(f"\n--- Identificando rachas de deuda para fecha_base (inicio): {fecha_base_str} y racha mínima: {min_racha_length} ---")

    fecha_base = pd.to_datetime(fecha_base_str)

    # Obtener la fecha máxima en la base de datos para no buscar en el futuro
    query_max_db_date = "SELECT MAX(fecha) FROM saldos_clientes;"
    max_db_date_result = execute_query(connection, query_max_db_date)
    max_db_date = None
    if max_db_date_result and max_db_date_result[0][0]:
        max_db_date = pd.to_datetime(max_db_date_result[0][0])
    
    if max_db_date is None or fecha_base > max_db_date:
        print(f"La fecha base ({fecha_base_str}) es posterior a la fecha máxima de datos disponibles en la base de datos ({max_db_date.strftime('%Y-%m-%d') if max_db_date else 'N/A'}). No se pueden encontrar rachas.")
        return

    # Paso 1: Obtener todos los saldos clasificados desde la fecha_base hasta la fecha máxima en la DB
    query_classified_saldos = f"""
    SELECT
        identificacion,
        fecha,
        CASE
            WHEN saldo >= 0 AND saldo < 300000 THEN 'N0'
            WHEN saldo >= 300000 AND saldo < 1000000 THEN 'N1'
            WHEN saldo >= 1000000 AND saldo < 3000000 THEN 'N2'
            WHEN saldo >= 3000000 AND saldo < 5000000 THEN 'N3'
            WHEN saldo >= 5000000 THEN 'N4'
            ELSE 'Desconocido'
        END as nivel_deuda
    FROM
        saldos_clientes
    WHERE
        fecha >= '{fecha_base.strftime('%Y-%m-%d')}' AND fecha <= '{max_db_date.strftime('%Y-%m-%d')}'
    ORDER BY
        identificacion, fecha;
    """

    classified_saldos = execute_query(connection, query_classified_saldos)

    if not classified_saldos:
        print("No se encontraron datos clasificados para la fecha base y el rango especificados.")
        return
    
    # Crear la tabla de resultados de rachas si no existe
    create_debt_streaks_table_if_not_exists(connection)
    # Limpiar resultados anteriores en la tabla de rachas
    execute_query(connection, "DELETE FROM debt_streaks_results;")

    # Procesar rachas por cliente
    client_streaks = {}
    for row in classified_saldos:
        identificacion, fecha_str, nivel_deuda = row
        fecha = pd.to_datetime(fecha_str)

        if identificacion not in client_streaks:
            client_streaks[identificacion] = []

        # Agrupar por nivel de deuda para encontrar rachas
        if not client_streaks[identificacion] or \
           client_streaks[identificacion][-1]['nivel'] != nivel_deuda or \
           (fecha - client_streaks[identificacion][-1]['fecha_fin']).days > 32: # esto es más de un mes de diferencia
            
            # Si hay un salto en la racha o cambio de nivel, empezar una racha d nueva
            client_streaks[identificacion].append({
                'nivel': nivel_deuda,
                'fecha_inicio': fecha,
                'fecha_fin': fecha,
                'racha': 1
            })
        else:
            # Si no continuar con la racha existnte
            client_streaks[identificacion][-1]['fecha_fin'] = fecha
            client_streaks[identificacion][-1]['racha'] += 1

    final_results = []
    for identificacion, streaks in client_streaks.items():
        eligible_streaks = []
        for streak in streaks:
            if streak['racha'] >= min_racha_length:
                eligible_streaks.append(streak)
        
        if not eligible_streaks:
            continue

        # Seleccionar la racha más larga
        longest_streak = None
        max_length = -1
        for streak in eligible_streaks:
            if streak['racha'] > max_length:
                max_length = streak['racha']
                longest_streak = streak
            elif streak['racha'] == max_length:
                # Si tienen la misma longitud, seleccionar la más reciente (fecha_fin más cercana a fecha_base)
                if longest_streak is None or abs((streak['fecha_fin'] - fecha_base).days) < abs((longest_streak['fecha_fin'] - fecha_base).days):
                    longest_streak = streak

        if longest_streak:
            final_results.append({
                'identificacion': identificacion,
                'racha': longest_streak['racha'],
                'fecha_fin': longest_streak['fecha_fin'].strftime('%Y-%m-%d'),
                'nivel': longest_streak['nivel']
            })

    if final_results:
        print("\n--- Resultados de Rachas de Deuda ---")
        for res in final_results:
            print(f"Identificacion: {res['identificacion']}, Racha: {res['racha']} meses, Fecha Fin: {res['fecha_fin']}, Nivel: {res['nivel']}")
            # Insertar resultados en la tabla debt_streaks_results
            insert_query = "INSERT INTO debt_streaks_results (identificacion, racha, fecha_fin, nivel) VALUES (?, ?, ?, ?);"
            execute_query(connection, insert_query, (res['identificacion'], res['racha'], res['fecha_fin'], res['nivel']))
        print("Resultados de rachas almacenados en la base de datos.")
    else:
        print("No se encontraron rachas que cumplan los criterios.")
    return final_results # Devolver los resultados para su posible exportación a CSV

def insert_data_into_db(connection, df):
    """
    Inserta los datos del DataFrame en la tabla `saldos_clientes`.

    Args:
        connection (connection object): Objeto de conexión a la base de datos.
        df (DataFrame): DataFrame de pandas con los datos a insertar.
    """
    insert_query = """
    INSERT INTO saldos_clientes (identificacion, fecha, saldo) VALUES (?, ?, ?);
    """
    for index, row in df.iterrows():
        # Los nombres de las columnas en el Excel son 'corte_mes', 'saldo' y 'identificacion'
        identificacion = str(row['identificacion'])
        fecha = row['corte_mes'].strftime('%Y-%m-%d')
        saldo = row['saldo']
        if not execute_query(connection, insert_query, (identificacion, fecha, saldo)):
            print(f"Error al insertar la fila: {row}")
    print("Datos insertados en la base de datos exitosamente.")

def insert_retiros_data_into_db(connection, df):
    """
    Inserta los datos del DataFrame (hoja retiros) en la tabla `retiros`.

    Args:
        connection (connection object): Objeto de conexión a la base de datos.
        df (DataFrame): DataFrame de pandas con los datos a insertar.
    """
    insert_query = """
    INSERT INTO retiros (identificacion, fecha_retiro) VALUES (?, ?);
    """
    for index, row in df.iterrows():
        identificacion = str(row['identificacion'])
        fecha_retiro = row['fecha_retiro'].strftime('%Y-%m-%d')
        if not execute_query(connection, insert_query, (identificacion, fecha_retiro)):
            print(f"Error al insertar la fila de retiros: {row}")
    print("Datos de retiros insertados en la base de datos exitosamente.") 

def export_results_to_csv(results, output_dir, file_name):
    if not results:
        print("No hay resultados para exportar a CSV.")
        return
    
    # Asegurarse de que el directorio de salida exista
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, file_name)

    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['identificacion', 'racha', 'fecha_fin', 'nivel']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(results)
        print(f"Resultados exportados exitosamente a {output_path}")
    except IOError as e:
        print(f"Error al exportar a CSV: {e}") 
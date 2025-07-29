# Análisis de Saldos de Clientes y Rachas de Deuda

para la solucion del punto 3 de la prueba tecnica se crea un proyecto con varios scripts que procesa datos de saldos de clientes y retiros desde un archivo Excel, los carga en una base de datos SQLite, clasifica los niveles de deuda y lo más importante, identifica rachas consecutivas de clientes dentro de un mismo nivel de saldo, aplicando ciertos criterios específicados en el ejercicio.

## Objetivo del Ejercicio

El objetivo principal de este programa es automatizar el análisis de saldos de clientes y generar información valiosa sobre sus patrones de deuda a lo largo del tiempo. Específicamente, busca:

1. **Cargar y almacenar datos**: Cargar información de saldos (`historia`) y retiros (`retiros`) desde un archivo Excel a una base de datos SQLite.
2. **Clasificación de Niveles de Deuda**: Categorizar los saldos de los clientes en diferentes niveles de deuda (`N0` a `N4`) según rangos predefinidos:
   * **N0**: Saldo >= 0 y < 300,000
   * **N1**: Saldo >= 300,000 y < 1,000,000
   * **N2**: Saldo >= 1,000,000 y < 3,000,000
   * **N3**: Saldo >= 3,000,000 y < 5,000,000
   * **N4**: Saldo >= 5,000,000
3. **Manejo de Meses sin Información**: Si un cliente no tiene un registro de saldo para un mes específico (después de su primera aparición), se asume un saldo `N0` para ese mes. La única excepción es si el mes es posterior a la `fecha_retiro` del cliente, en cuyo caso no se rellena el saldo.
4. **Identificación de Rachas de Deuda**: A partir de una `fecha_base` (fecha de inicio para el análisis), el programa identifica secuencias consecutivas de meses en las que un cliente ha mantenido un determinado nivel de deuda (una "racha").
5. **Selección de Rachas Específicas**: De las rachas identificadas, se seleccionan aquellas que:
   * Sean mayores o iguales a un número `n` de meses consecutivos.
   * Si un cliente tiene múltiples rachas que cumplen lo anterior, se selecciona la racha más larga.
   * Si aún hay empate en longitud, se selecciona la racha cuya `fecha_fin` sea la más reciente (más próxima a la `fecha_base`).
6. **Almacenamiento y Exportación de Resultados**: Los resultados finales de las rachas identificadas se almacenan en una nueva tabla de la base de datos (`debt_streaks_results`) y se exportan a un archivo CSV para facilitar su análisis y uso posterior.

## Estructura del Proyecto

El proyecto está organizado en los siguientes archivos:

* `main.py`: El punto de entrada del programa. Orquesta la ejecución de las funciones principales.
* `config.py`: Contiene las configuraciones globales como las rutas a la base de datos y al archivo Excel, y los nombres de las hojas.
* `database.py`: Define funciones para interactuar con la base de datos SQLite, incluyendo la creación de conexiones, ejecución de consultas, cierre de conexiones y la creación de todas las tablas de la base de datos.
* `logic.py`: Contiene la lógica de negocio principal: lectura de archivos Excel, poblamiento de tablas, la clasificación de niveles de deuda, el relleno de saldos faltantes, y la compleja lógica de identificación y selección de rachas.
* `check_db.py`: Un script auxiliar para verificar el esquema y el contenido de la base de datos (no es parte del flujo principal de `main.py`).
* `requirements.txt`: Lista las bibliotecas Python necesarias para ejecutar el proyecto.
* `data/saldos_clientes.db`: Directorio y archivo para la base de datos SQLite generada.
* `rachas/rachas.xlsx`: Directorio y archivo con los datos de entrada de saldos y retiros.
* `output_results/debt_streaks_results.csv`: Directorio y archivo donde se guardarán los resultados del análisis de rachas en formato CSV.

## Flujo de Ejecución Detallado (main.py)

El script `main.py` coordina las siguientes operaciones:

1. **Procesamiento de Argumentos de Línea de Comandos**:

   * Utiliza `argparse` para obtener dos parámetros de entrada:
     * `--fecha_base YYYY-MM-DD`: La fecha a partir de la cual se comenzarán a buscar las rachas. Es un parámetro obligatorio.
     * `--min_racha N`: La longitud mínima de la racha (en meses) para que sea considerada. El valor por defecto es 1.
2. **Inicialización de la Base de Datos**:

   * Verifica si el archivo de la base de datos (`saldos_clientes.db`) ya existe. Si existe, lo elimina para asegurar que se cree una base de datos limpia con el esquema más reciente. Esto es importnte cuando hay cambios en la estructura de las tablas.
   * Establece una conexión con la base de datos SQLite utilizando la ruta definida en `config.py`.
3. **Creación de Tablas (`database.py`) y Lectura/Poblamiento de Datos (`logic.py`)**:

   * El programa procede a crear todas las tablas necesarias llamando a las funciones respectivas en `database.py`:
     * `create_table_saldos_clientes_if_not_exists` para la tabla de saldos de clientes.
     * `create_table_retiros_if_not_exists` para la tabla de retiros.
     * `create_debt_streaks_table_if_not_exists` para la tabla de resultados de rachas.

   Una vez creadas las tablas, se procede a la lectura y poblamiento de datos:

   * Llama a `read_excel_data` (desde `logic.py`) para leer la hoja `historia` del archivo `rachas.xlsx`. Estos datos contienen la `identificacion` del cliente, la `fecha` del corte de mes y el `saldo`.
   * Llama a `insert_data_into_db` (desde `logic.py`) para insertar los datos leídos de la hoja `historia` en la tabla `saldos_clientes`.
   * Llama a `read_excel_data` (desde `logic.py`) nuevamente para leer la hoja `retiros`. Estos datos contienen la `identificacion` y la `fecha_retiro` de los clientes.
   * Llama a `insert_retiros_data_into_db` (desde `logic.py`) para insertar los datos leídos de la hoja `retiros` en la tabla `retiros`.
4. **Relleno de Saldos Faltantes (`logic.py`)**:

   * `fill_missing_saldos_with_n0`: Esta función es para poder manejar la ausencia de datos en meses consecutivos.
     * realizo una consulta a las tablas de la bd para poder obtener: `identificacion`, `MIN(s.fecha)` como `first_appearance_date` (primer registro en cuanto a fecha) y  `fecha_retiro.`
     * Si un cliente no tiene un registro de saldo para un mes dentro de ese rango y la fecha de ese mes no es posterior a su fecha de retiro, se inserta un registro con saldo 0 (clasificado como `N0`).
5. **Identificación y Reporte de Rachas de Deuda (`logic.py`)**:

   * `find_longest_debt_streak`: Esta es la función princpal  para el análisis de rachas:
     * Valida la `fecha_base`: Asegura que la `fecha_base` no sea posterior a la fecha máxima de datos disponibles en la base de datos. Si lo es, no procede con el análisis de rachas, ya que no se puede tener una racha por encima de la ultima fecha.
     * Obtiene los saldos clasificados: Consulta la bd para obtener todos los saldos de los clientes, sus fechas y sus niveles de deuda calculados (N0-N4), filtrando desde la `fecha_base` hasta la fecha máxima de datos disponibles.
     * Procesa las rachas por cliente: Itera sobre los datos clasificados para identificar secuencias consecutivas de meses en el mismo nivel de deuda.
     * Filtra rachas por longitud mínima: Descarta las rachas que no cumplen con el `--min_racha` especificado.
     * Selecciona la racha más larga: Para cada cliente, si hay múltiples rachas que sean valdias o elegibles, se elige la de mayor duración como dice en el ejercicio.
     * Resuelve empates: Si hay un empate en la longitud de la racha, selecciona aquella cuya `fecha_fin` sea la más reciente.
     * Presenta los resultados: Imprime la `identificacion` del cliente, la `racha` (número de meses), la `fecha_fin` de la racha y el `nivel` de deuda asociado.
6. **Almacenamiento y Exportación de Resultados**: Después de identificar las rachas, el programa realiza lo siguiente:

   * **Almacenamiento en Base de Datos**: Los resultados (`identificacion`, `racha`, `fecha_fin`, `nivel`) se insertan en la nueva tabla `debt_streaks_results` en la base de datos SQLite. Esta tabla se crea (si no existe) y se limpia de ejecuciones anteriores para asegurar la frescura de los datos.
   * **Exportación a CSV**: Los mismos resultados se exportan a un archivo CSV (`debt_streaks_results.csv`) dentro del directorio `./output_results`. Si el directorio no existe, se crea automáticamente.
7. **Cierre de Conexión a la Base de Datos**:

   * Finalmente, la conexión a la base de datos SQLite se cierra.

## Cómo Ejecutar el Programa

1. **Instalar dependencias**: Asegúrate de tener Python instalado. Luego, instala las bibliotecas necesarias:

   ```bash
   pip install -r requirements.txt
   ```
2. **Ejecutar el script**: Navega a la raíz del proyecto en tu terminal y ejecuta el `main.py`, dando como parametros la `fecha_base` y opcionalmente `min_racha`:

   ```bash
   python main.py --fecha_base YYYY-MM-DD --min_racha N
   ```
   * Reemplaza `YYYY-MM-DD` con la fecha en formato año-mes-día (ej: `2023-01-01`).
   * Reemplaza `N` con el número mínimo de meses consecutivos para una racha (ej: `2`).

   **Ejemplos:**

   * Buscar rachas a partir del 1 de enero de 2023 con un mínimo de 2 meses:
     ```bash
     python main.py --fecha_base 2023-01-01 --min_racha 2
     ```
   * Buscar rachas a partir del 31 de diciembre de 2022 con cualquier longitud (min_racha por defecto es 1):
     ```bash
     python main.py --fecha_base 2022-12-31
     ```
   * Intentar buscar rachas a partir de una fecha futura (no debería mostrar resultados de rachas):
     ```bash
     python main.py --fecha_base 2025-01-01 --min_racha 3
     ```

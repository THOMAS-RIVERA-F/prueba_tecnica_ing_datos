# Sistema de Datos Confiables - Números de Teléfono

## Problema a Resolver

Para la solucion del punto 1 se necesita diseñar e implementar un proceso automatizado y controlado mediante prácticas de CI/CD para la creación, validación, despliegue y mantenimiento de un dataset confiable de números de teléfono de clientes. Este dataset será utilizado para mejorar la comunicación y el servicio al cliente.

## Ejemplos de Procesamiento de Números

### Números que se CONSERVAN (válidos)

```python
# Números móviles colombianos válidos - se estandarizan a formato Internacianl
"3001234567" →  "+573001234567"  ✓ (móvil válido, se estandariza)
"+573012345678" → "+573012345678"  ✓ (ya en formato correcto)
"57 301 234 5678" → "+573012345678"  ✓ (prefijo 57, se formatea)
"(301) 234-5678" → "+573012345678"  ✓ (formato con paréntesis, se limpia)
"301-234-5678"  → "+573012345678"  ✓ (formato con guiones, se limpia)
"301 234 5678" → "+573012345678"  ✓ (espacios, se limpia)
"3012345678"  → "+573012345678"  ✓ (10 dígitos empezando por 3, válido)
```

**Razón**: Todos empiezan por "3" (indicador de móvil en Colombia), tienen 10 dígitos totales, y pasan la validación de la librería `phonenumbers` que verifica que sean números reales.

### Números que se ELIMINAN (inválidos)

```python
# Números fijos (empiezan por 1, 2, 4, 5, 6, 7, 8)
"12345678"          → ELIMINADO (número fijo, no móvil)

# Números con longitud incorrecta
"123456789"         → ELIMINADO  (9 dígitos, muy corto)
"12345678901"       → ELIMINADO  (11 dígitos, muy largo)

# Números que no existen 
"3999999999"        → ELIMINADO (no es un número real asignado)
"3000000000"        → ELIMINADO (patrón no válido)

# Campos vacíos o con caracteres inválidos
""                  → ELIMINADO  (campo vacío)
"N/A"               → ELIMINADO  (texto en lugar de número)
"3001234abc"        → ELIMINADO  (contiene letras)
"###########"       → ELIMINADO  (caracteres especiales)
```

**Razón**: No cumplen con las reglas de numeración móvil colombiana o fallan la validación algorítmica de la librería `phonenumbers`.

### Eliminación de Duplicados

```python
# Antes del procesamiento:
"3001234567"        → "+573001234567"
"300-123-4567"      → "+573001234567"  (mismo número, formato diferente)
"+57 300 123 4567"  → "+573001234567"  (mismo número, formato diferente)

# Después del procesamiento (se mantiene solo queda uno en el formato correcto interncional):
"+573001234567"     ✓ (duplicados eliminados, se conserva el primero)
```

Ya que después de estandarizar a formato intern, el sistema detecta que son el mismo número y elimina las ocurrencias duplicadas, manteniendo solo la primera.

## Sistema de Trazabilidad Completa

### Dónde se Guarda la Información

El sistema mantiene **dos niveles de trazabilidad**:

#### 1. Base de Datos Principal: `phone_numbers_trusted`

```sql
-- Ubicación: database/phone_numbers.db
-- Tabla: phone_numbers_trusted

CREATE TABLE phone_numbers_trusted (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente TEXT NOT NULL,                    -- ID original del cliente
    nombre TEXT NOT NULL,                        -- Nombre del cliente
    celular TEXT NOT NULL,                       -- Número original (sin procesar)
    celular_limpio TEXT NOT NULL UNIQUE,         -- Número procesado en E.164
    tipo_numero TEXT NOT NULL,                   -- Siempre "móvil"
    fecha_registro TEXT NOT NULL,                -- Fecha de registro original
    canal_obtencion TEXT NOT NULL,               -- Canal: Web, PCO, instagram
    consentimiento_contacto BOOLEAN NOT NULL,    -- Autorización de contacto
    fecha_procesamiento TEXT NOT NULL,           -- Cuándo fue procesado
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Ejemplo de registro guardado**:

```
id: 1
id_cliente: "C0001"
nombre: "Cliente 1"
celular: "300 123 4567"                    ← Número original (trazabilidad)
celular_limpio: "+573001234567"            ← Número procesado
tipo_numero: "móvil"
fecha_registro: "2024-01-15 10:30:00"
canal_obtencion: "Web"
consentimiento_contacto: true
fecha_procesamiento: "2025-01-29 14:22:15" ← Cuándo fue procesado
created_at: "2025-01-29 14:22:15"
updated_at: "2025-01-29 14:22:15"
```

#### 2. Auditoría de Procesamiento: `processing_audit`

```sql
-- Tabla: processing_audit

CREATE TABLE processing_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id TEXT NOT NULL,                      -- ID único del procesamiento
    total_records_input INTEGER NOT NULL,        -- Cuántos registros entraron
    total_records_output INTEGER NOT NULL,       -- Cuántos salieron válidos
    records_removed INTEGER NOT NULL,            -- Cuántos se eliminaron
    duplicates_removed INTEGER NOT NULL,         -- Cuántos duplicados
    invalid_numbers_removed INTEGER NOT NULL,    -- Cuántos inválidos
    processing_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL                         -- SUCCESS o ERROR
);
```

**Ejemplo de registro de auditoría**:

```
id: 1
batch_id: "batch_20250129_142215_a1b2c3d4"
total_records_input: 500
total_records_output: 342
records_removed: 158
duplicates_removed: 23
invalid_numbers_removed: 135
processing_date: "2025-01-29 14:22:15"
status: "SUCCESS"
```

### Información de Trazabilidad Guardada

#### Para cada número procesado:

1. **Número original** (`celular`): Exactamente como llegó al sistema
2. **Número procesado** (`celular_limpio`): Resultado final en formato E.164
3. **Timestamp de procesamiento**: Cuándo exactamente fue procesado
4. **Datos del cliente**: ID, nombre, canal de obtención, consentimiento
5. **Metadatos**: Fecha de creación, última actualización

#### Para cada ejecución del sistema:

1. **ID único del lote** (`batch_id`): Identificador único generado automáticamente
2. **Métricas completas**: Entradas, salidas, eliminados, duplicados
3. **Timestamp de ejecución**: Cuándo se ejecutó el procesamiento
4. **Estado del procesamiento**: SUCCESS o ERROR con detalles

### Consultas de Trazabilidad

```python
# Rastrear un número específico
SELECT celular, celular_limpio, fecha_procesamiento 
FROM phone_numbers_trusted 
WHERE celular_limpio = '+573001234567';

# Ver historial de procesamiento
SELECT batch_id, total_records_input, total_records_output, 
       processing_date, status 
FROM processing_audit 
ORDER BY processing_date DESC;

# Analizar calidad de datos por lote
SELECT batch_id,
       (total_records_output * 100.0 / total_records_input) as success_rate,
       duplicates_removed,
       invalid_numbers_removed
FROM processing_audit;
```

## Implementación de CI/CD

### Integración Continua (CI)

#### Pruebas Automáticas Ejecutadas

```bash
# 13 pruebas atómicas que validan:

# Validación de números:
tests/test_phone_validation.py::test_valid_colombian_mobile_numbers
tests/test_phone_validation.py::test_remove_invalid_numbers  
tests/test_phone_validation.py::test_remove_duplicates
tests/test_phone_validation.py::test_handle_null_values
tests/test_phone_validation.py::test_preserve_other_columns
tests/test_phone_validation.py::test_e164_format
tests/test_phone_validation.py::test_empty_dataframe

# Integridad de base de datos:
tests/test_database.py::test_database_creation
tests/test_database.py::test_phone_numbers_table_structure
tests/test_database.py::test_insert_phone_number
tests/test_database.py::test_unique_constraint_celular_limpio
tests/test_database.py::test_processing_audit_table
tests/test_database.py::test_indexes_exist
```

#### Dónde y Cuándo se Ejecutan

```bash
# Desarrollo local (antes de cada commit)
python scripts/run_tests.py

# CI/CD Pipeline (automático en cada push)
# GitHub Actions: .github/workflows/ci.yml

# Comando en pipeline:
pytest tests/ -v --cov=src --cov=config --cov-report=html
```

### Despliegue Continuo (CD)

#### Pipeline de Datos Automatizado

```bash
# 1. Validación previa (CI)
python scripts/run_tests.py  # Todas las pruebas deben pasar

# 2. Procesamiento automático
python src/clean_data.py     # Procesa datos nuevos

# 3. Verificación post-procesamiento
# - Verifica que la base de datos tenga registros nuevos
# - Confirma que el batch_id se creó correctamente
# - Valida que las métricas sean coherentes

# 4. Notificación de resultado
# Estado: SUCCESS/ERROR registrado en processing_audit
```

#### Rollback y Recuperación

```sql
-- En caso de error, se puede revertir usando la auditoría:

-- 1. Identificar el lote problemático
SELECT * FROM processing_audit WHERE status = 'ERROR';

-- 2. Eliminar registros del lote problemático
DELETE FROM phone_numbers_trusted 
WHERE fecha_procesamiento = '2025-01-29 14:22:15';

-- 3. Reejecutar procesamiento
python src/clean_data.py
```

## Flujo Completo del Sistema

### Proceso Automatizado

```
1. Datos Crudos (input/raw_numeros.csv)
   ↓
2. Validación (phonenumbers library)
   ↓
3. Estandarización (formato E.164)
   ↓
4. Eliminación de Duplicados
   ↓
5. Almacenamiento (SQLite database)
   ↓
6. Auditoría (processing_audit table)
   ↓
7. Salida Limpia (output/cleaned_numeros.csv)
```

### Ejemplo de Ejecución Real

```bash
python src/clean_data.py

# Salida:
Iniciando procesamiento de datos - Batch ID: batch_20250129_142215_a1b2c3d4
Datos cargados: 50 registros desde input/raw_numeros.csv

--- Datos crudos (primeras 5 filas) ---
  id_cliente     nombre        celular
0      C0001  Cliente 1   300 123 4567    ← Formato con espacios
1      C0002  Cliente 2  +57(301)234-5678 ← Formato con paréntesis
2      C0003  Cliente 3      3001234567    ← Formato estándar
3      C0004  Cliente 4      1234567890    ← Número inválido
4      C0005  Cliente 5                   ← Campo vacío

Iniciando limpieza de datos...

Estadísticas de procesamiento:
   Registros de entrada: 50
   Registros de salida: 32           ← 32 números válidos
   Registros eliminados: 18          ← 18 eliminados
   Duplicados eliminados: 3          ← 3 duplicados
   Números inválidos eliminados: 15  ← 15 inválidos

--- Datos limpios y estandarizados (primeras 3 filas) ---
  id_cliente     nombre celular_limpio
0      C0001  Cliente 1  +573001234567  ← Estandarizado
1      C0002  Cliente 2  +573012345678  ← Estandarizado
2      C0003  Cliente 3  +573001234567  ← Estandarizado

Dataset limpio guardado en: output/cleaned_numeros.csv
Datos guardados exitosamente en la base de datos
Registros procesados: 32/50
```

### Verificación de Trazabilidad

```python
# Consultar lo que se guardó en la base de datos
import sqlite3
conn = sqlite3.connect('database/phone_numbers.db')

# Ver los números procesados
cursor.execute("SELECT celular, celular_limpio FROM phone_numbers_trusted LIMIT 3")
# Resultado:
# ('300 123 4567', '+573001234567')      ← Original → Procesado
# ('+57(301)234-5678', '+573012345678')  ← Original → Procesado  
# ('3001234567', '+573001234567')        ← Original → Procesado

# Ver la auditoría del procesamiento
cursor.execute("SELECT * FROM processing_audit ORDER BY processing_date DESC LIMIT 1")
# Resultado:
# (1, 'batch_20250129_142215_a1b2c3d4', 50, 32, 18, 3, 15, '2025-01-29 14:22:15', 'SUCCESS')
```

## Instalación y Uso

### Requisitos

```bash
pandas
phonenumbers
pytest
pytest-cov
```

### Instalación

```bash
pip install -r requirements.txt
python config/database_config.py  # Crear base de datos
```

### Uso

```bash
# Generar datos de prueba
python generate_phone_numbers.py

# Procesar y limpiar datos
python src/clean_data.py

# Ejecutar pruebas
python scripts/run_tests.py
```

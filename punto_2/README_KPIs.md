# Sistema de KPIs y Veeduría de Calidad de Datos

## Problema a Resolver

**Objetivo**: Implementar un mecanismo/herramienta que permita hacer veeduría de la calidad de datos, trazabilidad del dato y generar KPIs para que los equipos de negocio obtengan métricas acerca de los teléfonos de los clientes.

## Arquitectura del Sistema de KPIs

### Fuentes de Datos Disponibles

#### Tabla Principal: `phone_numbers_trusted`

```sql
-- Datos confiables de clientes
id, id_cliente, nombre, celular, celular_limpio, tipo_numero, 
fecha_registro, canal_obtencion, consentimiento_contacto, 
fecha_procesamiento, created_at, updated_at
```

#### Tabla de Auditoría: `processing_audit`

```sql
-- Historial de procesamientos
id, batch_id, total_records_input, total_records_output, 
records_removed, duplicates_removed, invalid_numbers_removed, 
processing_date, status
```

## KPIs

### A. Métricas de Efectividad del Procesamiento

#### 1. **Tasa de Éxito Global**

```sql
-- KPI: Porcentaje de números válidos procesados
SELECT 
    ROUND(AVG(total_records_output * 100.0 / total_records_input), 2) as tasa_exito_promedio,
    COUNT(*) as total_procesamientos,
    MIN(processing_date) as primer_procesamiento,
    MAX(processing_date) as ultimo_procesamiento
FROM processing_audit 
WHERE status = 'SUCCESS';

-- Resultado esperado:
-- tasa_exito_promedio: 68.5%
-- total_procesamientos: 15
-- primer_procesamiento: 2025-01-15 08:00:00
-- ultimo_procesamiento: 2025-01-29 14:22:15
```

#### 2. **Distribución de Problemas de Calidad**

```sql
-- KPI: Análisis de tipos de errores
SELECT 
    SUM(duplicates_removed) as total_duplicados,
    SUM(invalid_numbers_removed) as total_invalidos,
    SUM(records_removed) as total_eliminados,
    ROUND(SUM(duplicates_removed) * 100.0 / SUM(records_removed), 2) as porcentaje_duplicados,
    ROUND(SUM(invalid_numbers_removed) * 100.0 / SUM(records_removed), 2) as porcentaje_invalidos
FROM processing_audit 
WHERE status = 'SUCCESS';

-- Resultado esperado:
-- total_duplicados: 145
-- total_invalidos: 2,340
-- total_eliminados: 2,485
-- porcentaje_duplicados: 5.8%
-- porcentaje_invalidos: 94.2%
```

#### 3. **Tendencia de Calidad por Período**

```sql
-- KPI: Evolución de la calidad de datos
SELECT 
    DATE(processing_date) as fecha,
    AVG(total_records_output * 100.0 / total_records_input) as tasa_exito_dia,
    SUM(total_records_input) as registros_entrada,
    SUM(total_records_output) as registros_salida
FROM processing_audit 
WHERE status = 'SUCCESS'
GROUP BY DATE(processing_date)
ORDER BY fecha DESC
LIMIT 7;

-- Resultado esperado:
-- 2025-01-29: 72.3% (500 → 362)
-- 2025-01-28: 68.1% (450 → 306)
-- 2025-01-27: 65.9% (520 → 343)
```

### B. Métricas de Negocio por Canal de Obtención

#### 4. **Efectividad por Canal de Adquisición**

```sql
-- KPI: Calidad de datos por canal de obtención
SELECT 
    canal_obtencion,
    COUNT(*) as total_clientes,
    COUNT(*) * 100.0 / (SELECT COUNT(*) FROM phone_numbers_trusted) as porcentaje_participacion,
    AVG(CASE WHEN consentimiento_contacto = 1 THEN 1.0 ELSE 0.0 END) * 100 as tasa_consentimiento
FROM phone_numbers_trusted
GROUP BY canal_obtencion
ORDER BY total_clientes DESC;

-- Resultado esperado:
-- Web: 1,250 clientes (45.2%) - 85.6% consentimiento
-- PCO: 890 clientes (32.1%) - 78.3% consentimiento  
-- instagram: 630 clientes (22.7%) - 92.1% consentimiento
```

#### 5. **Evolución Temporal por Canal**

```sql
-- KPI: Crecimiento de clientes por canal y mes
SELECT 
    canal_obtencion,
    strftime('%Y-%m', fecha_registro) as mes,
    COUNT(*) as nuevos_clientes,
    SUM(COUNT(*)) OVER (PARTITION BY canal_obtencion ORDER BY strftime('%Y-%m', fecha_registro)) as acumulado
FROM phone_numbers_trusted
WHERE fecha_registro >= date('now', '-12 months')
GROUP BY canal_obtencion, strftime('%Y-%m', fecha_registro)
ORDER BY canal_obtencion, mes;

-- Resultado esperado:
-- Web, 2024-02: 45 nuevos (45 acumulado)
-- Web, 2024-03: 67 nuevos (112 acumulado)
-- PCO, 2024-02: 23 nuevos (23 acumulado)
```

### C. Métricas de Consentimiento y Contactabilidad

#### 6. **Análisis de Consentimiento Global**

```sql
-- KPI: Estado del consentimiento de contacto
SELECT 
    CASE 
        WHEN consentimiento_contacto = 1 THEN 'Con Consentimiento'
        ELSE 'Sin Consentimiento'
    END as estado_consentimiento,
    COUNT(*) as total_clientes,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM phone_numbers_trusted), 2) as porcentaje
FROM phone_numbers_trusted
GROUP BY consentimiento_contacto;

-- Resultado esperado:
-- Con Consentimiento: 2,216 clientes (80.0%)
-- Sin Consentimiento: 554 clientes (20.0%)
```

#### 7. **Segmentación para Campañas**

```sql
-- KPI: Clientes contactables por canal
SELECT 
    canal_obtencion,
    COUNT(*) as total_clientes,
    SUM(CASE WHEN consentimiento_contacto = 1 THEN 1 ELSE 0 END) as contactables,
    ROUND(SUM(CASE WHEN consentimiento_contacto = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as tasa_contactabilidad,
    SUM(CASE WHEN consentimiento_contacto = 1 THEN 1 ELSE 0 END) as potencial_campanas
FROM phone_numbers_trusted
GROUP BY canal_obtencion
ORDER BY contactables DESC;

-- Resultado esperado:
-- Web: 1,250 total → 1,070 contactables (85.6%) 
-- PCO: 890 total → 697 contactables (78.3%)
-- instagram: 630 total → 580 contactables (92.1%)
```

### D. Métricas de Trazabilidad y Auditoría

#### 8. **Historial de Transformaciones**

```sql
-- KPI: Trazabilidad de números procesados
SELECT 
    COUNT(DISTINCT celular) as numeros_originales_unicos,
    COUNT(DISTINCT celular_limpio) as numeros_limpios_unicos,
    COUNT(*) as total_registros,
    ROUND((COUNT(*) - COUNT(DISTINCT celular_limpio)) * 100.0 / COUNT(*), 2) as porcentaje_duplicados_originales
FROM phone_numbers_trusted;

-- Resultado esperado:
-- numeros_originales_unicos: 2,770
-- numeros_limpios_unicos: 2,770  
-- total_registros: 2,770
-- porcentaje_duplicados_originales: 0.0%
```

#### 9. **Análisis de Patrones de Entrada**

```sql
-- KPI: Tipos de formato de entrada más comunes
SELECT 
    CASE 
        WHEN celular LIKE '+57%' THEN 'Formato Internacional (+57)'
        WHEN celular LIKE '57%' THEN 'Con Prefijo (57)'
        WHEN celular LIKE '3%' AND LENGTH(celular) = 10 THEN 'Móvil Estándar (10 dígitos)'
        WHEN celular LIKE '%-%' OR celular LIKE '%(%' THEN 'Con Separadores'
        WHEN celular LIKE '% %' THEN 'Con Espacios'
        ELSE 'Otros Formatos'
    END as tipo_formato,
    COUNT(*) as cantidad,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM phone_numbers_trusted), 2) as porcentaje
FROM phone_numbers_trusted
GROUP BY tipo_formato
ORDER BY cantidad DESC;

-- Resultado esperado:
-- Móvil Estándar (10 dígitos): 1,245 (44.9%)
-- Con Espacios: 678 (24.5%)
-- Con Separadores: 445 (16.1%)
-- Formato Internacional (+57): 234 (8.4%)
-- Con Prefijo (57): 168 (6.1%)
```

## Beneficios para Equipos de Negocio

### 1. **Euipos de Marketing**

- **Segmentación precisa**: Saber cuántos clientes contactables hay por canal
- **ROI de canales**: Identificar qué canales generan mejor calidad de datos
- **Planificación de campañas**: Calcular alcance real antes de ejecutar

### 2. **Equipos de Atención al Cliente**

- **Contactabilidad real**: Números válidos para soporte proactivo
- **Consentimiento**: Respetar preferencias de contacto de clientes
- **Trazabilida**: Rastrear origen de cada número para contexto

### 3. **Equipos de Calidad de Datos**

- **Monitoreo continuo**: Alertas cuando la calidad baja del umbral ()
- **Identificación de problemas**: Patrones de errores por fuente
- **Mejora continua**: Métricas para optimizar procesos

### 4. **Gerencia y Dirección**

- **KPIs ejecutivos**: Resumen de calidad y contactabilidad
- **Tendencias**: Evolución de la calidad de datos
- **ROI**: Impacto económico de tener datos limpios

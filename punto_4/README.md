# Procesamiento de Archivos HTML y Codificación de Imágenes a Base64

Esta es la solución al Ejercicio 4 de la prueba tecnia, cuyo objetivo es procesar archivos HTML para incrustar o ponr sus imágenes referenciadas directamente en el código del documento usando codificación Base64.

## Descripción del Ejercicio

Para el ejercicio se creean varios scripts en Python que sean capaces de:

1. **Recibir entradas:** Aceptar un listado de archivos HTML a procesar o un listado de directorios que contengan archivos HTML (incluyendo subdirectorios). En este caso lo llame `test_html_files`
2. **Identificar imágenes:** Recorrer todos los archivos HTML identificados y determinar qué imágenes están asociadas a ellos (asumiendo que todas están dentro de la etiqueta `<img>`).
3. **Convertir a Base64:** Convertir estas imágenes a su representación en Base64.
4. **Reemplazar y guardar:** Reemplazar las referencias de las imágenes originales en el HTML por sus versiones codificadas en Base64. Es crucial que el archivo HTML original *no* sea modificado; en su lugar, se debe crear un nuevo archivo con los cambios.(doc)
5. **Generar informe:** Producir un objeto o diccionario que contenga un resumen de las imágenes procesadas exitosamente y aquellas que hayan fallado, con el siguiente formato:

   ```json
   {
       "success": {},
       "fail": {}
   }
   ```

## Funcionamiento del Proyecto

El proyecto está estructurado de manera modular para abordar cada uno de los requisitos del ejercicio. El flujo que hace el progrma es el siguiente:

1. **Descubrimiento de Archivos:** El script comienza buscando todos los archivos HTML (con extensiones `.html` ) dentro de un directorio raíz especificado y sus subdirectorios.
2. **Lectura y Análisis:** Cada archivo HTML encontrado es leído, y su contenido es analizado para identificar todas las etiquetas `<img>` y extraer sus atributos `src`.
3. **Resolución de Rutas:** Las rutas de las imágenes (tanto relativas como absolutas) se resuelven para obtener la ubicación física del archivo de imagen en el sistema de archivos.
4. **Codificación a Base64:** Cada imagen identificada se lee y se convierte a una cadena de texto Base64.
5. **Reemplazo en HTML:** La ruta original en el atributo `src` de la etiqueta `<img>` se reemplaza por la cadena Base64 generada para ser usada en el archivo copia que creemos.
6. **Creación de Nuevos Archivos:** El contenido HTML modificado se guarda en un *nuevo* archivo. Este nuevo archivo se nombra añadiendo `_processed` al nombre original (ej. `index.html` -> `index_processed.html`) y se guarda en un directorio de resultados, manteniendo la estructura de subdirectorios del original.
7. **Generación de Informe:** Durante todo el proceso, se registra qué imágenes se procesaron con éxito y cuáles fallaron (con un mensaje de error asociado), compilando un resumen final.

## Estructura y Funciones Clave

El proyecto se compone de varias clases, cada una con una responsabilidad específica:

* **`src/main.py`**: El punto de entrada principal de la aplicación. Configura las rutas de entrada y salida, inicializa `HtmlProcessor` y llama al método principal para iniciar el procesamiento. También imprime el resumen final de las imágenes procesadas.
* **`src/core/html_processor.py` (`HtmlProcessor`)**:

  * Es la clase orquestador, coordina las operaciones de lectura, reemplazo y escritura de archivos HTML.
  * Invoca a las clases `HtmlReader`, `HtmlImageReplacer` y `HtmlFileWriter`.
  * Recopila y devuelve el resumen final de las imágenes (`success`/`fail`).
* **`html_processing_lib/html_reader.py` (`HtmlReader`)**:

  * Encargado de buscar archivos HTML (`.html`, `.htm`) en un directorio dado y sus subdirectorios (`find_html_files`).
  * Lee el contenido de un archivo HTML específico (`read_html_content`).
* **`html_processing_lib/html_image_replacer.py` (`HtmlImageReplacer`)**:

  * Utiliza expresiones regulares para encontrar etiquetas `<img>` y extraer sus atributos `src`.
  * Resuelve las rutas de las imágenes a rutas absolutas (`_resolve_image_path`).
  * Coordina la codificación de imágenes a Base64 usando `ImageEncoder`.
  * Realiza el reemplazo de las rutas `src` por las cadenas Base64 en el contenido HTML (`replace_images_with_base64`).
* **`html_processing_lib/image_encoder.py` (`ImageEncoder`)**:

  * Se encarga de convertir un archivo de imagen a su representación Base64 (`image_to_base64`).
  * Determina el tipo MIME de la imagen para el prefijo URI de datos (`_get_mime_type`) utilizando la librería `imghdr` y gestionando tipos adicionales como SVG, ICO y WebP.
* **`html_processing_lib/html_file_writer.py` (`HtmlFileWriter`)**:

  * Escribe el contenido HTML procesado en un nuevo archivo.
  * Se asegura de que los nuevos archivos se nombren con el sufijo `_processed` y se guarden en el directorio de salida, manteniendo la estructura de directorios original.

## Cómo Ejecutar el Proyecto

Para ejecutar el script, siga estos pasos:

**Navegue a la raíz del proyecto** en su terminal.

1. **Ejecute el script `main.py`**:

   ```bash
   python src/main.py
   ```

### Archivos de Entrada y Salida

* **Archivos de Entrada:** El script toma como entrada los archivos HTML ubicados en el directorio `test_html_files/` (y sus subdirectorios). Por ejemplo, `test_html_files/index.html` y `test_html_files/about/about.html` son ejemplos de archivos de entrada.
  Las imágenes referenciadas en estos HTML (por ejemplo, `test_html_files/images/image1.jpg`) son las que serán codificadas.
* **Archivos de Salida:** Los archivos HTML procesados se generarán en el directorio `results/`. Por cada archivo de entrada, se creará un archivo correspondiente con el sufijo `_processed`. Por ejemplo:

  * `test_html_files/index.html` se convierte en `results/index_processed.html`.
  * `test_html_files/about/about.html` se convierte en `results/about/about_processed.html` (manteniendo la estructura de subdirectorios).

Después de la ejecución, la consola mostrará un resumen detallado de las imágenes que fueron procesadas exitosamente y de aquellas que pudieron haber fallado.

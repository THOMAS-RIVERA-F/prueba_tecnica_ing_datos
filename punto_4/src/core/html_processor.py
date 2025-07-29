from html_processing_lib.html_reader import HtmlReader
from html_processing_lib.image_encoder import ImageEncoder
from html_processing_lib.html_image_replacer import HtmlImageReplacer
from html_processing_lib.html_file_writer import HtmlFileWriter

class HtmlProcessor:
    """
    Clase principal que orquesta el procesamiento de archivos HTML:
    lectura, reemplazo de imágenes por Base64 y escritura de archivos procesados.
    """
    def __init__(self, root_path: str, output_root_directory: str):
        """
        Inicializa HtmlProcessor con la ruta raíz de los archivos HTML.

        Args:
            root_path (str): La ruta absoluta del directorio raíz donde buscar archivos HTML.
        """
        self.html_reader = HtmlReader(root_path)
        self.image_encoder = ImageEncoder()
        self.html_image_replacer = HtmlImageReplacer(self.image_encoder)
        self.html_file_writer = HtmlFileWriter(root_path, output_root_directory)

    def process_all_html_files(self) -> dict:
        """
        Encuentra todos los archivos HTML en la ruta raíz y sus subcarpetas,
        procesa sus imágenes y guarda los archivos HTML resultantes.

        Returns:
            dict: Un diccionario que contiene las imágenes procesadas exitosamente y las que fallaron.
        """
        html_files = self.html_reader.find_html_files()
        if not html_files:
            print(f"No se encontraron archivos HTML en la ruta: {self.html_reader.root_path}")
            return {"success": {}, "fail": {}}

        all_image_results = {"success": {}, "fail": {}}

        for html_file_path in html_files:
            print(f"Procesando archivo: {html_file_path}")
            try:
                html_content = self.html_reader.read_html_content(html_file_path)
                processed_html_content, image_results = self.html_image_replacer.replace_images_with_base64(
                    html_content, html_file_path
                )
                new_file_path = self.html_file_writer.write_processed_html(
                    html_file_path, processed_html_content
                )
                if new_file_path:
                    print(f"Archivo procesado guardado en: {new_file_path}")
                
                all_image_results["success"].update(image_results["success"])
                all_image_results["fail"].update(image_results["fail"])

            except Exception as e:
                print(f"Error al procesar {html_file_path}: {e}")
                all_image_results["fail"][html_file_path] = str(e)
        
        return all_image_results

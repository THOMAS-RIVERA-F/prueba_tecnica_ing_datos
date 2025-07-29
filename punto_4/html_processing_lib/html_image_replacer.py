import os
import re
from .image_encoder import ImageEncoder

class HtmlImageReplacer:
    """
    Clase encargada de encontrar y reemplazar las rutas de imágenes en un contenido HTML
    por sus representaciones en Base64.
    """
    def __init__(self, image_encoder: ImageEncoder):
        """
        Inicializa HtmlImageReplacer con una instancia de ImageEncoder.

        Args:
            image_encoder (ImageEncoder): Una instancia de ImageEncoder para codificar imágenes.
        """
        self.image_encoder = image_encoder
        self.img_src_pattern = re.compile(r'<img[^>]+src=("|")(.*?)\1[^>]*>', re.IGNORECASE)

    def _resolve_image_path(self, html_file_path: str, image_src: str) -> str:
        """
        Resuelve la ruta absoluta de una imagen, considerando si es relativa al archivo HTML o absoluta.

        Args:
            html_file_path (str): La ruta absoluta del archivo HTML que contiene la imagen.
            image_src (str): El valor del atributo 'src' de la etiqueta <img>.

        Returns:
            str: La ruta absoluta de la imagen.
        """
        if os.path.isabs(image_src):
            return image_src
        else:
            return os.path.abspath(os.path.join(os.path.dirname(html_file_path), image_src))

    def replace_images_with_base64(self, html_content: str, html_file_path: str) -> tuple[str, dict]:
        """
        Encuentra todas las imágenes en el contenido HTML y reemplaza sus atributos 'src'
        con la representación Base64 de la imagen.

        Args:
            html_content (str): El contenido HTML como una cadena.
            html_file_path (str): La ruta absoluta del archivo HTML original.

        Returns:
            tuple[str, dict]: Una tupla que contiene el contenido HTML modificado y un diccionario
                              con los resultados del procesamiento de imágenes.
        """
        image_processing_results = {"success": {}, "fail": {}}

        def _replacer(match):
            original_tag = match.group(0)
            image_src = match.group(2)

            if image_src.startswith(('http://', 'https://', 'data:')):
                return original_tag

            absolute_image_path = self._resolve_image_path(html_file_path, image_src)
            
            success, result = self.image_encoder.image_to_base64(absolute_image_path)

            if success:
                src_attribute_match = re.search(r'src=("|")' + re.escape(image_src) + r'("|")', original_tag, re.IGNORECASE)
                if src_attribute_match:
                    old_src_full_string = src_attribute_match.group(0) 
                    new_src_full_string = f'src="{result}"'
                    image_processing_results["success"][image_src] = absolute_image_path
                    return original_tag.replace(old_src_full_string, new_src_full_string)
                else:
                    image_processing_results["fail"][image_src] = f"No se pudo encontrar el atributo src en la etiqueta: {original_tag}"
                    return original_tag
            else:
                image_processing_results["fail"][image_src] = result
                return original_tag

        processed_html = self.img_src_pattern.sub(_replacer, html_content)
        return processed_html, image_processing_results

import os
import base64
import imghdr
from typing import Optional

class ImageEncoder:
    """
    Clase encargada de codificar imágenes a Base64 y determinar su tipo MIME.
    """
    def __init__(self):
        """
        Inicializa ImageEncoder.
        """
        pass

    def _get_mime_type(self, image_path: str) -> str:
        """
        Determina el tipo MIME de la imagen.

        Args:
            image_path (str): La ruta absoluta de la imagen.

        Returns:
            str: El tipo MIME de la imagen (ej. 'image/png', 'image/jpeg').
                 Retorna 'application/octet-stream' si no puede determinar el tipo.
        """
        try:
            with open(image_path, 'rb') as f:
                header = f.read(32)
            image_type = imghdr.what(None, h=header)
            if image_type:
                return f"image/{image_type}"
            else:
                ext = os.path.splitext(image_path)[1].lower()
                if ext == '.svg':
                    return 'image/svg+xml'
                elif ext == '.ico':
                    return 'image/x-icon'
                elif ext == '.webp':
                    return 'image/webp'
                return 'application/octet-stream'
        except Exception:
            return 'application/octet-stream'

    def image_to_base64(self, image_path: str) -> tuple[bool, Optional[str]]:
        """
        Toma la ruta absoluta de la imagen y la convierte a una cadena Base64
        con su prefijo data: URI.

        Args:
            image_path (str): La ruta absoluta de la imagen.

        Returns:
            tuple[bool, Optional[str]]: Una tupla donde el primer elemento es True si la codificación fue exitosa
                                       y False en caso contrario. El segundo elemento es la cadena Base64 con el prefijo data: URI
                                       si fue exitoso, o un mensaje de error si falló.
        """
        if not os.path.exists(image_path):
            return False, f"Imagen no encontrada en {image_path}"

        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            encoded_string = base64.b64encode(image_data).decode('utf-8')
            mime_type = self._get_mime_type(image_path)
            return True, f"data:{mime_type};base64,{encoded_string}"
        except Exception as e:
            return False, f"Error al procesar la imagen {image_path}: {e}"

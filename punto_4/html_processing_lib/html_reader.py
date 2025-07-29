import os
from typing import List

class HtmlReader:
    """
    Clase encargada de encontrar y leer archivos HTML dentro de una ruta especificada,
    incluyendo subcarpetas.
    """
    def __init__(self, root_path: str):
        """
        Inicializa HtmlReader con la ruta raíz donde buscar archivos HTML.

        Args:
            root_path (str): La ruta absoluta del directorio raíz.
        """
        self.root_path = os.path.abspath(root_path)

    def find_html_files(self) -> List[str]:
        """
        Busca y devuelve una lista de rutas absolutas a todos los archivos HTML
        (.html y .htm) encontrados en la ruta raíz y sus subcarpetas.

        Returns:
            List[str]: Una lista de rutas absolutas a los archivos HTML.
        """
        html_files = []
        for dirpath, _, filenames in os.walk(self.root_path):
            for filename in filenames:
                if filename.endswith(('.html', '.htm')):
                    html_files.append(os.path.join(dirpath, filename))
        return html_files

    def read_html_content(self, file_path: str) -> str:
        """
        Lee el contenido de un archivo HTML dado su ruta absoluta.

        Args:
            file_path (str): La ruta absoluta del archivo HTML a leer.

        Returns:
            str: El contenido del archivo HTML como una cadena de texto.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"El archivo no se encontró: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise IOError(f"Error al leer el archivo {file_path}: {e}")

import os

class HtmlFileWriter:
    """
    Clase encargada de escribir contenido HTML procesado a un nuevo archivo.
    """
    def __init__(self, input_root_directory: str, output_root_directory: str):
        """
        Inicializa HtmlFileWriter con los directorios raíz de entrada y salida.

        Args:
            input_root_directory (str): La ruta absoluta del directorio raíz de los archivos HTML de entrada.
            output_root_directory (str): La ruta absoluta del directorio raíz donde se guardarán los archivos procesados.
        """
        self.input_root_directory = os.path.abspath(input_root_directory)
        self.output_root_directory = os.path.abspath(output_root_directory)

    def write_processed_html(self, original_file_path: str, processed_content: str) -> str:
        """
        Escribe el contenido HTML procesado a un nuevo archivo, añadiendo '_processed'
        al nombre del archivo original.

        Args:
            original_file_path (str): La ruta absoluta del archivo HTML original.
            processed_content (str): El contenido HTML procesado a escribir.

        Returns:
            str: La ruta absoluta del nuevo archivo procesado, o una cadena vacía si hay un error.
        """
        relative_path = os.path.relpath(original_file_path, self.input_root_directory)
        dirname = os.path.dirname(relative_path)
        basename = os.path.basename(original_file_path)
        name, ext = os.path.splitext(basename)
        new_filename = f"{name}_processed{ext}"

        output_dir = os.path.join(self.output_root_directory, dirname)
        os.makedirs(output_dir, exist_ok=True)

        new_file_path = os.path.join(output_dir, new_filename)

        try:
            with open(new_file_path, 'w', encoding='utf-8') as f:
                f.write(processed_content)
            return new_file_path
        except Exception as e:
            print(f"Error al escribir el archivo procesado {new_file_path}: {e}")
            return ""

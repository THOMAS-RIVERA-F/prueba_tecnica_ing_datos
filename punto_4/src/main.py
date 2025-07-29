import os
from .core.html_processor import HtmlProcessor


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    html_root_directory = os.path.join(project_root, "test_html_files") 

    results_directory = os.path.join(project_root, "results")
    os.makedirs(results_directory, exist_ok=True)

    processor = HtmlProcessor(html_root_directory, results_directory)
    image_processing_summary = processor.process_all_html_files()
    print("\nResumen del procesamiento de imágenes:")
    print(f"  Imágenes procesadas exitosamente: {len(image_processing_summary["success"])}")
    for original_src, absolute_path in image_processing_summary["success"].items():
        print(f"    - {original_src} (Ruta absoluta: {absolute_path})")
    
    print(f"  Imágenes que fallaron: {len(image_processing_summary["fail"])}")
    for original_src, error_message in image_processing_summary["fail"].items():
        print(f"    - {original_src} (Error: {error_message})")
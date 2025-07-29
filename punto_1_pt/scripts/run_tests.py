#!/usr/bin/env python3
"""
Script para ejecutar las pruebas del proyecto de números de teléfono.
Incluye pruebas unitarias, de integración y generación de reportes.
"""

import subprocess
import sys
import os
from datetime import datetime

def run_command(command, description):
    """Ejecuta un comando y muestra el resultado"""
    print(f"\n{description}")
    print(f"Comando: {command}")
    print("-" * 50)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"{description} - EXITOSO")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"{description} - FALLO")
            if result.stderr:
                print("Error:", result.stderr)
            if result.stdout:
                print("Output:", result.stdout)
            return False
    except Exception as e:
        print(f"Error ejecutando comando: {e}")
        return False
    
    return True

def main():
    """Función principal para ejecutar todas las pruebas"""
    print("Iniciando suite de pruebas del proyecto")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Cambiar al directorio raíz del proyecto
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    print(f"Directorio de trabajo: {project_root}")
    
    # Lista de comandos a ejecutar
    test_commands = [
        {
            "command": "python -m pytest tests/ -v",
            "description": "Ejecutar todas las pruebas unitarias"
        },
        {
            "command": "python -m pytest tests/test_phone_validation.py -v",
            "description": "Pruebas de validación de teléfonos"
        },
        {
            "command": "python -m pytest tests/test_database.py -v",
            "description": "Pruebas de base de datos"
        },
        {
            "command": "python -m pytest tests/ --cov=src --cov=config --cov-report=html --cov-report=term",
            "description": "Pruebas con cobertura de código"
        }
    ]
    
    # Ejecutar cada comando
    all_passed = True
    for test in test_commands:
        success = run_command(test["command"], test["description"])
        if not success:
            all_passed = False
    
    # Resumen final
    print("\n" + "=" * 60)
    if all_passed:
        print("TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
        print("El código está listo para producción")
    else:
        print("ALGUNAS PRUEBAS FALLARON")
        print("Revisar los errores antes de desplegar")
        sys.exit(1)
    
    print(f"\nReporte de cobertura generado en: htmlcov/index.html")
    print("Suite de pruebas completada")

if __name__ == "__main__":
    main() 
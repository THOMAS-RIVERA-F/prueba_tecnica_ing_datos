import pytest
import pandas as pd
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from clean_data import clean_phone_numbers

class TestPhoneValidation:
    
    def test_valid_colombian_mobile_numbers(self):
        """Prueba que números válidos de celular colombiano se procesen correctamente"""
        test_data = pd.DataFrame({
            'id_cliente': ['C0001', 'C0002'],
            'nombre': ['Cliente 1', 'Cliente 2'],
            'celular': ['3001234567', '3109876543'],
            'tipo_numero': ['móvil', 'móvil'],
            'fecha_registro': ['2024-01-01', '2024-01-02'],
            'canal_obtencion': ['Web', 'PCO'],
            'consentimiento_contacto': [True, False]
        })
        
        result = clean_phone_numbers(test_data)
        
        assert len(result) == 2
        assert '+573001234567' in result['celular_limpio'].values
        assert '+573109876543' in result['celular_limpio'].values
    
    def test_remove_invalid_numbers(self):
        """Prueba que números inválidos se eliminen"""
        test_data = pd.DataFrame({
            'id_cliente': ['C0001', 'C0002', 'C0003'],
            'nombre': ['Cliente 1', 'Cliente 2', 'Cliente 3'],
            'celular': ['3001234567', '1234567890', ''],  # Válido, inválido, vacío
            'tipo_numero': ['móvil', 'móvil', 'móvil'],
            'fecha_registro': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'canal_obtencion': ['Web', 'PCO', 'Web'],
            'consentimiento_contacto': [True, False, True]
        })
        
        result = clean_phone_numbers(test_data)
        
        assert len(result) == 1  # Solo el número válido debe permanecer
        assert '+573001234567' in result['celular_limpio'].values
    
    def test_remove_duplicates(self):
        """Prueba que números duplicados se eliminen"""
        test_data = pd.DataFrame({
            'id_cliente': ['C0001', 'C0002', 'C0003'],
            'nombre': ['Cliente 1', 'Cliente 2', 'Cliente 3'],
            'celular': ['3001234567', '3001234567', '3109876543'],  # Dos iguales
            'tipo_numero': ['móvil', 'móvil', 'móvil'],
            'fecha_registro': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'canal_obtencion': ['Web', 'PCO', 'Web'],
            'consentimiento_contacto': [True, False, True]
        })
        
        result = clean_phone_numbers(test_data)
        
        assert len(result) == 2  # Solo dos números únicos deben permanecer
        unique_numbers = result['celular_limpio'].unique()
        assert '+573001234567' in unique_numbers
        assert '+573109876543' in unique_numbers
    
    def test_handle_null_values(self):
        """Prueba que valores nulos se manejen correctamente"""
        test_data = pd.DataFrame({
            'id_cliente': ['C0001', 'C0002'],
            'nombre': ['Cliente 1', 'Cliente 2'],
            'celular': ['3001234567', None],
            'tipo_numero': ['móvil', 'móvil'],
            'fecha_registro': ['2024-01-01', '2024-01-02'],
            'canal_obtencion': ['Web', 'PCO'],
            'consentimiento_contacto': [True, False]
        })
        
        result = clean_phone_numbers(test_data)
        
        assert len(result) == 1  # Solo el registro con número válido
        assert result.iloc[0]['id_cliente'] == 'C0001'
    
    def test_preserve_other_columns(self):
        """Prueba que las otras columnas se mantengan intactas"""
        test_data = pd.DataFrame({
            'id_cliente': ['C0001'],
            'nombre': ['Cliente Prueba'],
            'celular': ['3001234567'],
            'tipo_numero': ['móvil'],
            'fecha_registro': ['2024-01-01 10:30:00'],
            'canal_obtencion': ['Web'],
            'consentimiento_contacto': [True]
        })
        
        result = clean_phone_numbers(test_data)
        
        assert result.iloc[0]['id_cliente'] == 'C0001'
        assert result.iloc[0]['nombre'] == 'Cliente Prueba'
        assert result.iloc[0]['tipo_numero'] == 'móvil'
        assert result.iloc[0]['fecha_registro'] == '2024-01-01 10:30:00'
        assert result.iloc[0]['canal_obtencion'] == 'Web'
        assert result.iloc[0]['consentimiento_contacto'] == True
    
    def test_e164_format(self):
        """Prueba que los números se formateen correctamente en E.164"""
        test_data = pd.DataFrame({
            'id_cliente': ['C0001', 'C0002'],
            'nombre': ['Cliente 1', 'Cliente 2'],
            'celular': ['3001234567', '+573109876543'],  # Con y sin prefijo
            'tipo_numero': ['móvil', 'móvil'],
            'fecha_registro': ['2024-01-01', '2024-01-02'],
            'canal_obtencion': ['Web', 'PCO'],
            'consentimiento_contacto': [True, False]
        })
        
        result = clean_phone_numbers(test_data)
        
        # Ambos deben estar en formato E.164
        for number in result['celular_limpio']:
            assert number.startswith('+57')
            assert len(number) == 13  # +57 + 10 dígitos
    
    def test_empty_dataframe(self):
        """Prueba el manejo de DataFrame vacío"""
        test_data = pd.DataFrame(columns=[
            'id_cliente', 'nombre', 'celular', 'tipo_numero', 
            'fecha_registro', 'canal_obtencion', 'consentimiento_contacto'
        ])
        
        result = clean_phone_numbers(test_data)
        
        assert len(result) == 0
        assert 'celular_limpio' in result.columns 
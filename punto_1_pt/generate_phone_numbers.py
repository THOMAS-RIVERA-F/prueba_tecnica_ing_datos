
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_colombian_mobile_numbers(num_numbers):
    """
    Genera una lista de números de celular dummy colombianos (10 dígitos, empiezan por 3).
    """
    phone_numbers = []
    for _ in range(num_numbers):
        # Los números de celular colombianos tienen 10 dígitos y empiezan por 3
        # Generamos los 9 dígitos restantes de forma aleatoria
        # Para asegurar que el segundo y tercer dígito también son aleatorios (ej. 3xx)
        second_digit = str(np.random.randint(0, 10))
        third_digit = str(np.random.randint(0, 10))
        remaining_digits = ''.join(np.random.choice([str(i) for i in range(10)], 7))
        phone_number = f"3{second_digit}{third_digit}{remaining_digits}"
        phone_numbers.append(phone_number)
    return phone_numbers

def create_customer_dataframe(num_customers=100):
    """
    Crea un DataFrame de Pandas con información de contacto de celular dummy para clientes colombianos.
    """
    mobile_numbers = generate_colombian_mobile_numbers(num_customers)
    
    data = {
        'id_cliente': [f'C{i+1:04d}' for i in range(num_customers)],
        'nombre': [f'Cliente {i+1}' for i in range(num_customers)],
        'celular': mobile_numbers,
        'tipo_numero': ['móvil'] * num_customers, # Siempre móvil
        'fecha_registro': [datetime.now() - timedelta(days=np.random.randint(1, 365*3)) for _ in range(num_customers)], # Fechas de los últimos 3 años
        'canal_obtencion': np.random.choice(['Web', 'PCO', 'instagram'], num_customers),
        'consentimiento_contacto': np.random.choice([True, False], num_customers, p=[0.8, 0.2]) # 80% True, 20% False
    }
    
    df = pd.DataFrame(data)
    return df

if __name__ == "__main__":
    df_customers = create_customer_dataframe(num_customers=50)
    # Guardar todo el DataFrame en el archivo de entrada
    df_customers.to_csv('input/raw_numeros.csv', index=False)
    print("DataFrame completo de clientes con números de celular dummy generado y guardado en input/raw_numeros.csv") 
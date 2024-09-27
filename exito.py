import streamlit as st
import requests
from urllib.parse import urlparse
import re
import json
import matplotlib.pyplot as plt
import io

# Función para extraer subdominios
def extraer_subdominios(domain, api_key):
    url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": f"site:*.{domain} -site:www.{domain}",
        "num": 100
    })
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    response.raise_for_status()
    
    results = response.json().get('organic', [])
    subdominios = set()
    for result in results:
        parsed_url = urlparse(result['link'])
        if parsed_url.netloc.endswith(domain) and parsed_url.netloc != domain:
            subdominios.add(parsed_url.netloc)
    
    return list(subdominios)

# Función para obtener búsqueda de Serper
def obtener_busqueda_serper(query, api_key):
    url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": query,
        "num": 10
    })
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    response.raise_for_status()
    
    results = response.json()
    summary = ""
    for result in results.get('organic', []):
        summary += f"{result['title']}\n{result['snippet']}\n\n"
    
    return summary

# Función para obtener análisis de Together
def obtener_analisis_together(summary, api_key):
    url = "https://api.together.xyz/v1/completions"
    payload = json.dumps({
        "model": "together/llama-2-70b-chat",
        "prompt": f"Analiza el siguiente resumen y proporciona un análisis detallado del potencial de éxito de la plataforma digital, incluyendo recomendaciones para mejorar y una estimación del máximo de visitantes diarios:\n\n{summary}",
        "max_tokens": 1000,
        "temperature": 0.7
    })
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    response.raise_for_status()
    
    return response.json()['choices'][0]['text']

# Función para generar gráficas
def generar_graficas(secciones):
    plots = {}
    for titulo, contenido in secciones.items():
        if titulo == "Estimación de Visitantes Diarios":
            # Extraer el número de visitantes del contenido
            match = re.search(r'(\d+(?:,\d+)?)', contenido)
            if match:
                visitantes = int(match.group(1).replace(',', ''))
                fig, ax = plt.subplots()
                ax.bar(['Estimación'], [visitantes])
                ax.set_ylabel('Número de Visitantes')
                ax.set_title('Estimación de Visitantes Diarios')
                
                # Guardar la figura en un buffer
                buf = io.BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)
                plots[titulo] = buf
    
    return plots

def main():
    # (El resto del código main permanece igual)
    # ...

if __name__ == "__main__":
    main()

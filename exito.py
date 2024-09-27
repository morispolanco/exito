import streamlit as st
import requests
from urllib.parse import urlparse
import re
import json
import matplotlib.pyplot as plt
import io

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

# Función actualizada para obtener análisis de Together
def obtener_analisis_together(summary, api_key):
    url = "https://api.together.xyz/v1/completions"
    payload = {
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",  # Se ha cambiado el modelo aquí
        "prompt": f"Human: Analiza el siguiente resumen y proporciona un análisis detallado del potencial de éxito de la plataforma digital, incluyendo recomendaciones para mejorar y una estimación del máximo de visitantes diarios:\n\n{summary}\n\nAssistant: Basado en el resumen proporcionado, aquí está mi análisis detallado del potencial de éxito de la plataforma digital:",
        "max_tokens": 1000,
        "temperature": 0.7,
        "top_p": 0.7,
        "top_k": 50,
        "repetition_penalty": 1,
        "stop": ["Human:", "Assistant:"]
    }
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    
    return response.json()['choices'][0]['text'].strip()

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

# Función principal
def main():
    # Dividimos la interfaz en dos columnas
    col1, col2 = st.columns([1, 2])

    # En la columna izquierda (col1), ponemos la explicación
    with col1:
        st.markdown("""
        ### 🤔 ¿Qué es esta aplicación?

        Esta aplicación realiza un análisis del **potencial de éxito** de plataformas digitales basadas en su URL. Para esto, utiliza varias fuentes y herramientas, como las APIs de **Serper** y **Together**.

        ### 🚀 ¿Qué hace?

        - Toma la URL de una plataforma digital (por ejemplo, un sitio web).
        - Utiliza la API de Serper para obtener información relacionada con esa URL.
        - A través de la API de Together, genera un análisis detallado que incluye recomendaciones para mejorar la plataforma y una estimación de cuántos visitantes diarios podría recibir.

        ### ❌ ¿Qué no hace?

        - No analiza subdominios ni subdirectorios, solo el dominio principal.
        - No realiza análisis de seguridad del sitio web.
        - No analiza el contenido completo del sitio, solo utiliza la información disponible públicamente y procesada por motores de búsqueda.
        - No garantiza que las proyecciones de visitantes sean completamente exactas, ya que dependen de factores externos como el mercado o la competencia.

        **Es una herramienta de evaluación preliminar** para obtener una idea del rendimiento potencial de una plataforma digital.
        """)

    # En la columna derecha (col2), ponemos el análisis
    with col2:
        # Título de la aplicación
        st.title("📈 Análisis de Potencial de Éxito de Plataformas Digitales")

        # Entrada de la URL
        url_input = st.text_input("🔗 Ingresa la URL de la plataforma digital que deseas analizar:", "")

        # Botón para iniciar el análisis
        if st.button("✅ Analizar"):
            if not url_input:
                st.error("⚠️ Por favor, ingresa una URL válida.")
            else:
                try:
                    # Validar y formatear la URL
                    parsed_url = urlparse(url_input)
                    if not parsed_url.scheme:
                        url_input = "https://" + url_input  # Preferir HTTPS
                        parsed_url = urlparse(url_input)

                    domain = parsed_url.netloc
                    if not domain:
                        st.error("⚠️ URL inválida. Por favor, intenta nuevamente.")
                        return

                    # Mostrar la URL que se analizará
                    st.write(f"**URL a analizar:** {url_input}")

                    # Verificar acceso a la URL
                    try:
                        response = requests.get(url_input, timeout=10)
                        response.raise_for_status()
                    except requests.exceptions.HTTPError as http_err:
                        st.error(f"⚠️ Error HTTP al acceder a la URL: {http_err}")
                        return
                    except requests.exceptions.ConnectionError:
                        st.error("⚠️ Error de conexión. Verifica tu red y la URL ingresada.")
                        return
                    except requests.exceptions.Timeout:
                        st.error("⚠️ Tiempo de espera excedido al intentar acceder a la URL.")
                        return
                    except requests.exceptions.RequestException as e:
                        st.error(f"⚠️ Error al acceder a la URL: {e}")
                        return

                    st.info("🔄 Procesando la URL...")

                    # Realizar búsqueda con Serper API para obtener información del dominio
                    serper_api_key = st.secrets["serper_api_key"]
                    query = f"Información sobre {domain}"
                    with st.spinner(f"🧠 Analizando {domain} con Together..."):
                        try:
                            search_summary = obtener_busqueda_serper(query, serper_api_key)
                            if not search_summary:
                                st.warning(f"⚠️ No se encontró información relevante para {domain}.")
                                return
                            analysis = obtener_analisis_together(search_summary, st.secrets["together_api_key"])
                        except requests.exceptions.HTTPError as http_err:
                            st.error(f"❌ Error HTTP al acceder a la API: {http_err}")
                            st.error(f"Detalles de la respuesta: {http_err.response.text}")
                            return
                        except requests.exceptions.RequestException as e:
                            st.error(f"❌ Error al acceder a la API: {e}")
                            return
                        except ValueError as ve:
                            st.error(f"❌ {ve}")
                            return
                        except Exception as e:
                            st.error(f"❌ Error inesperado: {str(e)}")
                            return

                        # Procesar y unificar el análisis
                        # Separar el análisis en secciones utilizando títulos en negrita
                        secciones = {}
                        current_section = None
                        for line in analysis.split('\n'):
                            line = line.strip()
                            match = re.match(r'\*\*(.*?)\*\*:', line)
                            if match:
                                section_title = match.group(1).strip()
                                secciones[section_title] = ""
                                current_section = section_title
                            elif current_section:
                                secciones[current_section] += line + "\n"

                        # Manejar caso sin secciones
                        if not secciones:
                            secciones["Contenido"] = analysis

                        # Generar las gráficas y obtener los buffers de imagen
                        plots = generar_graficas(secciones)

                        # Mostrar el análisis para el dominio/subdominio
                        with st.container():
                            st.subheader("📊 Análisis Unificado")
                            for titulo, contenido in secciones.items():
                                st.markdown(f"### 📌 **{titulo}**")
                                st.write(contenido)

                                # Incluir visualizaciones dentro de las secciones pertinentes
                                if titulo in plots:
                                    # Mostrar la gráfica en Streamlit
                                    st.image(plots[titulo], use_column_width=True)

                                    # Agregar explicación detallada para la estimación de visitantes diarios
                                    if titulo == "Estimación de Visitantes Diarios":
                                        st.markdown("""
                                        **¿Cómo se estima el número máximo de visitantes diarios?**
                                        Esta estimación se basa en el análisis de la información recopilada sobre la plataforma,
                                        incluyendo factores como el tráfico actual, el nicho de mercado, la competencia y el potencial de crecimiento.
                                        Es una proyección aproximada y puede variar según diversos factores externos.
                                        """)

                except Exception as e:
                    st.error(f"❌ Se produjo un error inesperado: {str(e)}")

if __name__ == "__main__":
    main()

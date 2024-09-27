import streamlit as st
import requests
from urllib.parse import urlparse
import matplotlib.pyplot as plt
import re
from io import BytesIO

# ============================================
# Funciones Auxiliares
# ============================================

def parse_number(text):
    """
    Función para parsear números con diferentes formatos.
    Convierte cadenas de texto a números flotantes.
    """
    text = re.sub(r'[^\d.,]', '', text)
    if text.count(',') > text.count('.'):
        text = text.replace('.', '').replace(',', '.')
    else:
        text = text.replace(',', '')
    try:
        return float(text)
    except ValueError:
        return None

@st.cache_data(show_spinner=False)
def obtener_busqueda_serper(query, api_key):
    """
    Función para obtener resultados de búsqueda utilizando la API de Serper.
    Retorna una lista de URLs encontradas en los resultados de búsqueda.
    """
    serper_url = "https://google.serper.dev/search"
    headers_serper = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    data_serper = {"q": query}
    response_serper = requests.post(serper_url, headers=headers_serper, json=data_serper, timeout=10)
    response_serper.raise_for_status()
    search_results = response_serper.json()
    urls = []
    if "organic" in search_results:
        for item in search_results["organic"]:
            if "link" in item:
                urls.append(item["link"])
    return urls if urls else []

@st.cache_data(show_spinner=False)
def obtener_analisis_together(search_summary, api_key):
    """
    Función para obtener análisis detallado utilizando la API de Together.
    Retorna el contenido del análisis.
    """
    together_url = "https://api.together.xyz/v1/chat/completions"
    headers_together = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    messages = [
        {
            "role": "system",
            "content": (
                "Eres un experto en análisis de plataformas digitales con un enfoque en las demandas del mercado actual. "
                "Proporciona una evaluación detallada del potencial de éxito de la plataforma digital basada en la siguiente información. "
                "Incluye recomendaciones sobre aspectos de forma (diseño, usabilidad, interfaz) y fondo (funcionalidades, contenido, estrategia de mercado), señalando lo que sobra y lo que falta. "
                "Además, expresa el potencial de éxito en términos de porcentaje, proporciona una estimación del máximo de visitantes al día y un resumen ejecutivo de los hallazgos clave."
                "\n\n"
                "Nota: La estimación de visitantes diarios se basa en la versión mejorada de la plataforma, incorporando los cambios sugeridos."
            )
        },
        {
            "role": "user",
            "content": f"Aquí hay información sobre la plataforma: {search_summary}"
        }
    ]
    data_together = {
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "messages": messages,
        "max_tokens": 2512,
        "temperature": 0.7,
        "top_p": 0.7,
        "top_k": 50,
        "repetition_penalty": 1,
        "stop": ["<|eot_id|>"],
        "stream": False
    }

    response_together = requests.post(together_url, headers=headers_together, json=data_together, timeout=30)
    response_together.raise_for_status()
    analysis = response_together.json()
    if "choices" in analysis and len(analysis["choices"]) > 0:
        return analysis["choices"][0]["message"]["content"]
    else:
        raise ValueError("Respuesta inesperada de Together API.")

def generar_graficas(secciones):
    """
    Función para generar las gráficas necesarias basadas en las secciones del análisis.
    Retorna un diccionario con el título de la sección y el buffer de la imagen.
    """
    plots = {}
    # Potencial de Éxito
    if "Potencial de Éxito" in secciones:
        porcentaje_val = parse_number(secciones["Potencial de Éxito"])
        if porcentaje_val is not None:
            fig, ax = plt.subplots(figsize=(2, 2))
            ax.pie([porcentaje_val, 100 - porcentaje_val], colors=['#4CAF50', '#CCCCCC'], startangle=90, counterclock=False)
            ax.axis('equal')
            buf = BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight')
            plt.close(fig)
            buf.seek(0)
            plots["Potencial de Éxito"] = buf

    # Estimación de Visitantes Diarios
    if "Estimación de Visitantes Diarios" in secciones:
        est_visitors_val = parse_number(secciones["Estimación de Visitantes Diarios"])
        if est_visitors_val is not None:
            est_visitors_val = int(est_visitors_val)
            fig, ax = plt.subplots(figsize=(4, 1))
            ax.barh([''], [est_visitors_val], color='#4CAF50')
            ax.set_xlim(0, est_visitors_val * 1.2)
            ax.set_xlabel('Número de Visitantes')
            ax.set_yticks([])
            plt.tight_layout()
            buf = BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight')
            plt.close(fig)
            buf.seek(0)
            plots["Estimación de Visitantes Diarios"] = buf

    return plots

def extraer_subdominios(domain, serper_api_key):
    """
    Función para extraer subdominios utilizando la API de Serper.
    Retorna una lista de subdominios únicos.
    """
    query = f"site:{domain}"
    urls = obtener_busqueda_serper(query, serper_api_key)
    subdominios_unicos = set()

    for url in urls:
        parsed_url = urlparse(url)
        subdomain = parsed_url.netloc
        if subdomain and subdomain != domain:
            subdominios_unicos.add(subdomain)

    return list(subdominios_unicos)

# ============================================
# Aplicación Streamlit
# ============================================

def main():
    # Título de la aplicación
    st.title("📈 Análisis de Potencial de Éxito de Plataformas Digitales")

    # Descripción de la aplicación
    st.markdown("""
    Esta aplicación analiza el potencial de éxito de una plataforma digital basada en su URL. Utiliza las APIs de Serper para obtener información relevante sobre la plataforma y de Together para evaluar su potencial en el mercado actual. Además, proporciona recomendaciones detalladas para mejorar tanto en forma como en contenido, así como una estimación del máximo de visitantes diarios que puede recibir la plataforma.

    **Funcionalidades Adicionales:**
    - **Análisis de Subdominios:** La aplicación identificará y analizará automáticamente todos los subdominios asociados al dominio principal proporcionado.
    """)

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
                    st.stop()

                # Mostrar la URL que se analizará
                st.write(f"**URL a analizar:** {url_input}")

                # Verificar acceso a la URL
                try:
                    response = requests.get(url_input, timeout=10)
                    response.raise_for_status()
                except requests.exceptions.HTTPError as http_err:
                    st.error(f"⚠️ Error HTTP al acceder a la URL: {http_err}")
                    st.stop()
                except requests.exceptions.ConnectionError:
                    st.error("⚠️ Error de conexión. Verifica tu red y la URL ingresada.")
                    st.stop()
                except requests.exceptions.Timeout:
                    st.error("⚠️ Tiempo de espera excedido al intentar acceder a la URL.")
                    st.stop()
                except requests.exceptions.RequestException as e:
                    st.error(f"⚠️ Error al acceder a la URL: {e}")
                    st.stop()

                st.info("🔄 Procesando la URL...")

                # Realizar búsqueda con Serper API para obtener subdominios
                serper_api_key = st.secrets["serper_api_key"]
                with st.spinner("🔍 Buscando subdominios con Serper..."):
                    try:
                        subdominios = extraer_subdominios(domain, serper_api_key)
                    except requests.exceptions.HTTPError as http_err:
                        st.error(f"❌ Error HTTP al acceder a Serper API: {http_err}")
                        st.stop()
                    except requests.exceptions.RequestException as e:
                        st.error(f"❌ Error al acceder a Serper API: {e}")
                        st.stop()

                if subdominios:
                    st.success(f"✅ Se encontraron {len(subdominios)} subdominio(s).")
                else:
                    st.warning("⚠️ No se encontraron subdominios para analizar.")

                # Agregar el dominio principal a la lista de subdominios para análisis
                todos_los_dominios = [domain] + subdominios

                # Preparar una estructura para almacenar los análisis
                analisis_resultados = {}

                for dom in todos_los_dominios:
                    st.write(f"### 🔍 **Analizando:** {dom}")
                    # Realizar búsqueda con Serper API para obtener información del dominio
                    query = f"Información sobre {dom}"
                    with st.spinner(f"🧠 Analizando {dom} con Together..."):
                        try:
                            search_summary = obtener_busqueda_serper(query, serper_api_key)
                            if not search_summary:
                                st.warning(f"⚠️ No se encontró información relevante para {dom}.")
                                analisis_resultados[dom] = "No se encontró información relevante."
                                continue
                            analysis = obtener_analisis_together(search_summary, st.secrets["together_api_key"])
                            analisis_resultados[dom] = analysis
                        except requests.exceptions.HTTPError as http_err:
                            st.error(f"❌ Error HTTP al acceder a la API: {http_err}")
                            analisis_resultados[dom] = "Error en el análisis."
                            continue
                        except requests.exceptions.RequestException as e:
                            st.error(f"❌ Error al acceder a la API: {e}")
                            analisis_resultados[dom] = "Error en el análisis."
                            continue
                        except ValueError as ve:
                            st.error(f"❌ {ve}")
                            analisis_resultados[dom] = "Error en el análisis."
                            continue

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
                                    
                                    La estimación de visitantes diarios se basa en un análisis detallado de la plataforma digital, considerando varios factores clave que influyen en su capacidad de atraer y retener usuarios. A continuación, se detallan los aspectos considerados para esta estimación:
                                    
                                    1. **Optimización de la Usabilidad y Diseño:**
                                       - **Mejoras en la Interfaz de Usuario (UI):** Un diseño intuitivo y atractivo facilita la navegación y mejora la experiencia del usuario, lo que puede incrementar la retención y la recomendación boca a boca.
                                       - **Responsive Design:** La adaptación del sitio web a diferentes dispositivos (móviles, tabletas, computadoras) asegura que una mayor audiencia pueda acceder y utilizar la plataforma sin inconvenientes.
                                    
                                    2. **Contenido Relevante y de Calidad:**
                                       - **Actualización Regular del Contenido:** Mantener el contenido fresco y actualizado atrae a usuarios recurrentes y mejora el posicionamiento en motores de búsqueda.
                                       - **SEO (Search Engine Optimization):** La optimización para motores de búsqueda incrementa la visibilidad de la plataforma, atrayendo más tráfico orgánico.
                                    
                                    3. **Estrategias de Marketing y Promoción:**
                                       - **Campañas de Marketing Digital:** Utilizar canales como redes sociales, correo electrónico y publicidad pagada puede aumentar significativamente el tráfico hacia la plataforma.
                                       - **Colaboraciones y Alianzas Estratégicas:** Asociarse con otras empresas o influencers puede ampliar la base de usuarios potenciales.
                                    
                                    4. **Funcionalidades Mejoradas:**
                                       - **Integración de Funcionalidades Clave:** Incorporar herramientas y características que satisfagan las necesidades de los usuarios puede aumentar el tiempo de permanencia y la frecuencia de visitas.
                                       - **Análisis de Datos y Personalización:** Utilizar datos para personalizar la experiencia del usuario mejora la satisfacción y fomenta la lealtad.
                                    
                                    5. **Soporte y Atención al Cliente:**
                                       - **Canales de Soporte Eficientes:** Ofrecer soporte rápido y efectivo resuelve problemas de usuarios y mejora la percepción general de la plataforma.
                                    
                                    **Conclusión:** 
                                    
                                    Al implementar las mejoras sugeridas en estos aspectos, se espera que la plataforma digital no solo aumente su atractivo y funcionalidad, sino que también mejore su capacidad para atraer y retener un mayor número de visitantes diarios. La combinación de un diseño optimizado, contenido de calidad, estrategias de marketing efectivas y funcionalidades avanzadas contribuye significativamente a la estimación del número máximo de visitantes diarios.
                                    """)

    # Ejecutar la aplicación
    if __name__ == "__main__":
    main()


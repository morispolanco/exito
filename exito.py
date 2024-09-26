import streamlit as st
import requests
from urllib.parse import urlparse
import matplotlib.pyplot as plt
import re
from io import BytesIO
import pyperclip  # Para copiar al portapapeles

# Función para parsear números con diferentes formatos
def parse_number(text):
    text = re.sub(r'[^\d.,]', '', text)
    if text.count(',') > text.count('.'):
        text = text.replace('.', '').replace(',', '.')
    else:
        text = text.replace(',', '')
    try:
        return float(text)
    except ValueError:
        return None

# Función para obtener resultados de Serper con caché
@st.cache_data(show_spinner=False)
def obtener_busqueda_serper(query, api_key):
    serper_url = "https://google.serper.dev/search"
    headers_serper = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    data_serper = {"q": query}
    response_serper = requests.post(serper_url, headers=headers_serper, json=data_serper, timeout=10)
    response_serper.raise_for_status()
    search_results = response_serper.json()
    snippets = []
    if "organic" in search_results:
        for item in search_results["organic"]:
            if "snippet" in item:
                snippets.append(item["snippet"])
    return "\n\n".join(snippets) if snippets else "No se encontraron resultados relevantes."

# Función para obtener análisis de Together con caché
@st.cache_data(show_spinner=False)
def obtener_analisis_together(search_summary, api_key):
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

# Función para generar las gráficas y retornarlas como buffers
def generar_graficas(secciones):
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

# Función para generar el PDF (Eliminada)
# Se ha removido toda la funcionalidad relacionada con la generación de PDF.

# Título de la aplicación
st.title("📈 Análisis de Potencial de Éxito de Plataformas Digitales")

# Descripción de la aplicación
st.markdown("""
Esta aplicación analiza el potencial de éxito de una plataforma digital basada en su URL. Utiliza las APIs de Serper para obtener información relevante sobre la plataforma y de Together para evaluar su potencial en el mercado actual. Además, proporciona recomendaciones detalladas para mejorar tanto en forma como en contenido, así como una estimación del máximo de visitantes diarios que puede recibir la plataforma.
""")

# Entrada de la URL
url_input = st.text_input("🔗 Ingresa la URL de la plataforma digital que deseas analizar:", "")

# Botón para iniciar el análisis
if st.button("✅ Analizar"):
    if not url_input:
        st.error("⚠️ Por favor, ingresa una URL válida.")
    else:
        # Validar y formatear la URL
        parsed_url = urlparse(url_input)
        if not parsed_url.scheme:
            url_input = "https://" + url_input  # Preferir HTTPS
            parsed_url = urlparse(url_input)

        domain = parsed_url.netloc
        if not domain:
            st.error("⚠️ URL inválida. Por favor, intenta nuevamente.")
            st.stop()

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

        # Realizar búsqueda con Serper API
        serper_api_key = st.secrets["serper_api_key"]
        query = f"Información sobre {domain}"

        with st.spinner("🔍 Realizando búsqueda con Serper..."):
            try:
                search_summary = obtener_busqueda_serper(query, serper_api_key)
            except requests.exceptions.HTTPError as http_err:
                st.error(f"❌ Error HTTP al acceder a Serper API: {http_err}")
                st.stop()
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Error al acceder a Serper API: {e}")
                st.stop()

        # Preparar el mensaje para Together API
        together_api_key = st.secrets["together_api_key"]

        with st.spinner("🧠 Analizando con Together..."):
            try:
                result = obtener_analisis_together(search_summary, together_api_key)
            except requests.exceptions.HTTPError as http_err:
                st.error(f"❌ Error HTTP al acceder a Together API: {http_err}")
                st.stop()
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Error al acceder a Together API: {e}")
                st.stop()
            except ValueError as ve:
                st.error(f"❌ {ve}")
                st.stop()

        # Procesar y unificar el análisis
        # Separar el análisis en secciones utilizando títulos en negrita
        secciones = {}
        current_section = None
        for line in result.split('\n'):
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
            secciones["Contenido"] = result

        # Generar las gráficas y obtener los buffers de imagen
        plots = generar_graficas(secciones)

        # Crear un contenedor para unificar el análisis
        with st.container():
            st.subheader("📊 Análisis Unificado")
            for titulo, contenido in secciones.items():
                st.markdown(f"### 📌 **{titulo}**")
                st.write(contenido)

                # Incluir visualizaciones dentro de las secciones pertinentes
                if titulo in plots:
                    # Mostrar la gráfica en Streamlit
                    st.image(plots[titulo], use_column_width=True)

                    # Opcional: Agregar descripciones adicionales si es necesario
                    if titulo == "Potencial de Éxito":
                        porcentaje_val = parse_number(contenido)
                        if porcentaje_val is not None:
                            st.markdown(f"**Potencial de Éxito: {porcentaje_val}%**")
                    elif titulo == "Estimación de Visitantes Diarios":
                        est_visitors_val = parse_number(contenido)
                        if est_visitors_val is not None:
                            est_visitors_val = int(est_visitors_val)
                            st.markdown("**La estimación de visitantes diarios se basa en la versión mejorada de la plataforma, incorporando los cambios sugeridos.**")
                            st.metric(label="Máximo de Visitantes al Día", value=f"{est_visitors_val:,}")

        # Generar el texto completo del análisis para copiar
        analisis_completo = ""
        for titulo, contenido in secciones.items():
            analisis_completo += f"**{titulo}:**\n{contenido}\n\n"

        # Botón para copiar el análisis al portapapeles
        # Utilizaremos pyperclip para copiar el texto. Sin embargo, pyperclip puede no funcionar en entornos web como Streamlit.
        # Por lo tanto, proporcionaremos el análisis en un área de texto para que el usuario lo copie manualmente.
        st.subheader("📋 Copiar Análisis")
        st.text_area("Análisis Completo", analisis_completo, height=300)

        st.info("Puedes copiar el análisis completo desde el área de texto de arriba.")

        # Alternativamente, si deseas utilizar un botón de copiar con JavaScript, puedes hacerlo mediante componentes personalizados.
        # Aquí te proporciono una forma sencilla utilizando HTML y JavaScript:
        copy_button_html = f"""
        <button onclick="navigator.clipboard.writeText(`{analisis_completo}`)" style="background-color:#4CAF50;color:white;padding:10px 20px;border:none;border-radius:5px;cursor:pointer;">
            📋 Copiar Análisis
        </button>
        """
        st.markdown(copy_button_html, unsafe_allow_html=True)

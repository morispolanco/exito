import streamlit as st
import requests
import json
from urllib.parse import urlparse
from io import BytesIO
from docx import Document
from docx.shared import Inches
import matplotlib.pyplot as plt
import re

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
        serper_url = "https://google.serper.dev/search"
        headers_serper = {
            "X-API-KEY": serper_api_key,
            "Content-Type": "application/json"
        }
        query = f"Información sobre {domain}"
        data_serper = {
            "q": query
        }

        with st.spinner("🔍 Realizando búsqueda con Serper..."):
            try:
                response_serper = requests.post(serper_url, headers=headers_serper, json=data_serper, timeout=10)
                response_serper.raise_for_status()
                search_results = response_serper.json()
                snippets = []
                if "organic" in search_results:
                    for item in search_results["organic"]:
                        if "snippet" in item:
                            snippets.append(item["snippet"])
                search_summary = "\n\n".join(snippets) if snippets else "No se encontraron resultados relevantes."
            except requests.exceptions.HTTPError as http_err:
                st.error(f"❌ Error HTTP al acceder a Serper API: {http_err}")
                st.stop()
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Error al acceder a Serper API: {e}")
                st.stop()

        # Preparar el mensaje para Together API
        together_api_key = st.secrets["together_api_key"]
        together_url = "https://api.together.xyz/v1/chat/completions"
        headers_together = {
            "Authorization": f"Bearer {together_api_key}",
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

        # Realizar solicitud a Together API
        with st.spinner("🧠 Analizando con Together..."):
            try:
                response_together = requests.post(together_url, headers=headers_together, json=data_together, timeout=30)
                response_together.raise_for_status()
                analysis = response_together.json()
                if "choices" in analysis and len(analysis["choices"]) > 0:
                    result = analysis["choices"][0]["message"]["content"]

                    # Mostrar la respuesta completa para depuración
                    st.subheader("📄 Respuesta de la API de Together")
                    st.write(result)

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

                    # Depuración: Mostrar las secciones detectadas
                    st.subheader("🔍 Secciones Detectadas")
                    st.write(list(secciones.keys()))

                    # Crear un documento DOCX
                    doc = Document()
                    doc.add_heading('Análisis de Potencial de Éxito', 0)

                    # Procesar cada sección
                    for titulo, contenido in secciones.items():
                        # Agregar encabezado al DOCX
                        doc.add_heading(f"📌 {titulo}", level=1)
                        doc.add_paragraph(contenido)

                        # Mostrar en Streamlit
                        st.subheader(f"📌 {titulo}")
                        st.write(contenido)

                        # Manejar secciones específicas
                        if titulo == "Potencial de Éxito":
                            porcentaje_val = parse_number(contenido)
                            if porcentaje_val is not None:
                                fig, ax = plt.subplots(figsize=(2, 2))
                                ax.pie([porcentaje_val, 100 - porcentaje_val], colors=['#4CAF50', '#CCCCCC'], startangle=90, counterclock=False)
                                ax.axis('equal')
                                st.pyplot(fig)
                                st.write(f"**Potencial de Éxito: {porcentaje_val}%**")
                                doc.add_paragraph(f"**Potencial de Éxito: {porcentaje_val}%**")
                        elif titulo == "Estimación de Visitantes Diarios":
                            est_visitors_val = parse_number(contenido)
                            if est_visitors_val is not None:
                                est_visitors_val = int(est_visitors_val)
                                st.subheader("👥 Estimación de Visitantes Diarios")
                                st.metric(label="Máximo de Visitantes al Día", value=f"{est_visitors_val:,}")
                                doc.add_paragraph(f"**Máximo de Visitantes al Día: {est_visitors_val:,}**")
                                fig, ax = plt.subplots(figsize=(4, 1))
                                ax.barh([''], [est_visitors_val], color='#4CAF50')
                                ax.set_xlim(0, est_visitors_val * 1.2)
                                ax.set_xlabel('Número de Visitantes')
                                ax.set_yticks([])
                                st.pyplot(fig)

                    # Crear un buffer para el archivo DOCX
                    buffer = BytesIO()
                    doc.save(buffer)
                    buffer.seek(0)

                    st.success("✅ Análisis completado:")
                    st.write(result)

                    st.download_button(
                        label="📥 Descargar Análisis en DOCX",
                        data=buffer,
                        file_name="analisis_plataforma.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                else:
                    st.error("❌ Respuesta inesperada de Together API.")
            except requests.exceptions.HTTPError as http_err:
                st.error(f"❌ Error HTTP al acceder a Together API: {http_err}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Error al acceder a Together API: {e}")

import streamlit as st
import requests
import json
from urllib.parse import urlparse
from io import BytesIO
from docx import Document
from docx.shared import Inches
import matplotlib.pyplot as plt
import re

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
            url_input = "http://" + url_input  # Añadir esquema si falta

        try:
            response = requests.get(url_input, timeout=10)
            if response.status_code != 200:
                st.error(f"⚠️ No se pudo acceder a la URL proporcionada. Código de estado: {response.status_code}")
                st.stop()
        except requests.exceptions.RequestException as e:
            st.error(f"⚠️ Error al acceder a la URL: {e}")
            st.stop()

        st.info("🔄 Procesando la URL...")

        # Extraer el dominio para la búsqueda
        domain = parsed_url.netloc
        if not domain:
            st.error("⚠️ URL inválida. Por favor, intenta nuevamente.")
            st.stop()
        else:
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
                response_serper = requests.post(serper_url, headers=headers_serper, json=data_serper)
                if response_serper.status_code == 200:
                    search_results = response_serper.json()
                    # Procesar los resultados
                    snippets = []
                    if "organic" in search_results:
                        for item in search_results["organic"]:
                            if "snippet" in item:
                                snippets.append(item["snippet"])
                    search_summary = "\n\n".join(snippets) if snippets else "No se encontraron resultados relevantes."
                else:
                    st.error(f"❌ Error al acceder a Serper API: {response_serper.status_code}")
                    st.stop()

            # Preparar el mensaje para Together API con enfoque en demandas del mercado, recomendaciones y estimación de visitantes
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
                "stream": False  # Mantener en False para simplificar el manejo
            }

            # Realizar solicitud a Together API
            with st.spinner("🧠 Analizando con Together..."):
                response_together = requests.post(together_url, headers=headers_together, json=data_together)
                if response_together.status_code == 200:
                    analysis = response_together.json()
                    # Asumiendo que la respuesta contiene 'choices' con 'message'
                    if "choices" in analysis and len(analysis["choices"]) > 0:
                        result = analysis["choices"][0]["message"]["content"]

                        # Separar el análisis en secciones utilizando títulos en negrita
                        secciones = {}
                        current_section = None
                        for line in result.split('\n'):
                            line = line.strip()
                            # Detectar títulos en formato **Título**:
                            match = re.match(r'\*\*(.*?)\*\*:', line)
                            if match:
                                section_title = match.group(1).strip()
                                secciones[section_title] = ""
                                current_section = section_title
                            elif current_section:
                                secciones[current_section] += line + "\n"

                        # Crear un documento DOCX
                        doc = Document()
                        doc.add_heading('Análisis de Potencial de Éxito', 0)

                        # Agregar Resumen Ejecutivo
                        if "Resumen Ejecutivo" in secciones:
                            doc.add_heading('📄 Resumen Ejecutivo', level=1)
                            doc.add_paragraph(secciones["Resumen Ejecutivo"])
                            del secciones["Resumen Ejecutivo"]

                        # Agregar Potencial de Éxito
                        if "Potencial de Éxito" in secciones:
                            doc.add_heading('📊 Potencial de Éxito', level=1)
                            pot_success_text = secciones["Potencial de Éxito"]
                            # Extraer el porcentaje del texto
                            porcentaje = re.search(r'(\d+)%', pot_success_text)
                            if porcentaje:
                                porcentaje_val = int(porcentaje.group(1))
                                # Visualización con matplotlib
                                fig, ax = plt.subplots(figsize=(2, 2))
                                ax.pie([porcentaje_val, 100 - porcentaje_val], colors=['#4CAF50', '#CCCCCC'], startangle=90, counterclock=False)
                                ax.axis('equal')  # Equal aspect ratio
                                st.pyplot(fig)
                                st.write(f"**Potencial de Éxito: {porcentaje_val}%**")
                                # Agregar al DOCX
                                doc.add_paragraph(f"**Potencial de Éxito: {porcentaje_val}%**")
                            else:
                                st.write(secciones["Potencial de Éxito"])
                                doc.add_paragraph(secciones["Potencial de Éxito"])
                            del secciones["Potencial de Éxito"]

                        # Agregar Estimación de Visitantes Diarios
                        if "Estimación de Visitantes Diarios" in secciones:
                            est_visitors_text = secciones["Estimación de Visitantes Diarios"]
                            est_visitors_match = re.search(r'(\d[\d,\.]*)\s*visitantes al día', es

import streamlit as st
import requests
import json
from urllib.parse import urlparse

# Título de la aplicación
st.title("Análisis de Potencial de Éxito de Plataformas Digitales")

# Entrada de la URL
url_input = st.text_input("Ingrese la URL de la plataforma digital que desea analizar:", "")

# Botón para iniciar el análisis
if st.button("Analizar"):
    if not url_input:
        st.error("Por favor, ingrese una URL válida.")
    else:
        # Validar la URL
        parsed_url = urlparse(url_input)
        if not parsed_url.scheme:
            url_input = "http://" + url_input  # Añadir esquema si falta

        st.info("Procesando la URL...")

        # Extraer el dominio para la búsqueda
        domain = parsed_url.netloc
        if not domain:
            st.error("URL inválida. Por favor, intente nuevamente.")
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

            with st.spinner("Realizando búsqueda con Serper..."):
                response_serper = requests.post(serper_url, headers=headers_serper, json=data_serper)
                if response_serper.status_code == 200:
                    search_results = response_serper.json()
                    # Puedes procesar los resultados según tus necesidades
                    # Por ejemplo, extraer snippets o descripciones
                    snippets = []
                    if "organic" in search_results:
                        for item in search_results["organic"]:
                            if "snippet" in item:
                                snippets.append(item["snippet"])
                    search_summary = "\n".join(snippets) if snippets else "No se encontraron resultados relevantes."
                else:
                    st.error(f"Error al acceder a Serper API: {response_serper.status_code}")
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
                    "content": "Eres un experto en análisis de plataformas digitales. Analiza el siguiente contenido y proporciona una evaluación del potencial de éxito."
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
                "stream": False  # Cambiado a False para simplificar el manejo
            }

            # Realizar solicitud a Together API
            with st.spinner("Analizando con Together..."):
                response_together = requests.post(together_url, headers=headers_together, json=data_together, stream=False)
                if response_together.status_code == 200:
                    analysis = response_together.json()
                    # Asumiendo que la respuesta contiene 'choices' con 'message'
                    if "choices" in analysis and len(analysis["choices"]) > 0:
                        result = analysis["choices"][0]["message"]["content"]
                        st.success("Análisis completado:")
                        st.write(result)
                    else:
                        st.error("Respuesta inesperada de Together API.")
                else:
                    st.error(f"Error al acceder a Together API: {response_together.status_code}")


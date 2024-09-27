import streamlit as st
import requests
from urllib.parse import urlparse
import re

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
                                    """)
            except Exception as e:
                st.error(f"❌ Se produjo un error inesperado: {str(e)}")

if __name__ == "__main__":
    main()

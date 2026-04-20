import streamlit as st
from langchain_community.chat_message_histories import ChatMessageHistory

from config import POWERBI_URL, POWERBI_HEIGHT, HISTORIAL_MENSAJES
from agent import invocar_agente
from components import CHAT_CSS, build_chat_html, render_chat_widget
from utils import manejar_error, construir_contexto, enriquecer_pregunta

# ---------------------------------------------------------------------------
# Configuración de página
# ---------------------------------------------------------------------------
st.set_page_config(layout="wide", page_title="Chatbot Finanzas")
st.markdown(CHAT_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Estado de sesión
# ---------------------------------------------------------------------------
if "scroll_counter" not in st.session_state:
    st.session_state.scroll_counter = 0

if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": """¡Hola! Soy tu asistente financiero de Lucro. Tengo acceso a una base de datos de facturación con la siguiente información para analizar:

        * **Factura:** Número de factura
        * **Fecha:** Fecha de emisión (en formato YYYY-MM-DD)
        * **Concepto:** Descripción del servicio o producto facturado
        * **Cliente:** Nombre del cliente
        * **Valor:** Valor en pesos colombianos (COP)

        ¿Qué te gustaría analizar hoy?"""}
            ]

if "chat_history" not in st.session_state:
    st.session_state.chat_history = ChatMessageHistory()

# ---------------------------------------------------------------------------
# Layout: tablero izquierda | chatbot derecha
# ---------------------------------------------------------------------------
col_pbi, col_chat = st.columns([2, 1])
 
with col_pbi:
    st.components.v1.iframe(
        src=POWERBI_URL,
        width=None,
        height=POWERBI_HEIGHT,
        scrolling=True,
    )
 
with col_chat:
    st.subheader("🤖 Asistente")
 
    st.session_state.scroll_counter += 1
    chat_html = build_chat_html(st.session_state.messages)
    widget_html = render_chat_widget(chat_html, st.session_state.scroll_counter)
 
    st.components.v1.html(widget_html, height=750, scrolling=False)
 
    pregunta = st.chat_input("Pregunta algo...")
    if pregunta:
        st.session_state.messages.append({"role": "user", "content": pregunta})
 
        contexto = construir_contexto(
            st.session_state.chat_history.messages,
            HISTORIAL_MENSAJES,
        )
        pregunta_enriquecida = enriquecer_pregunta(pregunta, contexto)
        print(f">>> PREGUNTA ENRIQUECIDA: {pregunta_enriquecida[:300]}")
        with st.spinner("⏳ Analizando..."):
            exito = False
            try:
                respuesta = invocar_agente(pregunta_enriquecida)
 
                # Normalizar a string si viene como lista
                if isinstance(respuesta, list):
                    respuesta = " ".join(
                        item.get("text", "") if isinstance(item, dict) else str(item)
                        for item in respuesta
                    )
 
                if not respuesta or not respuesta.strip():
                    respuesta = "No pude procesar la pregunta. ¿Puedes reformularla?"
 
                exito = True
 
            except Exception as e:
                respuesta = str(e)  # ← temporal
 
        # Solo guardar en historial si la respuesta fue exitosa
        if exito:
            st.session_state.chat_history.add_user_message(pregunta)
            st.session_state.chat_history.add_ai_message(respuesta)
 
        st.session_state.messages.append({"role": "assistant", "content": respuesta})
        st.rerun()
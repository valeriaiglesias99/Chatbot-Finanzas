import streamlit as st
from dotenv import load_dotenv

load_dotenv() 

# ← Agrega estas dos líneas
import langchain
langchain.debug = False

from langchain_google_genai import ChatGoogleGenerativeAI
from data import data_limpia
from prompts import SYSTEM_PROMPT
from langchain_experimental.agents import create_pandas_dataframe_agent
import os
from langchain_community.agent_toolkits.load_tools import load_tools

if "cache_cleared" not in st.session_state:
    st.cache_resource.clear()
    st.session_state.cache_cleared = True

# *Configuración inicial de la página, ocupando todo el ancho y título de la pestaña
st.set_page_config(layout="wide", page_title="Chatbot Finanzas")

# *
st.markdown("""
<style>

    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    #* Elimina scroll de la página completa
    html, body, [data-testid="stAppViewContainer"] {
        overflow: hidden !important;
        height: 100vh !important;
    }
            
    # *Agrega línea divisoria entre tablero y chatbot
    [data-testid="column"]:last-child {
        border-left: 1px solid #e0e0e0;
        padding-left: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# *Incializar estado
if "scroll_counter" not in st.session_state:
    st.session_state.scroll_counter = 0

# *¿Ya existe "messages" en la memoria?
if "messages" not in st.session_state:

    # *No existe → créalo con el mensaje de bienvenida
    st.session_state.messages = [
        {"role": "assistant", "content": "Hola! ¿En qué te puedo ayudar hoy?"}
    ]

# !Cargar datos y agente una sola vez
@st.cache_resource
def cargar_agente():
    df = data_limpia()  # ← carga el df aquí adentro
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0
    )
    agent = create_pandas_dataframe_agent(
        llm,
        df,
        verbose=True,
        prefix=SYSTEM_PROMPT,
        allow_dangerous_code=True,
        handle_parsing_errors=True,
        agent_type="openai-tools"
    )
    return agent

# *Chat con diseño personalizado
def build_chat_html(messages):
    html = ""
    for msg in messages:
        if msg["role"] == "assistant":
            html += f"""
                <div style="display:flex;gap:10px;margin-bottom:16px;">
                    <div style="width:32px;height:32px;border-radius:50%;background:#1B5E20;
                        display:flex;align-items:center;justify-content:center;
                        color:white;font-size:13px;flex-shrink:0;">A</div>
                    <div style="background:#f0f2f6;padding:10px 14px;
                        border-radius:0 18px 18px 18px;font-size:14px;
                        max-width:85%;line-height:1.5;">{msg["content"]}</div>
                </div>
            """
        else:
            html += f"""
                <div style="display:flex;gap:10px;margin-bottom:16px;flex-direction:row-reverse;">
                    <div style="width:32px;height:32px;border-radius:50%;
                        background:#e8f0fe;display:flex;align-items:center;
                        justify-content:center;color:#0C447C;
                        font-size:13px;flex-shrink:0;">U</div>
                    <div style="background:#ffffff;padding:10px 14px;
                        border-radius:18px 0 18px 18px;font-size:14px;
                        border:1px solid #e0e0e0;max-width:85%;
                        line-height:1.5;">{msg["content"]}</div>
                </div>
            """
    return html

# *URL de Power BI
POWERBI_URL = "https://app.powerbi.com/view?r=eyJrIjoiMjM0MDdiYTItYjI5Mi00YzBlLTkyMjAtNzJlYzI5MTdkNTJkIiwidCI6ImZjYWM0NWU1LTY1NjUtNGYxMi1iNTNhLWFjZTUwOGVmMTVjMSJ9"

col_pbi, col_chat = st.columns([2, 1])

# *Tablero izquierda
with col_pbi:
    st.components.v1.iframe(
        src=POWERBI_URL,
        width=None,
        height=880,
        scrolling=True
    )

# *Chatbot derecha
with col_chat:
    st.subheader("🤖 Asistente")

    # *HTML  de los mensajes
    chat_html = build_chat_html(st.session_state.messages)
    st.session_state.scroll_counter += 1


    st.components.v1.html(f"""
        <style>
            .tutor-chat-box {{
                height: 700px;
                overflow-y: auto;
                padding: 16px;
                font-family: sans-serif;
            }}
        </style>
        <div class="tutor-chat-box">
            {chat_html}
        </div>
        <script>
            var dummy = {st.session_state.scroll_counter};
            var box = document.querySelector('.tutor-chat-box');
            if(box) box.scrollTop = box.scrollHeight;
        </script>
    """, height=750, scrolling=False)

    # Input
    pregunta = st.chat_input("Pregunta algo...")
    if pregunta:
        st.session_state.messages.append({"role": "user", "content": pregunta})

        with st.spinner("Analizando..."):
            try:
                agent = cargar_agente()  # ← simple, sin parámetros
                respuesta = agent.run(pregunta)
            except Exception as e:
                respuesta = f"Ocurrió un error: {str(e)}"

        st.session_state.messages.append({"role": "assistant", "content": respuesta})
        st.rerun()
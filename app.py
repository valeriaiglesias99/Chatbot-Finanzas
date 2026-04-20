import re
import os
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_community.chat_message_histories import ChatMessageHistory
from data import data_limpia
from prompts import SYSTEM_PROMPT


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


# Inicializar memoria de LangChain en session_state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = ChatMessageHistory()
    

# !Cargar datos y agente una sola vez

@st.cache_resource
def cargar_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0,
        max_output_tokens=8192
    )

@st.cache_data
def cargar_data():
    return data_limpia()

def manejar_error(error) -> str:
    texto = str(error)
    if "Could not parse LLM output:" in texto:
        # Extrae solo el texto útil
        respuesta = texto.split("Could not parse LLM output:")[1]
        # Quita todo lo que venga después del backtick final
        if "For troubleshooting" in respuesta:
            respuesta = respuesta.split("For troubleshooting")[0]
        # Limpia backticks y espacios
        respuesta = respuesta.strip().strip("`").strip()
        return respuesta
    return "No pude procesar la respuesta. Intenta reformular la pregunta."
def crear_agente():
    from datetime import datetime
    df = cargar_data()
    llm = cargar_llm()
    hoy = datetime.now().strftime("%d/%m/%Y")
    año = datetime.now().year
    prompt_con_fecha = f"""
    Hoy es {hoy}. Año actual: {año}.
    Cuando digan "este año" usa {año}.

    INSTRUCCIONES DE FORMATO — MUY IMPORTANTE:
    Siempre debes responder usando este formato exacto:

    Thought: [tu razonamiento]
    Action: python_repl_ast
    Action Input: [el código python]

    O si no necesitas ejecutar código:

    Thought: [tu razonamiento]
    Final Answer: [tu respuesta]

    NUNCA respondas directamente sin usar Thought/Action o Thought/Final Answer.

    {SYSTEM_PROMPT}
    """
    return create_pandas_dataframe_agent(
        llm,
        df,
        verbose=True,
        prefix=prompt_con_fecha,
        allow_dangerous_code=True,
        max_iterations=5,
        max_execution_time=60
    )

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
                    <div class="msg-content" style="background:#f0f2f6;padding:10px 14px;
                        border-radius:0 18px 18px 18px;font-size:14px;
                        max-width:85%;line-height:1.5;">
                        <span class="markdown-content">{msg["content"]}</span>
                    </div>
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
# *Chatbot derecha
with col_chat:
    st.subheader("🤖 Asistente")

    chat_html = build_chat_html(st.session_state.messages)
    st.session_state.scroll_counter += 1

    st.components.v1.html(f"""
        <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/9.1.6/marked.min.js"></script>
        <style>
            .tutor-chat-box {{
                height: 700px;
                overflow-y: auto;
                padding: 16px;
                font-family: sans-serif;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 8px 0;
                font-size: 13px;
            }}
            th {{
                background-color: #1B5E20;
                color: white;
                padding: 8px 12px;
                text-align: left;
            }}
            td {{
                padding: 6px 12px;
                border-bottom: 1px solid #e0e0e0;
            }}
            tr:nth-child(even) {{
                background-color: #f5f5f5;
            }}
            tr:hover {{
                background-color: #e8f5e9;
            }}
        </style>
        <div class="tutor-chat-box">
            {chat_html}
        </div>
        <script>
            var dummy = {st.session_state.scroll_counter};
            document.querySelectorAll('.markdown-content').forEach(function(el) {{
                el.innerHTML = marked.parse(el.textContent);
            }});
            var box = document.querySelector('.tutor-chat-box');
            if(box) box.scrollTop = box.scrollHeight;
        </script>
    """, height=750, scrolling=False)

    pregunta = st.chat_input("Pregunta algo...")
    if pregunta:
        st.session_state.messages.append({"role": "user", "content": pregunta})

        # ← Construye contexto ANTES del try
        contexto = ""
        for msg in st.session_state.chat_history.messages[-4:]:
            if msg.type == "human":
                contexto += f"Usuario: {msg.content}\n\n"
            else:
                sin_tabla = re.sub(r'\|.+\|', '', msg.content)
                sin_tabla = re.sub(r'\n{2,}', '\n', sin_tabla).strip()
                contexto += f"Asistente: {sin_tabla}\n\n"

        pregunta_con_memoria = f"""
    Historial reciente:
    {contexto}
    IMPORTANTE: Si es seguimiento ejecuta lo prometido antes.
    Pregunta actual: {pregunta}
    """

        with st.spinner("⏳ Analizando..."):
            respuesta = ""
            try:
                agent = crear_agente()
                resultado = agent.invoke({"input": pregunta_con_memoria})
                output = resultado["output"]

                if isinstance(output, list):
                    respuesta = "".join([
                        item.get("text", "") if isinstance(item, dict) else str(item)
                        for item in output
                    ])
                else:
                    respuesta = str(output)

            except Exception as e:
                error_texto = str(e)
                if "Could not parse LLM output:" in error_texto:
                    respuesta = error_texto.split("Could not parse LLM output:")[1]
                    if "For troubleshooting" in respuesta:
                        respuesta = respuesta.split("For troubleshooting")[0]
                    respuesta = respuesta.strip().strip("`").strip()
                else:
                    respuesta = f"Ocurrió un error: {error_texto}"

            if not respuesta.strip():
                respuesta = "No pude procesar la pregunta. ¿Puedes reformularla?"

        st.session_state.chat_history.add_user_message(pregunta)
        st.session_state.chat_history.add_ai_message(respuesta)
        st.session_state.messages.append({"role": "assistant", "content": respuesta})
        st.rerun()
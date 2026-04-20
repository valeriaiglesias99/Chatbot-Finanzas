import streamlit as st
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.agents import create_pandas_dataframe_agent


from config import (
    GOOGLE_API_KEY,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    AGENT_MAX_ITERATIONS,
    AGENT_MAX_EXECUTION_TIME,
)
from data import data_limpia
from prompts import SYSTEM_PROMPT
 
 
@st.cache_resource
def cargar_llm():
    return ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=LLM_TEMPERATURE,
        max_output_tokens=LLM_MAX_TOKENS,
    )
 
 
@st.cache_data
def cargar_data():
    return data_limpia()
 
@st.cache_resource(ttl=1)
def cargar_agente():
    """Crea y cachea el agente para no recrearlo en cada mensaje."""
    hoy = datetime.now().strftime("%d/%m/%Y")
    año = datetime.now().year
    fecha_header = f"""
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
    """

    prompt_con_fecha = fecha_header + SYSTEM_PROMPT
    agente = create_pandas_dataframe_agent(
        cargar_llm(),
        cargar_data(),
        verbose=True,
        prefix=prompt_con_fecha,
        allow_dangerous_code=True,
        max_iterations=AGENT_MAX_ITERATIONS,
        max_execution_time=AGENT_MAX_EXECUTION_TIME,
    )
    
    # Envolver en AgentExecutor con handle_parsing_errors
    agente.handle_parsing_errors = True
    return agente
 

import time

def invocar_agente(pregunta_con_contexto: str, max_reintentos: int = 3) -> str:
    agente = cargar_agente()
    
    for intento in range(max_reintentos):
        try:
            resultado = agente.invoke({"input": pregunta_con_contexto})
            output = resultado["output"]
            if isinstance(output, list):
                return "".join(
                    item.get("text", "") if isinstance(item, dict) else str(item)
                    for item in output
                )
            return str(output)
            
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                if intento < max_reintentos - 1:
                    time.sleep(5)  # espera 5 segundos y reintenta
                    continue
            raise e  # si no es 503, lanza el error normal
    
    return "El servicio está experimentando alta demanda. Intenta en unos segundos."
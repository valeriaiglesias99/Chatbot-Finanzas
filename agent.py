import io
import streamlit as st
import contextlib
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage

from config import (
    GOOGLE_API_KEY,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
)
from data import data_limpia
from prompts import SYSTEM_PROMPT


@st.cache_data
def cargar_data():
    return data_limpia()


@st.cache_resource
def cargar_llm():
    return ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=LLM_TEMPERATURE,
        max_output_tokens=LLM_MAX_TOKENS,
    )


def _ejecutar_codigo(codigo: str) -> str:
    """Ejecuta código Python sobre el df y retorna el output impreso."""
    df = cargar_data()
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            exec(codigo, {"df": df})  # noqa: S102
        resultado = buffer.getvalue()
        return resultado if resultado.strip() else "Código ejecutado sin output."
    except Exception as e:
        return f"Error al ejecutar el código: {e}"

def _content_a_str(content) -> str:
    """Convierte el content de Gemini a string sin importar el formato."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in content
        )
    return str(content)

# Definición de la herramienta para bind_tools
TOOLS = [
    {
        "name": "ejecutar_python",
        "description": (
            "Ejecuta código Python sobre el DataFrame de facturación llamado `df`. "
            "Usa print() para mostrar los resultados. "
            "Úsala cuando necesites calcular, filtrar o analizar datos del df."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "codigo": {
                    "type": "string",
                    "description": (
                        "Código Python válido. El DataFrame se llama `df`. "
                        "Usa print() para mostrar resultados."
                    ),
                }
            },
            "required": ["codigo"],
        },
    }
]


def invocar_agente(pregunta_con_contexto: str) -> str:
    """
    Invoca el modelo con tool calling.
    - Si la pregunta requiere datos: ejecuta código y redacta respuesta con el resultado.
    - Si es saludo o pregunta simple: responde directo sin ejecutar código.
    """
    hoy = datetime.now().strftime("%d/%m/%Y")
    año = datetime.now().year

    llm = cargar_llm()
    llm_con_tools = llm.bind_tools(TOOLS)

    system_prompt = f"Hoy es {hoy}. Año actual: {año}.\nCuando digan 'este año' usa {año}.\n\n{SYSTEM_PROMPT}"

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=pregunta_con_contexto),
    ]

    # Primera llamada — modelo decide si usar herramienta o responder directo
    respuesta = llm_con_tools.invoke(messages)

    # Si no necesita código (saludo, pregunta simple, fuera de contexto)
    if not respuesta.tool_calls:
        return _content_a_str(respuesta.content)

    # Ejecutar el código solicitado por el modelo
    tool_call = respuesta.tool_calls[0]
    codigo = tool_call["args"]["codigo"]
    resultado = _ejecutar_codigo(codigo)

    # Segunda llamada — modelo redacta la respuesta final con el resultado real
    messages.append(respuesta)
    messages.append(
        ToolMessage(
            content=resultado,
            tool_call_id=tool_call["id"],
        )
    )

    respuesta_final = llm.invoke(messages)
    return _content_a_str(respuesta_final.content)
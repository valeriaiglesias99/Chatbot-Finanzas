import io
import re
import streamlit as st
import contextlib
from datetime import datetime

import google.generativeai as genai

from config import GOOGLE_API_KEY, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS
from data import data_limpia
from prompts import SYSTEM_PROMPT


#Cargar el df y cachearlo
@st.cache_data
def cargar_data():
    return data_limpia()


def _ejecutar_codigo(codigo: str) -> str:
    """Ejecuta código Python sobre el df y retorna el output."""
    df = cargar_data()
    # buffer de texto en memoria para capturar el output de print()
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            exec(codigo, {"df": df})  # noqa: S102
        resultado = buffer.getvalue()
        return resultado if resultado.strip() else "Código ejecutado sin output."
    except Exception as e:
        return f"Error: {e}"


def _extraer_texto(respuesta) -> str:
    """Extrae texto plano de una respuesta de Gemini."""
    texto = ""
    for part in respuesta.parts:
        if hasattr(part, "text") and part.text:
            texto += part.text
    return texto.strip()


def _extraer_function_call(respuesta):
    """Extrae el function_call de una respuesta de Gemini si existe."""
    for part in respuesta.parts:
        if hasattr(part, "function_call") and part.function_call.name:
            return part.function_call
    return None


TOOL_EJECUTAR_PYTHON = genai.protos.Tool(
    function_declarations=[
        genai.protos.FunctionDeclaration(
            name="ejecutar_python",
            description=(
                "Ejecuta código Python sobre el DataFrame de facturación llamado df. "
                "Usa print() para mostrar resultados. "
                "SIEMPRE usa esta herramienta para calcular datos."
            ),
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={
                    "codigo": genai.protos.Schema(
                        type=genai.protos.Type.STRING,
                        description="Código Python. El DataFrame se llama df. Usa print() para mostrar resultados.",
                    )
                },
                required=["codigo"],
            ),
        )
    ]
)


@st.cache_resource
def cargar_modelo():
    genai.configure(api_key=GOOGLE_API_KEY)
    return genai.GenerativeModel(
        model_name=LLM_MODEL,
        tools=[TOOL_EJECUTAR_PYTHON],
        tool_config={"function_calling_config": {"mode": "AUTO"}},  # ← agregar esto
        generation_config=genai.GenerationConfig(
            temperature=LLM_TEMPERATURE,
            max_output_tokens=LLM_MAX_TOKENS,
        ),
        system_instruction=(
            "CRÍTICO: NUNCA respondas con bloques ```python``` ni escribas código como texto. "
            "SIEMPRE usa la herramienta ejecutar_python para ejecutar código. "
            "Escribir código como texto no ejecuta nada y no sirve."
        ),
    )


def invocar_agente(pregunta_con_contexto: str) -> str:
    hoy = datetime.now().strftime("%d/%m/%Y")
    año = datetime.now().year
    prompt_completo = f"Hoy es {hoy}. Año actual: {año}.\nCuando digan 'este año' usa {año}.\n\n{SYSTEM_PROMPT}\n\nPregunta: {pregunta_con_contexto}"

    modelo = cargar_modelo()
    chat = modelo.start_chat(history=[])
    respuesta = chat.send_message(prompt_completo)

    for _ in range(5):
        try:
            function_call = _extraer_function_call(respuesta)
        except Exception:
            # MALFORMED_FUNCTION_CALL — reintentar
            respuesta = chat.send_message(
                "Hubo un error en el formato. Por favor intenta de nuevo usando ejecutar_python."
            )
            continue

        if function_call is None:
            texto = _extraer_texto(respuesta)
            print(f">>> RESPUESTA DIRECTA: {texto[:300]}")

            # Detectar código escrito como texto en lugar de usar la herramienta
            match = re.search(r'```python\n(.*?)```', texto, re.DOTALL)
            if not match:
                match = re.search(r'ejecutar_python\s*(.*?)(?:\n\n|$)', texto, re.DOTALL)

            if match:
                codigo = match.group(1).strip()
                print(f">>> CÓDIGO EN TEXTO DETECTADO, ejecutando...")
                resultado = _ejecutar_codigo(codigo)
                respuesta = chat.send_message(
                    f"Resultado del código:\n{resultado}\n\nRedacta la respuesta final en español con estos datos."
                )
                continue

            # Respuesta vacía — forzar reintento
            if not texto:
                respuesta = chat.send_message(
                    "Por favor usa la herramienta ejecutar_python para responder la pregunta."
                )
                continue

            return texto

        # Ejecutar la herramienta
        codigo = function_call.args.get("codigo", "")
        resultado = _ejecutar_codigo(codigo)
        print(f">>> TOOL CALL:\n{codigo}")
        print(f">>> RESULTADO: {resultado[:200]}")

        respuesta = chat.send_message(
            genai.protos.Content(
                parts=[
                    genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name="ejecutar_python",
                            response={"result": resultado},
                        )
                    )
                ]
            )
        )

    texto_final = _extraer_texto(respuesta)
    print(f">>> RESPUESTA FINAL: {texto_final[:300]}")
    return texto_final if texto_final else "No pude procesar la pregunta. ¿Puedes reformularla?"
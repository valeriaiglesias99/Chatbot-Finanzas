import re
 
 
def manejar_error(error: Exception) -> str:
    texto = str(error)
    if "503" in texto or "UNAVAILABLE" in texto:
        return "El servicio está temporalmente saturado. Por favor intenta de nuevo en unos segundos."
    if "Could not parse LLM output:" in texto:
        respuesta = texto.split("Could not parse LLM output:")[1]
        if "For troubleshooting" in respuesta:
            respuesta = respuesta.split("For troubleshooting")[0]
        return respuesta.strip().strip("`").strip()
    return "No pude procesar la respuesta. Intenta reformular la pregunta."
 
 
def limpiar_mensaje_para_historial(contenido: str) -> str:
    """Elimina tablas markdown de un mensaje para aligerar el contexto."""
    sin_tabla = re.sub(r'\|.+\|', '', contenido)
    return re.sub(r'\n{2,}', '\n', sin_tabla).strip()
 
 
def construir_contexto(historial_mensajes: list, n: int) -> str:
    """
    Construye un string de contexto a partir de los últimos n mensajes
    del historial de LangChain.
    """
    contexto = ""
    for msg in historial_mensajes[-n:]:
        if msg.type == "human":
            contexto += f"Usuario: {msg.content}\n\n"
        else:
            sin_tabla = limpiar_mensaje_para_historial(msg.content)
            contexto += f"Asistente: {sin_tabla}\n\n"
    return contexto
 
 
def enriquecer_pregunta(pregunta: str, contexto: str) -> str:
    """Combina la pregunta actual con el historial de contexto."""
    return f"""Historial reciente:
{contexto}
IMPORTANTE: Si es seguimiento ejecuta lo prometido antes.
Pregunta actual: {pregunta}
"""
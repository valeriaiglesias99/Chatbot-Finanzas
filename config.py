import os
from dotenv import load_dotenv
 
load_dotenv()
 
# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
 
# LLM
LLM_MODEL = "gemini-2.5-flash"
LLM_TEMPERATURE = 0
LLM_MAX_TOKENS = 16384
 
# Agente
AGENT_MAX_ITERATIONS = 15
AGENT_MAX_EXECUTION_TIME = 60
HISTORIAL_MENSAJES = 4  # cuántos mensajes recientes incluir como contexto
 
# Power BI
POWERBI_URL = (
    "https://app.powerbi.com/view?r=eyJrIjoiMjM0MDdiYTItYjI5Mi00YzBlLTkyMjAtNzJlYzI"
    "5MTdkNTJkIiwidCI6ImZjYWM0NWU1LTY1NjUtNGYxMi1iNTNhLWFjZTUwOGVmMTVjMSJ9"
)
POWERBI_HEIGHT = 880
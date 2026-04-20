CHAT_CSS = """
<style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    html, body, [data-testid="stAppViewContainer"] {
        overflow: hidden !important;
        height: 100vh !important;
    }
    [data-testid="column"]:last-child {
        border-left: 1px solid #e0e0e0;
        padding-left: 1rem;
    }
</style>
"""
 
 
def _burbuja_asistente(contenido: str) -> str:
    return f"""
        <div style="display:flex;gap:10px;margin-bottom:16px;">
            <div style="width:32px;height:32px;border-radius:50%;background:#1B5E20;
                display:flex;align-items:center;justify-content:center;
                color:white;font-size:13px;flex-shrink:0;">A</div>
            <div class="msg-content" style="background:#f0f2f6;padding:10px 14px;
                border-radius:0 18px 18px 18px;font-size:14px;
                max-width:85%;line-height:1.5;">
                <span class="markdown-content">{contenido}</span>
            </div>
        </div>
    """
 
 
def _burbuja_usuario(contenido: str) -> str:
    return f"""
        <div style="display:flex;gap:10px;margin-bottom:16px;flex-direction:row-reverse;">
            <div style="width:32px;height:32px;border-radius:50%;
                background:#e8f0fe;display:flex;align-items:center;
                justify-content:center;color:#0C447C;
                font-size:13px;flex-shrink:0;">U</div>
            <div style="background:#ffffff;padding:10px 14px;
                border-radius:18px 0 18px 18px;font-size:14px;
                border:1px solid #e0e0e0;max-width:85%;
                line-height:1.5;">{contenido}</div>
        </div>
    """
 
 
def build_chat_html(messages: list) -> str:
    """Construye el HTML completo del historial de mensajes."""
    html = ""
    for msg in messages:
        if msg["role"] == "assistant":
            html += _burbuja_asistente(msg["content"])
        else:
            html += _burbuja_usuario(msg["content"])
    return html
 
 
def render_chat_widget(chat_html: str, scroll_counter: int) -> str:
    """Devuelve el HTML completo del widget de chat (scroll + markdown)."""
    return f"""
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
            var dummy = {scroll_counter};
            document.querySelectorAll('.markdown-content').forEach(function(el) {{
                el.innerHTML = marked.parse(el.textContent);
            }});
            var box = document.querySelector('.tutor-chat-box');
            if(box) box.scrollTop = box.scrollHeight;
        </script>
    """
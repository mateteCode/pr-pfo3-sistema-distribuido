import sys

# Definicion de colores ANSI globales
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def clear_screen():
    """Limpia la terminal completamente al iniciar."""
    sys.stdout.write("\033[2J")
    sys.stdout.flush()

def get_status_color(status):
    """
    Analiza el texto del estado y devuelve un color apropiado.
    Esto centraliza la logica de colores para todos los modulos.
    """
    status_lower = status.lower()
    
    if "error" in status_lower or "desconect" in status_lower:
        return RED
    elif "todas las tareas completadas" in status_lower:
        return CYAN
    elif "disponible" in status_lower or "recibido" in status_lower or "registrado" in status_lower or status == "conectado":
        return GREEN
    else:
        # Por defecto, estado intermedio (procesando, enviando, conectando...)
        return YELLOW

def generate_panel(title, sections):
    """
    Genera el texto formateado del panel.
    `sections` debe ser una lista de tuplas: (Titulo de Seccion, Prefijo, Diccionario de datos)
    """
    output = "\033[H" # Mueve el cursor arriba a la izquierda
    output += f"{CYAN}{BOLD}=== {title} ==={RESET}\033[K\n\033[K\n"
    
    for section_title, item_prefix, data_dict in sections:
        if section_title:
            output += f"{BOLD}--- {section_title} ---{RESET}\033[K\n"
            
        for key in sorted(data_dict.keys()):
            status = data_dict[key]
            color = get_status_color(status)
            output += f"{item_prefix} {key}: {color}{status}{RESET}\033[K\n"
            
        output += "\033[K\n" # Espacio entre secciones
        
    output += "\033[K\n\033[K\n"
    return output
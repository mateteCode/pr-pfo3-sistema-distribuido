import random
import socket
import threading
import json
import time
import sys
from utils import dashboard

HOST = '127.0.0.1'
PORT = 8000
NUM_CLIENTS = 4
TASKS_PER_CLIENT = 5

state_lock = threading.Lock()
clients_ui_state = {}

def update_dashboard():
    dashboard.clear_screen()
    
    while True:
        with state_lock:
            sections = [
                ("", "Cliente", clients_ui_state)
            ]
            
            output = dashboard.generate_panel("DASHBOARD DE CLIENTES", sections)
            sys.stdout.write(output)
            sys.stdout.flush()
        time.sleep(0.1)

# Simula una aplicacion cliente generando tareas
def run_client(client_index):
    with state_lock:
        clients_ui_state[client_index] = "Conectando..."

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((HOST, PORT))
        with state_lock:
            clients_ui_state[client_index] = "Conectado"
            
        reader = client_socket.makefile('r', encoding='utf-8')
        
        for task_num in range(1, TASKS_PER_CLIENT + 1):
            task_id = f"C{client_index}-T{task_num}"
            task = {
                "task_id": task_id,
                "data": f"Data to process {task_num}"
            }
            
            with state_lock:
                clients_ui_state[client_index] = f"Enviando tarea {task_id}..."
            
            msg = json.dumps(task) + "\n"
            client_socket.sendall(msg.encode('utf-8'))
            
            with state_lock:
                clients_ui_state[client_index] = f"Esperando por la tarea {task_id}..."
                
            response_line = reader.readline()
            if response_line:
                result = json.loads(response_line)
                with state_lock:
                    clients_ui_state[client_index] = f"Recibido ✔: {result['task_id']} | Result: {result['status']}"
            
            time.sleep(random.uniform(0.6, 1.4)) # Pausa entre tareas para visualizaci÷on
            
        with state_lock:
            clients_ui_state[client_index] = "Todas las tareas completadas. Desconectando."
            
    except Exception as e:
        with state_lock:
            clients_ui_state[client_index] = f"Error de conexión"
    finally:
        client_socket.close()

if __name__ == "__main__":
    threading.Thread(target=update_dashboard, daemon=True).start()
    
    threads = []
    # Creamos un hilo por cada cliente simulado
    for i in range(1, NUM_CLIENTS + 1):
        t = threading.Thread(target=run_client, args=(i,))
        threads.append(t)
        t.start()
        # time.sleep(0.25) # Desfasaje para que no inicien todos al mismo tiempo
        
    for t in threads:
        t.join()
        
    time.sleep(2)
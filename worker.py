import random
import socket
import threading
import json
import time
import sys
from utils import dashboard

HOST = '127.0.0.1'
PORT = 8001
NUM_WORKERS = 3

state_lock = threading.Lock()
workers_ui_state = {}

def update_dashboard():
    dashboard.clear_screen()
    
    while True:
        with state_lock:
            sections = [
                ("", "Nodo Worker", workers_ui_state)
            ]
            
            output = dashboard.generate_panel("DASHBOARD DE WORKERS", sections)
            sys.stdout.write(output)
            sys.stdout.flush()
        time.sleep(0.1)

# Simula un nodo worker procesando tareas
def run_worker(worker_index):
    with state_lock:
        workers_ui_state[worker_index] = "Conectando..."

    worker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        time.sleep(random.uniform(0.2, 0.6))
        worker_socket.connect((HOST, PORT))
        with state_lock:
            workers_ui_state[worker_index] = "Registrado - Esperando por tareas"            
        reader = worker_socket.makefile('r', encoding='utf-8')
        
        while True:
            line = reader.readline()
            if not line:
                break
                
            task = json.loads(line)
            task_id = task['task_id']
            
            with state_lock:
                workers_ui_state[worker_index] = f"Procesando tarea {task_id}..."
                
            time.sleep(random.uniform(2.0, 3.5))
            
            result = {
                "task_id": task_id,
                "status": "Success",
                "processed_by": f"Node-{worker_index}"
            }
            
            msg = json.dumps(result) + "\n"
            worker_socket.sendall(msg.encode('utf-8'))
            
            with state_lock:
                workers_ui_state[worker_index] = f"Tarea {task_id} completada"
                
    except Exception as e:
        with state_lock:
            workers_ui_state[worker_index] = "Desconectado/Error"
    finally:
        worker_socket.close()

if __name__ == "__main__":
    threading.Thread(target=update_dashboard, daemon=True).start()
    
    threads = []
    # Creamos un pool de threads, cada uno emulando un worker en el cluster
    for i in range(1, NUM_WORKERS + 1):
        t = threading.Thread(target=run_worker, args=(i,), daemon=True)
        threads.append(t)
        t.start()
        
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sys.exit(0)
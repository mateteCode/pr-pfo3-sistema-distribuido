import socket
import threading
import json
import time
import sys
from utils import dashboard

# Configuracion de red
CLIENT_PORT = 8000
WORKER_PORT = 8001
HOST = '127.0.0.1'

# Estado del sistema (para el dashboard)
state_lock = threading.Lock()
clients_state = {}
workers_state = {}

# Estructuras de datos para el balanceo de carga
workers_list = []
worker_rr_index = 0
task_mapping = {} # Mapea task_id -> client_socket

def update_dashboard():
    dashboard.clear_screen()
    
    while True:
        with state_lock:
            sections = [
                ("WORKERS", "Worker", workers_state),
                ("CLIENTES", "Cliente", clients_state)
            ]
            
            output = dashboard.generate_panel("DASHBOARD DEL BALANCEADOR DE CARGA", sections)
            sys.stdout.write(output)
            sys.stdout.flush()
        time.sleep(0.2)

# Maneja la conexion con un cliente individual
def handle_client(client_socket, address):
    client_id = f"{address[0]}:{address[1]}"
    
    with state_lock:
        clients_state[client_id] = "Conectado - Esperando por tareas"
        
    try:
        # Usamos makefile para leer linea por linea (JSON terminado en \n)
        reader = client_socket.makefile('r', encoding='utf-8')
        while True:
            line = reader.readline()
            if not line:
                break
                
            task = json.loads(line)
            task_id = task['task_id']
            
            with state_lock:
                clients_state[client_id] = f"Enviando tarea {task_id}"
                # Guardamos el socket del cliente para devolverle la respuesta
                task_mapping[task_id] = client_socket
                
            distribute_task(task)
            
    except Exception:
        pass
    finally:
        with state_lock:
            clients_state[client_id] = "Desconectado"
        client_socket.close()

# Maneja la conexion con un worker individual
def handle_worker(worker_socket, address):
    worker_id = f"{address[0]}:{address[1]}"
    
    with state_lock:
        workers_state[worker_id] = "Conectado - Disponible"
        workers_list.append(worker_socket)
        
    try:
        reader = worker_socket.makefile('r', encoding='utf-8')
        while True:
            line = reader.readline()
            if not line:
                break
                
            result_data = json.loads(line)
            task_id = result_data['task_id']
            
            with state_lock:
                workers_state[worker_id] = f"Tarea {task_id} completada - Disponible"
            
            # Buscamos a quien pertenece esta tarea y le enviamos el resultado
            return_result_to_client(task_id, result_data)
            
    except Exception:
        pass
    finally:
        with state_lock:
            workers_state[worker_id] = "Desconectado"
            if worker_socket in workers_list:
                workers_list.remove(worker_socket)
        worker_socket.close()

# Asigna la tarea a un worker usando Round-Robin
def distribute_task(task):
    global worker_rr_index
    
    with state_lock:
        if not workers_list:
            # En un sistema real se se usaria una cola RabbitMQ
            return
            
        # Algoritmo Round-Robin
        worker_socket = workers_list[worker_rr_index]
        worker_rr_index = (worker_rr_index + 1) % len(workers_list)
        
    try:
        msg = json.dumps(task) + "\n"
        worker_socket.sendall(msg.encode('utf-8'))
    except Exception:
        # Si falla, el worker maneja su propia desconexion
        pass

# Devuelve el resultado procesado al cliente original
def return_result_to_client(task_id, result_data):
    with state_lock:
        if task_id in task_mapping:
            client_socket = task_mapping[task_id]
            try:
                msg = json.dumps(result_data) + "\n"
                client_socket.sendall(msg.encode('utf-8'))
                
                # Encontramos el ID del cliente para actualizar el dashboard
                client_addr = client_socket.getpeername()
                c_id = f"{client_addr[0]}:{client_addr[1]}"
                clients_state[c_id] = f"Respuesta recibida para la tarea {task_id}"
                
            except Exception:
                pass
            finally:
                del task_mapping[task_id]

# Configura el socket, escucha y acepta conexiones
def accept_connections(port, handler_function):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, port))
    server.listen(10)
    
    while True:
        conn, addr = server.accept()
        t = threading.Thread(target=handler_function, args=(conn, addr), daemon=True)
        t.start()

if __name__ == "__main__":
    # Hilo para el dashboard
    threading.Thread(target=update_dashboard, daemon=True).start()
    
    # Hilos para aceptar conexiones de clientes y workers
    threading.Thread(target=accept_connections, args=(CLIENT_PORT, handle_client), daemon=True).start()
    threading.Thread(target=accept_connections, args=(WORKER_PORT, handle_worker), daemon=True).start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sys.exit(0)
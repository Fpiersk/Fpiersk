import socket
import threading

HOST = '0.0.0.0'  # слушаем все интерфейсы
PORT = 65432

clients = []

def handle_client(conn, addr):
    print(f"Connected by {addr}")
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            # ретранслируем полученные данные всем клиентам кроме отправителя
            for c in clients:
                if c != conn:
                    try:
                        c.sendall(data)
                    except:
                        pass
    except:
        pass
    finally:
        print(f"Disconnected {addr}")
        clients.remove(conn)
        conn.close()

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server started on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            clients.append(conn)
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    main()

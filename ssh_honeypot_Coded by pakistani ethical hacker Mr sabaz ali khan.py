import socket
import threading
import json
import time
import os
from datetime import datetime

class SSHHoneypot:
    def __init__(self, host='0.0.0.0', port=2222, log_dir='honeypot_logs'):
        self.host = host
        self.port = port
        self.log_dir = log_dir
        self.active_connections = 0
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    def log_activity(self, client_ip, data):
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'client_ip': client_ip,
            'data': data
        }
        log_file = os.path.join(self.log_dir, f'honeypot_{datetime.now().date()}.json')
        with open(log_file, 'a') as f:
            json.dump(log_entry, f)
            f.write('\n')

    def simulate_ssh_banner(self, client_socket):
        banner = "SSH-2.0-OpenSSH_7.4p1 Debian-10+deb9u7\r\n"
        client_socket.send(banner.encode())

    def handle_connection(self, client_socket, client_address):
        self.active_connections += 1
        client_ip = client_address[0]
        try:
            self.log_activity(client_ip, "Connection established")
            self.simulate_ssh_banner(client_socket)

            # Simulate SSH login prompt
            client_socket.send(b"login: ")
            username = client_socket.recv(1024).decode().strip()
            self.log_activity(client_ip, f"Username attempted: {username}")

            client_socket.send(b"Password: ")
            password = client_socket.recv(1024).decode().strip()
            self.log_activity(client_ip, f"Password attempted: {password}")

            # Fake authentication failure
            client_socket.send(b"Permission denied, please try again.\r\n")
            time.sleep(1)

            # Fake command prompt
            client_socket.send(b"root@debian:~# ")
            command = client_socket.recv(1024).decode().strip()
            self.log_activity(client_ip, f"Command attempted: {command}")

            # Simulate command output
            if command:
                client_socket.send(b"command not found\r\n")
            else:
                client_socket.send(b"\r\n")

        except Exception as e:
            self.log_activity(client_ip, f"Error: {str(e)}")
        finally:
            self.active_connections -= 1
            client_socket.close()
            self.log_activity(client_ip, "Connection closed")

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(5)
        print(f"[*] Honeypot listening on {self.host}:{self.port}")

        try:
            while True:
                client_socket, client_address = server.accept()
                client_thread = threading.Thread(
                    target=self.handle_connection,
                    args=(client_socket, client_address)
                )
                client_thread.start()
        except KeyboardInterrupt:
            print("\n[*] Shutting down honeypot...")
            server.close()

if __name__ == "__main__":
    honeypot = SSHHoneypot()
    honeypot.start()
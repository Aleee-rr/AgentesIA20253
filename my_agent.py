# my_agent.py
import socket
import sys
import time
import re
import random

SERVER = ("localhost", 6000)
INIT_RE = re.compile(r"\(init\s+([lr])\s+(\d+)", re.IGNORECASE)

class SoccerAgent:
    def __init__(self, team_name="MY_TEAM"):
        self.team_name = team_name
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(2.0)
        self.side = None
        self.player_number = None

    def send(self, msg):
        """Envía un mensaje al servidor"""
        self.sock.sendto(msg.encode(), SERVER)

    def recv(self):
        """Recibe un mensaje del servidor"""
        try:
            data, _ = self.sock.recvfrom(4096)
            return data.decode()
        except socket.timeout:
            return ""

    def connect(self):
        """Conecta con el servidor"""
        print(f"Conectando al servidor como {self.team_name}...")
        self.send(f"(init {self.team_name})")

        init_data = ""
        start_time = time.time()

        while time.time() - start_time < 5:
            data = self.recv()
            if data:
                init_data += data
                match = INIT_RE.search(init_data)
                if match:
                    self.side = match.group(1)
                    self.player_number = int(match.group(2))
                    print(f"✅ Conectado! Lado: {self.side}, Jugador: {self.player_number}")
                    self.sock.settimeout(None)
                    return
        print("❌ No se recibió respuesta del servidor al init()")

    def move_to_start_position(self):
        """Posiciona al jugador según su número"""
        # Posiciones iniciales de ejemplo
        x_positions = [-49, -40, -35, -30, -25, -20, -15, -10, -5, 0, 5]
        y_positions = [0, 8, 3, -3, -8, 6, -6, 10, -10, 0, 0]

        # Si no hay número asignado, usa posición base
        if not self.player_number:
            x, y = -40, 0
        else:
            idx = max(0, min(self.player_number - 1, 10))
            x, y = x_positions[idx], y_positions[idx]

        # Ajusta si es lado derecho
        if self.side == "r":
            x = -x  # espejo horizontal

        print(f"📍 Moviendo jugador {self.player_number} a ({x}, {y})")
        for _ in range(3):
            self.send(f"(move {x} {y})")
            time.sleep(0.2)

    def play(self):
        """Bucle principal del agente"""
        print("Entrando en ciclo de juego...")

        # Mover a posición inicial antes del kickoff
        self.move_to_start_position()

        while True:
            data = self.recv()
            if data:
                # Puedes imprimir para depuración:
                # print("Percepción:", data[:80])
                pass

            # Movimiento básico: corre hacia adelante con potencia variable
            dash_power = random.uniform(40, 70)
            self.send(f"(dash {dash_power:.1f})")

            # Gira aleatoriamente un poco
            turn_angle = random.uniform(-20, 20)
            self.send(f"(turn {turn_angle:.1f})")

            time.sleep(0.2)


if __name__ == "__main__":
    team = sys.argv[1] if len(sys.argv) > 1 else "MY_TEAM"
    agent = SoccerAgent(team)
    agent.connect()
    agent.play()


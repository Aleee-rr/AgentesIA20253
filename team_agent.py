import socket
import time
import threading
import json
import os
import re
import random

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 6000
NUM_PLAYERS = 11
TEAM_NAME = "MY_TEAM"
CONF_FILE = "conf_file.conf"

INIT_RE = re.compile(r"\(init\s+([lrLR])\s+(\d+)", re.IGNORECASE)


def load_positions(conf_file):
    """Carga posiciones iniciales desde el archivo conf_file.conf"""
    if not os.path.exists(conf_file):
        raise FileNotFoundError(f"No se encontró {conf_file}")
    with open(conf_file, "r") as f:
        data = json.load(f)

    positions = {}
    for i in range(1, NUM_PLAYERS + 1):
        entry = data["data"][0].get(str(i))
        if entry is None:
            raise KeyError(f"No hay posición para '{i}' en {conf_file}")
        positions[i] = (float(entry["x"]), float(entry["y"]))
    return positions


def safe_send(sock, text):
    """Envía comandos al servidor de forma segura"""
    try:
        sock.sendto(text.encode(), (SERVER_HOST, SERVER_PORT))
    except Exception:
        pass


def random_move_loop(sock, unum):
    """Movimiento aleatorio continuo"""
    # Desfase inicial leve (para que no se muevan todos sincronizados)
    time.sleep(0.1 * (unum % 5))
    while True:
        try:
            # Gira aleatoriamente un poco
            angle = random.uniform(-45.0, 45.0)
            safe_send(sock, f"(turn {angle:.2f})")
            time.sleep(0.15)

            # Da un pequeño impulso
            power = random.uniform(30, 80)
            safe_send(sock, f"(dash {power:.1f})")

            # Espera un tiempo aleatorio antes de volver a moverse
            time.sleep(random.uniform(0.4, 1.2))
        except Exception:
            break


def player_thread(idx, positions):
    """Inicia un jugador, lo posiciona y arranca su movimiento aleatorio"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", 0))
    sock.settimeout(1.0)

    print(f"[Jugador {idx}] Enviando init...")
    safe_send(sock, f"(init {TEAM_NAME})")

    side = None
    unum = None
    init_buf = ""
    t0 = time.time()

    # Esperar init del servidor
    while time.time() - t0 < 5:
        try:
            data, _ = sock.recvfrom(8192)
            msg = data.decode(errors="ignore")
            init_buf += msg
            m = INIT_RE.search(init_buf)
            if m:
                side = m.group(1).lower()
                unum = int(m.group(2))
                print(f"[Jugador {idx}] Init detectado: side={side}, unum={unum}")
                break
        except socket.timeout:
            continue

    if unum is None:
        print(f"[Jugador {idx}] No se detectó init. Cerrando socket.")
        sock.close()
        return

    # Obtener posición inicial
    target_pos = positions.get(unum) or positions.get(idx)
    if not target_pos:
        print(f"[Jugador {idx}] No hay posición definida, usando (-40,0)")
        x, y = (-40.0, 0.0)
    else:
        x, y = target_pos

    # Reflejar coordenadas si el jugador está en el lado derecho
    if side == "r":
        x = -x

    print(f"[Jugador {unum}] Moviéndose a posición inicial ({x:.2f}, {y:.2f})")
    for _ in range(6):
        safe_send(sock, f"(move {x:.2f} {y:.2f})")
        safe_send(sock, "(turn 0)")
        time.sleep(0.1)

    # Una vez posicionado, arranca movimiento aleatorio siempre
    threading.Thread(target=random_move_loop, args=(sock, unum), daemon=True).start()

    # Mantener socket vivo
    while True:
        try:
            data, _ = sock.recvfrom(8192)
            msg = data.decode(errors="ignore")
            # No hace falta analizar mensajes; los jugadores solo se mueven
        except socket.timeout:
            continue
        except Exception:
            break


def main():
    try:
        positions = load_positions(CONF_FILE)
    except Exception as e:
        print("ERROR cargando conf:", e)
        return

    threads = []
    for i in range(1, NUM_PLAYERS + 1):
        t = threading.Thread(target=player_thread, args=(i, positions), daemon=True)
        t.start()
        threads.append(t)
        time.sleep(0.12)

    print("[INFO] Todos los jugadores iniciados y moviéndose aleatoriamente.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Interrupción por usuario. Cerrando equipo.")


if __name__ == "__main__":
    main()


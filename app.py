from flask import Flask, render_template, jsonify
import socket
import subprocess
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import threading
import time
import requests

app = Flask(__name__)

# Diccionario con detalles de las IPs privadas
ip_details = {
    "10.18.63.1": {"Region": "Región Antofagasta", "Ciudad": "Antofagasta", "Pais": "Chile"},
    "10.18.133.1": {"Region": "Región Coquimbo", "Ciudad": "Coquimbo", "Pais": "Chile"},
    "10.18.61.1": {"Region": "Región Metropolitana", "Ciudad": "Santiago", "Pais": "Chile"},
    "10.18.65.1": {"Region": "Región del BioBio", "Ciudad": "Concepción", "Pais": "Chile"},
    "10.18.115.1": {"Region": "Región de la Araucania", "Ciudad": "Temuco", "Pais": "Chile"},
    "10.18.67.1": {"Region": "Región de los Lagos", "Ciudad": "Puerto Montt", "Pais": "Chile"},
    "8.242.207.9": {"Region": "CIRION", "Ciudad": "GATEWAY", "Pais": "Chile"},
    "216.241.20.193": {"Region": "IFX", "Ciudad": "GATEWAY", "Pais": "Chile"},   
}

# Diccionario para registrar los tiempos de caída y envío de correo de cada IP
down_since = {}

# Lista para almacenar los mensajes de consola
console_messages = []

# Función para agregar mensajes a la lista de consola con fecha y hora
def add_console_message(message):
    """Añadir un mensaje a la lista de consola con marca de tiempo exacta, con un máximo de 100 mensajes."""
    timestamp = datetime.now().strftime("[%d/%b/%Y %H:%M:%S]")  # Formato: [18/Mar/2025 15:44:30]
    console_messages.append(f"{timestamp} {message}")
    if len(console_messages) > 100:  # Limitar a los últimos 100 mensajes
        console_messages.pop(0)

# Función para enviar correos electrónicos
def send_email(ip, details):
    sender_email = "estatusredesksb@gmail.com"
    receiver_email = "javier.geneve@gmail.com"
    password = "fijj gnwu lhbg wsne"  # Contraseña de aplicación de Google

    subject = f"Alerta: IP {ip} está caída"
    body = (
        f"IP: {ip}\n"
        f"Estado: {details.get('Estado', 'Desconocido')}\n"
        f"Región: {details.get('Region', 'Desconocido')}\n"
        f"Ciudad: {details.get('Ciudad', 'Desconocido')}\n"
        f"País: {details.get('Pais', 'Desconocido')}\n"
        f"Nombre del Host: {details.get('HostName', 'Desconocido')}\n"
        f"Hora: {details.get('Hora', 'Desconocida')}\n"
    )

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        add_console_message(f"Correo enviado para la IP {ip}")
    except Exception as e:
        add_console_message(f"Error al enviar correo: {e}")

# Función para obtener detalles locales de una IP
def get_local_ip_details(ip):
    try:
        host_name = socket.gethostbyaddr(ip)[0]
    except socket.herror:
        host_name = "Desconocido"

    details = ip_details.get(ip, {"Region": "Desconocida", "Ciudad": "Desconocida", "Pais": "Desconocido"})
    details["HostName"] = host_name
    return details

# Función para realizar ping con subprocess
def check_ip_status(ip):
    try:
        result = subprocess.run(
            ["ping", "-n", "4", ip],  # Cambia a ["ping", "-c", "4", ip] en Linux/Unix
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        add_console_message(f"Ping Output for {ip}:\n{result.stdout}")
        add_console_message(f"Ping Error for {ip}:\n{result.stderr}")

        if result.returncode == 0:
            return "Activa"
        else:
            return "Caída"
    except Exception as e:
        add_console_message(f"Error al ejecutar ping para {ip}: {e}")
        return "Error"

# Función para verificar la navegación HTTP
def check_navigation(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return "Navegación Activa"
        else:
            return f"Problemas de Navegación (HTTP {response.status_code})"
    except requests.RequestException as e:
        return f"Problemas de Navegación: {e}"

# Función para combinar estado de red y navegación
def check_ip_status_and_navigation(ip, url):
    network_status = check_ip_status(ip)
    if network_status == "Activa":
        navigation_status = check_navigation(url)
    else:
        navigation_status = "Sin Navegación (Red Caída)"
    return network_status, navigation_status

# Función para obtener detalles de estado de IP
def get_ip_status_and_details(ip):
    url = "http://www.google.com"  # URL fija para navegación
    network_status, navigation_status = check_ip_status_and_navigation(ip, url)
    details = get_local_ip_details(ip)
    current_time = datetime.now().strftime("%H:%M:%S %d-%m")
    details["Hora"] = current_time
    details["Estado"] = network_status
    details["Navegación"] = navigation_status
    details["IP"] = ip

    return details

# Función para monitorear la red
def monitor_network():
    while True:
        ips = ["10.18.63.1", "10.18.133.1", "10.18.61.1", "10.18.65.1", "10.18.115.1", "10.18.67.1", "8.242.207.9", "216.241.20.193"]
        for ip in ips:
            status = check_ip_status(ip)
            if status == "Caída":
                if ip not in down_since:
                    down_since[ip] = {"first_down": datetime.now(), "last_email": None}
                    details = get_ip_status_and_details(ip)
                    details["Estado"] = "Micro Corte"
                    add_console_message(f"IP {ip} está en Micro Corte")
                else:
                    elapsed = datetime.now() - down_since[ip]["first_down"]
                    if elapsed > timedelta(seconds=4):
                        details = get_ip_status_and_details(ip)
                        details["Estado"] = "Caída"
                        if details["Estado"] == "Caída" and (down_since[ip]["last_email"] is None or datetime.now() - down_since[ip]["last_email"] > timedelta(minutes=30)):
                            send_email(ip, details)
                            down_since[ip]["last_email"] = datetime.now()
                    else:
                        details = get_ip_status_and_details(ip)
                        details["Estado"] = "Micro Corte"
                        add_console_message(f"IP {ip} está en Micro Corte")
            else:
                if ip in down_since:
                    del down_since[ip]
        time.sleep(10)

# Endpoint para devolver los mensajes de consola
@app.route('/console_logs')
def get_console_logs():
    return jsonify(console_messages)

# Página principal
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_status')
def get_status():
    ips = ["10.18.63.1", "10.18.133.1", "10.18.61.1", "10.18.65.1", "10.18.115.1", "10.18.67.1", "8.242.207.9", "216.241.20.193"]
    ip_info_list = []
    for ip in ips:
        details = get_ip_status_and_details(ip)
        if ip in down_since:
            elapsed = datetime.now() - down_since[ip]["first_down"]
            if elapsed <= timedelta(seconds=4):
                details["Estado"] = "Micro Corte"
        ip_info_list.append(details)
    return jsonify(ip_info_list)

@app.errorhandler(400)
def bad_request(error):
    return "Bad request!", 400

if __name__ == "__main__":
    threading.Thread(target=monitor_network, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)

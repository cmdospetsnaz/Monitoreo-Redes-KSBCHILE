from flask import Flask, render_template, jsonify
import socket
from ping3 import ping
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import threading
import time

app = Flask(__name__)

# Diccionario con detalles de las IPs privadas
ip_details = {
    "10.18.63.1": {"Region": "Región Antofagasta", "Ciudad": "Antofagasta", "Pais": "Chile"},
    "10.18.133.1": {"Region": "Región Coquimbo", "Ciudad": "Coquimbo", "Pais": "Chile"},
    "10.18.65.1": {"Region": "Región del BioBio", "Ciudad": "Concepción", "Pais": "Chile"},
    "10.18.115.1": {"Region": "Región de la Araucania", "Ciudad": "Temuco", "Pais": "Chile"},
    "10.18.67.1": {"Region": "Región de los Lagos", "Ciudad": "Puerto Montt", "Pais": "Chile"},
    "8.242.207.9": {"Region": "CIRION", "Ciudad": "GATEWAY", "Pais": "Chile"},
    "216.241.20.193": {"Region": "IFX", "Ciudad": "GATEWAY", "Pais": "Chile"},
    "10.18.61.1": {"Region": "Región Metropolitana", "Ciudad": "Santiago", "Pais": "Chile"},
}

# Diccionario para registrar los tiempos de caída y envío de correo de cada IP
down_since = {}

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
        print(f"Correo enviado para la IP {ip}")
    except Exception as e:
        print(f"Error al enviar correo: {e}")

def get_local_ip_details(ip):
    try:
        host_name = socket.gethostbyaddr(ip)[0]
    except socket.herror:
        host_name = "Desconocido"

    details = ip_details.get(ip, {"Region": "Desconocida", "Ciudad": "Desconocida", "Pais": "Desconocido"})
    details["HostName"] = host_name
    return details

def check_ip_status(ip):
    response_time = ping(ip)
    if response_time is None:
        return "Caída"
    else:
        return "Activa"

def get_ip_status_and_details(ip):
    status = check_ip_status(ip)
    details = get_local_ip_details(ip)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    details["Hora"] = current_time
    details["Estado"] = status
    details["IP"] = ip  # Añadir IP al diccionario
    return details

def monitor_network():
    while True:
        ips = ["10.18.63.1", "10.18.133.1", "10.18.65.1", "10.18.115.1", "10.18.67.1", "8.242.207.9", "216.241.20.193", "10.18.61.1"]
        for ip in ips:
            status = check_ip_status(ip)
            if status == "Caída":
                if ip not in down_since:
                    down_since[ip] = {"first_down": datetime.now(), "last_email": None}
                else:
                    if datetime.now() - down_since[ip]["first_down"] > timedelta(minutes=1):
                        if down_since[ip]["last_email"] is None or datetime.now() - down_since[ip]["last_email"] > timedelta(minutes=30):
                            details = get_ip_status_and_details(ip)
                            send_email(ip, details)
                            down_since[ip]["last_email"] = datetime.now()
            else:
                if ip in down_since:
                    del down_since[ip]
        time.sleep(10)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_status')
def get_status():
    ips = ["10.18.63.1", "10.18.133.1", "10.18.65.1", "10.18.115.1", "10.18.67.1", "8.242.207.9", "216.241.20.193", "10.18.61.1"]
    ip_info_list = [get_ip_status_and_details(ip) for ip in ips]
    return jsonify(ip_info_list)

@app.errorhandler(400)
def bad_request(error):
    return "Bad request!", 400

if __name__ == "__main__":
    threading.Thread(target=monitor_network, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)

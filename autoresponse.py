
//v2 de el script de auto respuesta automaticas, se actulizo la seguridad y donde se envian las contraseñas de acceso, se actulizo el metodo de envio a un servidor local 
  


import imaplib
import smtplib
import email
import os
from email.mime.text import MIMEText
from email.utils import formataddr, parseaddr
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Cargar variables de entorno desde un archivo .env
load_dotenv()

# Configuración del servidor de correo desde variables de entorno
IMAP_SERVER = os.getenv('IMAP_SERVER')
IMAP_USER = os.getenv('IMAP_USER')
IMAP_PASSWORD = os.getenv('IMAP_PASSWORD')
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = 587  # Usa 465 para SSL
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

# Conectar al servidor IMAP
def connect_imap():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(IMAP_USER, IMAP_PASSWORD)
        mail.select('inbox')
        return mail
    except imaplib.IMAP4.error as e:
        print(f"Error al conectar al servidor IMAP: {e}")
        return None

# Conectar al servidor SMTP
def connect_smtp():
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Seguridad
        server.login(SMTP_USER, SMTP_PASSWORD)
        return server
    except smtplib.SMTPException as e:
        print(f"Error al conectar al servidor SMTP: {e}")
        return None

# Buscar correos no respondidos en las últimas 48 horas
def fetch_unanswered_emails(mail):
    date = (datetime.now() - timedelta(days=2)).strftime("%d-%b-%Y")
    status, response = mail.search(None, f'(SINCE {date})')

    if status != 'OK':
        print("No se pudo obtener los correos.")
        return []

    emails = []
    for num in response[0].split():
        status, data = mail.fetch(num, '(RFC822)')
        if status != 'OK' or not data[0]:
            continue  # Evita errores si no hay datos válidos

        msg = email.message_from_bytes(data[0][1], policy=email.policy.default)
        email_date = email.utils.parsedate_to_datetime(msg['Date'])
        
        # Verifica si el correo tiene más de 48 horas
        if datetime.now() - email_date >= timedelta(days=2):
            sender_name, sender_email = parseaddr(msg['From'])
            emails.append((sender_email, msg['Subject'], msg['Message-ID']))

    return emails

# Enviar respuesta a un correo
def send_reply(server, sender_email, msg_subject, msg_id):
    try:
        reply = MIMEText('Este es un recordatorio de que su correo no ha sido respondido en más de 48 horas.')
        reply['Subject'] = 'Re: ' + msg_subject
        reply['From'] = formataddr(("Soporte Técnico", SMTP_USER))
        reply['To'] = sender_email
        reply['In-Reply-To'] = msg_id
        reply['References'] = msg_id

        server.sendmail(SMTP_USER, sender_email, reply.as_string())
        print(f"Respuesta enviada a {sender_email}")
    except Exception as e:
        print(f"Error al enviar correo a {sender_email}: {e}")

# Generar reporte de correos respondidos
def generate_report(responded_emails):
    with open('reporte_respuestas.txt', 'w') as report_file:
        report_file.write('Correos respondidos:\n')
        for email in responded_emails:
            report_file.write(f'{email}\n')

# Función principal
def main():
    # Conectar a los servidores
    mail = connect_imap()
    if not mail:
        return

    server = connect_smtp()
    if not server:
        return

    responded_emails = []

    # Buscar correos no respondidos
    unanswered_emails = fetch_unanswered_emails(mail)
    
    for sender_email, msg_subject, msg_id in unanswered_emails:
        send_reply(server, sender_email, msg_subject, msg_id)
        responded_emails.append(sender_email)

    # Generar reporte
    generate_report(responded_emails)

    # Cerrar conexiones
    mail.logout()
    server.quit()

if __name__ == '__main__':
    main()

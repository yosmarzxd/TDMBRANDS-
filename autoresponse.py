import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.utils import formataddr, parseaddr
from datetime import datetime, timedelta

# Configuración del servidor de correo
IMAP_SERVER = 'imap.example.com'
IMAP_USER = 'tu_correo@example.com'
IMAP_PASSWORD = 'tu_contraseña'
SMTP_SERVER = 'smtp.example.com'
SMTP_PORT = 587  # Usa 465 para SSL
SMTP_USER = 'tu_correo@example.com'
SMTP_PASSWORD = 'tu_contraseña'

# Conectar al servidor IMAP
mail = imaplib.IMAP4_SSL(IMAP_SERVER)
mail.login(IMAP_USER, IMAP_PASSWORD)
mail.select('inbox')

# Buscar correos no respondidos en las últimas 48 horas
date = (datetime.now() - timedelta(days=2)).strftime("%d-%b-%Y")
status, response = mail.search(None, f'(SINCE {date})')

responded_emails = []

for num in response[0].split():
    status, data = mail.fetch(num, '(RFC822)')
    
    if status != 'OK' or not data[0]:
        continue  # Evita errores si no hay datos válidos
    
    msg = email.message_from_bytes(data[0][1], policy=email.policy.default)
    email_date = email.utils.parsedate_to_datetime(msg['Date'])
    
    sender_name, sender_email = parseaddr(msg['From'])
    
    # Verifica si el correo es reciente
    if datetime.now() - email_date < timedelta(days=2):
        continue
    
    # Crear respuesta
    reply = MIMEText('Este es un recordatorio de que su correo no ha sido respondido en más de 48 horas.')
    reply['Subject'] = 'Re: ' + msg['Subject']
    reply['From'] = formataddr(("Soporte Técnico", SMTP_USER))
    reply['To'] = sender_email
    reply['In-Reply-To'] = msg['Message-ID']
    reply['References'] = msg['Message-ID']
    
    # Enviar correo de respuesta
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Seguridad
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, sender_email, reply.as_string())
        
        responded_emails.append(sender_email)
    
    except Exception as e:
        print(f"Error al enviar correo a {sender_email}: {e}")

# Generar reporte
with open('reporte_respuestas.txt', 'w') as report_file:
    report_file.write('Correos respondidos:\n')
    for email in responded_emails:
        report_file.write(f'{email}\n')

# Cerrar conexión
mail.logout()
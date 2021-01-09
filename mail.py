import smtplib, ssl

port = 465  # For SSL
smtp_server = "smtp.gmail.com"
sender_email = "shakileash2000@gmail.com"  # Enter your address
receiver_email = "sirenatechnology@gmail.com"  # Enter receiver address
password = "vvnurinqqtagonij"
message = """\
Subject: Crypto Coin alert

This message is sent from Python."""

def send_mail(reciever_mail,msg):
    context = ssl.create_default_context()
    message = """\
    Subject: ALert

    Hi , 
    this is BitHook alert the price of """+ msg +""" is falling please sell it soon...
        
    - BitHook"""
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, reciever_mail, message)

#send_mail("shakileash2000@gmail.com","BTC")
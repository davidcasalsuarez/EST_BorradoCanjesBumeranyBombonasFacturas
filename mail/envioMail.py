#!/usr/bin/python
# -*- coding: utf-8 -*-

from email.mime.text import MIMEText
from smtplib import SMTP
from datetime import datetime
import logging
import traceback


from_address=''
password=''

def setUserAndPassword(user, passw):
    globals()['from_address'] = user
    globals()['password'] = passw


def formatearFecha(fecha):
    if hasattr(fecha, "strftime"):
        return fecha.strftime("%d/%m/%Y")
    return str(fecha)


def formatearImporte(importe):
    try:
        return ("%.2f" % float(importe)).replace(".", ",") + " EUR"
    except:
        return str(importe)


def enviarMail(email, listadoProductos, anio):
    try:
        to_address = email
        enviaMensaje = False
        if(len(listadoProductos) > 0):
            message = "\nSe han emitido las siguientes facturas con CANJES BUMERAN o Bombonas:\n\n"
            for emp in listadoProductos.keys():
                message = message + "\n-----------"+emp+":"
                num = 1
                for producto in listadoProductos.get(emp):
                    if(len(producto) >= 5):
                        message = (message + "\n" + str(num)
                                   + " - FACTURA " + str(producto[0])
                                   + " | FECHA " + formatearFecha(producto[1]))
                        if(len(producto) >= 6):
                            accion = str(producto[5])
                            if(accion.startswith("SOLO AVISO")):
                                etiquetaLinea = "LINEA DETECTADA - SOLO AVISO"
                            elif("ELIMINADAS DE LVFACTURACP" in accion):
                                etiquetaLinea = "LINEA ELIMINADA"
                            else:
                                etiquetaLinea = "LINEA DETECTADA - ELIMINACION NO CONFIRMADA"
                            message = (message + "\n    " + etiquetaLinea
                                       + " -> REFERENCIA " + str(producto[2])
                                       + " | CONCEPTO " + str(producto[3])
                                       + " | IMPORTE " + formatearImporte(producto[4])
                                       + "\n    RESULTADO -> " + accion)
                        else:
                            message = (message + "\n    LINEA DETECTADA"
                                       + " -> REFERENCIA " + str(producto[2])
                                       + " | CONCEPTO " + str(producto[3])
                                       + " | IMPORTE " + formatearImporte(producto[4]))
                    else:
                        message = (message + "\n" + str(num) + " - " + str(producto[0])
                                   + " | FECHA " + formatearFecha(producto[1]))
                    num = num + 1
                    enviaMensaje = True
        else:
            enviaMensaje = True
            message = "\nNo hay facturas pendientes con CANJES BUMERAN o Bombonas:\n\n"

        if(enviaMensaje):
            message = message + "\n\n\n\nPor favor, no conteste a este mail. Si ha recibido este correo por error háganoslo saber. \nMuchas gracias."
            
            mime_message = MIMEText(message, "plain")
            mime_message["From"] = from_address
            mime_message["To"] = to_address
            mime_message["Subject"] = "REEMISIÓN DE FACTURAS "+str(anio)
            
            smtp = SMTP("smtp.office365.com", 587)
            smtp.connect("smtp.office365.com", 587)
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(from_address, password) #fecha de nacimiento 1/01/1990
            
            #"Notificaciones.caducados"
            smtp.sendmail(from_address, to_address, mime_message.as_string())
            smtp.quit()
    except:
        logging.error("batchCanjesBumeran.py.- enviarMail: Se ha producido un error: " + traceback.format_exc())
        print("batchCanjesBumeran.py.- enviarMail: Se ha producido un error: " + traceback.format_exc())

    

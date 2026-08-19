# -*- coding: utf-8 -*-
'''
Created on 20 feb. 2019

@author: USUARIO
'''
from bbdd.wasoil import getBombonas, getCanjesBumeran, setRutaWasoil
from mail.envioMail import *
from datetime import datetime, timedelta
import logging
import configparser
import traceback

anio=''
listaEmpresas=[]
user=''
password=''

def leerProperties():
    try:
        #Leemos el fichero de configuracion
        config = configparser.ConfigParser()
        config.read(r'\\Vmapp\c\PROGRAMAS GALURESA\config.conf')
        #Obtenemos parametros
        anio = config.get('DEFAULT', 'anio')
        setRutaWasoil(config.get('DEFAULT','rutaWasoil2'))
        listaEmpresas = config.get('LISTA_EMPRESAS', 'listaEmpresasGlobal').split(",")
        #Obtenemos los parametros para el envio del mail
        setUserAndPassword(config.get('MAIL', 'usuarioEnvio'), config.get('MAIL', 'passEnvio'))
        #Configuramos el log
        rutaLog = config.get('DEFAULT', 'log')
        logging.basicConfig(filename=rutaLog+'batchCanjesBumeran.log',  # Nombre del archivo de registro
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            # Nivel de registro (puede ser DEBUG, INFO, WARNING, ERROR, CRITICAL)
                            level=logging.INFO)
        return anio, listaEmpresas
    except:
        logging.error("batchActualizarPreciosRamallosa.py.- main: Se ha producido un error: " + traceback.format_exc())
        

def main(anio, listaEmpresas):
    try:
        fechaAConsiderar = datetime.now() - timedelta(days = 7)
        fechaTexto = fechaAConsiderar.strftime("%d/%m/%Y")
        dictProductos = {}
        #Para cada LOCAL:
        for emp in listaEmpresas:
            listadoCanjes = getCanjesBumeran(emp,fechaTexto,anio)
            listadoBombonas = getBombonas(emp, fechaTexto, anio)
            logging.info("Canjes %s: %s", emp, str(listadoCanjes))
            logging.info("Bombonas %s: %s", emp, str(listadoBombonas))

            lineas = []
            if listadoCanjes is not None:
                lineas.extend(listadoCanjes.get(emp, []))
            if listadoBombonas is not None:
                lineas.extend(listadoBombonas.get(emp, []))

            lineasPorFactura = {}
            for linea in lineas:
                factura = str(linea[0])
                if factura not in lineasPorFactura:
                    lineasPorFactura[factura] = []
                lineasPorFactura[factura].append(linea)

            if len(lineasPorFactura) == 0:
                print(emp + " - SIN CANJES NI BOMBONAS EN FACTURAS")

            for factura, lineasFactura in lineasPorFactura.items():
                idsLineas = [linea[5] for linea in lineasFactura]
                # MODO SOLO AVISO: no borrar ni desasociar hasta reactivarlo.
                # correccionOk, estado = corregirLineasFactura(
                #     emp, factura, idsLineas, anio
                # )
                estado = "SOLO AVISO - NO SE HA ELIMINADO NI DESASOCIADO"

                if emp not in dictProductos:
                    dictProductos[emp] = []

                for linea in lineasFactura:
                    fechaLinea = linea[1].strftime("%d/%m/%Y") if hasattr(linea[1], "strftime") else str(linea[1])
                    referencia = str(linea[2])
                    concepto = str(linea[3])
                    importe = ("%.2f" % float(linea[4])).replace(".", ",")
                    dictProductos[emp].append(
                        (linea[0], linea[1], linea[2], linea[3], linea[4], estado)
                    )
                    print(emp + " - FACTURA " + factura + " - FECHA " + fechaLinea
                          + " - REFERENCIA " + referencia + " - CONCEPTO " + concepto
                          + " - IMPORTE " + importe + " EUR - ACCION " + estado)
                        
        #Enviamos mail al local con la lista de productos recabada
        enviarMail('albertodominguez@galuresa.com', dictProductos, str(fechaTexto))
        enviarMail('david.casalsuarez@galuresa.com', dictProductos, str(fechaTexto))
    except:
        logging.error("batchCanjesBumeran.py.- main: Se ha producido un error: " + traceback.format_exc())
    
if __name__ == "__main__":
    anio, listaEmpresas = leerProperties()
    main(anio, listaEmpresas)


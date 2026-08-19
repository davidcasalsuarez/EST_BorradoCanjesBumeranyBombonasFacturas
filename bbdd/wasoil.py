# -*- coding: utf-8 -*-
'''
Created on 3 jul. 2018

@author: USUARIO
'''
import pyodbc
import os
import logging
import traceback
import time

rutaWasoil = "Y:\\WASOIL5\\"
MODO_SOLO_AVISO = True

def setRutaWasoil(ruta):
    globals()['rutaWasoil'] = ruta

#Conectar con un solo booleano
def conectar(esGestion, empresa, anio):
    return conectarBBDD(esGestion, False, empresa, anio)

#Connector
def conectarBBDD(esGestion, esGestionTPV, empresa, anio):
    ''' config = configparser.ConfigParser()
    config = config.read('wasoil.properties')
    option = config.options("EMPRESAS")
    listaEmpresas = config.get('EMPRESAS', 'paxonal')
    ruta_inicio = config.get('RUTAS_MICROASIS', 'local_wasoil')'''
    
    try:
        #Si no se trata de la gestion obtenemos el archivo wasoil con los datos del tpv
        wasoil = "\\Wasoil.mdb"
        #Si se trata de la gestion obtenemos los datos que utiliza el programa wasoil, almacen2
        if esGestion:
            wasoil = str(anio)+"\\Wasoil4.mdb"
        #TPV volcado
        if esGestionTPV:
            wasoil = str(anio)+"\\Wasoil41.mdb"
            
        #rutaWasoil = "Y:\\WASOIL5\\"
        archivo = rutaWasoil+empresa+"\\"+wasoil
        #print(archivo)
        #archivo = "C:\\WASOIL5\\"+empresa+"\\"+wasoil
        #Permisos al archivo .mdb
        #os.chmod(archivo,777)
        #Conexion a la ruta indicada
        #conn = pyodbc.connect('Driver={Microsoft Access Driver (*.mdb, *.accdb)};Dbq='+archivo+';Uid=Admin;Pwd=;')
        conn = pyodbc.connect('Driver={Microsoft Access Driver (*.mdb)};Dbq='+archivo+';')
        
        return conn
    
    except:
        logging.error("wasoil.py.- conectar: No se ha podido conectar a la BBDD de Wasoil, " + traceback.format_exc())
        return None
    

#Metodo para obtener todos los datos de una empresa en base a una consulta
def ejecutarQueryListaEmpresasTag(listaEmpresas, esGestion, esGestionTPV, anio, consultaSql, *params):
    resultado={}
    anioInicioNegocio = 2015 #anio de comienxo del negocio
    #Recorremos el listado de empresas
    for k in listaEmpresas:
        try:
            if(anio is not None):
                ejecutarConsulta(esGestion, esGestionTPV, k, anio, consultaSql, resultado, params)
            else:
                #Cogemos todos los anios
                while(anioInicioNegocio <= int(time.strftime("%Y"))):
                    ejecutarConsulta(esGestion, esGestionTPV, k, anioInicioNegocio, consultaSql, resultado, params)
                    anioInicioNegocio += 1
        except:
            logging.error("wasoil.py.- ejecutarQueryListaEmpresas: Se ha producido un error al realizar la query : " + consultaSql 
                          + " para la empresa: " + k + ". " + traceback.format_exc())
    return resultado

#Metodo para ejecutar la consulta
def ejecutarConsulta(esGestion, esGestionTPV, empresa, anio, consultaSql, resultado, *params):
    try:
        conn = conectarBBDD(esGestion, esGestionTPV, empresa, anio)
        if(conn is not None):
            cur = conn.cursor()
            #Ejecutamos las consultas
            if(params is not None and len(params) > 0 and len(params[0]) > 0):
                cur.execute(consultaSql, *params)
            else:
                cur.execute(consultaSql)
            #Anhadimos los datos para todos  los anios
            #Si no es una temporal...
            if("into" not in consultaSql and "DROP" not in consultaSql and "update" not in consultaSql 
               and "delete from" not in consultaSql):
                if(len(resultado) > 0 and resultado.get(empresa) is not None 
                   and resultado[empresa] is not None):
                     resultado.get(empresa).append((list(cur.fetchall())))
                else:
                    resultado[empresa] = (list(cur.fetchall()))
            else:
                #comiteamos la temporal
                conn.commit()
            conn.close()
    except:
        logging.error("wasoil.py.- ejecutarQueryListaEmpresas: Se ha producido un error al realizar la query : " + consultaSql 
                    + traceback.format_exc())

'''
Metodo para obtener los canjes bumeran que se han metido en facturas
'''
def getCanjesBumeran(empresa, fechaConsiderada, anio):
    #Recuperamos el anio actual 
    listaEmpresas = [empresa]
    
    try:
        
        strsql = """SELECT numero, fecha, referencia, concepto, importe, ID
                    FROM LVFACTURACP
                    WHERE (
                        UCase(Trim(concepto)) = 'CANJE BUMERAN'
                        OR (referencia IS NOT NULL AND UCase(Trim(referencia)) = 'CANJE')
                    )
                    and fecha > #"""+transformarFechaAccess(fechaConsiderada)+"""#"""
        
        #Filtro mes
        resultado = ejecutarQueryListaEmpresasTag(listaEmpresas, True, False, str(anio), strsql)         
    
        return resultado
    
    except:
        logging.error("wasoil.py.- getCanjesBumeran: No se han podido obtener los datos, " + traceback.format_exc())
        return None
    

'''
Elimina de LVFACTURACP las lineas detectadas de CANJE o bombona y
desasocia en TPVLIN las lineas equivalentes vaciando nrofactpv.
Cada linea de factura se borra por su ID para no afectar a otros productos.
'''
def corregirLineasFactura(empresa, factura, idsLineas, anio):
    if MODO_SOLO_AVISO:
        return False, "SOLO AVISO - NO SE HA ELIMINADO NI DESASOCIADO"

    connGestion = None
    connTPV = None

    condicionLinea = """(
        UCase(Trim([concepto])) = 'CANJE BUMERAN'
        OR ([referencia] IS NOT NULL AND UCase(Trim([referencia])) = 'CANJE')
        OR ([referencia] IS NOT NULL AND Left(UCase(Trim([referencia])), 3) = '820')
        OR ([referencia] IS NOT NULL AND Left(UCase(Trim([referencia])), 6) = 'FNT820')
    )"""
    condicionTPV = """(
        UCase(Trim([codigo])) = 'CANJE'
        OR Left(UCase(Trim([codigo])), 3) = '820'
        OR Left(UCase(Trim([codigo])), 6) = 'FNT820'
    )"""

    try:
        connGestion = conectarBBDD(True, False, empresa, str(anio))
        connTPV = conectarBBDD(False, True, empresa, str(anio))
        if connGestion is None or connTPV is None:
            raise RuntimeError("No se pudo abrir Wasoil4.mdb o Wasoil41.mdb")

        curGestion = connGestion.cursor()
        curTPV = connTPV.cursor()

        curTPV.execute(
            "UPDATE TPVLIN SET nrofactpv = '' "
            "WHERE nrofactpv = ? AND " + condicionTPV,
            str(factura),
        )
        tpvDesasociadas = max(curTPV.rowcount, 0)

        lineasEliminadas = 0
        for idLinea in idsLineas:
            curGestion.execute(
                "DELETE FROM LVFACTURACP "
                "WHERE ID = ? AND numero = ? AND " + condicionLinea,
                int(idLinea),
                str(factura),
            )
            lineasEliminadas += max(curGestion.rowcount, 0)

        connTPV.commit()
        connGestion.commit()

        pendientesLV = 0
        for idLinea in idsLineas:
            curGestion.execute(
                "SELECT COUNT(*) FROM LVFACTURACP "
                "WHERE ID = ? AND numero = ? AND " + condicionLinea,
                int(idLinea),
                str(factura),
            )
            pendientesLV += int(curGestion.fetchone()[0])

        curTPV.execute(
            "SELECT COUNT(*) FROM TPVLIN "
            "WHERE nrofactpv = ? AND " + condicionTPV,
            str(factura),
        )
        pendientesTPV = int(curTPV.fetchone()[0])

        correcto = pendientesLV == 0 and pendientesTPV == 0
        if correcto:
            estado = (
                "LINEAS CANJE/BOMBONA ELIMINADAS DE LVFACTURACP: "
                + str(lineasEliminadas)
                + " | LINEAS DESASOCIADAS DE TPVLIN: "
                + str(tpvDesasociadas)
            )
        else:
            estado = (
                "NO SE PUDO CONFIRMAR LA CORRECCION"
                + " | PENDIENTES LVFACTURACP: " + str(pendientesLV)
                + " | PENDIENTES TPVLIN: " + str(pendientesTPV)
            )

        logging.info("Factura %s, empresa %s: %s", factura, empresa, estado)
        return correcto, estado

    except:
        if connGestion is not None:
            try:
                connGestion.rollback()
            except:
                pass
        if connTPV is not None:
            try:
                connTPV.rollback()
            except:
                pass
        estado = "ERROR CORRIGIENDO CANJE/BOMBONA - REVISAR LOG"
        logging.error(
            "wasoil.py.- corregirLineasFactura: %s. %s",
            estado,
            traceback.format_exc(),
        )
        return False, estado

    finally:
        if connGestion is not None:
            try:
                connGestion.close()
            except:
                pass
        if connTPV is not None:
            try:
                connTPV.close()
            except:
                pass



'''
Metodo para obtener una fecha en el formato adecuado para consultar en access.
Se le pasa una fecha en str con formato dd/mm/yyyy y devueve la fecha en formato 
mm/dd/yyyy
'''
def transformarFechaAccess(fechaString):
    try:
        if("/" in fechaString):
            arrayFecha = str(fechaString).split(" ")[0].split("/")
        else:
            arrayFecha = str(fechaString).split(" ")[0].split("-")
        return arrayFecha[2] + "/" + arrayFecha[1] + "/" + arrayFecha[0]
    except:
        logging.error("wasoil.py.- transformarFechaAccess: No se han podido obtener los datos, " + traceback.format_exc())
        return None 

'''
Metodo para obtener las bombonas incluidas en facturas.
Solo consulta datos; no realiza ninguna modificacion.
'''
def getBombonas(empresa, fechaConsiderada, anio):
    listaEmpresas = [empresa]

    try:
        strsql = """SELECT [numero], [fecha], [referencia], [concepto], [importe], [ID]
            FROM LVFACTURACP
            WHERE [fecha] > #""" + transformarFechaAccess(fechaConsiderada) + """#
            AND [referencia] IS NOT NULL
            AND (
                Left(UCase(Trim(CStr([referencia]))), 3) = '820'
                OR Left(UCase(Trim(CStr([referencia]))), 6) = 'FNT820'
            )"""

        resultado = ejecutarQueryListaEmpresasTag(listaEmpresas, True, False, str(anio), strsql)

        return resultado

    except:
        logging.error("wasoil.py.- getBombonas: No se han podido obtener las bombonas, " + traceback.format_exc())
        return None

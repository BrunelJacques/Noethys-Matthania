#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-13 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import datetime




def GetLigne(dictDonnees={}) :
    """ Création d'une line ROLMRE """
    ROLMVT = "1"
    ROLCOL = dictDonnees["ROLCOL"]
    ROLNAT = dictDonnees["ROLNAT"]
    ROLEX = dictDonnees["ROLEX"]
    ROLPER = "0"
    ROLDET = "{:0>13}".format(dictDonnees["ROLDET"])
    ROLCLE1 = str(GetCle_modulo11((ROLCOL, ROLNAT, ROLEX[-2:], ROLPER, ROLDET)))
    ROLNUL = "0"
    ROLCLE2 = str(GetCle_modulo23((ROLEX[-2:], ROLPER, "00", ROLDET)))
    ROLREC = dictDonnees["ROLREC"]
    ROLDAT = dictDonnees["date_edition"].strftime("%Y%m%d")
    ROLROL = dictDonnees["ROLROL"]
    ROLEAU = "{:0>12}".format(dictDonnees["ROLEAU"])
    ROLASS = "0" * 12
    ROLTVE = "0" * 12
    ROLTVA = "0" * 12
    ROLTOT = "{:0>12}".format(int(ROLEAU)+int(ROLASS)+int(ROLTVE)+int(ROLTVA))
    ROLNMAJ = "0" * 12
    ROLNOM = "{:<32}".format(dictDonnees["nom"][:32])
    ROLCNM = " " * 32
    ROLDIS  = " " * 32
    ROLADR  = "{:<32}".format(dictDonnees["rue"][:32])
    ROLCVI  = " " * 32
    ROLCP = "{:<5}".format(dictDonnees["code_postal"])
    ROLLOC  = "{:<27}".format(dictDonnees["ville"][:27])
    ROLORU = "{:<32}".format(dictDonnees["objet"][:32])
    ROLOVI = "{:<32}".format(dictDonnees["objet"][32:])
    if dictDonnees["prelevement"] == True :
        ROLPRE = "5"
    else :
        ROLPRE = "2"
    ROLRET = "{:<5}".format(dictDonnees["prelevement_etab"][:5])
    ROLRGU = "{:<5}".format(dictDonnees["prelevement_guichet"][:5])
    ROLRCO = "{:<11}".format(dictDonnees["prelevement_compte"][:11])
    ROLRCL = "{:<2}".format(dictDonnees["prelevement_cle"][:2])
    ROLTIT = "{:<24}".format(dictDonnees["prelevement_titulaire"][:24])
    ROLCLI = " " * 20
    ROLSCH = " " * 10
    ROLART = " " * 20
    ROLMONNAIE = "E"
    ROLHOM  = " "
    ROLDEB  = "00"
    FILLER = " " * 30
    ROLTPR  = " "
    ROLVER = "2"

    listeZones = [
        ROLMVT,
        ROLCOL,
        ROLNAT,
        ROLEX,
        ROLPER,
        ROLDET,
        ROLCLE1,
        ROLNUL,
        ROLCLE2,
        ROLREC,
        ROLDAT,
        ROLROL,
        ROLEAU, 
        ROLASS,
        ROLTVE,
        ROLTVA,
        ROLTOT,
        ROLNMAJ,
        ROLNOM,
        ROLCNM,
        ROLDIS,
        ROLADR,
        ROLCVI,
        ROLCP,
        ROLLOC,
        ROLORU,
        ROLOVI,
        ROLPRE,
        ROLRET,
        ROLRGU,
        ROLRCO,
        ROLRCL,
        ROLTIT,
        ROLCLI,
        ROLSCH,
        ROLART,
        ROLMONNAIE,
        ROLHOM,
        ROLDEB,
        FILLER,
        ROLTPR,
        ROLVER,
        ]
    
    return "".join(listeZones) + "\n"
    
def GetCle_modulo11(elements=[]):
    """ Calcul de la clé Modulo 11 """
##    elements = ("01", "04", "00", "0", "0000000900001")
##    elements = ("39", "01", "13", "0", "0000000000303")
##    elements = ("453267")
    nombre = "".join(elements)[::-1]
    listeCoeff = [2, 3, 4, 5, 6, 7] * (len(nombre) // 6 + 1)
    total = 0
    index = 0
    for chiffre in nombre :
        if chiffre not in "0123456789" : chiffre = "0"
        total += int(chiffre) * listeCoeff[index]
        index += 1
    if total % 11 == 0 : return 0
    cle = 11 - (total % 11)
    if cle > 9 : cle = 1
    return cle

def GetCle_modulo23(elements=[]):
    """ Calcul de la clé Modulo 23 """
##    elements = ("00", "0", "00", "0000000900001") 
    nombre = "".join(elements)
    K = (int(nombre) % 23) + 1
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXY"
    cle = alphabet[K-1]
    return cle
    

if __name__ == "__main__":
    print(GetCle_modulo11())
#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-12 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import decimal


def FloatToDecimal(montant=0.0, plusProche=False):
    """ Transforme un float en decimal """
    if montant == None :
        montant = 0.0
    if type(montant) == str:
        montant = float(montant)
    x = decimal.Decimal(u"%.2f" % montant)
    # Arrondi au centime le plus proche
    if plusProche == True :
        x.quantize(decimal.Decimal('0.01')) # typeArrondi = decimal.ROUND_UP ou decimal.ROUND_DOWN
    return x

def Decimal(montant=0.0, decimales=2, plusProche=True):
    """ Transforme en decimal """
    try:
        montant = float(montant)
    except:
        montant = 0
    if plusProche == False:
        # tronque au nombre de décimales sans arrondi
        montant = int(montant * 10**decimales) / 10**decimales
    fmt = "{:.%df}"%decimales
    x = decimal.Decimal(fmt.format(montant))
    return x


if __name__ == "__main__":
    print(FloatToDecimal(3.554, plusProche=True))

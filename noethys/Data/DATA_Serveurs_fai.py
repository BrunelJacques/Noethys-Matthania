#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

LISTE_SERVEURS_FAI = [
    ( "9 Telecom", "smtp.neuf.fr", None, True, True),
    ( "9ONLINE", "smtp.9online.fr", None, False, False),
    ( "ALICE ADSL", "smtp.aliceadsl.fr", None, False, False),
    ( "AOL", "smtp.neuf.fr", None, False, False),
    ( "Bouygues BBOX", "smtp.bbox.fr", None, False, False),
    ( "Bouygues Télécom", "smtp.bouygtel.fr", None, False, False),
    ( "CEGETEL", "smtp.cegetel.net", None, False, False),
    ( "CLUB INTERNET", "mail.club-internet.fr", None, False, False),
    ( "DARTY BOX", "smtpauth.dbmail.com", None, False, False),
    ( "FREE", "smtp.free.fr", None, False, False),
    ( "FREESURF", "smtp.freesurf.fr", None, False, False),
    ( "GAWAB", "smtp.gawab.com", None, False, False),
    ( "GMAIL", "smtp.gmail.com", 587, True, True),
    ( "HOTMAIL", "smtp.live.com", 25, True, True),
    ( "IFrance", "smtp.ifrance.com", None, False, False),
    ( "LA POSTE", "smtp.laposte.net", None, False, False),
    ( "MAGIC ONLINE", "smtp.magic.fr", None, False, False),
    ( "NERIM", "smtp.nerim.net", None, False, False),
    ( "NOOS", "mail.noos.fr", None, False, False),
    ( "Numéricable", "smtp.numericable.fr", None, False, False),
    ( "ORANGE", "smtp.orange.fr", None, False, False),
    ( "OREKA", "mail.oreka.fr", None, False, False),
    ( "SYMPATICO", "smtp1.sympatico.ca", None, False, False),
    ( "SFR", "smtp.sfr.fr", None, False, False),
    ( "TELE2", "smtp.tele2.fr", None, False, False),
    ( "TISCALI", "smtp.tiscali.fr", None, False, False),
    ( "TISCALI-FREESBEE", "smtp.freesbee.fr", None, False, False),
    ( "WANADOO", "smtp.wanadoo.fr", None, False, False),
    ( "YAHOO", "smtp.mail.yahoo.fr", 465, True, True),
    ] # Nom FAI, serveur smtp, port, connexionAuthentifiee, startTLS

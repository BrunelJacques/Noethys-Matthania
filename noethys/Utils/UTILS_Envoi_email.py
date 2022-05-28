#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import os
import GestionDB
import FonctionsPerso
import re

from Utils import UTILS_Titulaires


def EnvoiEmailFamille(parent=None, IDfamille=None, nomDoc="", categorie="", listeAdresses=[]):
    # Création du PDF
    dictChamps = parent.CreationPDF(nomDoc=nomDoc, afficherDoc=False)
    if dictChamps == False :
        return False
    
    # Recherche adresse famille
    if len(listeAdresses) == 0 :
        listeAdresses = GetAdresseFamille(IDfamille)
        if len(listeAdresses) == 0 :
            return False
    
    # DLG Mailer
    listeDonnees = []
    for adresse in listeAdresses :
        listeDonnees.append({
            "adresse" : adresse, 
            "label" : "Envoi mail",
            "pieces" : [],
            "champs" : dictChamps,
            })
    from Dlg import DLG_Mailer
    dlg = DLG_Mailer.Dialog(parent, categorie=categorie)
    dlg.SetDonnees(listeDonnees, modificationAutorisee=True)
    dlg.ctrl_pieces.listeDonnees.append(nomDoc)
    dlg.ctrl_pieces.MAJ()

    dlg.ChargerModeleDefaut()
    #dlg.ApercuFusion(None)
    dlg.ShowModal() 
    dlg.Destroy()

    # Suppression du PDF temporaire
    os.remove(nomDoc)        


def ValidationEmail(email):
    if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
        return True
    else :
        return False


def GetAdresseExpDefaut():
    """ Retourne les paramètres de l'adresse d'expéditeur par défaut """
    dictAdresse = {}
    # Récupération des données
    DB = GestionDB.DB()        
    req = """SELECT IDadresse, adresse, motdepasse, smtp, port, defaut, connexionssl
    FROM adresses_mail WHERE defaut=1 ORDER BY adresse; """
    DB.ExecuterReq(req,MsgBox="ExecuterReq")
    listeDonnees = DB.ResultatReq()
    DB.Close()
    if len(listeDonnees) == 0 : return None
    IDadresse, adresse, motdepasse, smtp, port, defaut, connexionssl = listeDonnees[0]
    dictAdresse = {"adresse":adresse, "motdepasse":motdepasse, "smtp":smtp, "port":port, "connexionssl":connexionssl}
    return dictAdresse

def GetAdresseFamille(IDfamille=None, choixMultiple=True, muet=False, **args):
    """ Récupère l'adresse email de la famille avec une description"""
    # Récupération de l'adresse mail famille ou choisir des adresses mails de membres de la famille
    DB = GestionDB.DB()
    reqMulti = """
        SELECT rattachements.IDindividu, rattachements.IDcategorie, rattachements.titulaire,
                individus.nom, individus.prenom, individus.mail, individus.travail_mail, familles.adresse_individu
        FROM rattachements 
        LEFT JOIN individus ON individus.IDindividu = rattachements.IDindividu
        LEFT JOIN familles ON familles.IDfamille = rattachements.IDfamille
        WHERE rattachements.IDcategorie IN (1, 2) AND rattachements.IDfamille=%d
        ;""" % IDfamille
    if choixMultiple == True :
        req = reqMulti
    else:
        # on ne sert que l'adresse du correspondant famille
        req = """
        SELECT rattachements.IDindividu, rattachements.IDcategorie, rattachements.titulaire, individus.prenom, 
                    familles.adresse_intitule, individus.mail, individus.travail_mail, familles.adresse_individu
        FROM (familles 
            LEFT JOIN rattachements ON (familles.adresse_individu = rattachements.IDindividu) 
                                        AND (familles.IDfamille = rattachements.IDfamille)) 
            LEFT JOIN individus ON rattachements.IDindividu = individus.IDindividu
        WHERE (familles.IDfamille = %d );""" % IDfamille

    ret = DB.ExecuterReq(req,MsgBox= "UTILS_Envois_email.GetAdresseFamille")
    listeDonnees = DB.ResultatReq()

    okCorresp = False
    # test de l'accès direct réussi en mono adresse
    if choixMultiple == False:
        if len(listeDonnees) == 1:
            if (listeDonnees[0][4] and  len(listeDonnees[0][4]) > 0): okCorresp = True
            if (listeDonnees[0][5] and  len(listeDonnees[0][5]) > 0): okCorresp = True
        # Le correspondant n'ayant pas d'adresse on élargit le champ
        if not okCorresp:
            if muet == False :
                mess = "Le correspondant de la famille de %s ne dispose pas d'adresse mail"%listeDonnees[0][-1]
                mess += "\nOn élargit le choix aux autres membres de la famille !"
                dlg = wx.MessageDialog(None, mess, "Erreur", wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
            ret = DB.ExecuterReq(reqMulti,MsgBox= "UTILS_Envois_email.GetAdresseFamille2")
            listeDonnees = DB.ResultatReq()
    DB.Close()
    listeAdresses = []
    titre = ""
    designation = str(IDfamille)
    for IDindividu,  IDcategorie, titulaire, nom, prenom, mailPerso, mailTravail, IDcorresp in listeDonnees :
        if IDcategorie ==  1: titre = "Resp"
        elif IDcategorie == 2: titre = "Enf"

        if titulaire == 1: titre = "Tit"
        if IDcorresp == IDindividu:
            titre = "Cor"
            designation = prenom

        if mailPerso != None and mailPerso != "" :
            listeAdresses.append((_("%s: %s (mel perso %s)") % (titre, mailPerso, prenom), mailPerso))
            # si pas de choix multiple une seule adresse suffit
            if choixMultiple  == False:
                break
        if mailTravail != None and mailTravail != "" :
            listeAdresses.append((_("%s: %s: (mel pro %s)") % (titre, mailTravail, prenom), mailTravail))
            # si pas de choix multiple une seule adresse suffit
            if choixMultiple  == False:
                break

    if len(listeAdresses) == 0 :
        if muet == False :
            dlg = wx.MessageDialog(None, "Les membres de la famille de %s ne dispose d'adresse mail !"%designation, "Erreur", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
        return []
    elif len(listeAdresses) == 1 :
        lstMails = [listeAdresses[0][1],]
    else:
        # préparation du choix
        listeLabels = []
        lstMails = []
        for label, adresse in listeAdresses :
            listeLabels.append(label)

        if choixMultiple == True :
            dlg = wx.MultiChoiceDialog(None, _("%d adresses internet sont disponibles pour la famille de %s.\nSélectionnez celles que vous souhaitez utiliser puis cliquez sur le bouton 'Ok' :") % (len(listeAdresses), designation), _("Choix d''adresses Emails"), listeLabels)
        else :
            dlg = wx.SingleChoiceDialog(None, _("%d adresses internet sont disponibles pour la famille de %s.\nSélectionnez celle que vous souhaitez utiliser puis cliquez sur le bouton 'Ok' :") % (len(listeAdresses), designation), _("Choix d'une adresse Email"), listeLabels)
        dlg.SetSize((550, -1))
        dlg.CenterOnScreen()
        if dlg.ShowModal() == wx.ID_OK :
            if choixMultiple == True :
                selections = dlg.GetSelections()
            else :
                selections = dlg.GetSelection()
            dlg.Destroy()
            if len(selections) == 0 and not muet:
                dlg = wx.MessageDialog(None, _("Vous n'avez sélectionné aucune adresse mail !"), "Erreur", wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return []
            for index in selections :
               lstMails.append(listeAdresses[index][1])
        else:
            dlg.Destroy()
            return []

    if choixMultiple == True :
        return lstMails
    else :
        return lstMails[0]

def Envoi_mail(adresseExpediteur="", listeDestinataires=[], listeDestinatairesCCI=[], sujetMail="", texteMail="", listeFichiersJoints=[], serveur="localhost", port=None, ssl=False, listeImages=[], motdepasse=None, accuseReception=False):
    """ Envoi d'un mail avec pièce jointe """
    import smtplib
    import poplib
    from email.MIMEMultipart import MIMEMultipart
    from email.MIMEBase import MIMEBase
    from email.MIMEText import MIMEText
    from email.MIMEImage import MIMEImage
    from email.MIMEAudio import MIMEAudio
    from email.Utils import COMMASPACE, formatdate
    from email import Encoders
    import mimetypes
    
    assert type(listeDestinataires)==list
    assert type(listeFichiersJoints)==list
    
    # Corrige le pb des images embarquées
    index = 0
    for img in listeImages :
        img = img.replace("\\", "/")
        img = img.replace(":", "%3a")
        texteMail = texteMail.replace(_("file:/%s") % img, "cid:image%d" % index)
        index += 1
    
    # Création du message
    msg = MIMEMultipart()
    msg['From'] = adresseExpediteur
    msg['To'] = ";".join(listeDestinataires)
    msg['Bcc'] = ";".join(listeDestinatairesCCI)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = sujetMail
    
    if accuseReception == True :
        msg['Disposition-Notification-To'] = adresseExpediteur
    txt = texteMail.encode('utf-8')
    tab = "\t"
    htab = "<dd>"
    txt = txt.replace(tab,htab)

    msg.attach( MIMEText(txt, 'html', 'utf-8') )
    
    # Attache des pièces jointes
    for fichier in listeFichiersJoints:
        """Guess the content type based on the file's extension. Encoding
        will be ignored, altough we should check for simple things like
        gzip'd or compressed files."""
        ctype, encoding = mimetypes.guess_type(fichier)
        if ctype is None or encoding is not None:
            # No guess could be made, or the file is encoded (compresses), so
            # use a generic bag-of-bits type.
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)
        if maintype == 'text':
            fp = open(fichier)
            # Note : we should handle calculating the charset
            part = MIMEText(fp.read(), _subtype=subtype)
            fp.close()
        elif maintype == 'image':
            fp = open(fichier, 'rb')
            part = MIMEImage(fp.read(), _subtype=subtype)
            fp.close()
        elif maintype == 'audio':
            fp = open(fichier, 'rb')
            part = MIMEAudio(fp.read(), _subtype=subtype)
            fp.close()
        else:
            fp = open(fichier, 'rb')
            part = MIMEBase(maintype, subtype)
            part.set_payload(fp.read())
            fp.close()
            # Encode the payload using Base64
            Encoders.encode_base64(part)
        # Set the filename parameter
        nomFichier= os.path.basename(fichier)
        if type(nomFichier) == str :
            nomFichier = FonctionsPerso.Supprime_accent(nomFichier)
        part.add_header('Content-Disposition', 'attachment', filename=nomFichier)
        msg.attach(part)
    
    # Images incluses
    index = 0
    for img in listeImages :
        fp = open(img, 'rb')
        msgImage = MIMEImage(fp.read())
        fp.close()
        msgImage.add_header('Content-ID', '<image%d>' % index)
        msgImage.add_header('Content-Disposition', 'inline', filename=img)
        msg.attach(msgImage)
        index += 1
    
##    pop = poplib.POP3(serveur)
##    print pop.getwelcome()
##    pop.user(adresseExpediteur)
##    pop.pass_(motdepasse)
##    print pop.stat()
##    print pop.list()
    
    if ssl == False :
        # Envoi standard
        smtp = smtplib.SMTP(serveur, timeout=150)
    else:
        # Si identification SSL nécessaire :
        smtp = smtplib.SMTP(serveur, port, timeout=150)
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(adresseExpediteur.encode('utf-8'), motdepasse.encode('utf-8'))
    
    smtp.sendmail(adresseExpediteur, listeDestinataires + listeDestinatairesCCI, msg.as_string())
    smtp.close()
    
    return True



# TEST d'envoi d'emails
if __name__ == "__main__":
    app = wx.App(0)


    """print Envoi_mail( 
        adresseExpediteur="XXX", 
        listeDestinataires=["XXX",], 
        listeDestinatairesCCI=[], 
        sujetMail=_("Sujet du Mail"), 
        texteMail=_("Texte du Mail"), 
        listeFichiersJoints=[], 
        serveur="XXX", 
        port=465, 
        ssl=True, 
        listeImages=[],
        motdepasse="XXX",
        accuseReception = False,
        )"""
    ret = GetAdresseFamille(1861,choixMultiple=True,muet = False)
    print(ret)
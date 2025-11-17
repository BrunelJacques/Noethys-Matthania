#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys 2022, Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------
import wx
import os
import sys
import time
import GestionDB
import FonctionsPerso
import re
import traceback
import base64
from Utils import UTILS_Html2text
from Utils import UTILS_Parametres
from Utils import UTILS_Titulaires
from Dlg import DLG_Messagebox
from Dlg import DLG_Mailer

import smtplib
import six
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.header import Header
from email.utils import formatdate
from email import encoders
import mimetypes

from Outils import mail

def EnvoiEmailFamille(parent=None, IDfamille=None, nomDoc="", categorie="", listeAdresses=[],
                      visible=True, log=None, CreationPDF=None, IDmodel=None):
    # Création du PDF
    if CreationPDF == None and hasattr(parent,"CreationPDF"):
        CreationPDF = parent.CreationPDF
    if not CreationPDF:
        mess = "Lancement CreationPDF non trouvé, pb logique"
        raise Exception(mess)

    resultat = CreationPDF(nomDoc=nomDoc, afficherDoc=False,repertoireTemp=True)
    if not resultat:
        return False

    (dictChamps, dictPieces) = resultat

    if dictChamps == False :
        return False
    liste_pieces = []

    for key,nomDoc in dictPieces.items():
        liste_pieces.append(nomDoc)

    # Recherche adresse famille
    if len(listeAdresses) == 0 :
        listeAdresses = GetAdresseFamille(IDfamille)
        if listeAdresses == False or len(listeAdresses) == 0 :
            return False
    
    # DLG Mailer
    ldDonnees = []
    for adresse in listeAdresses :
        ldDonnees.append({
            "adresse" : adresse, 
            "pieces" : [], # une seule famille, toutes les adresses auront toutes les pièces
            "champs" : dictChamps[IDfamille],
            })
    dlg = DLG_Mailer.Dialog(parent, categorie=categorie, afficher_confirmation_envoi=visible)

    # envoi des adresses pouvant contenir des pieces dans 'champs'
    dlg.SetDonnees(ldDonnees, modificationAutorisee=True)

    # envoi des pièces jointes communes à toutes les adresses
    dlg.SetPiecesJointes(liste_pieces)
    if IDmodel == None :
        dlg.ChargerModeleDefaut()
    else :
        dlg.ChargerModele(IDmodel)

    if visible == True :
        # Fenêtre visible
        dlg.ShowModal()
    else :
        # Fenêtre cachée
        dlg.OnBoutonEnvoyer(None)

    if len(dlg.listeSucces) > 0 :
        resultat = True
        if log : log.EcritLog("L'Email a été envoyé avec succès.")
    else :
        resultat = False
        if log : log.EcritLog("L'email n'a pas été envoyé.")

    dlg.Destroy()

    # Suppression du PDF temporaire
    if nomDoc != False :
        try :
            os.remove(nomDoc)
        except :
            pass

    return resultat

def ValidationEmail(email):
    if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
        return True
    else :
        return False

def GetAdresseExpDefaut():
    """ Retourne les paramètres de l'adresse d'expéditeur par défaut """
    return GetAdresseExp(IDadresse=None)

def GetAdresseExp(IDadresse=None):
    """ Si IDadresse = None, retourne l'adresse par défaut"""
    if IDadresse == None :
        condition = "defaut=1"
    else :
        condition = "IDadresse=%d" % IDadresse
    # Récupération des données
    DB = GestionDB.DB()        
    req = """SELECT IDadresse, moteur, adresse, nom_adresse, motdepasse, smtp, port, defaut, connexionAuthentifiee, startTLS, utilisateur, parametres
    FROM adresses_mail WHERE %s ORDER BY adresse;""" % condition
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    DB.Close()
    if len(listeDonnees) == 0 : return None
    IDadresse, moteur, adresse, nom_adresse, motdepasse, smtp, port, defaut, auth, startTLS, utilisateur, parametres = listeDonnees[0]
    dictAdresse = {"adresse":adresse, "moteur": moteur, "nom_adresse":nom_adresse, "motdepasse":motdepasse,
                   "smtp":smtp, "port":port, "auth" : auth, "startTLS":startTLS, "utilisateur" : utilisateur, "parametres": parametres}
    return dictAdresse

def GetAdresseFamille(IDfamille=None, choixMultiple=True, muet=False, nomTitulaires=None):
    """ Récupère l'adresse email de la famille """
    # Récupération du nom de la famille
    if nomTitulaires == None :
        dictTitulaires = UTILS_Titulaires.GetTitulaires([IDfamille,])
        if IDfamille in dictTitulaires:
            nomTitulaires = dictTitulaires[IDfamille]["titulairesSansCivilite"]
        else :
            nomTitulaires = "Famille inconnue"
    # Récupération des adresses mails de chaque membre de la famille
    DB = GestionDB.DB()
    req = """
    SELECT rattachements.IDindividu, IDcategorie,
    individus.nom, individus.prenom, individus.mail, individus.travail_mail
    FROM rattachements 
    LEFT JOIN individus ON individus.IDindividu = rattachements.IDindividu
    WHERE IDcategorie=1 AND titulaire=1 AND IDfamille=%d
    ;""" % IDfamille
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    DB.Close()
    listeAdresses = []
    listeTemp = []
    for IDindividu,  IDcategorie, nom, prenom, mailPerso, mailTravail in listeDonnees :
        if mailPerso != None and mailPerso != "" and mailPerso not in listeTemp :
            listeAdresses.append(("%s (Adresse perso de %s)" % (mailPerso, prenom), mailPerso))
            listeTemp.append(mailPerso)
        if mailTravail != None and mailTravail != "" and mailTravail not in listeTemp :
            listeAdresses.append(("%s (Adresse pro de %s)" %(mailTravail, prenom), mailTravail))
            listeTemp.append(mailTravail)
    if len(listeAdresses) == 0 :
        if muet == False :
            dlg = wx.MessageDialog(None, "Aucun titulaire de la famille de %s ne dispose d'adresse mail !" % nomTitulaires, "Erreur", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
        return []
    elif len(listeAdresses) == 1 :
        listeMails = [listeAdresses[0][1],]
    else:
        listeLabels = []
        listeMails = []
        for label, adresse in listeAdresses :
            listeLabels.append(label)
        mess = "%d adresses internet sont disponibles pour la famille de %s.\nSélectionnez celles que vous souhaitez utiliser puis cliquez sur le bouton 'Ok' :" % (len(listeAdresses),
                                                                                                                                                                    nomTitulaires)
        if choixMultiple == True :
            dlg = wx.MultiChoiceDialog(None,
                                       mess,
                                       "Choix d'adresses Emails", listeLabels)
        else :
            dlg = wx.SingleChoiceDialog(None,
                                        mess,
                                        "Choix d'une adresse Email", listeLabels)
        dlg.SetSize((450, -1))
        dlg.CenterOnScreen()
        if dlg.ShowModal() == wx.ID_OK :
            if choixMultiple == True :
                selections = dlg.GetSelections()
            else :
                selections = [dlg.GetSelection(),]
            dlg.Destroy()
            if len(selections) == 0 :
                dlg = wx.MessageDialog(None, "Vous n'avez sélectionné aucune adresse mail !", "Erreur", wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return []
            for index in selections :
                listeMails.append(listeAdresses[index][1])
        else:
            dlg.Destroy()
            return False

    if choixMultiple == True :
        return listeMails
    else :
        return listeMails[0]

# -------------------------------------------------------------------------------------------------------

def GetAdressesFamilles(liste_IDfamille=[]):
    dictTitulaires = UTILS_Titulaires.GetTitulaires()

    # Sélection des adresses mail
    liste_actions = [
        ("all", "Toutes les adresses de la famille"),
        ("one_perso_first", "Une seule adresse par famille (perso en priorité)"),
        ("one_pro_first", "Une seule adresse par famille (pro en priorité)"),
        ("all_perso", "Toutes les adresses personnelles de la famille"),
        ("all_pro", "Toutes les adresses professionnelles de la famille"),
        ("all_perso_first", "Toutes les adresses personnelles de la famille en priorité"),
        ("all_pro_first", "Toutes les adresses professionnelles de la famille en priorité"),
        ("selection", "Je veux sélectionner les adresses pour chaque famille"),
        ]
    dlg = wx.SingleChoiceDialog(None, u"Quelles adresses internet souhaitez-vous utiliser ?", u"Sélection des adresses", [label for code, label in liste_actions], wx.CHOICEDLG_STYLE)
    dlg.SetSize((350, 240))
    dlg.CenterOnScreen()
    if dlg.ShowModal() == wx.ID_OK:
        code_action = liste_actions[dlg.GetSelection()][0]
        dlg.Destroy()
    else:
        dlg.Destroy()
        return False

    # Importation des toutes les adresses existantes
    DB = GestionDB.DB()
    req = """
    SELECT IDfamille, rattachements.IDindividu,
    individus.nom, individus.prenom, individus.mail, individus.travail_mail
    FROM rattachements 
    LEFT JOIN individus ON individus.IDindividu = rattachements.IDindividu
    WHERE IDcategorie=1 AND titulaire=1
    ;"""
    DB.ExecuterReq(req)
    liste_adresses = DB.ResultatReq()
    DB.Close()
    dict_individus = {}
    for IDfamille, IDindividu, nom, prenom, mail_perso, mail_pro in liste_adresses:
        if IDfamille not in dict_individus:
            dict_individus[IDfamille] = []
        dict_individus[IDfamille].append({"IDindividu": IDindividu, "nom": nom, "prenom": prenom, "mail_perso": mail_perso, "mail_pro": mail_pro})

    # Création du dict de résultats
    dict_adresses = {}
    listeFamillesAvecAdresses = []
    liste_anomalies = []

    def Ajouter_adresse(IDfamille, adresse):
        if adresse not in (None, ""):
            if IDfamille not in dict_adresses:
                dict_adresses[IDfamille] = []
            if adresse not in dict_adresses[IDfamille]:
                dict_adresses[IDfamille].append(adresse)
                if IDfamille not in listeFamillesAvecAdresses:
                    listeFamillesAvecAdresses.append(IDfamille)

    # Toutes les adresses
    if code_action == "all":
        for IDfamille, liste_individus in dict_individus.items():
            for dict_individu in liste_individus:
                Ajouter_adresse(IDfamille, dict_individu["mail_perso"])
                Ajouter_adresse(IDfamille, dict_individu["mail_pro"])

    # Toutes les adresses perso
    if code_action == "all_perso":
        for IDfamille, liste_individus in dict_individus.items():
            for dict_individu in liste_individus:
                Ajouter_adresse(IDfamille, dict_individu["mail_perso"])

    # Toutes les adresses pro
    if code_action == "all_pro":
        for IDfamille, liste_individus in dict_individus.items():
            for dict_individu in liste_individus:
                Ajouter_adresse(IDfamille, dict_individu["mail_pro"])

    # L'adresse personnelle en priorité
    if code_action == "all_perso_first":
        for IDfamille, liste_individus in dict_individus.items():
            for dict_individu in liste_individus:
                if dict_individu["mail_perso"] not in ("", None):
                    Ajouter_adresse(IDfamille, dict_individu["mail_perso"])
                else:
                    Ajouter_adresse(IDfamille, dict_individu["mail_pro"])

    # L'adresse professionnelle en priorité
    if code_action == "all_pro_first":
        for IDfamille, liste_individus in dict_individus.items():
            for dict_individu in liste_individus:
                if dict_individu["mail_pro"] not in ("", None):
                    Ajouter_adresse(IDfamille, dict_individu["mail_pro"])
                else:
                    Ajouter_adresse(IDfamille, dict_individu["mail_perso"])

    # Une adresse par famille (perso en priorité)
    if code_action == "one_perso_first":
        for IDfamille, liste_individus in dict_individus.items():
            liste_temp = []
            for dict_individu in liste_individus:
                if dict_individu["mail_perso"] not in ("", None): liste_temp.append((1, dict_individu["mail_perso"]))
                if dict_individu["mail_pro"] not in ("", None): liste_temp.append((2, dict_individu["mail_pro"]))
            liste_temp.sort()
            if len(liste_temp) > 0:
                Ajouter_adresse(IDfamille, liste_temp[0][1])

    # Une adresse par famille (pro en priorité)
    if code_action == "one_pro_first":
        for IDfamille, liste_individus in dict_individus.items():
            liste_temp = []
            for dict_individu in liste_individus:
                if dict_individu["mail_perso"] not in ("", None): liste_temp.append((2, dict_individu["mail_perso"]))
                if dict_individu["mail_pro"] not in ("", None): liste_temp.append((1, dict_individu["mail_pro"]))
            liste_temp.sort()
            if len(liste_temp) > 0:
                Ajouter_adresse(IDfamille, liste_temp[0][1])

    # Je veux sélectionner les adresses
    if code_action == "selection":
        for IDfamille in liste_IDfamille :
            nom_titulaires = dictTitulaires[IDfamille]["titulairesSansCivilite"]
            adresses = GetAdresseFamille(IDfamille, choixMultiple=True, muet=True, nomTitulaires=nom_titulaires)
            if adresses == False:
                return False
            for adresse in adresses:
                Ajouter_adresse(IDfamille, adresse)

    # Annonce les anomalies trouvées
    for IDfamille in liste_IDfamille:
        if IDfamille not in listeFamillesAvecAdresses:
            if IDfamille in dictTitulaires:
                nom_titulaires = dictTitulaires[IDfamille]["titulairesSansCivilite"]
            else:
                nom_titulaires = "Titulaires inconnus"
            liste_anomalies.append(nom_titulaires)

    if len(liste_anomalies) > 0 and len(liste_anomalies) != len(liste_IDfamille):
        intro = "%d des familles sélectionnées n'ont pas d'adresse Email :" % len(liste_anomalies)
        conclusion = "Souhaitez-vous quand même continuer avec les autres destinataires ?"
        detail = u"\n".join([nom for nom in liste_anomalies])
        dlgErreur = DLG_Messagebox.Dialog(None, titre="Avertissement", introduction=intro, detail=detail, conclusion=conclusion, icone=wx.ICON_EXCLAMATION, boutons=["Oui", "Non", "Annuler"])
        reponse = dlgErreur.ShowModal()
        dlgErreur.Destroy()
        if reponse != 0:
            return False

    # Dernière vérification avant transfert
    if len(dict_adresses) == 0 :
        dlg = wx.MessageDialog(None, "Il ne reste finalement aucune adresse internet !", "Erreur", wx.OK | wx.ICON_EXCLAMATION)
        dlg.ShowModal()
        dlg.Destroy()
        return False

    # Renvoie le dict des adresses
    return dict_adresses

# -------------------------------------------------------------------------------------------------------


class Message():
    def __init__(self, destinataires=[], sujet="", texte_html="", fichiers=[], images=[], champs={}):
        self.destinataires = destinataires
        self.sujet = sujet
        self.fichiers = fichiers
        self.images = images
        self.texte_html = texte_html
        self.champs = champs

        # Corrige le pb des images embarquées
        index = 0
        for img in images:
            img = img.replace(u"\\", u"/")
            img = img.replace(u":", u"%3a")
            self.texte_html = self.texte_html.replace(u"file:/%s" % img, u"cid:image%d" % index)
            index += 1

        # Conversion du html en texte plain
        self.texte_plain = UTILS_Html2text.html2text(self.texte_html)

    def AttacheImagesIncluses(self, email=None):
        index = 0
        for img in self.images:
            fp = open(img, 'rb')
            msgImage = MIMEImage(fp.read())
            fp.close()
            msgImage.add_header('Content-ID', '<image%d>' % index)
            msgImage.add_header('Content-Disposition', 'inline', filename=img)
            email.attach(msgImage)
            index += 1

    def AttacheFichiersJoints(self, email=None):
        for fichier in self.fichiers:
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
            else:
                fp = open(fichier, 'rb')
                part = MIMEBase(maintype, subtype)
                part.set_payload(fp.read())
                fp.close()
                # Encode the payload using Base64
                encoders.encode_base64(part)
            # Set the filename parameter
            nomFichier = os.path.basename(fichier)
            if type(nomFichier) == six.text_type:
                nomFichier = FonctionsPerso.Supprime_accent(nomFichier)
            # changement cosmetique pour ajouter les guillements autour du filename
            part.add_header('Content-Disposition', "attachment; filename=\"%s\"" % nomFichier)
            email.attach(part)

    def GetLabelDestinataires(self):
        return ";".join(self.destinataires)

def Messagerie(backend='smtp', **kwds):
    # Ancien moteur SMTP
    if backend == "smtp_obsolete":
        klass = SmtpV1(**kwds)
    # Nouveau moteur SMTP
    elif backend == "smtp":
        klass = SmtpV2(**kwds)
    # Mailjet
    elif backend == "mailjet":
        klass = Mailjet(**kwds)
    else:
        klass = SmtpV2(**kwds)
    return klass

class Base_messagerie():
    def __init__(self, hote=None, port=None, utilisateur=None, motdepasse=None, email_exp=None, nom_exp=None, timeout=None, use_tls=False, fail_silently=False, parametres=None):
        self.hote = hote
        self.port = port
        self.utilisateur = utilisateur
        self.motdepasse = motdepasse
        self.email_exp = email_exp
        self.nom_exp = nom_exp
        self.timeout = timeout
        self.use_tls = use_tls
        self.fail_silently = fail_silently
        self.parametres = parametres

        if self.utilisateur == "" or self.utilisateur == None:
            self.utilisateur = self.email_exp
        if self.motdepasse == "" : self.motdepasse = None

        # Timeout
        timeout = UTILS_Parametres.Parametres(mode="get", categorie="email",
                                              nom="timeout", valeur=None)
        if timeout not in ("", None,"None"):
            self.timeout = int(timeout)

        # Préparation de l'adresse d'expédition
        if self.nom_exp not in ("", None):
            self.from_email = u"%s <%s>" % (self.nom_exp, self.email_exp)
        else :
            self.from_email = self.email_exp

        # Formatage des paramètres
        self.dict_parametres = {}
        if parametres not in ("", None):
            liste_parametres = parametres.split("##")
            for texte in liste_parametres:
                nom, valeur = texte.split("==")
                self.dict_parametres[nom] = valeur

    def Connecter(self):
        pass

    def Envoyer(self, message=None):
        pass

    def Fermer(self):
        pass

class SmtpV1(Base_messagerie):
    # avec tls forcé, déclaration smtp_obsolete
    def __init__(self, **kwds):
        Base_messagerie.__init__(self, **kwds)

    def Connecter(self):
        try :
            if self.utilisateur == None and self.motdepasse == None:
                # Envoi standard
                self.connection = smtplib.SMTP(self.hote, timeout=self.timeout)
            else:
                # Si identification SSL nécessaire :
                self.connection = smtplib.SMTP(self.hote, self.port, timeout=self.timeout)
                self.connection.ehlo()
                self.connection.starttls()
                self.connection.ehlo()
                self.connection.login(self.utilisateur, self.motdepasse)
        except smtplib.SMTPException as err:
            if not self.fail_silently:
                raise

    def Envoyer(self, message=None):
        # Création du message
        email = MIMEMultipart('alternative')
        # msg['Message-ID'] = make_msgid()

        # if accuseReception == True:
        #     msg['Disposition-Notification-To'] = adresseExpediteur

        email.attach(MIMEText(message.texte_plain.encode('utf-8'), 'plain', 'utf-8'))
        email.attach(MIMEText(message.texte_html.encode('utf-8'), 'html', 'utf-8'))

        tmpmsg = email
        email = MIMEMultipart('mixed')
        email.attach(tmpmsg)

        # Ajout des headers Ã  ce Multipart
        if self.nom_exp in ("", None):
            email['From'] = self.email_exp
        else:
            sender = Header(self.nom_exp, "utf-8")
            sender.append(self.email_exp, "ascii")
            email['From'] = sender  # formataddr((nomadresseExpediteur, adresseExpediteur))
        email['To'] = ";".join(message.destinataires)
        email['Date'] = formatdate(localtime=True)
        email['Subject'] = message.sujet

        message.AttacheImagesIncluses(email)
        message.AttacheFichiersJoints(email)

        try:
            self.connection.sendmail(self.email_exp, message.destinataires, email.as_string())
        except smtplib.SMTPException:
            if not self.fail_silently:
                raise
            return False
        return True

    def Fermer(self):
        self.connection.close()

    def Envoyer_lot(self, messages=[], dlg_progress=None, afficher_confirmation_envoi=True):
        """ Envoi des messages par lot """
        # Envoi des mails
        index = 1
        listeAnomalies = []
        listeSucces = []
        ne_pas_signaler_erreurs = False
        for message in messages:
            while True:
                adresse = message.GetLabelDestinataires()
                try:
                    labelAdresse = adresse.decode('cp1252')
                except:
                    labelAdresse = adresse
                label = "Envoi %d/%d : %s..." % (index, len(messages), labelAdresse)

                # Si la dlg_progress a été fermée, on la réouvre
                if dlg_progress == None:
                    dlg_progress = wx.ProgressDialog("Envoi des mails", "", maximum=len(messages) + 1, parent=None)
                    dlg_progress.SetSize((450, 140))
                    dlg_progress.CenterOnScreen()
                dlg_progress.Update(index, label)

                # Envoi
                erreur = None
                try:
                    self.Envoyer(message)
                    listeSucces.append(message)
                except smtplib.SMTPServerDisconnected:
                    erreur = "deconnexion"
                except Exception as err:
                    erreur = err

                # Tentative de reconnexion du serveur de messagerie puis renvoi du mail
                if erreur == "deconnexion":
                    print("Reconnexion au serveur de messagerie...")
                    try:
                        self.Connecter()
                        self.Envoyer(message)
                        listeSucces.append(message)
                        erreur = None
                    except Exception as err:
                        traceback.print_exc(file=sys.stdout)
                        erreur = err

                if erreur != None:
                    err = six.text_type(erreur)
                    listeAnomalies.append((message, err))
                    print(("Erreur dans l'envoi d'un mail : %s...", err))

                    if ne_pas_signaler_erreurs == False:

                        # Fermeture de la dlg_progress
                        dlg_progress.Destroy()
                        dlg_progress = None

                        # Affichage de l'erreur
                        intro = "L'erreur suivante a été détectée :"
                        detail = err
                        if index <= len(messages) - 1:
                            conclusion = "Souhaitez-vous quand même continuer l'envoi des autres emails ?"
                            boutons = ["Réessayer", "Continuer",
                                       "Continuer et ne plus signaler les erreurs", "Arrêter"]
                        else:
                            conclusion = None
                            boutons = ["Réessayer", "Arrêter", ]
                        dlgErreur = DLG_Messagebox.Dialog(None, titre="Erreur", introduction=intro, detail=detail,
                                                          conclusion=conclusion, icone=wx.ICON_ERROR, boutons=boutons)
                        reponse = dlgErreur.ShowModal()
                        dlgErreur.Destroy()
                        if reponse == 0:
                            continue
                        if reponse == 2:
                            ne_pas_signaler_erreurs = True
                        if reponse == 3:
                            return listeSucces
                break

            if len(messages) > 1:
                time.sleep(1)
            index += 1

        # Fin de la gauge
        if dlg_progress != None:
            dlg_progress.Update(index, "Fin de l'envoi.")
            dlg_progress.Destroy()

        # Si tous les Emails envoyés avec succès
        if len(listeAnomalies) == 0 and afficher_confirmation_envoi == True:
            if len(listeSucces) == 1:
                message = "L'Email a été envoyé avec succès !"
            else:
                message = "Les %d Emails ont été envoyés avec succès !" % len(listeSucces)
            dlg = wx.MessageDialog(None, message, "Fin de l'envoi", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()

        # Si Anomalies
        if len(listeAnomalies) > 0 and len(messages) > 1:
            if len(listeSucces) > 0:
                intro = "%d Email(s) ont été envoyés avec succès mais les %d envois suivants ont échoué :" % (
                len(listeSucces), len(listeAnomalies))
            else:
                intro = "Tous les envois ont lamentablement échoué :"
            lignes = []
            for message, erreur in listeAnomalies:
                adresse = message.GetLabelDestinataires()
                try:
                    lignes.append(u"- %s : %s" % (adresse.decode('cp1252'), erreur))
                except:
                    lignes.append(u"- %s : %s" % (adresse, erreur))
            dlg = DLG_Messagebox.Dialog(None, titre="Compte-rendu de l'envoi", introduction=intro,
                                        detail="\n".join(lignes), icone=wx.ICON_INFORMATION, boutons=["Ok", ])
            dlg.ShowModal()
            dlg.Destroy()

        return listeSucces

class SmtpV2(Base_messagerie):
    def __init__(self, **kwds):
        Base_messagerie.__init__(self, **kwds)

    def Connecter(self):
        try :
            self.connection = mail.get_connection(backend='Outils.mail.smtp.EmailBackend', fail_silently=self.fail_silently,
                                             host=self.hote, port=self.port, username=self.utilisateur, password=self.motdepasse,
                                             use_tls=self.use_tls, use_ssl=False, timeout=self.timeout, ssl_keyfile=None, ssl_certfile=None)
            self.connection.open()
        except smtplib.SMTPException:
            if not self.fail_silently:
                raise

    def Envoyer(self, message=None):
        headers = {}

        # Accusé de réception
        notification = self.dict_parametres.get("notification", 0)
        if notification == "1":
            headers["Return-Receipt-To"] = self.from_email
            headers["Disposition-Notification-To"] = self.from_email

        email = mail.EmailMultiAlternatives(
            subject=message.sujet,
            body=message.texte_plain,
            from_email=self.from_email,
            to=message.destinataires,
            connection=self.connection,
            headers=headers,
        )

        email.attach_alternative(message.texte_html, "text/html")

        message.AttacheImagesIncluses(email)
        message.AttacheFichiersJoints(email)

        resultat = email.send()
        return resultat

    def Fermer(self):
        self.connection.close()

    def Envoyer_lot(self, messages=[], dlg_progress=None, afficher_confirmation_envoi=True):
        """ Envoi des messages par lot """
        # Envoi des mails
        index = 1
        listeAnomalies = []
        listeSucces = []
        ne_pas_signaler_erreurs = False
        for message in messages:
            while True:
                adresse = message.GetLabelDestinataires()
                try:
                    labelAdresse = adresse.decode('cp1252')
                except:
                    labelAdresse = adresse
                label = "Envoi %d/%d : %s..." % (index, len(messages), labelAdresse)

                # Si la dlg_progress a été fermée, on la réouvre
                if dlg_progress == None:
                    dlg_progress = wx.ProgressDialog("Envoi des mails", "", maximum=len(messages) + 1, parent=None)
                    dlg_progress.SetSize((450, 140))
                    dlg_progress.CenterOnScreen()
                dlg_progress.Update(index, label)

                # Envoi
                erreur = None
                try:
                    self.Envoyer(message)
                    listeSucces.append(message)
                except smtplib.SMTPServerDisconnected:
                    erreur = "deconnexion"
                except Exception as err:
                    erreur = err

                # Tentative de reconnexion du serveur de messagerie puis renvoi du mail
                if erreur == "deconnexion":
                    print("Reconnexion au serveur de messagerie...")
                    try:
                        self.Connecter()
                        self.Envoyer(message)
                        listeSucces.append(message)
                        erreur = None
                    except Exception as err:
                        traceback.print_exc(file=sys.stdout)
                        erreur = err

                if erreur != None:
                    err = six.text_type(erreur)
                    listeAnomalies.append((message, err))
                    print(("Erreur dans l'envoi d'un mail : %s...", err))

                    if ne_pas_signaler_erreurs == False:

                        # Fermeture de la dlg_progress
                        dlg_progress.Destroy()
                        dlg_progress = None

                        # Affichage de l'erreur
                        intro = "L'erreur suivante a été détectée :"
                        detail = err
                        if index <= len(messages) - 1:
                            conclusion = "Souhaitez-vous quand même continuer l'envoi des autres emails ?"
                            boutons = ["Réessayer", "Continuer",
                                       "Continuer et ne plus signaler les erreurs",
                                       "Arrêter"]
                        else:
                            conclusion = None
                            boutons = ["Réessayer", "Arrêter", ]
                        dlgErreur = DLG_Messagebox.Dialog(None, titre="Erreur", introduction=intro, detail=detail,
                                                          conclusion=conclusion, icone=wx.ICON_ERROR, boutons=boutons)
                        reponse = dlgErreur.ShowModal()
                        dlgErreur.Destroy()
                        if reponse == 0:
                            continue
                        if reponse == 2:
                            ne_pas_signaler_erreurs = True
                        if reponse == 3:
                            return listeSucces
                break

            if len(messages) > 1:
                time.sleep(1)
            index += 1

        # Fin de la gauge
        if dlg_progress != None:
            dlg_progress.Update(index, "Fin de l'envoi.")
            dlg_progress.Destroy()

        # Si tous les Emails envoyés avec succès
        if len(listeAnomalies) == 0 and afficher_confirmation_envoi == True:
            if len(listeSucces) == 1:
                message = "L'Email a été envoyé avec succès !"
            else:
                message = "Les %d Emails ont été envoyés avec succès !"% len(listeSucces)
            dlg = wx.MessageDialog(None, message, "Fin de l'envoi", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()

        # Si Anomalies
        if len(listeAnomalies) > 0 and len(messages) > 1:
            if len(listeSucces) > 0:
                intro = "%d Email(s) ont été envoyés avec succès mais les %d envois suivants ont échoué :" % (
                len(listeSucces), len(listeAnomalies))
            else:
                intro = "Tous les envois ont lamentablement échoué :"
            lignes = []
            for message, erreur in listeAnomalies:
                adresse = message.GetLabelDestinataires()
                try:
                    lignes.append(u"- %s : %s" % (adresse.decode('cp1252'), erreur))
                except:
                    lignes.append(u"- %s : %s" % (adresse, erreur))
            dlg = DLG_Messagebox.Dialog(None, titre="Compte-rendu de l'envoi", introduction=intro,
                                        detail="\n".join(lignes), icone=wx.ICON_INFORMATION, boutons=["Ok", ])
            dlg.ShowModal()
            dlg.Destroy()

        return listeSucces

class Mailjet(Base_messagerie):
    def __init__(self, **kwds):
        Base_messagerie.__init__(self, **kwds)

    def Connecter(self):
        # Récupération des clés Mailjet
        api_key = self.dict_parametres.get("api_key", None)
        api_secret = self.dict_parametres.get("api_secret", None)
        if api_key == None or api_secret == None:
            raise ValueError(u"Les codes MAILJET ne sont pas valides.")

        # Connexion à Mailjet à réactiver si 'mailjet_rest' existe
        """
        try:
            from mailjet_rest import Client
            self.connection = Client(auth=(api_key, api_secret), version='v3.1')
        except Exception as err:
            raise
        """

    def Envoyer(self, message=None):
        # Préparation du message
        dict_message = {
            "From": {"Email": self.email_exp, "Name": self.nom_exp},
            "To": [{"Email": destinataire} for destinataire in message.destinataires],
            "Subject": message.sujet,
            "TextPart": message.texte_plain,
            "HTMLPart": message.texte_html,
            "Attachments": [],
            "InlinedAttachments": [],
        }

        # Intégration des images incluses
        index = 0
        for fichier in message.images:
            ctype, encoding = mimetypes.guess_type(fichier)
            with open(fichier, "rb") as file:
                Base64Content = base64.b64encode(file.read())
            nom_fichier = os.path.basename(fichier)

            dict_fichier = {
                "ContentType": ctype,
                "Filename": nom_fichier,
                "ContentID": "image%d" % index,
                "Base64Content": Base64Content,
            }
            dict_message["InlinedAttachments"].append(dict_fichier)
            index += 1

        # Intégration des pièces jointes
        for fichier in message.fichiers:
            ctype, encoding = mimetypes.guess_type(fichier)
            with open(fichier, "rb") as file:
                Base64Content = base64.b64encode(file.read())
            nom_fichier = os.path.basename(fichier)

            dict_fichier = {
                "ContentType": ctype,
                "Filename": nom_fichier,
                "Base64Content": Base64Content,
            }
            dict_message["Attachments"].append(dict_fichier)

        # Envoi de la requête à Mailjet
        resultats = self.connection.send.create(data={"Messages": [dict_message,]})

        # Analyse du résultat
        try:
            resultat = resultats.json()["Messages"][0][u'Status']
        except Exception as err:
            print(err)
            print(resultats.status_code)
            print(resultats.json())
            raise Exception(err)

        if resultat != u'success':
            raise Exception(resultat)

        return resultat

    def Fermer(self):
        self.connection.close()

    def Envoyer_lot(self, messages=[], dlg_progress=None, afficher_confirmation_envoi=True):
        """ Envoi des messages par lot """
        # Envoi des mails
        index = 1
        listeAnomalies = []
        listeSucces = []
        ne_pas_signaler_erreurs = False
        for message in messages:
            while True:
                adresse = message.GetLabelDestinataires()
                try:
                    labelAdresse = adresse.decode('cp1252')
                except:
                    labelAdresse = adresse
                label = "Envoi %d/%d : %s..." % (index, len(messages), labelAdresse)

                # Si la dlg_progress a été fermée, on la réouvre
                if dlg_progress == None:
                    dlg_progress = wx.ProgressDialog("Envoi des mails", "", maximum=len(messages) + 1, parent=None)
                    dlg_progress.SetSize((450, 140))
                    dlg_progress.CenterOnScreen()
                dlg_progress.Update(index, label)

                # Envoi
                try:
                    self.Envoyer(message)
                    listeSucces.append(message)
                except Exception as err:
                    err = str(err).decode('cp1252')
                    listeAnomalies.append((message, err))
                    print(("Erreur dans l'envoi d'un mail : %s...", err))
                    traceback.print_exc(file=sys.stdout)

                    if ne_pas_signaler_erreurs == False:

                        # Fermeture de la dlg_progress
                        dlg_progress.Destroy()
                        dlg_progress = None

                        # Affichage de l'erreur
                        intro = "L'erreur suivante a été détectée :"
                        detail = err
                        if index <= len(messages) - 1:
                            conclusion = "Souhaitez-vous quand même continuer l'envoi des autres emails ?"
                            boutons = ["Réessayer", "Continuer",
                                       "Continuer et ne plus signaler les erreurs", "Arrêter"]
                        else:
                            conclusion = None
                            boutons = ["Réessayer", "Arrêter", ]
                        dlgErreur = DLG_Messagebox.Dialog(None, titre="Erreur", introduction=intro, detail=detail,
                                                          conclusion=conclusion, icone=wx.ICON_ERROR, boutons=boutons)
                        reponse = dlgErreur.ShowModal()
                        dlgErreur.Destroy()
                        if reponse == 0:
                            continue
                        if reponse == 2:
                            ne_pas_signaler_erreurs = True
                        if reponse == 3:
                            return listeSucces
                break

            if len(messages) > 1:
                time.sleep(1)
            index += 1

        # Fin de la gauge
        if dlg_progress != None:
            dlg_progress.Update(index, "Fin de l'envoi.")
            dlg_progress.Destroy()

        # Si tous les Emails envoyés avec succès
        if len(listeAnomalies) == 0 and afficher_confirmation_envoi == True:
            if len(listeSucces) == 1:
                message = "L'Email a été envoyé avec succès !"
            else:
                message = "Les %d Emails ont été envoyés avec succès !" % len(listeSucces)
            dlg = wx.MessageDialog(None, message, "Fin de l'envoi", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()

        # Si Anomalies
        if len(listeAnomalies) > 0 and len(messages) > 1:
            if len(listeSucces) > 0:
                intro = "%d Email(s) ont été envoyés avec succès mais les %d envois suivants ont échoué :" % ( len(listeSucces), len(listeAnomalies))
            else:
                intro = "Tous les envois ont lamentablement échoué :"
            lignes = []
            for message, erreur in listeAnomalies:
                adresse = message.GetLabelDestinataires()
                try:
                    lignes.append(u"- %s : %s" % (adresse.decode('cp1252'), erreur))
                except:
                    lignes.append(u"- %s : %s" % (adresse, erreur))
            dlg = DLG_Messagebox.Dialog(None, titre="Compte-rendu de l'envoi", introduction=intro, detail="\n".join(lignes), icone=wx.ICON_INFORMATION, boutons=["Ok", ])
            dlg.ShowModal()
            dlg.Destroy()

        return listeSucces

    def Fermer(self):
        pass

# Envoie un mail test à l'adresse de la famille 709
if __name__ == u"__main__":
    raise "SECURITE EN TEST: envoie le mail test sans sommation, masquer la ligne pour tester un envoi voulu"
    dictDest = UTILS_Titulaires.GetCorrespondant(IDfamille=709)
    lstDest = dictDest["mails"].split(";")
    pathFichier = ''
    dictExp = GetAdresseExp()
    dictEnvoi = {
        "backend" : "smtp",
        "hote" : dictExp["smtp"],# "smtp.gmail.com",
        "port" : dictExp["port"],# 587,
        "utilisateur" : dictExp["utilisateur"],# "xxxxx@xxxx.com",
        "motdepasse" : dictExp["motdepasse"],# "**************",
        "email_exp" : dictExp["adresse"],# "xxxxx@xxxx.com",
        "nom_exp" : "expediteur test",
        "timeout" : 20,
        "use_tls" : 1,
        "parametres" : "notification==0",
        "fail_silently" : False
        }
    # Préparation du message
    message = Message(destinataires=lstDest, sujet=u"Sujet du mail",
                      texte_html="<p>Ceci est le <b>texte</b> html</p>", 
                      fichiers=[],
                      images=[])

    # Envoi du message
    messagerie = Messagerie(**dictEnvoi)
    messagerie.Connecter()
    messagerie.Envoyer(message)
    messagerie.Fermer()

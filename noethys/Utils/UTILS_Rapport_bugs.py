#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Branche Matthania
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS, JB
# Copyright:       (c) 2010-19 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import Chemins
import FonctionsPerso
from Utils.UTILS_Traduction import _
import wx
import os
from Ctrl import CTRL_Bouton_image
import sys
import platform
import traceback
import datetime
import GestionDB
import webbrowser
import wx.lib.dialogs
from Utils import UTILS_Config
from Utils import UTILS_Customize
from Utils import UTILS_Fichiers
from Utils import UTILS_Identification
from Dlg import DLG_Preferences

def Activer_rapport_erreurs(version=""):
    def my_excepthook(exctype, value, tb):
        dateDuJour = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        systeme = "%s %s %s %s" % (sys.platform, platform.system(), platform.release(), platform.machine())
        infos = "## %s | %s | wxPython %s | %s ##" % (dateDuJour, version, wx.version(), systeme)
        bug = ''.join(traceback.format_exception(exctype, value, tb))

        # Affichage dans le journal
        print(bug)

        # Affichage dans une DLG
        try :
            if UTILS_Config.GetParametre("rapports_bugs", True) == False :
                return
        except :
            pass
        try :
            texte = "%s\n%s" % (infos, bug)
            dlg = DLG_Rapport(None, texte)
            dlg.ShowModal()
            dlg.Destroy()
        except :
            pass

    sys.excepthook = my_excepthook

def ScreenShot(pathFile):
    s = wx.ScreenDC()
    w, h = s.Size.Get()
    b = wx.Bitmap(w, h)

    m = wx.MemoryDC(s)
    m.SelectObject(b)
    m.Blit(0, 0, w, h, s, 0, 0)
    m.SelectObject(wx.NullBitmap)
    b.SaveFile(pathFile, wx.BITMAP_TYPE_PNG)

# ------------------------------------------- BOITE DE DIALOGUE ----------------------------------------------------------------------------------------

class DLG_Rapport(wx.Dialog):
    def __init__(self, parent, texte=""):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent

        # copy �cran dans un fichier temp
        self.pathFile = UTILS_Fichiers.GetRepTemp("tmpScreenShot.png")
        ScreenShot(self.pathFile)

        self.ctrl_image = wx.StaticBitmap(self, wx.ID_ANY, wx.Bitmap(Chemins.GetStaticPath(u"Images/48x48/Erreur.png"), wx.BITMAP_TYPE_ANY))
        self.label_ligne_1 = wx.StaticText(self, wx.ID_ANY, _("Noethys a rencontr� un probl�me !"))
        self.label_ligne_2 = wx.StaticText(self, wx.ID_ANY, _("Le rapport d'erreur ci-dessous peut servir � la r�solution de ce bug.\nMerci de bien vouloir le communiquer � l'auteur par Email."))
        self.ctrl_rapport = wx.TextCtrl(self, wx.ID_ANY, texte, style=wx.TE_MULTILINE | wx.TE_READONLY)
        
        self.bouton_envoyer = CTRL_Bouton_image.CTRL(self, texte=_("Envoyer au support"), cheminImage="Images/32x32/Emails_exp.png")
        self.bouton_forum = CTRL_Bouton_image.CTRL(self, texte=_("Acc�der au forum"), cheminImage="Images/32x32/Forum.png")
        self.bouton_fermer = CTRL_Bouton_image.CTRL(self, texte=_("Fermer"), cheminImage="Images/32x32/Fermer.png")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonEnvoyer, self.bouton_envoyer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonForum, self.bouton_forum)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonFermer, self.bouton_fermer)

        # Envoi dans le presse-papiers
        clipdata = wx.TextDataObject()
        clipdata.SetText(texte)
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(clipdata)
        wx.TheClipboard.Close()

        self.bouton_fermer.SetFocus()

    def __set_properties(self):
        self.SetTitle(_("Rapport d'erreurs"))
        self.label_ligne_1.SetFont(wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.ctrl_rapport.SetToolTip(wx.ToolTip(_("Ce rapport d'erreur a �t� copi� dans le presse-papiers")))
        self.bouton_envoyer.SetToolTip(wx.ToolTip(_("Cliquez ici pour envoyer ce rapport d'erreur � l'auteur par Email")))
        self.bouton_forum.SetToolTip(wx.ToolTip(_("Cliquez ici pour ouvrir votre navigateur internet et acc�der au forum de Noethys. Vous pourrez ainsi signaler ce bug dans la rubrique d�di�e.")))
        self.bouton_fermer.SetToolTip(wx.ToolTip(_("Cliquez ici pour fermer")))
        self.SetMinSize((650, 850))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(2, 1, 10, 10)
        grid_sizer_bas = wx.FlexGridSizer(1, 5, 10, 10)
        grid_sizer_haut = wx.FlexGridSizer(1, 2, 10, 10)
        grid_sizer_droit = wx.FlexGridSizer(3, 1, 10, 10)
        grid_sizer_haut.Add(self.ctrl_image, 0, wx.ALL, 10)
        grid_sizer_droit.Add(self.label_ligne_1, 0, 0, 0)
        grid_sizer_droit.Add(self.label_ligne_2, 0, 0, 0)
        grid_sizer_droit.Add(self.ctrl_rapport, 0, wx.EXPAND, 0)
        grid_sizer_droit.AddGrowableRow(2)
        grid_sizer_droit.AddGrowableCol(0)
        grid_sizer_haut.Add(grid_sizer_droit, 1, wx.RIGHT | wx.TOP | wx.EXPAND, 10)
        grid_sizer_haut.AddGrowableRow(0)
        grid_sizer_haut.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_haut, 1, wx.EXPAND, 0)
        grid_sizer_bas.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_bas.Add(self.bouton_envoyer, 0, 0, 0)
        grid_sizer_bas.Add(self.bouton_forum, 0, 0, 0)
        grid_sizer_bas.Add(self.bouton_fermer, 0, 0, 0)
        grid_sizer_bas.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_bas, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(0)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen() 

    def OnBoutonFermer(self, event):
        if os.path.isfile(self.pathFile):
            os.remove(self.pathFile)
        self.EndModal(wx.ID_CANCEL)

    def OnBoutonEnvoyer(self, event):
        # DLG Commentaires
        texteRapport = self.ctrl_rapport.GetValue()
        dlg = DLG_Envoi(self, texteRapport)
        reponse = dlg.ShowModal()
        commentaires = dlg.GetCommentaires()
        joindre_journal = dlg.GetJoindreJournal()
        dlg.Destroy()
        if reponse == wx.ID_OK :
            self.Envoyer_mail(commentaires, joindre_journal)

    def OnBoutonForum(self, event):
        dlg = wx.MessageDialog(self, _("Il n'y a pas de forum sp�cifique d�di� � la brance Noethys-Matthania. Le forum Noethys ne peut recueillir que les bugs sur les installations de Noethys t�l�charg� sur Noethys"), _("Forum Noethys"), wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
        webbrowser.open("https://www.noethys.com/index.php/forum-34")

    def GetAdresseExpDefaut(self):
        """ Retourne les param�tres de l'adresse d'exp�diteur par d�faut """
        dictAdresse = {}
        # R�cup�ration des donn�es
        DB = GestionDB.DB()
        req = """SELECT IDadresse, moteur, adresse, motdepasse, smtp, port, defaut, connexionAuthentifiee, startTLS, utilisateur, parametres
        FROM adresses_mail WHERE defaut=1 ORDER BY adresse; """
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if len(listeDonnees) == 0 : return None
        IDadresse, moteur, adresse, motdepasse, smtp, port, defaut, connexionAuthentifiee, startTLS, utilisateur, parametres = listeDonnees[0]
        dictAdresse = {"adresse":adresse, "moteur":moteur, "motdepasse":motdepasse, "smtp":smtp, "port":port, "auth":connexionAuthentifiee, "startTLS":startTLS, "utilisateur" : utilisateur, "parametres": parametres}
        return dictAdresse

    def Envoyer_mail(self, commentaires="", joindre_journal=False):
        """ Envoi d'un mail avec pi�ce jointe """
        from Utils import UTILS_Envoi_email

        # Exp�diteur
        dictExp = self.GetAdresseExpDefaut()
        if dictExp == None :
            dlg = wx.MessageDialog(self, _("Vous devez d'abord saisir une adresse d'exp�diteur depuis le menu Param�trage > Adresses d'exp�dition d'Emails. Sinon, postez votre rapport de bug dans le forum de Noethys."), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        moteur = dictExp["moteur"]
        adresseExpediteur = dictExp["adresse"]
        serveur = dictExp["smtp"]
        port = dictExp["port"]
        auth = dictExp["auth"]
        startTLS = dictExp["startTLS"]
        motdepasse = dictExp["motdepasse"]
        utilisateur = dictExp["utilisateur"]
        parametres = dictExp["parametres"]

        # Destinataire
        mailAuteur = DLG_Preferences.Parametres("get","rapports_mailAuteur", "xxxx@yyyy.com")
        if len(mailAuteur) == 0 or "xxx" in mailAuteur:
            mess = "L'adresse du correspondant n'est pas renseign�e dans les pr�f�rences. Veuillez la v�rifier."
            wx.MessageBox(mess,"Envoi impossible", wx.OK | wx.ICON_EXCLAMATION)
            return False

        if adresseExpediteur == None :
            dlg = wx.MessageDialog(self, _("L'adresse d'exp�dition ne semble pas valide. Veuillez la v�rifier."), _("Envoi impossible"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        # Attacher le journal d'erreurs et le screenShot
        fichiers = []
        if joindre_journal == True :
            customize = UTILS_Customize.Customize()
            nom_journal = UTILS_Fichiers.GetRepUtilisateur(customize.GetValeur("journal", "nom", "journal.log"))
            fichiers.append(nom_journal)
            fichiers.append(self.pathFile)

        # Pr�paration du message
        IDrapport = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        texteRapport = self.ctrl_rapport.GetValue().replace("\n","<br/>")
        if len(commentaires) == 0 :
            commentaires = _("Aucun")
        texte_html = _("<u>Rapport de bug %s :</u><br/><br/>%s<br/><u>Commentaires :</u><br/><br/>%s") % (IDrapport, texteRapport, commentaires)

        sujet = _("Rapport de bug Noethys n�%s") % IDrapport
        message = UTILS_Envoi_email.Message(destinataires=[mailAuteur,], sujet=sujet, texte_html=texte_html, fichiers=fichiers)

        # Envoi du mail
        try :
            messagerie = UTILS_Envoi_email.Messagerie(backend=moteur, hote=serveur, port=port, utilisateur=utilisateur, motdepasse=motdepasse, email_exp=adresseExpediteur, use_tls=startTLS, parametres=parametres)
            messagerie.Connecter()
            messagerie.Envoyer(message)
            messagerie.Fermer()
        except Exception as err :
            dlg = wx.MessageDialog(self, _("Le message n'a pas pu �tre envoy� automatiquement. Merci de 'coller' la copie d'�cran dans un mail ordinaire\n\nErreur : %s !") % err, _("Envoi impossible"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        # Message de confirmation
        dlg = wx.MessageDialog(self, _("Le rapport d'erreur a �t� envoy� avec succ�s."), _("Rapport envoy�"), wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

        return True

# -------------------------------------------------------------------------------------------------------------------------------------------------------------

class DLG_Envoi(wx.Dialog):
    def __init__(self, parent, texteRapport=u""):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.texteRapport = texteRapport

        self.label_ligne_1 = wx.StaticText(self, wx.ID_ANY, _("Le rapport est pr�t � �tre envoy�..."))
        self.label_ligne_2 = wx.StaticText(self, wx.ID_ANY, _("Veuillez ajouter ci-dessous les circonstances de l'�v�nement: Que faisiez-vous, sur quel client?\nCeci permettra de reproduire le cas pour un diagnostic."))

        dicUser = UTILS_Identification.GetDictUtilisateur()
        if not dicUser:
            dicUser = {"prenom":"Lancement direct","nom":""}
        version = FonctionsPerso.GetVersionLogiciel(datee=True)
        userName = "%s %s Version %s"%(dicUser["prenom"],dicUser["nom"],version)
        intro = "Bug envoy� par : %s\n\nQuelle action :\n\nReproductible :\n\n'"%userName
        self.ctrl_commentaires = wx.TextCtrl(self, wx.ID_ANY, intro , style=wx.TE_MULTILINE)

        self.check_journal = wx.CheckBox(self, -1, _("Joindre la copie d'�cran et le journal des erreurs (Facilite le diagnostic)"))
        self.check_journal.SetValue(True)
        self.bouton_apercu = CTRL_Bouton_image.CTRL(self, texte=_("Aper�u"), cheminImage="Images/32x32/Apercu.png")
        self.bouton_envoyer = CTRL_Bouton_image.CTRL(self, texte=_("Envoyer l'Email"), cheminImage="Images/32x32/Emails_exp.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Annuler"), cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonApercu, self.bouton_apercu)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonEnvoyer, self.bouton_envoyer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)

    def __set_properties(self):
        self.SetTitle(_("Envoyer le rapport � l'auteur"))
        self.label_ligne_1.SetFont(wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.ctrl_commentaires.SetToolTip(wx.ToolTip(_("Vous pouvez saisir des commentaires ici")))
        self.check_journal.SetToolTip(wx.ToolTip(_("Le rapport d'erreurs, facilite la r�solution du bug, ")))
        self.bouton_apercu.SetToolTip(wx.ToolTip(_("Cliquez ici pour visualiser le contenu du message qui sera envoy� � l'auteur")))
        self.bouton_envoyer.SetToolTip(wx.ToolTip(_("Cliquez ici pour envoyer le rapport et les commentaires � l'auteur")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Cliquez ici pour annuler")))
        self.SetMinSize((550, 350))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(5, 1, 10, 10)
        grid_sizer_boutons = wx.FlexGridSizer(1, 4, 10, 10)
        grid_sizer_base.Add(self.label_ligne_1, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        grid_sizer_base.Add(self.label_ligne_2, 0, wx.LEFT | wx.RIGHT, 10)
        grid_sizer_base.Add(self.ctrl_commentaires, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        grid_sizer_base.Add(self.check_journal, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        grid_sizer_boutons.Add(self.bouton_apercu, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_envoyer, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(2)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()

    def OnBoutonApercu(self, event):
        """ Visualisation du message � envoyer """
        commentaires = self.ctrl_commentaires.GetValue()
        if len(commentaires) == 0 :
            commentaires = _("Aucun")
        message = _("Rapport : \n\n%s\nCommentaires : \n\n%s") % (self.texteRapport, commentaires)
        dlg = wx.lib.dialogs.ScrolledMessageDialog(self, message, _("Visualisation du contenu du message"))
        dlg.ShowModal()
        dlg.Destroy()

    def OnBoutonEnvoyer(self, event):
        if self.GetJoindreJournal():
            mess = "La copie de votre �cran sera jointe\n\n"
            mess += "Si des infos confidentielles y apparaissent, 'Annulez' puis d�cochez la case en bas de l'�cran pr�c�dent."
            ret = wx.MessageBox(mess,"Confirmation d'envoi", style=wx.ICON_INFORMATION|wx.YES_DEFAULT|wx.CANCEL)
            if ret != wx.OK:
                return
        self.EndModal(wx.ID_OK)

    def OnBoutonAnnuler(self, event):
        self.EndModal(wx.ID_CANCEL)

    def GetCommentaires(self):
        return self.ctrl_commentaires.GetValue()

    def GetJoindreJournal(self):
        return self.check_journal.GetValue()

if __name__ == "__main__":
    app = wx.App(0)
    dialog_1 = DLG_Rapport(None)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()

    app.MainLoop()

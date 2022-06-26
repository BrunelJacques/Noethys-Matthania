#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Branche Matthania
# Module :         Mise en place d'un fichier release contenant les patchs
# Auteur:          JB adaptation de DLG_Restauration
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

from Utils.UTILS_Traduction import _
import wx
import GestionDB
import FonctionsPerso
import datetime
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Bandeau
from Utils import UTILS_Fichiers
from Utils import UTILS_Parametres
from Utils import UTILS_Dates
from Utils import UTILS_Config

# ------------------------------------------------------------------------------------------------------------------------------------------------

def GetVersionsFromZipFile(nameFichier, releaseZip):
    # Cherche le fichier versions dans le fichier zip, retourne le fichier
    if not releaseZip: return
    lstFichiers = UTILS_Fichiers.GetListeFichiersZip(releaseZip)
    lstVersions = [x for x in lstFichiers if "versions" in x.lower()]
    if len(lstVersions) == 0:
        mess = "Le Zip %s ne contient pas de fichier 'Versions.txt'" % nameFichier
        wx.MessageBox(mess, "Echec", style=wx.ICON_ERROR)
        return
    nameVersionsFile = lstVersions[0]
    return UTILS_Fichiers.GetOneFileInZip(releaseZip, nameVersionsFile)

class CTRL_AfficheVersion(wx.TextCtrl):
    def __init__(self, parent):
        label = "Info dernières versions"
        id = wx.ID_ANY
        pos = wx.DefaultPosition
        size = wx.DefaultSize
        style = wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH | wx.TE_DONTWRAP
        wx.TextCtrl.__init__(self, parent, id, label, pos, size, style=style)
        self.parent = parent
        self.version_logiciel = self.parent.version_logiciel
        self.tplVersionLogiciel = self.parent.tplVersionLogiciel
        tplVersionData = self.parent.tplVersionData

        # les deux premiers items sont exprimés en texte comme préfixe
        self.categorie = str(self.tplVersionLogiciel[:2])
        self.invite = "\nActuellement: Version % s\n"%self.version_logiciel


        if tplVersionData == self.tplVersionLogiciel:
            self.parent.bouton_ok.Enable(False)
            self.parent.bouton_fichier.Enable(True)
            # le logiciel est à jour
            invite = "%s\nChoisissez un fichier"%self.invite
            self.SetValue(invite)
        else:
            # release automatique
            self.parent.bouton_ok.Enable(True)
            self.parent.bouton_fichier.Enable(False)
            ret = self.GetReleaseDocument(tplVersionData)
            if ret != "ok":
                invite = "%s\nEchec sur ouverture du fichier version '%s'" %(self.invite,str(tplVersionData))
                invite += "\n%s"%ret
                self.SetValue(invite)
                self.parent.bouton_ok.Enable(False)
                self.parent.bouton_fichier.Enable(True)

    def GetVersionChoisie(self, texte):
        # affiche les nouveautés et retourne le no version
        posF = texte.find(self.version_logiciel) - 8
        if posF == -1:
            posF = min(2000, len(texte))
        nouveautes = texte[:posF].strip()
        #dc = wx.ClientDC(self)
        #dc.SetFont(self.GetFont())
        posDebut = texte.find("n")
        posFin = texte.find("(", 0, 50)
        version = texte[posDebut + 1:posFin].strip()
        if nouveautes.strip() == "":
            nouveautes = "%s\n Même version !"%version
        self.SetValue("%sVersions à installer :\n\n%s" % (self.invite, nouveautes))
        return version

    def ChoisirFichier(self):
        # choix d'un fichier et affichage du contenu de versions

        def GetNameReleaseZip():
            # Recherche et sélectionne un fichier release.zip
            wildcard = "Release Noethys (*.zip; *.7z)|*.*"
            intro = "Veuillez sélectionner le fichier contenant la MISE A JOUR DE NOETHYS"
            return UTILS_Fichiers.SelectionFichier(intro, wildcard, verifZip=True)

        nameFichier = GetNameReleaseZip()
        if not nameFichier:
            return
        try:
            self.zipFile = UTILS_Fichiers.GetZipFile(nameFichier,"r")
            texte = GestionDB.Decod(GetVersionsFromZipFile(nameFichier,self.zipFile))
            # afichage du contenu
            if texte:
                version_choisie = self.GetVersionChoisie(texte)
                if version_choisie.split('.')[:3] != self.version_logiciel.split('.')[:3]:
                    mess = "Trop de différence entre les versions\n\n"
                    mess += "Refaites une installation complète depuis Github NoethysMatthania"
                    wx.MessageBox(mess, "Impossible",style=wx.ICON_ERROR)
                    return
                if version_choisie < self.version_logiciel:
                    mess = "Rétropédalage à confirmer\n\n"
                    mess += "La %s remontée sera antérieure\nà l'actuelle %s\n\n"%(version_choisie,self.version_logiciel)
                    mess += "Certaines nouvelles modifications pourront rester en place"
                    ret = wx.MessageBox(mess,style=wx.YES_NO|wx.ICON_INFORMATION)
                    if ret  != wx.YES:
                        return
                self.parent.bouton_ok.Enable(True)
                self.parent.bouton_fichier.Enable(False)
            
        except Exception as err:
            if isinstance(err,UnicodeDecodeError):
                mess = "Le fichier version importé n'est pas codé en UTF-8\n%s"%err
                wx.MessageBox(mess,"Abandon")
            print(type(err),err)
        return

    def SetReleaseDocument(self,tplVersion):
        # Copie le fichier zip-release dans la base de donnée
        DBdoc = GestionDB.DB(suffixe="DOCUMENTS")
        categorie = "%d.%d"%(tplVersion[0],tplVersion[1])
        dte = UTILS_Dates.DateDDEnDateEng(datetime.date.today())
        lstTplDon = [
            ("categorie",categorie),
            ("niveau",tplVersion[2]),
            ("echelon", tplVersion[3]),
            ("dateImport", dte),
            ("fichier",self.zipFile),
            ("description","{user:%s}"%DBdoc.UtilisateurActuel())
            ]
        mess = "DLG_Release.SetReleaseDocument"
        return DBdoc.ReqInsert("releases",lstTplDon,MsgBox=mess)

    def GetNoReleases(self,DBdoc,categorie):
        req = """
        SELECT niveau, echelon
        FROM releases
        WHERE categorie = %s
        ORDER BY niveau desc, echelon DESC
        ;"""%(categorie)
        ret = DBdoc.ExecuterReq(req,MsgBox="DLG_Release.GetReleaseDocument")
        if ret != "ok":
            return ret
        recordset = DBdoc.ResultatReq()
        a,b = categorie.split(".")
        tplCategorie = (int(a), int(b))
        lstNoReleases = [ tplCategorie + (x,y) for (x,y) in recordset]
        return lstNoReleases

    def GetReleaseDocument(self, tplVersion,nomFichier=''):
        # Retourne le fichier zip-release de la base de donnée
        ix = self.parent.choice_baseDonnees.GetSelection()
        nomFichier = self.parent.choice_baseDonnees.GetString(ix)
        if nomFichier == '':
            DBdoc = GestionDB.DB(suffixe="DOCUMENTS")
        else:
            DBdoc = GestionDB.DB(nomFichier=nomFichier,suffixe="DOCUMENTS")
        categorie = "%d.%d"%(tplVersion[0],tplVersion[1])

        lstNoReleases = self.GetNoReleases(DBdoc, categorie)
        lastNoRelease = None
        if len(lstNoReleases) > 0 :
            lastNoRelease = lstNoReleases[0]

        mess = None
        if not lastNoRelease:
            mess = "Pas de releases sockées dans cette base pour Noethys '(%s)'"%categorie
        elif lastNoRelease != tplVersion:
            mess = "La version '%s' n'est pas stockée dans cette base, d'autres versions sont disponibles"%str(tplVersion)
        if mess:
            return mess

        # La release de la version attendue est présente
        req = """
        SELECT fichier
        FROM releases
        WHERE categorie = %s 
            AND niveau = %d
            AND echelon = %d"""%(categorie,tplVersion[2],tplVersion[3])
        ret = DBdoc.ExecuterReq(req,MsgBox="DLG_Release.GetReleaseDocument")
        if ret != "ok":
            return ret
        recordset = DBdoc.ResultatReq()
        self.zipFile = None
        if len(recordset) == 0:
            return "Fichier de mise à jour n'est pas présent dans la base"
        self.zipFile = recordset[0][0]
        versions = GetVersionsFromZipFile("Release %s"%str(tplVersion)[1:-1], self.zipFile)
        texte = GestionDB.Decod(versions)
        invite = "%s\n%s"%(self.invite,texte)
        self.SetValue(invite)
        return "ok"

class Dialog(wx.Dialog):
    def __init__(self, parent,version_data=None,version_logiciel_date=None):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        if not version_data or not version_logiciel_date:
            version_data, version_logiciel_date = self.GetVersions()
        posDeb = version_logiciel_date.find("n") +1
        posFin = version_logiciel_date.find("(")
        version_logiciel = version_logiciel_date[posDeb:posFin].strip()
        self.version_logiciel = version_logiciel
        self.version_data = version_data
        self.tplVersionLogiciel = FonctionsPerso.ConvertVersionTuple(version_logiciel)
        self.tplVersionData = FonctionsPerso.ConvertVersionTuple(version_data)

        if self.tplVersionData == self.tplVersionLogiciel:
            intro = _("Vous pouvez ici mettre à jour votre version Noethys, à partir d'un fichier ZIP contenant la release")
        else:
            intro = _("Vous pouvez ici mettre à jour votre version Noethys automatiquement")
        titre ="Mise à jour"
        self.SetTitle(titre)
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/32x32/Restaurer.png")

        self.txt_base = wx.StaticBox(self,-1,"Stockage des versions : ")
        self.choice_baseDonnees = wx.Choice(self, -1, choices=self.__getDerniersFichiers())
        self.check_maj =     wx.CheckBox(self, -1, "Mettre à jour ma station")
        self.check_stocke =  wx.CheckBox(self, -1, "Stocker pour partager")
        # Boutons
        self.bouton_versions = CTRL_Bouton_image.CTRL(self, texte=_("Anciennes Versions"), cheminImage="Images/32x32/Droits.png")
        self.bouton_fichier = CTRL_Bouton_image.CTRL(self, texte=_("Choisir le fichier"), cheminImage="Images/32x32/Desarchiver.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ok pour release"), cheminImage="Images/32x32/Valider.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Annuler"), cheminImage="Images/32x32/Annuler.png")

        # Affichage de la version proposée
        self.box_donnees_staticbox = wx.StaticBox(self, -1,"Description des versions :")
        self.ctrl_donnees = CTRL_AfficheVersion(self)
        self.ctrl_donnees.SetMinSize((250, -1))

        self.__set_properties()
        self.__do_layout()
        
        self.Bind(wx.EVT_BUTTON, self.OnBoutonFichier, self.bouton_fichier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)

    def __set_properties(self):
        self.choice_baseDonnees.Select(0)
        self.check_maj.SetValue(True)
        self.check_stocke.SetValue(True)
        self.txt_base.SetToolTip(wx.ToolTip("Choix de la base de donnée qui conserve les versions"))
        self.choice_baseDonnees.SetToolTip(wx.ToolTip("Base de donnée qui conserve les différentes versions"))
        self.check_maj.SetToolTip(wx.ToolTip("Pour mettre à jour l'application sur votre station de travail"))
        self.check_stocke.SetToolTip(wx.ToolTip("Pour enregistrer la mise à jour dans la base et qu'elle devienne accessible aux autres stations"))
        self.bouton_fichier.SetToolTip(wx.ToolTip(_("Cliquez ici pour choisir le fichier release.zip")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_("Cliquez ici pour lancer la restauration")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Cliquez ici pour annuler")))
        self.SetMinSize((600, 800))

    def __getDerniersFichiers(self):
        cfg = UTILS_Config.FichierConfig()
        userConfig = cfg.GetDictConfig()
        lstFichiers = userConfig["derniersFichiers"]
        lstNomsFichiers = []
        for nomFichier in lstFichiers:
            if "[RESEAU]" in nomFichier:
                port, hote, user, mdp = nomFichier.split(";")
                nomFichier = nomFichier[
                             nomFichier.index("[RESEAU]")+8:] + " - %s" % hote
                if not nomFichier in lstNomsFichiers:
                    lstNomsFichiers.append(nomFichier)
        return lstNomsFichiers

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)
        
        box_donnees = wx.StaticBoxSizer(self.box_donnees_staticbox, wx.VERTICAL)
        box_donnees.Add(self.ctrl_donnees, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(box_donnees, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

        grid_sizer_bd = wx.FlexGridSizer(rows=1, cols=4, vgap=0, hgap=0)
        grid_sizer_bd.Add(self.txt_base,0,0,0)
        grid_sizer_bd.Add(self.choice_baseDonnees,1,wx.EXPAND,0)
        grid_sizer_bd.Add((150,10),1,wx.EXPAND,0)
        grid_sizer_bd.Add(self.bouton_versions,1,wx.EXPAND,0)
        grid_sizer_base.Add(grid_sizer_bd,1,wx.EXPAND,0)

        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=5, vgap=10, hgap=10)
        grid_sizer_options = wx.FlexGridSizer(rows=2, cols=1, vgap=2, hgap=3)
        grid_sizer_options.Add(self.check_maj, 0, wx.LEFT, 4)
        grid_sizer_options.Add(self.check_stocke, 0, wx.LEFT, 4)
        grid_sizer_boutons.Add(grid_sizer_options, 1, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_fichier, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        self.Layout()
        self.CenterOnScreen() 

    def GetVersions(self):
        version_logiciel = FonctionsPerso.GetVersionLogiciel(datee=True)
        version_data =  UTILS_Parametres.Parametres(mode="get",
                                categorie="fichier", nom="version", 
                                valeur=version_logiciel)
        return version_data, version_logiciel

    def OnBoutonFichier(self, event):
        self.ctrl_donnees.ChoisirFichier()
        return

    def OnBoutonAnnuler(self, event):
        self.EndModal(wx.ID_CANCEL)

    def OnBoutonOk(self, event):
        # release doit contenir l'arborescence à partir de noethys inclus
        pathRoot = "%s"%FonctionsPerso.GetPathRoot()
        # test si on est bien à l'emplacement
        try:
            fichierVersion = open("%s/noethys/Versions.txt"%pathRoot)
            fichierVersion.close()
        except Exception as err:
            print(err)
            mess = "Vérification du positionnement\n\n%s"%err
            wx.MessageBox(mess, "Erreur inattendue", style=wx.ICON_ERROR)
            return
        # action de dézippage
        mess = "Process interrompu !!"
        if self.ctrl_donnees.zipFile:
            self.ctrl_donnees.zipFile.extractall("%s"%pathRoot)

            mess = "Le processus de mise à jour est terminé."

        # Fin du processus
        dlg = wx.MessageDialog(self,mess, "Release", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

        # Fermeture
        self.EndModal(wx.ID_OK)

if __name__ == "__main__":
    app = wx.App(0)
    FonctionsPerso.GetPathRoot()
    dialog_1 = Dialog(None,"1.3.1.12","version 1.3.1.10 (15/06/2022)")
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()

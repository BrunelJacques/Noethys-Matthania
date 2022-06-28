#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------------------------------------
# Application :    Noethys, Branche Matthania
# Module :         Mise en place d'un fichier release contenant les patchs
# Auteur:          JB adaptation de DLG_Restauration
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------------------------------------

import wx
import GestionDB
import FonctionsPerso
import datetime
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_ChoixListe
from Ctrl import CTRL_Bandeau
from Utils import UTILS_Fichiers
from Utils import UTILS_Parametres
from Utils import UTILS_Dates
from Utils import UTILS_Config

# ------------------------------------------------------------------------------------------------------------------------------------------------

def GetVersionsFromZipFile(releaseZip=None, nameFichier="???"):
    # Cherche le fichier versions dans le fichier zip, retourne le fichier
    if not releaseZip: return
    lstFichiers = UTILS_Fichiers.GetListeFichiersZip(releaseZip)
    lstVersions = [x for x in lstFichiers if "versions" in x.lower()]
    if len(lstVersions) == 0:
        mess = "Le Zip %s ne contient pas de fichier 'Versions.txt'" % nameFichier
        wx.MessageBox(mess, "Echec", style=wx.ICON_ERROR)
        return
    pathNameVersions = lstVersions[0]
    versions = None
    try:
        versions = UTILS_Fichiers.GetOneFileInZip(releaseZip, pathNameVersions)
        versions = GestionDB.Decod(versions)
    except Exception() as err:
        if isinstance(err, UnicodeDecodeError):
            mess = "Le fichier version importé n'est pas codé en UTF-8\n%s" % err
            wx.MessageBox(mess, "Abandon")
            return
    return pathNameVersions, versions

class CTRL_AfficheVersion(wx.TextCtrl):
    def __init__(self, parent):
        label = "Info dernières versions"
        pos = wx.DefaultPosition
        size = wx.DefaultSize
        style = wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH | wx.TE_DONTWRAP
        wx.TextCtrl.__init__(self, parent, wx.ID_ANY, label, pos, size, style=style)
        self.parent = parent
        self.version_logiciel = self.parent.version_logiciel
        # les deux premiers items affichés sont exprimés en texte comme préfixe
        self.invite = "\nActuellement: Version % s\n" % self.version_logiciel
        self.dbDoc = None
        self.SetParamConnexion("")

        self.tplVersionLogiciel = FonctionsPerso.ConvertVersionTuple(self.version_logiciel)
        self.version_data = self.parent.version_data
        self.zipFile = None
        self.tplVersionData = None
        self.MAJ(self.version_data)

    def MAJ(self,version_choix):
        self.tplVersionData = FonctionsPerso.ConvertVersionTuple(version_choix)
        invite = self.invite
        if not self.zipFile:
            # recherche un zipFile dans documents de la base pointée
            ret = self.GetFileInDocuments(self.tplVersionData)
            if ret != "ok":
                invite += "\nPas de mise à jour trouvée"
                invite += "\n\n%s" % ret
                invite += "\nChoisissez un fichier"
                if "disponible" in invite:
                    invite += ", ou une autre version."
                self.SetValue(invite)
        else:
            nouveautes = self.GetNouveautes(self.zipFile)
            self.SetValue("%sVersions à installer :\n\n%s" % (self.invite, nouveautes))
        self.parent.EnableBoutons()

    def SetParamConnexion(self,paramConnexion):
        self.dbDoc = GestionDB.DB(nomFichier=paramConnexion, suffixe="DOCUMENTS")

    def SetFileInDocuments(self,tplVersion):
        # Copie le fichier zip-release dans la base de donnée
        dbDoc = self.dbDoc
        categorie = "%d.%d"%(tplVersion[0],tplVersion[1])
        dte = UTILS_Dates.DateDDEnDateEng(datetime.date.today())
        lstTplDon = [
            ("categorie",categorie),
            ("niveau",tplVersion[2]),
            ("echelon", tplVersion[3]),
            ("dateImport", dte),
            ("fichier","%s" % self.zipFile),
            ("description","{user:%s}"%dbDoc.UtilisateurActuel())
            ]
        mess = "DLG_Release.SetFileInDocuments"
        return dbDoc.ReqInsert("releases",lstTplDon,retourID=False,MsgBox=mess)

    def GetNouveautes(self,zipFile):
        tplVersions = GetVersionsFromZipFile(zipFile)
        if not tplVersions:
            return
        pathNameVersions, versions = tplVersions
        posF = versions.find(self.version_logiciel) - 8
        if posF == -1:
            posF = min(2000, len(versions))
        nouveautes = versions[:posF].strip()
        posDebut = versions.find("n")
        posFin = versions.find("(", 0, 50)
        version = versions[posDebut + 1:posFin].strip()
        if nouveautes.strip() == "":
            nouveautes = "%s\n Même version !"%version
        return nouveautes

    def ChoixVersion(self):
        # Affiche la liste des releases pour un choix
        lstChoix = self.GetLabelsReleases()
        if len(lstChoix) == 0:
            mess = "Aucune release\n\nDésolé aucune release partagée dans cette base de données!"
            wx.MessageBox(mess,"résultat")
            return
        lstStrChoix = [(str(x),y) for x,y in lstChoix]
        dlg = CTRL_ChoixListe.Dialog(lstStrChoix)
        #listeOriginale=[("Choix1","Texte1"),],LargeurCode=150,LargeurLib=100,colSort=0, minSize=(600, 350),
        #         titre="Faites un choix !", intro="Double Clic sur la réponse souhaitée...")
        ret = dlg.ShowModal()

    @staticmethod
    def GetVersionInTexte(versions):
        # affiche les nouveautés et retourne le no version
        posDebut = versions.find("n")
        posFin = versions.find("(", 0, 50)
        version = versions[posDebut + 1:posFin].strip()
        return version

    def ValidationFile(self,zipFile,nameFichier="???"):
        self.parent.tplVersionChoix = None

        tplVersions = GetVersionsFromZipFile(zipFile,nameFichier)
        if not tplVersions:
            return

        # la release doit contenir l'arborescence à partir de noethys inclus
        pathNameVersions, versions = tplVersions
        if pathNameVersions.split('/')[0] != "noethys":
            mess = "Le fichier zip ne contient pas le répertoire 'noethys' en racine\n\n"
            mess += "Installez manuellement en respectant l'arborescence initiale"
            wx.MessageBox(mess, "Impossible", style=wx.ICON_ERROR)
            return

        # analyse du contenu
        version_choix = self.GetVersionInTexte(versions)
        if len(version_choix.split('.')) != 4:
            mess = "Le fichier version ne commence pas par un numéro de version valide\n\n"
            mess += "Vérifiez le contenu et rectifiez-le éventuellement"
            wx.MessageBox(mess, "Impossible", style=wx.ICON_ERROR)
            return

        tplVersionChoix = FonctionsPerso.ConvertVersionTuple(version_choix)
        if version_choix.split('.')[:3] != self.version_logiciel.split('.')[:3]:
            mess = "Trop de différence entre les versions\n\n"
            mess += "Refaites une installation complète depuis Github NoethysMatthania"
            wx.MessageBox(mess, "Impossible", style=wx.ICON_ERROR)
            return
        if version_choix < self.version_logiciel:
            mess = "Rétropédalage à confirmer\n\n"
            mess += "La %s remontée sera antérieure\nà l'actuelle %s\n\n" % (
                version_choix, self.version_logiciel)
            mess += "Certaines nouvelles modifications pourront rester en place"
            ret = wx.MessageBox(mess, style=wx.YES_NO | wx.ICON_INFORMATION)
            if ret != wx.YES:
                return
        # Enregistrement de la validation
        self.parent.tplVersionChoix = tplVersionChoix
        self.zipFile = zipFile
        self.MAJ(version_choix)
        return "ok"

    def GetFileByChoisir(self):
        # choix d'un fichier et intégration par validation
        def GetNameZipFile():
            # Recherche et sélectionne un fichier release.zip
            wildcard = "Release Noethys (*.zip; *.7z)|*.*"
            intro = "Veuillez sélectionner le fichier contenant la MISE A JOUR DE NOETHYS"
            return UTILS_Fichiers.SelectionFichier(intro, wildcard, verifZip=True)

        nameFichier = GetNameZipFile()
        if not nameFichier:
            return
        try:
            zipFile = UTILS_Fichiers.GetZipFile(nameFichier, "r")
        except Exception as err:
            print(type(err), err)
            return
        self.ValidationFile(zipFile,nameFichier)

    def GetFileInDocuments(self, tplVersion):
        # Ouvre le fichier zip-release de la base de donnée et affiche son contenu
        dbDoc = self.dbDoc
        categorie = "%d.%d"%(tplVersion[0],tplVersion[1])

        lstNumReleases = self.GetNumReleases(dbDoc, categorie)
        trouvee = False
        for no in lstNumReleases:
            if no == tplVersion:
                trouvee = True
        mess = None
        if len(lstNumReleases) == 0:
            mess = "Pas de releases stockées dans cette base pour Noethys '(%s)'"%categorie
        elif not trouvee:
            mess = "La version '%s' n'est pas stockée dans cette base, " % str(tplVersion)
            mess += "d'autres versions sont disponibles"
        if mess:
            return mess
        # La release de la version attendue est présente
        req = """
        SELECT fichier
        FROM releases
        WHERE categorie = %s 
            AND niveau = %d
            AND echelon = %d"""%(categorie,tplVersion[2],tplVersion[3])
        ret = dbDoc.ExecuterReq(req,MsgBox="DLG_Release.GetFileInDocuments")
        if ret != "ok":
            return ret
        recordset = dbDoc.ResultatReq()
        self.zipFile = None
        if len(recordset) == 0:
            return "Fichier de mise à jour n'est pas présent dans la base"
        dataBytes = recordset[0][0]
        fileName = UTILS_Fichiers.GetRepTemp(fichier="release.zip")
        ret = UTILS_Fichiers.SetFileFromBytes(fileName,dataBytes)
        if ret != 'ok':
            mess = "Ecriture impossible du fichier '%s'" % fileName
            mess += "\n%s" % ret
            return mess
        zipFile = UTILS_Fichiers.GetZipFile(fileName)
        return self.ValidationFile(zipFile,"Fichier_partagé")

    @staticmethod
    def GetLabelsReleases(dbDoc, categorie):
        # retrourne la liste des Releases dispo
        req = """
        SELECT categorie, niveau, echelon,description,dateImport
        FROM releases
        ORDER BY categorie desc niveau desc, echelon DESC
        ;""" % categorie
        ret = dbDoc.ExecuterReq(req,MsgBox="DLG_Release.GetLanelsReleases")
        if ret != "ok":
            return []
        lstReleases = []
        recordset = dbDoc.ResultatReq()
        for categorie, niveau, echelon,description,dateImport in recordset:
            a, b = categorie.split(".")
            version = (int(a), int(b),niveau,echelon)
            label =  "(%s) %s" % (str(dateImport),description)
            lstReleases.append((version,label))
        return lstReleases

    @staticmethod
    def GetNumReleases(dbDoc, categorie):
        # retrourne la liste des Releases dispo
        req = """
        SELECT niveau, echelon
        FROM releases
        WHERE categorie = '%s'
        ORDER BY niveau desc, echelon DESC
        ;""" % categorie
        ret = dbDoc.ExecuterReq(req,MsgBox="DLG_Release.GetNumReleases")
        if ret != "ok":
            return []
        recordset = dbDoc.ResultatReq()
        a,b = categorie.split(".")
        tplCategorie = (int(a), int(b))
        lstNumReleases = [ tplCategorie + (x,y) for (x,y) in recordset]
        return lstNumReleases

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
        self.tplVersionChoix = None
        if self.tplVersionData == self.tplVersionLogiciel:
            intro = "Vous pouvez ici mettre à jour votre version Noethys, à partir d'un fichier ZIP contenant la release"
        else:
            intro = "Vous pouvez ici mettre à jour votre version Noethys automatiquement"
        titre ="Mise à jour"
        self.SetTitle(titre)
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/32x32/Restaurer.png")

        # Connexion à la base de donnée
        self.txt_base = wx.StaticBox(self,-1,"Stockage des versions : ")
        lstNomsFichiersDB, self.lstDicParamsDB = self.__getDerniersFichiers()
        self.choice_baseDonnees = wx.Choice(self, -1, choices=lstNomsFichiersDB)
        self.check_maj =     wx.CheckBox(self, -1, "Mettre à jour ma station")
        self.check_stocke =  wx.CheckBox(self, -1, "Stocker pour partager")
        # Boutons
        self.bouton_versions = CTRL_Bouton_image.CTRL(self, texte="Autres Versions", cheminImage="Images/32x32/Droits.png")
        self.bouton_fichier = CTRL_Bouton_image.CTRL(self, texte="Choisir le fichier", cheminImage="Images/32x32/Desarchiver.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte="Ok pour release", cheminImage="Images/32x32/Valider.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte="Annuler", cheminImage="Images/32x32/Annuler.png")

        # Affichage de la version proposée
        self.box_donnees_staticbox = wx.StaticBox(self, -1,"Description des versions :")
        self.ctrl_donnees = CTRL_AfficheVersion(self)
        self.ctrl_donnees.SetMinSize((250, -1))

        self.__set_properties()
        self.__do_layout()
        
        self.Bind(wx.EVT_BUTTON, self.OnBoutonVersions, self.bouton_versions)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonFichier, self.bouton_fichier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)
        self.Bind(wx.EVT_CHOICE, self.OnChoiceBaseDonnees, self.choice_baseDonnees)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheck, self.check_stocke)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheck, self.check_maj)
        self.Bind(wx.EVT_CLOSE, self.OnBoutonAnnuler)

    def __set_properties(self):
        self.choice_baseDonnees.Select(0)
        self.check_maj.SetValue(True)
        self.check_stocke.SetValue(True)
        self.txt_base.SetToolTip(wx.ToolTip("Choix de la base de donnée qui conserve les versions"))
        self.choice_baseDonnees.SetToolTip(wx.ToolTip("Base de donnée qui conserve les différentes versions"))
        self.check_maj.SetToolTip(wx.ToolTip("Pour mettre à jour l'application sur votre station de travail"))
        self.check_stocke.SetToolTip(wx.ToolTip("Pour enregistrer la mise à jour dans la base et qu'elle devienne accessible aux autres stations"))
        self.bouton_versions.SetToolTip(wx.ToolTip("Cliquez ici pour accéder aux versions partagées dans la base de données"))
        self.bouton_fichier.SetToolTip(wx.ToolTip("Cliquez ici pour choisir le fichier release.zip"))
        self.bouton_ok.SetToolTip(wx.ToolTip("Cliquez ici pour lancer la restauration"))
        self.bouton_annuler.SetToolTip(wx.ToolTip("Cliquez ici pour annuler"))
        self.EnableBoutons()
        self.SetMinSize((600, 800))

    @staticmethod
    def __getDerniersFichiers():
        # liste les accès aux bases réseau, génère un dictionnaire de params
        cfg = UTILS_Config.FichierConfig()
        userConfig = cfg.GetDictConfig()
        lstFichiers = userConfig["derniersFichiers"]
        lstNomsFichiersDB = []
        dicParamsDB = {}
        for param in lstFichiers:
            if "[RESEAU]" in param:
                port, hote, user, mdp = param.split(";")
                nomFichier = param[
                             param.index("[RESEAU]")+8:] + " - %s" % hote
                if not nomFichier in lstNomsFichiersDB:
                    lstNomsFichiersDB.append(nomFichier)
                    dicParamsDB[nomFichier] = param
        return lstNomsFichiersDB,dicParamsDB

    @staticmethod
    def GetVersions():
        # retourne les deux versions de l'application et de la base de données
        version_logiciel = FonctionsPerso.GetVersionLogiciel(datee=True)
        version_data =  UTILS_Parametres.Parametres(mode="get",
                                categorie="fichier", nom="version", 
                                valeur=version_logiciel)
        return version_data, version_logiciel

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

    def EnableBoutons(self):
        if self.tplVersionChoix and len(self.tplVersionChoix) == 4:
            ok = True
        else: ok = False
        self.bouton_ok.Enable(ok)
        self.check_maj.Enable(ok)
        self.check_stocke.Enable(ok)
        self.bouton_fichier.Enable(not ok)
        self.choice_baseDonnees.Enable(not ok)
        self.bouton_versions.Enable(not ok)
        # porte dérobée pour dégriser l'accès aux autres versions
        if not self.check_maj.GetValue() and not self.check_stocke.GetValue():
            self.bouton_fichier.Enable(True)
            self.choice_baseDonnees.Enable(True)
            self.bouton_versions.Enable(True)

    def OnCheck(self, event):
        # MAJ de l'affichage de la recherche par défaut
        self.ctrl_donnees.MAJ(self.version_data)
        return

    def OnChoiceBaseDonnees(self, event):
        # MAJ de l'affichage de la recherche par défaut
        ix = self.choice_baseDonnees.GetSelection()
        nomFichierDB = self.choice_baseDonnees.GetString(ix)
        self.ctrl_donnees.SetParamConnexion(self.lstDicParamsDB[nomFichierDB])
        # réinitialise la recherche de releass
        self.ctrl_donnees.zipFile = None
        self.ctrl_donnees.MAJ(self.version_data)
        return

    def OnBoutonVersions(self, event):
        self.ctrl_donnees.ChoixVersion()
        return

    def OnBoutonFichier(self, event):
        self.ctrl_donnees.GetFileByChoisir()
        return

    def OnBoutonAnnuler(self, event):
        self.Quitter(wx.ID_CANCEL)

    def OnBoutonOk(self, event):
        # stockage de la release dans la base pointée
        messStockage = "Pas de stockage"
        i = self.check_stocke.GetValue()
        if self.check_stocke.GetValue():
            ret = self.ctrl_donnees.SetFileInDocuments(self.tplVersionChoix)
            if ret == 'ok':
                messStockage = "Version stockée pour être partagée aux stations"
            else:
                messStockage = "Echec Stockage: \n%s"%ret 
                
        # Mise à jour de la station
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
        mess = "Mise à jour station NON FAITE !!"
        if self.check_maj.GetValue():
            mess = "MAJ Process interrompu !!"
            if self.ctrl_donnees.zipFile:
                self.ctrl_donnees.zipFile.extractall("%s"%pathRoot)
                mess = "Le processus de mise à jour est terminé."

        mess = "Fin d'opération\n\n-\t%s\n-\t%s" % (messStockage, mess)
        # Fin du processus
        dlg = wx.MessageDialog(self,mess, "Release", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

        # Fermeture
        self.Quitter(wx.ID_OK)

    def Quitter(self, IDend = wx.ID_CANCEL):
        self.ctrl_donnees.dbDoc.Close()
        self.EndModal(IDend)

if __name__ == "__main__":
    app = wx.App(0)
    FonctionsPerso.GetPathRoot()
    dialog_1 = Dialog(None,"1.3.1.10","version 1.3.1.10 (15/06/2022)")
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()

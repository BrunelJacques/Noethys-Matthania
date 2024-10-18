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
import UpgradeDB
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

def GetVersionsFromZipFile(releaseZip=None, nomFichier="???"):
    # Cherche le fichier versions dans le fichier zip, retourne le fichier
    if not releaseZip: return
    if not releaseZip.fp:
        nomFichier = releaseZip.filename
        releaseZip = UTILS_Fichiers.GetZipFile(nomFichier)
    lstFichiers = UTILS_Fichiers.GetListeFichiersZip(releaseZip)
    lstVersions = [x for x in lstFichiers if "versions" in x.lower()]
    if len(lstVersions) == 0:
        mess = "Le Zip %s ne contient pas de fichier 'Versions.txt'" % nomFichier
        wx.MessageBox(mess, "Echec", style=wx.ICON_ERROR)
        return
    pathNameVersions = lstVersions[0]
    versions = None
    try:
        with releaseZip as zip:
            versions = UTILS_Fichiers.GetOneFileInZip(zip, pathNameVersions)
        versions = UpgradeDB.Decod(versions)
    except Exception as err:
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
        self.version_data = self.parent.version_data
        self.version_choix = None
        # les deux premiers items affichés sont exprimés en texte comme préfixe
        self.invite = "\nActuellement: Version % s\n" % self.parent.version_logiciel_date
        self.dbDoc, self.dbData = self.SetParamConnexion("")

        self.tplVersionLogiciel = FonctionsPerso.ConvertVersionTuple(self.version_logiciel)
        self.zipFile = None # vient d'un fichier ou de la base (alors non re-stockable)
        self.nomFichier = None # signale un fichier valide - chargé - stockable
        self.tplVersionData = None
        self.MAJ(self.version_data)

    def MAJ(self,version_choix):
        self.tplVersionData = FonctionsPerso.ConvertVersionTuple(version_choix)
        invite = self.invite
        if not self.zipFile:
            # recherche un zipFile dans documents de la base pointée
            ret = self.GetFileInDocuments(self.tplVersionData)
            if ret != wx.ID_OK:
                invite += "\nPas de mise à jour trouvée"
                invite += "\n\n%s" % ret
                invite += "\nChoisissez un fichier"
                if "disponible" in invite:
                    invite += ", ou une autre version."
                self.SetValue(invite)
                version_choix = None
        else:
            nouveautes = self.GetNouveautes(self.zipFile)
            self.SetValue("%sVersions à installer :\n\n%s" % (self.invite, nouveautes))
        self.version_choix = version_choix

    def SetParamConnexion(self,paramConnexion):
        dbDoc = UpgradeDB.DB(nomFichier=paramConnexion, suffixe="DOCUMENTS")
        dbData = UpgradeDB.DB(nomFichier=paramConnexion, suffixe="DATA")
        return dbDoc, dbData

    def UpdateBlobInDocuments(self,ID):
        # Copie le fichier zip-release dans la base de donnée
        try:
            bytesBuffer = UTILS_Fichiers.GetBytesFromFile(self.nomFichier)
            self.dbDoc.MAJimage("releases","IDrelease", ID, bytesBuffer,"fichier")
        except Exception as err:
            return "%s\n%s" % ("DLG_Release.UpdateBlobInDocuments", err)
        return 'ok'

    def StockerInDocuments(self,tplVersion):
        # Crée ou met à jour un record dans documents.releases
        dbDoc = self.dbDoc
        categorie = "%d.%d"%(tplVersion[0],tplVersion[1])
        dte = UTILS_Dates.DateDDEnDateEng(datetime.date.today())
        # composition du cartouche
        lstTplDon = [
            ("categorie",categorie),
            ("niveau",tplVersion[2]),
            ("echelon", tplVersion[3]),
            ("dateImport", dte),
            ("description","'partagé par':'%s'" % dbDoc.UtilisateurActuel())
            ]
        mess = "DLG_Release.StockerInDocuments"

        # Teste l'existence préalable
        ID = self.GetIdRelease(tplVersion)
        ret = 'ok'
        if not ID:
            ID = dbDoc.ReqInsert("releases",lstTplDon,retourID=True,MsgBox=mess)
            if not isinstance(ID,int):
                ret = 'Erreur sur Insert du cartouche'
        else:
            ret = dbDoc.ReqMAJ("releases",lstTplDon, "IDrelease", ID, IDestChaine=False,
                               MsgBox=mess)
        if ret == 'ok':
            ret = self.UpdateBlobInDocuments(ID)
        return ret

    def GetIdRelease(self,tplVersion):
        # retourne l'ID de l'enregistrement document
        categorie = "%d.%d"%(tplVersion[0],tplVersion[1])
        req = """
        SELECT IDrelease
        FROM releases
        WHERE categorie = '%s' AND niveau = %d AND echelon = %d
        ;""" % (categorie, tplVersion[2], tplVersion[3])
        ret = self.dbDoc.ExecuterReq(req)
        if ret != "ok":
            return ret
        recordset = self.dbDoc.ResultatReq()
        ID = None
        if len(recordset) > 0:
            ID = recordset[0][0]
        return ID

    def GetNouveautes(self,zipFile):
        # dans le fichier version, isole les nouveautés à afficher
        tplVersions = GetVersionsFromZipFile(zipFile)
        if not tplVersions:
            self.version_choix = None
            return
        pathNameVersions, versions = tplVersions
        posDebut = versions.find("n")
        posFin = versions.find("(",0,50)
        choixVersion = versions[posDebut + 1:posFin].strip()
        posActu = versions.find(self.version_logiciel) # position de l'actuelle dans l'histo
        # recaler la position de l'ancienne version trouvée dans l'historique
        posActu = versions.find("version",max(0,posActu - 12))
        if posActu < 0 or (choixVersion != self.version_logiciel and posActu < 5):
            posActu = min(2000, len(versions))
            nouveautes = "Version en cours NON TROUVEE\n\nDernières qui seront remontées:\n"
            nouveautes += versions[:posActu].strip()
        elif self.version_logiciel == choixVersion:
            nouveautes = "%s\n Même version !"%choixVersion
        else:
            nouveautes = versions[:posActu].strip()
        return nouveautes

    def ChoixVersion(self):
        # Affiche la liste des releases pour un choix
        lstChoix = self.GetLabelsReleases()
        if len(lstChoix) == 0:
            mess = "Aucune release\n\nDésolé aucune release partagée dans cette base de données!"
            wx.MessageBox(mess,"résultat")
            return
        titre = "Choisissez une version d'application"
        intro = "Double-clic vous permet de choisir une ligne, <B>'SUPPR' pour retirer la version de la base</B>"
        dlg = CTRL_ChoixListe.Dialog(self,lstChoix,titre=titre,intro=intro,
                                     LargeurCode=100)
        dlg.listview.SetSortColumn(0, resortNow=True,ascending=False)
        ret = dlg.ShowModal()
        version_choix = None
        if ret == wx.ID_OK:
            choix = dlg.GetChoix()
            version_choix = choix[0]
        dlg.Destroy()
        if version_choix:
            self.MAJ(version_choix)
        return ret

    @staticmethod
    def GetVersionInTexte(versions):
        # affiche les nouveautés et retourne le no version
        posDebut = versions.find("n")
        posFin = versions.find("(", 0, 50)
        version = versions[posDebut + 1:posFin].strip()
        return version

    def ValidationFile(self,zipFile,nomFichier=None):
        self.parent.tplVersionChoix = None
        self.parent.versionChoix = None
        self.version_choix = None

        tplVersions = GetVersionsFromZipFile(zipFile,nomFichier)
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
        version_logiciel = self.version_logiciel
        if len(version_choix.split('.')) != 4:
            mess = "Le fichier version ne commence pas par un numéro de version valide\n\n"
            mess += "Vérifiez le contenu et rectifiez-le éventuellement"
            wx.MessageBox(mess, "Impossible", style=wx.ICON_ERROR)
            return

        tplVersionChoix = FonctionsPerso.ConvertVersionTuple(version_choix)
        tplVersionLogiciel = FonctionsPerso.ConvertVersionTuple(version_logiciel)

        def cutFinVer(versionStr):
            # coupe le dernier indice du numéro de version (échelon de la version)
            ret = ""
            for x in versionStr.split('.')[:-1]:
                ret += str(x) + "."
            return ret[:-1]

        niveauLogiciel = cutFinVer(version_logiciel)
        niveauChoix = cutFinVer(version_choix)

        # test si on a changé de niveau
        if (FonctionsPerso.NeedMaj(niveauLogiciel, niveauChoix)
                and (tplVersionLogiciel[-1] not in (99,999)
                    or tplVersionLogiciel[-2] != tplVersionChoix[-2]-1)):
            mess = "Trop de différence entre les versions\n\n"
            mess += ("La version à installer est de niveau %s"
                     "\nla votre %s est trop ancienne\n")%(niveauChoix, niveauLogiciel)
            mess += "\nVous pouvez installer d'abord un fichier %s.99 | 999!"%niveauLogiciel
            mess += "\nou refaites l'installation depuis Github NoethysMatthania"
            wx.MessageBox(mess, "Impossible", style=wx.ICON_ERROR)
            return

        # test de version présente plus avancée que les stockées
        if ((not FonctionsPerso.NeedMaj(version_logiciel,version_choix))
                and version_logiciel != version_choix):
            mess = "La version proposée n'est pas postérieure à l'actuelle \n\n"
            mess += "La version à installer est %s \nla votre %s semble plus récente\n\n"%(version_choix, version_logiciel)
            mess += "Vous pouvez installer votre version sur la base de données, via un file.zip!"
            wx.MessageBox(mess, style=wx.OK | wx.ICON_INFORMATION)

        # Ouverture de l'envoi possible
        if version_choix > version_logiciel:
            self.parent.check_maj.SetValue(True)
        else: self.parent.check_maj.SetValue(False)

        # Enregistrement de la validation
        self.parent.tplVersionChoix = tplVersionChoix
        self.version_choix = version_choix

        self.zipFile = zipFile
        self.nomFichier = nomFichier
        self.MAJ(version_choix)
        return wx.ID_OK

    def GetFileByChoisir(self):
        # choix d'un fichier et intégration par validation
        def GetNameZipFile():
            # Recherche et sélectionne un fichier release.zip
            wildcard = "Release Noethys (*.zip; *.7z)|*.*"
            intro = "Veuillez sélectionner le fichier contenant la MISE A JOUR DE NOETHYS"
            return UTILS_Fichiers.SelectionFichier(intro, wildcard, verifZip=True)

        nomFichier = GetNameZipFile()
        if not nomFichier:
            return
        try:
            zipFile = UTILS_Fichiers.GetZipFile(nomFichier, "r")
        except Exception as err:
            print(type(err), err)
            return
        return self.ValidationFile(zipFile,nomFichier)

    def GetFileInDocuments(self, tplVersion):
        # Ouvre le fichier zip-release de la base de donnée et affiche son contenu
        dbDoc = self.dbDoc
        categorie = "%d.%d"%(tplVersion[0],tplVersion[1])

        lstNumReleases = self.GetNumReleases(categorie)
        trouvee = False
        lastVersion = tplVersion
        for no in lstNumReleases:
            if no == tplVersion:
                trouvee = True
            if no > tplVersion and no > lastVersion:
                lastVersion = no
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
        self.nomFichier = None
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
        if isinstance(zipFile,str):
            # un message d'erreur a été retourné
            return zipFile
        return self.ValidationFile(zipFile,None)

    def GetLabelsReleases(self):
        dbDoc = self.dbDoc
        # retourne la liste des Releases dispo
        req = """
        SELECT categorie, niveau, echelon,description,dateImport
        FROM releases
        ORDER BY categorie desc, niveau desc, echelon DESC
        ;"""
        ret = dbDoc.ExecuterReq(req,MsgBox="DLG_Release.GetLabelsReleases")
        if ret != "ok":
            return []
        lstReleases = []
        recordset = dbDoc.ResultatReq()
        for categorie, niveau, echelon,description,dateImport in recordset:
            version = "%s.%d.%d" % (categorie,niveau,echelon)
            label =  "Version %s (%s): %s" % (version,str(dateImport),description.decode())
            lstReleases.append((version,label))
        return lstReleases

    def GetNumReleases(self,categorie=""):
        # retourne la liste des Releases dispo
        dbDoc = self.dbDoc
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

    def OnDeleteChoixListe(self,item):
        # touche delete activée sur un item de choixListe
        version_choix, label = item
        tplVersion = FonctionsPerso.ConvertVersionTuple(version_choix)
        ID = self.GetIdRelease(tplVersion)
        mess = "DLG_Releases.OnDeleteChoixListe"
        ret = self.dbDoc.ReqDEL( nomTable="releases", nomChampID="IDrelease",
                           ID=ID,MsgBox=mess)
        if ret == 'ok':
            return True
        else: return False

    def UpgradeDB(self):
        # mise à jour de la base de donnée
        resultat = self.dbData.UpdateDB(self, self.parent.tplVersionChoix)
        nomFichier = self.dbData.nomFichier
        if resultat == True:
            # Mémorisation de la nouvelle version du fichier
            UTILS_Parametres.Parametres(
                mode="set",
                categorie="fichier",
                nom="version",
                valeur=self.version_choix,
                nomFichier=nomFichier)
            return resultat
        else:
            raise Exception(resultat)

class Dialog(wx.Dialog):
    def __init__(self, parent,version_data=None,version_logiciel_date=None):
        wx.Dialog.__init__(self, parent, -1,
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.majFaite = False
        if not version_data or not version_logiciel_date:
            version_data, version_logiciel_date = self.GetVersions()
        posDeb = version_logiciel_date.find("n") +1
        posFin = version_logiciel_date.find("(")
        version_logiciel = version_logiciel_date[posDeb:posFin].strip()
        self.version_logiciel = version_logiciel
        self.version_logiciel_date = version_logiciel_date
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
        self.box_affiche_staticbox = wx.StaticBox(self, -1,"Description des versions :")
        self.ctrl_affiche = CTRL_AfficheVersion(self)
        self.ctrl_affiche.SetMinSize((250, -1))

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
        if self.version_data <= self.version_logiciel:
            self.check_maj.SetValue(False)
        else:
            self.check_maj.SetValue(True)
        self.check_stocke.SetValue(False)
        self.check_stocke.Enable(False)
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
        
        box_donnees = wx.StaticBoxSizer(self.box_affiche_staticbox, wx.VERTICAL)
        box_donnees.Add(self.ctrl_affiche, 1, wx.ALL|wx.EXPAND, 10)
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
        if not hasattr(self, "ctrl_affiche"):
            return
        versionChoix = self.ctrl_affiche.version_choix
        txt = "Ok release"
        actif = False
        coche = False
        if versionChoix:
            actif = True
            coche = FonctionsPerso.NeedMaj(self.version_logiciel,versionChoix)
            txt = "Ok release\n%s"%versionChoix

        self.bouton_ok.SetTexte(txt)
        self.bouton_ok.Enable(actif)
        self.check_maj.Enable(actif)
        self.check_maj.SetValue(coche)
        self.choice_baseDonnees.Enable(True)
        self.bouton_fichier.Enable(True)

    def OnCheck(self, event):
        return

    def OnChoiceBaseDonnees(self, event):
        # MAJ de l'affichage de la recherche par défaut
        ix = self.choice_baseDonnees.GetSelection()
        nomFichierDB = self.choice_baseDonnees.GetString(ix)
        ctrl = self.ctrl_affiche
        ctrl.dbDoc, ctrl.dbData = ctrl.SetParamConnexion(self.lstDicParamsDB[nomFichierDB])
        # réinitialise la recherche de release
        ctrl.zipFile = None
        ctrl.MAJ(self.version_data)
        if self.choice_baseDonnees.GetSelection() == 0:
            self.bouton_ok.Enable(True)
        elif self.ctrl_affiche.nomFichier:
            self.bouton_ok.Enable(True)
        else:
            self.bouton_ok.Enable(False)
        return

    def OnBoutonVersions(self, event):
        self.ctrl_affiche.zipFile = None
        ret = self.ctrl_affiche.ChoixVersion()
        if ret != wx.ID_OK:
            self.ctrl_affiche.version_choix = None
        self.EnableBoutons()
        return

    def OnBoutonFichier(self, event):
        ret = self.ctrl_affiche.GetFileByChoisir()
        if ret == wx.ID_OK:
            self.check_stocke.Enable(True)
            self.check_stocke.SetValue(True)
        else:
            self.ctrl_affiche.version_choix = None
            self.check_stocke.Enable(False)
            self.check_stocke.SetValue(False)

        self.EnableBoutons()
        return

    def OnBoutonAnnuler(self, event):
        self.Quitter(wx.ID_CANCEL)

    def OnBoutonOk(self, event):
        # stockage de la release dans la base pointée
        messStockage = "Pas de stockage"
        if self.check_stocke.GetValue() and self.ctrl_affiche.nomFichier:
            ret = self.ctrl_affiche.StockerInDocuments(self.tplVersionChoix)
            if ret == 'ok':
                messStockage = "Version stockée pour être partagée aux stations"
                # Mise à jour base de donnée
                mess =  "Faut-il mettre à jour les données"
                dlg = wx.MessageDialog(self, mess, "Confirmation",
                                       wx.YES_NO | wx.YES_DEFAULT | wx.ICON_WARNING)
                reponse = dlg.ShowModal()
                dlg.Destroy()
                if reponse == wx.ID_YES:
                    # Fait la conversion de la base par updateDB
                    info = "Lancement de la conversion de la base"
                    if self.parent:
                        self.parent.SetStatusText(info)
                    print(info)
                    ret = self.ctrl_affiche.UpgradeDB()
                    if ret:

                        messStockage += "\n\nBase à jour: %s" % self.ctrl_affiche.version_choix
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
            if self.ctrl_affiche.zipFile:
                UTILS_Fichiers.ExtractAll(self.ctrl_affiche.zipFile,pathRoot)
                mess = "Le processus de mise à jour est terminé."
                self.majFaite = True
        if self.version_logiciel == self.version_data:
            self.majFaite = True

        mess = "Fin d'opération\n\n-\t%s\n-\t%s" % (messStockage, mess)
        style = wx.OK
        if self.majFaite and self.version_logiciel != self.version_data:
            mess += "\n\nRedémarrage de Noethys pour prendre en compte la version à jour?"
            mess += "\nSans redémarrage les anciens programmes restent chargés."
            style = wx.YES_NO
        # Fin du processus
        dlg = wx.MessageDialog(self,mess, "Release", style | wx.ICON_INFORMATION)
        ret = dlg.ShowModal()
        dlg.Destroy()
        if ret == wx.ID_YES:
            IDfin = wx.ID_OK
        else: IDfin = wx.ID_CANCEL

        # Fermeture
        self.Quitter(IDfin)

    def Quitter(self, IDfin = wx.ID_CANCEL):
        self.ctrl_affiche.dbDoc.Close()
        self.ctrl_affiche.dbData.Close()
        self.EndModal(IDfin)

if __name__ == "__main__":
    app = wx.App(0)
    FonctionsPerso.GetPathRoot()
    dialog_1 = Dialog(None)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()

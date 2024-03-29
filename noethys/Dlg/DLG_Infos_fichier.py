#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys branche Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Bandeau
import wx.lib.agw.hypertreelist as HTL
import datetime
import GestionDB
from Utils import UTILS_Historique
from Utils import UTILS_Dates as ut

def DateComplete(dateDD):
    """ Transforme une date DD en date compl�te : Ex : lundi 15 janvier 2008 """
    listeJours = (_("Lundi"), _("Mardi"), _("Mercredi"), _("Jeudi"), _("Vendredi"), _("Samedi"), _("Dimanche"))
    listeMois = (_("janvier"), _("f�vrier"), _("mars"), _("avril"), _("mai"), _("juin"), _("juillet"), _("ao�t"), _("septembre"), _("octobre"), _("novembre"), _("d�cembre"))
    dateComplete = listeJours[dateDD.weekday()] + " " + str(dateDD.day) + " " + listeMois[dateDD.month-1] + " " + str(dateDD.year)
    return dateComplete

def DateEngEnDateDD(dateEng):
    if dateEng and not isinstance(dateEng,str): dateEng = str(dateEng)
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

# ---------------------------------------------------------------------------------------------------------------------------

class Informations():
    """ R�cup�re les informations sur le fichier """
    def __init__(self):
        self.listeDonnees = []
        self.DB = GestionDB.DB()
        
        # Ajout des items par cat�gorie
        self.listeDonnees.append(self.Categorie_general())
        self.listeDonnees.append(self.Categorie_historique())
        self.listeDonnees.append(self.Categorie_occupation())
        self.listeDonnees.append(self.Categorie_stats())

        self.DB.Close()
    
    def GetInformations(self):
        return self.listeDonnees
    
    def Categorie_general(self):
        nomCategorie = _("G�n�ral")
        listeItems = []
    
        # R�cup�ration du nom du fichier
        nomFichier = self.DB.GetNomFichierDefaut() 
        if "[RESEAU]" in nomFichier :
            nomFichier = nomFichier[nomFichier.index("[RESEAU]"):]
        listeItems.append((_("Nom du fichier"), nomFichier))
        
        # R�cup�ration des param�tres du fichier
        req = """SELECT IDparametre, nom, parametre 
        FROM parametres WHERE categorie='fichier'
        ;"""
        self.DB.ExecuterReq(req,MsgBox="DLG_Infos_fichier")
        listeTemp = self.DB.ResultatReq()
        dictInfos = {}
        for IDparametre, nom, parametre  in listeTemp :
            dictInfos[nom] = parametre
        
        listeItems.append((_("Date de cr�ation"), ut.DateEngFr(dictInfos["date_creation"])))
        listeItems.append((_("Version de fichier"), dictInfos["version"]))
        listeItems.append((_("IDfichier"), dictInfos["IDfichier"]))
        
        # Nbre de tables de donn�es
        listeTables = self.DB.GetListeTables()
        listeItems.append((_("Nombre de tables de donn�es"), str(len(listeTables)+2)))

        # R�cup�ration des variables MySQL
        if "[RESEAU]" in nomFichier:
            req = """SHOW VARIABLES LIKE "version";"""
            self.DB.ExecuterReq(req,MsgBox="DLG_Infos_fichier")
            listeTemp = self.DB.ResultatReq()
            if len(listeTemp) > 0:
                listeItems.append((_("Version MySQL du serveur"), listeTemp[0][1]))
        return nomCategorie, listeItems

    def Categorie_historique(self):
        nomCategorie = _("Historique")
        listeItems = []

        req = """SELECT IDcategorie, COUNT(IDaction) 
        FROM historique
        GROUP BY IDcategorie
        ;"""
        self.DB.ExecuterReq(req)
        listeTemp = self.DB.ResultatReq()

        for IDcategorie, nbreActions in listeTemp:
            if IDcategorie in UTILS_Historique.CATEGORIES:
                labelCategorie = UTILS_Historique.CATEGORIES[IDcategorie]
                listeItems.append((labelCategorie, "%9d" % (nbreActions)))

        return nomCategorie, listeItems

    def Categorie_occupation(self):
        nomCategorie = _("Occupation des tables")
        listeItems = []
        gb = GestionDB.GestionBase()

        listeTemp = gb.GetOccupations()

        for labelTable, occupation in listeTemp :
                listeItems.append((labelTable, "%14.2f Mo"%occupation))

        return nomCategorie, listeItems

    def Categorie_stats(self):
        nomCategorie = _("Statistiques")
        listeItems = []

        def GetQuantite(label="", champID="", table=""):
            req = """SELECT COUNT(%s) FROM %s;""" % (champID, table)
            self.DB.ExecuterReq(req,MsgBox="DLG_Infos_fichier")
            nbre = self.DB.ResultatReq()[0][0]
            listeItems.append((label, str(nbre)))

        # Nbre individus
        GetQuantite(_("Nombre d'individus"), "IDindividu", "individus")

        # Nbre familles
        GetQuantite(_("Nombre de familles"), "IDfamille", "familles")

        # Nbre pieces
        GetQuantite(_("Nombre de matPieces"), "pieIDnumPiece", "matPieces")

        # Nbre lignes de pieces
        GetQuantite(_("Nombre de matPiecesLignes"), "ligIDnumLigne", "matPiecesLignes")

        # Nbre de consommations
        GetQuantite(_("Nombre de consommations"), "IDconso", "consommations")

        # Nbre de prestations
        GetQuantite(_("Nombre de prestations"), "IDprestation", "prestations")

        # Nbre de d�p�ts
        GetQuantite(_("Nombre de d�p�ts bancaires"), "IDdepot", "depots")

        # Nbre de factures
        GetQuantite(_("Nombre de factures"), "IDfacture", "factures")

        # Nbre de r�glements
        GetQuantite(_("Nombre de r�glements"), "IDreglement", "reglements")

        # Nbre de pi�ces
        GetQuantite(_("Nombre de pi�ces"), "pieIDnumPiece", "matPieces")

        # Nbre de lignes de pi�ces
        GetQuantite(_("Nombre de lignes"), "ligIDnumLigne", "matPiecesLignes")

        # Nbre de traces historique
        GetQuantite(_("Lignes dans l'historique"), "IDaction", "historique")

        # Nbre de photos
        DBTemp = GestionDB.DB(suffixe="PHOTOS")
        req = """SELECT COUNT(IDphoto) FROM photos;"""
        DBTemp.ExecuterReq(req,MsgBox="DLG_Infos_fichier")
        donnees = DBTemp.ResultatReq()
        DBTemp.Close()
        if len(donnees) > 0 :
            nbre = donnees[0][0]
        else :
            nbre = "Base non install�e"
        listeItems.append((_("Nombre de photos"), str(nbre)))

        # Nbre de documents scann�s
        DBTemp = GestionDB.DB(suffixe="DOCUMENTS")
        req = """SELECT COUNT(IDdocument) FROM documents;"""
        DBTemp.ExecuterReq(req,MsgBox="DLG_Infos_fichier")
        donnees = DBTemp.ResultatReq()
        DBTemp.Close()
        if len(donnees) > 0 :
            nbre = donnees[0][0]
        else :
            nbre = "Base non install�e"
        listeItems.append((_("Nombre de documents scann�s"), str(nbre)))

        return nomCategorie, listeItems

# --------------------------------------------------------------------------------------------------------------------

class CTRL_Infos(HTL.HyperTreeList):
    def __init__(self, parent): 
        HTL.HyperTreeList.__init__(self, parent, -1)
        self.SetBackgroundColour(wx.WHITE)
        self.SetAGWWindowStyleFlag(HTL.TR_COLUMN_LINES | HTL.TR_NO_HEADER | wx.TR_HIDE_ROOT | wx.TR_FULL_ROW_HIGHLIGHT )
        self.parent = parent
        
        # Adapte taille Police pour Linux
##        from Utils import UTILS_Linux
##        UTILS_Linux.AdaptePolice(self)
        
        self.listeDonnees = []
            
    def MAJ(self, listeDonnees=[]): 
        self.listeDonnees = listeDonnees
                      
        # Cr�ation des colonnes
        self.AddColumn(_("Cat�gorie"))
        self.SetMainColumn(0)
        self.SetColumnWidth(0, 300)
        self.AddColumn(_("Valeur"))
        self.SetColumnWidth(1, 190)
        
        # ImageList
        il = wx.ImageList(16, 16)
        self.img_general = il.Add(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Database.png"), wx.BITMAP_TYPE_PNG))
        self.img_stats = il.Add(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Barres.png"), wx.BITMAP_TYPE_PNG))
        self.img_historique = il.Add(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Historique.png"), wx.BITMAP_TYPE_PNG))
        self.listeImages = [
            self.img_general,
            self.img_historique,
            self.img_general,
            self.img_stats,
            ]
        self.AssignImageList(il)

        # Cr�ation de la racine
        self.root = self.AddRoot(_("Racine"))
        
        # Cr�ation des branches
        numCategorie = 0
        for categorie, listeItems in self.listeDonnees :
            
            # Cr�ation de la cat�gorie
            brancheCategorie = self.AppendItem(self.root, categorie)
            if numCategorie == 0:
                generalite = brancheCategorie
            self.SetItemBold(brancheCategorie, True)
            self.SetItemBackgroundColour(brancheCategorie, wx.Colour(200, 200, 200) )
            self.SetItemTextColour(brancheCategorie, wx.Colour(100, 100, 100) )
            self.SetItemImage(brancheCategorie, self.listeImages[numCategorie], which=wx.TreeItemIcon_Normal)
            
            for label, valeur in listeItems :

                # Cr�ation du label + valeur
                brancheItem = self.AppendItem(brancheCategorie, label)
                self.SetItemText(brancheItem, valeur, 1)
            
            numCategorie+= 1
        
        self.ExpandAllChildren(self.root)

# -------------------------------------------------------------------------------------------------------------------------------------------

class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        
        intro = _("Double clic sur le chapitre � consulter ou � r�duire")
        titre = _("Informations sur la base de donn�es")
        self.SetTitle("DLG_Infos-fichier")
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/32x32/Information.png")
        
        self.ctrl_informations = CTRL_Infos(self)
                
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_fermer = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Fermer"), cheminImage="Images/32x32/Fermer.png")

        self.__set_properties()
        self.__do_layout()
        
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        
        # MAJ liste
        infos = Informations()
        listeDonnees = infos.GetInformations()
        self.ctrl_informations.MAJ(listeDonnees)
        
    def __set_properties(self):
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici pour obtenir de l'aide")))
        self.bouton_fermer.SetToolTip(wx.ToolTip(_("Cliquez ici pour fermer")))
        self.SetMinSize((550, 550))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)
        grid_sizer_base.Add(self.ctrl_informations, 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=3, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_fermer, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()

    def OnBoutonAide(self, event): 
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Informationssurlefichier")

if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dialog_1 = Dialog(None)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()

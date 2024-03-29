#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import datetime
import GestionDB
from dateutil import relativedelta
from Utils import UTILS_Historique
from Ctrl import CTRL_Saisie_date

from Ctrl import CTRL_Pieces_obligatoires
from Ctrl import CTRL_Vignettes_documents
from Utils import UTILS_Dates


class Choix_Piece_autre(wx.Choice):
    def __init__(self, parent, listePiecesObligatoires=[], dictTypesPieces={} ):
        wx.Choice.__init__(self, parent, -1) 
        self.parent = parent
        self.listeNoms = []
        self.listeID = []
        self.listeDonnees = []
        self.listePiecesObligatoires = listePiecesObligatoires
        self.dictTypesPieces = dictTypesPieces
        self.SetListeDonnees() 
    
    def SetListeDonnees(self):
        self.listeNoms = []
        self.listeID = []
        self.listeDonnees = []
        
        # Si on vient d'une fiche INDIVIDU :
        if self.parent.IDindividu != None :
            IDindividu = self.parent.IDindividu
            
            if self.parent.dictFamillesRattachees != None :
                
                # S'il y a une seule famille rattach�e :
                if len(self.parent.dictFamillesRattachees) == 1 :
                    IDfamille = list(self.parent.dictFamillesRattachees.keys())[0]
                    for IDtype_piece, dictTypePiece in self.dictTypesPieces.items() :
                        nomPiece = dictTypePiece["nom"]
                        public = dictTypePiece["public"]
                        if public == "famille" : 
                            IDindividuTmp = None
                        else:
                            IDindividuTmp = IDindividu
                        if (IDfamille, IDtype_piece, IDindividuTmp) not in self.listePiecesObligatoires :
                            self.listeNoms.append(nomPiece)
                            self.listeID.append(IDtype_piece)
                            self.listeDonnees.append( {"IDfamille":IDfamille, "IDtype_piece":IDtype_piece, "IDindividu":IDindividuTmp, "nomPiece":nomPiece} )
                        
                else:
                    # S'il y a plusieurs familles rattach�es :
                    for IDtype_piece, dictTypePiece in self.dictTypesPieces.items() :
                        nomPiece = dictTypePiece["nom"]
                        public = dictTypePiece["public"]
                        if public == "famille" : 
                            IDindividuTmp = None
                        else:
                            IDindividuTmp = IDindividu
                        for IDfamille, dictFamille in self.parent.dictFamillesRattachees.items() :
                            nomTitulaires = dictFamille["nomsTitulaires"]
                            if (IDfamille, IDtype_piece, IDindividuTmp) not in self.listePiecesObligatoires :
                                self.listeNoms.append( _("%s (Famille de %s)") % (nomPiece, nomTitulaires))
                                self.listeID.append(IDtype_piece)
                                self.listeDonnees.append( {"IDfamille":IDfamille, "IDtype_piece":IDtype_piece, "IDindividu":IDindividuTmp, "nomPiece":nomPiece} )
                    
                
        # Si on vient d'une fiche famille
        else:
            
            # R�cup�ration de tous les membres de la famille
            DB = GestionDB.DB()
            req = """SELECT IDrattachement, rattachements.IDindividu, rattachements.IDfamille, IDcategorie, titulaire, nom, prenom
            FROM rattachements 
            LEFT JOIN individus ON individus.IDindividu = rattachements.IDindividu
            WHERE IDfamille=%d
            ORDER BY nom, prenom;""" % self.parent.IDfamille
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            listeMembres = DB.ResultatReq()
            DB.Close()
            
            for IDtype_piece, dictTypePiece in self.dictTypesPieces.items() :
                nomPiece = dictTypePiece["nom"]
                public = dictTypePiece["public"]
                if public == "famille" :
                    if (self.parent.IDfamille, IDtype_piece, None) not in self.listePiecesObligatoires :
                        self.listeNoms.append(nomPiece)
                        self.listeID.append(IDtype_piece)
                        self.listeDonnees.append( {"IDfamille":self.parent.IDfamille, "IDtype_piece":IDtype_piece, "IDindividu":None, "nomPiece":nomPiece} )
                else:
                    for IDrattachement, IDindividu, IDfamille, IDcategorie, titulaire, nom, prenom in listeMembres :
                        if (IDfamille, IDtype_piece, IDindividu) not in self.listePiecesObligatoires :
                            self.listeNoms.append( _("% s de %s") % (nomPiece, prenom) )
                            self.listeID.append(IDtype_piece)
                            self.listeDonnees.append( {"IDfamille":IDfamille, "IDtype_piece":IDtype_piece, "IDindividu":IDindividu, "nomPiece":nomPiece} )
        
        # Remplissage du contr�le
        self.SetItems(self.listeNoms)
    
    def SetID(self, ID=None):
        index = 0
        for IDcompte in self.listeID :
            if IDcompte == ID :
                 self.SetSelection(index)
            index += 1
    
    def SelectPiece(self, IDfamille=None, IDtype_piece=None, IDindividu=None):
        index = 0
        for dictPiece in self.listeDonnees :
            if dictPiece["IDfamille"] == IDfamille and dictPiece["IDtype_piece"] == IDtype_piece and dictPiece["IDindividu"] == IDindividu :
                self.Select(index)
                return True
            index += 1
        return False

    def GetID(self):
        index = self.GetSelection()
        if index == -1 : return None
        return self.listeID[index]
    
    def GetDonneesSelection(self):
        index = self.GetSelection()
        if index == -1 : return None
        return self.listeDonnees[index]

# ------------------------------------------------------------------------------------------------------------------------------------------

class Dialog(wx.Dialog):
    def __init__(self, parent, IDpiece=None, IDfamille=None, IDindividu=None, dictFamillesRattachees={}):
        wx.Dialog.__init__(self, parent, -1, name="DLG_Saisie_piece", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.IDpiece = IDpiece
        self.IDfamille = IDfamille
        self.IDindividu = IDindividu
        self.dictFamillesRattachees = dictFamillesRattachees
        
        # R�cup�re les types de pi�ces existants
        self.dictTypesPieces = self.Importation_types_pieces() 
        
        # Liste des pi�ces
        self.sizer_type_staticbox = wx.StaticBox(self, -1, _("Type de pi�ce"))
        if IDfamille != None :
            texte = _("la famille")
        else:
            texte = _("l'individu")
        self.radio_pieces_1 = wx.RadioButton(self, -1, _("Dans la liste des pi�ces que %s doit fournir :") % texte, style = wx.RB_GROUP)
        self.ctrl_pieces_obligatoires = CTRL_Pieces_obligatoires.CTRL(self, IDfamille=IDfamille, IDindividu=IDindividu, dictFamillesRattachees=dictFamillesRattachees, size=(-1, 200))
        self.ctrl_pieces_obligatoires.SetMinSize((-1, 90))
        self.ctrl_pieces_obligatoires.MAJ() 
        self.listePiecesObligatoires = self.ctrl_pieces_obligatoires.GetlistePiecesObligatoires()
        
        # Types de pi�ces autres
        self.radio_pieces_2 = wx.RadioButton(self, -1, _("Dans la liste des autres types de pi�ces pr�d�finis :"))
        self.ctrl_pieces_autres = Choix_Piece_autre(self, self.listePiecesObligatoires, self.dictTypesPieces)

        # Un type de pi�ce libre
        self.radio_pieces_3 = wx.RadioButton(self, -1, _("Un autre type de pi�ce :"))
        self.label_titre_piece = wx.StaticText(self, -1, "Titre :")
        self.ctrl_titre_piece = wx.TextCtrl(self, -1, "")

        # Date de d�but
        self.sizer_date_debut_staticbox = wx.StaticBox(self, -1, _("Date de d�but"))
        self.label_date_debut = wx.StaticText(self, -1, "Date :")
        self.ctrl_date_debut = CTRL_Saisie_date.Date(self)
        
        # Date de fin
        self.sizer_date_fin_staticbox = wx.StaticBox(self, -1, _("Date de fin"))
        self.radio_date_fin_1 = wx.RadioButton(self, -1, _("Date :"), style = wx.RB_GROUP)
        self.radio_date_fin_2 = wx.RadioButton(self, -1, _("Validit� illimit�e"))
        self.ctrl_date_fin = CTRL_Saisie_date.Date(self)
        
        # Pages captur�es
        self.sizer_pages_staticbox = wx.StaticBox(self, -1, _("Documents associ�s"))
        self.ctrl_pages = CTRL_Vignettes_documents.CTRL(self, type_donnee="piece", IDpiece=self.IDpiece, style=wx.BORDER_SUNKEN)
        self.bouton_ajouter_page = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_supprimer_page = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_visualiser_page = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Loupe.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_zoom_plus = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Zoom_plus.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_zoom_moins = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Zoom_moins.png"), wx.BITMAP_TYPE_ANY))
        
        # Commandes
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ok"), cheminImage="Images/32x32/Valider.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Annuler"), cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()

        # Init contr�les
        self.ctrl_pieces_autres.Enable(False)
        self.ctrl_titre_piece.Enable(False)

        # Si Modification -> importation des donn�es
        if IDpiece == None :
            self.SetTitle(_("Saisie d'une pi�ce"))
            self.ctrl_date_debut.SetDate(datetime.date.today())
        else:
            self.SetTitle(_("Modification d'une pi�ce"))
            self.Importation()

        # Binds
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioPieces, self.radio_pieces_1)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioPieces, self.radio_pieces_2)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioPieces, self.radio_pieces_3)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioDateFin, self.radio_date_fin_1)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioDateFin, self.radio_date_fin_2)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_TEXT, self.OnDateDebut, self.ctrl_date_debut)
        self.Bind(wx.EVT_CHOICE, self.OnChoixAutres, self.ctrl_pieces_autres)
        self.Bind(wx.EVT_BUTTON, self.ctrl_pages.AjouterPage, self.bouton_ajouter_page)
        self.Bind(wx.EVT_BUTTON, self.ctrl_pages.SupprimerPage, self.bouton_supprimer_page)
        self.Bind(wx.EVT_BUTTON, self.ctrl_pages.VisualiserPage, self.bouton_visualiser_page)
        self.Bind(wx.EVT_BUTTON, self.ctrl_pages.ZoomPlus, self.bouton_zoom_plus)
        self.Bind(wx.EVT_BUTTON, self.ctrl_pages.ZoomMoins, self.bouton_zoom_moins)

    def __set_properties(self):
        self.radio_pieces_1.SetValue(1)
        self.radio_pieces_2.SetToolTip(wx.ToolTip(_("Cliquez ici si la pi�ce que vous souhaitez enregistrer n'est pas dans la liste des pi�ces obligatoires � fournir")))
        self.radio_pieces_3.SetToolTip(wx.ToolTip(_("Cliquez ici si la pi�ce que vous souhaitez enregistrer n'est pas un type de pi�ce pr�d�fini")))
        self.ctrl_titre_piece.SetToolTip(wx.ToolTip(_("Saisissez un titre pour cette pi�ce")))
        self.ctrl_pieces_obligatoires.SetToolTip(wx.ToolTip(_("S�lectionnez un type de pi�ce en cliquant sur son nom")))
        self.ctrl_date_debut.SetToolTip(wx.ToolTip(_("Saisissez la date de d�but de validit�.\nRemarque : Il s'agit bien de la date d'emission de la pi�ce \n(par exemple, la date d'obtention d'un dipl�me) et non la date � laquelle vous avez re�ue la pi�ce")))
        self.ctrl_date_fin.SetToolTip(wx.ToolTip(_("Saisissez la date d'expiration de la pi�ce")))
        self.radio_date_fin_1.SetToolTip(wx.ToolTip(_("Cliquez ici si la pi�ce a une dur�e de validit� limit�e dans le temps")))
        self.radio_date_fin_2.SetToolTip(wx.ToolTip(_("Cliquez ici si la pi�ce que vous souhaitez enregistrer a une dur�e de validit� illimit�e")))
        self.bouton_ajouter_page.SetToolTip(wx.ToolTip(_("Cliquez ici pour ajouter un document")))
        self.bouton_supprimer_page.SetToolTip(wx.ToolTip(_("Cliquez ici pour supprimer le document s�lectionn�")))
        self.bouton_visualiser_page.SetToolTip(wx.ToolTip(_("Cliquez ici pour visualiser le document s�lectionn�")))
        self.bouton_zoom_plus.SetToolTip(wx.ToolTip(_("Cliquez ici pour agrandir les vignettes")))
        self.bouton_zoom_moins.SetToolTip(wx.ToolTip(_("Cliquez ici pour r�duire les vignettes")))
        self.SetMinSize((640, 500)) 
        
    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=10, hgap=10)
        
        grid_sizer_contenu = wx.FlexGridSizer(rows=1, cols=2, vgap=10, hgap=10)
        
        grid_sizer_gauche = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        
        sizer_type = wx.StaticBoxSizer(self.sizer_type_staticbox, wx.VERTICAL)
        grid_sizer_3 = wx.FlexGridSizer(rows=6, cols=1, vgap=10, hgap=10)
        grid_sizer_3.Add(self.radio_pieces_1, 0, 0, 0)
        grid_sizer_3.Add(self.ctrl_pieces_obligatoires, 1, wx.LEFT|wx.EXPAND, 17)
        grid_sizer_3.Add(self.radio_pieces_2, 0, 0, 0)
        grid_sizer_3.Add(self.ctrl_pieces_autres, 0, wx.LEFT|wx.EXPAND, 17)
        grid_sizer_3.Add(self.radio_pieces_3, 0, 0, 0)

        grid_sizer_titre = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_titre.Add(self.label_titre_piece, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_titre.Add(self.ctrl_titre_piece, 0, wx.EXPAND)
        grid_sizer_titre.AddGrowableCol(1)
        grid_sizer_3.Add(grid_sizer_titre, 0, wx.LEFT|wx.EXPAND, 17)

        grid_sizer_3.AddGrowableRow(1)
        grid_sizer_3.AddGrowableCol(0)
        sizer_type.Add(grid_sizer_3, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_gauche.Add(sizer_type, 1, wx.EXPAND, 10)
        
        # Dates
        sizer_date_debut = wx.StaticBoxSizer(self.sizer_date_debut_staticbox, wx.VERTICAL)
        grid_sizer_date_debut = wx.FlexGridSizer(rows=1, cols=2, vgap=10, hgap=10)
        sizer_date_fin = wx.StaticBoxSizer(self.sizer_date_fin_staticbox, wx.VERTICAL)
        grid_sizer_date_fin_1 = wx.FlexGridSizer(rows=2, cols=1, vgap=10, hgap=10)
        grid_sizer_date_fin_2 = wx.FlexGridSizer(rows=1, cols=2, vgap=10, hgap=10)
        grid_sizer_dates = wx.FlexGridSizer(rows=1, cols=2, vgap=10, hgap=10)
        grid_sizer_date_debut.Add(self.label_date_debut, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_date_debut.Add(self.ctrl_date_debut, 0, 0, 0)
        sizer_date_debut.Add(grid_sizer_date_debut, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_dates.Add(sizer_date_debut, 1, wx.EXPAND, 0)
        grid_sizer_date_fin_2.Add(self.radio_date_fin_1, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_date_fin_2.Add(self.ctrl_date_fin, 0, 0, 0)
        grid_sizer_date_fin_1.Add(grid_sizer_date_fin_2, 1, wx.EXPAND, 0)
        grid_sizer_date_fin_1.Add(self.radio_date_fin_2, 0, 0, 0)
        sizer_date_fin.Add(grid_sizer_date_fin_1, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_dates.Add(sizer_date_fin, 1, wx.EXPAND, 0)
        grid_sizer_dates.AddGrowableCol(0)
        grid_sizer_dates.AddGrowableCol(1)
        grid_sizer_gauche.Add(grid_sizer_dates, 1, wx.EXPAND, 10)
        
        grid_sizer_gauche.AddGrowableRow(0)
        grid_sizer_gauche.AddGrowableCol(0)
        grid_sizer_contenu.Add(grid_sizer_gauche, 1, wx.EXPAND, 0)
        
        # Pages
        sizer_pages = wx.StaticBoxSizer(self.sizer_pages_staticbox, wx.VERTICAL)
        
        grid_sizer_pages = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        
        grid_sizer_pages.Add(self.ctrl_pages, 0, wx.EXPAND, 0)
        grid_sizer_pages.AddGrowableRow(0)
        grid_sizer_pages.AddGrowableCol(0)
        
        grid_sizer_commandes_pages = wx.FlexGridSizer(rows=7, cols=1, vgap=5, hgap=5)
        grid_sizer_commandes_pages.Add(self.bouton_ajouter_page, 0, 0, 0)
        grid_sizer_commandes_pages.Add(self.bouton_supprimer_page, 0, 0, 0)
        grid_sizer_commandes_pages.Add( (10, 10), 0, 0, 0)
        grid_sizer_commandes_pages.Add(self.bouton_visualiser_page, 0, 0, 0)
        grid_sizer_commandes_pages.Add( (10, 10), 0, 0, 0)
        grid_sizer_commandes_pages.Add(self.bouton_zoom_plus, 0, 0, 0)
        grid_sizer_commandes_pages.Add(self.bouton_zoom_moins, 0, 0, 0)
        grid_sizer_pages.Add(grid_sizer_commandes_pages, 1, wx.EXPAND, 0)
        
        sizer_pages.Add(grid_sizer_pages, 1, wx.ALL|wx.EXPAND, 10)
        
        grid_sizer_contenu.Add(sizer_pages, 1, wx.EXPAND, 0)
        grid_sizer_contenu.AddGrowableRow(0)
        grid_sizer_contenu.AddGrowableCol(1)
        
        grid_sizer_base.Add(grid_sizer_contenu, 1, wx.ALL|wx.EXPAND, 10)
        
        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((15, 15), 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(0)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen() 
    
    def Importation_types_pieces(self):
        dictTypesPieces = {}
        DB = GestionDB.DB()
        req = """SELECT IDtype_piece, nom, public, duree_validite, valide_rattachement
        FROM types_pieces 
        ORDER BY nom;"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        for IDtype_piece, nom, public, duree_validite, valide_rattachement in listeDonnees :
            dictTypesPieces[IDtype_piece] = {"nom" : nom, "public" : public, "duree_validite" : duree_validite, "valide_rattachement" : valide_rattachement}
        return dictTypesPieces
    
    def SelectPiece(self, IDfamille=None, IDtype_piece=None, IDindividu=None):
        self.ctrl_pieces_obligatoires.SelectPiece(IDfamille, IDtype_piece, IDindividu)
        if self.CalcValiditeDefaut() == False :
            # Mets le focus sur la date de d�but
            self.ctrl_date_debut.SetFocus()
    
    def OnSelectionPieceObligatoire(self, donnees):
        # Si une date de d�but a d�j� �t� saisie, on proc�de � la recherche de la date de fin par d�faut
        if self.CalcValiditeDefaut() == False :
            # Mets le focus sur la date de d�but
            self.ctrl_date_debut.SetFocus()
        
    def OnChoixAutres(self, event):
        IDtype_piece = self.ctrl_pieces_autres.GetID()
        if IDtype_piece == None : return
        # Si une date de d�but a d�j� �t� saisie, on proc�de � la recherche de la date de fin par d�faut
        if self.CalcValiditeDefaut() == False :
            # Mets le focus sur la date de d�but
            self.ctrl_date_debut.SetFocus()
        self.ctrl_pieces_obligatoires.Unselect() 

    def OnRadioPieces(self, event):
        self.ctrl_pieces_autres.Enable(self.radio_pieces_2.GetValue())
        self.ctrl_pieces_obligatoires.Enable(self.radio_pieces_1.GetValue())
        self.ctrl_titre_piece.Enable(self.radio_pieces_3.GetValue())
        if not self.radio_pieces_1.GetValue():
            self.ctrl_pieces_obligatoires.Unselect()

    def OnRadioDateFin(self, event):
        if self.radio_date_fin_1.GetValue() == True:
            self.ctrl_date_fin.Enable(True)
        else:
            self.ctrl_date_fin.Enable(False)
        
    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Pices")
    
    def GetSelectionPiece(self):
        if self.radio_pieces_1.GetValue() == True :
            donnees = self.ctrl_pieces_obligatoires.GetDonneesSelection() 
            if donnees == None :
                return None
            if donnees["type"] == "famille" :
                return
            if donnees["type"] == "piece" :
                IDtype_piece = donnees["IDtype_piece"]
                IDindividu = donnees["IDindividu"]
                IDfamille = donnees["IDfamille"]
                nomPiece = donnees["nomPiece"]
        elif self.radio_pieces_2.GetValue() == True:
            donnees = self.ctrl_pieces_autres.GetDonneesSelection() 
            if donnees == None :
                return None
            IDtype_piece = donnees["IDtype_piece"]
            IDindividu = donnees["IDindividu"]
            IDfamille = donnees["IDfamille"]
            nomPiece = donnees["nomPiece"]
        elif self.radio_pieces_3.GetValue() == True:
            IDfamille = self.IDfamille
            IDtype_piece = None
            IDindividu = None
            nomPiece = None
        return { "IDfamille":IDfamille, "IDtype_piece":IDtype_piece, "IDindividu":IDindividu, "nomPiece":nomPiece}
            

    def OnDateDebut(self, event):
        texte = self.ctrl_date_debut.GetValue()
        for caract in texte:
            if caract == " ":
                return
        self.CalcValiditeDefaut()
        event.Skip()

    def CalcValiditeDefaut(self):
        dateDebut = self.ctrl_date_debut.GetValue()

        if dateDebut == "  /  /    ":
            return False

        # R�cup�ration des donn�es sur la pi�ces
        selection = self.GetSelectionPiece()
        if selection == None : return
        
        # Validation de la date de d�but
        validation = self.ctrl_date_debut.FonctionValiderDate()
        if validation == False:
            self.ctrl_date_debut.SetFocus()
            return

        # Recherche de la dur�e de validit� par d�faut de la pi�ce
        IDtype_piece = selection["IDtype_piece"]
        if IDtype_piece in self.dictTypesPieces :
            validite = self.dictTypesPieces[IDtype_piece]["duree_validite"]
        else :
            validite = None
        
        # Si illimit�
        if validite == None or validite == "j0-m0-a0" : 
            dateFin = "2999-01-01"
            self.radio_date_fin_2.SetValue(1)
            self.ctrl_date_fin.Enable(False)
            self.bouton_ok.SetFocus()
        
        # Si dur�e limit�e
        elif validite != None and validite.startswith("j") :
            posM = validite.find("m")
            posA = validite.find("a")
            jours = int(validite[1:posM-1])
            mois = int(validite[posM+1:posA-1])
            annees = int(validite[posA+1:])
        
            dateJour = int(dateDebut[:2])
            dateMois = int(dateDebut[3:5])
            dateAnnee = int(dateDebut[6:10])
            dateDebut = datetime.date(dateAnnee, dateMois, dateJour)

            # Calcul de la date de fin de validit�
            dateFin = dateDebut
            if jours != 0 : dateFin = dateFin + relativedelta.relativedelta(days=+jours)
            if mois != 0 : dateFin = dateFin + relativedelta.relativedelta(months=+mois)
            if annees != 0 : dateFin = dateFin + relativedelta.relativedelta(years=+annees)

            # Insertion de la date dans la case Date_Fin
            dateFinale = str(dateFin)
            dateFinale = dateFinale[8:10] + "/" + dateFinale[5:7] + "/" + dateFinale[:4]
            self.ctrl_date_fin.SetValue(dateFinale)

            # Mets le focus sur la date de fin
            self.radio_date_fin_1.SetValue(1)
            self.ctrl_date_fin.Enable(True)
            self.bouton_ok.SetFocus()
        
        # Date Max
        elif validite != None and validite.startswith("d") :
            date_fin = UTILS_Dates.DateEngFr(validite[1:])
            self.ctrl_date_fin.SetValue(date_fin)
            self.radio_date_fin_1.SetValue(1)
            self.ctrl_date_fin.Enable(True)
            self.bouton_ok.SetFocus()

    def GetIDpiece(self):
        return self.IDpiece

    def Importation(self):
        """ Importation des donnees de la base """
        DB = GestionDB.DB()
        req = """SELECT pieces.IDtype_piece, IDindividu, IDfamille, date_debut, date_fin, public, titre
        FROM pieces 
        LEFT JOIN types_pieces ON types_pieces.IDtype_piece = pieces.IDtype_piece
        WHERE IDpiece=%d;""" % self.IDpiece
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if len(listeDonnees) == 0 : return
        IDtype_piece, IDindividu, IDfamille, date_debut, date_fin, public, titre = listeDonnees[0]
        if public == "famille" : IDindividu = None

        self.SetValeurs(IDfamille, IDtype_piece, IDindividu, titre)

        # Insertion de la date de d�but
        self.ctrl_date_debut.SetDate(date_debut)

        # Insertion de la date de fin
        if date_fin == "2999-01-01":
            self.radio_date_fin_2.SetValue(True)
            self.ctrl_date_fin.Enable(False)
        else:
            self.radio_date_fin_1.SetValue(True)
            self.ctrl_date_fin.Enable(True)
            self.ctrl_date_fin.SetDate(date_fin)

    def SetValeurs(self, IDfamille=None, IDtype_piece=None, IDindividu=None, titre=None):
        # S�lection de la pi�ce dans les pi�ces obligatoires
        resultat = self.ctrl_pieces_obligatoires.SelectPiece(IDfamille, IDtype_piece, IDindividu)
        self.radio_pieces_1.SetValue(True)

        # S�lection de la pi�ce dans les pi�ces pr�d�finies
        if not resultat:
            self.ctrl_pieces_autres.SelectPiece(IDfamille, IDtype_piece, IDindividu)
            self.radio_pieces_2.SetValue(True)

        # Si autre type de pi�ce
        if not IDtype_piece:
            self.radio_pieces_3.SetValue(True)
            if titre:
                self.ctrl_titre_piece.SetValue(titre)

        self.OnRadioPieces(None)

    def Sauvegarde(self):
        # V�rification des donn�es saisies
        selection = self.GetSelectionPiece()
        if selection == None:
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucun type de pi�ce !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        # Validation de la date de d�but
        if self.ctrl_date_debut.FonctionValiderDate() == False or self.ctrl_date_debut.GetDate() == None:
            dlg = wx.MessageDialog(self, _("Vous devez saisir une date de d�but valide !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_date_debut.SetFocus()
            return False

        if self.radio_date_fin_1.GetValue() == True:
            if self.ctrl_date_fin.FonctionValiderDate() == False or self.ctrl_date_fin.GetDate() == None:
                dlg = wx.MessageDialog(self, _("Vous devez saisir une date de fin valide !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                self.ctrl_date_fin.SetFocus()
                return False

        # V�rifie que la date de fin est sup�rieure � la date de d�but
        if self.radio_date_fin_1.GetValue() == True:
            if self.ctrl_date_debut.GetDate() > self.ctrl_date_fin.GetDate():
                dlg = wx.MessageDialog(self, _("Attention, la date de d�but est sup�rieure � la date de fin !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                self.ctrl_date_fin.SetFocus()
                return False

        # V�rifie que le titre a �t� saisi
        titre = None
        if self.radio_pieces_3.GetValue() == True:
            titre = self.ctrl_titre_piece.GetValue()
            if not titre:
                dlg = wx.MessageDialog(self, _("Vous devez obligatoirement saisir un titre pour cette pi�ce !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                self.ctrl_titre_piece.SetFocus()
                return False

        # Sauvegarde
        IDtype_piece = selection["IDtype_piece"]
        IDindividu = selection["IDindividu"]
        IDfamille = selection["IDfamille"]
        date_debut = str(self.ctrl_date_debut.GetDate())
        if self.radio_date_fin_1.GetValue() == True:
            date_fin = str(self.ctrl_date_fin.GetDate())
        else:
            date_fin = "2999-01-01"

        DB = GestionDB.DB()
        listeDonnees = [
            ("IDtype_piece", IDtype_piece),
            ("IDindividu", IDindividu),
            ("IDfamille", IDfamille),
            ("date_debut", date_debut),
            ("date_fin", date_fin),
            ("titre", titre),
        ]
        if self.IDpiece == None:
            nouvellePiece = True
            self.IDpiece = DB.ReqInsert("pieces", listeDonnees)
        else:
            nouvellePiece = False
            DB.ReqMAJ("pieces", listeDonnees, "IDpiece", self.IDpiece)
        DB.Close()

        # M�morise l'action dans l'historique
        if nouvellePiece == True:
            type = _("Saisie")
            IDcategorie = 15
        else:
            type = _("Modification")
            IDcategorie = 16
        if IDindividu != None and IDfamille != None:
            texteDetail = _("pour l'individu ID%d et la famille ID%d") % (IDindividu, IDfamille)
        elif IDindividu == None and IDfamille != None:
            texteDetail = _("pour la famille ID%d") % IDfamille
        elif IDindividu != None and IDfamille == None:
            texteDetail = _("pour l'individu ID%d") % IDindividu
        else:
            texteDetail = ""
        nomPiece = selection["nomPiece"]
        UTILS_Historique.InsertActions([{
            "IDindividu": IDindividu,
            "IDfamille": self.IDfamille,
            "IDcategorie": IDcategorie,
            "action": _("%s de la pi�ce ID%d '%s' %s") % (type, self.IDpiece, nomPiece, texteDetail),
        }, ])

        # Sauvegarde des pages scann�es
        self.ctrl_pages.Sauvegarde(self.IDpiece)

        return True

    def OnBoutonOk(self, event):
        """ Bouton Ok """
        if self.Sauvegarde() == False :
            return

        # Fermeture
        self.EndModal(wx.ID_OK)


if __name__ == "__main__":
    app = wx.App(0)
    dialog_1 = Dialog(None, IDpiece=18, IDindividu=None, IDfamille=7)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()

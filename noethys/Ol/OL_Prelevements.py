#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-13 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import datetime
import decimal
import GestionDB
from Utils import UTILS_Dates
from Dlg import DLG_Saisie_prelevement
from Dlg import DLG_Saisie_prelevement_sepa
from Utils import UTILS_Identification
from Utils import UTILS_Prelevements
from Utils import UTILS_Mandats
import wx.lib.dialogs as dialogs

from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "�")


from Utils import UTILS_Interface
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils

from Utils import UTILS_Titulaires

DICT_BANQUES = {}




class Track(object):
    def __init__(self, donnees, dictTitulaires):
        self.dictTitulaires = dictTitulaires
        self.IDprelevement = donnees["IDprelevement"]
        self.IDlot = donnees["IDlot"]
        self.IDfamille = donnees["IDfamille"]
        self.IDcompte_payeur = donnees["IDcompte_payeur"]

        self.prelevement_banque = donnees["prelevement_banque"]
        self.prelevement_iban =  donnees["prelevement_iban"]
        self.prelevement_bic =  donnees["prelevement_bic"]
        
        self.IDmandat = donnees["IDmandat"]
        self.prelevement_reference_mandat =  donnees["prelevement_reference_mandat"]
        self.prelevement_date_mandat =  donnees["prelevement_date_mandat"]
        self.sequence = donnees["sequence"]
        
        self.titulaire = donnees["titulaire"]
        self.type = donnees["type"]
        self.IDfacture = donnees["IDfacture"]
        self.libelle = donnees["libelle"]
        self.montant = donnees["montant"]
        self.statut = donnees["statut"]
        
        self.MAJnomBanque()
        
        self.titulaires = ""
        self.InitNomsTitulaires() 
        
        self.IDreglement = donnees["IDreglement"]
        if self.IDreglement == None :
            self.reglement = False
        else :
            self.reglement = True
        self.dateReglement = donnees["dateReglement"]
        self.IDdepot = donnees["IDdepot"]
        
        # Lot de pr�l�vements
        self.dateLot = donnees["dateLot"]
        self.nomLot = donnees["nomLot"]
            

    def InitNomsTitulaires(self):
        if self.IDfamille != None :
            self.titulaires = self.dictTitulaires[self.IDfamille]["titulairesSansCivilite"]
    
    def MAJnomBanque(self):
        if self.prelevement_banque in DICT_BANQUES :
            self.nomBanque = DICT_BANQUES[self.prelevement_banque]
        else :
            self.nomBanque = ""




    
class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        # R�cup�ration des param�tres perso
        self.IDfamille = kwds.pop("IDfamille", None)
        self.IDmandat = kwds.pop("IDmandat", None)
        self.selectionID = None
        self.selectionTrack = None
        self.criteres = ""
        self.itemSelected = False
        self.popupIndex = -1
        self.listeFiltres = []
        self.tracks = []
        self.numColonneTri = 1
        self.ordreAscendant = True
        self.dictBanques = {}
        # Initialisation du listCtrl
        self.InitBanques() 
        self.nom_fichier_liste = __file__
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        
    def InitModel(self):
        self.donnees = self.GetTracks()

    def GetTracks(self):
        """ R�cup�ration des donn�es """
        self.InitBanques() 
        dictTitulaires = UTILS_Titulaires.GetTitulaires() 
        criteres = ""
        if self.IDfamille != None :
            criteres = "WHERE prelevements.IDfamille=%d" % self.IDfamille
        if self.IDmandat != None :
            criteres = "WHERE prelevements.IDmandat=%d" % self.IDmandat
        DB = GestionDB.DB()
        req = """SELECT 
        prelevements.IDprelevement, prelevements.IDlot, prelevements.IDfamille, 
        prelevement_banque, prelevement_iban, prelevement_bic, 
        prelevements.IDmandat, prelevement_reference_mandat, prelevement_date_mandat,
        prelevements.sequence,
        titulaire, prelevements.type, IDfacture, libelle, prelevements.montant, statut,
        banques.nom,
        reglements.IDreglement, reglements.date, reglements.IDdepot,
        comptes_payeurs.IDcompte_payeur,
        lots_prelevements.date, lots_prelevements.nom
        FROM prelevements
        LEFT JOIN banques ON banques.IDbanque = prelevements.prelevement_banque
        LEFT JOIN reglements ON reglements.IDprelevement = prelevements.IDprelevement
        LEFT JOIN comptes_payeurs ON comptes_payeurs.IDfamille = prelevements.IDfamille
        LEFT JOIN lots_prelevements ON lots_prelevements.IDlot = prelevements.IDlot
        %s
        ;""" % criteres
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        listeListeView = []
        for IDprelevement, IDlot, IDfamille, prelevement_banque, prelevement_iban, prelevement_bic, IDmandat, prelevement_reference_mandat, prelevement_date_mandat, sequence, titulaire, type_prelevement, IDfacture, libelle, montant, statut, nomBanque, IDreglement, dateReglement, IDdepot, IDcompte_payeur, dateLot, nomLot in listeDonnees :
            prelevement_date_mandat = UTILS_Dates.DateEngEnDateDD(prelevement_date_mandat)
            dateLot = UTILS_Dates.DateEngEnDateDD(dateLot)
            dictTemp = {
                "IDprelevement" : IDprelevement, "IDlot" : IDlot, "IDfamille" : IDfamille, 
                "prelevement_banque" : prelevement_banque, "prelevement_iban" : prelevement_iban, "prelevement_bic" : prelevement_bic, 
                "IDmandat" : IDmandat, "prelevement_reference_mandat" : prelevement_reference_mandat, "prelevement_date_mandat" : prelevement_date_mandat,
                "sequence" : sequence, "titulaire" : titulaire, "type" : type_prelevement, "IDfacture" : IDfacture, 
                "libelle" : libelle, "montant" : montant, "statut" : statut, "IDlot" : IDlot, "IDmandat" : IDmandat, "nomBanque" : nomBanque, 
                "IDreglement" : IDreglement, "dateReglement" : dateReglement, "IDdepot" : IDdepot, "IDcompte_payeur" : IDcompte_payeur,
                "dateLot" : dateLot, "nomLot" : nomLot,
                }
            track = Track(dictTemp, dictTitulaires)
            listeListeView.append(track)
        return listeListeView
        
    def InitBanques(self):
        global DICT_BANQUES
        DICT_BANQUES = self.GetNomsBanques()
    
    def GetNomsBanques(self):
        DB = GestionDB.DB()
        req = """SELECT IDbanque, nom
        FROM banques;"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        dictBanques = {}
        for IDbanque, nom in listeDonnees :
            dictBanques[IDbanque] = nom
        return dictBanques
                
    def InitObjectListView(self):            
        # Couleur en alternance des lignes
        self.oddRowsBackColor = UTILS_Interface.GetValeur("couleur_tres_claire", wx.Colour(240, 251, 237))
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
                
        # Image list
        self.imgValide = self.AddNamedImages("valide", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ok.png"), wx.BITMAP_TYPE_PNG))
        self.imgRefus = self.AddNamedImages("refus", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Interdit.png"), wx.BITMAP_TYPE_PNG))
        self.imgAttente = self.AddNamedImages("attente", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Attente.png"), wx.BITMAP_TYPE_PNG))
        
        def GetImageStatut(track):
            if track.statut == "valide" : return self.imgValide
            if track.statut == "refus" : return self.imgRefus
            if track.statut == "attente" : return self.imgAttente

        def GetImageReglement(track):
            if track.reglement == False :
                return self.imgRefus
            else :
                return self.imgValide

        def FormateDateCourt(dateDD):
            if dateDD == None :
                return ""
            else:
                return UTILS_Dates.DateEngFr(str(dateDD))

        def FormateMontant(montant):
            if montant == None : return ""
            return "%.2f %s" % (montant, SYMBOLE)

        def FormateType(statut):
            if statut == "manuel" : return _("Manuel")
            if statut == "facture" : return _("Facture")
            return ""

        def FormateStatut(statut):
            if statut == "valide" : return _("Valide")
            if statut == "refus" : return _("Refus")
            if statut == "attente" : return _("Attente")

        def FormateReglement(reglement):
            if reglement == True :
                return _("Oui")
            else:
                return ""

        liste_Colonnes = [
            ColumnDefn(_("ID"), "left", 0, "IDprelevement", typeDonnee="entier"),
            ColumnDefn(_("Date pr�l�v."), 'left', 75, "dateLot", typeDonnee="date", stringConverter=FormateDateCourt),
            ColumnDefn(_("Lot pr�l�v."), 'left', 150, "nomLot", typeDonnee="texte"),
##            ColumnDefn(_("Type"), 'left', 70, "type", stringConverter=FormateType),
            ColumnDefn(_("Libell�"), 'left', 110, "libelle", typeDonnee="texte"),
##            ColumnDefn(_("Banque"), 'left', 120, "nomBanque"),
            ColumnDefn(_("Montant"), 'right', 70, "montant", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_("Statut"), 'left', 80, "statut", typeDonnee="texte", stringConverter=FormateStatut, imageGetter=GetImageStatut),
            ColumnDefn(_("R�glement"), 'left', 70, "reglement", typeDonnee="bool", stringConverter=FormateReglement, imageGetter=GetImageReglement),
            ColumnDefn(_("S�quence"), 'left', 70, "sequence", typeDonnee="texte"),
            ColumnDefn(_("IBAN"), 'left', 190, "prelevement_iban", typeDonnee="texte"),
            ColumnDefn(_("BIC"), 'left', 100, "prelevement_bic", typeDonnee="texte"),
##            ColumnDefn(_("Etab."), 'left', 50, "prelevement_etab"),
##            ColumnDefn(_("Guich."), 'left', 50, "prelevement_guichet"),
##            ColumnDefn(_("Compte"), 'left', 90, "prelevement_numero"),
##            ColumnDefn(_("Cl�"), 'left', 30, "prelevement_cle"),
            ColumnDefn(_("Banque"), 'left', 130, "nomBanque", typeDonnee="texte"),
            ColumnDefn(_("Titulaire du compte"), 'left', 160, "titulaire", typeDonnee="texte"),
            ColumnDefn(_("Ref. mandat"), 'left', 90, "prelevement_reference_mandat", typeDonnee="texte"),
            ColumnDefn(_("Date mandat"), 'left', 100, "prelevement_date_mandat", typeDonnee="date", stringConverter=FormateDateCourt),
            ]
        
##        if self.IDfamille == None :
##            liste_Colonnes.insert(3, ColumnDefn(_("Famille"), 'left', 210, "titulaires"))
            
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_("Aucun pr�l�vement"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, False, "Tekton"))
##        self.SetSortColumn(self.columns[self.numColonneTri])
        self.SortBy(self.numColonneTri, ascending=self.ordreAscendant)
        self.SetObjects(self.donnees)
       
    def MAJ(self):
        self.InitModel()
        self.InitObjectListView()

    def Selection(self):
        return self.GetSelectedObjects()

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        # Cr�ation du menu contextuel
        menuPop = UTILS_Adaptations.Menu()
    
        # G�n�ration automatique des fonctions standards
        self.GenerationContextMenu(menuPop, dictParametres=self.GetParametresImpression())

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def GetParametresImpression(self):
        intro = ""
        # R�cup�re le total
        total = 0.0
        for track in self.donnees :
            total += track.montant
        total = self.GetTexteTotaux().replace("<B>", "").replace("</B>", "")

        dictParametres = {
            "titre" : _("Liste des pr�l�vements"),
            "intro" : intro,
            "total" : total,
            "orientation" : wx.LANDSCAPE,
            }
        return dictParametres

    def GetLabelListe(self):
        """ R�cup�re le nombre de pr�l�vements et le montant total de la liste """
        nbre = 0
        montant = 0.0
        for track in self.GetObjects() :
            nbre += 1
            montant += track.montant
        # Label de staticbox
        if nbre > 1 :
            texte = _("pr�l�vements")
        else :
            texte = _("pr�l�vement")
        label = "%d %s (%.2f %s)" % (nbre, texte, montant, SYMBOLE)
        return label          

    def MAJtotaux(self):
        """ Cr�� le texte infos avec les stats du lot """
        if self.GetParent().GetName() != "DLG_Saisie_prelevement_lot" :
            return
        # Label de staticbox
        texte = self.GetTexteTotaux()
        self.GetParent().ctrl_totaux.SetLabel(texte)
        self.GetParent().box_prelevements_staticbox.SetLabel(self.GetLabelListe())

    def GetTexteTotaux(self):
        # R�cup�ration des chiffres
        nbreTotal = 0
        montantTotal = 0.0
        dictDetails = {}
        for track in self.GetObjects() :
            nbreTotal += 1
            montantTotal += track.montant
            # Regroupement par statut
            if (track.statut in dictDetails) == False :
                dictDetails[track.statut] = {"nbre" : 0, "montant" : 0.0}
            dictDetails[track.statut]["nbre"] += 1
            dictDetails[track.statut]["montant"] += track.montant
            # Regroupement par r�glemennt
            if track.reglement == True :
                reglement = "regle"
            else :
                reglement = "pasregle"
            if (reglement in dictDetails) == False :
                dictDetails[reglement] = {"nbre" : 0, "montant" : 0.0}
            dictDetails[reglement]["nbre"] += 1
            dictDetails[reglement]["montant"] += track.montant
            
        # Cr�ation du texte
        if nbreTotal == 0 :
            texte = _("<B>Aucun pr�l�vement.   </B>")
        elif nbreTotal == 1 :
            texte = _("<B>%d pr�l�vement (%.2f %s) : </B>") % (nbreTotal, montantTotal, SYMBOLE)
        else :
            texte = _("<B>%d pr�l�vements (%.2f %s) : </B>") % (nbreTotal, montantTotal, SYMBOLE)
        
        for key in ("attente", "valide", "refus", "regle", "pasregle") :
            if key in dictDetails :
                dictDetail = dictDetails[key]
                if dictDetail["nbre"] == 1 :
                    if key == "attente" : label = _("en attente")
                    if key == "valide" : label = _("valid�")
                    if key == "refus" : label = _("refus�")
                    if key == "regle" : label = _("r�gl�")
                    if key == "pasregle" : label = _("non r�gl�")
                else :
                    if key == "attente" : label = _("en attente")
                    if key == "valide" : label = _("valid�s")
                    if key == "refus" : label = _("refus�s")
                    if key == "regle" : label = _("r�gl�s")
                    if key == "pasregle" : label = _("non r�gl�s")
                texteDetail = "%d %s (%.2f %s), " % (dictDetail["nbre"], label, dictDetail["montant"], SYMBOLE)
                texte += texteDetail
        if len(dictDetails) > 0 :
            texte = texte[:-2] + "."
        else:
            texte = texte[:-7] + "</B>"
        return texte






# -------------------------------------------------------------------------------------------------------------------------------------------

class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False
        
        self.SetDescriptiveText(_("Rechercher..."))
        self.ShowSearchButton(True)
        
        self.listView = self.parent.ctrl_reglements
        nbreColonnes = self.listView.GetColumnCount()
        self.listView.SetFilter(Filter.TextSearch(self.listView, self.listView.columns[0:nbreColonnes]))
        
        self.SetCancelBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Interdit.png"), wx.BITMAP_TYPE_PNG))
        self.SetSearchBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Loupe.png"), wx.BITMAP_TYPE_PNG))
        
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnDoSearch)
        self.Bind(wx.EVT_TEXT, self.OnDoSearch)

    def OnSearch(self, evt):
        self.Recherche()
            
    def OnCancel(self, evt):
        self.SetValue("")
        self.Recherche()

    def OnDoSearch(self, evt):
        self.Recherche()
        
    def Recherche(self):
        txtSearch = self.GetValue()
        self.ShowCancelButton(len(txtSearch))
        self.listView.GetFilter().SetText(txtSearch)
        self.listView.RepopulateList()
        self.Refresh() 


# -------------------------------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        
        self.myOlv = ListView(panel, id=-1, name="OL_test", style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        self.myOlv.MAJ() 
        
        self.bouton_test = wx.Button(panel, -1, _("Bouton test"))
        self.Bind(wx.EVT_BUTTON, self.OnBoutonTest, self.bouton_test)
        
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.myOlv, 1, wx.ALL|wx.EXPAND, 4)
        sizer_2.Add(self.bouton_test, 0, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.SetSize((800, 400))
        self.CenterOnScreen()
        
    def OnBoutonTest(self, event):
        print("Test de la sauvegarde des reglements :")
        self.myOlv.SauvegardeReglements(date=datetime.date.today(), IDcompte=99)
        
        
        

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "OL TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()

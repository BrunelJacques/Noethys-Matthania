#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys branche Matthania, Matthania pour gérer les None sur les dates
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB, Jacques Brunel
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import datetime
import GestionDB
from Utils import UTILS_Titulaires
from Utils import UTILS_Transports
from Utils import UTILS_Utilisateurs
from Ctrl.CTRL_Saisie_transport import DICT_CATEGORIES
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils

def Nz(valeur, type = "int"):
    try:
        valeur = float(valeur)
    except:
        valeur = 0.0
    if type == 'int':
        valeur = int(valeur)
    return valeur

def DateEngFr(textDate):
    if textDate == None: return ""
    textDate = str(textDate)
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text

def DateComplete(dateDD):
    """ Transforme une date DD en date complète : Ex : lundi 15 janvier 2008 """
    listeJours = (_("Lundi"), _("Mardi"), _("Mercredi"), _("Jeudi"), _("Vendredi"), _("Samedi"), _("Dimanche"))
    listeMois = (_("janvier"), _("février"), _("mars"), _("avril"), _("mai"), _("juin"), _("juillet"), _("août"), _("septembre"), _("octobre"), _("novembre"), _("décembre"))
    dateComplete = listeJours[dateDD.weekday()] + " " + str(dateDD.day) + " " + listeMois[dateDD.month-1] + " " + str(dateDD.year)
    return dateComplete

def DateEngEnDateDD(dateEng):
    if dateEng == None : return None
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

class Track(object):
    def __init__(self, donnees, modLocalisation,dictCorrespondants={}):
        self.IDtransport = donnees[0]
        self.IDindividu = donnees[1]
        self.categorie = donnees[2]
        self.labelTransport = DICT_CATEGORIES[self.categorie]["label"]
        
        self.depart_date = donnees[3]
        #JB
        if self.depart_date== None:
            self.depart_date = "2000-01-01"
        self.depart_dateDD = DateEngEnDateDD(self.depart_date)
        self.depart_heure = donnees[4]
        if self.depart_heure != None :
            hr, mn = self.depart_heure.split(":")
        else :
            hr, mn = 0, 0
        self.depart_date = datetime.date(self.depart_dateDD.year, self.depart_dateDD.month, self.depart_dateDD.day)
        self.depart_IDarret = donnees[5]
        self.depart_IDlieu = donnees[6]
        self.depart_localisation = donnees[7]
        
        self.arrivee_date = donnees[8]
        if self.arrivee_date== None:
            self.arrivee_date = "2000-01-01"
        self.arrivee_dateDD = DateEngEnDateDD(self.arrivee_date)
        self.arrivee_heure = donnees[9]
        if self.arrivee_heure != None :
            hr, mn = self.arrivee_heure.split(":")
        else :
            hr, mn = 0, 0
        self.arrivee_date = datetime.date(self.arrivee_dateDD.year, self.arrivee_dateDD.month, self.arrivee_dateDD.day)
        self.arrivee_IDarret = donnees[10]
        self.arrivee_IDlieu = donnees[11]
        self.arrivee_localisation = donnees[12]
        
        # Analyse des localisations
        self.depart_nom = modLocalisation.Analyse(self.depart_IDarret, self.depart_IDlieu, self.depart_localisation)
        self.arrivee_nom = modLocalisation.Analyse(self.arrivee_IDarret, self.arrivee_IDlieu, self.arrivee_localisation)
        
        # Nom de l'individu
        self.individu_nom = donnees[13]
        self.individu_prenom = donnees[14]
        if self.individu_prenom == None :
            self.individu_prenom = ""
        self.individu_nom_complet = "%s %s" % (self.individu_nom, self.individu_prenom)

        # Date naissance - age
        def Age(naissance, date):
            age = 0
            if date == None:
                date = datetime.date.today()
            if naissance != None:
                if naissance.year > 1900 and date != None :
                    age = (date.year - naissance.year) - int((date.month, date.day) < (naissance.month, naissance.day))
            return age
        self.individu_naiss = DateEngEnDateDD(donnees[15])
        self.individu_age = (Age(self.individu_naiss, self.depart_dateDD))

        #transport et affectation
        self.prix_transport = Nz(donnees[16],type = "float") + Nz(donnees[19],type = "float")
        activite = ""
        if donnees[17]: activite += donnees[17]
        if donnees[20]: activite += donnees[20]
        self.activite = activite
        self.analytique_convoi = Nz(donnees[18]) + Nz(donnees[21])

        #ligne
        self.ligne = donnees[22]

        # Représentant
        self.correspondant_nom = ""
        self.telephones = ""
        self.mails = ""
        IDfamille = None
        if donnees[-2]: IDfamille = donnees[-2]
        if donnees[-1]: IDfamille = donnees[-1]

        # la famille n'a pas été détectée, on cherche le correspondant à l'unité sur l'individu
        if not IDfamille or ( not IDfamille in list(dictCorrespondants.keys())):
            dictCorrespondant = UTILS_Titulaires.GetCorrespondant(IDindividu=self.IDindividu)
        # la famille est dans le dictionnaire des correspondants
        else:
            dictCorrespondant = dictCorrespondants[IDfamille]

        if dictCorrespondant:
            if "nom_complet" in dictCorrespondant: self.correspondant_nom = dictCorrespondant["nom_complet"]
            if "telephones" in dictCorrespondant: self.telephones = dictCorrespondant["telephones"]
            if "mails" in dictCorrespondant: self.mails = dictCorrespondant["mails"]

class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        # Récupération des paramètres perso
        self.IDindividu = kwds.pop("IDindividu", None)
        self.selectionID = None
        self.selectionTrack = None
        self.criteres = ""
        self.itemSelected = False
        self.popupIndex = -1
        self.dictFiltres = {}
        # Initialisation du listCtrl
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        
    def OnItemActivated(self,event):
        self.Modifier(None)
                
    def InitModel(self):
        self.donnees = self.GetTracks()
    
    def SetFiltres(self, filtres={}, futur = False):
        self.dictFiltres = filtres
        self.MAJ(futur = futur)
        
    def GetTracks(self):
        """ Récupération des données """
        modLocalisation = UTILS_Transports.AnalyseLocalisation() 
        
        if self.IDindividu != None :
            conditionIndividu = "AND transports.IDindividu=%d" % self.IDindividu
        else :
            conditionIndividu = ""
        
        if self.futur :
            conditionIndividu += " AND depart_date >= '%s'" % str(datetime.date.today())
        listeID = None
        DB = GestionDB.DB()
        req = """SELECT transports.IDtransport, transports.IDindividu, transports.categorie, transports.depart_date,
                transports.depart_heure, transports.depart_IDarret, transports.depart_IDlieu, transports.depart_localisation,
                transports.arrivee_date, transports.arrivee_heure, transports.arrivee_IDarret, transports.arrivee_IDlieu,
                transports.arrivee_localisation, individus.nom, individus.prenom, individus.date_naiss,
                SUM(matPieces.piePrixTranspAller), activites.nom, activites.code_transport,
                SUM(matPieces_1.piePrixTranspRetour), activites_1.nom, activites_1.code_transport, transports_lignes.nom,
                MAX(matPieces.pieIDfamille),MAX(matPieces_1.pieIDfamille)
        FROM ((((((transports
            LEFT JOIN individus ON transports.IDindividu = individus.IDindividu)
            LEFT JOIN transports_lignes ON transports.IDligne = transports_lignes.IDligne)
            LEFT JOIN matPieces ON transports.IDtransport = matPieces.pieIDtranspAller)
            LEFT JOIN activites ON matPieces.pieIDactivite = activites.IDactivite)
            LEFT JOIN matPieces AS matPieces_1 ON transports.IDtransport = matPieces_1.pieIDtranspRetour)
            LEFT JOIN activites AS activites_1 ON matPieces_1.pieIDactivite = activites_1.IDactivite)
        WHERE transports.mode ='TRANSP'  %s
        GROUP BY transports.IDtransport, transports.IDindividu, transports.categorie, transports.depart_date,
                transports.depart_heure, transports.depart_IDarret, transports.depart_IDlieu, transports.depart_localisation,
                transports.arrivee_date, transports.arrivee_heure, transports.arrivee_IDarret, transports.arrivee_IDlieu,
                transports.arrivee_localisation, individus.nom, individus.prenom, individus.date_naiss,
                activites.nom, activites.code_transport, activites_1.nom, activites_1.code_transport, 
                transports_lignes.nom
        ORDER BY transports.depart_date;
        """ % conditionIndividu
        DB.ExecuterReq(req,MsgBox="OL_Transport.GetTracks")
        listeDonnees = DB.ResultatReq()
        DB.Close()

        # constitution d'un dictionnaire des représentants des familles concernées
        lstIDfamilles = []
        for item in listeDonnees:
            if item[-2]: 
                if not item[-2] in lstIDfamilles:
                    lstIDfamilles.append(item[-2])
            if item[-1]: 
                if not item[-1] in lstIDfamilles:
                    lstIDfamilles.append(item[-1])
        dictCorrespondants = UTILS_Titulaires.GetCorrespondants(lstIDfamilles)

        listeListeView = []
        for item in listeDonnees :
            valide = True
            if listeID != None :
                if item[0] not in listeID :
                    valide = False
            if valide == True :
                track = Track(item, modLocalisation,dictCorrespondants)
                
                # Filtres
                valide = True
                if "individu" in self.dictFiltres and track.IDindividu != self.dictFiltres["individu"] : valide = False
                if "transport" in self.dictFiltres and track.categorie != self.dictFiltres["transport"] : valide = False
                if "depart_date" in self.dictFiltres and track.depart_dateDD != self.dictFiltres["depart_date"] : valide = False
                if "depart_heure" in self.dictFiltres and track.depart_heure != self.dictFiltres["depart_heure"] : valide = False
                if "depart_lieu" in self.dictFiltres and track.depart_nom != self.dictFiltres["depart_lieu"] : valide = False
                if "arrivee_date" in self.dictFiltres and track.arrivee_dateDD != self.dictFiltres["arrivee_date"] : valide = False
                if "arrivee_heure" in self.dictFiltres and track.arrivee_heure != self.dictFiltres["arrivee_heure"] : valide = False
                if "arrivee_lieu" in self.dictFiltres and track.arrivee_nom != self.dictFiltres["arrivee_lieu"] : valide = False
                
                if valide == True :
                    listeListeView.append(track)
                    if self.selectionID == item[0] :
                        self.selectionTrack = track
                        
        return listeListeView
            
    def InitObjectListView(self):            
        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED" 
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
        
        # Image list
        for code, valeurs in DICT_CATEGORIES.items() :
            img = self.AddNamedImages(code, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/%s.png" % valeurs["image"]), wx.BITMAP_TYPE_PNG))
        
        def GetImageCategorie(track):
            return track.categorie

        def FormateDateCourt(dateDD):
            if dateDD == None :
                return ""
            else:
                return DateEngFr(str(dateDD))

        def FormateDate(dateDT):
            date = FormateDateCourt(datetime.date(dateDT.year, dateDT.month, dateDT.day))
            return "%s" % (date)

        def FormateCategorie(categorie):
            return DICT_CATEGORIES[categorie]["label"]

        liste_Colonnes = [
            ColumnDefn("ID", "left", 40, "IDtransport", typeDonnee="entier"),
            ColumnDefn(_("Transport"), "left", 120, "categorie", typeDonnee="texte", stringConverter=FormateCategorie,  imageGetter=GetImageCategorie),
            ColumnDefn(_("Départ"), 'left', 80, "depart_date", typeDonnee="date", stringConverter=FormateDate),
            ColumnDefn(_("Origine"), 'left', 140, "depart_nom", typeDonnee="texte"),
            ColumnDefn(_("Arrivée"), 'left', 80, "arrivee_date", typeDonnee="date", stringConverter=FormateDate),
            ColumnDefn(_("Destination"), 'left', 140, "arrivee_nom", typeDonnee="texte"),
            ColumnDefn(_("Prix"), 'right', 40, "prix_transport", typeDonnee="montant"),
            ColumnDefn(_("Activité"), 'right', 160, "activite", typeDonnee="entier"),
            ColumnDefn(_("Convoi"), 'right', 60, "analytique_convoi", typeDonnee="entier"),
            ColumnDefn(_("Ligne"), 'left', 160, "ligne", typeDonnee="entier"),
            ColumnDefn(_("Correspondant"), "left", 140, "correspondant_nom", typeDonnee="texte"),
            ColumnDefn(_("Téléphones"), "left", 100, "telephones", typeDonnee="texte"),
            ColumnDefn(_("Mails"), "left", 100, "mails", typeDonnee="texte")
            ]
        
        if self.IDindividu == None :
            liste_Colonnes.insert(1, ColumnDefn(_("Individu"), "left", 150, "individu_nom_complet", typeDonnee="texte") )
            liste_Colonnes.insert(2, ColumnDefn(_("Âge"), "left", 40, "individu_age", typeDonnee="entier") )

        self.SetColumns(liste_Colonnes)
        self.CreateCheckStateColumn(1)
        self.SetEmptyListMsg(_("Aucun transport"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, False, "Tekton"))
        if self.IDindividu == None :
            self.SetSortColumn(self.columns[4])
        else :
            self.SetSortColumn(self.columns[3])
        self.SetObjects(self.donnees)
       
    def MAJ(self, ID=None, futur=False):
        if ID != None :
            self.selectionID = ID
            self.selectionTrack = None
        else:
            self.selectionID = None
            self.selectionTrack = None
        self.futur = futur
        self.InitModel()
        self.InitObjectListView()
        # Sélection d'un item
        if self.selectionTrack != None :
            self.SelectObject(self.selectionTrack, deselectOthers=True, ensureVisible=True)
        self.selectionID = None
        self.selectionTrack = None
        if ID == None :
            self.DefileDernier() 
        self.Refresh()

    def Selection(self):
        return self.GetSelectedObjects()

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        if len(self.Selection()) == 0:
            noSelection = True
        else:
            noSelection = False
            ID = self.Selection()[0].IDtransport
                
        # Création du menu contextuel
        menuPop = wx.Menu()

        if self.IDindividu != None :

            # Item Ajouter
            item = wx.MenuItem(menuPop, 10, _("Ajouter"))
            bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_PNG)
            item.SetBitmap(bmp)
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.Ajouter, id=10)
                
            menuPop.AppendSeparator()

        # Item Modifier
        item = wx.MenuItem(menuPop, 20, _("Modifier"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Modifier, id=20)
        if noSelection == True : item.Enable(False)
        
        # Item Supprimer
        item = wx.MenuItem(menuPop, 30, _("Supprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Supprimer, id=30)
        if noSelection == True : item.Enable(False)
        
        if self.IDindividu != None :
            
            menuPop.AppendSeparator()

            # Item Calendrier
            item = wx.MenuItem(menuPop, 100, _("Planning des transports"))
            bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Calendrier.png"), wx.BITMAP_TYPE_PNG)
            item.SetBitmap(bmp)
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.Calendrier, id=100)
                
        menuPop.AppendSeparator()

        # Item Tout cocher
        item = wx.MenuItem(menuPop, 70, _("Tout cocher"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Cocher.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.CocheTout, id=70)

        # Item Tout décocher
        item = wx.MenuItem(menuPop, 80, _("Tout décocher"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Decocher.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.CocheRien, id=80)

        menuPop.AppendSeparator()

        # Item Apercu avant impression
        item = wx.MenuItem(menuPop, 40, _("Aperçu avant impression"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=40)
        
        # Item Imprimer
        item = wx.MenuItem(menuPop, 50, _("Imprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=50)
        
        menuPop.AppendSeparator()
    
        # Item Export Texte
        item = wx.MenuItem(menuPop, 600, _("Exporter au format Texte"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Texte2.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.ExportTexte, id=600)
        
        # Item Export Excel
        item = wx.MenuItem(menuPop, 700, _("Exporter au format Excel"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Excel.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.ExportExcel, id=700)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Impression(self, mode="preview"):
        if self.donnees == None or len(self.donnees) == 0 :
            dlg = wx.MessageDialog(self, _("Il n'y a aucune donnée à imprimer !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des transports"), format="A", orientation=wx.PORTRAIT)
        if mode == "preview" :
            prt.Preview()
        else:
            prt.Print()
    
    def Calendrier(self, event):
        from Dlg import DLG_Planning_transports
        dlg = DLG_Planning_transports.Dialog(self, IDindividu=self.IDindividu)
        dlg.ShowModal()
        dlg.Destroy()
        self.MAJ() 
        
    def Apercu(self, event):
        self.Impression("preview")

    def Imprimer(self, event):
        self.Impression("print")

    def ExportTexte(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(self, titre=_("Liste des transports"))
        
    def ExportExcel(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=_("Liste des transports"))

    def Ajouter(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_transports", "creer") == False : return
        from Dlg import DLG_Saisie_transport
        dlg = DLG_Saisie_transport.Dialog_multiple(self, IDindividu=self.IDindividu) 
        if dlg.ShowModal() == wx.ID_OK:
            self.MAJ()
        dlg.Destroy()

    def Modifier(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_transports", "modifier") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucun transport à modifier dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]
        from Dlg import DLG_Saisie_transport
        dlg = DLG_Saisie_transport.Dialog(self, IDtransport=track.IDtransport, IDindividu=track.IDindividu)      
        if dlg.ShowModal() == wx.ID_OK:
            self.MAJ(track.IDtransport)
        dlg.Destroy() 

    def Supprimer(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_transports", "supprimer") == False : return
        if len(self.Selection()) == 0 and len(self.GetTracksCoches()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucun transport à supprimer dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        if len(self.GetTracksCoches()) > 0 :
            # Suppression multiple
            listeSelections = self.GetTracksCoches()
            dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer les %d transports cochés ?") % len(listeSelections), _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
            reponse = dlg.ShowModal() 
            dlg.Destroy()
            if reponse != wx.ID_YES :
                return
        
        else :
            # Suppression unique
            listeSelections = self.Selection()        
            dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer le transport n°%d ?") % listeSelections[0].IDtransport, _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
            reponse = dlg.ShowModal() 
            dlg.Destroy()
            if reponse != wx.ID_YES :
                return
        
        listeSuppressions = []
        DB = GestionDB.DB()
        for track in listeSelections :
            DB.ReqDEL("transports", "IDtransport", track.IDtransport)
            listeSuppressions.append(track)
        DB.Close()
        self.MAJ()

        # Confirmation de suppression
        dlg = wx.MessageDialog(self, _("%d transport(s) ont été supprimé(s) avec succès.") % len(listeSuppressions), _("Suppression"), wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()


    def CocheTout(self, event=None):
        if self.GetFilter() != None :
            listeObjets = self.GetFilteredObjects()
        else :
            listeObjets = self.GetObjects()
        for track in listeObjets :
            self.Check(track)
            self.RefreshObject(track)
        
    def CocheRien(self, event=None):
        for track in self.donnees :
            self.Uncheck(track)
            self.RefreshObject(track)

    def GetTracksCoches(self):
        return self.GetCheckedObjects()

# -------------------------------------------------------------------------------------------------------------------------------------------

class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent, listview):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False
        
        self.SetDescriptiveText(_("Rechercher un transport..."))
        self.ShowSearchButton(True)
        
        self.listView = listview
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
        self.myOlv = ListView(panel, id=-1, IDindividu=None, name="OL_test", style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        self.myOlv.MAJ() 
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.myOlv, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.SetSize((800, 200))

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "OL TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()

#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
import datetime
import GestionDB
from six.moves import range
from Utils import UTILS_Interface
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils
from Ctrl.CTRL_Questionnaire import LISTE_CONTROLES


LISTE_CHAMPS_STANDARDS = [
    ("INDIVIDU_ID", _("ID de l'individu"), _("Individu"), _("IDIndividu"), 50),
    ("INDIVIDU_GENRE", _("Genre de l'individu (M/F)"), _("Individu"), _("Genre"), 70),
    ("INDIVIDU_CIVILITE_LONG", _("Civilité de l'individu (long)"), _("Individu"), _("Civilité"), 80),
    ("INDIVIDU_CIVILITE_COURT", _("Civilité de l'individu (court)"), _("Individu"), _("Civilité"), 80),
    ("INDIVIDU_NOM", _("Nom de l'individu"), _("Individu"), _("Nom"), 150),
    ("INDIVIDU_PRENOM", _("Prénom de l'individu"), _("Individu"), _("Prénom"), 150),
    ("INDIVIDU_NOM_COMPLET", _("Nom complet de l'individu"), _("Individu"), _("Nom"), 200),
    ("INDIVIDU_DATE_NAISS", _("Date de naissance de l'individu"), _("Individu"), _("Date Naiss."), 80),
    ("INDIVIDU_AGE", _("Age de l'individu"), _("Individu"), _("Age"), 80),
    ("INDIVIDU_NUM_SECU", _("Numéro de sécu de l'individu"), _("Individu"), _("Num. sécu."), 120),
    ("INDIVIDU_RUE", _("Adresse de l'individu - Rue"), _("Individu"), _("Rue"), 100),
    ("INDIVIDU_CP", _("Adresse de l'individu - CP"), _("Individu"), _("C.P."), 80),
    ("INDIVIDU_VILLE", _("Adresse de l'individu - Ville"), _("Individu"), _("Ville"), 80),
    ("INDIVIDU_SECTEUR", _("Adresse de l'individu - Secteur"), _("Individu"), _("Secteur"), 80),

    ("FAMILLE_ID", _("ID de la famille"), _("Famille"), _("IDfamille"), 50),
    ("FAMILLE_TITULAIRES", _("Nom des titulaires"), _("Famille"), _("Représentants"), 200),
    ("FAMILLE_RUE", _("Adresse de la famille - Rue"), _("Famille"), _("Rue"), 200),
    ("FAMILLE_CP", _("Adresse de la famille - CP"), _("Famille"), _("C.P."), 80),
    ("FAMILLE_VILLE", _("Adresse de la famille - Ville"), _("Famille"), _("Ville"), 100),
    ("FAMILLE_SECTEUR", _("Adresse de la famille - Secteur"), _("Famille"), _("Secteur"), 100),
    ("FAMILLE_CAISSE", _("Nom de la caisse d'allocation"), _("Famille"), _("Caisse"), 100),
    ("FAMILLE_NUM_ALLOCATAIRE", _("Numéro d'allocataire"), _("Famille"), _("Num. Alloc."), 80),
    ("FAMILLE_ALLOCATAIRE", _("Nom du titulaire allocataire"), _("Famille"), _("Allocataire"), 100),
    ("FAMILLE_QF", _("Quotient familial de la famille"), _("Famille"), _("QF"), 80),
    ] # (code, label, actif)


def FormateLabelPrestation(label=u""):
    liste1 = [u"é", "è", "ê", "à", "ù", "û", "ç", "ô", "î", "ï", "â", " ",]
    liste2 = [u"e", "e", "e", "a", "u", "u", "c", "o", "i", "i", "a", "_"]
    for i in range(len(liste1)):
        label = label.replace(liste1[i], liste2[i])
    for i in ("'", "(", ")", "{", "}", ",", ".", "!", "+", "-", "[", "]", "/", "*", "#") :
        label = label.replace(i, "")
    label = label.upper()
    return label


class Track(object):
    def __init__(self, donnees):
        self.IDchamp = donnees["IDchamp"]
        self.code = donnees["code"]
        self.titre = donnees["titre"]
        self.label = donnees["label"]
        self.type = donnees["type"]
        self.categorie = donnees["categorie"]
        self.formule = donnees["formule"]
        
        # Largeur de colonne
        if "largeur" in donnees :
            self.largeur = donnees["largeur"]
        else :
            self.largeur = 100

# ----------------------------------------------------------------------------------------------------------------

class Champs():
    """ Importation des champs """
    def __init__(self, listeActivites=[], dateMin=None, dateMax=None):
        self.dateMin = dateMin
        self.dateMax = dateMax
        self.listeActivites = listeActivites
        self.donnees = self.GetTracks() 
        
    def GetChamps(self):
        return self.donnees
    
    def GetDictChamps(self):
        """ Retourne les champs sous forme de dictionnaire de tracks avec key=code """
        dictChamps = {}
        for track in self.donnees :
            dictChamps[track.code] = track
        return dictChamps
    
    def GetTracks(self):
        """ Récupération des données """
        listeListeView = []

        # Champs STANDARDS
        for code, label, categorie, titre, largeur in LISTE_CHAMPS_STANDARDS :
            dictTemp = {"IDchamp":None, "code":code, "label":label, "type":"STANDARD", "categorie":categorie, "formule":None, "titre":titre, "largeur":largeur}
            listeListeView.append(Track(dictTemp))
        
        # Champs QUESTIONNAIRES
        listeQuestions = self.ImportationQuestions() 
        for IDquestion, label, type, controle in listeQuestions :
            if type == "individu" : categorie = _("Individu")
            if type == "famille" : categorie = _("Famille")
            dictTemp = {"IDchamp":None, "code":"QUESTION%d" % IDquestion, "label":label, "type":"QUESTION", "categorie":categorie, "titre":label, "formule":None}
            listeListeView.append(Track(dictTemp))
            
        # Quantité UNITES
        listeUnites = self.ImportationUnites() 
        for IDunite, IDactivite, nomUnite, typeUnite, nomActivite, abregeActivite in listeUnites :
            listeListeView.append(Track({"IDchamp":None, "code":"NBRE_UNITE%d" % IDunite, "label":_("Quantité de '%s (%s)'") % (nomUnite, abregeActivite), "type":"NBRE_UNITE", "categorie":_("Consommation"), "titre":_("Qté %s") % nomUnite ,"formule":None}))
            listeListeView.append(Track({"IDchamp":None, "code":"NBRE_GV_UNITE%d" % IDunite, "label":_("Quantité de '%s (%s)' durant les grandes vacances") % (nomUnite, abregeActivite), "type":"NBRE_UNITE", "categorie":_("Consommation"), "titre":_("Qté %s GV") % nomUnite ,"formule":None}))
            listeListeView.append(Track({"IDchamp":None, "code":"NBRE_PV_UNITE%d" % IDunite, "label":_("Quantité de '%s (%s)' durant les petites vacances") % (nomUnite, abregeActivite), "type":"NBRE_UNITE", "categorie":_("Consommation"), "titre":_("Qté %s PV") % nomUnite ,"formule":None}))
            listeListeView.append(Track({"IDchamp":None, "code":"NBRE_HV_UNITE%d" % IDunite, "label":_("Quantité de '%s (%s)' hors vacances") % (nomUnite, abregeActivite), "type":"NBRE_UNITE", "categorie":_("Consommation"), "titre":_("Qté %s HV") % nomUnite ,"formule":None}))

        # Temps UNITES
        for IDunite, IDactivite, nomUnite, typeUnite, nomActivite, abregeActivite in listeUnites :
            listeListeView.append(Track({"IDchamp":None, "code":"TEMPS_UNITE%d" % IDunite, "label":_("Temps de '%s (%s)'") % (nomUnite, abregeActivite), "type":"TEMPS_UNITE", "categorie":_("Consommation"), "titre":_("Temps %s") % nomUnite ,"formule":None}))
            listeListeView.append(Track({"IDchamp":None, "code":"TEMPS_GV_UNITE%d" % IDunite, "label":_("Temps de '%s (%s)' durant les grandes vacances") % (nomUnite, abregeActivite), "type":"TEMPS_UNITE", "categorie":_("Consommation"), "titre":_("Temps %s GV") % nomUnite ,"formule":None}))
            listeListeView.append(Track({"IDchamp":None, "code":"TEMPS_PV_UNITE%d" % IDunite, "label":_("Temps de '%s (%s)' durant les petites vacances") % (nomUnite, abregeActivite), "type":"TEMPS_UNITE", "categorie":_("Consommation"), "titre":_("Temps %s PV") % nomUnite ,"formule":None}))
            listeListeView.append(Track({"IDchamp":None, "code":"TEMPS_HV_UNITE%d" % IDunite, "label":_("Temps de '%s (%s)' hors vacances") % (nomUnite, abregeActivite), "type":"TEMPS_UNITE", "categorie":_("Consommation"), "titre":_("Temps %s HV") % nomUnite ,"formule":None}))

        # Temps facturé UNITES
        for IDunite, IDactivite, nomUnite, typeUnite, nomActivite, abregeActivite in listeUnites :
            listeListeView.append(Track({"IDchamp":None, "code":"TEMPS_FACTURE_UNITE%d" % IDunite, "label":_("Temps facturé de '%s (%s)'") % (nomUnite, abregeActivite), "type":"TEMPS_FACTURE_UNITE", "categorie":_("Consommation"), "titre":_("Temps facturé %s") % nomUnite ,"formule":None}))
            listeListeView.append(Track({"IDchamp":None, "code":"TEMPS_FACTURE_GV_UNITE%d" % IDunite, "label":_("Temps facturé de '%s (%s)' durant les grandes vacances") % (nomUnite, abregeActivite), "type":"TEMPS_FACTURE_UNITE", "categorie":_("Consommation"), "titre":_("Temps facturé %s GV") % nomUnite ,"formule":None}))
            listeListeView.append(Track({"IDchamp":None, "code":"TEMPS_FACTURE_PV_UNITE%d" % IDunite, "label":_("Temps facturé de '%s (%s)' durant les petites vacances") % (nomUnite, abregeActivite), "type":"TEMPS_FACTURE_UNITE", "categorie":_("Consommation"), "titre":_("Temps facturé %s PV") % nomUnite ,"formule":None}))
            listeListeView.append(Track({"IDchamp":None, "code":"TEMPS_FACTURE_HV_UNITE%d" % IDunite, "label":_("Temps facturé de '%s (%s)' hors vacances") % (nomUnite, abregeActivite), "type":"TEMPS_FACTURE_UNITE", "categorie":_("Consommation"), "titre":_("Temps facturé %s HV") % nomUnite ,"formule":None}))

        # Montant PRESTATIONS
##        listePrestations = self.ImportationPrestations() 
##        for label, abregeActivite in listePrestations :
##            code = FormateLabelPrestation(label)
##            listeListeView.append(Track({"IDchamp":None, "code":"MONTANT_%s" % code, "label":_("Montant de '%s (%s)'") % (label, abregeActivite), "type":"MONTANT_PRESTATION", "categorie":_("Prestation"), "titre":_("Montant %s") % label ,"formule":None}))
##            # Grandes vacances
##            listeListeView.append(Track({"IDchamp":None, "code":"MONTANT_GV_%s" % code, "label":_("Montant de '%s (%s)' durant les grandes vacances") % (label, abregeActivite), "type":"MONTANT_PRESTATION", "categorie":_("Prestation"), "titre":_("Montant %s GV") % label ,"formule":None}))
##            # Petites vacances
##            listeListeView.append(Track({"IDchamp":None, "code":"MONTANT_PV_%s" % code, "label":_("Montant de '%s (%s)' durant les petites vacances") % (label, abregeActivite), "type":"MONTANT_PRESTATION", "categorie":_("Prestation"), "titre":_("Montant %s PV") % label ,"formule":None}))
##            # Hors vacances
##            listeListeView.append(Track({"IDchamp":None, "code":"MONTANT_HV_%s" % code, "label":_("Montant de '%s (%s)' hors vacances") % (label, abregeActivite), "type":"MONTANT_PRESTATION", "categorie":_("Prestation"), "titre":_("Montant %s HV") % label ,"formule":None}))
            
        # Aides
##        listeCaisses = self.ImportationCaisses() 
##        for IDcaisse, nomCaisse in listeCaisses :
##            dictTemp = {"IDchamp":None, "code":"NBRE_AIDES%d" % IDcaisse, "label":_("Qté des aides %s") % nomCaisse, "type":"NBRE_AIDES", "categorie":_("Aide"), "titre":_("Qté Aides") ,"formule":None}
##            listeListeView.append(Track(dictTemp))
##            dictTemp = {"IDchamp":None, "code":"MONTANT_AIDES%d" % IDcaisse, "label":_("Montant des aides %s") % nomCaisse, "type":"MONTANT_AIDES", "categorie":_("Aide"), "titre":_("Montant Aides") ,"formule":None}
##            listeListeView.append(Track(dictTemp))

        # Champs PERSO
        listeChamps = self.ImportationChampsPerso() 
        for IDchamp, code, label, formule, titre in listeChamps :
            dictTemp = {"IDchamp":IDchamp, "code":code, "label":label, "type":"PERSO", "categorie":_("Personnalisé"), "titre":titre ,"formule":formule}
            listeListeView.append(Track(dictTemp))
        
        return listeListeView
    
    def ImportationQuestions(self):
        # Importation des questions
        dictControles = {}
        for dictControle in LISTE_CONTROLES :
            dictControles[dictControle["code"]] = dictControle
            
        DB = GestionDB.DB()
        req = """SELECT IDquestion, questionnaire_questions.label, type, controle
        FROM questionnaire_questions
        LEFT JOIN questionnaire_categories ON questionnaire_categories.IDcategorie = questionnaire_questions.IDcategorie
        ;"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeQuestions = DB.ResultatReq()
        DB.Close()
        listeResultats = []
        for IDquestion, label, type, controle in listeQuestions :
            if dictControles[controle]["filtre"] != None :
                listeResultats.append((IDquestion, label, type, controle))
            
        return listeResultats

    def ImportationUnites(self):
        # Importation des unités de consommations
        if len(self.listeActivites) == 0 : return []
        elif len(self.listeActivites) == 1 : conditionActivites = "unites.IDactivite=%d" % self.listeActivites[0]
        else : conditionActivites = "unites.IDactivite IN %s" % str(tuple(self.listeActivites))
        DB = GestionDB.DB()
        req = """SELECT unites.IDunite, unites.IDactivite, unites.nom, unites.type, activites.nom, activites.abrege
        FROM unites
        LEFT JOIN activites ON activites.IDactivite = unites.IDactivite
        WHERE %s AND activites.date_debut<='%s' AND activites.date_fin>='%s'
        ORDER BY ordre
        ;""" % (conditionActivites, self.dateMax, self.dateMin)
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeUnites = DB.ResultatReq()     
        DB.Close() 
        return listeUnites

    def ImportationPrestations(self):
        # Importation des prestations de la période
        if len(self.listeActivites) == 0 : return []
        elif len(self.listeActivites) == 1 : conditionActivites = "prestations.IDactivite=%d" % self.listeActivites[0]
        else : conditionActivites = "prestations.IDactivite IN %s" % str(tuple(self.listeActivites))
        DB = GestionDB.DB()
        req = """SELECT label, activites.abrege
        FROM prestations
        LEFT JOIN activites ON activites.IDactivite = prestations.IDactivite
        WHERE %s AND date>='%s' AND date<='%s'
        GROUP BY label
        ORDER BY label
        ;""" % (conditionActivites, self.dateMin, self.dateMax)
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listePrestations = DB.ResultatReq()     
        DB.Close() 
        return listePrestations

    def ImportationCaisses(self):
        # Importation des caisses
        DB = GestionDB.DB()
        req = """SELECT IDcaisse, nom
        FROM caisses
        ORDER BY nom
        ;""" 
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeCaisses = DB.ResultatReq()     
        DB.Close() 
        return listeCaisses

    def ImportationChampsPerso(self):
        # Importation des champs personnalisés
        DB = GestionDB.DB()
        req = """SELECT IDchamp, code, label, formule, titre
        FROM etat_nomin_champs
        ORDER BY code
        ;""" 
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeChamps = DB.ResultatReq()     
        DB.Close() 
        return listeChamps

# ----------------------------------------------------------------------------------------------------------------

class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        # Récupération des paramètres perso
        self.selectionID = None
        self.selectionTrack = None
        self.criteres = ""
        self.itemSelected = False
        self.popupIndex = -1
        self.dateMin = None
        self.dateMax = None
        self.listeActivites = []
        # Initialisation du listCtrl
        self.nom_fichier_liste = __file__
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
    
    def SetParametres(self, dateMin=None, dateMax=None, listeActivites=[], listeSelections=[]):
        self.dateMin = dateMin
        self.dateMax = dateMax
        self.listeActivites = listeActivites
        self.listeSelections = listeSelections
    
    def OnItemActivated(self,event):
        self.Modifier(None)

    def InitModel(self):
        champs = Champs(listeActivites=self.listeActivites, dateMin=self.dateMin, dateMax=self.dateMax)
        self.donnees = champs.GetChamps()
    
    def InitObjectListView(self):           
        # ImageList 
        self.AddNamedImages("individu", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Personnes.png"), wx.BITMAP_TYPE_PNG))
        self.AddNamedImages("famille", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Famille.png"), wx.BITMAP_TYPE_PNG))
        self.AddNamedImages("unite", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Etiquette.png"), wx.BITMAP_TYPE_PNG))
        self.AddNamedImages("perso", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_PNG))
        self.AddNamedImages("euro", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Euro.png"), wx.BITMAP_TYPE_PNG))
        self.AddNamedImages("formule", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Formule.png"), wx.BITMAP_TYPE_PNG))
        self.AddNamedImages("temps", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Horloge3.png"), wx.BITMAP_TYPE_PNG))

        def GetImageCode(track):
            if track.categorie == _("Individu") : return "individu"
            if track.categorie == _("Famille") : return "famille"
            if track.type == _("NBRE_UNITE") : return "unite"
            if track.type == _("TEMPS_UNITE") : return "temps"
            if track.type == _("TEMPS_FACTURE_UNITE"): return "euro"
            if track.type == _("MONTANT_PRESTATION") : return "euro"
            if track.type == _("NBRE_AIDES") : return "unite"
            if track.type == _("MONTANT_AIDES") : return "euro"
            if track.type == _("PERSO") : return "perso"
            return None

        def GetImageFormule(track):
            if len(track.formule) > 0 :
                return "formule"
            else :
                return None

        # Couleur en alternance des lignes
        self.oddRowsBackColor = UTILS_Interface.GetValeur("couleur_tres_claire", wx.Colour(240, 251, 237))
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
        
        liste_Colonnes = [
            ColumnDefn(_("ID"), "left", 0, "IDchamp", typeDonnee="entier"),
            ColumnDefn(_("Code"), "left", 200, "code", typeDonnee="texte", imageGetter=GetImageCode),
            ColumnDefn(_("Description"), 'left', 300, "label", typeDonnee="texte"),
            ColumnDefn(_("Titre"), 'left', 120, "titre", typeDonnee="texte"),
            ColumnDefn(_("Catégorie"), 'left', 80, "categorie", typeDonnee="texte"),
            ColumnDefn(_("Formule"), 'left', 150, "formule", typeDonnee="texte", imageGetter=GetImageFormule, isSpaceFilling=True),
            ]
        
        self.SetColumns(liste_Colonnes)
        self.CreateCheckStateColumn(0)
        self.SetEmptyListMsg(_("Aucun champ"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, False, "Tekton"))
        self.SetSortColumn(self.columns[1])
        self.SetObjects(self.donnees)
       
    def MAJ(self, ID=None):
        if ID != None :
            self.selectionID = ID
            self.selectionTrack = None
        else:
            self.selectionID = None
            self.selectionTrack = None
        self.InitModel()
        self.InitObjectListView()
        self.CocheSelections(self.listeSelections) 
        # Sélection d'un item
        if self.selectionTrack != None :
            self.SelectObject(self.selectionTrack, deselectOthers=True, ensureVisible=True)
        self.selectionID = None
        self.selectionTrack = None
        self._ResizeSpaceFillingColumns() 

    def Selection(self):
        return self.GetSelectedObjects()

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        if len(self.Selection()) == 0:
            noSelection = True
        else:
            noSelection = False
                
        # Création du menu contextuel
        menuPop = UTILS_Adaptations.Menu()

        # Item Modifier
        item = wx.MenuItem(menuPop, 10, _("Ajouter"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Ajouter, id=10)
        
        menuPop.AppendSeparator()

        # Item Ajouter
        item = wx.MenuItem(menuPop, 20, _("Modifier"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Modifier, id=20)
        if noSelection == True : item.Enable(False)
        
        # Item Supprimer
        item = wx.MenuItem(menuPop, 30, _("Supprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Supprimer, id=30)
        if noSelection == True : item.Enable(False)
                
        menuPop.AppendSeparator()
    
        # Item Apercu avant impression
        item = wx.MenuItem(menuPop, 40, _("Aperçu avant impression"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=40)
        
        # Item Imprimer
        item = wx.MenuItem(menuPop, 50, _("Imprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=50)
        
        menuPop.AppendSeparator()
    
        # Item Export Texte
        item = wx.MenuItem(menuPop, 600, _("Exporter au format Texte"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Texte2.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.ExportTexte, id=600)
        
        # Item Export Excel
        item = wx.MenuItem(menuPop, 700, _("Exporter au format Excel"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Excel.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.ExportExcel, id=700)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Apercu(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des champs"), format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des champs"), format="A", orientation=wx.PORTRAIT)
        prt.Print()

    def ExportTexte(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(self, titre=_("Liste des champs"))
        
    def ExportExcel(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=_("Liste des champs"))
    
    def GetChamps(self):
        listeChamps = []
        for track in self.donnees :
            listeChamps.append((track.code, track.label))
        return listeChamps
        
    def Ajouter(self, event):
        # Ouverture de la fenêtre de saisie
        from Dlg import DLG_Etat_nomin_saisie
        dlg = DLG_Etat_nomin_saisie.Dialog(self, listeChamps=self.GetChamps())
        if dlg.ShowModal() == wx.ID_OK:
            code = dlg.GetCode() 
            nom = dlg.GetNom() 
            formule = dlg.GetFormule()
            titre = dlg.GetTitre()
            DB = GestionDB.DB()
            listeDonnees = [ ("code", code), ("label", nom), ("formule", formule), (_("titre"), titre),]
            IDchamp = DB.ReqInsert("etat_nomin_champs", listeDonnees)
            DB.Close()
            self.MAJ(IDchamp)
        dlg.Destroy()

    def Modifier(self, event):
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucun champ à modifier dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]
        if track.type != "PERSO" :
            dlg = wx.MessageDialog(self, _("Vous ne pouvez modifier que des champs personnalisés !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        from Dlg import DLG_Etat_nomin_saisie
        dlg = DLG_Etat_nomin_saisie.Dialog(self, listeChamps=self.GetChamps(), IDchamp=track.IDchamp, code=track.code, nom=track.label, formule=track.formule, titre=track.titre)
        if dlg.ShowModal() == wx.ID_OK:
            code = dlg.GetCode() 
            nom = dlg.GetNom() 
            formule = dlg.GetFormule()
            titre = dlg.GetTitre()
            DB = GestionDB.DB()
            listeDonnees = [ ("code", code), ("label", nom), ("formule", formule), ("titre", titre)]
            DB.ReqMAJ("etat_nomin_champs", listeDonnees, "IDchamp", track.IDchamp)
            DB.Close()
            self.MAJ(track.IDchamp)
        dlg.Destroy()

    def Supprimer(self, event):
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucun champ à supprimer dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]
        if track.type != "PERSO" :
            dlg = wx.MessageDialog(self, _("Vous ne pouvez supprimer que des champs personnalisés !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer ce champ ?"), _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
        if dlg.ShowModal() == wx.ID_YES :
            DB = GestionDB.DB()
            DB.ReqDEL("etat_nomin_champs", "IDchamp", track.IDchamp)
            DB.Close() 
            self.MAJ() 
        dlg.Destroy()

    def Selection(self):
        return self.GetSelectedObjects()
    
    def CocheTout(self, event=None):
        for track in self.donnees :
            self.Check(track)
            self.RefreshObject(track)
        
    def CocheRien(self, event=None):
        for track in self.donnees :
            self.Uncheck(track)
            self.RefreshObject(track)
    
    def CocheSelections(self, listeSelections=[]):
        for track in self.donnees :
            if track.code in listeSelections :
                self.Check(track)
                self.RefreshObject(track)
        
    def GetTracksCoches(self):
        return self.GetCheckedObjects()
    
    def GetCodesCoches(self):
        """ Retourne la liste des codes des champs cochés """
        listeCodes = []
        for track in self.GetTracksCoches() :
            listeCodes.append(track.code)
        return listeCodes
            
        

# -------------------------------------------------------------------------------------------------------------------------------------------

class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False
        
        self.SetDescriptiveText(_("Rechercher un champ..."))
        self.ShowSearchButton(True)
        
        self.listView = self.parent.ctrl_listview
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


# -------------------------------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        self.SetSize((600, 600))
        panel = wx.Panel(self, -1, name="test1")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.myOlv = ListView(panel, id=-1, name="OL_test", style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        self.myOlv.SetParametres(dateMin=datetime.date(2012, 1, 1), dateMax=datetime.date(2012, 12, 31), listeActivites=[1, 2, 3])
        self.myOlv.MAJ() 
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.myOlv, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "OL TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()

#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys, Modif des modes de transports ajout intercamp
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB, Jacques Brunel
# Copyright:       (c) 2010-12 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import Chemins
from Utils.UTILS_Traduction import _
import wx
from wx.adv import BitmapComboBox
import datetime
from Utils import UTILS_Utilisateurs

import GestionDB
from Ctrl import CTRL_ChoixListe

from Ctrl import CTRL_Saisie_date
from Ctrl import CTRL_Saisie_heure
from Dlg import DLG_Saisie_adresse

from Data.DATA_Tables import DB_DATA as DICT_TABLES

# catégories de moyens de transports et des contrôles qui devront être visibles
DICT_CATEGORIES = {

    "avion" : {         "label" : _("Avion"), "image" : "Avion",
                        "type" : "lieux",
                        "controles" :["compagnie_avion", "numero_avion", "details", "observations","date_heure", "aeroport"]},

    "bus" : {           "label" : _("Bus grandes Lignes"), "image" : "Bus",
                        "type" : "lieux",
                        "controles" : ["ligne_bus", "observations","date_heure", "gare"],},

    "intercamp" : {     "label" : _("Inter-camp"),     "image" : "Horloge3",
                        "controles" :["observations","date", "arret_intercamp"]},

    "navette" : {       "label" : _("Navette du Camp"), "image" : "Bus",
                        "type" : "lieux",
                        "controles" : [ "ligne_navette", "observations","date","arret_navette"]},

    "train" : {         "label" : _("Train"),             "image" : "Train",
                        "type" : "lieux",
                        "controles" : [ "ligne_train", "numero_train", "observations","date_heure", "gare"]},

    "voiture" : {       "label" : _("Voiture Parents"), "image" : "Voiture",
                        "type" : "lieux",
                        "controles" : ["observations","date", "gare"]},

    "noTransport" : {   "label" : _("Pas de transport"), "image" : "Pedibus",
                        "controles" : []},
    }

#définition des différents contrôles pouvant être utilisés, tous sont positionnés en aveugle
"""
la valeur de "ctrl" sera exécutée par eval(), la valeur de 'catégorie' du ctrl  n'est pas celle de DICT_CATEGORIES de ce module.
 C'est la catégorie utilisée dans les tables des items, mais aussi dans les DIC_CATEGORIES des modules: DLG_Arrets,DLG_Lignes etc.
On veillera à ce que le dernier mot du code du contrôle soit celui de sa catégorie car plus facile à extraire.
"""
DICT_CONTROLES = {
    "generalites" : [
        {"code" : "compagnie_avion", "label" : _("Compagnie"), "ctrl" : "CTRL_Compagnies(self, categorie='avion')",},

        {"code" : "ligne_bus", "label" : _("Ligne Bus"), "ctrl" : "CTRL_Lignes(self, categorie='bus')" },
        {"code" : "ligne_navette", "label" : _("Ligne Matthania"), "ctrl" : "CTRL_Lignes(self, categorie='navette')" },
        {"code" : "ligne_train", "label" : _("Ligne Train"), "ctrl" : "CTRL_Lignes(self, categorie='train')" },

        {"code" : "numero_avion", "label" : _("N° de vol"), "ctrl" : "CTRL_Numero(self, categorie='avion')" },
        {"code" : "numero_train", "label" : _("N° de train"), "ctrl" : "CTRL_Numero(self, categorie='train')" },

        {"code" : "details", "label" : _("Détails"), "ctrl" : "CTRL_Details(self)" },
        {"code" : "observations", "label" : _("Observ."), "ctrl" : "CTRL_Observations(self)" },
        ],
        
    "depart" : [
        {"code": "date",       "label": _("Date"),             "ctrl": "CTRL_Date(self)" },
        {"code": "date_heure", "label": _("Heure"),            "ctrl": "CTRL_DateHeure(self)" },

        {"code": "arret_intercamp",  "label": _("Finit intercamp"),   "ctrl": "CTRL_Arrets(self, categorie='intercamp')"},
        {"code": "arret_navette","label": _("Info sur pièce"), "ctrl": "CTRL_Arrets(self, categorie='navette')"},

        {"code": "aeroport",   "label": _("Aéroport"),         "ctrl": "CTRL_Lieux(self, categorie='aeroport')" },
        {"code": "gare",       "label": _("Gare/Lieu"),        "ctrl": "CTRL_Lieux(self, categorie='gare')" },
        {"code": "localisation","label": _("Localisation"),    "ctrl": "CTRL_Localisation(self)" },
        ],

    "arrivee" : [
        {"code": "date",       "label": _("Date"),             "ctrl": "CTRL_Date(self)" },
        {"code": "date_heure", "label": _("Heure"),            "ctrl": "CTRL_DateHeure(self)" },

        {"code": "arret_intercamp",  "label": _("Débute intercamp"),   "ctrl": "CTRL_Arrets(self, categorie='intercamp')"},
        {"code": "arret_navette","label": _("Info sur pièce"), "ctrl": "CTRL_Arrets(self, categorie='navette')"},

        {"code": "aeroport",   "label": _("Aéroport"),         "ctrl": "CTRL_Lieux(self, categorie='aeroport')" },
        {"code": "gare",       "label": _("Gare/Lieu"),        "ctrl": "CTRL_Lieux(self, categorie='gare')" },
        {"code": "localisation","label": _("Localisation"),    "ctrl": "CTRL_Localisation(self)" },
        ],
}

# le lancement des actions menus est dans 'MenuTransports.dict_actions', qui pointe les fonctions idoines A GERER

def GetDic_rub_ctrl_Utiles():
    # retourne la structure DICT_CONTROLES épuré des contrôles non présents dans DICT_CATEGORIES[x]["controles"], donc inutiles
    dict_controles = {"generalites":[],"depart":[],"arrivee":[]}
    for categorie, dicCategorie in DICT_CATEGORIES.items():
        for ctrl in dicCategorie["controles"]:
            for rubrique in ("generalites","depart","arrivee"):
                for dicCtrl in DICT_CONTROLES[rubrique]:
                        if ctrl == dicCtrl["code"]:
                            if not dicCtrl in dict_controles[rubrique]:
                                dict_controles[rubrique].append(dicCtrl)
    return dict_controles

def GetDic_ctrl_Utiles():
    # retourne un dictionnaire avec pour clé le nom du controle
    dicControles = {}
    for rubrique,lstCtrl in GetDic_rub_ctrl_Utiles().items():
        for ctrl in lstCtrl:
            cle = ctrl["code"]
            dicControles[cle] = ctrl
    return dicControles

def DateEngEnDateDD(dateEng):
    if dateEng and not isinstance(dateEng,str): dateEng = str(dateEng)
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

#------------------------------------------------------------------------------------------------------

class MenuTransports(object):
    # Penser à gérer les lancements bind du menu dans self.dict_actions
    def __init__(self,parent):
        if hasattr(parent,"parent"):
            self.parent = parent.parent
        else: self.parent = parent
        self.dict_actions = {   "lignes": {
                                        "train": self.On_param_lignes_train,
                                        "pedibus": self.On_param_lignes_pedibus,
                                        "navette": self.On_param_lignes_navette,
                                        "intercamp": self.On_param_lignes_intercamp,
                                        "car": self.On_param_lignes_car,
                                        "bus": self.On_param_lignes_bus,
                                        "bateau": self.On_param_lignes_bateau,},
                                "lieux": {
                                        "port": self.On_param_lieux_port,
                                        "gare": self.On_param_lieux_gare,
                                        "aeroport": self.On_param_lieux_aeroport,},
                                "compagnies": {
                                        "train": self.On_param_compagnies_train,
                                        "taxi": self.On_param_compagnies_taxi,
                                        "navette": self.On_param_compagnies_navette,
                                        "intercamp": self.On_param_compagnies_intercamp,
                                        "car": self.On_param_compagnies_car,
                                        "bus": self.On_param_compagnies_bus,
                                        "bateau": self.On_param_compagnies_bateau,
                                        "avion": self.On_param_compagnies_avion,},
                                "arrets": {
                                        "pedibus": self.On_param_arrets_pedibus,
                                        "navette": self.On_param_arrets_navette,
                                        "intercamp": self.On_param_arrets_intercamp,
                                        "car": self.On_param_arrets_car,
                                        "bus": self.On_param_arrets_bus,
                                        "bateau": self.On_param_arrets_bateau,}
                            }

    # génération des options du sous-menu transports de Noethys
    def GetMenuTransports(self):
        from Dlg import DLG_Arrets
        from Dlg import DLG_Lignes
        from Dlg import DLG_Compagnies
        from Dlg import DLG_Lieux
        dicControles = GetDic_ctrl_Utiles()
        lstNomsMenuCategories = []
        lstDicMenuCategories = []
        dicNatures = {  "arrets":    DLG_Arrets.DICT_CATEGORIES,
                        "lignes":    DLG_Lignes.DICT_CATEGORIES,
                        "lieux":     DLG_Lieux.DICT_CATEGORIES,
                        "compagnies":DLG_Compagnies.DICT_CATEGORIES}

        dicMenuTransport = {
                    "code": "menu_parametrage_transports",
                    "label": _("Transports"),
                    "items": lstDicMenuCategories}

        # l'ordre du menu sera celui des catégories dans DICT_CATEGORIES
        for categorie,dicCategorie in DICT_CATEGORIES.items():
            dicItemCategorie = {}
            # l'ordre du sous menu sera celui des controles décrits dans DICT_CATEGORIES['controles']
            for codeCtrl in dicCategorie['controles']:
                dicCtrl = dicControles[codeCtrl]
                appel = dicCtrl["ctrl"]
                lstMotsAppel = appel.split("_")
                if lstMotsAppel[0] != "CTRL":
                    wx.MessageBox("Erreur dans Menu/paramétrages/Transports\n\nCf dans CTRL_Saisie_transport, item: %s"%appel)
                    return {}
                appel = appel[5:]
                lstMotsAppel = appel.split("(")
                nature = lstMotsAppel[0].lower()
                if not nature in ("compagnies","lignes","arrets","lieux"):
                    continue
                # composition d'une ligne categorie dans le menu
                if not categorie in lstNomsMenuCategories:
                    lstDicMenuCategories.append({"code": "menu_parametrage_transports_%s"%categorie,
                                                 "label": _("%s"%(categorie.capitalize())),
                                                 "items":[]})
                    lstNomsMenuCategories.append(categorie)

                # composition d'un sous menu
                catCtrl = codeCtrl.split("_")[-1]
                nomImage = dicNatures[nature.lower()][catCtrl]["image"]
                label = dicNatures[nature.lower()][catCtrl]["pluriel"]

                dicItem = { "code": "%s_%s"%(nature,categorie.lower()),
                            "label": _("%s")%(label),
                            "infobulle": _("Paramétrage %s de %s")%(nature,categorie.lower()),
                            "image": "Images/16x16/%s.png"%nomImage,
                            "action": self.GetOnParam(nature,catCtrl)}
                ix = lstNomsMenuCategories.index(categorie)
                lstDicMenuCategories[ix]["items"].append(dicItem)
        return dicMenuTransport

    def GetOnParam(self,nature, categorie):
        # Retourne la fonction qui sera appellé par le bind dans le menu
        fnct = self.OnEchec
        if nature in list(self.dict_actions.keys()):
            if categorie in list(self.dict_actions[nature].keys()):
                fnct = self.dict_actions[nature][categorie]
        return fnct

    # cas où la fonction n'est pas répertoriée dans self.dict_actions
    def OnEchec(self,event):
        return

    def On_param_compagnies_bus(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_compagnies", "consulter") == False : return
        from Dlg import DLG_Compagnies
        dlg = DLG_Compagnies.Dialog(self.parent, categorie="bus", mode="gestion")
        dlg.ShowModal() 
        dlg.Destroy()

    def On_param_compagnies_car(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_compagnies", "consulter") == False : return
        from Dlg import DLG_Compagnies
        dlg = DLG_Compagnies.Dialog(self.parent, categorie="car", mode="gestion")
        dlg.ShowModal() 
        dlg.Destroy()

    def On_param_compagnies_navette(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_compagnies", "consulter") == False : return
        from Dlg import DLG_Compagnies
        dlg = DLG_Compagnies.Dialog(self.parent, categorie="navette", mode="gestion")
        dlg.ShowModal() 
        dlg.Destroy()

    def On_param_compagnies_taxi(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_compagnies", "consulter") == False : return
        from Dlg import DLG_Compagnies
        dlg = DLG_Compagnies.Dialog(self.parent, categorie="taxi", mode="gestion")
        dlg.ShowModal() 
        dlg.Destroy()

    def On_param_compagnies_avion(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_compagnies", "consulter") == False : return
        from Dlg import DLG_Compagnies
        dlg = DLG_Compagnies.Dialog(self.parent, categorie="avion", mode="gestion")
        dlg.ShowModal() 
        dlg.Destroy()

    def On_param_compagnies_bateau(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_compagnies", "consulter") == False : return
        from Dlg import DLG_Compagnies
        dlg = DLG_Compagnies.Dialog(self.parent, categorie="bateau", mode="gestion")
        dlg.ShowModal() 
        dlg.Destroy()

    def On_param_compagnies_train(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_compagnies", "consulter") == False : return
        from Dlg import DLG_Compagnies
        dlg = DLG_Compagnies.Dialog(self.parent, categorie="train", mode="gestion")
        dlg.ShowModal() 
        dlg.Destroy()

    def On_param_compagnies_intercamp(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_compagnies", "consulter") == False : return
        from Dlg import DLG_Compagnies
        dlg = DLG_Compagnies.Dialog(self.parent, categorie="intercamp", mode="gestion")
        dlg.ShowModal() 
        dlg.Destroy()

    def On_param_lieux_gare(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_lieux", "consulter") == False : return
        from Dlg import DLG_Lieux
        dlg = DLG_Lieux.Dialog(self.parent, categorie="gare", mode="gestion")
        dlg.ShowModal() 
        dlg.Destroy()

    def On_param_lieux_aeroport(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_lieux", "consulter") == False : return
        from Dlg import DLG_Lieux
        dlg = DLG_Lieux.Dialog(self.parent, categorie="aeroport", mode="gestion")
        dlg.ShowModal() 
        dlg.Destroy()

    def On_param_lieux_port(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_lieux", "consulter") == False : return
        from Dlg import DLG_Lieux
        dlg = DLG_Lieux.Dialog(self.parent, categorie="port", mode="gestion")
        dlg.ShowModal() 
        dlg.Destroy()

    def On_param_lieux_station(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_lieux", "consulter") == False : return
        from Dlg import DLG_Lieux
        dlg = DLG_Lieux.Dialog(self.parent, categorie="station", mode="gestion")
        dlg.ShowModal() 
        dlg.Destroy()

    def On_param_lignes_bus(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_lignes", "consulter") == False : return
        from Dlg import DLG_Lignes
        dlg = DLG_Lignes.Dialog(self.parent, categorie="bus", mode="gestion")
        dlg.ShowModal() 
        dlg.Destroy()

    def On_param_lignes_car(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_lignes", "consulter") == False : return
        from Dlg import DLG_Lignes
        dlg = DLG_Lignes.Dialog(self.parent, categorie="car", mode="gestion")
        dlg.ShowModal() 
        dlg.Destroy()

    def On_param_lignes_train(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_lignes", "consulter") == False : return
        from Dlg import DLG_Lignes
        dlg = DLG_Lignes.Dialog(self.parent, categorie="train", mode="gestion")
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_lignes_navette(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_lignes", "consulter") == False : return
        from Dlg import DLG_Lignes
        dlg = DLG_Lignes.Dialog(self.parent, categorie="navette", mode="gestion")
        dlg.ShowModal() 
        dlg.Destroy()

    def On_param_lignes_bateau(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_lignes", "consulter") == False : return
        from Dlg import DLG_Lignes
        dlg = DLG_Lignes.Dialog(self.parent, categorie="bateau", mode="gestion")
        dlg.ShowModal() 
        dlg.Destroy()

    def On_param_lignes_intercamp(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_lignes", "consulter") == False : return
        from Dlg import DLG_Lignes
        dlg = DLG_Lignes.Dialog(self.parent, categorie="intercamp", mode="gestion")
        dlg.ShowModal() 
        dlg.Destroy()

    def On_param_lignes_pedibus(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_lignes", "consulter") == False : return
        from Dlg import DLG_Lignes
        dlg = DLG_Lignes.Dialog(self.parent, categorie="pedibus", mode="gestion")
        dlg.ShowModal() 
        dlg.Destroy()

    def On_param_arrets_bus(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_arrets", "consulter") == False : return
        from Dlg import DLG_Arrets
        dlg = DLG_Arrets.Dialog(self.parent, categorie="bus")
        dlg.ShowModal() 
        dlg.Destroy()

    def On_param_arrets_navette(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_arrets", "consulter") == False : return
        from Dlg import DLG_Arrets
        dlg = DLG_Arrets.Dialog(self.parent, categorie="navette")
        dlg.ShowModal() 
        dlg.Destroy()

    def On_param_arrets_car(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_arrets", "consulter") == False : return
        from Dlg import DLG_Arrets
        dlg = DLG_Arrets.Dialog(self.parent, categorie="car")
        dlg.ShowModal() 
        dlg.Destroy()

    def On_param_arrets_bateau(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_arrets", "consulter") == False : return
        from Dlg import DLG_Arrets
        dlg = DLG_Arrets.Dialog(self.parent, categorie="bateau")
        dlg.ShowModal() 
        dlg.Destroy()

    def On_param_arrets_intercamp(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_arrets", "consulter") == False : return
        from Dlg import DLG_Arrets
        dlg = DLG_Arrets.Dialog(self.parent, categorie="intercamp")
        dlg.ShowModal() 
        dlg.Destroy()

    def On_param_arrets_pedibus(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_arrets", "consulter") == False : return
        from Dlg import DLG_Arrets
        dlg = DLG_Arrets.Dialog(self.parent, categorie="pedibus")
        dlg.ShowModal() 
        dlg.Destroy()

#------------------------------------------------------------------------------------------------------

class CTRL_Choix_arrets(wx.Choice):
    def __init__(self, parent, categorie="bus", IDligne=0):
        wx.Choice.__init__(self, parent, -1, size=(170, -1))
        self.parent = parent
        self.categorie = categorie
        self.IDligne = IDligne
        self.MAJ() 
        self.Select(0)
        self.SetToolTip(_("Sélectionnez ici un arrêt"))
    
    def MAJ(self, IDligne=0):
        if IDligne == None : IDligne = 0
        self.IDligne = IDligne
        listeItems = self.GetListeDonnees()
        if len(listeItems) == 1 :
            self.Enable(True)
        else:
            self.Enable(True)
        self.SetItems(listeItems)
                                        
    def GetListeDonnees(self):
        # appel des arrêts de la ligne
        if self.IDligne == 0 and self.categorie != "intercamp":
            listeDonnees = []
        else:
            db = GestionDB.DB()
            req = """SELECT IDarret, nom
            FROM transports_arrets
            WHERE IDligne=%d
            ORDER BY ordre; """ % self.IDligne
            db.ExecuterReq(req)
            ret = db.ResultatReq()
            listeDonnees = [item for item in ret]
            db.Close()
        listeItems = []
        self.dictDonnees = {}
        index = 0
        # Si pas d'arrêts gérés ou plusieurs arrêts possibles, ajout d'un choix par défaut
        if len(listeDonnees) != 1:
            listeDonnees.insert(0,(0,"à préciser"))
        for IDarret, nom in listeDonnees :
            self.dictDonnees[index] = {"ID" : IDarret, "nom " : nom}
            listeItems.append(nom)
            index += 1
        return listeItems

    def SetID(self, ID=0):
        if ID == None :
            self.SetSelection(0)
        elif ID == 0:
            self.SetSelection(0)
        else:
            for index, values in self.dictDonnees.items():
                if values["ID"] == ID :
                     self.SetSelection(index)

    def GetID(self):
        index = self.GetSelection()
        if index == -1 : return None
        return self.dictDonnees[index]["ID"]

class CTRL_Arrets(wx.Panel):
    """ Contrôle Choix des arrêts """
    def __init__(self, parent, categorie="bus"):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.categorie = categorie

        self.ctrl_arrets = CTRL_Choix_arrets(self, categorie=categorie)
        self.bouton_gestion = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Mecanisme.png"), wx.BITMAP_TYPE_ANY))
        
        self.Bind(wx.EVT_BUTTON, self.OnBoutonGestion, self.bouton_gestion)
        self.bouton_gestion.SetToolTip(_("Cliquez ici pour accéder au paramétrage des arrêts"))

        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_base.Add(self.ctrl_arrets, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.EXPAND, 0)
        grid_sizer_base.Add(self.bouton_gestion, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 0)
        grid_sizer_base.AddGrowableCol(0)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        self.Layout()

    def OnBoutonGestion(self, event): 
        from Dlg import DLG_Arrets
        dlg = DLG_Arrets.Dialog(self, categorie=self.categorie,ligne= self.GetLigneParent())
        dlg.ShowModal() 
        dlg.Destroy()
        # MAJ contrôles
        for controle in self.parent.GetControles("arret_%s" % self.categorie) :
            controle.MAJ() 
        for controle in self.parent.GetControles("ligne_%s" % self.categorie) :
            controle.MAJ() 

    def MAJ(self, IDligne=False):
        IDarret = self.ctrl_arrets.GetID()
        if not IDligne or IDligne == False :
            IDligne = self.ctrl_arrets.IDligne
        self.ctrl_arrets.MAJ(IDligne)
        self.ctrl_arrets.SetID(IDarret)
        
    def SetArret(self, IDarret=None):
        self.ctrl_arrets.SetID(IDarret)
        
    def GetArret(self):
        return self.ctrl_arrets.GetID()

    def GetLigneParent(self):
        # recherche de la ligne de l'arret pointé par le contrôle
        IDarret = self.GetArret()
        if not IDarret: return None

        db = GestionDB.DB()
        req = """SELECT IDligne
        FROM transports_arrets
        WHERE IDarret=%d
        ; """ %IDarret
        db.ExecuterReq(req)
        ret = db.ResultatReq()
        IDligne = None
        if len(ret)>0:
            IDligne = ret[0][0]
        return IDligne

    def Validation(self):
        return True
    
    def GetData(self):
        key = "%s_IDarret" % self.rubrique
        valeur = self.GetArret() 
        return {key : valeur}
    
    def SetData(self, listeDonnees=[]):
        for key, valeur in listeDonnees :
            if key == "%s_IDarret" % self.rubrique :
                self.SetArret(valeur)

#------------------------------------------------------------------------------------------------------

class CTRL_Choix_lignes(wx.Choice):
    def __init__(self, parent, categorie="bus"):
        wx.Choice.__init__(self, parent, -1, size=(170, -1)) 
        self.parent = parent
        self.categorie = categorie
        self.MAJ() 
        self.Select(0)
        self.SetToolTip(_("Sélectionnez ici une ligne"))
    
    def MAJ(self):
        listeItems = self.GetListeDonnees()
        if len(listeItems) == 1 :
            self.Enable(False)
        else:
            self.Enable(True)
        self.SetItems(listeItems)
                                        
    def GetListeDonnees(self):
        db = GestionDB.DB()
        req = """SELECT IDligne, nom
        FROM transports_lignes
        WHERE categorie='%s' 
        ORDER BY nom; """ % self.categorie
        db.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = db.ResultatReq()
        db.Close()
        listeItems = ["",]
        self.dictDonnees = {}
        self.dictDonnees[0] = { "ID" : 0, "nom" : _("Inconnue")}
        index = 1
        for IDligne, nom in listeDonnees :
            self.dictDonnees[index] = { "ID" : IDligne, "nom " : nom}
            listeItems.append(nom)
            index += 1
        return listeItems

    def SetID(self, ID=0):
        if ID == None :
            self.SetSelection(0)
        for index, values in self.dictDonnees.items():
            if values["ID"] == ID :
                 self.SetSelection(index)

    def GetID(self):
        index = self.GetSelection()
        if index == -1 or index == 0 : return None
        return self.dictDonnees[index]["ID"]

class CTRL_Lignes(wx.Panel):
    """ Contrôle Choix de Lignes """
    def __init__(self, parent, categorie="bus"):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.categorie = categorie
        
        self.ctrl_lignes = CTRL_Choix_lignes(self, categorie=categorie)
        self.bouton_gestion = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Mecanisme.png"), wx.BITMAP_TYPE_ANY))
        self.Bind(wx.EVT_CHOICE, self.OnChoix, self.ctrl_lignes)
        
        self.Bind(wx.EVT_BUTTON, self.OnBoutonGestion, self.bouton_gestion)
        self.bouton_gestion.SetToolTip(_("Cliquez ici pour accéder au paramétrage des lignes"))

        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_base.Add(self.ctrl_lignes, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.EXPAND, 0)
        grid_sizer_base.Add(self.bouton_gestion, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 0)
        grid_sizer_base.AddGrowableCol(0)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        self.Layout()

    def OnChoix(self, event):
        # MAJ contrôles arrêts
        for controle in self.parent.GetControles("arret_%s" % self.categorie) :
            controle.MAJ(IDligne=self.GetLigne())

    def MAJ(self):
        IDligne = self.ctrl_lignes.GetID()
        self.ctrl_lignes.MAJ()
        self.ctrl_lignes.SetID(IDligne)

    def OnBoutonGestion(self, event): 
        IDligne = self.ctrl_lignes.GetID()
        from Dlg import DLG_Lignes
        dlg = DLG_Lignes.Dialog(self, categorie=self.categorie, mode="gestion")
        dlg.ShowModal() 
        dlg.Destroy()
        self.ctrl_lignes.MAJ() 
        if IDligne == None : IDligne = 0
        self.ctrl_lignes.SetID(IDligne)
    
    def SetLigne(self, IDligne=None):
        self.ctrl_lignes.SetID(IDligne)
        
    def GetLigne(self):
        return self.ctrl_lignes.GetID()

    def Validation(self):
        return True

    def GetData(self):
        key = "IDligne"
        valeur = self.GetLigne() 
        return {key : valeur}

    def SetData(self, listeDonnees=[]):
        for key, valeur in listeDonnees :
            if key == "IDligne" :
                self.SetLigne(valeur)
                self.OnChoix(None)

#------------------------------------------------------------------------------------------------------

class CTRL_Localisation_domicile(wx.Panel):
    """ Contrôle Domicile pour CTRL Localisation """
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        rue_resid = ""
        cp_resid = ""
        ville_resid = ""
        
        # Recherche de l'adresse de l'individu
##        DB = GestionDB.DB()
##        req = """SELECT adresse_auto, rue_resid, cp_resid, ville_resid FROM individus WHERE IDindividu=%d;""" % IDindividu
##        DB.ExecuterReq(req,MsgBox="ExecuterReq")
##        listeDonnees = DB.ResultatReq()
##        if len(listeDonnees) > 0  :
##            adresse_auto, rue_resid, cp_resid, ville_resid = listeDonnees[0]
##            if adresse_auto != None :
##                req = """SELECT rue_resid, cp_resid, ville_resid FROM individus WHERE IDindividu=%d;""" % adresse_auto
##                DB.ExecuterReq(req,MsgBox="ExecuterReq")
##                listeDonnees = DB.ResultatReq()
##                if len(listeDonnees) > 0  :
##                    rue_resid, cp_resid, ville_resid = listeDonnees[0]
##        DB.Close()
##        
##        if rue_resid == None : rue_resid = ""
##        if cp_resid == None : cp_resid = ""
##        if ville_resid == None : ville_resid = ""
##
##        # Affichage
##        texte = "%s\n%s %s" % (rue_resid, cp_resid, ville_resid)
##        self.label_heure = wx.StaticText(self, -1, texte)
    
    def GetLocalisation(self):
        return "DOMI"
    
    def SetLocalisation(self, valeur=""):
        pass
        
    def Validation(self):
        return True

class CTRL_Choix_activite(wx.Choice):
    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1, size=(-1, -1)) 
        self.parent = parent
        self.MAJ() 
        self.Select(0)
        self.SetToolTip(_("Sélectionnez ici une activité"))
    
    def MAJ(self):
        listeItems = self.GetListeDonnees()
        if len(listeItems) == 1 :
            self.Enable(False)
        else:
            self.Enable(True)
        self.SetItems(listeItems)
                                        
    def GetListeDonnees(self):
        db = GestionDB.DB()
        req = """SELECT IDactivite, nom
        FROM activites
        ORDER BY date_fin DESC;"""
        db.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = db.ResultatReq()
        db.Close()
        listeItems = ["",]
        self.dictDonnees = {}
        self.dictDonnees[0] = { "ID" : 0, "nom" : ""}
        index = 1
        for IDactivite, nom in listeDonnees :
            if nom == None : nom = "Activité inconnue"
            self.dictDonnees[index] = { "ID" : IDactivite, "nom " : nom}
            listeItems.append(nom)
            index += 1
        return listeItems

    def SetID(self, ID=0):
        if ID == None :
            self.SetSelection(0)
        for index, values in self.dictDonnees.items():
            if values["ID"] == ID :
                 self.SetSelection(index)

    def GetID(self):
        index = self.GetSelection()
        if index == -1 or index == 0 : return None
        return self.dictDonnees[index]["ID"]

class CTRL_Localisation_activite(wx.Panel):
    """ Contrôle Activité pour CTRL Localisation """
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent

        self.label_activite = wx.StaticText(self, -1, _("Activité :"))
        self.ctrl_activite = CTRL_Choix_activite(self)
        
        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=4, vgap=5, hgap=5)
        grid_sizer_base.Add(self.label_activite, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 0)
        grid_sizer_base.Add(self.ctrl_activite, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.EXPAND, 0)
        grid_sizer_base.AddGrowableCol(1)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        self.Layout()

    def GetLocalisation(self):
        IDactivite = self.ctrl_activite.GetID()
        if IDactivite == None : 
            IDactivite = 0
        return "ACTI;%d" % IDactivite
    
    def SetLocalisation(self, valeur=""):
        code, IDactivite = valeur.split(";")
        self.ctrl_activite.SetID(int(IDactivite))

    def Validation(self):
        if self.ctrl_activite.GetID() == None :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune activité !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.SetFocus()
            return False
        return True

class CTRL_Choix_ecole(wx.Choice):
    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1, size=(-1, -1)) 
        self.parent = parent
        self.MAJ() 
        self.Select(0)
        self.SetToolTip(_("Sélectionnez ici une école"))
    
    def MAJ(self):
        listeItems = self.GetListeDonnees()
        if len(listeItems) == 1 :
            self.Enable(False)
        else:
            self.Enable(True)
        self.SetItems(listeItems)
                                        
    def GetListeDonnees(self):
        db = GestionDB.DB()
        req = """SELECT IDecole, nom
        FROM ecoles
        ORDER BY nom;"""
        db.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = db.ResultatReq()
        db.Close()
        listeItems = ["",]
        self.dictDonnees = {}
        self.dictDonnees[0] = { "ID" : 0, "nom" : ""}
        index = 1
        for IDecole, nom in listeDonnees :
            self.dictDonnees[index] = { "ID" : IDecole, "nom " : nom}
            listeItems.append(nom)
            index += 1
        return listeItems

    def SetID(self, ID=0):
        if ID == None :
            self.SetSelection(0)
        for index, values in self.dictDonnees.items():
            if values["ID"] == ID :
                 self.SetSelection(index)

    def GetID(self):
        index = self.GetSelection()
        if index == -1 or index == 0 : return None
        return self.dictDonnees[index]["ID"]

class CTRL_Localisation_ecole(wx.Panel):
    """ Contrôle Ecole pour CTRL Localisation """
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent

        self.label_ecole = wx.StaticText(self, -1, _("Ecole :"))
        self.ctrl_ecole = CTRL_Choix_ecole(self)
        
        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=4, vgap=5, hgap=5)
        grid_sizer_base.Add(self.label_ecole, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 0)
        grid_sizer_base.Add(self.ctrl_ecole, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.EXPAND, 0)
        grid_sizer_base.AddGrowableCol(1)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        self.Layout()
    
    def GetLocalisation(self):
        IDecole = self.ctrl_ecole.GetID()
        if IDecole == None : 
            IDecole = 0
        return "ECOL;%d" % IDecole
    
    def SetLocalisation(self, valeur=""):
        code, IDecole = valeur.split(";")
        self.ctrl_ecole.SetID(int(IDecole))

    def Validation(self):
        if self.ctrl_ecole.GetID() == None :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune école !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.SetFocus()
            return False
        return True

class CTRL_Localisation_autre(wx.Panel):
    """ Contrôle Autre pour CTRL Localisation """
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        
        self.nom = ""
        self.rue = ""
        self.cp = ""
        self.ville = ""
        
        self.label_adresse = wx.StaticText(self, -1, _("Adresse :"))
        self.ctrl_adresse = wx.TextCtrl(self, -1, "", style=wx.TE_READONLY)
        self.bouton_modifier = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_ANY))
        
        self.Bind(wx.EVT_BUTTON, self.OnBoutonModifier, self.bouton_modifier)
        self.bouton_modifier.SetToolTip(wx.ToolTip(_("Cliquez ici pour saisir ou modifier l'adresse")))

        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=4, vgap=5, hgap=5)
        grid_sizer_base.Add(self.label_adresse, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 0)
        grid_sizer_base.Add(self.ctrl_adresse, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.EXPAND, 0)
        grid_sizer_base.Add(self.bouton_modifier, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 0)
        grid_sizer_base.AddGrowableCol(1)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        self.Layout()
    
    def SetAdresse(self, nom="", rue="", cp="", ville=""):
        self.nom = nom
        self.rue = rue
        self.cp = cp
        self.ville = ville
        if self.nom == None : self.nom = ""
        if self.rue == None : self.rue = ""
        if self.cp == None : self.cp = ""
        if self.ville == None : self.ville = ""
        texte = "%s %s %s %s" % (self.nom, self.rue, self.cp, self.ville)
        self.ctrl_adresse.SetValue(texte)
    
    def OnBoutonModifier(self, event):
        dlg = DLG_Saisie_adresse.Dialog(self)
        dlg.SetNom(self.nom)
        dlg.SetRue(self.rue) 
        dlg.SetCp(self.cp) 
        dlg.SetVille(self.ville) 
        if dlg.ShowModal() == wx.ID_OK:
            nom = dlg.GetNom()
            rue = dlg.GetRue() 
            cp = dlg.GetCp()
            ville = dlg.GetVille()
            self.SetAdresse(nom, rue, cp, ville) 
        dlg.Destroy()
        
    def GetLocalisation(self):
        return "AUTR;%s;%s;%s;%s" % (self.nom, self.rue, self.cp, self.ville)
    
    def SetLocalisation(self, valeur=""):
        code, nom, rue, cp, ville = valeur.split(";")
        self.SetAdresse(nom, rue, cp, ville)

    def Validation(self):
        return True

class CTRL_Localisation(wx.Choicebook):
    """ Contrôle Localisation """
    def __init__(self, parent):
        wx.Choicebook.__init__(self, parent, id=-1)
        self.parent = parent
        self.SetToolTip(wx.ToolTip(_("Sélectionnez ici une localisation")))
        
        self.listePanels = [
            ("DOMI", _("Domicile de l'individu"), CTRL_Localisation_domicile(self) ),
            ("ACTI", _("Une activité"), CTRL_Localisation_activite(self) ),
            ("ECOL", _("Une école"), CTRL_Localisation_ecole(self) ),
            #("CONT", _("Contact du carnet d'adresses"), wx.Panel(self, -1) ),
            ("AUTR", _("Autre"), CTRL_Localisation_autre(self) ),
            ]
        
        for code, label, ctrl in self.listePanels :
            self.AddPage(ctrl, label)
            
        # Sélection par défaut
        self.SetSelection(3)
    
    def GetLocalisation(self):
        ctrl = self.listePanels[self.GetSelection()][2]
        return ctrl.GetLocalisation()

    def SetLocalisation(self, valeur=""):
        if valeur == None : valeur = ""
        codePage = valeur.split(";")[0]
        index = 0
        for code, label, ctrl in self.listePanels :
            if code == codePage :
                ctrl.SetLocalisation(valeur)
                self.SetSelection(index)
            index += 1

    def Validation(self):
        ctrl = self.listePanels[self.GetSelection()][2]
        return ctrl.Validation()

    def GetData(self):
        key = "%s_localisation" % self.rubrique
        valeur = self.GetLocalisation() 
        return {key : valeur}

    def SetData(self, listeDonnees=[]):
        for key, valeur in listeDonnees :
            if key == "%s_localisation" % self.rubrique :
                self.SetLocalisation(valeur)

#------------------------------------------------------------------------------------------------------

class CTRL_DateHeure(wx.Panel):
    """ Contrôle Date et Heure """
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        
        self.ctrl_heure = CTRL_Saisie_heure.Heure(self)
        self.label_date = wx.StaticText(self, -1, _("Date :"))
        self.ctrl_date = CTRL_Saisie_date.Date2(self)
        
        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=4, vgap=5, hgap=5)
        grid_sizer_base.Add(self.ctrl_heure, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 0)
        grid_sizer_base.Add( (5, 5), 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 0)
        grid_sizer_base.Add(self.label_date, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 0)
        grid_sizer_base.Add(self.ctrl_date, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 0)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        self.Layout()
    
    def AffichageDate(self, etat=True):
        """ Affiche ou non le contrôle Date """
        self.label_date.Show(etat)
        self.ctrl_date.Show(etat)
        
    def OnChoixDate(self):
        if self.GetDate() != None and self.rubrique == "depart" :
            ctrl = self.parent.GetControle(code="date_heure", rubrique="arrivee")
            if ctrl and ctrl.GetDate() == None :
                ctrl.SetDate(self.GetDate())
        # Vérification si possible versus dates d'activité
        if hasattr(self.parent.parent,"VerifDatesActivite"):
            self.parent.parent.VerifDatesActivite()

    
    def SetDateTime(self, datedt=None):
        """ Remplit les contrôles à partir d'un datetime date + heure """
        self.SetDate(datetime.date(datedt.year, datedt.month, datedt.day))
        self.SetHeure("%02d:%02d" % (datedt.hour, datedt.minute))
        
    def SetDate(self, date=None):
        self.ctrl_date.SetDate(date)
        
    def GetDate(self):
        return self.ctrl_date.GetDate()

    def SetHeure(self, heure=None):
        self.ctrl_heure.SetHeure(heure)
        
    def GetHeure(self):
        return self.ctrl_heure.GetHeure()

    def Validation(self):
        if self.rubrique == "depart" : nomTemp = _("de départ")
        if self.rubrique == "arrivee" : nomTemp = _("d'arrivée")

        if self.GetDate() == None  and self.ctrl_date.IsShown() :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement saisir une date %s !") % nomTemp, _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_date.SetFocus()
            return False

        if self.GetDate() != None and self.ctrl_date.Validation() == False and self.ctrl_date.IsEnabled():
            dlg = wx.MessageDialog(self, _("Veuillez vérifier la cohérence de la date %s !") % nomTemp, _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_date.SetFocus()
            return False

        if self.GetHeure() != None and self.ctrl_heure.Validation() == False :
            dlg = wx.MessageDialog(self, _("Veuillez vérifier la cohérence de l'heure %s !") % nomTemp, _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_heure.SetFocus()
            return False
        return True

    def GetData(self):
        keyDate = "%s_date" % self.rubrique
        valeurDate = self.GetDate()
        keyHeure = "%s_heure" % self.rubrique
        valeurHeure = self.GetHeure()
        return {keyDate : valeurDate, keyHeure : valeurHeure}

    def SetData(self, listeDonnees=[]):
        for key, valeur in listeDonnees :
            if key == "%s_date" % self.rubrique :
                self.SetDate(valeur)
            if key == "%s_heure" % self.rubrique :
                self.SetHeure(valeur)

class CTRL_Date(wx.Panel):
    """ Contrôle Date et Heure """
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent

        self.ctrl_date = CTRL_Saisie_date.Date2(self)
        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_base.Add( (5, 5), 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 0)
        grid_sizer_base.Add(self.ctrl_date, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 0)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        self.Layout()

    def AffichageDate(self, etat=True):
        """ Affiche ou non le contrôle Date """
        self.label_date.Show(etat)
        self.ctrl_date.Show(etat)

    def OnChoixDate(self):
        # étend la date départ à la date d'arrivée si elle n'est pas renseignée
        if self.GetDate() != None and self.rubrique == "depart" :
            ctrl = self.parent.GetControle(code="date", rubrique="arrivee")
            if ctrl and ctrl.GetDate() == None :
                ctrl.SetDate(self.GetDate())
        # Vérification si possible versus dates d'activité
        if hasattr(self.parent.parent,"VerifDatesActivite"):
            self.parent.parent.VerifDatesActivite()

    def SetDateTime(self, datedt=None):
        """ Remplit les contrôles à partir d'un datetime date + heure """
        self.SetDate(datetime.date(datedt.year, datedt.month, datedt.day))

    def SetDate(self, date=None):
        self.ctrl_date.SetDate(date)

    def SetHeure(self, heure=None):
        return

    def GetDate(self):
        return self.ctrl_date.GetDate()

    def GetHeure(self):
        return None

    def Validation(self):
        if self.rubrique == "depart" : nomTemp = _("de départ")
        if self.rubrique == "arrivee" : nomTemp = _("d'arrivée")

        if self.GetDate() == None  and self.ctrl_date.IsShown() :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement saisir une date %s !") % nomTemp, _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_date.SetFocus()
            return False

        if self.GetDate() != None and self.ctrl_date.Validation() == False and self.ctrl_date.IsEnabled():
            dlg = wx.MessageDialog(self, _("Veuillez vérifier la cohérence de la date %s !") % nomTemp, _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_date.SetFocus()
            return False

        if self.GetHeure() != None and self.ctrl_heure.Validation() == False :
            dlg = wx.MessageDialog(self, _("Veuillez vérifier la cohérence de l'heure %s !") % nomTemp, _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_heure.SetFocus()
            return False
        return True

    def GetData(self):
        keyDate = "%s_date" % self.rubrique
        valeurDate = self.GetDate()
        keyHeure = "%s_heure" % self.rubrique
        valeurHeure = self.GetHeure()
        return {keyDate : valeurDate, keyHeure : valeurHeure}

    def SetData(self, listeDonnees=[]):
        for key, valeur in listeDonnees :
            if key == "%s_date" % self.rubrique :
                self.SetDate(valeur)
            if key == "%s_heure" % self.rubrique :
                self.SetHeure(valeur)

#------------------------------------------------------------------------------------------------------

class CTRL_Details(wx.TextCtrl):
    def __init__(self, parent):
        wx.TextCtrl.__init__(self, parent, -1, size=(170, -1)) 
        self.parent = parent
        self.SetToolTip(wx.ToolTip(_("Saisissez ici les détails concernant ce transport (Ex : numéro de place, classe, etc...)")))
    
    def SetDetails(self, details=""):
        if details == None : details = ""
        self.SetValue(details)
    
    def GetDetails(self):
        details = self.GetValue()
        return details
    
    def Validation(self):
        return True

    def GetData(self):
        key = "details"
        valeur = self.GetDetails() 
        return {key : valeur}

    def SetData(self, listeDonnees=[]):
        for key, valeur in listeDonnees :
            if key == "details" :
                self.SetDetails(valeur)

class CTRL_Observations(wx.TextCtrl):
    def __init__(self, parent):
        wx.TextCtrl.__init__(self, parent, -1, size=(170, -1), style=wx.TE_MULTILINE) 
        self.parent = parent
        self.SetToolTip(wx.ToolTip(_("Saisissez ici des observations")))
    
    def SetObservations(self, observations=""):
        if observations == None : observations = ""
        self.SetValue(observations)
    
    def GetObservations(self):
        observations = self.GetValue()
        return observations
    
    def Validation(self):
        return True

    def GetData(self):
        key = "observations"
        valeur = self.GetObservations() 
        return {key : valeur}

    def SetData(self, listeDonnees=[]):
        for key, valeur in listeDonnees :
            if key == "observations" :
                self.SetObservations(valeur)

class CTRL_Numero(wx.TextCtrl):
    def __init__(self, parent, categorie="avion"):
        wx.TextCtrl.__init__(self, parent, -1, size=(170, -1)) 
        self.parent = parent
        if categorie == "avion" : self.SetToolTip(wx.ToolTip(_("Saisissez ici le numéro du vol")))
        if categorie == "train" : self.SetToolTip(wx.ToolTip(_("Saisissez ici le numéro du train")))
    
    def SetNumero(self, numero=""):
        if numero == None : numero = ""
        self.SetValue(numero)
    
    def GetNumero(self):
        numero = self.GetValue()
        return numero

    def Validation(self):
        return True

    def GetData(self):
        key = "numero"
        valeur = self.GetNumero() 
        return {key : valeur}

    def SetData(self, listeDonnees=[]):
        for key, valeur in listeDonnees :
            if key == "numero" :
                self.SetNumero(valeur)

#------------------------------------------------------------------------------------------------------

class CTRL_Choix_compagnies(wx.Choice):
    def __init__(self, parent, categorie="car"):
        wx.Choice.__init__(self, parent, -1, size=(170, -1)) 
        self.parent = parent
        self.categorie = categorie
        self.MAJ() 
        self.Select(0)
        self.SetToolTip(wx.ToolTip(_("Sélectionnez ici une compagnie")))
    
    def MAJ(self):
        listeItems = self.GetListeDonnees()
        if len(listeItems) == 1 :
            self.Enable(False)
        else:
            self.Enable(True)
        self.SetItems(listeItems)
                                        
    def GetListeDonnees(self):
        db = GestionDB.DB()
        req = """SELECT IDcompagnie, nom, rue, cp, ville, tel, fax, mail
        FROM transports_compagnies
        WHERE categorie='%s' 
        ORDER BY nom; """ % self.categorie
        db.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = db.ResultatReq()
        db.Close()
        listeItems = ["",]
        self.dictDonnees = {}
        self.dictDonnees[0] = { "ID" : 0, "nom" : _("Inconnue")}
        index = 1
        for IDcompagnie, nom, rue, cp, ville, tel, fax, mail in listeDonnees :
            self.dictDonnees[index] = { "ID" : IDcompagnie, "nom " : nom}
            listeItems.append(nom)
            index += 1
        return listeItems

    def SetID(self, ID=0):
        if ID == None :
            self.SetSelection(0)
        for index, values in self.dictDonnees.items():
            if values["ID"] == ID :
                 self.SetSelection(index)

    def GetID(self):
        index = self.GetSelection()
        if index == -1 or index == 0 : return None
        return self.dictDonnees[index]["ID"]

class CTRL_Compagnies(wx.Panel):
    """ Contrôle Choix de compagnies """
    def __init__(self, parent, categorie="car"):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.categorie = categorie
        
        self.ctrl_compagnies = CTRL_Choix_compagnies(self, categorie=categorie)
        self.bouton_gestion = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Mecanisme.png"), wx.BITMAP_TYPE_ANY))
        
        self.Bind(wx.EVT_BUTTON, self.OnBoutonGestion, self.bouton_gestion)
        self.bouton_gestion.SetToolTip(wx.ToolTip(_("Cliquez ici pour accéder au paramétrage des compagnies")))

        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_base.Add(self.ctrl_compagnies, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.EXPAND, 0)
        grid_sizer_base.Add(self.bouton_gestion, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 0)
        grid_sizer_base.AddGrowableCol(0)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        self.Layout()

    def MAJ(self):
        self.ctrl_compagnies.MAJ(self.ctrl_compagnies.IDcompagnie)

    def OnBoutonGestion(self, event): 
        IDcompagnie = self.ctrl_compagnies.GetID()
        from Dlg import DLG_Compagnies
        dlg = DLG_Compagnies.Dialog(self, categorie=self.categorie, mode="gestion")
        dlg.ShowModal() 
        dlg.Destroy()
        self.ctrl_compagnies.MAJ() 
        if IDcompagnie == None : IDcompagnie = 0
        self.ctrl_compagnies.SetID(IDcompagnie)
    
    def SetCompagnie(self, IDcompagnie=None):
        self.ctrl_compagnies.SetID(IDcompagnie)
        
    def GetCompagnie(self):
        return self.ctrl_compagnies.GetID()

    def Validation(self):
        return True

    def GetData(self):
        key = "IDcompagnie"
        valeur = self.GetCompagnie() 
        return {key : valeur}

    def SetData(self, listeDonnees=[]):
        for key, valeur in listeDonnees :
            if key == "IDcompagnie" :
                self.SetCompagnie(valeur)

#------------------------------------------------------------------------------------------------------

class CTRL_Choix_lieux(wx.Choice):
    def __init__(self, parent, categorie="gare"):
        wx.Choice.__init__(self, parent, -1, size=(170, -1)) 
        self.parent = parent
        self.categorie = categorie
        self.MAJ() 
        self.Select(0)
        self.SetToolTip(_("Sélectionnez ici un lieu"))
    
    def MAJ(self):
        listeItems = self.GetListeDonnees()
        if len(listeItems) == 1 :
            self.Enable(False)
        else:
            self.Enable(True)
        self.SetItems(listeItems)
                                        
    def GetListeDonnees(self):
        db = GestionDB.DB()
        req = """SELECT IDlieu, nom, cp, ville
        FROM transports_lieux
        WHERE categorie='%s'
        ORDER BY nom;""" % self.categorie
        db.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = db.ResultatReq()
        db.Close()
        listeItems = ["",]
        self.dictDonnees = {}
        self.dictDonnees[0] = { "ID" : 0, "nom" : _("Inconnue")}
        index = 1
        for IDlieu, nom, cp, ville in listeDonnees :
            self.dictDonnees[index] = { "ID" : IDlieu, "nom " : nom}
            listeItems.append(nom)
            index += 1
        return listeItems

    def SetID(self, ID=0):
        if ID == None :
            self.SetSelection(0)
        for index, values in self.dictDonnees.items():
            if values["ID"] == ID :
                 self.SetSelection(index)

    def GetID(self):
        index = self.GetSelection()
        if index == -1 or index == 0 : return None
        return self.dictDonnees[index]["ID"]

class CTRL_Lieux(wx.Panel):
    """ Contrôle Choix de lieux """
    def __init__(self, parent, categorie="gare"):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.categorie = categorie
        
        self.ctrl_lieux = CTRL_Choix_lieux(self, categorie=categorie)
        self.bouton_gestion = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Mecanisme.png"), wx.BITMAP_TYPE_ANY))
        
        self.Bind(wx.EVT_BUTTON, self.OnBoutonGestion, self.bouton_gestion)
        self.bouton_gestion.SetToolTip(wx.ToolTip(_("Cliquez ici pour accéder au paramétrages des lieux")))

        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_base.Add(self.ctrl_lieux, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.EXPAND, 0)
        grid_sizer_base.Add(self.bouton_gestion, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 0)
        grid_sizer_base.AddGrowableCol(0)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        self.Layout()

    def MAJ(self):
        self.ctrl_lieux.MAJ(self.ctrl_lieux.IDlieu)

    def OnBoutonGestion(self, event): 
        from Dlg import DLG_Lieux
        dlg = DLG_Lieux.Dialog(self, categorie=self.categorie, mode="gestion")
        dlg.ShowModal() 
        dlg.Destroy()
        # MAJ contrôles
        for controle in self.parent.GetControles(self.categorie) :
            controle.MAJ() 
    
    def MAJ(self, IDlieu=False):
        IDlieu = self.ctrl_lieux.GetID()
        if IDlieu == False :
            IDlieu = self.ctrl_lieux.IDlieu
        self.ctrl_lieux.MAJ()
        self.ctrl_lieux.SetID(IDlieu)

    def SetLieu(self, IDlieu=None):
        self.ctrl_lieux.SetID(IDlieu)
        
    def GetLieu(self):
        return self.ctrl_lieux.GetID()

    def Validation(self):
        return True

    def GetData(self):
        key = "%s_IDlieu" % self.rubrique
        valeur = self.GetLieu() 
        return {key : valeur}

    def SetData(self, listeDonnees=[]):
        for key, valeur in listeDonnees :
            if key == "%s_IDlieu" % self.rubrique :
                self.SetLieu(valeur)

#------------------------------------------------------------------------------------------------------

class CTRL_Categorie(BitmapComboBox):
    def __init__(self, parent, size=(-1,  -1)):
        BitmapComboBox.__init__(self, parent, -1, size=size, style=wx.CB_READONLY)
        self.parent = parent
        self.MAJlisteDonnees() 
        if len(self.dictDonnees) > 0 :
            self.SetSelection(0)
        self.SetToolTip(_("Sélectionnez ici un moyen de locomotion"))
    
    def MAJlisteDonnees(self):
        listeItems = self.GetListeDonnees()
        if len(listeItems) == 0 :
            self.Enable(False)
        self.dictDonnees = {}
        index = 0
        for label, bmp, categorie in listeItems :
            self.Append(label, bmp, categorie)
            self.dictDonnees[index] = { "categorie" : categorie }
            index += 1
            
    def GetListeDonnees(self):
        listeItems = []
        for categorie, dictValeurs in DICT_CATEGORIES.items() :
            label = dictValeurs["label"]
            bmp = wx.Bitmap(Chemins.GetStaticPath("Images/32x32/%s.png" % dictValeurs["image"]), wx.BITMAP_TYPE_ANY)
            listeItems.append((label, bmp, categorie))
        listeItems.sort()
        return listeItems

    def SetCategorie(self, categorie="bus"):
        for index, values in self.dictDonnees.items():
            if values["categorie"] == categorie :
                self.SetSelection(index)

    def GetCategorie(self):
        index = self.GetSelection()
        if index == -1 : return None
        return self.dictDonnees[index]["categorie"]

# -----------------------------------------------------------------------------------------------------------------------

class CTRL(wx.Panel):
    def __init__(self, parent, IDtransport=0, IDindividu=None, dictDonnees={}, verrouilleBoutons=False, ar=None):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        if not ar:
            titre = "Gestion du DEPART ou de l'ARRIVEE"
            intro = "Pour chaque trajet le camp est soit l'arrivée soit le départ, il est peu utile de le gérer."\
                    + "\n L'important est de gérer l'origine de l'aller ou la destination du retour du campeur."
            listeChoix = [("ALLER","Vous ne gérerez que le départ qui est l'origine, car l'arrivée c'est le camp"),
                          ("RETOUR","Vous ne gérerez que l'arrivee qui est la destination, car le départ c'est le camp"),
                          ("TOUT", "Vous gérerez le départ et l'arrivee, sans vous tromper!")]
            dlg = CTRL_ChoixListe.Dialog(None, listeOriginale=listeChoix,intro=intro,titre=titre, minSize = (600, 350),
                                          LargeurCode=100, LargeurLib=300,)
            dlg.ShowModal()
            choix = dlg.choix
            if not  choix: choix = (None,None)
            del dlg
            if choix[0] in ("ALLER","RETOUR"):
                ar = choix[0]
        else: ar = ar.upper()

        self.allerRetour = ar

        if not IDtransport: IDtransport = 0
        self.IDtransport = IDtransport
        self.IDindividu = IDindividu
        self.dictDonnees = dictDonnees
        self.categorie = "noTransport"
        self.listeDonneesSauvegardees = []

        self.grid_sizer_base = wx.FlexGridSizer(rows=5, cols=1, vgap=5, hgap=10)
        
        self.listeSizers = []
        self.listeControles = []
        
        # Ctrl Choix Catégorie
        self.ctrl_categorie = CTRL_Categorie(self)
        self.ctrl_categorie.SetCategorie(self.categorie)
        self.grid_sizer_base.Add(self.ctrl_categorie, 0, wx.EXPAND|wx.BOTTOM, 0)
        self.Bind(wx.EVT_COMBOBOX, self.OnChoixCategorie, self.ctrl_categorie)
        
        # Généralités
        self.CreationControles(rubrique="generalites", label=_("Généralités"))

        # Appel des contrôles Départ Arrivée  aller-retour

        if self.allerRetour =="ALLER":
            self.CreationControles(rubrique="depart", label=_("Provenance"))
        elif self.allerRetour == "RETOUR":
            self.CreationControles(rubrique="arrivee", label=_("Destination"))
        else:
            self.CreationControles(rubrique="depart", label=_("Départ du trajet"))
            self.CreationControles(rubrique="arrivee", label=_("Arrivée du trajet"))

        # Verouillage boutons de gestion
        if verrouilleBoutons == True :
            self.VerrouilleBoutonsGestion() 

        # Finalisation Layout
        self.grid_sizer_base.AddGrowableCol(0)
        self.SetSizer(self.grid_sizer_base)
        self.grid_sizer_base.Fit(self)
        
        self.OnChoixCategorie(None)
        
        # Importation
        if self.IDtransport != 0 :
            self.Importation()
        else:
            self.ImportationVirtuelle()

    def CreationControles(self, rubrique="generalites", label=_("Généralités")):
        # Crée tous les contrôles possibles, seuls ceux du
        box = wx.StaticBox(self, -1, label)
        boxSizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        grid_sizer = wx.FlexGridSizer(rows=18, cols=2, vgap=10, hgap=10)

        for dictControle in GetDic_rub_ctrl_Utiles()[rubrique] :
            code = dictControle["code"]
            # Label
            label = dictControle["label"]
            ctrl_label = wx.StaticText(self, -1, "%s :" % label)
            grid_sizer.Add(ctrl_label, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
            ctrl = None
            # contrôle
            command = dictControle["ctrl"]
            #ctrlTest = CTRL_Compagnies(self, categorie='avion')
            ctrl = eval(command)
            ctrl.SetName(code)
            ctrl.rubrique = rubrique
            grid_sizer.Add(ctrl, 0, wx.EXPAND, 0)
            
            # Mémorisation des 2 contrôles
            self.listeControles.append((code, ctrl, ctrl_label))

        grid_sizer.AddGrowableCol(1)
        boxSizer.Add(grid_sizer, 1, wx.ALL|wx.EXPAND, 10)
        self.grid_sizer_base.Add(boxSizer, 1, wx.EXPAND, 0)
        
        self.listeSizers.append(boxSizer)
        self.listeSizers.append(grid_sizer)

    def OnChoixCategorie(self, event):
        if event:
            self.dictDonnees.update(self.GetDictDonnees())
        self.categorie = self.ctrl_categorie.GetCategorie()
        self.MAJaffichage()
        if event:
            self.dictDonnees["categorie"] = self.categorie
            self.dictDonnees.update(self.dictDonnees)
            self.ImportationVirtuelle()

    def SelectCategorie(self, categorie="avion"):
        self.categorie = categorie
        self.ctrl_categorie.SetCategorie(self.categorie)
        self.OnChoixCategorie(None)
        
    def MAJaffichage(self):
        """ Affiche ou non les contrôles de la catégorie """
        # recherche des contrôles à afficher
        self.Freeze()
        for codeControle, ctrl, ctrl_label in self.listeControles :
            resultat = self.RechercheControle(codeControle, self.categorie)
            ctrl.Show(resultat)
            ctrl_label.Show(resultat)  
        # Ajustement des sizers
        for sizer in self.listeSizers :
            sizer.Layout()
        self.Layout()
        self.Thaw()
        self.Refresh()

    def RechercheControle(self, codeControle="", categorie="bus"):
        """ Recherche si un contrôle donné est utilisé par la catégorie donnée """
        listeControlesCategorie = DICT_CATEGORIES[self.categorie]["controles"]
        if codeControle in listeControlesCategorie :
            return True
        return False

    def GetControles(self, texteNom="", controleActuel=None):
        """ Retrouve les contrôles du panel dont le nom comporte le texte texteNom """
        listeControlesTrouves = []
        for children in self.GetChildren():
            if texteNom in children.GetName() and children != controleActuel : 
                listeControlesTrouves.append(children)
        return listeControlesTrouves
    
    def GetControle(self, code="date_heure", rubrique="depart"):
        """ Recherche un contrôle particulier d'après son code """
        for codeControle, ctrl, ctrl_label in self.listeControles :
            if codeControle == code and ctrl.rubrique == rubrique :
                return ctrl
        return None

    def AffichageDates(self, etat=True):
        # Départ
        ctrlDep = self.GetControle("date_heure", rubrique="depart")
        if ctrlDep:
            ctrlDep.AffichageDate(etat)
        # Arrivée
        ctrlArr = self.GetControle("date_heure", rubrique="arrivee")
        if ctrlArr:
            ctrlArr.AffichageDate(etat)

    def SaisirLigne(self,categorie):
        resultat = False
        for item in DICT_CATEGORIES[categorie]["controles"]:
            if item[:5] == "ligne":
                resultat = True
                break
        return resultat

    def ValideLocalisation(self):
        saisirLigne = self.SaisirLigne(self.categorie)
        dic = self.GetDictDonnees()
        if saisirLigne and dic["IDligne"] == None and self.categorie != "intercamp":
            wx.MessageBox("Il faut saisir une ligne pour le trajet")
            return False
        if saisirLigne:
            date = False
            loc = False
            for sens in ("depart","arrivee"):
                if dic[(sens + "_date")]: date = True
                for typ in ('IDlieu','IDarret',"localisation"):
                    if dic[(sens + "_" + typ)]:
                        loc = True
            resultat = date and loc
            if (not loc) and self.categorie == "intercamp" :
                wx.MessageBox("Il faut préciser l'intercamp pour la pièce")
            elif (not loc) :
                wx.MessageBox("Quand une ligne est renseignée, il faut localiser un arrêt")
            if not date: wx.MessageBox("Quand une ligne est renseignée, il faut une date")
        else:
            resultat = True
        return resultat

    def Validation(self):
        """ Validation des données """
        if self.categorie in ("voiture",):
            return True
        # Recherche les contrôles actifs
        for codeControle, ctrl, ctrl_label in self.listeControles :
            resultat = self.RechercheControle(codeControle, self.categorie)
            if resultat == True :
                if ctrl.Validation() == False :
                    #print "ca coince sur le contrôle", codeControle, ctrl.rubrique
                    return False
        if not self.ValideLocalisation():
            return False
        return True

    def GetDictDonnees(self):
        # Retourne un dict avec toutes les données
        # Création d'un dict de données vierges d'après la table de champs
        dictDonnees = {}
        for nom, type, info in DICT_TABLES["transports"] :
            if nom not in ("IDtransport", "IDindividu", "IDcompagnie"):
                dictDonnees[nom] = None
        
        # Récupère la valeur des contrôles
        for codeControle, ctrl, ctrl_label in self.listeControles :
            resultat = self.RechercheControle(codeControle, self.categorie)
            if resultat == True :
                dictData = ctrl.GetData()
                for key, data in dictData.items() :
                    dictDonnees[key] = data
        # Ajout de la catégorie et IDindividu
        dictDonnees["categorie"] = self.categorie
        dictDonnees["IDindividu"] = self.IDindividu
        if not "depart_date" in dictDonnees: dictDonnees["depart_date"] = None
        if not "arrivee_date" in dictDonnees: dictDonnees["arrivee_date"] = None
        if not dictDonnees["depart_date"]: dictDonnees["depart_date"] = dictDonnees["arrivee_date"]
        if not dictDonnees["arrivee_date"]: dictDonnees["arrivee_date"] = dictDonnees["depart_date"]
        return dictDonnees

    def Sauvegarde(self, mode="unique", parametres=None):
        """ Sauvegarde des données """
        self.listeDonneesSauvegardees = []
        DB = GestionDB.DB()
        
        # Récupère les données
        dictDonnees = self.GetDictDonnees() 
        
        # ----------------------------------------- SAISIE UNIQUE ----------------------------------------
        dictDonnees["mode"] = "TRANSP"

        # Conversion en liste
        listeDonnees = []
        for key, valeur in dictDonnees.items() :
            listeDonnees.append((key, valeur))

        # Sauvegarde
        if self.IDtransport == 0 :
            self.IDtransport = DB.ReqInsert("transports", listeDonnees,MsgBox="CTRL_Saisietransport.Sauvegarde.insert")
        else:
            retour = DB.ReqMAJ("transports", listeDonnees, "IDtransport", self.IDtransport)
            if retour != "ok":
                self.IDtransport = DB.ReqInsert("transports", listeDonnees,MsgBox="CTRL_Saisietransport.Sauvegarde.insert")
        DB.Close()
        return True
    
    def GetIDtransport(self):
        return self.IDtransport
    
    def Importation(self):
        """ Importation des données """
        # Récupère les noms de champs de la table
        listeChamps = []
        for nom, type, info in DICT_TABLES["transports"] :
            listeChamps.append(nom)

        # Importation des données de l'enregistrement
        DB = GestionDB.DB()
        req = """SELECT %s
        FROM transports 
        WHERE IDtransport=%d;""" % (", ".join(listeChamps), self.IDtransport)
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeValeurs = DB.ResultatReq()
        DB.Close()
        if len(listeValeurs) == 0 : return
        listeDonnees = []
        index = 0
        for valeur in listeValeurs[0] :
            listeDonnees.append((listeChamps[index], valeur))
            index += 1
        # Remplit les champs
        self.RemplitChamps(listeDonnees)

    def RemplitChamps(self, listeDonnees=[]):
        # Sélectionne la catégorie
        for key, valeur in listeDonnees :
            if key == "categorie" :
                self.SelectCategorie(valeur)
        # Importe les valeurs dans les contrôles
        for codeControle, ctrl, ctrl_label in self.listeControles :
            ctrl.SetData(listeDonnees)
    
    def ImportationVirtuelle(self):
        listeDonnees = []
        for key, valeur in self.dictDonnees.items() :
            listeDonnees.append((key, valeur))
        self.RemplitChamps(listeDonnees)
    
    def VerrouilleBoutonsGestion(self):
        """ Verrouille tous les boutons de gestion """
        for ctrl in self.GetChildren():
            if hasattr(ctrl, 'bouton_gestion'):
                ctrl.bouton_gestion.Show(False)

#------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.ctrl = CTRL(panel, IDtransport=12579, IDindividu=13242)
        self.ctrl.VerrouilleBoutonsGestion() 
        bouton_test = wx.Button(panel, -1, _("TEST"))
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.ALL|wx.EXPAND, 4)
        sizer_2.Add(bouton_test, 0, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnBoutonTest, bouton_test)
    
    def OnBoutonTest(self, event):
        self.ctrl.Importation()

if __name__ == '__main__':
    app = wx.App(0)
    mnt = MenuTransports(None)
    #print(mnt.GetMenuTransports())
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "TEST : CTRL_Saisie_transport", size=(450, 580))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
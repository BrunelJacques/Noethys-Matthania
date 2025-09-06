#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys branche Matthania
# Module:  De cotisations vers dons
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import Chemins
import datetime
import GestionDB

from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Bandeau
from Ctrl import CTRL_Saisie_date
from Ctrl import CTRL_Saisie_euros

from Data import DATA_Types_prestations
from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")


def ConvertStrToListe(texte=None):
    """ Convertit un texte "1;2;3;4" en [1, 2, 3, 4] """
    if not texte :
        return None
    listeResultats = []
    temp = texte.split(";")
    for ID in temp :
        listeResultats.append(int(ID))
    return listeResultats


class Choix_compte(wx.Choice):
    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1)
        self.parent = parent

        DB = GestionDB.DB()
        self.planCpte = DATA_Types_prestations.GetLstComptes(DB)
        DB.Close()
        self.SetListeDonnees()

    def SetListeDonnees(self, filtre='conso-don-autre'):
        self.lstCodesCpte, self.lstLibCptes,self.lstComptes = [],[],[]

        def addItem():
            self.lstCodesCpte.append(code)
            self.lstLibCptes.append(lib)
            self.lstComptes.append(cpte)

        for code,lib,cpte in self.planCpte:
            if 'conso' in filtre and code.startswith('VTE'):
                addItem()
                continue
            if 'don' in filtre and code.startswith('DON'):
                addItem()
                continue
            if 'autre' in filtre and not (code.startswith('VTE')
                                          or code.startswith('DON')):
                addItem()
                continue
            addItem() # pour la valeur nulle
        self.SetItems(self.lstLibCptes)
        self.SetValue("")

    def SetValue(self, compte=""):
        if compte in self.lstCodesCpte:
            index = self.lstCodesCpte.index(compte)
        else:
            index = 0
        self.SetSelection(index)

    def GetCompte(self):
        index = self.GetSelection()
        if index == -1: return None
        return self.lstCodesCpte[index]


class Choix_categorie(wx.Choice):
    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1)
        self.parent = parent
        self.SetListeDonnees('autres-dons')

    def SetListeDonnees(self,filtre='conso-don-autre'):
        kw = {}
        kw['consos'] = 'conso' in filtre
        kw['dons'] = 'don' in filtre
        kw['autres'] = 'autre' in filtre
        self.lstIDtypes, self.lstLibTypes = DATA_Types_prestations.GetLstTypes(**kw)
        self.SetItems(self.lstLibTypes)
        self.SetCategorie("")

    def SetCategorie(self, ID=""):
        if ID in self.lstIDtypes:
            index = self.lstIDtypes.index(ID)
            self.SetSelection(index)

    def GetCategorie(self):
        index = self.GetSelection()
        if index == -1 : return None
        return self.lstIDtypes[index]


class Choix_individu(wx.Choice):
    def __init__(self, parent, IDfamille=None):
        wx.Choice.__init__(self, parent, -1)
        self.parent = parent
        self.IDfamille = IDfamille
        self.listeIndividus = []
        self.listeNoms = []
    
    def SetListeDonnees(self, dictIndividus):
        self.listeIndividus = []
        self.listeNoms = []
        for IDindividu, dictIndividu in dictIndividus.items() :
            nomIndividu = "%s %s" % (dictIndividu['nom'], dictIndividu['prenom'])
            self.listeIndividus.append([nomIndividu, IDindividu])
        self.listeIndividus.sort()
        for nomIndividu, IDindividu in self.listeIndividus :
            self.listeNoms.append(nomIndividu)
        self.SetItems(self.listeNoms)
    
    def SetID(self, ID=None):
        index = 0
        for nomIndividu, IDindividu in self.listeIndividus :
            if IDindividu == ID :
                 self.SetSelection(index)
            index += 1

    def GetID(self):
        index = self.GetSelection()
        if index == -1 : return None
        return self.listeIndividus[index][1]


class Choix_activite(wx.Choice):
    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1)
        self.parent = parent
        self.listeNoms = []
        self.listeActivites = []
    
    def SetListeDonnees(self, listeActivites):
        self.listeNoms = []
        self.listeActivites = listeActivites
        for dictActivite in listeActivites :
            nom = dictActivite["nom"]
            self.listeNoms.append(nom)
        self.SetItems(self.listeNoms)
    
    def SetID(self, ID=None):
        index = 0
        for dictActivite in self.listeActivites :
            IDactivite = dictActivite["IDactivite"]
            if IDactivite == ID :
                 self.SetSelection(index)
            index += 1

    def GetID(self):
        index = self.GetSelection()
        if index == -1 : return None
        return self.listeActivites[index]

# ---------------------------------------------------------------------------------------

class Dialog(wx.Dialog):
    def __init__(self, parent, IDprestation=None, IDfamille=None, mode="saisie" ):
        wx.Dialog.__init__(self, parent, -1, name="DLG_Saisie_prestation",
            style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        if mode != 'saisie':
            self.mode = 'visu'
        else:
            self.mode = 'saisie'
        self.IDprestation = IDprestation
        self.IDfamille = IDfamille
        self.ancienMontant = 0.0
        self.date = None

        # Importation lors d'une modification
        self.categorie = ""
        prestation = None
        if self.IDprestation:
            prestation = self.__Importation()
        # les consos sont passées en read only
        if self.categorie and self.categorie.startswith('conso'):
            self.mode = 'visu'

        intro = "Vous pouvez saisir ou modifier ici une prestation qui ne fait pas l'objet d'une facture (ex.: Dons, frais de dossier, pénalité, report...)."
        if self.mode == 'saisie':
            self.SetTitle("DLG_Saisie_prestation")
            titre = "Saisie d'une prestation"
        else:
            self.SetTitle("DLG_Saisie_prestation")
            intro = "Vous pouvez consulter une prestation sans pouvoir la modifier par cet outil"
            titre = "Gestion d'une prestation"
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self,titre=titre,texte=intro,hauteurHtml=30,
                                                 nomImage="Images/22x22/Smiley_nul.png")
        self.__CreateCtrl()
        if prestation:
            self.__ChargePrestation(prestation)
        self.__set_properties()
        self.__do_layout()
        self.EnableCtrl()

    def __Importation(self): # cas d'un ID prestation fourni
        """ Importation des données """
        DB = GestionDB.DB()
        req = """
        SELECT IDprestation, IDfamille, date, categorie, label, IDcontrat, compta, 
            factures.numero, montant, IDactivite, IDindividu, code_compta
        FROM prestations 
        LEFT JOIN factures ON factures.IDfacture = prestations.IDfacture
        WHERE IDprestation=%d;""" % self.IDprestation

        DB.ExecuterReq(req, MsgBox="DLG_Saisie_prestation.Importation")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if len(listeDonnees) == 0:
            return
        prestation = listeDonnees[0]
        self.categorie = prestation[3] # sera utililsé pour filtrer les types de compte
        IDcontrat = prestation[5]
        compta = prestation[6]
        numFacture = prestation[7]

        if self.categorie:
            IDtype = self.categorie
            if IDtype.startswith('conso'):
                self.ctrl_categorie.SetListeDonnees(filtre='consos')
            elif IDtype.startswith('don'):
                self.ctrl_categorie.SetListeDonnees(filtre='dons')
            else:
                self.ctrl_categorie.SetListeDonnees(filtre='autres')
            self.ctrl_categorie.SetCategorie(IDtype)
            self.OnChoixCategorie()
            if self.categorie.lower().startswith("conso"):
                self.mode = 'visu'

        # empécher la modif d'une pièce par sa prestation, ce qui créerait une anomalie
        if IDcontrat or compta or numFacture:
            self.mode = 'visu'
        return prestation

    def __CreateCtrl(self): # Création des controls affichés
        self.staticbox_generalites_staticbox = wx.StaticBox(self, -1, "Généralites")
        self.label_date = wx.StaticText(self, -1, "Date :")
        self.ctrl_date = CTRL_Saisie_date.Date2(self)
        self.label_categorie = wx.StaticText(self, -1, "Catégorie :")
        self.ctrl_categorie = Choix_categorie(self)
        self.label_label = wx.StaticText(self, -1, "Intitulé :")
        self.ctrl_label = wx.TextCtrl(self, -1, "")
        self.label_type = wx.StaticText(self, -1, "Type :")
        self.radio_type_familiale = wx.RadioButton(self, -1, "Prestation familiale",
                                                   style=wx.RB_GROUP)
        self.radio_type_individuelle = wx.RadioButton(self, -1,
                                                      "Prestation individuelle :")
        self.ctrl_individu = Choix_individu(self, self.IDfamille)

        # Facturation
        self.staticbox_facturation_staticbox = wx.StaticBox(self, -1, "Facturation")
        self.label_activite = wx.StaticText(self, -1, "Activité :")
        self.ctrl_activite = Choix_activite(self)
        self.label_facture = wx.StaticText(self, -1, "Facture :")
        self.ctrl_facture = wx.StaticText(self, -1, "Non facturé")

        # Code comptable
        self.label_compte = wx.StaticText(self, -1, "Code compta :")
        self.ctrl_compte = Choix_compte(self)

        # Montants
        self.label_montant_avant_deduc = wx.StaticText(self, -1,
                                                       "Montant TTC (%s) :" % SYMBOLE)
        self.ctrl_montant_avant_deduc = CTRL_Saisie_euros.CTRL(self)
        self.ctrl_montant_avant_deduc.SetMinSize((80, -1))
        self.label_montant = wx.StaticText(self, -1, "Total (%s) :" % SYMBOLE)
        self.ctrl_montant = CTRL_Saisie_euros.CTRL(self,
                                                   font=wx.Font(13, wx.DEFAULT, wx.NORMAL,
                                                                wx.BOLD, 0, ""))
        self.ctrl_montant.SetBackgroundColour("#F0FBED")
        self.ctrl_montant.SetEditable(False)
        self.ctrl_montant.SetMinSize((100, -1))

        # Commandes
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte="Aide",
                                                  cheminImage=Chemins.GetStaticPath(
                                                      "Images/32x32/Aide.png"))
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte="Ok",
                                                cheminImage=Chemins.GetStaticPath(
                                                    "Images/32x32/Valider.png"))
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL,
                                                     texte="Annuler",
                                                     cheminImage=Chemins.GetStaticPath(
                                                         "Images/32x32/Annuler.png"))

    def __set_properties(self):
        self.ctrl_date.SetToolTip("Saisissez ici la date de la prestation")
        self.ctrl_categorie.SetToolTip("Sélectionnez ici la catégorie de la prestation")
        self.ctrl_label.SetToolTip("Saisissez un intitulé pour cette prestation")
        self.radio_type_familiale.SetToolTip("Selectionnez cette case si la prestation concerne toute la famille")
        self.radio_type_individuelle.SetToolTip("Selectionnez cette case si la prestation ne concerne qu'un individu")
        self.ctrl_individu.SetToolTip("Selectionnez l'individu associé à la prestation")
        self.ctrl_activite.SetToolTip("Selectionnez ici l'activité concernée par la prestation")
        self.ctrl_montant_avant_deduc.SetToolTip("Saisissez ici le montant en Euros")
        self.ctrl_montant.SetToolTip("Montant en Euros")
        self.ctrl_facture.SetToolTip("Quand une prestation a été facturée, le numéro de facture apparait ici")
        self.bouton_aide.SetToolTip("Cliquez ici pour obtenir de l'aide")
        self.bouton_ok.SetToolTip("Cliquez ici pour valider")
        self.bouton_annuler.SetToolTip("Cliquez ici pour annuler et fermer")
        self.ctrl_compte.SetToolTip("Saisissez le code comptable de cette prestation")

        # Event sur contrôles
        self.Bind(wx.EVT_CHOICE, self.OnChoixCompte, self.ctrl_compte)
        self.Bind(wx.EVT_CHOICE, self.OnChoixCategorie, self.ctrl_categorie)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnChoixCategorie, self.ctrl_label)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioType, self.radio_type_familiale)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioType, self.radio_type_individuelle)
        self.Bind(wx.EVT_CHOICE, self.OnChoixActivite, self.ctrl_activite)
        self.Bind(wx.EVT_CHOICE, self.OnTextMontant, self.ctrl_montant_avant_deduc)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_TEXT, self.OnTextMontant, self.ctrl_montant_avant_deduc)

        self.ctrl_label.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.SetMinSize((650, 360))
        
    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        
        grid_sizer_contenu = wx.FlexGridSizer(rows=1, cols=2, vgap=10, hgap=10)
        staticbox_facturation = wx.StaticBoxSizer(self.staticbox_facturation_staticbox, wx.VERTICAL)
        grid_sizer_facturation = wx.FlexGridSizer(rows=6, cols=2, vgap=10, hgap=10)
        staticbox_generalites = wx.StaticBoxSizer(self.staticbox_generalites_staticbox, wx.VERTICAL)
        grid_sizer_generalites = wx.FlexGridSizer(rows=6, cols=2, vgap=10, hgap=10)
        grid_sizer_type = wx.FlexGridSizer(rows=3, cols=1, vgap=5, hgap=5)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)
        grid_sizer_generalites.Add(self.label_date, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_generalites.Add(self.ctrl_date, 0, 0, 0)
        grid_sizer_generalites.Add(self.label_categorie, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_generalites.Add(self.ctrl_categorie, 0, wx.EXPAND, 0)
        grid_sizer_generalites.Add(self.label_label, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_generalites.Add(self.ctrl_label, 0, wx.EXPAND, 0)
        grid_sizer_generalites.Add(self.label_type, 0, wx.ALIGN_RIGHT, 0)
        grid_sizer_type.Add(self.radio_type_familiale, 0, 0, 0)
        grid_sizer_type.Add(self.radio_type_individuelle, 0, 0, 0)
        grid_sizer_type.Add(self.ctrl_individu, 0, wx.LEFT|wx.EXPAND, 18)
        grid_sizer_type.AddGrowableCol(0)
        grid_sizer_generalites.Add(grid_sizer_type, 1, wx.EXPAND, 0)
        grid_sizer_generalites.AddGrowableCol(1)
        staticbox_generalites.Add(grid_sizer_generalites, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_contenu.Add(staticbox_generalites, 1, wx.EXPAND, 0)

        grid_sizer_facturation.Add(self.label_activite, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_facturation.Add(self.ctrl_activite, 0, wx.EXPAND, 0)
        grid_sizer_facturation.Add(self.label_facture, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_facturation.Add( self.ctrl_facture, 0, wx.ALIGN_CENTER_VERTICAL, 0)

         # code comptable
        grid_sizer_facturation.Add(self.label_compte, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_facturation.Add(self.ctrl_compte, 0, 0, 0)

       # Montants
        grid_sizer_facturation.Add(self.label_montant_avant_deduc, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_facturation.Add(self.ctrl_montant_avant_deduc, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_facturation.Add(self.label_montant, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_facturation.Add( self.ctrl_montant, 0, 0, 0)
        
        grid_sizer_facturation.AddGrowableCol(1)
        staticbox_facturation.Add(grid_sizer_facturation, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_contenu.Add(staticbox_facturation, 1, wx.EXPAND, 0)
        grid_sizer_contenu.AddGrowableRow(0)
        grid_sizer_contenu.AddGrowableCol(0)
        grid_sizer_contenu.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_contenu, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(2)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()

    def __ChargePrestation(self,prestation):
        (IDprestation, IDfamille, date, categorie, label, IDcontrat, compta,
        numFacture, montant, IDactivite, IDindividu, code_compta) = prestation

        # Date
        self.ctrl_date.SetDate(date)
        self.date = self.ctrl_date.GetDate()
        self.OnChoixDate(None)

        # Label
        self.ctrl_label.SetValue(label)
        # Catégorie
        self.ctrl_categorie.SetCategorie(categorie)
        self.OnChoixCategorie()

        # préchargements seulement si nécessaires
        if IDactivite or IDindividu:
            self.Importation_activites()
            self.Importation_individus()

        # Individu
        if IDindividu and IDindividu != 0 :
            self.radio_type_individuelle.SetValue(True)
            self.ctrl_individu.SetID(IDindividu)
        # Activité
        if IDactivite:
            self.ctrl_activite.SetID(IDactivite)
        # Code comptable
        if code_compta:
            self.ctrl_compte.SetValue(code_compta)
        # Montant final
        self.ctrl_montant.SetMontant(montant)
        self.ancienMontant = montant
        # Facture
        if numFacture:
            self.ctrl_facture.SetLabel("Facture n°%d" % numFacture)
        if IDindividu:
            self.Importation_individus()
        if IDactivite:
            self.Importation_activites()

        if not self.IDprestation:
            self.ctrl_date.SetDate(datetime.date.today())
            self.OnChoixDate(None)

    def EnableCtrl(self):
        if self.mode == "visu":
            for ctrl in (self.label_date, self.ctrl_date, self.label_categorie, self.ctrl_categorie, self.label_label,
                         self.ctrl_label, self.label_type, self.radio_type_familiale, self.radio_type_individuelle,
                         self.ctrl_individu, self.label_activite, self.ctrl_activite, self.label_facture, self.ctrl_facture,
                         self.label_montant_avant_deduc, self.ctrl_montant_avant_deduc, self.label_montant, self.ctrl_montant,
                         self.label_compte, self.ctrl_compte, self.bouton_ok):
                ctrl.Enable(False)
        elif self.radio_type_familiale.GetValue():
            self.ctrl_individu.Enable(False)
            self.ctrl_activite.Enable(False)
            self.label_activite.Enable(False)
        else:
            self.ctrl_individu.Enable(True)
            self.ctrl_activite.Enable(True)
            self.label_activite.Enable(True)

    def Importation_individus(self):
        DB = GestionDB.DB()
        # Recherche les individus de la famille
        dictIndividus = {}
        req = """SELECT individus.IDindividu, IDcivilite, nom, prenom, date_naiss, IDcategorie, titulaire
        FROM individus
        LEFT JOIN rattachements ON individus.IDindividu = rattachements.IDindividu
        WHERE rattachements.IDfamille = %d
        ORDER BY nom, prenom;""" % self.IDfamille
        DB.ExecuterReq(req, MsgBox="ExecuterReq")
        listeIndividus = DB.ResultatReq()
        for IDindividu, IDcivilite, nom, prenom, date_naiss, IDcategorie, titulaire in listeIndividus:
            dictTemp = {
                "IDcivilite": IDcivilite, "nom": nom, "prenom": prenom,
                "IDcategorie": IDcategorie, "titulaire": titulaire,
                "inscriptions": [],
            }
            dictIndividus[IDindividu] = dictTemp

            # Recherche des inscriptions pour chaque membre de la famille
        req = """SELECT inscriptions.IDinscription, IDindividu, inscriptions.IDactivite, IDgroupe, inscriptions.IDcategorie_tarif, categories_tarifs.nom
        FROM inscriptions 
        LEFT JOIN categories_tarifs ON categories_tarifs.IDcategorie_tarif = inscriptions.IDcategorie_tarif
        WHERE IDfamille = %d ;""" % self.IDfamille
        DB.ExecuterReq(req, MsgBox="ExecuterReq")
        listeInscriptions = DB.ResultatReq()
        for IDinscription, IDindividu, IDactivite, IDgroupe, IDcategorie_tarif, nomCategorie_tarif in listeInscriptions:
            if not IDindividu in list(dictIndividus.keys()): continue
            dictTemp = {
                "IDinscription": IDinscription, "IDactivite": IDactivite,
                "IDgroupe": IDgroupe,
                "IDcategorie_tarif": IDcategorie_tarif,
                "nomCategorie_tarif": nomCategorie_tarif,
            }
            dictIndividus[IDindividu]["inscriptions"].append(dictTemp)

        # Cloture de la base de données
        DB.Close()

        # Remplissage du contrôle
        self.ctrl_individu.SetListeDonnees(self.dictIndividus)
        return

    def Importation_activites(self):
        DB = GestionDB.DB()
        # Recherche les activités
        req = """SELECT IDactivite, nom, abrege
        FROM activites
        ORDER BY nom;"""
        DB.ExecuterReq(req, MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        listeActivites = []
        for IDactivite, nom, abrege in listeDonnees:
            dictTemp = {"IDactivite": IDactivite, "nom": nom, "abrege": abrege}
            listeActivites.append(dictTemp)

        # Remplissage du contrôle
        self.ctrl_activite.SetListeDonnees(listeActivites)
        return

    def Message(self,mess,titre="SAISIE INCORRECTE"):
        dlg = wx.MessageDialog(self, mess, titre, style=wx.OK | wx.ICON_EXCLAMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def OnChoixDate(self, event=None):
        # controle si saisie dans un exercice ouvert
        self.bouton_ok.Enable(True)
        dateSaisie = self.ctrl_date.GetDate()
        if dateSaisie == self.date:
            return
        DB = GestionDB.DB()
        exerciceDeb, exerciceFin = DB.GetExercice(dateSaisie,alertes=False,approche=False)
        self.bouton_ok.Enable(True)
        if exerciceDeb and exerciceFin:
            #la date est dans un exercice
            self.date = dateSaisie
        elif dateSaisie and dateSaisie >= datetime.date.today():
            #on accepte les dates futures
            self.date = dateSaisie
        else:
            mess = "Veuillez choisir une date dans un exercie ouvert"
            self.message(mess)
            # on remet la date précédente et pointe le controle
            self.ctrl_date.SetDate(self.date)
            self.ctrl_date.SetFocus()
        DB.Close()

    def OnChoixCompte(self,event):
        ix = self.ctrl_compte.GetSelection()
        if ix == 0:
            mess = "Veuillez choisir un libellé des codes comptables proposés"
            self.message(mess)
            self.ctrl_compte.SetFocus()

    def OnChoixCategorie(self, event):
        ix = self.ctrl_categorie.GetSelection()
        if ix == 0:
            mess = "Veuillez choisir une des catégories de prestations proposées"
            self.message(mess)
            self.ctrl_categorie.SetFocus()
        else:
            # actualisation des choix de compte selon le type
            filtre = 'autres'
            IDtype = self.ctrl_categorie.lstIDtypes[ix]
            if IDtype.startswith('conso'): filtre = 'consos'
            if IDtype.startswith('don'): filtre = 'dons'
            self.ctrl_compte.SetListeDonnees(filtre=filtre)
        if self.compte:
            pass # todo

    def OnRadioType(self, event):
        if self.radio_type_individuelle.GetValue() == True:
            self.Importation_activites()
            self.Importation_individus()
        self.EnableCtrl()

    def OnChoixActivite(self, event):
        # MAJ du contrôle des catégories de tarifs
        pass

    def OnTextMontant(self, event):
        validation, message = self.ctrl_montant_avant_deduc.Validation() 
        if validation:
            montantInitial = self.ctrl_montant_avant_deduc.GetMontant() 
            self.ctrl_montant.SetMontant(montantInitial)

    def GetIDprestation(self):
        return self.IDprestation

    def Final(self):
        # Récupération et vérification des données saisies
        date = self.ctrl_date.GetDate()
        if not date:
            mess = "Vous devez obligatoirement saisir une date !"
            self.Message(mess)
            self.ctrl_date.SetFocus()
            return

        label = self.ctrl_label.GetValue()
        if label == "":
            mess = "Vous devez obligatoirement saisir un intitulé !"
            self.Message(mess)
            self.ctrl_label.SetFocus()
            return

        self.categorie = self.ctrl_categorie.GetCategorie()
        if self.categorie == "":
            mess = "Vous devez obligatoirement choisir une catégorie !"
            self.Message(mess)
            self.ctrl_categorie.SetFocus()
            return

        IDactivite = self.ctrl_activite.GetID()
        montant = self.ctrl_montant.GetMontant()
        montant_initial = montant
        if not montant:
            mess = "Le montant que vous avez saisi ne semble pas valide !"
            self.Message(mess)
            self.ctrl_montant.SetFocus()
            return

        IDfamille = self.IDfamille
        if self.radio_type_individuelle.GetValue():
            IDindividu = self.ctrl_individu.GetID()
            if not IDindividu:
                mess = "Etant donné que vous avez sélectionné le type 'prestation individuelle',\n"
                mess += "vous devez obligatoirement sélectionner un individu dans la liste !"
                self.ctrl_individu.SetFocus()
                return
        else:
            IDindividu = 0

        code_comptable = self.ctrl_compte.GetValue()
        if not code_comptable:
            mess = "Vous devez obligatoirement choisir un code comptable!"
            self.Message(mess)
            self.ctrl_compte.SetFocus()

        DB = GestionDB.DB()

        # Recherche modif si cette prestation a déjà été ventilée sur un règlement
        if self.IDprestation:
            req = """SELECT IDventilation, ventilation.montant
            FROM ventilation
            LEFT JOIN reglements ON reglements.IDreglement = ventilation.IDreglement
            WHERE IDprestation=%d
            ORDER BY reglements.date;""" % self.IDprestation
            DB.ExecuterReq(req, MsgBox="ExecuterReq")
            listeVentilations = DB.ResultatReq()
            montantVentilation = 0.0
            for IDventilation, montantTmp in listeVentilations:
                montantVentilation += montantTmp
            if montantVentilation > montant:
                # Si le montant total ventilé est supérieur à celui de la prestation :
                montantVentilationTmp = 0.0
                for IDventilation, montantTmp in listeVentilations:
                    montantVentilationTmp += montantTmp
                    if montantVentilationTmp > montant:
                        nouveauMontant = montantTmp - (montantVentilationTmp - montant)
                        if nouveauMontant > 0.0:
                            DB.ReqMAJ("ventilation", [("montant", nouveauMontant), ],
                                      "IDventilation", IDventilation)
                            montantVentilationTmp = (
                                                                montantVentilationTmp - montantTmp) + nouveauMontant
                        else:
                            DB.ReqDEL("ventilation", "IDventilation", IDventilation)

        # Sauvegarde de la prestation
        listeDonnees = [
            ("IDcompte_payeur", IDfamille),
            ("date", date),
            ("categorie", self.categorie),
            ("label", label),
            ("montant_initial", montant_initial),
            ("montant", montant),
            ("IDactivite", IDactivite),
            ("IDfamille", IDfamille),
            ("IDindividu", IDindividu),
            ("code_compta", code_comptable),
        ]
        if not self.IDprestation:
            self.IDprestation = DB.ReqInsert("prestations", listeDonnees)
            if isinstance(int,self.IDprestation):
                ret = 'ok'
            else: ret = self.IDprestation # l'échec d'insertion renvoie l'erreur
        else:
            ret = DB.ReqMAJ("prestations", listeDonnees, "IDprestation",
                      self.IDprestation)
        if not ret == 'ok':
            mess = "L'enregistrement a échoué\n\n" + ret
            self.Message(mess,"ECHEC ECRITURE")
        DB.Close()

    def OnBoutonOk(self, event):
        self.Final()
        self.EndModal(wx.ID_OK)

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Prestations")

if __name__ == "__main__":
    app = wx.App(False)
    frame = wx.Frame(None, title="Main Window")
    #dialog = Dialog(frame, IDprestation=46681, IDfamille=9)
    dialog = Dialog(frame, IDfamille=9)

    result = dialog.ShowModal()  # This blocks until EndModal is called
    dialog.Destroy()


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


from Utils.UTILS_Traduction import _
import wx
import Chemins
from Ctrl import CTRL_Bouton_image
import datetime
import GestionDB
import wx.lib.agw.floatspin as FS

from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")

from Ctrl import CTRL_Bandeau
from Ctrl import CTRL_Saisie_date
from Ctrl import CTRL_Saisie_euros

try: import psyco; psyco.full()
except: pass


def DateEngEnDateDD(dateEng):
    if dateEng != None :
        return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))
    else:
        return None

def DateDDenFr(dateDD):
    if dateDD == None : return None
    return dateDD.strftime("%d/%m/%Y")
    

def DateFREnDateDD(dateFR):
    return datetime.date(int(dateFR[6:10]),int(dateFR[3:5]),int(dateFR[:2]), )


def ConvertStrToListe(texte=None):
    """ Convertit un texte "1;2;3;4" en [1, 2, 3, 4] """
    if texte == None :
        return None
    listeResultats = []
    temp = texte.split(";")
    for ID in temp :
        listeResultats.append(int(ID))
    return listeResultats


class Choix_categorie(wx.Choice):
    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1) 
        self.parent = parent
        
        self.listeCategories = [
            ("don", _("Don à l'association")),
            ("donsscerfa", _("Don sans Cerfa")),
            ("debour", _("Frais ou débour dû par client")),
            ("autre", _("Paye pour autre client (ou autre: compte à préciser)")),
            ("consommation", _("Prestation liée à une inscription et gérée par elle ")),
            ("consoavoir", _("Prestation annulée par un avoir)")),
            ("autre","Origine non déterminée"),
            ("","")
            ]
        self.lstIDCategories = [x for (x,y) in self.listeCategories]
        self.listeNoms = [y for (x,y) in self.listeCategories]

        self.SetItems(self.listeNoms)
        self.SetCategorie("")
    
    def SetCategorie(self, categorie=""):
        if categorie in self.lstIDCategories:
            index = self.lstIDCategories.index(categorie)
        else:
            index = self.lstIDCategories.index("autre")
        self.SetSelection(index)

    def GetCategorie(self):
        index = self.GetSelection()
        if index == -1 : return None
        return self.listeCategories[index][0]

# ------------------------------------------------------------------------------------------------------------------------------------------

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
            nomIndividu = "%s %s" % (dictIndividu["nom"], dictIndividu["prenom"])
            self.listeIndividus.append((nomIndividu, IDindividu))
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

# ------------------------------------------------------------------------------------------------------------------------------------------

class Choix_activite(wx.Choice):
    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1) 
        self.parent = parent
        self.listeNoms = []
        self.listeActivites = []
    
    def SetListeDonnees(self, listeActivites=[]):
        self.listeNoms = []
        self.listeActivites = listeActivites
        for dictActivite in listeActivites :
            IDactivite = dictActivite["IDactivite"]
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
        return self.listeActivites[index]["IDactivite"]

# ------------------------------------------------------------------------------------------------------------------------------------------

class Dialog(wx.Dialog):
    def __init__(self, parent, IDprestation=None, IDfamille=None, mode="saisie" ):
        wx.Dialog.__init__(self, parent, -1, name="DLG_Saisie_prestation", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.mode = mode
        self.IDprestation = IDprestation
        self.IDfamille = IDfamille
        self.ancienMontant = 0.0
        self.IDfacture = None
        self.dateInit = None
        self.IDcompte_payeur = self.IDfamille
        
        if self.IDprestation == None :
            self.SetTitle(_("DLG_Saisie_prestation"))
            titre = _("Saisie d'une prestation")
        else:
            self.SetTitle(_("DLG_Saisie_prestation"))
            titre = _("Gestion d'une prestation")
        intro = _("Exceptionnellement vous pouvez saisir ou modifier ici une prestation qui ne fait pas l'objet d'une facture (ex.: Dons, frais de dossier, pénalité, report...).")
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/22x22/Smiley_nul.png")
        
        # Généralités
        self.staticbox_generalites_staticbox = wx.StaticBox(self, -1, _("Généralites"))
        self.label_date = wx.StaticText(self, -1, _("Date :"))
        self.ctrl_date = CTRL_Saisie_date.Date(self)
        self.label_categorie = wx.StaticText(self, -1, _("Catégorie :"))
        self.ctrl_categorie = Choix_categorie(self)
        self.label_label = wx.StaticText(self, -1, _("Intitulé :"))
        self.ctrl_label = wx.TextCtrl(self, -1, "")
        self.label_type = wx.StaticText(self, -1, _("Type :"))
        self.radio_type_familiale = wx.RadioButton(self, -1, _("Prestation familiale"), style=wx.RB_GROUP)
        self.radio_type_individuelle = wx.RadioButton(self, -1, _("Prestation individuelle :"))
        self.ctrl_individu = Choix_individu(self, self.IDfamille)
        
        # Facturation
        self.staticbox_facturation_staticbox = wx.StaticBox(self, -1, _("Facturation"))
        self.label_activite = wx.StaticText(self, -1, _("Activité :"))
        self.ctrl_activite = Choix_activite(self)
        self.label_facture = wx.StaticText(self, -1, _("Facture :"))
        self.ctrl_facture = wx.StaticText(self, -1, _("Non facturé"))

        # Code comptable
        self.label_code_comptable = wx.StaticText(self, -1, _("Code compta :"))
        self.ctrl_code_comptable = wx.TextCtrl(self, -1, "") 
        
        # Montants
        self.label_montant_avant_deduc = wx.StaticText(self, -1, _("Montant TTC (%s) :") % SYMBOLE)
        self.ctrl_montant_avant_deduc = CTRL_Saisie_euros.CTRL(self)
        self.ctrl_montant_avant_deduc.SetMinSize((80, -1))
        self.label_montant = wx.StaticText(self, -1, _("Total (%s) :") % SYMBOLE)
        self.ctrl_montant = CTRL_Saisie_euros.CTRL(self, font=wx.Font(13, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.ctrl_montant.SetBackgroundColour("#F0FBED")
        self.ctrl_montant.SetEditable(False)
        self.ctrl_montant.SetMinSize((100, -1))

        # Commandes
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png"))
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ok"), cheminImage=Chemins.GetStaticPath("Images/32x32/Valider.png"))
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Annuler"), cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png"))

        self.EnableCtrl()
        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_CHOICE, self.OnChoixCategorie, self.ctrl_categorie)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnChoixCategorie, self.ctrl_label)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioType, self.radio_type_familiale)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioType, self.radio_type_individuelle)
        self.Bind(wx.EVT_CHOICE, self.OnChoixActivite, self.ctrl_activite)
        self.Bind(wx.EVT_CHOICE, self.OnTextMontant, self.ctrl_montant_avant_deduc)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.ctrl_date.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocusDate)


        # Remplissage des contrôles
        self.dictIndividus = self.Importation_individus()
        self.ctrl_individu.SetListeDonnees(self.dictIndividus)
        
        self.listeActivites = self.Importation_activites() 
        self.ctrl_activite.SetListeDonnees(self.listeActivites)
        
        # Importation lors d'une modification
        if self.IDprestation != None :
            self.Importation() 
        else:
            self.ctrl_date.SetDate(datetime.date.today())
            self.OnKillFocusDate(None)

        # MAJ des contrôles
        self.Bind(wx.EVT_TEXT, self.OnTextMontant, self.ctrl_montant_avant_deduc)

    def __set_properties(self):
        self.ctrl_date.SetToolTip(_("Saisissez ici la date de la prestation"))
        self.ctrl_categorie.SetToolTip(_("Sélectionnez ici la catégorie de la prestation"))
        self.ctrl_label.SetToolTip(_("Saisissez un intitulé pour cette prestation"))
        self.radio_type_familiale.SetToolTip(_("Selectionnez cette case si la prestation concerne toute la famille"))
        self.radio_type_individuelle.SetToolTip(_("Selectionnez cette case si la prestation ne concerne qu'un individu"))
        self.ctrl_individu.SetToolTip(_("Selectionnez l'individu associé à la prestation"))
        self.ctrl_activite.SetToolTip(_("Selectionnez ici l'activité concernée par la prestation"))
        self.ctrl_montant_avant_deduc.SetToolTip(_("Saisissez ici le montant en Euros"))
        self.ctrl_montant.SetToolTip(_("Montant en Euros"))
        self.ctrl_facture.SetToolTip(_("Quand une prestation a été facturée, le numéro de facture apparait ici"))
        self.bouton_aide.SetToolTip(_("Cliquez ici pour obtenir de l'aide"))
        self.bouton_ok.SetToolTip(_("Cliquez ici pour valider"))
        self.bouton_annuler.SetToolTip(_("Cliquez ici pour annuler et fermer"))
        self.ctrl_code_comptable.SetToolTip(_("Saisissez le code comptable de cette prestation a utiliser pour forcer la valeur lors de l'export comptabilité [Optionnel]"))

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
        grid_sizer_facturation.Add(self.label_code_comptable, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_facturation.Add( self.ctrl_code_comptable, 0, 0, 0)

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

    def EnableCtrl(self):
        if self.mode == "visu":
            for ctrl in (self.label_date,self.ctrl_date,self.label_categorie,self.ctrl_categorie,self.label_label,
                         self.ctrl_label,self.label_type,self.radio_type_familiale,self.radio_type_individuelle,
                         self.ctrl_individu,self.label_activite,self.ctrl_activite,self.label_facture,self.ctrl_facture,
                         self.label_montant_avant_deduc,self.ctrl_montant_avant_deduc,self.label_montant,self.ctrl_montant,
                         self.label_code_comptable,self.ctrl_code_comptable,self.bouton_ok):
                ctrl.Enable(False)
        elif self.radio_type_familiale.GetValue() == True :
            self.ctrl_individu.Enable(False)
            self.ctrl_activite.Enable(False)
            self.label_activite.Enable(False)
        else:
            self.ctrl_individu.Enable(True)
            self.ctrl_activite.Enable(True)
            self.label_activite.Enable(True)

    def OnKillFocusDate(self, event):
        # controle si saisie dans un exercice ouvert
        DB = GestionDB.DB()
        dateSaisie = DateFREnDateDD(self.ctrl_date.GetValue())
        exerciceDeb, exerciceFin = DB.GetExercice(dateSaisie,approche=False)
        if exerciceDeb != None and exerciceFin != None:
            #la date est dans un exercice
            pass
        else:
            if dateSaisie >= datetime.date.today():
                #on accepte les dates futures
                pass
            else:
                self.ctrl_date.SetDate(self.dateInit)
                if dateSaisie == self.dateInit:
                    self.bouton_ok.Enable(False)
                self.Refresh()
        DB.Close()

    def OnChoixCategorie(self, event):
        self.EnableCtrl()

    def OnRadioType(self, event): 
        self.EnableCtrl()

    def OnChoixActivite(self, event):
        # MAJ du contrôle des catégories de tarifs
        IDactivite = self.ctrl_activite.GetID()

    def OnTextMontant(self, event):
        validation, message = self.ctrl_montant_avant_deduc.Validation() 
        if validation == True :
            montantInitial = self.ctrl_montant_avant_deduc.GetMontant() 
            self.ctrl_montant.SetMontant(montantInitial)
                                    
    def Importation(self):
        """ Importation des données """
        DB = GestionDB.DB()
        req = """SELECT IDprestation, prestations.IDcompte_payeur, date, categorie, label, montant_initial, montant, prestations.IDactivite, 
        prestations.IDtarif, prestations.IDfacture, IDfamille, IDindividu, temps_facture, categories_tarifs, prestations.IDcategorie_tarif, prestations.code_compta, prestations.tva,
        factures.numero
        FROM prestations 
        LEFT JOIN tarifs ON prestations.IDtarif = tarifs.IDtarif
        LEFT JOIN noms_tarifs ON tarifs.IDnom_tarif = noms_tarifs.IDnom_tarif
        LEFT JOIN factures ON factures.IDfacture = prestations.IDfacture
        WHERE IDprestation=%d;""" % self.IDprestation
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        if len(listeDonnees) == 0 :
            DB.Close()
            return
        prestation = listeDonnees[0]
        IDprestation, IDcompte_payeur, date, categorie, label, montant_initial, montant, IDactivite, IDtarif, IDfacture, IDfamille, IDindividu, temps_facture, categories_tarifs, IDcategorie_tarif, code_compta, tva, numFacture = prestation
        
        # Date
        self.ctrl_date.SetDate(date)
        self.dateInit = self.ctrl_date.GetDate()
        self.OnKillFocusDate(None)

        # Label
        self.ctrl_label.SetValue(label)
        # Catégorie
        self.ctrl_categorie.SetCategorie(categorie)
        # Individu
        if IDindividu != None and IDindividu != 0 :
            self.radio_type_individuelle.SetValue(True)
            self.ctrl_individu.SetID(IDindividu)
        # Activité
        if IDactivite != None :
            self.ctrl_activite.SetID(IDactivite)
        # Code comptable
        if code_compta != None :
            self.ctrl_code_comptable.SetValue(code_compta)
        # TVA
        # Montant initial
        self.ctrl_montant_avant_deduc.SetMontant(montant_initial)
        # Montant final
        self.ctrl_montant.SetMontant(montant)
        self.ancienMontant = montant
        # Facture
        self.IDfacture = IDfacture
        if numFacture != None :
            self.ctrl_facture.SetLabel(_("Facture n°%d") % numFacture)

    def Importation_individus(self):
        DB = GestionDB.DB()
        # Recherche les individus de la famille
        dictIndividus = {}
        req = """SELECT individus.IDindividu, IDcivilite, nom, prenom, date_naiss, IDcategorie, titulaire
        FROM individus
        LEFT JOIN rattachements ON individus.IDindividu = rattachements.IDindividu
        WHERE rattachements.IDfamille = %d
        ORDER BY nom, prenom;""" % self.IDfamille
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeIndividus = DB.ResultatReq()
        for IDindividu, IDcivilite, nom, prenom, date_naiss, IDcategorie, titulaire in listeIndividus :
            dictTemp = { 
                "IDcivilite" : IDcivilite, "nom" : nom, "prenom" : prenom, 
                "IDcategorie" : IDcategorie, "titulaire" : titulaire,
                "inscriptions" : [],
            }
            dictIndividus[IDindividu] = dictTemp 
        
        # Recherche des inscriptions pour chaque membre de la famille
        req = """SELECT inscriptions.IDinscription, IDindividu, inscriptions.IDactivite, IDgroupe, inscriptions.IDcategorie_tarif, categories_tarifs.nom
        FROM inscriptions 
        LEFT JOIN categories_tarifs ON categories_tarifs.IDcategorie_tarif = inscriptions.IDcategorie_tarif
        WHERE IDfamille = %d ;""" % self.IDfamille
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeInscriptions = DB.ResultatReq()
        for IDinscription, IDindividu, IDactivite, IDgroupe, IDcategorie_tarif, nomCategorie_tarif in listeInscriptions :
            if not IDindividu in list(dictIndividus.keys()): continue
            dictTemp = { 
                "IDinscription" : IDinscription, "IDactivite" : IDactivite, "IDgroupe" : IDgroupe, 
                "IDcategorie_tarif" : IDcategorie_tarif, "nomCategorie_tarif" : nomCategorie_tarif,
                }
            dictIndividus[IDindividu]["inscriptions"].append(dictTemp)
        
        # Cloture de la base de données
        DB.Close()
        
        return dictIndividus

    def Importation_activites(self):
        DB = GestionDB.DB()
        # Recherche les activités
        dictIndividus = {}
        req = """SELECT IDactivite, nom, abrege
        FROM activites
        ORDER BY nom;"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        listeActivites = []
        for IDactivite, nom, abrege in listeDonnees :
            dictTemp = {"IDactivite" : IDactivite, "nom" : nom, "abrege" : abrege}
            listeActivites.append(dictTemp)
        return listeActivites

    def OnBoutonAide(self, event): 
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Prestations")

    def OnBoutonOk(self, event):
        # Récupération et vérification des données saisies
        if self.IDfacture != None :
            dlg = wx.MessageDialog(self, _("Cette prestation apparaît déjà sur une facture. Il est donc impossible de la modifier !\n\nVous devez obligatoirement cliquer sur le bouton ANNULER pour quitter."), _("Validation impossible"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
            
        date = self.ctrl_date.GetDate()
        if date == None :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement saisir une date !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_date.SetFocus()
            return
        
        categorie = self.ctrl_categorie.GetCategorie() 
        
        label = self.ctrl_label.GetValue()
        if label == "" :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement saisir un intitulé !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_label.SetFocus()
            return

        categorie = self.ctrl_categorie.GetCategorie()
        if categorie == "":
            dlg = wx.MessageDialog(self,
                                   _("Vous devez obligatoirement choisir une catégorie !"),
                                   _("Erreur de saisie"),
                                   wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_categorie.SetFocus()
            return

        IDactivite = self.ctrl_activite.GetID()

        montant_initial = self.ctrl_montant_avant_deduc.GetMontant()
        montant = self.ctrl_montant.GetMontant()
        if montant == None :
            dlg = wx.MessageDialog(self, _("Le montant que vous avez saisi ne semble pas valide !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_montant.SetFocus()
            return
        
        IDfamille = self.IDfamille
        if self.radio_type_individuelle.GetValue() == True :
            IDindividu = self.ctrl_individu.GetID()
            if IDindividu == None :
                dlg = wx.MessageDialog(self, _("Etant donné que vous avez sélectionné le type 'prestation individuelle', vous devez obligatoirement sélectionner un individu dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                self.ctrl_individu.SetFocus()
                return
        else:
            IDindividu = 0
        
        code_comptable = self.ctrl_code_comptable.GetValue() 
        if code_comptable == "" :
            code_comptable = None


        # Récupération du IDcompte_payeur
        DB = GestionDB.DB()
        req = "SELECT IDcompte_payeur FROM familles WHERE IDfamille=%d" % self.IDfamille
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()     
        IDcompte_payeur = listeDonnees[0][0]
        
        # Recherche si cette prestation a déjà été ventilée sur un règlement
        if self.IDprestation != None :
            req = """SELECT IDventilation, ventilation.montant
            FROM ventilation
            LEFT JOIN reglements ON reglements.IDreglement = ventilation.IDreglement
            WHERE IDprestation=%d
            ORDER BY reglements.date;""" % self.IDprestation
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            listeVentilations = DB.ResultatReq()
            montantVentilation = 0.0
            for IDventilation, montantTmp in listeVentilations :
                montantVentilation += montantTmp
            if montantVentilation > montant :
                # Si le montant total ventilé est supérieur au montant de la prestation :
                montantVentilationTmp = 0.0
                for IDventilation, montantTmp in listeVentilations :
                    montantVentilationTmp += montantTmp
                    if montantVentilationTmp > montant :
                        nouveauMontant = montantTmp - (montantVentilationTmp - montant)
                        if nouveauMontant > 0.0 :
                            DB.ReqMAJ("ventilation", [("montant", nouveauMontant),], "IDventilation", IDventilation)
                            montantVentilationTmp =  (montantVentilationTmp - montantTmp) + nouveauMontant
                        else:
                            DB.ReqDEL("ventilation", "IDventilation", IDventilation)

        # Sauvegarde de la prestation
        listeDonnees = [    
                ("IDcompte_payeur", IDcompte_payeur),
                ("date", date),
                ("categorie", categorie),
                ("label", label),
                ("montant_initial", montant_initial),
                ("montant", montant),
                ("IDactivite", IDactivite),
                ("IDfamille", IDfamille),
                ("IDindividu", IDindividu),
                ("code_compta", code_comptable),
            ]
        if self.IDprestation == None :
            self.IDprestation = DB.ReqInsert("prestations", listeDonnees)
        else:
            DB.ReqMAJ("prestations", listeDonnees, "IDprestation", self.IDprestation)
        DB.Close()
        
        # Fermeture de la fenêtre
        self.EndModal(wx.ID_OK)
    
    def GetIDprestation(self):
        return self.IDprestation


if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dialog_1 = Dialog(None, IDprestation=38664, IDfamille=9)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()


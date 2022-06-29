#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:           Ivan LUCAS, JB, Jacques Brunel
# Licence:         Licence GNU GPL
# Permet un choix dans une liste et retourne l'indice
#------------------------------------------------------------------------

import wx
import Chemins
import copy,datetime
import FonctionsPerso as fp
from Ctrl import CTRL_Bouton_image
import decimal
from Ctrl.CTRL_ObjectListView import FastObjectListView, ObjectListView, ColumnDefn, Filter, CTRL_Outils, PanelAvecFooter
from Utils.UTILS_Decimal import FloatToDecimal
from Ctrl import CTRL_Bandeau
import GestionDB

def Nz(valeur):
    if valeur == None:
        valeur = 0
    return valeur

def FormateValue(value):   
    if not value : return ""
    if isinstance(value,(datetime.date,datetime.datetime,wx.DateTime)):
        return str(value)
    if isinstance(value,(int,float,decimal.Decimal,bool)):
        return "%.2f " % (value)
    return value

def FormateMontant(montant):   
    if not montant : return ""
    elif not isinstance(montant,(int,float,bool,decimal.Decimal)) :
        return montant
    if int(montant*100) == 0: return ""
    if isinstance(montant,(int,bool)): return "%d"%(montant)
    return "%.2f" %(montant)

def LettreSuivante(lettre=''):
    if not isinstance(lettre,str): lettre = 'A'
    if lettre == '': lettre = 'A'
    # incrémentation d'un lettrage
    lastcar = lettre[-1]
    precars = lettre[:-1]
    if ord(lastcar) in (90,122):
        if len(precars) == 0:
            precars = chr(ord(lastcar)-25)
        else:
            precars= LettreSuivante(precars)
        new = precars + chr(ord(lastcar)-25)
    else:
        new = precars + chr(ord(lastcar) + 1)
    return new

class CTRL_Solde(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, name="panel_solde", style=wx.SUNKEN_BORDER | wx.TAB_TRAVERSAL,
                          size=(100, 40))
        self.parent = parent

        # Solde du compte
        self.ctrl_solde = wx.StaticText(self, -1, "0.00 ")
        font = wx.Font(11, wx.SWISS, wx.NORMAL, wx.BOLD)
        self.ctrl_solde.SetFont(font)

        # Layout
        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=1, vgap=5, hgap=5)
        grid_sizer_base.Add(self.ctrl_solde, 1, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(0)
        # self.SetToolTip(u"Solde")
        self.ctrl_solde.SetToolTip("Solde")

    def SetSolde(self, montant=FloatToDecimal(0.0)):
        """ MAJ intégrale du controle avec MAJ des donnees """
        if montant > FloatToDecimal(0.0):
            label = "+ %.2f " % (montant)
            self.SetBackgroundColour("#C4BCFC")  # Bleu
        elif montant == FloatToDecimal(0.0):
            label = "0.00 "
            self.SetBackgroundColour("#5DF020")  # Vert
        else:
            label = "- %.2f " % (-montant,)
            self.SetBackgroundColour("#F81515")  # Rouge
        self.ctrl_solde.SetLabel(label)
        self.Layout()
        self.Refresh()

class Track(object):
    def __init__(self, donnees,champs):
        for ix in range(len(champs)):
            champ= champs[ix]
            setattr(self, "%s" % champ, donnees[ix])

            # -------------------------------------------------------------------------------------------------------------------------------------------

class ListView(ObjectListView):
    def __init__(self, *args, **kwds):
        kwds['style'] = wx.LC_REPORT | wx.SUNKEN_BORDER | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES
        ObjectListView.__init__(self, *args,**kwds)

class ListviewAvecFooter(PanelAvecFooter):
    def __init__(self, parent, dictFooter={}, kwargs={}):
        PanelAvecFooter.__init__(self, parent, ListView, kwargs, dictFooter)

#---------------------------------------------------------------------------------------------------------------------

class DLGventilations(wx.Dialog):
    # Gestion d'un lettrage à partir de deux dictionnaires d'écritures, ventilations, liste des champs de désignations
    # La clé des dictionnaires est l'ID  (origine fichier), ensuite deux clés 'designations, montant.
    # les tuples de ventilations sont IDdebit, IDcredit, montant
    # la liste champs de désignation est les labels correspondants aux valeurs désignations des dictionnaires
    
    def __init__(self, parent,ddDebits={},ddCredits={},ltVentilations=[],lChampsDesign=(),**kwds):

        parentName = parent.__class__.__name__
        self.parent = parent
        intro =         kwds.pop('intro',"Cochez les lignes associées puis cliquez sur lettrage ou délettrage...")
        titre_bandeau = kwds.pop('titre',"Lettrage par les montants ventilés")
        titre_frame =   kwds.pop('titre_frame',"%s / CTRL_ChoixListe.DLGventilations"%parentName)
        dfooter   =  {"debit" : {"mode" : "total"},
                        "mtt" : {"mode" : "total"},
                        "credit" : {"mode" : "total"},}
        dictFooter =    kwds.pop('dictFooter',dfooter)
        autoLayout =    kwds.pop('autoLayout',True)
        columnSort =    kwds.pop('columnSort',2)
        lstWidth =      kwds.pop('lstWidts',None)
        minSize  =      kwds.pop('minSize',(500, 350))

        kwdlg = {}
        kwdlg['size']=  kwds.pop('size',(1000, 500))
        kwdlg['pos']=  kwds.pop('pos',(300,150))
        style = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX
        kwdlg['style']= kwds.pop('style',style)
        wx.Dialog.__init__(self, None, -1, **kwdlg)

        self.multiwidth = 7 # multiplicateur du nombre de caratère dans la colonne pour déterminer la largeur
        self.maxWidth = 250 # longeur maxi d'une colonne avant extend
        self.lstWidth = lstWidth
        self.SetMinSize(minSize)
        self.SetTitle(titre_frame)
        self.ltVentilationsOriginal = copy.deepcopy(ltVentilations)
        self.ltVentilations = ltVentilations
        self.ddDebits = ddDebits
        self.ddCredits = ddCredits
        self.lChampsDesign = lChampsDesign
        self.columnSort = columnSort
        self.choix = None
        self.nbChampsDesign = len(lChampsDesign)
        self.autoWidth = False
        if not self.lstWidth:
            self.autoWidth = True
        self.ixDateD = None
        self.ixDateC = None
        # conteneur des données OLV
        self.pnlListview = ListviewAvecFooter(self, dictFooter = dictFooter, kwargs=kwds)
        self.listview = self.pnlListview.GetListview()
        self.ctrl_outils = CTRL_Outils(self, listview=self.listview, afficherCocher=True)

        # préaffectation des pointeurs de ventilations pour accès plus rapide colonnes vent et reste
        let = "d`" # da sera la première lettre
        for key,dic in self.ddDebits.items():
            let = LettreSuivante(let)
            dic['ptVentil']= let
        let = "c`" # ca sera la première lettre
        for key,dic in self.ddCredits.items():
            let = LettreSuivante(let)
            dic['ptVentil']= let

        # préparation des libellés de colonnes, remplissage à blanc
        champsDesign = ["",]*(self.nbChampsDesign)
        champsMilieu = ["Lettre D-C","Débit","Mtt lettre","Crédit","cID",]
        champsEntete = ["dID",]
        self.lstLibels =  champsEntete  + champsDesign +champsMilieu+ champsDesign
        self.nbColonnes = len(self.lstLibels)

        self.ixChampsDebits = len(champsEntete)
        self.ixChampsMilieu = self.ixChampsDebits +self.nbChampsDesign
        self.ixChampsCredits = self.ixChampsMilieu + len(champsMilieu)

        #insertion des libelles désignations après l'ID en entête
        ix = 0
        for champ in lChampsDesign:
            self.lstLibels[self.ixChampsDebits + ix] = 'd' + champ
            self.lstLibels[self.ixChampsCredits + ix] = 'c' + champ
            ix +=1

        # constitution de liste des codes (le premier mot du libellé de la colonne, sans accent et en minuscule)
        self.lstCodes = [fp.Supprime_accent(x.split(" ")[0].strip()).lower() for x in self.lstLibels]
        if "ddate" in self.lstCodes:
            self.ixDateD = self.lstCodes.index("ddate")
        if "cdate" in self.lstCodes:
            self.ixDateC = self.lstCodes.index("cdate")

        # vérif unicité code
        lstano = [x for x in self.lstCodes if self.lstCodes.count(x)>1]
        if len(lstano)>0:
            mess = "Les noms des champs doivent être uniques dans un même liste liste!\n voir le doublon: '%s'"%lstano[0]
            wx.MessageBox(mess, "Impossible")
            return


        # calcul de la largeur nécessaire pour les colonnes si non fournie en kwds
        self.lstDonnees = []
        if self.autoWidth:
            self.lstWidth = [50]*(self.nbColonnes) # préalimentation d'une largeur par défaut
            for libel in self.lstLibels:
                if self.lstWidth[self.lstLibels.index(libel)] < self.multiwidth*len(libel)+10:
                    self.lstWidth[self.lstLibels.index(libel)] = min(self.maxWidth,self.multiwidth*len(libel)+10)

        # Bandeau
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre_bandeau, texte=intro, hauteurHtml=15,
                                                 nomImage=Chemins.GetStaticPath("Images/22x22/Smiley_nul.png"))

        # Pied de l'écran
        self.case_avecLettrees = wx.CheckBox(self,-1,"Masquer les lignes entièrement lettrées")
        self.bouton_lettrer = CTRL_Bouton_image.CTRL(self, texte="Lettrer", cheminImage="Images/32x32/Configuration2.png")
        self.bouton_delettrer = CTRL_Bouton_image.CTRL(self, texte="DeLettrer", cheminImage="Images/32x32/Depannage.png")
        self.bouton_fermer = CTRL_Bouton_image.CTRL(self, texte="Annuler", cheminImage="Images/32x32/Annuler.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte="Valider", cheminImage="Images/32x32/Valider.png")
        self.__set_properties()
        if autoLayout:
            self.MAJ()
            self.__do_layout()

    def __set_properties(self):
        # TipString, Bind et constitution des colonnes de l'OLV
        self.case_avecLettrees.SetToolTip("Cliquez ici après avoir coché des lignes à associer")
        self.bouton_lettrer.SetToolTip("Cliquez ici après avoir coché des lignes à associer")
        self.bouton_delettrer.SetToolTip("Cliquez ici après avoir sélectionné une ligne de la lettre à supprimer")
        self.bouton_ok.SetToolTip("Cliquez ici pour valider et enregistrer les modifications")
        self.bouton_fermer.SetToolTip("Cliquez ici pour abandonner les modifications")
        self.listview.SetToolTip("Double Cliquez pour cocher")
        # Binds
        self.Bind(wx.EVT_BUTTON, self.OnClicOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnClicFermer, self.bouton_fermer)
        self.Bind(wx.EVT_CHECKBOX, self.OnCaseLettrees, self.case_avecLettrees)
        self.Bind(wx.EVT_BUTTON, self.OnClicLettrer, self.bouton_lettrer)
        self.Bind(wx.EVT_BUTTON, self.OnClicDelettrer, self.bouton_delettrer)
        self.listview.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnDblClic)

    def __do_layout(self):
        gridsizer_base = wx.FlexGridSizer(rows=6, cols=1, vgap=0, hgap=0)

        gridsizer_base.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)
        gridsizer_base.Add(self.pnlListview, 5, wx.LEFT | wx.RIGHT | wx.EXPAND, 0)
        gridsizer_base.Add(self.ctrl_outils, 1, wx.EXPAND, 0)
        gridsizer_base.Add((5, 5), 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 0)

        # Bas d'écran
        gridsizer_boutons = wx.FlexGridSizer(rows=1, cols=7, vgap=0, hgap=0)
        gridsizer_boutons.Add((20, 20), 1, wx.ALIGN_BOTTOM, 0)
        gridsizer_boutons.Add(self.case_avecLettrees, 1, wx.EXPAND, 0)
        gridsizer_boutons.Add(self.bouton_lettrer, 1, wx.EXPAND, 0)
        gridsizer_boutons.Add(self.bouton_delettrer, 1, wx.EXPAND, 0)
        gridsizer_boutons.Add((20, 20), 1, wx.ALIGN_BOTTOM, 0)
        gridsizer_boutons.Add(self.bouton_fermer, 1, wx.EXPAND, 0)
        gridsizer_boutons.Add(self.bouton_ok, 1, wx.EXPAND, 0)
        gridsizer_boutons.AddGrowableCol(0)
        gridsizer_base.Add(gridsizer_boutons, 1, wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        gridsizer_base.AddGrowableRow(1)
        gridsizer_base.AddGrowableCol(0)
        self.SetSizer(gridsizer_base,)
        self.Layout()

    def InitModel(self):
        # transformation des lignes en track pour l'OLV
        self.tracks = [Track(don,self.lstCodes ) for don in self.lstDonnees]

    def InitObjectListView(self):
        # Couleur en alternance des lignes
        self.listview.oddRowsBackColor = "#F0FBED"
        self.listview.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.listview.useExpansionColumn = True

        # Image list
        self.imgVert = self.listview.AddNamedImages("vert", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ventilation_vert.png"), wx.BITMAP_TYPE_PNG))
        self.imgRouge = self.listview.AddNamedImages("rouge", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ventilation_rouge.png"), wx.BITMAP_TYPE_PNG))
        self.imgOrange = self.listview.AddNamedImages("orange", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ventilation_orange.png"), wx.BITMAP_TYPE_PNG))
        self.imgVertRond = self.listview.AddNamedImages("vert", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Euro_vert.png"), wx.BITMAP_TYPE_PNG))
        self.imgOrangeRond = self.listview.AddNamedImages("orange", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Euro_orange.png"), wx.BITMAP_TYPE_PNG))


        # Construction des colonnes de l'OLV
        lstColumns = []
        for ix in range(0,self.nbColonnes):
            lstColumns.append(
                ColumnDefn(self.lstLibels[ix], self.lstJustifs[ix],
                           width=self.lstWidth[ix],
                           isSpaceFilling = (self.lstWidth[ix] > 150 or ix in (self.ixChampsCredits,self.ixChampsDebits)),
                           valueGetter=self.lstCodes[ix],
                           valueSetter=self.lstValSetter[ix],
                           typeDonnee=self.lstTypesDonnees[ix],
                           isEditable=False))
            # retouche sur la colonne en cours de création
            if lstColumns[-1].typeDonnee in ('entier','montant'):
                lstColumns[-1].stringConverter = FormateMontant
            if lstColumns[-1].typeDonnee in ('date',):
                lstColumns[-1].width = 80
            if lstColumns[-1].valueGetter == "lettre":
                lstColumns[-1].imageGetter=self.GetCouleurLettre
            if lstColumns[-1].valueGetter == "did":
                lstColumns[-1].imageGetter=self.GetCouleurDID
                lstColumns[-1].width = 60
            if lstColumns[-1].valueGetter == "cid":
                lstColumns[-1].imageGetter=self.GetCouleurCID
                lstColumns[-1].width = 60
            if lstColumns[-1].valueGetter in ('debit','credit'):
                # l'édition est non encore implementée
                lstColumns[-1].isEditable=False
                if self.autoWidth:
                    lstColumns[-1].width = 60

        lstColumns[0].width += 20
        self.listview.SetColumns(lstColumns)
        self.listview.SetSortColumn(self.columnSort)
        self.listview.CreateCheckStateColumn(self.ixChampsMilieu+1)
        self.listview.SetObjects(self.tracks)
        self.listview.CocheListeRien()
        equilibre = {'typeDonnee': "libre",'criteres': "track.lettre.upper() != track.lettre",
                     'choix':"",'code':"",'titre':"",}

        if self.case_avecLettrees.GetValue() == True:
            if not equilibre in self.listview.listeFiltresColonnes:
                self.listview.listeFiltresColonnes += [equilibre,]
        elif equilibre in self.listview.listeFiltresColonnes:
            self.listview.listeFiltresColonnes.remove(equilibre)

        #self.listview.cellEditMode = ObjectListView.CELLEDIT_DOUBLECLICK

    def MAJ(self):
        self.ComposeLignes(self.ddDebits,self.ddCredits)
        self.Lettrage()
        self.InitModel()
        self.InitObjectListView()
        self.Layout()
        search = self.ctrl_outils.barreRecherche.GetValue()
        self.listview.Filtrer(search)

    # affectation de la couleur de l'image
    def GetCouleurLettre(self,track):
        if track.lettre and len(track.lettre)>0 and track.lettre == track.lettre.upper():
            return self.imgVert
        elif track.cid > 0 and  track.credit and self.ddCredits[track.cid]['montant'] * track.credit < 0.0:
            return self.imgRouge
        elif track.did > 0 and track.debit and self.ddDebits[track.did]['montant'] * track.debit < 0.0:
            return self.imgRouge
        elif track.did != 0:
            return self.imgOrange

    def GetCouleurDID(self,track):
        # si lettrage non vert
        if track.lettre and len(track.lettre)>0 and track.lettre == track.lettre.upper():
            return
        # teste la couleur du côté débit
        if track.did > 0:
            if abs(self.ddDebits[track.did]['montant'] - self.ddDebits[track.did]['mtVentil']) < 0.005:
                return self.imgVertRond
            else: return self.imgOrangeRond

    def GetCouleurCID(self, track):
        # si lettretrage non vert
        if track.lettre and len(track.lettre)>0 and track.lettre == track.lettre.upper():
            return
        # teste la couleur du côté crédit
        if track.cid > 0:
            if abs(self.ddCredits[track.cid]['montant'] - self.ddCredits[track.cid]['mtVentil']) < 0.005:
                return self.imgVertRond
            else:
                return self.imgOrangeRond

    def ComposeLignes(self,ddDebits, ddCredits):
        # composition des protolignes
        self.lstDonnees = []
        
        # raz des champs cumuls ventilations dans les fichiers originaux
        for key,dic in ddDebits.items():
            dic['mtVentil'] = 0.0
        for key,dic in ddCredits.items():
            dic['mtVentil'] = 0.0
    
        # déroulé des ventilations pour créer les lignes
        for kdeb, kcre, mtvent in self.ltVentilations:

            # passe les ventilations non complètes par deux ID != 0 et présents
            if (not (kdeb in list(ddDebits.keys()) and kcre in list(ddCredits.keys()))):
                continue
            # initialise les données, les champs désignation viendront ensuite
            donnee = [""] * self.nbColonnes

            # données de l'entête
            donnee[0] = kdeb 

            # calcul des donnée du milieu
            dmtt, cmtt = 0.0 , 0.0
            if kdeb in list(ddDebits.keys()):
                dmtt = ddDebits[kdeb]["montant"]
            if kcre in list(ddCredits.keys()):
                cmtt = ddCredits[kcre]["montant"]

            donneesMilieu = ["",dmtt,mtvent,cmtt,kcre]
            for ix in range(len(donneesMilieu)):
                donnee[self.ixChampsMilieu + ix] = donneesMilieu[ix]

            # alimentation des données des désignations débits puis crédits
            key = kdeb
            ixMt = self.ixChampsMilieu
            ixDesign = self.ixChampsDebits
            for dic in (self.ddDebits,self.ddCredits):
                item = dic[key]
                item['mtVentil'] += mtvent
                for i in range(self.nbChampsDesign):
                    donnee[ixDesign+i] = item["designations"][i]
                    if self.autoWidth:
                        if isinstance(item["designations"][i], (str)):
                            lg = len(item["designations"][i])
                        else:
                            lg = len(str(item["designations"][i]))
                        if self.lstWidth[ixDesign] < self.multiwidth * lg + 10:
                            self.lstWidth[ixDesign] = min(self.maxWidth, self.multiwidth * lg + 10)
                ixDesign = self.ixChampsCredits
                key = kcre
                ixMt = self.ixChampsCredits-1
            self.lstDonnees.append(donnee)

        # traitement des ventilation présentes avec des opposées à zéro
        for kdeb, kcre, mtvent in self.ltVentilations:
            # passe les ventilations déja traitées car complètes par deux ID != 0
            if kdeb != 0 and kcre != 0:
                continue
            if kdeb == 0:
                let = "c@"
                key = kcre
                ddDic = self.ddCredits
            elif kcre == 0:
                let = "d@"
                key = kdeb
                ddDic = self.ddDebits
            else: continue

            item = ddDic[key]
            # la clé opposée est nulle!
            item['ptVentil'] = let


    # --------------- passages supplémentaires pour constituer des lignes non ventilées ------------------
        ixID = 0
        ixDesign = self.ixChampsDebits
        ixMt = self.ixChampsMilieu + 1
        mttVentil = 0.0 # montant de ventilation des lignes négatives compensant d'autres dans la colonne
        ptVentil = None # reperage de la lettre commune de compensation
        dicLetEquil = {}
        for ddDic in (self.ddDebits,self.ddCredits):
            ixIDzero = None
            for key,item in ddDic.items():
                # déroule tous les items, une ligne pour chacun restant à lettrer
                if abs(item['montant'] - item['mtVentil']) < 0.005:
                    continue
                donnee = [""] * self.nbColonnes
                champsNum = [ x for x in range(self.ixChampsMilieu + 1,self.ixChampsCredits-1)]
                champsNum += [self.ixChampsDebits-1,self.ixChampsCredits-1,]
                for ix in champsNum:
                    donnee[ix] = 0
                # Test pour éventuelles compensations négatives dans la colonne
                if '@' in item['ptVentil']:
                    if mttVentil == 0: # nouveau groupe de lignes
                        ptVentil = item['ptVentil']
                        dicLetEquil[ptVentil] = []

                    mttVentil += item['montant'] - item['mtVentil']
                    dicLetEquil[ptVentil].append(key)

                # données de la demi ligne
                donnee[ixID] = key
                donnee[self.ixChampsMilieu + 2] = item['montant'] - item['mtVentil']
                donnee[ixMt] = item['montant']
                for ix in range(self.nbChampsDesign):
                    donnee[ixDesign + ix] = item['designations'][ix]
                self.lstDonnees.append(donnee)

            if mttVentil != 0: # la derniere lettre de suivi d'equilibre n'est pas équlibrée
                del dicLetEquil[ptVentil]
            for let, lstID in dicLetEquil.items(): # traitement des lettres s'équilibrant dans la colonne
                for IDitem in lstID:
                    item  = ddDic[IDitem]
                    item['ptVentil'] = let.upper()
                    item['mtVentil'] = item['montant']

            # fixe les index pour le deuxième passage (crédits)
            ixID = self.ixChampsCredits - 1
            ixMt = self.ixChampsCredits - 2
            ixDesign = self.ixChampsCredits
            mttVentil = 0.0 # montant de ventilation des lignes négatives compensant d'autres dans la colonne
            ptVentil = None # reperage de la lettre commune de compensation
            dicLetEquil = {}

        # ----------------- Constitution des valeurs par défaut ---------------------------------------------
        self.lstValSetter = [None,] * self.nbColonnes
        self.lstTypesDonnees = ['texte',] * self.nbColonnes
        self.lstJustifs = ['centre',] * self.nbColonnes
        for i in range(len(self.lstDonnees)):
            for ix in range(self.nbColonnes):
                value = self.lstDonnees[i][ix]
                if value == None:
                    continue
                self.lstValSetter[ix]=value
                if isinstance(value,(float,decimal.Decimal)):
                    self.lstTypesDonnees[ix] = "montant"
                    self.lstJustifs[ix] = "right"
                elif isinstance(value, (int)):
                    self.lstTypesDonnees[ix] = "entier"
                    self.lstJustifs[ix] = "right"
                elif isinstance(value, (datetime.date,datetime.datetime,wx.DateTime)):
                    self.lstTypesDonnees[ix] = "date"
                    self.lstJustifs[ix] = "centre"
                elif isinstance(value, (str)) and len(value) == 10 and '-' in value:
                    self.lstTypesDonnees[ix] = "date"
                    self.lstJustifs[ix] = "centre"
                elif isinstance(value,str) and len(value) > 0:
                    self.lstTypesDonnees[ix] = "texte"
                    self.lstJustifs[ix] = "left"
        return

    def Lettrage(self):
        # application de la lettre dans les données
        ixLet = self.ixChampsMilieu
        ixIDc = self.ixChampsCredits - 1 # l'ID précède les champs désignés

        # compose la lettre de la ligne à partir des deux moitiés assemblées
        for donnee in self.lstDonnees:
            letD, letC = '', ''
            if donnee[0] > 0 :
                letD = self.ddDebits[donnee[0]]['ptVentil']

            if donnee[ixIDc] > 0:
                letC += str(self.ddCredits[donnee[ixIDc]]['ptVentil'])

            # forcer en majuscule si la partie le crédit ou le débit est totalement ventilé
            if donnee[0] > 0:
                if abs(self.ddDebits[donnee[0]]['montant'] - self.ddDebits[donnee[0]]['mtVentil']) < 0.005:
                    letD = letD.upper()
                    self.ddDebits[donnee[0]]['ptVentil'] = letD
            if donnee[ixIDc] > 0:
                if abs(self.ddCredits[donnee[ixIDc]]['montant'] - self.ddCredits[donnee[ixIDc]]['mtVentil']) < 0.005:
                    letC = letC.upper()
                    self.ddCredits[donnee[ixIDc]]['ptVentil'] = letC
            donnee[ixLet] = letD + '-' +letC

        return

    def OnDblClic(self, event):
        state = self.listview.GetCheckState(self.listview.GetSelectedObject())
        if state:
            state = False
        else:
            state = True
        self.listview.SetCheckState(self.listview.GetSelectedObject(), state)
        self.listview.Refresh()

    def ClearLetters(self,choix):
        # récup des ID à lettrer, puis suppression des items
        lstletDeb, lstletCre = [], []
        for track in choix:
            for kdeb, kcre, mtvent in self.ltVentilations:
                if kdeb == track.did and kcre == track.cid:
                    self.ltVentilations.remove((kdeb, kcre, mtvent))
                    if kcre > 0:
                        lstletCre.append(kcre)
                        self.ddCredits[kcre]['mtVentil'] -= mtvent
                        self.ddCredits[kcre]['ptVentil'] = self.ddCredits[kcre]['ptVentil'].lower()
                    if kdeb > 0:
                        lstletDeb.append(kdeb)
                        self.ddDebits[kdeb]['mtVentil'] -= mtvent
                        self.ddDebits[kdeb]['ptVentil'] = self.ddDebits[kdeb]['ptVentil'].lower()
        # changement de casse par extension
        for key,item in self.ddCredits.items():
            if item['ptVentil'] in lstletCre:
                item['ptVentil'] = item['ptVentil'].lower()
        for key,item in self.ddDebits.items():
            if item['ptVentil'] in lstletDeb:
                item['ptVentil'] = item['ptVentil'].lower()

    def OnCaseLettrees(self,event):
        self.MAJ()

    def OnClicLettrer(self, event):
        choix = self.listview.GetCheckedObjects()
        if len(choix) == 0:
            event.Skip()
            return

        # on réassocie en ventilation toutes les lignes selectionnées
        lettrer = [x for x in choix]
        if len(lettrer) < 2  :
            wx.MessageBox("Pas de lettrage possible !\n\nIl faut cocher plusieurs lignes")
            event.Skip()
            return

        # on délettre tout ce qui était coché, avant de refaire les ventilations
        self.ClearLetters(choix)

        # constitution de listes de tuple (montant à ventiler, ID) pour les lignes cochées
        ldid = set([x.did for x in choix if x.did >0])
        ldmtt = [self.ddDebits[x]['montant']-self.ddDebits[x]['mtVentil']  for x in ldid]
        # tri par date des opérations si présence d'une colonne date
        if self.ixDateD:
            lddate =  [self.ddDebits[x]['designations'][self.ixDateD-1] for x in ldid]
            temp = sorted(zip(lddate,ldmtt,ldid))
            ltDebits = [(y,z) for (x,y,z) in temp]
        else:
            ltDebits = list(zip(ldmtt,ldid))

        # idem pour les crédits
        lcid = [x.cid for x in choix if x.cid >0]
        lcmtt = [self.ddCredits[x]['montant']-self.ddCredits[x]['mtVentil']  for x in lcid]
        if self.ixDateC:
            lcdate =  [self.ddCredits[x]['designations'][self.ixDateD-1] for x in lcid]
            temp = sorted(zip(lcdate,lcmtt,lcid))
            ltCredits = [(y,z) for (x,y,z) in temp]
        else:
            ltCredits = list(zip(lcmtt,lcid))

        # les liste de tuple vont se conjuguer

        # compensations des opposés dans une même colonne
        ddSerie = self.ddDebits
        ix= 0
        for ltSerie in (ltDebits,ltCredits):
            negatifs = [(x,y) for (x,y) in ltSerie if x <= -0.005]
            for mt,id in negatifs:
                let = ddSerie[id]['ptVentil']
                for mtopp, idopp in ltSerie:
                    if mtopp < 0.005:
                        continue
                    mtVentil = min(abs(mt) - ddSerie[id]['mtVentil'] , mtopp - ddSerie[idopp]['mtVentil'])
                    if mtVentil < 0.05: continue
                    # association par règlement 0
                    ddSerie[id]['mtVentil'] += -mtVentil
                    ddSerie[idopp]['mtVentil'] += mtVentil
                    ddSerie[idopp]['ptVentil'] = let
                    if ix == 0:
                        self.ltVentilations.append((id, 0, -mtVentil))
                        self.ltVentilations.append((idopp, 0, mtVentil))
                    else:
                        self.ltVentilations.append((0,id, -mtVentil))
                        self.ltVentilations.append((0,idopp, mtVentil))
            ddSerie = self.ddCredits
            ix = 1
                        
        # ventilation par déroulé des deux listes
        def ventile(debits,credits):
            ltrestedeb = []
            restedeb = 0.0
            # déroule la partie gauche
            for mttd, idd in debits:
                # montant restant à ventiler
                restedeb += self.ddDebits[idd]['montant']-self.ddDebits[idd]['mtVentil']

                # déroule la partie droite
                ltrestecre = []
                restecre = 0.0
                for mttc, idc in credits:
                    restecre = self.ddCredits[idc]['montant'] - self.ddCredits[idc]['mtVentil']
                    # associations de montant de mêmes signes et non nuls
                    if restedeb * mttc > 0.005:

                        mtVentil = min(abs(restedeb),
                                       abs(restecre),
                                       abs(self.ddDebits[idd]['montant'] - self.ddDebits[idd]['mtVentil']))
                        if mtVentil != 0.0:
                            self.ddDebits[idd]['mtVentil'] += mtVentil
                            self.ddCredits[idc]['mtVentil'] += mtVentil
                            self.ltVentilations.append((idd, idc, mtVentil))
                            restedeb -= mtVentil
                            restecre -= mtVentil
                            mttc -= mtVentil
                    if abs(restecre) >= 0.005:
                        ltrestecre.append((restecre, idc))
                if abs(restedeb) >= 0.005:
                    ltrestedeb.append((restedeb, idd))
                if len(ltrestedeb) >0 and len(ltrestecre) > 0 and ltrestedeb != debits and ltrestecre != credits:
                    ventile(ltrestedeb,ltrestecre)
            return

        ventile(ltDebits,ltCredits)

        # supprime les affectations de sens inversés sur les id considérés
        for id in ldid:
            for kdeb, kcre, mtvent in  self.ltVentilations:
                if id == kdeb and mtvent * self.ddDebits[id]['montant'] < -0.005:
                    self.ltVentilations.remove((kdeb, kcre, mtvent))
        for id in lcid:
            for kdeb, kcre, mtvent in  self.ltVentilations:
                if id == kcre and mtvent * self.ddCredits[id]['montant'] < -0.005:
                    self.ltVentilations.remove((kdeb, kcre, mtvent))
        self.Lettrage()
        event.Skip()
        self.MAJ()

    def OnClicDelettrer(self, event):

        choix = self.listview.GetSelectedObjects()
        if len(choix) == 0:
            event.Skip()
            return

        delettrer = [x for x in choix if x.cid and x.did and x.cid * x.did > 0]
        if len(delettrer) == 0:
            mess = "Il faut cocher des lignes complètes pour pouvoir dissocier Débit  et Crédit"
            wx.MessageBox("Pas d'association!\n\n%s"%mess)
        self.ClearLetters(choix)
        event.Skip()
        self.MAJ()

    def OnClicFermer(self, event):
        self.choix = []
        self.EndModal(wx.ID_CANCEL)

    def OnClicOk(self, event):

        self.EndModal(wx.ID_OK)

    def GetVentilSuppr(self):
        return [x for x in self.ltVentilationsOriginal if not x in self.ltVentilations]

    def GetVentilNews(self):
        return [x for x in self.ltVentilations if not x in self.ltVentilationsOriginal]

class DialogLettrage(wx.Dialog):
    # Gestion d'un lettrage à partir de deux dictionnaires, mots clés des champs : montant en dernière position
    # La première colonne sera le sens suivi de l'ID (origine fichier). La suite sera les champs
    # le dernier champ montant étant remplacé par lettre et débit puis crédit
    def __init__(self, parent,dicList1={},lstChamps1=[],dicList2={},lstChamps2=[],lstLettres=[],**kwds):

        parentName = parent.__class__.__name__
        intro = kwds.pop('intro',"Cochez les lignes associées puis cliquez sur lettrage...")
        titre_bandeau = kwds.pop('titre',"Lettrage des montants")
        titre_frame = kwds.pop('titre_frame',"parent: %s - CTRL_ChoixListe.DialogLettrage"%parentName)
        autoLayout = kwds.pop('autoLayout',True)
        columnSort = kwds.pop('columnSort',2)
        LargeurCode = kwds.pop('LargeurCode',80)
        LargeurLib = kwds.pop('LargeurLib',100)
        width,height  = kwds.pop('minSize',(450, 350))

        if not 'style' in list(kwds.keys()):
            kwds['style'] = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX
        kwds['size'] = wx.Size(width,height)
        wx.Dialog.__init__(self, None, -1, **kwds)

        self.SetTitle(titre_frame)
        self.lstLettres = [x for x in lstLettres]
        self.dicList1 = dicList1
        self.dicList2 = dicList2
        self.lstChamps1 = lstChamps1
        self.lstChamps2 = lstChamps2
        self.columnSort = columnSort
        #self.minSize = minSize
        self.wCode = LargeurCode
        self.wLib = LargeurLib
        self.nbValeurs = len(lstChamps2)
        if len(lstChamps1) > len(lstChamps2): self.nbValeurs = len(lstChamps1)
        self.nbColonnes = self.nbValeurs + 4
        self.lstLibels = ["DC","ID",]+(["",]*(self.nbValeurs-1))+["Let","Débits","Crédits",]
        #composition des libelles colonnes et des codes
        i=2
        for item in lstChamps1:
            if item.lower() == "montant": continue
            self.lstLibels[i] = item
            i +=1
        i=2
        for item in lstChamps2:
            if item.lower() == "montant": continue
            if self.lstLibels[i] != item:
                self.lstLibels[i] += "/%s"%item
            i +=1
        # le code est le dernier mot du libellé de la colonne, sans accent et en minuscule
        self.lstCodes = [fp.Supprime_accent(x.split("/")[0].strip()).lower() for x in self.lstLibels]
        # vérif unicité code
        lstano = [x for x in self.lstCodes if self.lstCodes.count(x)>1]
        if len(lstano)>0:
            wx.MessageBox("Les noms des champs doivent être uniques dans un même liste liste!\n voir le doublon: '%s'"%lstano[0], "Impossible")
            return
        # constitution de la liste de données et calcul au passage de la largeur nécessaire pour les colonnes
        self.lstDonnees = []
        self.lstWidth = [40]*(self.nbColonnes+1) # préalimentation d'une largeur par défaut
        multiwidth = 7 # multiplicateur du nombre de caractère maxi dans la colonne pour déterminer la largeur
        for libel in self.lstLibels:
            if self.lstWidth[self.lstLibels.index(libel)] < multiwidth*len(libel)+10:
                self.lstWidth[self.lstLibels.index(libel)] = multiwidth*len(libel)+10
        self.lstWidth[0]=0 # largeur de la colonne DC
        self.lstWidth[1]=55 # largeur de la colonne ID

        for sens in (+1.0,-1.0):
            # les montants seront alignés dans les deux colonnes le plus à droite
            if sens == +1.0:
                ixMtt = self.nbColonnes-2
                dic = dicList1
                champs = lstChamps1
            else:
                ixMtt = self.nbColonnes-1
                dic = dicList2
                champs = lstChamps2
            if not "montant" in str(champs).lower():
                wx.MessageBox("Les listes de données n'ont pas chacune un champ 'montant'!","Impossible")
                return
            nbval = len(champs)
            # balayage des deux dictionnaires de données et de leur liste de champs
            for key,item in dic.items():
                donnee=[sens,key] + ([""]*(self.nbValeurs-1)) + ["",0.0,0.0]
                ixVal = 2
                valMtt = 0.0
                for i in range(nbval):
                    if "montant" in champs[i].lower():
                        valMtt = item[i]
                        continue
                    donnee[ixVal] = item[i]
                    if isinstance(item[i],(str)):
                        lg = len(item[i])
                    else: lg = len(str(item[i]))
                    if self.lstWidth[ixVal] < lg*multiwidth + 10:
                        self.lstWidth[ixVal] = min(250,lg*multiwidth + 10)
                    ixVal += 1
                # ajout du montant à droite
                donnee[ixMtt] = valMtt
                self.lstDonnees.append(donnee)

        # Bandeau
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre_bandeau, texte=intro, hauteurHtml=15,
                                                 nomImage=Chemins.GetStaticPath("Images/22x22/Smiley_nul.png"))
        # conteneur des données
        self.listview = FastObjectListView(self, id=-1,
                                           style=wx.LC_REPORT | wx.SUNKEN_BORDER | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES)
        self.listview.SetMinSize((10, 10))
        self.ctrl_outils = CTRL_Outils(self, listview=self.listview, afficherCocher=True)

        # Boutons
        self.bouton_lettrer = CTRL_Bouton_image.CTRL(self, texte="Lettrer", cheminImage="Images/32x32/Configuration2.png")
        self.bouton_delettrer = CTRL_Bouton_image.CTRL(self, texte="DeLettrer", cheminImage="Images/32x32/Depannage.png")
        self.bouton_fermer = CTRL_Bouton_image.CTRL(self, texte="Annuler", cheminImage="Images/32x32/Annuler.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte="Valider", cheminImage="Images/32x32/Valider.png")
        self.__set_properties()
        if autoLayout:
            self.MAJ()
            self.__do_layout()
        DB = GestionDB.DB()
        self.txtIDuser = "7"+("0000"+ str(DB.IDutilisateurActuel()))[-4:]
        DB.Close()

    def __set_properties(self):
        # TipString, Bind et constitution des colonnes de l'OLV
        self.bouton_lettrer.SetToolTip("Cliquez ici après avoir coché des lignes à associer")
        self.bouton_delettrer.SetToolTip("Cliquez ici après avoir sélectionné une ligne de la lettre à supprimer")
        self.bouton_ok.SetToolTip("Cliquez ici pour valider et enregistrer les modifications")
        self.bouton_fermer.SetToolTip("Cliquez ici pour abandonner les modifications")
        self.listview.SetToolTip("Double Cliquez pour cocher")
        # Binds
        self.Bind(wx.EVT_BUTTON, self.OnClicOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnClicFermer, self.bouton_fermer)
        self.Bind(wx.EVT_BUTTON, self.OnClicLettrer, self.bouton_lettrer)
        self.Bind(wx.EVT_BUTTON, self.OnClicDelettrer, self.bouton_delettrer)
        self.listview.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnDblClic)

    def __do_layout(self):
        gridsizer_base = wx.FlexGridSizer(rows=6, cols=1, vgap=0, hgap=0)

        gridsizer_base.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)
        gridsizer_base.Add(self.listview, 5, wx.LEFT | wx.RIGHT | wx.EXPAND, 0)
        gridsizer_base.Add(self.ctrl_outils, 1, wx.EXPAND, 0)
        gridsizer_base.Add((5, 5), 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 0)

        # Boutons
        gridsizer_boutons = wx.FlexGridSizer(rows=1, cols=6, vgap=0, hgap=0)
        gridsizer_boutons.Add((20, 20), 1, wx.ALIGN_BOTTOM, 0)
        gridsizer_boutons.Add(self.bouton_lettrer, 1, wx.EXPAND, 0)
        gridsizer_boutons.Add(self.bouton_delettrer, 1, wx.EXPAND, 0)
        gridsizer_boutons.Add((20, 20), 1, wx.ALIGN_BOTTOM, 0)
        gridsizer_boutons.Add(self.bouton_fermer, 1, wx.EXPAND, 0)
        gridsizer_boutons.Add(self.bouton_ok, 1, wx.EXPAND, 0)
        gridsizer_boutons.AddGrowableCol(0)
        gridsizer_base.Add(gridsizer_boutons, 1, wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        gridsizer_base.AddGrowableRow(1)
        gridsizer_base.AddGrowableCol(0)
        self.SetSizer(gridsizer_base)
        self.CenterOnScreen()

    def InitModel(self):
        # calcul du lettrage et composition des tracks
        lettre = "a"
        # réinit lettrage à partir de lstLettres
        self.dicEquiLet = {}
        self.dicLettres = {}
        for ID1,ID2, solde in self.lstLettres:
            let3 = None
            try:
                let1 = self.dicLettres[(+1,ID1)]
            except: let1=None
            try:
                let2 = self.dicLettres[(-1,ID2)]
            except: let2=None
            if let1 and let2:
                #lignes déjà lettrées
                if let1 != let2:
                    # fusionne let1 dans let2
                    for sens in (+1,-1):
                        for key,item in self.dicLettres.items():
                            if key == (sens,ID1) or key == (sens,ID2):
                                if item == let2 : item = let1
            # on étend la lettre déjà présente
            elif let1: self.dicLettres[(-1,ID2)] = let1
            elif let2: self.dicLettres[(+1,ID1)] = let2
            # pose la lettre dans les deux lignes, car non encore lettrées
            else:
                self.dicLettres[(+1,ID1)] = lettre
                self.dicLettres[(-1,ID2)] = lettre
                let3 = lettre
                lettre = LettreSuivante(lettre)
            for let9 in (let1,let2,let3):
                if let9 and (let9 not in self.dicEquiLet):
                    self.dicEquiLet[let9] = 0.0

        # calcul de l'équilibre
        for donnee in self.lstDonnees:
            if (donnee[0],donnee[1]) in self.dicLettres:
                let = self.dicLettres[(donnee[0],donnee[1])]
                for ix in (0,-1,-2):
                    if not donnee[ix]: donnee[ix]=0
                self.dicEquiLet[let] += donnee[0]*(donnee[-1]+donnee[-2])
        # application de la lettre dans les données et vérif de l'équilibre pour la mettre en majuscules
        for donnee in self.lstDonnees:
            key = (donnee[0],donnee[1])
            if key in self.dicLettres:
                let = self.dicLettres[key]
                if abs(self.dicEquiLet[let]) < 0.5:
                    let = let.upper()
                donnee[-3] = let
            else: donnee[-3] = ""
        # constitution des données track pour l'OLV
        self.tracks = [Track(don,self.lstCodes) for don in self.lstDonnees]

    def InitObjectListView(self):
        # Couleur en alternance des lignes
        self.listview.oddRowsBackColor = "#F0FBED"
        self.listview.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.listview.useExpansionColumn = True

        # Image list
        self.imgVert = self.listview.AddNamedImages("vert", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ventilation_vert.png"), wx.BITMAP_TYPE_PNG))
        self.imgRouge = self.listview.AddNamedImages("rouge", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ventilation_rouge.png"), wx.BITMAP_TYPE_PNG))
        self.imgOrange = self.listview.AddNamedImages("orange", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ventilation_orange.png"), wx.BITMAP_TYPE_PNG))

        def GetImageVentilation(track):
            if track.let == "":
                return self.imgOrange
            elif track.let == track.let.upper() :
                return self.imgVert
            else:
                return self.imgRouge

        # Construction des colonnes de l'OLV
        lstColumns = []
        for ix in range(self.nbColonnes-2):
            if ix in (1,2):
                justif = 'right'
            else:
                justif = 'left'
            code = self.lstCodes[ix]
            #width = self.lstWidth[ix],maximumWidth=self.lstWidth[ix]
            if code == "let":
                lstColumns.append(ColumnDefn(self.lstLibels[ix], justif, width=self.lstWidth[ix], valueGetter=code,
                                             isEditable=False, isSpaceFilling=False,imageGetter=GetImageVentilation ))
            else:
                if self.lstWidth[ix] > 200:
                    filling = True
                else: filling = False
                lstColumns.append(ColumnDefn(self.lstLibels[ix], justif, width=self.lstWidth[ix], valueGetter=code,
                                         isEditable=False,isSpaceFilling=filling,))
        lstColumns.append(ColumnDefn("coche", "left", 0, 0))
        lstColumns.append(ColumnDefn(self.lstLibels[-2],'right',maximumWidth=80,valueGetter="debits",stringConverter=FormateMontant,
                                     isEditable=False,isSpaceFilling=True))
        lstColumns.append(ColumnDefn(self.lstLibels[-1],'right',maximumWidth=80,valueGetter="credits",stringConverter=FormateMontant,
                                     isEditable=False,isSpaceFilling=True))
        self.listview.SetColumns(lstColumns)
        self.listview.SetSortColumn(self.columnSort)
        self.listview.CreateCheckStateColumn(self.nbColonnes-2)
        self.listview.SetObjects(self.tracks)
        self.listview.CocheListeRien()

    def MAJ(self):
        self.InitModel()
        self.InitObjectListView()
        self.Layout()

    def OnDblClic(self, event):
        state = self.listview.GetCheckState(self.listview.GetSelectedObject())
        if state:
            state = False
        else:
            state = True
        self.listview.SetCheckState(self.listview.GetSelectedObject(), state)
        self.listview.Refresh()

    def ClearLetters(self,choix):
        # récup des ID à lettrer, puis suppression des items
        lstID1 = []
        lstID2 = []
        for ligne in choix:
            if ligne.dc == +1: lstID1.append(ligne.id)
            else: lstID2.append(ligne.id)
            ligne.let = ''
        # constitution de la liste des suppressions dans lstLettres
        lstSupprimer = []
        for ID1,ID2, solde in self.lstLettres:
            if ID1 in lstID1 or ID2 in lstID2:
                lstSupprimer.append((ID1,ID2, solde))
        # suppression des anciennes lettres
        for item in lstSupprimer:
            self.lstLettres.remove(item)
        return lstID1,lstID2

    def OnClicLettrer(self, event):
        choix = self.listview.GetSelectedObjects()
        if len(choix) == 0:
            event.Skip()
            return

        # on ne relettre pas les lettres majuscules qui sont équilibrées
        lettrer = [x for x in choix if x.let.lower() == x.let]
        if len(lettrer) == 0:
            wx.MessageBox("Pas de lettre modifiable !\n\nIl faut cocher des lettres en minuscule ou sans lettre pour pouvoir lettrer")
            event.Skip()
            return

        # test si les règlements sont supérieurs au dûs, à confirmer
        deb = 0.0
        cre = 0.0
        for track in choix:
            deb += Nz(track.debits)
            cre += Nz(track.credits)
        if deb + cre < 0.01:
            mess = "Vous lettrez plus de règlements que la somme due, est-ce bien ce que vous voulez?"
            ret = wx.MessageBox(mess, "Confirmez une anomalie", wx.YES_NO, self)
            if ret != wx.YES:
                event.Skip()
                return

        lstID1,lstID2 = self.ClearLetters(choix)
        # ajout de nouveaux lettrages produit cartésien des lignes cochées
        if lstID1 == [] : lstID1=[None]
        if lstID2 == [] : lstID2=[None]
        for ID1 in lstID1:
            for ID2 in lstID2:
                self.lstLettres.append((ID1,ID2, self.txtIDuser))
        event.Skip()
        self.MAJ()

    def OnClicDelettrer(self, event):
        choix = self.listview.GetSelectedObjects()
        if len(choix) == 0:
            event.Skip()
            return

        delettrer = [x for x in choix if (x.let.lower() == x.let) and (x.let != '')]
        if len(delettrer) == 0:
            wx.MessageBox("Pas de lettre modifiable !\n\nIl faut cocher des lettres en minuscule pour pouvoir delettrer")
        lstID1,listID2 = self.ClearLetters(choix)
        event.Skip()
        self.MAJ()

    def OnClicFermer(self, event):
        self.EndModal(wx.ID_CANCEL)

    def OnClicOk(self, event):
        self.EndModal(wx.ID_OK)

    def GetLettrage(self):
        return self.lstLettres

class DialogCoches(wx.Dialog):
    def __init__(self, parent, listeOriginale=[("Choix1","Texte1"),("Choix2","Texte2"),],columnSort=1,
                 LargeurCode=80,LargeurLib=100,minSize=(200, 150),size=(350, 350), titre="Faites un choix !",
                 checked=False,intro="Double Clic sur la ou les réponses souhaitées..."):
        wx.Dialog.__init__(self, parent, -1,size=size,style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)

        self.SetTitle("CTRL_ChoixListe.DialogCoches")
        self.columnSort = columnSort
        self.choix= None
        self.parent = parent
        self.minSize = minSize
        self.wCode = LargeurCode
        self.wLib = LargeurLib
        self.liste = []
        self.nbColonnes=0
        for item in listeOriginale :
            if isinstance(item,(list,tuple)):
                self.nbColonnes = len(item)
            else:
                self.nbColonnes = 1
                item = (str(item),)
            self.liste.append(item)

        # Bandeau
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro,  hauteurHtml=15, nomImage=Chemins.GetStaticPath("Images/22x22/Smiley_nul.png"))
        # conteneur des données
        self.listview = FastObjectListView(self)
        # Boutons
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte="Valider", cheminImage="Images/32x32/Valider.png")
        self.bouton_fermer = CTRL_Bouton_image.CTRL(self, texte="Annuler", cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()
        # Binds
        self.Bind(wx.EVT_BUTTON, self.OnClicOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnClicFermer, self.bouton_fermer)
        self.listview.Bind(wx.EVT_LIST_ITEM_ACTIVATED,self.OnDblClic)
        if checked:
            for obj in self.listview.innerList:
                self.listview.SetCheckState(obj,True)
        self.checked = checked

    def __set_properties(self):
        self.SetMinSize(self.minSize)
        self.bouton_fermer.SetToolTip("Cliquez ici pour fermer")
        self.listview.SetToolTip("Double Cliquez pour choisir")
        # Couleur en alternance des lignes
        self.listview.oddRowsBackColor = "#F0FBED"
        self.listview.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.listview.useExpansionColumn = True

        if self.nbColonnes >1:
            filCode = False
        else: filCode = True
        lstColumns = [
            ColumnDefn("Code", "left", 0, 0),
            ColumnDefn("Code", "left", self.wCode, 0,isSpaceFilling=filCode),]
        if self.nbColonnes >1:
            texte = "Libelle (non modifiables)"
            for ix in range(1,self.nbColonnes):
                lstColumns.append(ColumnDefn(texte, "left", self.wLib, ix, isSpaceFilling=True))
                texte = "-"

        self.listview.SetColumns(lstColumns)
        self.listview.SetSortColumn(self.columnSort)
        self.listview.CreateCheckStateColumn(0)
        self.listview.SetObjects(self.liste)

    def __do_layout(self):
        gridsizer_base = wx.FlexGridSizer(rows=6, cols=1, vgap=0, hgap=0)

        gridsizer_base.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)
        gridsizer_base.Add(self.listview, 5, wx.LEFT|wx.RIGHT|wx.EXPAND, 0)
        gridsizer_base.Add((5, 5), 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 0)

        # Boutons
        gridsizer_boutons = wx.FlexGridSizer(rows=1, cols=3, vgap=0, hgap=0)
        gridsizer_boutons.Add((20, 20), 1, wx.ALIGN_BOTTOM, 0)
        gridsizer_boutons.Add(self.bouton_ok, 1, wx.EXPAND, 0)
        gridsizer_boutons.Add(self.bouton_fermer, 1, wx.EXPAND, 0)
        gridsizer_boutons.AddGrowableCol(0)
        gridsizer_base.Add(gridsizer_boutons, 1, wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        self.SetSizer(gridsizer_base)
        gridsizer_base.AddGrowableRow(1)
        gridsizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen() 


    def OnClicFermer(self, event):
        self.choix = []
        self.EndModal(wx.ID_CANCEL)

    def OnClicOk(self, event):
        self.choix = self.listview.GetCheckedObjects()
        if len(self.choix) == 0 and not self.checked:
            dlg = wx.MessageDialog(self, "Pas de sélection faite !\nIl faut choisir ou cliquer sur annuler", "Accord Impossible", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            if self.nbColonnes == 1:
                self.choix = [x[0] for x in self.choix]
            self.EndModal(wx.ID_OK)

    def OnDblClic(self, event):
        state = self.listview.GetCheckState(self.listview.GetSelectedObject())
        if state :
            state = False
        else : state = True
        self.listview.SetCheckState(self.listview.GetSelectedObject(),state)
        self.listview.Refresh()

class Dialog(wx.Dialog):
    def __init__(self, parent, listeOriginale=[("Choix1","Texte1"),],LargeurCode=150,LargeurLib=100,colSort=0, minSize=(600, 350),
                 titre="Faites un choix !", intro="Double Clic sur la réponse souhaitée..."):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.SetTitle("CTRL_ChoixListe")
        self.choix= None
        self.colSort = colSort
        self.parent = parent
        self.minSize = minSize
        self.wCode = LargeurCode
        self.wLib = LargeurLib
        self.liste = []
        ix = 1
        for item in listeOriginale :
            if len(item) == 1:
                self.liste.append((ix,item[0]))
            else:
                self.liste.append(item)
            ix += 1

        # Bandeau
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro,  hauteurHtml=15, nomImage="Images/22x22/Smiley_nul.png")
        # conteneur des données
        self.listview = FastObjectListView(self)
        # Boutons
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte="Valider", cheminImage="Images/32x32/Valider.png")
        self.bouton_fermer = CTRL_Bouton_image.CTRL(self, texte="Annuler", cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()
        # Binds
        self.Bind(wx.EVT_BUTTON, self.OnDblClicOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnDblClicFermer, self.bouton_fermer)
        self.listview.Bind(wx.EVT_LIST_ITEM_ACTIVATED,self.OnDblClic)
        self.listview.Bind(wx.EVT_KEY_DOWN,self.OnDelete)

    def __set_properties(self):
        self.SetMinSize(self.minSize)
        self.bouton_fermer.SetToolTip("Cliquez ici pour fermer")
        self.listview.SetToolTip("Double Cliquez pour choisir")
        # Couleur en alternance des lignes
        self.listview.oddRowsBackColor = "#F0FBED"
        self.listview.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.listview.useExpansionColumn = True
        self.listview.SetColumns([
            ColumnDefn("Code", "left", self.wCode,  0),
            ColumnDefn("Description - libellé ", "left", self.wLib, 1,isSpaceFilling = True),
            ])
        self.listview.SetSortColumn(self.listview.columns[self.colSort])
        self.listview.SetObjects(self.liste)

    def __do_layout(self):
        gridsizer_base = wx.FlexGridSizer(rows=6, cols=1, vgap=0, hgap=0)

        gridsizer_base.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)
        gridsizer_base.Add(self.listview, 5, wx.LEFT|wx.RIGHT|wx.EXPAND, 0)
        gridsizer_base.Add((5, 5), 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 0)

        # Boutons
        gridsizer_boutons = wx.FlexGridSizer(rows=1, cols=3, vgap=0, hgap=0)
        gridsizer_boutons.Add((20, 20), 1, wx.ALIGN_BOTTOM, 0)
        gridsizer_boutons.Add(self.bouton_ok, 1, wx.EXPAND, 0)
        gridsizer_boutons.Add(self.bouton_fermer, 1, wx.EXPAND, 0)
        gridsizer_boutons.AddGrowableCol(0)
        gridsizer_base.Add(gridsizer_boutons, 1, wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        self.SetSizer(gridsizer_base)
        gridsizer_base.Fit(self)
        gridsizer_base.AddGrowableRow(1)
        gridsizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen() 

    def OnDblClicFermer(self, event):
        self.EndModal(wx.ID_CANCEL)

    def OnDblClicOk(self, event):
        self.choix = self.listview.GetSelectedObject()
        if self.choix == None:
            dlg = wx.MessageDialog(self, "Pas de sélection faite !\nIl faut choisir une ligne ou cliquer sur annuler",
                                   "Accord Impossible", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            self.EndModal(wx.ID_OK)

    def OnDblClic(self, event):
        self.choix = self.listview.GetSelectedObject()
        self.EndModal(wx.ID_OK)

    def OnDelete(self,event):
        if event.KeyCode in (wx.WXK_NUMPAD_DELETE,wx.WXK_DELETE):
            if not hasattr(self.parent,"OnDeleteChoixListe"):
                wx.MessageBox("Suppression sans effet","Non prévu")
            else:
                selection = self.GetChoix()
                if selection == None:
                    dlg = wx.MessageDialog(self,
                                           "Pas de sélection faite !\nIl faut choisir une ligne ou cliquer sur annuler",
                                           "Accord Impossible",
                                           wx.OK | wx.ICON_EXCLAMATION)
                    dlg.ShowModal()
                    dlg.Destroy()
                else:
                    dlg = wx.MessageDialog(self,
                                           "Suppression demandée !\n\nConfirmez vous la suppression de la ligne sélectionnée?",
                                           "Accord nécessaire",
                                           wx.YES_NO | wx.ICON_EXCLAMATION)
                    ret = dlg.ShowModal()
                    dlg.Destroy()
                    if ret == wx.ID_YES:
                        # action de suppression gérée par le parent, puis rafraichissement
                        if self.parent.OnDeleteChoixListe(selection):
                            self.liste.remove(selection)
                            self.listview.SetObjects(self.liste)
                            self.listview.RepopulateList()
        event.Skip()

    def GetChoix(self):
        self.choix = self.listview.GetSelectedObject()
        return self.choix

if __name__ == "__main__":
    app = wx.App(0)
    dlg = DLGventilations(None,
                          {12456:{"designations":["pièce réglée 1",datetime.date.today()],
                                  "montant":15.25,
                                  },
                          12457:{"designations":["pièce récente 2",datetime.date.today()],
                                  "montant":37,
                                  }},
                          {6545:{"designations":["règlement 1",datetime.date.today()],
                                 "montant":15.25,
                                 },
                          6546:{"designations":["règlement 2",datetime.date.today()],
                                    "montant":30,
                            },},
                          [(12456,6545,15.25),
                           (12457,6546,7)],
                          ["libellé1", "Date"])
    """
    """
    dlg = Dialog(None)
    app.SetTopWindow(dlg)
    print(dlg.ShowModal())
    #print dlg.GetChoix()
    app.MainLoop()

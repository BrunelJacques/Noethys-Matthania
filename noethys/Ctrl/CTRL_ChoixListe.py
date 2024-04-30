#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur :           Ivan LUCAS, JB, Jacques Brunel
# Licence :         Licence GNU GPL
# Permet un choix dans une liste et retourne l'indice
# ------------------------------------------------------------------------

import wx
import Chemins
import GestionDB
import datetime
import FonctionsPerso as fp
from Ctrl import CTRL_Bouton_image
from Utils import UTILS_Config
import decimal
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, CTRL_Outils, PanelAvecFooter
from Ctrl import CTRL_Bandeau

SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")

def Nz(valeur):
    if not valeur:
        valeur = 0
    return valeur

def FmtNombre(montant, zero = True):
    if montant == None:
        return ""
    elif not isinstance(montant, (int, float, bool, decimal.Decimal)):
        return montant
    if zero:
        if isinstance(montant, (int, bool)): return "%d.00" % montant
        return '{:.2f}'.format(montant)
    else:
        if int(montant * 100) == 0:
            return ""
        return '{:.2f}'.format(montant)

def FormateMontant(montant):
    return FmtNombre(montant,zero=False)

def FormateCumul(montant):
    return FmtNombre(montant,zero=True)

def GetColonnesVentil():
    lstColumns = [
        ColumnDefn("Nature",'left',60,'nature',typeDonnee='texte', isSpaceFilling=False),
        ColumnDefn("Date", 'left', 80, 'date',typeDonnee='texte',isSpaceFilling=False),
        ColumnDefn("ID", 'left', 60, "ID", typeDonnee="entier", isSpaceFilling=False),
        ColumnDefn("Libellé",'left',240,'label',typeDonnee='texte',isSpaceFilling=True),
        ColumnDefn("Montant", 'right', 80, 'montant_aff', typeDonnee='montant',
                   isSpaceFilling=False, stringConverter=FormateMontant),
        ColumnDefn("A ventiler", 'right', 80, 'mttVentiler_aff', typeDonnee='montant',
                   isSpaceFilling=False, stringConverter=FormateMontant),
        ColumnDefn("Let", 'right', 60, 'lettreID', typeDonnee='texte',
                   isSpaceFilling=False),
        ColumnDefn("Lettrage", 'left', 240, 'lettres', typeDonnee='texte',
                   isSpaceFilling=True),
        ColumnDefn("Solde Progressif", 'right', 80, 'solde', typeDonnee='montant',
                   isSpaceFilling=False, stringConverter=FormateCumul),
    ]
    return lstColumns

def AlphaSeuls(txt):
    new = ""
    for car in txt:
        if (car >= "a") and (car <= "z"):
            new += car
        if (car >= "A") and (car <= "Z"):
            new += car
    return new

def LettreSuivante(lettre=''):
    # plusieurs caractères possibles, chiffres ou lettres de casses différentes
    if not isinstance(lettre, str): lettre = 'A'
    lettre = lettre.strip()
    if lettre == '': lettre = '@'
    # incrémentation d'un lettrage dans la même casse
    lastcar = lettre[-1]
    precars = lettre[:-1]
    dicPlage = {"9":"1", "Z":"A", "z":"a"}
    if lastcar in ("9","Z","z"):
        # limite atteinte: lastcar recule en début de plage et incrementation precars
        if len(precars) > 0 and (precars[-1] <= lastcar) and (precars[-1] >= dicPlage[lastcar]):
            # le caractère précédent est de même casse, on l'incrémente
            precars = LettreSuivante(precars)
        else:
            # le préfixe étant absent ou de casse différente, on insère un nouveau caractère
            precars += dicPlage[lastcar]
        # rétrogradation de lastcar pour les chiffres il faut '10' et non ('11' ou '00')
        if lastcar == "9":
            new = precars + "0"
        else:
            new = precars + dicPlage[lastcar]

    else:
        # incrémentation simple dans la casse
        new = precars + chr(ord(lastcar) + 1)
    if len(lettre) >2:
        print(lettre,new)
    return new

def LettresMax(lstLignes, pos):
    lstLettres = [x[pos] for x in lstLignes if x[pos]]
    lstNombres = [0,]
    lstAlpha = [" ",]
    for lettre in lstLettres:
        if "_" in lettre:
            # le séparateur "_" trahit la présence d'un ID null, on garde la partie left
            lettre = lettre.split("_")[0]
        chiffres = fp.ChiffresSeuls(lettre)
        if len(chiffres) > 0 :
            lstNombres.append(int(chiffres))
        alphas = AlphaSeuls(lettre)
        if len(alphas) > 0:
            lstAlpha.append(alphas)
    lstNombres.sort()
    lstAlpha.sort()
    return str(lstNombres[-1]), lstAlpha[-1]

def rowFormatter(listItem, track):
    if track.nature == 'P':
        listItem.SetBackgroundColour(wx.Colour(255, 205, 210))
    elif track.nature == 'R':
        listItem.SetBackgroundColour(wx.Colour(220, 237, 200))
    if track.montant < 0:
        listItem.SetTextColour(wx.BLUE)

class Track(object):
    # Reçoit un dic donnees  et une liste champs, retrourne une track
    def __init__(self, donnees, champs):
        for ix in range(len(champs)):
            champ = champs[ix]
            if isinstance(donnees, (list,tuple)):
                valeur = donnees[ix]
            else:
                valeur = donnees[champ]
            setattr(self, champ, valeur)

class CTRL_Solde(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, name='panel_solde', style=wx.SUNKEN_BORDER | wx.TAB_TRAVERSAL,
                          size=(100, 30))
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
        self.ctrl_solde.SetToolTip("Afichage du solde calculé")

    def SetValue(self, montant):
        """ MAJ intégrale du controle avec MAJ des donnees """
        if montant > 0.0:
            label = "+ %.2f " % montant
            self.SetBackgroundColour(wx.Colour(220, 237, 200))  # vert
        elif montant == 0.0:
            label = "0.00 "
            self.SetBackgroundColour("#5DF020")  # Vert
        else:
            label = "- %.2f " % (-montant,)
            self.SetBackgroundColour(wx.Colour(255, 205, 210))  # Rouge
        self.ctrl_solde.SetLabel(label)
        self.Layout()
        self.Refresh()

# ----------------------------------------------------------------------------------------

class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        kwds[
            'style'] = wx.LC_REPORT | wx.SUNKEN_BORDER | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES
        FastObjectListView.__init__(self, *args, **kwds)
        self.rowFormatter = rowFormatter
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        menuPop = wx.Menu()

        if hasattr(self.GrandParent.ctrl_outils,'bouton_cocher'):
            # Item Tout cocher
            item = wx.MenuItem(menuPop, 70, "Tout cocher")
            item.SetBitmap(
                wx.Bitmap("Static/Images/16x16/Cocher.png", wx.BITMAP_TYPE_PNG))
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.CocheListeTout, id=70)

            # Item Tout décocher
            item = wx.MenuItem(menuPop, 80, "Tout décocher")
            item.SetBitmap(
                wx.Bitmap("Static/Images/16x16/Decocher.png", wx.BITMAP_TYPE_PNG))
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.CocheListeRien, id=80)

            menuPop.AppendSeparator()

        # Item Apercu avant impression
        item = wx.MenuItem(menuPop, 40, "Aperçu avant impression")
        bmp = wx.Bitmap("Static/Images/16x16/Apercu.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=40)

        # Item Imprimer
        item = wx.MenuItem(menuPop, 50, "Imprimer")
        bmp = wx.Bitmap("Static/Images/16x16/Imprimante.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=50)

        menuPop.AppendSeparator()

        # Item Export Texte
        item = wx.MenuItem(menuPop, 600, "Exporter au format Texte")
        bmp = wx.Bitmap("Static/Images/16x16/Texte2.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.ExportTexte, id=600)

        # Item Export Excel
        item = wx.MenuItem(menuPop, 700, "Exporter au format Excel")
        bmp = wx.Bitmap("Static/Images/16x16/Excel.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.ExportExcel, id=700)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Selection(self):
        return self.GetSelectedObjects()

    def Apercu(self, event=None):
        from Utils import UTILS_Printer
        txtIntro, txtTotal = self.GetTextesImpression()
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre="Liste des factures", intro=txtIntro, total=txtTotal, format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event=None):
        from Utils import UTILS_Printer
        txtIntro, txtTotal = self.GetTextesImpression()
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre="Liste des factures", intro=txtIntro, total=txtTotal, format="A", orientation=wx.PORTRAIT)
        prt.Print()

    def ExportTexte(self, event=None):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(self, titre="Liste des factures")

    def ExportExcel(self, event=None):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre="Liste des factures")

class ListviewAvecFooter(PanelAvecFooter):
    def __init__(self, parent, dictFooter={}, kwargs={}):
        PanelAvecFooter.__init__(self, parent, ListView, kwargs, dictFooter)

# ---------------------------------------------------------------------------------------------------------------------

class DLGventilations(wx.Dialog):
    # Gestion d'un lettrage à partir de deux dictionnaires d'écritures, ventilations, liste des champs de désignations
    # La clé des dictionnaires est l'ID  (origine fichier), ensuite deux clés 'designations, montant.
    # les tuples de ventilations sont IDdebit, IDcredit, montant
    # la liste champs de désignation est les labels correspondants aux valeurs désignations des dictionnaires

    def __init__(self, parent, ddDebits=None, ddCredits=None, ltVentilations=(), **kwds):

        parentName = parent.__class__.__name__
        self.parent = parent
        intro = kwds.pop('intro',
                         "Cochez les lignes associées puis cliquez sur lettrage ou délettrage...")
        titre_bandeau = kwds.pop('titre', "Lettrage par les montants ventilés")
        titre_frame = kwds.pop('titre_frame',
                               "%s / CTRL_ChoixListe.DLGventilations" % parentName)
        dfooter = {'montant_aff': {'mode': 'total'},'mttVentiler_aff': {'mode': 'total'}}
        dictFooter = kwds.pop('dictFooter', dfooter)
        autoLayout = kwds.pop('autoLayout', True)
        self.columnSort = kwds.pop('columnSort', 1)
        minSize = kwds.pop('minSize', (600, 350))

        kwdlg = {}
        kwdlg['size'] = kwds.pop('size', (1000, 700))
        kwdlg['pos'] = kwds.pop('pos', (300, 50))
        style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX
        kwdlg['style'] = kwds.pop('style', style)
        wx.Dialog.__init__(self, None, -1, **kwdlg)

        self.SetMinSize(minSize)
        self.SetTitle(titre_frame)
        self.filtreLet = None
        self.ltVentilationsOriginal = [x for x in ltVentilations]
        self.llVentilations = [[w,x,round(y,2),z] for (w,x,y,z) in ltVentilations]
        self.ddDonnees, self.ldDonnees = self.InitLignes(ddDebits, ddCredits)
        # Construction des colonnes de l'OLV
        self.lstColumns = GetColonnesVentil()
        self.lstCodes = [x.valueGetter for x in self.lstColumns]
        self.lstCodes += ['montant', 'mttVentiler', 'sens', 'signeMtt']

        # conteneur des données OLV
        self.pnlListview = ListviewAvecFooter(self, dictFooter=dictFooter, kwargs=kwds)
        self.listview = self.pnlListview.GetListview()
        self.ctrl_outils = CTRL_Outils(self, listview=self.listview, afficherCocher=True)
        self.SetCouleurImages()

        # Bandeau
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre_bandeau, texte=intro,
                                                 hauteurHtml=15,
                                                 nomImage=Chemins.GetStaticPath(
                                                     "Images/22x22/Smiley_nul.png"))

        # Pied de l'écran
        self.ctrl_labelMttVentil = wx.StaticText(self, -1, "àVentiler coché : ")
        self.ctrl_mttVentil = CTRL_Solde(self)

        self.ctrl_labelMontant = wx.StaticText(self, -1,    "Montant coché : ")
        self.ctrl_montant = CTRL_Solde(self)

        self.ctrl_labelFiltreLet = wx.StaticText(self, -1, "Filtrer lettre: ")
        self.ctrl_filtreLet = wx.TextCtrl(self, -1, style=wx.TE_PROCESS_ENTER,
                                          size=(40, 25))

        self.check_avecLettrees = wx.CheckBox(self, -1,
                                              " Masquer les \n lignes ventilées")
        self.bouton_lettrer = CTRL_Bouton_image.CTRL(self, texte="Lettrer",
                                                     cheminImage="Images/32x32/Configuration2.png")
        self.bouton_delettrer = CTRL_Bouton_image.CTRL(self, texte="DeLettrer",
                                                       cheminImage="Images/32x32/Depannage.png")
        self.bouton_fermer = CTRL_Bouton_image.CTRL(self, texte="Annuler",
                                                    cheminImage="Images/32x32/Annuler.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte="Valider",
                                                cheminImage="Images/32x32/Valider.png")
        self.__set_properties()
        self.InitObjectListView()
        if autoLayout:
            self.MAJ()
            self.__do_layout()

    def __set_properties(self):
        # TipString, Bind et constitution des colonnes de l'OLV
        self.ctrl_mttVentil.SetToolTip(
            "Pour aider la recherche, ici la somme des mttVentils à lettrer")
        self.ctrl_montant.SetToolTip(
            "Pour aider la recherche, ici la somme des montants à lettrer")
        self.ctrl_filtreLet.SetToolTip(
            "En saisisant une lettre seules les lignes associées seront filtrées")
        self.check_avecLettrees.SetToolTip(
            "Cliquez ici après avoir coché des lignes à associer")
        self.bouton_lettrer.SetToolTip(
            "Cliquez ici après avoir coché des lignes à associer")
        self.bouton_delettrer.SetToolTip(
            "Cliquez ici après avoir sélectionné une ligne de la lettre à supprimer")
        self.bouton_ok.SetToolTip(
            "Cliquez ici pour valider et enregistrer les modifications")
        self.bouton_fermer.SetToolTip("Cliquez ici pour abandonner les modifications")
        self.listview.SetToolTip("Double Cliquez pour cocher")
        # Binds
        self.Bind(wx.EVT_BUTTON, self.OnClicOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnClicFermer, self.bouton_fermer)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnMAJ, self.ctrl_filtreLet)
        self.Bind(wx.EVT_CHECKBOX, self.OnMAJ, self.check_avecLettrees)
        self.Bind(wx.EVT_BUTTON, self.OnClicLettrer, self.bouton_lettrer)
        self.Bind(wx.EVT_BUTTON, self.OnClicDelettrer, self.bouton_delettrer)
        self.listview.Bind(wx.EVT_COMMAND_LEFT_CLICK, self.OnCalculLettres)
        self.ctrl_outils.bouton_cocher.Bind(wx.EVT_ERASE_BACKGROUND, self.OnCalculLettres)

    def __do_layout(self):
        gridsizer_base = wx.FlexGridSizer(rows=6, cols=1, vgap=0, hgap=0)

        gridsizer_base.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)
        gridsizer_base.Add(self.pnlListview, 5, wx.LEFT | wx.RIGHT | wx.EXPAND, 0)
        gridsizer_outils = wx.FlexGridSizer(rows=1, cols=4, vgap=0, hgap=0)
        gridsizer_outils.Add(self.ctrl_labelMttVentil, 0, wx.ALL, 5)
        gridsizer_outils.Add(self.ctrl_mttVentil, 1, wx.ALIGN_CENTER, 0)
        gridsizer_outils.Add((85,10), 1, wx.EXPAND,0)
        gridsizer_outils.Add(self.ctrl_outils, 1, wx.RIGHT|wx.EXPAND, 15)
        gridsizer_outils.AddGrowableCol(3)
        gridsizer_base.Add(gridsizer_outils, 1, wx.EXPAND, 0)
        gridsizer_base.Add((5, 5), 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 0)

        # Bas d'écran
        gridsizer_boutons = wx.FlexGridSizer(rows=1, cols=11, vgap=0, hgap=0)
        gridsizer_boutons.Add(self.ctrl_labelMontant, 0, wx.ALL, 5)
        gridsizer_boutons.Add(self.ctrl_montant, 1, wx.ALIGN_CENTER, 0)
        gridsizer_boutons.Add((85, 20), 1, wx.ALIGN_BOTTOM, 0)
        gridsizer_boutons.Add(self.ctrl_labelFiltreLet, 0, wx.ALL, 5)
        gridsizer_boutons.Add(self.ctrl_filtreLet, 1, wx.ALIGN_CENTER | wx.RIGHT, 25)
        gridsizer_boutons.Add(self.check_avecLettrees, 1, wx.EXPAND, 0)
        gridsizer_boutons.Add(self.bouton_lettrer, 1, wx.EXPAND, 0)
        gridsizer_boutons.Add(self.bouton_delettrer, 1, wx.EXPAND, 0)
        gridsizer_boutons.Add((20, 20), 1, wx.ALIGN_BOTTOM, 0)
        gridsizer_boutons.Add(self.bouton_fermer, 1, wx.EXPAND, 0)
        gridsizer_boutons.Add(self.bouton_ok, 1, wx.EXPAND, 0)
        gridsizer_boutons.AddGrowableCol(3)
        gridsizer_base.Add(gridsizer_boutons, 1, wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        gridsizer_base.AddGrowableRow(1)
        gridsizer_base.AddGrowableCol(0)
        self.SetSizer(gridsizer_base, )
        self.Layout()

    def SetLettresID(self,ldDonnees):
        # affecte une lettre aux lignes sans lettreID
        maxLetNum, maxLetAlpha = LettresMax(self.llVentilations, 3)
        letNumSuivante = LettreSuivante(maxLetNum)
        letAlphaSuivante = LettreSuivante(maxLetAlpha)
        for dDonnees in ldDonnees:
            if dDonnees['lettreID']:
                continue
            if dDonnees['nature'] == 'P':
                dDonnees['lettreID'] = letNumSuivante
                letNumSuivante = LettreSuivante(letNumSuivante)
            else:
                dDonnees['lettreID'] = letAlphaSuivante
                letAlphaSuivante = LettreSuivante(letAlphaSuivante)

    def InitLignes(self, ddDebits, ddCredits):
        # même contenu retourné en liste et en dic: lignes de l'OLV
        ldDonnees = []
        ddDonnees = {}

        # compose ddDonnees et ldDonnees ajoute des champs calculés
        nature = 'P'  # prestations au débits
        sens = -1
        for ddLignes in (ddDebits, ddCredits):
            for ID, dic in ddLignes.items():
                # 'designations' et 'montant' doivent être présents dans ddDebits-Credits
                signeMtt = 1
                if dic['montant'] < 0:
                    signeMtt = -1
                key = (nature, ID)
                dic['nature'] = nature
                dic['ID'] = ID
                dic['sens'] = sens
                dic['signeMtt'] = signeMtt
                dic['montant'] = round(dic['montant'], 2)
                dic['montant_aff'] = round(dic['montant'], 2) * sens
                dic['key'] = key
                dic['label'] = dic['designations'][0]
                dic['date'] = dic['designations'][1]
                dic['mttVentiler'] = 0.0
                dic['mttVentiler_aff'] = 0.0
                dic['lettres'] = None
                dic['solde'] = None
                dic['lettreID'] = None
                ldDonnees.append(dic)
                ddDonnees[key] = dic
            # changement pour le deuxième passage (crédits = Règlements)
            nature = 'R'  # Règlements au crédit quelque soit leur signe
            sens = +1

        # purge des ventilations orphelines des lignes
        lstRemove = []
        for IDdeb, IDcre, mttVent, lettre in self.llVentilations:
            verif = 0
            if IDdeb == 0 or  ('P', IDdeb) in ddDonnees:
                verif = 1
            if IDcre == 0 or ('R', IDcre) in ddDonnees:
                verif += 1
            if verif == 2:
                continue
            lstRemove.append([IDdeb, IDcre, mttVent, lettre])

        for ventilation in lstRemove:
            self.llVentilations.remove(ventilation)

        # précharge les lettres à partir de ltVentil
        for ventilation in self.llVentilations:
            IDdeb, IDcre, mttVent, lettre = ventilation
            if not lettre or len(lettre.strip()) == 0:
                continue
            if "_" in lettre:
                # le séparateur "_" trahit la présence d'un ID null, on garde la partie left
                lettre = lettre.split("_")[0]
            key = ('P', IDdeb)
            if key in ddDonnees:
                if not ddDonnees[key]['lettreID']:
                    # une seule lettreID par ligne seule la première est retenue
                    lettreLigne = fp.ChiffresSeuls(lettre)
                    if len(lettreLigne) > 0:
                        ddDonnees[key]['lettreID'] = lettreLigne

            key = ('R', IDcre)
            if key in ddDonnees:
                if not ddDonnees[key]['lettreID']:
                    lettreLigne = AlphaSeuls(lettre)
                    if len(lettreLigne) > 0:
                        ddDonnees[key]['lettreID'] = lettreLigne

        # affecte une lettre aux lignes sans lettreID
        self.SetLettresID(ldDonnees)

        return ddDonnees, ldDonnees

    def InitModel(self):
        # transformation des lignes en track pour l'OLV
        self.tracks = []
        for don in self.ldDonnees:
            track = Track(don, self.lstCodes)
            track.montant_aff = round(track.montant * track.sens,2)
            track.mttVentiler_aff = round(track.mttVentiler * track.sens,2)
            self.tracks.append(track)
        self.listview.SetObjects(self.tracks)

        filtreLettre = {'typeDonnee': 'libre',
                        'criteres': "'%s' in (track.lettres + track.lettreID)" % self.ctrl_filtreLet.GetValue(),
                        'choix': "", 'code': "", 'titre': "", }
        if self.filtreLet:
            self.listview.listeFiltresColonnes.remove(self.filtreLet)
            self.filtreLet = None

        if len(self.ctrl_filtreLet.GetValue()) > 0:
            self.listview.listeFiltresColonnes.append(filtreLettre)
            self.filtreLet = filtreLettre

        equilibre = {'typeDonnee': 'libre',
                     'criteres': "int(track.mttVentiler) != 0",
                     'choix': "", 'code': "", 'titre': "", }
        if self.check_avecLettrees.GetValue():
            if not equilibre in self.listview.listeFiltresColonnes:
                self.listview.listeFiltresColonnes += [equilibre, ]
        elif equilibre in self.listview.listeFiltresColonnes:
            self.listview.listeFiltresColonnes.remove(equilibre)

    def InitObjectListView(self):
        # Couleur en alternance des lignes
        self.listview.oddRowsBackColor = "#F0FBED"
        self.listview.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.listview.useExpansionColumn = True
        #
        self.listview.SetColumns(self.lstColumns)
        self.listview.SetSortColumn(self.columnSort)
        self.listview.CreateCheckStateColumn(5)
        self.listview.CocheListeRien()

    def SetCumul(self):
        cumul = 0.0
        for track in self.listview.GetObjects():
            cumul += track.montant_aff
            track.solde = cumul

    def MAJ(self):
        self.ComposeLignes()
        self.InitModel()
        self.Layout()
        search = self.ctrl_outils.barreRecherche.GetValue()
        self.listview.Filtrer(search)
        self.OnCalculLettres(None)
        self.SetCumul()

    # retourne l'image colorisée, colonne Montant
    def GetCouleurMontant(self, track):
        if round(track.mttVentiler_aff, 2) == 0 and len(track.lettres) < 50:
            return self.imgVert
        elif abs(track.mttVentiler) > 1:
            return self.imgOrange
        else:
            return self.imgRouge

    # retourne l'image colorisée, colonne aVentiler
    def GetCouleurVentil(self, track):
        # si lettrage non vert
        if track.mttVentiler_aff == 0:
            return
        # teste la couleur
        if abs(track.mttVentiler_aff) > abs(track.montant_aff):
            return self.imgSupprimer
        elif (track.mttVentiler_aff * track.montant_aff) < 0:
            # signes différents
            return self.imgSupprimer
        elif track.mttVentiler == track.montant:
            return self.imgVertRond
        else:
            return self.imgOrangeRond

    # paramétrage des images à insérer
    def InitCouleurs(self):
        # Image list
        self.imgVert = self.listview.AddNamedImages("vert", wx.Bitmap(
            Chemins.GetStaticPath("Images/16x16/Ventilation_vert.png"),
            wx.BITMAP_TYPE_PNG))
        self.imgRouge = self.listview.AddNamedImages("rouge", wx.Bitmap(
            Chemins.GetStaticPath("Images/16x16/Ventilation_rouge.png"),
            wx.BITMAP_TYPE_PNG))
        self.imgOrange = self.listview.AddNamedImages("orange", wx.Bitmap(
            Chemins.GetStaticPath("Images/16x16/Ventilation_orange.png"),
            wx.BITMAP_TYPE_PNG))
        self.imgVertRond = self.listview.AddNamedImages("vert", wx.Bitmap(
            Chemins.GetStaticPath("Images/16x16/Euro_vert.png"), wx.BITMAP_TYPE_PNG))
        self.imgOrangeRond = self.listview.AddNamedImages("orange", wx.Bitmap(
            Chemins.GetStaticPath("Images/16x16/Euro_orange.png"), wx.BITMAP_TYPE_PNG))
        self.imgSupprimer = self.listview.AddNamedImages("supprimer", wx.Bitmap(
            Chemins.GetStaticPath("Images/16x16/Supprimer_2.png"), wx.BITMAP_TYPE_PNG))

    # pose les fonctions de colorisation dans les columnDefn
    def SetCouleurImages(self):
        # colorisation par image
        self.InitCouleurs()
        colonneMtt = self.lstColumns[self.lstCodes.index('montant_aff')]
        colonneMtt.imageGetter = self.GetCouleurMontant
        colonneVentil = self.lstColumns[self.lstCodes.index('mttVentiler_aff')]
        colonneVentil.imageGetter = self.GetCouleurVentil

    def CoherenceVentil(self):
        # vérifie les incohérences de ventilations de même nature
        for ix  in range(2) :
            lstVentils = []
            cumul = 0.0
            for ventil in self.llVentilations:
                IDdeb, IDcre, mttVent, lettre = ventil
                if ventil[ix] == 0:
                    cumul += mttVent
                    lstVentils.append(ventil)
            if round(cumul,2) == 0.0:
                continue
            # corrige les incohérences de ventilation
            for ventil in lstVentils:
                IDdeb, IDcre, mttVent, lettre = ventil
                if ventil[ix] * cumul < 0: # signes opposés
                    continue
                corr = min(abs(cumul),abs(mttVent))
                if cumul < 0 : corr = -corr
                cumul -= corr
                ventil[2] -= corr
                if cumul == 0.0:
                    break

    def ComposeLignes(self):
        self.CoherenceVentil()

        def fusionLettres(lettreA, lettreB):
            if lettreA == lettreB:
                return lettreA
            # cas des associations homonatures
            if lettreA:
                llet = lettreA.split("_")
                leftA = llet[0]
                rightA = ""
            if len(llet) >1:
                rightA  = "".join(llet[1:])
            llet = lettreB.split("_")
            leftB = llet[0]
            rightB = ""
            if len(llet) >1:
                rightB  = "".join(llet[1:])
            if rightB in rightA: rightB = ""
            if rightA in rightB: rightA = ""
            if leftA == leftB:
                return leftA + "_" + rightA + rightB
            elif rightA == rightB:
                return leftA + leftB + "_" + rightA
            return leftA + leftB + "_" + rightA + rightB

        # MAJ des lignes selon ltVentilations changeant
        for dDonnees in self.ldDonnees:
            key = dDonnees['key']
            dDonnees['mttVentiler'] = dDonnees['montant']
            dDonnees['lettres'] = ""

            # regroupement des ventilations éclatées
            dVentil = {}
            llSupprime = []
            for ventil in self.llVentilations:
                IDdeb, IDcre, mttVent, lettre = ventil
                if not (IDdeb, IDcre) in dVentil:
                    dVentil[(IDdeb, IDcre)] = ventil
                else:
                    # cumule la ventilation avec la précédente pour le même couple
                    ix = self.llVentilations.index(dVentil[(IDdeb, IDcre)])
                    self.llVentilations[ix][2] += mttVent
                    if self.llVentilations[ix][3]:
                        self.llVentilations[ix][3] = fusionLettres(self.llVentilations[ix][3],lettre)
                    llSupprime.append(ventil)
            for ventil in llSupprime:
                self.llVentilations.remove(ventil)

            # déroulé pour prise en compte des ventilations
            for IDdeb, IDcre, mttVent, lettre in self.llVentilations:
                sens = dDonnees['sens']
                keyDeb = ('P', IDdeb)
                keyCre = ('R', IDcre)
                if not key in (keyDeb, keyCre):
                    # La ventilation ne concerne pas cette ligne
                    continue
                # prise en compte du montant ventilé
                dDonnees['mttVentiler'] -= mttVent

                # récupération lettre de ventilation
                if keyDeb in self.ddDonnees:
                    if not lettre:
                        lettre = self.ddDonnees[keyDeb]['lettreID']
                    lettreIDdeb = lettre
                else:
                    lettreIDdeb = '*'
                if keyCre in self.ddDonnees:
                    if not lettre:
                        lettre = self.ddDonnees[keyCre]['lettreID']
                    lettreIDcre = lettre
                else:
                    lettreIDcre = '*'

                if lettreIDdeb == lettreIDcre:
                    lettre = lettreIDcre
                else:
                    lettre = lettreIDdeb + lettreIDcre
                # Composition des lettres
                signe = sens
                dDonnees['lettres'] += "%s %.0f%s, " % (lettre, mttVent * signe, SYMBOLE)

        return

    def Lettrage(self, lstDemande, lstRecept):
        # Création d'une ventilation des tracks Demande par Recept
        def takeTwo(trackA, trackB):
            if trackA == trackB:
                return
            if trackA.mttVentiler_aff * trackB.mttVentiler_aff >= 0:
                # rien à ventiler car non opposés
                return
            if trackA.montant * trackA.mttVentiler <= 0\
                    or abs(trackA.montant) < abs(trackA.mttVentiler):
                # Ventilation précédentes invalide
                return
            if trackB.montant * trackB.mttVentiler <= 0\
                    or abs(trackB.montant) < abs(trackB.mttVentiler):
                # Ventilation précédentes invalide
                return

            # calcul de la ventilation possible
            mttVentilA = trackA.mttVentiler
            signeA = trackA.signeMtt
            mttVentilB = trackB.mttVentiler
            signeB = trackB.signeMtt
            absVentil = min(abs(mttVentilA), abs(mttVentilB))
            if absVentil == 0:
                return

            trackA.mttVentiler -= absVentil * signeA
            trackB.mttVentiler -= absVentil * signeB
            letA = trackA.lettreID
            letB = trackB.lettreID

            if trackA.nature != trackB.nature:
                # les deux lignes sont de nature différente : chiffre+lettre
                if trackA.nature == 'P':
                    letDeb = letA
                    letCre = letB
                    IDdeb = trackA.ID
                    IDcre = trackB.ID
                    mttVentil = absVentil * trackB.signeMtt
                else:
                    # nature de ligneA est règlement
                    letDeb = letB
                    letCre = letA
                    IDdeb = trackB.ID
                    IDcre = trackA.ID
                    mttVentil = absVentil * trackA.signeMtt
                lettre = letDeb + letCre
                ventilation = [IDdeb, IDcre, mttVentil, lettre]
                self.llVentilations.append(ventilation)
            else:
                # les deux lignes sont de même nature association homo mais séparées
                if trackA.nature == 'R':
                    ventilation = [0, trackA.ID, absVentil * trackA.signeMtt,
                                   "%s_%s"%(letA,letB)]
                    self.llVentilations.append(ventilation)
                    ventilation = [0, trackB.ID, absVentil * trackB.signeMtt,
                                   "%s_%s"%(letB,letA)]
                    self.llVentilations.append(ventilation)
                else:
                    ventilation = [trackA.ID, 0, absVentil * trackA.signeMtt,
                                   "%s_%s"%(letA,letB)]
                    self.llVentilations.append(ventilation)
                    ventilation = [trackB.ID, 0, absVentil * trackB.signeMtt,
                                   "%s_%s"%(letB,letA)]
                    self.llVentilations.append(ventilation)

        for trackD in lstDemande:
            if trackD.mttVentiler == 0:
                break
            for trackR in lstRecept:
                if trackR.mttVentiler == 0:
                    continue
                takeTwo(trackD, trackR)
        return

    def ClearLetters(self, choix):
        # récup des ID à lettrer, puis suppression des items
        lstRemove = []
        if len(self.listview.GetCheckedObjects()) in (0,len(self.listview.modelObjects)):
            # cas d'un reset global des ventilations
            self.llVentilations = []
            for dDonnees in self.ldDonnees:
                dDonnees['lettreID'] = None
            self.SetLettresID(self.ldDonnees)

        def addRemove(tple):
            if not tple in lstRemove:
                lstRemove.append(tple)

        for track in choix:
            for IDdeb, IDcre, mttVent, lettre in self.llVentilations:
                if ((IDdeb == track.ID) and (track.nature == 'P')) \
                        or ((IDcre == track.ID) and (track.nature == 'R')):
                    addRemove([IDdeb, IDcre, mttVent, lettre])
        for lst in lstRemove:
            self.llVentilations.remove(lst)

    def OnCalculLettres(self, event):
        mtt = 0.0
        mttVentil = 0.0
        for track in self.listview.GetCheckedObjects():
            mtt += track.montant_aff
            mttVentil += track.mttVentiler_aff
        # self.ctrl_montant.SetValue("{:10.2f} {}".format(mtt, SYMBOLE))
        self.ctrl_montant.SetValue(mtt)
        self.ctrl_mttVentil.SetValue(mttVentil)

    def OnMAJ(self, event):
        self.MAJ()

    def OnClicLettrer(self, event):
        choix = self.listview.GetCheckedObjects()
        if len(choix) == 0:
            mess = "Pas de choix = 'Toutes les lignes'\n\n"
            mess += "Sans ligne cochée nous allons lettrer l'ensemble avec deux possibilités:\n\n"
            mess += "- OUI: avec un délettrage préalable (conseillé pour initialiser)\n"
            mess += "- NON: seules les lignes avec montant à ventiler seront traitées\n"
            ret = wx.MessageBox(mess, "Confirmez", style=wx.YES_NO | wx.CANCEL)
            if ret == wx.YES:
                # extension du choix à toutes les lignes
                choix = self.listview.GetObjects()
                self.ClearLetters(choix)
                self.MAJ()
                choix = self.listview.GetObjects()
            elif ret != wx.NO:
                # ni oui ni non c'est l'abandon
                return

        lstIxChoix = [self.listview.modelObjects.index(x) for x in choix]

        # on vérifie si des montants sont opposés sinon rien à faire
        positives = [x for x in choix if x.montant_aff > 0]
        negatives = [x for x in choix if x.montant_aff < 0]
        if len(positives) * len(negatives) == 0:
            mess = "Pas de lettrage possible !\n\n"
            mess += "Il faut cocher des lignes avec des montants opposés + et -"
            wx.MessageBox(mess, "Information", style=wx.ICON_EXCLAMATION)
            return

        lettrer = [x for x in choix]

        def triDate(track):
            return track.date

        lettrer.sort(key=triDate)

        # premier passage pour imputer les négatifs sur les lignes de même nature
        prestPositif = [x for x in lettrer if x.montant_aff < 0 and x.nature == 'P']
        prestNegatif = [x for x in lettrer if x.montant_aff > 0 and x.nature == 'P']
        reglPositif = [x for x in lettrer if x.montant_aff > 0 and x.nature == 'R']
        reglNegatif = [x for x in lettrer if x.montant_aff < 0 and x.nature == 'R']
        if (len(prestNegatif) * len(prestPositif)) > 0:
            self.Lettrage(prestNegatif, prestPositif)
        if (len(reglNegatif) * len(reglPositif)) > 0:
            self.Lettrage(reglNegatif, reglPositif)

        self.MAJ()
        # Deuxième lancement pour le reste
        lettrer = [x for x in lettrer if x.mttVentiler != 0.0]
        self.Lettrage(lettrer, lettrer)

        choix = [self.listview.modelObjects[x] for x in lstIxChoix]
        for track in choix:
            self.listview.SetCheckState(track, True)
        self.MAJ()

    def OnClicDelettrer(self, event):
        choix = self.listview.GetCheckedObjects()
        if len(choix) == 0:
            mess = "Sans ligne cochée nous allons tout délettrer..."
            ret = wx.MessageBox("Pas de choix = 'Tous'\n\n%s" % mess, "Confirmez",
                                style=wx.YES_NO | wx.ICON_INFORMATION)
            if ret != wx.YES:
                return
            choix = self.listview.GetObjects()
        self.ClearLetters(choix)
        self.MAJ()

    def OnClicFermer(self, event):
        self.EndModal(wx.ID_CANCEL)

    def OnClicOk(self, event):
        self.EndModal(wx.ID_OK)

    def GetVentilSuppr(self):
        lstSuppr = [x for x in self.ltVentilationsOriginal if not list(x) in self.llVentilations]
        return lstSuppr

    def GetVentilNews(self):
        return [x for x in self.llVentilations if not tuple(x) in self.ltVentilationsOriginal]

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
        width,height  = kwds.pop('minSize',(550, 350))

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
        self.lstCodes = [x.lower() for x in self.lstLibels]
        self.lstCodes = [fp.Supprime_accent(x.split("/")[0].strip()) for x in self.lstCodes]
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
                        valMtt = item[champs[i]]
                        continue
                    donnee[ixVal] = item[champs[i]]
                    if isinstance(item[champs[i]],(str)):
                        lg = len(item[champs[i]])
                    else: lg = len(str(item[champs[i]]))
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
    import os
    os.chdir("..")
    app = wx.App(0)
    ddDebits = {
        12456: {"designations": ["pièce réglée 1", datetime.date.today()+datetime.timedelta(1)],
                'montant': 150.25,
                },
        12457: {"designations": ["pièce récente 2", datetime.date.today()+datetime.timedelta(5)],
                'montant': 85,
                },
        12458: {"designations": ["avoir sur piece 2", datetime.date.today()+datetime.timedelta(10)],
                'montant': -40,
                },
        12459: {"designations": ["avoir sur piece 1 à rembourser",
                                 datetime.date.today() + datetime.timedelta(10)],
                'montant': -27,
                },
    }
    ddCredits = {
        6544: {"designations": ["règlement 1", datetime.date.today()],
               'montant': 100,
               },
        6545: {"designations": ["règlement 2", datetime.date.today()+datetime.timedelta(4)],
               'montant': 90.25,
               },
        6546: {"designations": ["remboursement 1", datetime.date.today()+datetime.timedelta(5)],
               'montant': -20,
               },
        6547: {"designations": ["règlement 3", datetime.date.today()+datetime.timedelta(11)],
               'montant': 50},
        6548: {"designations": ["remboursement avoir",
                                datetime.date.today() + datetime.timedelta(5)],
               'montant': -19,
               },
    }

    ltVentilations = [
        (12458,0,-40,"3_1"),
        (12456,0,40,"1_3"),
        (0,6546, -20,"C_A"),
        (0, 6544, 39, "A_CE"),
        (0, 6547, -19, "E_A"),
        (12456,4644,100,"1A")
    ]
    ltVentilationsXXX= [
                      (12456, 6545, 66,"2O"),
                      (12456, 6545, 34, "2O"),
                      (12456, 6548, -15, "2O"),
                      (12456, 6546, -5,"3R"),
                      (12457, 65, 19, None),
                      (0,6546,-10,"R P"),
                      (0,6544,10,"P R"),
                      (12458,6547,40,None),
                      (12459,0,-13,None),
                      (12457,0,13,None)
                      ]

    dlg = DLGventilations(None, ddDebits, ddCredits, ltVentilations)

    """
    """
    # dlg = Dialog(None)
    app.SetTopWindow(dlg)
    print(dlg.ShowModal())
    # print dlg.GetChoix()
    app.MainLoop()

#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys branche Matthania
# Site internet :  www.noethys.com, Matthania
# Auteur:           Ivan LUCAS, JB, Jacques Brunel
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#-----------------------------------------------------------


from Utils.UTILS_Traduction import _
import Chemins
import wx
import datetime
from Ctrl import CTRL_Bouton_image
from wx.lib.floatcanvas import FloatCanvas
import numpy
import wx.lib.agw.pybusyinfo as PBI
from Dlg import DLG_Noedoc
from Ctrl import CTRL_Bandeau
from Ctrl import CTRL_Choix_modele
from Utils import UTILS_Config
from Ol import OL_Etiquettes

# Couleurs
COULEUR_ZONE_TRAVAIL = (100, 200, 0)
COULEUR_FOND_PAGE = (255, 255, 255)
EPAISSEUR_OMBRE = 2
COULEUR_OMBRE_PAGE = (0, 0, 0)
COULEUR_BORD_ETIQUETTE = (255, 0, 0)
COULEUR_FOND_ETIQUETTE = (200, 200, 200)

    
# ------------------------------------------------------------------------------------------------------------

LISTE_CATEGORIES = [
    ("", _(" ")),
    ("individu", _("Individus")),
    ("pur_enfant", _("Ind. pur enfants")),
    ("pur_prospect", _("Ind. pur prospects")),
    ("famille", _("Familles")),
    ("isole", _("Ajouter les sans famille")),
    ("famille_actif", _("Familles actives")),
    ("benevole_actif", _("Bénévoles actifs")),
]

class CTRL_Categorie(wx.Choice):
    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1, size=(-1, -1)) 
        self.parent = parent
        self.MAJ() 
        self.SetSelection(0)
    
    def MAJ(self):
        listeItems = self.GetListeDonnees()
        if len(listeItems) == 0 :
            self.Enable(False)
        self.SetItems(listeItems)
                                        
    def GetListeDonnees(self):
        listeItems = []
        index = 0
        for code, label in LISTE_CATEGORIES :
            listeItems.append(label)
            index += 1
        return listeItems

    def SetCategorie(self, categorie=""):
        index = 0
        for code, label in LISTE_CATEGORIES :
            if code == categorie :
                 self.SetSelection(index)
            index += 1

    def GetCategorie(self):
        index = self.GetSelection()
        return LISTE_CATEGORIES[index][0]

# -----------------------------------------------------------------------------------------------------
    
class CTRL_Apercu(wx.Panel):
    def __init__(self, parent,
                IDmodele=None, 
                taille_page=(210, 297),
                margeHaut=10,
                margeGauche=10,
                margeBas = 10,
                margeDroite=10,
                espaceVertical=5,
                espaceHorizontal=5,
                ):
        wx.Panel.__init__(self, parent, id=-1, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL)        
        self.parent = parent
        self.taille_page = taille_page
        self.largeurPage = taille_page[0]
        self.hauteurPage = taille_page[1]
        self.margeHaut = margeHaut
        self.margeGauche = margeGauche
        self.margeBas = margeBas
        self.margeDroite = margeDroite
        self.espaceVertical = espaceVertical
        self.espaceHorizontal = espaceHorizontal
        
        # FloatCanvas
        self.canvas = FloatCanvas.FloatCanvas(self, Debug=0, BackgroundColor=COULEUR_ZONE_TRAVAIL)

        # Layout
        grid_sizer_base = wx.FlexGridSizer(rows=2, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.canvas, 0, wx.EXPAND, 0)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.AddGrowableRow(0)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        
        # Init Modèle
        self.SetModele(IDmodele)
    
    def SetModele(self, IDmodele=None):
        # Initialisation du modèle de document
        if IDmodele == None :
            self.largeurEtiquette = 0
            self.hauteurEtiquette = 0
            return
        modeleDoc = DLG_Noedoc.ModeleDoc(IDmodele=IDmodele)
        self.largeurEtiquette = modeleDoc.dictInfosModele["largeur"]
        self.hauteurEtiquette = modeleDoc.dictInfosModele["hauteur"]
        
    def SetTaillePage(self, taille_page=(210, 297)):
        self.taille_page = taille_page
        self.largeurPage = taille_page[0]
        self.hauteurPage = taille_page[1]
        
    def SetMargeHaut(self, valeur=0):
        self.margeHaut = valeur

    def SetMargeGauche(self, valeur=0):
        self.margeGauche = valeur
        
    def SetMargeBas(self, valeur=0):
        self.margeBas = valeur
        
    def SetMargeDroite(self, valeur=0):
        self.margeDroite = valeur
        
    def SetEspaceVertical(self, valeur=0):
        self.espaceVertical = valeur
        
    def SetEspaceHorizontal(self, valeur=0):
        self.espaceHorizontal = valeur

    def MAJ(self):
        self.canvas.ClearAll()
        self.Init_page() 
        self.Dessine_etiquettes() 
        self.canvas.ZoomToBB()        

    def Init_page(self):
        """ Dessine le fond de page """
        # Ombre de la page
        ombre1 = FloatCanvas.Rectangle( (self.taille_page[0]-1, -EPAISSEUR_OMBRE), (EPAISSEUR_OMBRE+1, self.taille_page[1]), LineWidth=0, LineColor=COULEUR_OMBRE_PAGE, FillColor=COULEUR_OMBRE_PAGE, InForeground=False)
        ombre2 = FloatCanvas.Rectangle( (EPAISSEUR_OMBRE, -EPAISSEUR_OMBRE), (self.taille_page[0]-1, EPAISSEUR_OMBRE+1), LineWidth=0, LineColor=COULEUR_OMBRE_PAGE, FillColor=COULEUR_OMBRE_PAGE, InForeground=False)
        # Fond de page
        rect = FloatCanvas.Rectangle( (0, 0), self.taille_page, LineWidth=1, FillColor=COULEUR_FOND_PAGE, InForeground=False)
        self.page = self.canvas.AddGroup([ombre1, ombre2, rect], InForeground=False)

    def Dessine_etiquettes(self):
        # Calcul du nbre de colonnes et de lignes
        if self.largeurEtiquette < 1 or self.hauteurEtiquette < 1 :
            nbreColonnes = 0
            nbreLignes = 0
        else:
            nbreColonnes = (self.largeurPage - self.margeGauche - self.margeDroite + self.espaceHorizontal) / (self.largeurEtiquette + self.espaceHorizontal)
            nbreLignes = (self.hauteurPage - self.margeHaut - self.margeBas + self.espaceVertical) / (self.hauteurEtiquette + self.espaceVertical)
        # Dessin des étiquettes
        numColonne = 0
        numLigne = 0
        y = self.hauteurPage - self.margeHaut- self.hauteurEtiquette
        for numLigne in range(0, int(nbreLignes)) :
            x = self.margeGauche
            for numColonne in range(0, int(nbreColonnes)) :
                rect = FloatCanvas.Rectangle(numpy.array([x, y]), numpy.array([self.largeurEtiquette, self.hauteurEtiquette]), LineWidth=0.25, LineColor=COULEUR_BORD_ETIQUETTE, FillColor=COULEUR_FOND_ETIQUETTE, InForeground=True)
                self.canvas.AddObject(rect)
                x += (self.largeurEtiquette + self.espaceHorizontal)
            y -= (self.hauteurEtiquette + self.espaceVertical)

# ---------------------------------------------------------------------------------------------------------------------------------

class CTRL_Donnees(wx.Panel):
    def __init__(self, parent, categorie="", IDindividu=None, IDfamille=None):
        wx.Panel.__init__(self, parent, id=-1)
        # Contrôles
        self.parent = parent

        self.listview = OL_Etiquettes.ListView(self, id=-1, categorie=categorie,
                                                IDindividu=IDindividu,
                                                IDfamille=IDfamille,
                                                style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        self.listview.SetMinSize((600, 400))
        self.barre_recherche = OL_Etiquettes.CTRL_Outils(self, listview=self.listview, afficherCocher=True)
        #self.listview.MAJ()
        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.listview, 1, wx.EXPAND | wx.BOTTOM, 5)
        sizer.Add(self.barre_recherche, 0, wx.EXPAND, 0)
        self.SetSizer(sizer)
        sizer.Fit(self)

    def MAJ(self):
        self.listview.MAJ()
        self.listview.CocheListeTout()

class Panel_Donnees(wx.Panel):
    def __init__(self, parent, IDindividu=None, IDfamille=None):
        wx.Panel.__init__(self, parent, id=-1) 
        self.parent = parent
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.listePages = []

        # Page DIVERS
        if not (IDindividu or IDfamille):
            for categ,libel in LISTE_CATEGORIES:
                if len(categ) > 0:
                    page =  CTRL_Donnees(self)
                    sizer.Add(page, 1, wx.EXPAND, 0)
                    page.Show(False)
                    self.listePages.append((categ, page))
        else:
            # Page Individus
            page =  CTRL_Donnees(self, categorie="individu", IDindividu=IDindividu)
            sizer.Add(page, 1, wx.EXPAND, 0)
            page.Show(False)
            self.listePages.append(("individu", page))

            # Page Familles
            page =  CTRL_Donnees(self, categorie="famille", IDfamille=IDfamille)
            sizer.Add(page, 1, wx.EXPAND, 0)
            page.Show(False)
            self.listePages.append(("famille", page))

        self.SetSizer(sizer)
        sizer.Fit(self)
        
    def SetSelection(self, categorie="individu", questions=False, diffusions=False, refusPub=False, actif=None):
        self.Freeze()
        nomPage = categorie
        if nomPage == "isole": nomPage = "famille"
        # DLG Attente
        dlgAttente = PBI.PyBusyInfo(_("Veuillez patienter durant l'initialisation de l'éditeur..."), parent=None, title=_("Patientez"), icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
        wx.Yield()
        for categoriePage, page in self.listePages :
            if categoriePage == nomPage :
                page.listview.MAJ(categorie=categorie, questions=questions, diffusions=diffusions, refusPub=refusPub, actif=actif)
                page.Show(True)
            else :
                page.Show(False)
        del dlgAttente
        self.Layout()
        self.Thaw() 
            
    def GetPage(self):
        for categoriePage, page in self.listePages :
            if page.IsShown() :
                return page
        return None
    
    def GetInfosCoches(self):
        return self.GetPage().listview.GetInfosCoches()

# ---------------------------------------------------------------------------------------------------------------------------------

class Dialog(wx.Dialog):
    def __init__(self, parent, categorie=[], IDindividu=None, IDfamille=None):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        # Si on vient d'une fiche famille ou d'une fiche individuelle, force la catégorie
        if IDindividu != None : categorie = "individu"
        if IDfamille != None : categorie = "famille"
        self.categorie_liste = categorie
        self.categorie_doc = None
        self.questions = False
        self.diffusions = False
        self.refusPub = False
        self.oldCategorie = None



        # Bandeau
        titre = _("Impression d'étiquettes ou de badges")
        intro = _("Vous pouvez ici imprimer rapidement des planches d'étiquettes ou de badges au format PDF. Commencez par sélectionner la catégorie de données et un modèle, puis définissez le gabarit de la page avant de cocher les données à afficher.")
        self.SetTitle("DLG_Impression_etiquettes")
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/22x22/Smiley_nul.png")
        
        # Modèle
        self.box_modele_staticbox = wx.StaticBox(self, -1, _("Sélection liste et modèle"))
        self.label_categorie = wx.StaticText(self, -1, _("Liste :"))
        self.ctrl_categorie = CTRL_Categorie(self)
        self.label_actif = wx.StaticText(self, -1, _("Depuis :"))
        self.ctrl_actif = wx.TextCtrl(self,style=wx.TE_PROCESS_ENTER)
        self.bouton_actif = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Actualiser2.png"), wx.BITMAP_TYPE_ANY))
        self.label_modele = wx.StaticText(self, -1, _("Modèle :"))
        self.ctrl_modele = CTRL_Choix_modele.CTRL_Choice(self, categorie=self.categorie_liste)
        self.bouton_modele = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Mecanisme.png"), wx.BITMAP_TYPE_ANY))
        
        # Gabarit
        self.box_gabarit_staticbox = wx.StaticBox(self, -1, _("Gabarit (en mm)"))
        self.label_largeur_page = wx.StaticText(self, -1, _("Largeur page :"))
        self.ctrl_largeur_page = wx.SpinCtrl(self, -1, "", min=1, max=1000)
        self.label_marge_haut = wx.StaticText(self, -1, _("Marge haut :"))
        self.ctrl_marge_haut = wx.SpinCtrl(self, -1, "", min=0, max=1000)
        self.label_hauteur_page = wx.StaticText(self, -1, _("Hauteur page :"))
        self.ctrl_hauteur_page = wx.SpinCtrl(self, -1, "", min=1, max=1000)
        self.label_marge_bas = wx.StaticText(self, -1, _("Marge bas :"))
        self.ctrl_marge_bas = wx.SpinCtrl(self, -1, "", min=0, max=1000)
        self.label_espace_vertic = wx.StaticText(self, -1, _("Espace vertic. :"))
        self.ctrl_espace_vertic = wx.SpinCtrl(self, -1, "", min=0, max=1000)
        self.label_marge_gauche = wx.StaticText(self, -1, _("Marge gauche :"))
        self.ctrl_marge_gauche = wx.SpinCtrl(self, -1, "", min=0, max=1000)
        self.label_espace_horiz = wx.StaticText(self, -1, _("Espace horiz. :"))
        self.ctrl_espace_horiz = wx.SpinCtrl(self, -1, "", min=0, max=1000)
        self.label_marge_droite = wx.StaticText(self, -1, _("Marge droite :"))
        self.ctrl_marge_droite = wx.SpinCtrl(self, -1, "", min=0, max=1000)
        
        # Aperçu
        self.box_apercu_staticbox = wx.StaticBox(self, -1, _("Aperçu du gabarit"))
        self.ctrl_apercu = CTRL_Apercu(self)

        # Options
        self.box_options_staticbox = wx.StaticBox(self, -1, _("Options"))
        self.check_contour = wx.CheckBox(self, -1, _("Contour des étiquettes"))
        self.check_reperes = wx.CheckBox(self, -1, _("Repères de découpe"))
        
        # Données
        self.box_donnees_staticbox = wx.StaticBox(self, -1, _("Liste des étiquettes"))
        self.ctrl_donnees = Panel_Donnees(self, IDindividu=IDindividu, IDfamille=IDfamille)
        
        # Mémorisation des paramètres
        self.ctrl_memoriser = wx.CheckBox(self, -1, _("Mémoriser les paramètres"))
        self.ctrl_questions = wx.CheckBox(self, -1, _("Avec colonnes questionnaires"))
        self.ctrl_diffusions = wx.CheckBox(self, -1, _("Avec colonnes listes de diffusion"))
        self.ctrl_forcerPub = wx.CheckBox(self, -1, _("Ignorer refus pub_papier"))
        font = self.GetFont()
        font.SetPointSize(7)
        self.ctrl_memoriser.SetFont(font)
        self.ctrl_memoriser.SetValue(True) 
        self.ctrl_questions.SetFont(font)
        self.ctrl_questions.SetValue(False)
        self.ctrl_diffusions.SetFont(font)
        self.ctrl_diffusions.SetValue(True)
        self.ctrl_forcerPub.SetFont(font)
        self.ctrl_forcerPub.SetValue(True)

        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png"))
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Etiquettes"), cheminImage=Chemins.GetStaticPath("Images/32x32/Apercu.png"))
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Fermer"), cheminImage=Chemins.GetStaticPath("Images/32x32/Fermer.png"))
        self.bouton_actual = CTRL_Bouton_image.CTRL(self, texte=_("Actualiser"), cheminImage=Chemins.GetStaticPath("Images/32x32/Actualiser.png"))

        self.__set_properties()
        self.__do_layout()
        
        self.Bind(wx.EVT_CHOICE, self.OnChoixCategorie, self.ctrl_categorie)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnChoixCategorie, self.ctrl_actif)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnChoixCategorie, self.ctrl_actif)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonActif, self.bouton_actif)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonActif, self.bouton_actual)
        self.Bind(wx.EVT_CHECKBOX, self.OnChoixCategorie, self.ctrl_questions)
        self.Bind(wx.EVT_CHECKBOX, self.OnChoixCategorie, self.ctrl_diffusions)
        self.Bind(wx.EVT_CHECKBOX, self.OnChoixCategorie, self.ctrl_forcerPub)
        self.Bind(wx.EVT_CHOICE, self.OnChoixModele, self.ctrl_modele)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonModele, self.bouton_modele)
        self.Bind(wx.EVT_SPINCTRL, self.OnChoixTaille, self.ctrl_largeur_page)
        self.Bind(wx.EVT_SPINCTRL, self.OnChoixMargeH, self.ctrl_marge_haut)
        self.Bind(wx.EVT_SPINCTRL, self.OnChoixTaille, self.ctrl_hauteur_page)
        self.Bind(wx.EVT_SPINCTRL, self.OnChoixMargeB, self.ctrl_marge_bas)
        self.Bind(wx.EVT_SPINCTRL, self.OnChoixEspaceV, self.ctrl_espace_vertic)
        self.Bind(wx.EVT_SPINCTRL, self.OnChoixMargeG, self.ctrl_marge_gauche)
        self.Bind(wx.EVT_SPINCTRL, self.OnChoixEspaceH, self.ctrl_espace_horiz)
        self.Bind(wx.EVT_SPINCTRL, self.OnChoixMargeD, self.ctrl_marge_droite)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)
        
        # Init contrôles
        largeurPage = UTILS_Config.GetParametre("impression_etiquettes_largeurpage", defaut=210)
        hauteurPage = UTILS_Config.GetParametre("impression_etiquettes_hauteurpage", defaut=297)
        margeHaut = UTILS_Config.GetParametre("impression_etiquettes_margehaut", defaut=10)
        margeBas = UTILS_Config.GetParametre("impression_etiquettes_margebas", defaut=10)
        margeGauche = UTILS_Config.GetParametre("impression_etiquettes_margegauche", defaut=10)
        margeDroite = UTILS_Config.GetParametre("impression_etiquettes_margedroite", defaut=10)
        espaceV = UTILS_Config.GetParametre("impression_etiquettes_espacev", defaut=5)
        espaceH = UTILS_Config.GetParametre("impression_etiquettes_espaceh", defaut=5)
        contour = UTILS_Config.GetParametre("impression_etiquettes_contour", defaut=False)
        reperes = UTILS_Config.GetParametre("impression_etiquettes_reperes", defaut=False)
        memoriser = UTILS_Config.GetParametre("impression_etiquettes_memoriser", defaut=1)
        questions = UTILS_Config.GetParametre("impression_etiquettes_questions", defaut=0)
        diffusions = UTILS_Config.GetParametre("impression_etiquettes_diffusions", defaut=0)
        forcerPub = UTILS_Config.GetParametre("impression_etiquettes_refusPub", defaut=1)
        self.categorie_liste = UTILS_Config.GetParametre("impression_etiquettes_categorie", defaut=categorie)


        self.ctrl_questions.SetValue(questions)
        self.ctrl_diffusions.SetValue(diffusions)
        self.ctrl_forcerPub.SetValue(forcerPub)

        self.ctrl_largeur_page.SetValue(largeurPage)
        self.ctrl_hauteur_page.SetValue(hauteurPage)
        self.ctrl_marge_haut.SetValue(margeHaut)
        self.ctrl_marge_bas.SetValue(margeBas)
        self.ctrl_marge_gauche.SetValue(margeGauche)
        self.ctrl_marge_droite.SetValue(margeDroite)
        self.ctrl_espace_vertic.SetValue(espaceV)
        self.ctrl_espace_horiz.SetValue(espaceH)
        
        self.check_contour.SetValue(contour)
        self.check_reperes.SetValue(reperes)
        self.ctrl_memoriser.SetValue(memoriser)
        
        self.ctrl_categorie.SetCategorie(self.categorie_liste)
        self.OnChoixCategorie(None)
        self.ctrl_actif.SetValue(str(datetime.date.today().year))

        # Init Aperçu
        self.ctrl_apercu.SetTaillePage((largeurPage, hauteurPage))
        self.ctrl_apercu.SetMargeHaut(margeHaut)
        self.ctrl_apercu.SetMargeGauche(margeGauche)
        self.ctrl_apercu.SetMargeBas(margeBas)
        self.ctrl_apercu.SetMargeDroite(margeDroite)
        self.ctrl_apercu.SetEspaceVertical(espaceV)
        self.ctrl_apercu.SetEspaceHorizontal(espaceH)
        self.ctrl_apercu.SetModele(self.ctrl_modele.GetID())
        self.ctrl_apercu.MAJ()
        
        if IDindividu != None or IDfamille != None :
            self.ctrl_categorie.Enable(False)
        self.ctrl_actif.Enable(False)
        self.label_actif.Enable(False)
        #self.ctrl_donnees.SetSelection(categorie=self.categorie_liste)

    def __set_properties(self):
        self.ctrl_categorie.SetToolTip(_("Sélectionnez ici une catégorie de liste"))
        self.ctrl_actif.SetToolTip(_("Pour critère 'actif' sélectionnez ici l'année d'antériorité possible d'activité"))
        self.bouton_actif.SetToolTip(_("Validation et Constitution de la liste"))
        self.bouton_actual.SetToolTip(_("Validation et Constitution de la liste"))
        self.ctrl_modele.SetToolTip(_("Sélectionnez ici un modèle"))
        self.bouton_modele.SetToolTip(_("Cliquez ici pour accéder au paramétrage des modèles"))
        self.ctrl_largeur_page.SetMinSize((60, -1))
        self.ctrl_largeur_page.SetToolTip(_("Saisissez ici la largeur de la page (en mm)"))
        self.ctrl_marge_haut.SetMinSize((60, -1))
        self.ctrl_marge_haut.SetToolTip(_("Saisissez ici la marge de haut de page (en mm)"))
        self.ctrl_hauteur_page.SetMinSize((60, -1))
        self.ctrl_hauteur_page.SetToolTip(_("Saisissez ici la hauteur de la page (en mm)"))
        self.ctrl_marge_bas.SetMinSize((60, -1))
        self.ctrl_marge_bas.SetToolTip(_("Saisissez ici la marge de bas de page (en mm)"))
        self.ctrl_espace_vertic.SetMinSize((60, -1))
        self.ctrl_espace_vertic.SetToolTip(_("Saisissez ici l'espace vertical entre 2 étiquettes (en mm)"))
        self.ctrl_marge_gauche.SetMinSize((60, -1))
        self.ctrl_marge_gauche.SetToolTip(_("Saisissez ici la marge gauche de la page (en mm)"))
        self.ctrl_espace_horiz.SetMinSize((60, -1))
        self.ctrl_espace_horiz.SetToolTip(_("Saisissez ici l'espace horizontal entre 2 étiquettes de la page (en mm)"))
        self.ctrl_marge_droite.SetMinSize((60, -1))
        self.ctrl_marge_droite.SetToolTip(_("Saisissez ici la marge droite de la page (en mm)"))
        self.check_contour.SetToolTip(_("Cochez ici pour afficher un cadre noir autour de chaque étiquette"))
        self.check_reperes.SetToolTip(_("Cochez cette case pour afficher les repères de découpe sur chaque page"))
        self.bouton_aide.SetToolTip(_("Cliquez ici pour obtenir de l'aide"))
        self.bouton_ok.SetToolTip(_("Cliquez ici pour afficher un aperçu du PDF"))
        self.bouton_annuler.SetToolTip(_("Cliquez ici pour annuler"))
        self.ctrl_memoriser.SetToolTip(_("Cochez cette case pour mémoriser les paramètres pour la prochaine édition"))
        self.ctrl_questions.SetToolTip(_("Cochez cette case pour faire apparaître les réponses aux questionnaires"))
        self.ctrl_diffusions.SetToolTip(_("Cochez cette case pour faire apparaître les listes de diffusions dans les colonnes"))
        self.ctrl_forcerPub.SetToolTip(_("Pour faire apparaître les lignes dont le client refus la pub ou sans code postal"))
        self.SetMinSize((1200, 770))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=5, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)

        grid_sizer_contenu = wx.FlexGridSizer(rows=1, cols=2, vgap=10, hgap=10)
        grid_sizer_gauche = wx.FlexGridSizer(rows=4, cols=1, vgap=5, hgap=5)

        # Modèle
        box_modele = wx.StaticBoxSizer(self.box_modele_staticbox, wx.VERTICAL)

        grid_sizer_modele0 = wx.FlexGridSizer(rows=1, cols=5, vgap=3, hgap=5)
        grid_sizer_modele0.Add(self.label_categorie, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_modele0.Add(self.ctrl_categorie, 0, wx.EXPAND, 0)
        grid_sizer_modele0.Add(self.label_actif, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_modele0.Add(self.ctrl_actif, 0, wx.EXPAND, 0)
        grid_sizer_modele0.Add(self.bouton_actif, 0, wx.EXPAND, 0)
        box_modele.Add(grid_sizer_modele0, 1, wx.ALL|wx.EXPAND, 5)

        grid_sizer_modele1 = wx.FlexGridSizer(rows=3, cols=2, vgap=5, hgap=5)
        grid_sizer_modele1.Add(self.label_modele, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_modele2 = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_modele2.Add(self.ctrl_modele, 0, wx.EXPAND, 0)
        grid_sizer_modele2.Add(self.bouton_modele, 0, 0, 0)
        grid_sizer_modele2.AddGrowableCol(0)
        grid_sizer_modele1.Add(grid_sizer_modele2, 1, wx.EXPAND, 0)
        grid_sizer_modele1.AddGrowableCol(1)
        box_modele.Add(grid_sizer_modele1, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_gauche.Add(box_modele, 1, wx.EXPAND, 0)
        
        # Gabarit
        box_gabarit = wx.StaticBoxSizer(self.box_gabarit_staticbox, wx.VERTICAL)
        grid_sizer_gabarit = wx.FlexGridSizer(rows=4, cols=4, vgap=2, hgap=5)
        grid_sizer_gabarit.Add(self.label_largeur_page, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_gabarit.Add(self.ctrl_largeur_page, 0, wx.RIGHT, 10)
        grid_sizer_gabarit.Add(self.label_marge_haut, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_gabarit.Add(self.ctrl_marge_haut, 0, 0, 0)
        grid_sizer_gabarit.Add(self.label_hauteur_page, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_gabarit.Add(self.ctrl_hauteur_page, 0, 0, 0)
        grid_sizer_gabarit.Add(self.label_marge_bas, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_gabarit.Add(self.ctrl_marge_bas, 0, 0, 0)
        grid_sizer_gabarit.Add(self.label_espace_vertic, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_gabarit.Add(self.ctrl_espace_vertic, 0, 0, 0)
        grid_sizer_gabarit.Add(self.label_marge_gauche, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_gabarit.Add(self.ctrl_marge_gauche, 0, 0, 0)
        grid_sizer_gabarit.Add(self.label_espace_horiz, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_gabarit.Add(self.ctrl_espace_horiz, 0, 0, 0)
        grid_sizer_gabarit.Add(self.label_marge_droite, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_gabarit.Add(self.ctrl_marge_droite, 0, 0, 0)
        box_gabarit.Add(grid_sizer_gabarit, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_gauche.Add(box_gabarit, 1, wx.EXPAND, 0)

        # Options
        box_options = wx.StaticBoxSizer(self.box_options_staticbox, wx.VERTICAL)
        grid_sizer_options = wx.FlexGridSizer(rows=1, cols=5, vgap=5, hgap=5)
        grid_sizer_options.Add(self.check_contour, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_options.Add(self.check_reperes, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        box_options.Add(grid_sizer_options, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_gauche.Add(box_options, 1, wx.EXPAND, 0)

        # Aperçu
        box_apercu = wx.StaticBoxSizer(self.box_apercu_staticbox, wx.VERTICAL)
        box_apercu.Add(self.ctrl_apercu, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_gauche.Add(box_apercu, 1, wx.EXPAND, 0)

        grid_sizer_gauche.AddGrowableRow(3)
        grid_sizer_gauche.AddGrowableCol(0)
        grid_sizer_contenu.Add(grid_sizer_gauche, 1, wx.EXPAND, 0)

        # Données
        box_donnees = wx.StaticBoxSizer(self.box_donnees_staticbox, wx.VERTICAL)
        grid_sizer_donnees = wx.FlexGridSizer(rows=2, cols=1, vgap=5, hgap=5)
        grid_sizer_donnees.Add(self.ctrl_donnees, 1, wx.EXPAND, 0)
                
        grid_sizer_donnees.AddGrowableRow(0)
        grid_sizer_donnees.AddGrowableCol(0)
        box_donnees.Add(grid_sizer_donnees, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_contenu.Add(box_donnees, 1,wx.EXPAND, 0)

        grid_sizer_contenu.AddGrowableRow(0)
        grid_sizer_contenu.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_contenu, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

        # Check Mémoriser
        grid_sizer_cases = wx.FlexGridSizer(rows=1, cols=4, vgap=5, hgap=5)
        grid_sizer_cases.Add(self.ctrl_memoriser, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        grid_sizer_cases.Add(self.ctrl_questions, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        grid_sizer_cases.Add(self.ctrl_diffusions, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        grid_sizer_cases.Add(self.ctrl_forcerPub, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        grid_sizer_base.Add(grid_sizer_cases, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 0)

        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=5, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_actual, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)

        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        self.Layout()
        self.CenterOnScreen() 
        
        wx.CallLater(0, self.Layout) # Contre pb d'affichage du wx.Choice
    
    def OnChoixCategorie(self, event):
        self.questions = self.ctrl_questions.Value
        self.diffusions = self.ctrl_diffusions.Value
        self.refusPub = not self.ctrl_forcerPub.Value
        self.actif = None
        self.categorie_liste = self.ctrl_categorie.GetCategorie()
        self.categorie_doc = self.categorie_liste
        if self.categorie_doc == "isole" : self.categorie_doc = "famille"
        if "benevole" in self.categorie_liste : self.categorie_doc = "individu"
        elif "pur" in self.categorie_liste:
            self.categorie_doc = "individu"
        elif "famille" in self.categorie_liste : self.categorie_doc = "famille"
        if self.oldCategorie and self.categorie_liste == "isole":
            if self.oldCategorie != "famille":
                self.oldCategorie = None
                ret = wx.MessageBox("Les 'sans famille' ne peuvent s'ajouter qu'à la liste 'Familles',\n"+
                              "Vous pouvez demander à nouveau pour avoir les 'sans famille' seuls")
        if 'actif' in self.categorie_liste :
            self.ctrl_actif.Enable(True)
            self.label_actif.Enable(True)
            annee = str(self.ctrl_actif.GetValue())
            if (not annee) or int(annee)< 2000:
                wx.MessageBox("Veuillez resaisir une année nombre entier supérieur à 2000")
                return 'ko'
            self.actif = annee
        else:
            self.ctrl_actif.Enable(False)
            self.label_actif.Enable(False)
        self.ctrl_modele.SetCategorie(self.categorie_doc)
        self.ctrl_apercu.SetModele(self.ctrl_modele.GetID())

    def OnBoutonActif(self,event):
        ret = self.Validation()
        if not ret : return
        self.OnChoixCategorie(None)
        self.ctrl_apercu.MAJ()
        self.ctrl_donnees.SetSelection(categorie=self.categorie_liste, questions = self.questions, diffusions = self.diffusions,
                                       refusPub = self.refusPub,actif=self.actif)
        self.oldCategorie = self.categorie_liste

    def OnChoixModele(self, event): 
        self.ctrl_apercu.SetModele(self.ctrl_modele.GetID())
        self.ctrl_apercu.MAJ() 

    def OnBoutonModele(self, event): 
        from Dlg import DLG_Modeles_docs
        dlg = DLG_Modeles_docs.Dialog(self, categorie=self.categorie_doc)
        dlg.ShowModal() 
        dlg.Destroy()
        self.ctrl_modele.MAJ() 
        self.ctrl_apercu.SetModele(self.ctrl_modele.GetID())
        self.ctrl_apercu.MAJ() 

    def OnChoixTaille(self, event): 
        largeur = self.ctrl_largeur_page.GetValue()
        hauteur = self.ctrl_hauteur_page.GetValue()
        self.ctrl_apercu.SetTaillePage((largeur, hauteur))
        self.ctrl_apercu.MAJ() 

    def OnChoixMargeH(self, event): 
        valeur = self.ctrl_marge_haut.GetValue()
        self.ctrl_apercu.SetMargeHaut(valeur)
        self.ctrl_apercu.MAJ() 

    def OnChoixMargeB(self, event): 
        valeur = self.ctrl_marge_bas.GetValue()
        self.ctrl_apercu.SetMargeBas(valeur)
        self.ctrl_apercu.MAJ() 
        
    def OnChoixMargeG(self, event): 
        valeur = self.ctrl_marge_gauche.GetValue()
        self.ctrl_apercu.SetMargeGauche(valeur)
        self.ctrl_apercu.MAJ() 

    def OnChoixMargeD(self, event): 
        valeur = self.ctrl_marge_droite.GetValue()
        self.ctrl_apercu.SetMargeDroite(valeur)
        self.ctrl_apercu.MAJ() 

    def OnChoixEspaceV(self, event): 
        valeur = self.ctrl_espace_vertic.GetValue()
        self.ctrl_apercu.SetEspaceVertical(valeur)
        self.ctrl_apercu.MAJ() 

    def OnChoixEspaceH(self, event): 
        valeur = self.ctrl_espace_horiz.GetValue()
        self.ctrl_apercu.SetEspaceHorizontal(valeur)
        self.ctrl_apercu.MAJ() 

    def OnBoutonAide(self, event): 
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Editiondtiquettesetdebadges")

    def OnBoutonAnnuler(self, event):
        self.MemoriserParametres() 
        self.EndModal(wx.ID_CANCEL)

    def MemoriserParametres(self):
        if self.ctrl_memoriser.GetValue() == True :
            UTILS_Config.SetParametre("impression_etiquettes_largeurpage", self.ctrl_largeur_page.GetValue())
            UTILS_Config.SetParametre("impression_etiquettes_hauteurpage", self.ctrl_hauteur_page.GetValue())
            UTILS_Config.SetParametre("impression_etiquettes_margehaut", self.ctrl_marge_haut.GetValue())
            UTILS_Config.SetParametre("impression_etiquettes_margebas", self.ctrl_marge_bas.GetValue())
            UTILS_Config.SetParametre("impression_etiquettes_margegauche", self.ctrl_marge_gauche.GetValue())
            UTILS_Config.SetParametre("impression_etiquettes_margedroite", self.ctrl_marge_droite.GetValue())
            UTILS_Config.SetParametre("impression_etiquettes_espacev", self.ctrl_espace_vertic.GetValue())
            UTILS_Config.SetParametre("impression_etiquettes_espaceh", self.ctrl_espace_horiz.GetValue())
            UTILS_Config.SetParametre("impression_etiquettes_contour", self.check_contour.GetValue())
            UTILS_Config.SetParametre("impression_etiquettes_reperes", self.check_reperes.GetValue())
            UTILS_Config.SetParametre("impression_etiquettes_memoriser", self.ctrl_memoriser.GetValue())
            UTILS_Config.SetParametre("impression_etiquettes_questions", self.ctrl_questions.GetValue())
            UTILS_Config.SetParametre("impression_etiquettes_diffusions", self.ctrl_diffusions.GetValue())
            UTILS_Config.SetParametre("impression_etiquettes_refusPub", self.ctrl_forcerPub.GetValue())
            UTILS_Config.SetParametre("impression_etiquettes_categorie", self.ctrl_categorie.GetCategorie())

    def Validation(self):
        # Récupère les paramètres,
        IDmodele = self.ctrl_modele.GetID()
        if IDmodele == None :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement sélectionner une liste et modèle !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        return wx.ID_OK

    def OnBoutonOk(self, event):
        # lancement impression
        ret = self.Validation()
        if not ret : return
        if not self.ctrl_donnees.GetPage():
            wx.MessageBox("Liste vide\n\nvalidez la liste et l'année en haut de l'écran pour afficher la liste")
            return
        # DLG Attente
        IDmodele = self.ctrl_modele.GetID()
        taillePage = (self.ctrl_largeur_page.GetValue(), self.ctrl_hauteur_page.GetValue())
        margeHaut = self.ctrl_marge_haut.GetValue()
        margeGauche = self.ctrl_marge_gauche.GetValue()
        margeBas = self.ctrl_marge_bas.GetValue()
        margeDroite = self.ctrl_marge_droite.GetValue()
        espaceVertical = self.ctrl_espace_vertic.GetValue()
        espaceHorizontal = self.ctrl_espace_horiz.GetValue()
        AfficherContourEtiquette = self.check_contour.GetValue()
        AfficherReperesDecoupe = self.check_reperes.GetValue()
        
        # Récupération des valeurs
        listeValeurs = self.ctrl_donnees.GetInfosCoches()
        j=0
        i = 0
        for track in self.ctrl_donnees.GetPage().listview.GetTracksCoches():
            if track.cp == None :
                i+=1
            elif track.cp[:2] == '00':
                j+= 1
            elif track.cp[:2] == "0 ":
                i += 1
        if i>0 : mess = "Des étiquettes auront des codes postaux à blanc !\n Vous pouviez les décocher avant en triant la colonne."
        if j>0 : mess = "Des étiquettes auront des codes postaux commençant par '00'!\n Vous pouviez les filtrer en décochant 'Avec code postal 00'."
        if i+j > 0 :
            dlg = wx.MessageDialog(self, _(mess), _("Remarque"), wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()

        if len(listeValeurs) == 0 :
            dlg = wx.MessageDialog(self, _("Il n'y a aucune donnée à imprimer !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return


        # Impression PDF
        from Utils import UTILS_Impression_etiquettes
        UTILS_Impression_etiquettes.Impression(
                    IDmodele=IDmodele, 
                    taillePage=taillePage,
                    listeValeurs=listeValeurs,
                    margeHaut=margeHaut,
                    margeGauche=margeGauche,
                    margeBas=margeBas, 
                    margeDroite=margeDroite,
                    espaceVertical=espaceVertical,
                    espaceHorizontal=espaceHorizontal,
                    AfficherContourEtiquette=AfficherContourEtiquette,
                    AfficherReperesDecoupe=AfficherReperesDecoupe,
                    )


if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dialog_1 = Dialog(None)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()

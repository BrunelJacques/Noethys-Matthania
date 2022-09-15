#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania gestion multi-activit�s
# Auteur:          Ivan LUCAS, JB
# Modifs: ajout bouton facturation et cha�nage d�rout�
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import Chemins
import wx
from Ctrl import CTRL_Bouton_image
import datetime
import wx.lib.agw.toasterbox as Toaster

from Utils import UTILS_Config
from Utils import UTILS_Historique
from Utils import UTILS_Utilisateurs
import GestionDB
import FonctionsPerso
from Dlg import DLG_Releve_prestations
from Gest import GestionCoherence

from Ctrl import CTRL_Composition
from Dlg import DLG_Famille_informations
from Dlg import DLG_Famille_prestations
from Dlg import DLG_Famille_reglements
from Dlg import DLG_Famille_quotients
from Dlg import DLG_Famille_caisse
from Dlg import DLG_Famille_pieces
from Dlg import DLG_Famille_cotisations
from Dlg import DLG_Famille_divers
from Dlg import DLG_Famille_factures
from Dlg import DLG_Famille_questionnaire
from Dlg import DLG_LettrageVentil
from Dlg import DLG_PrixFamille

def CreateIDfamille(DB):
    """ Cr�e la fiche famille dans la base de donn�es afin d'obtenir un IDfamille et un IDcompte_payeur """
    from Utils import UTILS_Internet
    date_creation = str(datetime.date.today())
    mess = "DLG_Familles.CreateIDfamille Insert"
    IDfamille = DB.ReqInsert("familles", [("date_creation", date_creation),],retourID=True,MsgBox=mess)
    # Cr�ation du compte payeur
    IDcompte_payeur = DB.ReqInsert("comptes_payeurs", [("IDfamille", IDfamille),("IDcompte_payeur", IDfamille)],
                                   retourID=True,MsgBox=mess)
    # Cr�ation des codes internet
    internet_identifiant= UTILS_Internet.CreationIdentifiant(IDfamille=IDfamille)
    internet_mdp = UTILS_Internet.CreationMDP()
    # Sauvegarde des donn�es
    listeDonnees = [
        ("IDcompte_payeur", IDcompte_payeur),
        ("internet_actif", 1),
        ("internet_identifiant", internet_identifiant),
        ("internet_mdp", internet_mdp),
        ]
    DB.ReqMAJ("familles", listeDonnees, "IDfamille", IDfamille)
    return IDfamille

class Notebook(wx.Notebook):
    def __init__(self, parent, id=-1, IDfamille=None):
        wx.Notebook.__init__(self, parent, id, style= wx.BK_DEFAULT) # | wx.NB_MULTILINE
        self.parent = parent
        self.IDfamille = IDfamille
        self.dictPages = {}
        
        self.listePages = [
            ("informations", _("Informations"), "DLG_Famille_informations.Panel(self, IDfamille=IDfamille)", "Information.png"),
            ("questionnaire", _("Questionnaire"), "DLG_Famille_questionnaire.Panel(self, IDfamille=IDfamille)", "Questionnaire.png"),
            ("pieces", _("Pi�ces"), "DLG_Famille_pieces.Panel(self, IDfamille=IDfamille)", "Dupliquer.png"),
            ("cotisations", _("Cotisations"), "DLG_Famille_cotisations.Panel(self, IDfamille=IDfamille)", "Cotisation.png"),
            ("caisse", _("Caisse"), "DLG_Famille_caisse.Panel(self, IDfamille=IDfamille)", "Mecanisme.png"),
            ("quotients", _("Quotients familiaux"), "DLG_Famille_quotients.Panel(self, IDfamille=IDfamille)", "Calculatrice.png"),
            ("prestations", _("Prestations"), "DLG_Famille_prestations.Panel(self, IDfamille=IDfamille)", "Etiquette.png"),
            ("factures", _("Factures"), "DLG_Famille_factures.Panel(self, IDfamille=IDfamille)", "Facture.png"),
            ("reglements", _("R�glements"), "DLG_Famille_reglements.Panel(self, IDfamille=IDfamille)", "Reglement.png"),
            ("divers", _("Divers"), "DLG_Famille_divers.Panel(self, IDfamille=IDfamille)", "Planete.png"),
            ]
            
        # ImageList pour le NoteBook
        il = wx.ImageList(16, 16)
        index = 0
        for codePage, labelPage, ctrlPage, imgPage in self.listePages :
            setattr(self, "img%d" % index, il.Add(
                wx.Bitmap(Chemins.GetStaticPath('Images/16x16/%s') % imgPage,
                          wx.BITMAP_TYPE_PNG)))
            index += 1
        self.AssignImageList(il)

        # Cr�ation des pages
        dictParametres = self.GetParametres()

        index = 0
        for codePage, labelPage, ctrlPage, imgPage in self.listePages :
            if dictParametres[codePage] == True :
                setattr(self, "page%s" % index, eval(ctrlPage))
                self.AddPage(getattr(self, "page%s" % index), labelPage)
                self.SetPageImage(index, getattr(self, "img%d" % index))
                self.dictPages[codePage] = {'ctrl': getattr(self, "page%d" % index), 'index': index}
                index += 1
        
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
        
    def GetPageAvecCode(self, codePage=""):
        return self.dictPages[codePage]["ctrl"]
    
    def AffichePage(self, codePage=""):
        indexPage = self.dictPages[codePage]["index"]
        self.SetSelection(indexPage)

    def OnPageChanged(self, event):
        """ Quand une page du notebook est s�lectionn�e """
        indexAnciennePage = event.GetOldSelection()
        codePage = self.listePages[indexAnciennePage][0]
        # Sauvegarde ancienne page si besoin
        if indexAnciennePage!=wx.NOT_FOUND:
            if codePage in ("caisse", "divers") :
                page = self.GetPage(indexAnciennePage)
                page.Sauvegarde()
            anciennePage = self.GetPage(indexAnciennePage)
        indexPage = event.GetSelection()
        page = self.GetPage(indexPage)
        if page.IsLectureAutorisee() == False :
            self.AffichePage("informations")
            UTILS_Utilisateurs.AfficheDLGInterdiction() 
            return
        self.Freeze()
        wx.CallLater(1, page.MAJ)
        self.Thaw()
        event.Skip()
        
    def MAJpageActive(self):
        """ MAJ la page active du notebook """
        indexPage = self.GetSelection()
        page = self.GetPage(indexPage)
        wx.CallLater(1, page.MAJ)
    
    def MAJpage(self, codePage=""):
        page = self.dictPages[codePage]["ctrl"]
        wx.CallLater(1, page.MAJ)

    def GetParametres(self):
        parametres = UTILS_Config.GetParametre("fiche_famille_pages", defaut={})
        dictParametres = {}
        for codePage, labelPage, ctrlPage, imgPage in self.listePages:
            if codePage in parametres:
                afficher = parametres[codePage]
            else :
                afficher = True
            dictParametres[codePage] = afficher
        return dictParametres

    def SelectionParametresPages(self):
        # Pr�paration de l'affichage des pages
        dictParametres = self.GetParametres()
        listeLabels = []
        listeSelections = []
        listeCodes = []
        index = 0
        for codePage, labelPage, ctrlPage, imgPage in self.listePages:
            if codePage not in self.pagesObligatoires :
                listeLabels.append(labelPage)
                if codePage in dictParametres:
                    if dictParametres[codePage] == True :
                        listeSelections.append(index)
                listeCodes.append(codePage)
                index += 1

        # Demande la s�lection des pages
        dlg = wx.MultiChoiceDialog( self, _(u"Cochez ou d�cochez les onglets � afficher ou � masquer :"), _(u"Afficher/masquer des onglets"), listeLabels)
        dlg.SetSelections(listeSelections)
        dlg.SetSize((300, 350))
        dlg.CenterOnScreen()
        reponse = dlg.ShowModal()
        selections = dlg.GetSelections()
        dlg.Destroy()
        if reponse != wx.ID_OK :
            return False

        # M�morisation des pages coch�es
        dictParametres = {}
        index = 0
        for codePage in listeCodes:
            if index in selections :
                dictParametres[codePage] = True
            else :
                dictParametres[codePage] = False
            index += 1
        UTILS_Config.SetParametre("fiche_famille_pages", dictParametres)

        # Info
        dlg = wx.MessageDialog(self, _(u"Fermez cette fiche pour appliquer les modifications demand�es !"), _(u"Information"), wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

class Dialog(wx.Dialog):
    def __init__(self, parent, IDfamille=None, dataRattach=None, AfficherMessagesOuverture=True):
        wx.Dialog.__init__(self, parent, id=-1, name="fiche_famille", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.dataRattach = dataRattach
        self.IDfamille = IDfamille
        self.DB = GestionDB.DB()
        if self.DB.echec == 1:
            raise Exception("Interrompu par absence de base de donnees")

        self.nouvelleFiche = False
        if IDfamille == None :
            self.CreateIDfamille(self.DB)
            self.nouvelleFiche = True
        # Adapte taille Police pour Linux
        from Utils import UTILS_Linux
        UTILS_Linux.AdaptePolice(self)

        # Composition
        self.sizer_composition_staticbox = wx.StaticBox(self, -1, _("Composition de la famille"))
        self.ctrl_composition = CTRL_Composition.Notebook(self, IDfamille=self.IDfamille)
        self.bouton_ajouter = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_modifier = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_supprimer = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_calendrier = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Calendrier.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_liens_famille = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Composition.png"), wx.BITMAP_TYPE_ANY))
        
        # Notebook
        self.notebook = Notebook(self, IDfamille=self.IDfamille)
        
        # Boutons de commande
        self.bouton_outils = CTRL_Bouton_image.CTRL(self, texte=_("Outils"), cheminImage=Chemins.GetStaticPath("Images/32x32/Configuration.png"))
        self.bouton_consommations = CTRL_Bouton_image.CTRL(self, texte=_("Consommations"), cheminImage=Chemins.GetStaticPath("Images/32x32/Calendrier.png"))
		#JB ajout bouton facturation
        self.bouton_famille = CTRL_Bouton_image.CTRL(self, texte=_("Famille"), cheminImage=Chemins.GetStaticPath("Images/32x32/Calculatrice.png"))
        self.bouton_facturation = CTRL_Bouton_image.CTRL(self, texte=_("Facturation"), cheminImage=Chemins.GetStaticPath("Images/32x32/Calculatrice.png"))
        self.bouton_saisie_reglement = CTRL_Bouton_image.CTRL(self, texte=_("Saisir un r�glement"), cheminImage=Chemins.GetStaticPath("Images/32x32/Reglement.png"))
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ok"), cheminImage=Chemins.GetStaticPath("Images/32x32/Valider.png"))
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Annuler"), cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png"))

        self.__set_properties()
        self.__do_layout()
        
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAjouterIndividu, self.bouton_ajouter)

        self.Bind(wx.EVT_BUTTON, self.OnBoutonOutils, self.bouton_outils)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonLiens, self.bouton_liens_famille)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonCalendrier, self.bouton_calendrier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonConsommations, self.bouton_consommations)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonFamille, self.bouton_famille)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonFacturation, self.bouton_facturation)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSaisieReglement, self.bouton_saisie_reglement)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAjouter, self.bouton_ajouter)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonModifier, self.bouton_modifier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSupprimer, self.bouton_supprimer)
        
        self.notebook.SetFocus() 
        
        # Si c'est une nouvelle fiche, on propose imm�diatement la cr�ation d'un individu
        if self.nouvelleFiche == True :
            wx.CallAfter(self.CreerPremierIndividu)

        # Cache le bouton de saisie d'un r�glement si l'onglet R�glements est cach�
        if ("reglements" in self.notebook.dictPages) == False :
            self.bouton_saisie_reglement.Show(False)

        # MAJ de l'onglet Informations
        self.notebook.GetPageAvecCode("informations").MAJ() 
        
        # MAJ CTRL composition
        self.ctrl_composition.MAJ()

        # Affiche les messages � l'ouverture de la fiche famille
        if AfficherMessagesOuverture == True :
            self.AfficheMessagesOuverture()

    def __set_properties(self):
        self.SetTitle(_("Fiche familiale n�%d") % self.IDfamille)
        self.bouton_ajouter.SetToolTip(_("Cliquez ici pour ajouter ou cr�er un nouvel individu"))
        self.bouton_modifier.SetToolTip(_("Cliquez ici pour modifier l'individu s�lectionn�"))
        self.bouton_supprimer.SetToolTip(_("Cliquez ici pour supprimer ou d�tacher l'individu s�lectionn�"))
        self.bouton_liens_famille.SetToolTip(_("Cliquez ici pour visualiser l'ensemble des liens de la famille"))
        self.bouton_calendrier.SetToolTip(_("Cliquez ici pour ouvrir la grille des consommations de l'individu s�lectionn�"))
        self.bouton_outils.SetToolTip(_("Cliquez ici pour acc�der aux outils"))
        self.bouton_consommations.SetToolTip(_("Cliquez ici pour consulter ou modifier les consommations d'un membre de la famille"))
        self.bouton_famille.SetToolTip(_("Cliquez ici pour acc�der � la facturation niveau famille"))
        self.bouton_facturation.SetToolTip(_("Cliquez ici pour acc�der � la facturation"))
        self.bouton_saisie_reglement.SetToolTip(_("Cliquez ici pour saisir rapidement un r�glement"))
        self.bouton_ok.SetToolTip(_("Cliquez ici pour valider et fermer"))
        self.bouton_annuler.SetToolTip(_("Cliquez ici pour annuler et fermer"))

        self.bouton_ajouter.SetSize(self.bouton_ajouter.GetBestSize())
        self.bouton_modifier.SetSize(self.bouton_modifier.GetBestSize())
        self.bouton_supprimer.SetSize(self.bouton_supprimer.GetBestSize())
        self.bouton_calendrier.SetSize(self.bouton_calendrier.GetBestSize())
        self.bouton_liens_famille.SetSize(self.bouton_liens_famille.GetBestSize())
        
        self.ctrl_composition.SetMinSize((-1, 300))
        self.notebook.SetMinSize((-1, 260))
        self.SetMinSize((960, 710))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        
        sizer_composition = wx.StaticBoxSizer(self.sizer_composition_staticbox, wx.VERTICAL)
        grid_sizer_composition = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_composition.Add(self.ctrl_composition, 0, wx.EXPAND, 0)
        
        grid_sizer_boutons_composition = wx.FlexGridSizer(rows=8, cols=1, vgap=5, hgap=5)
        grid_sizer_boutons_composition.Add(self.bouton_ajouter, 0, 0, 0)
        grid_sizer_boutons_composition.Add(self.bouton_modifier, 0, 0, 0)
        grid_sizer_boutons_composition.Add(self.bouton_supprimer, 0, 0, 0)
        grid_sizer_boutons_composition.Add((5, 5), 0, wx.EXPAND, 0)
        grid_sizer_boutons_composition.Add(self.bouton_calendrier, 0, 0, 0)
        grid_sizer_boutons_composition.Add((5, 5), 0, wx.EXPAND, 0)
        grid_sizer_boutons_composition.Add(self.bouton_liens_famille, 0, 0, 0)
        grid_sizer_composition.Add(grid_sizer_boutons_composition, 1, wx.EXPAND, 0)
        grid_sizer_composition.AddGrowableRow(0)
        grid_sizer_composition.AddGrowableCol(0)
        sizer_composition.Add(grid_sizer_composition, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_base.Add(sizer_composition, 1, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 10)
        
        grid_sizer_base.Add(self.notebook, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=10, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_outils, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_consommations, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_famille, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_facturation, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_saisie_reglement, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(4)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)

        grid_sizer_base.AddGrowableRow(0)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)

        self.SetSizer(grid_sizer_base)
##        grid_sizer_base.Fit(self)
        self.Layout()
        
        # D�termine la taille de la fen�tre
        taille_fenetre = UTILS_Config.GetParametre("taille_fenetre_famille")
        if taille_fenetre == None :
            self.SetSize((840, 700))
        elif taille_fenetre == (0, 0) or taille_fenetre == [0, 0]:
            self.Maximize(True)
        else:
            self.SetSize(taille_fenetre)        
        self.CenterOnScreen() 
    
    def CreerPremierIndividu(self):
        IDindividu = self.ctrl_composition.Ajouter()
        # Renseigne le premier individu comme titulaire H�lios
        if IDindividu != None :
            try :
                self.notebook.GetPageAvecCode("divers").ctrl_parametres.SetPropertyValue("titulaire_helios", IDindividu)
            except :
                pass
                
    def MAJpageActive(self):
        self.notebook.MAJpageActive() 
    
    def MAJpage(self, codePage=""):
        self.notebook.MAJpage(codePage) 

    def OnBoutonAjouter(self, event):
        self.ctrl_composition.Ajouter()
        
    def OnBoutonModifier(self, event):
        self.ctrl_composition.Modifier_selection()
        
    def OnBoutonSupprimer(self, event):
        self.ctrl_composition.Supprimer_selection()
    
    def OnBoutonLiens(self, event):
        from Dlg import DLG_Individu_liens
        dlg = DLG_Individu_liens.Dialog_liens(self, IDfamille=self.IDfamille)
        dlg.ShowModal() 
        dlg.Destroy()
        self.ctrl_composition.MAJ() 
    
    def OnBoutonCalendrier(self, event):
        self.ctrl_composition.Calendrier_selection()
        
    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Lafichefamiliale")
    
    def OnBoutonOutils(self, event):
        # Cr�ation du menu contextuel
        menuPop = wx.Menu()

        """
        # Item R�gler une facture
        item = wx.MenuItem(menuPop, 40, _("R�gler une facture"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Codebarre.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.MenuReglerFacture, id=40)
        
        menuPop.AppendSeparator() """

        # Item Editer un revel� de compte
        item = wx.MenuItem(menuPop, 90, _("Editer un relev� des prestations"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Euro.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.MenuImprimerReleve, id=90)

        # Item g�rer les lettrages
        item = wx.MenuItem(menuPop, 91, _("G�rer la ventilation des r�glements"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Depannage.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.AppelLettrage, id=91)

        # Item coh�rences
        item = wx.MenuItem(menuPop, 93, _("V�rifier la coh�rence des �critures"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Depannage.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.AppelCoherence, id=93)

        menuPop.AppendSeparator()

        # Item suivi des parrainages
        item = wx.MenuItem(menuPop, 92, _("Suivre et g�rer les parrainages"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Personnes.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.MenuParrainages, id=92)

        menuPop.AppendSeparator()

        # Item Editer Attestation de pr�sence
        item = wx.MenuItem(menuPop, 10, _("G�n�rer une attestation de pr�sence"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Generation.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.MenuGenererAttestation, id=10)
        
        # Item Liste Attestation de pr�sence
        item = wx.MenuItem(menuPop, 20, _("Liste des attestations de pr�sences g�n�r�es"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Facture.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.MenuListeAttestations, id=20)

        menuPop.AppendSeparator() 

        # Item Editer Lettre de rappel
        item = wx.MenuItem(menuPop, 110, _("G�n�rer une lettre de rappel"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Generation.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.MenuGenererRappel, id=110)
        
        # Item Liste Lettres de rappel
        item = wx.MenuItem(menuPop, 120, _("Liste des lettres de rappel g�n�r�es"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Facture.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.MenuListeRappels, id=120)

        menuPop.AppendSeparator() 

        # Item Liste des re�us �dit�s
        item = wx.MenuItem(menuPop, 300, _("Liste des re�us de r�glements �dit�s"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Note.png"), wx.BITMAP_TYPE_PNG))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.MenuListeRecus, id=300)

        item = wx.MenuItem(menuPop, 301, _("R�partition de la ventilation par r�glement"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Repartition.png"), wx.BITMAP_TYPE_PNG))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.MenuRepartitionVentilation, id=301)

        menuPop.AppendSeparator()
        
        # Item Edition d'�tiquettes et de badges
        item = wx.MenuItem(menuPop, 80, _("Edition d'�tiquettes et de badges"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Etiquette2.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.MenuEditionEtiquettes, id=80)
        
        menuPop.AppendSeparator() 
        
        # Item Historique
        item = wx.MenuItem(menuPop, 30, _("Historique"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Historique.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.MenuHistorique, id=30)
        
        item = wx.MenuItem(menuPop, 70, _("Chronologie"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Timeline.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.MenuChronologie, id=70)
        
        menuPop.AppendSeparator()

        # Item Envoyer un email
        menuPop.AppendSeparator()

        item = wx.MenuItem(menuPop, 200,
                           _(u"Envoyer un Email avec l'�diteur d'Emails de Noethys"))
        item.SetBitmap(
            wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Editeur_email.png"),
                      wx.BITMAP_TYPE_PNG))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.MenuEnvoyerMail, id=200)

        item = wx.MenuItem(menuPop, 210,
                           _(u"Envoyer un Email avec le client de messagerie par d�faut"))
        item.SetBitmap(
            wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Editeur_email.png"),
                      wx.BITMAP_TYPE_PNG))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.MenuEnvoyerMail, id=210)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def AppelLettrage(self,event):
        DLG_LettrageVentil.Lettrage(self.IDfamille)
        self.MAJpageActive()

    def AppelCoherence(self,event):
        GestionCoherence.DLG_Diagnostic(self.IDfamille)

    def MenuReglerFacture(self, event):
        from Ctrl import CTRL_Numfacture
        dlg = CTRL_Numfacture.Dialog(self, IDfamille=self.IDfamille)
        dlg.ShowModal() 
        dlg.Destroy()
    
    def GetIDcomptePayeur(self):
        req = """SELECT IDcompte_payeur
        FROM familles
        WHERE IDfamille = %d ;
        """ % self.IDfamille
        self.DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = self.DB.ResultatReq()
        IDcompte_payeur = 0
        try:
            IDcompte_payeur = listeDonnees[0][0]
        except:
            mess = GestionDB.Messages()
            ret = mess.Box(message="Pas de compte, v�rifier connection � la base")
        return IDcompte_payeur

    def MenuImprimerReleve(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_releve_prestations", "creer") == False : return
        # R�cup�ration du IDcompte_payeur
        IDcompte_payeur = self.GetIDcomptePayeur()
        # V�rification de la ventilation
        from Dlg import DLG_Verification_ventilation
        tracks = DLG_Verification_ventilation.Verification(IDcompte_payeur)
        if len(tracks) > 0 :
            dlg = wx.MessageDialog(self, _("Un ou plusieurs r�glements sont encore � ventiler.\n\nIl est conseill� de le faire avant d'�diter un relev� des prestations..."), _("Ventilation"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
        # Ouverture de la facturation
        #JB d�rout� pour une relev� reprenant ant les r�glements non affect�s
        dlg = DLG_Releve_prestations.Dialog(self, IDfamille=self.IDfamille)
        dlg.ShowModal()
        dlg.Destroy()

    def MenuParrainages(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("famille_factures", "creer") == False : return
        # V�rification de la ventilation
        from Gest import GestionPieces
        pGest = GestionPieces.Forfaits(self)
        ret = pGest.CoherenceParrainages(IDfamille=self.IDfamille,forcerGestion=True,DB=self.DB)
        del pGest

    def MenuGenererAttestation(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_attestation_presence", "creer") == False : return
        # V�rification de la ventilation
        from Dlg import DLG_Verification_ventilation
        IDcompte_payeur = self.GetIDcomptePayeur()
        tracks = DLG_Verification_ventilation.Verification(IDcompte_payeur)
        if len(tracks) > 0 :
            dlg = wx.MessageDialog(self, _("Un ou plusieurs r�glements sont encore � ventiler.\n\nVous devez obligatoirement effectuer cela avant d'�diter une attestation..."), _("Ventilation"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        # Ouverture de la facturation
        from Dlg import DLG_Impression_attestation
        dlg = DLG_Impression_attestation.Dialog(self, IDfamille=self.IDfamille)
        dlg.ShowModal()
        dlg.Destroy()

    def MenuListeAttestations(self, event):
        from Dlg import DLG_Liste_attestations
        dlg = DLG_Liste_attestations.Dialog(self, IDfamille=self.IDfamille)
        dlg.ShowModal() 
        dlg.Destroy()

    def MenuGenererRappel(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_lettre_rappel", "creer") == False : return
        # R�cup�ration du IDcompte_payeur
        IDcompte_payeur = self.GetIDcomptePayeur()
        # V�rification de la ventilation
        from Dlg import DLG_Verification_ventilation
        tracks = DLG_Verification_ventilation.Verification(IDcompte_payeur)
        if len(tracks) > 0 :
            dlg = wx.MessageDialog(self, _("Un ou plusieurs r�glements sont encore � ventiler.\n\nVous devez obligatoirement effectuer cela avant d'�diter une attestation..."), _("Ventilation"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        # Ouverture de la facturation
        from Dlg import DLG_Rappels_generation
        dlg = DLG_Rappels_generation.Dialog(self,self.IDfamille)
        #dlg.SetFamille(self.IDfamille)
        dlg.ShowModal()
        dlg.Destroy()

    def MenuListeRappels(self, event):
        from Dlg import DLG_Liste_rappels
        dlg = DLG_Liste_rappels.Dialog(self, IDcompte_payeur=self.GetIDcomptePayeur())
        dlg.ShowModal() 
        dlg.Destroy()

    def MenuListeRecus(self, event):
        from Dlg import DLG_Liste_recus
        dlg = DLG_Liste_recus.Dialog(self, IDfamille=self.IDfamille)
        dlg.ShowModal() 
        dlg.Destroy()

    def MenuRepartitionVentilation(self, event):
        from Dlg import DLG_Repartition
        dlg = DLG_Repartition.Dialog(self, IDfamille=self.IDfamille)
        dlg.ShowModal()
        dlg.Destroy()

    def OnBoutonConsommations(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("consommations_conso", "consulter") == False : return
        self.Sauvegarde()
        from Dlg import DLG_Grille
        dlg = DLG_Grille.Dialog(self, IDfamille=self.IDfamille, selectionTous=True)
        if dlg.ShowModal() == wx.ID_OK:
            self.MAJpageActive() 
        try :
            dlg.Destroy()
        except :
            pass

   #JB gestion du bouton Famille
    def OnBoutonFamille(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("famille_factures", "creer") == False :
            return
        self.Sauvegarde()
        IDcompte_payeur = self.GetIDcomptePayeur()
        dictDonnees = {'IDfamille': self.IDfamille,'IDcompte_payeur': IDcompte_payeur}
        #JB
        from Dlg import DLG_PrixFamille
        dlg = DLG_PrixFamille.DlgTarification(self,dictDonnees)
        dlg.ShowModal()
        self.MAJpageActive()
        try :
            dlg.Destroy()
        except :
            pass

    #JB gestion du bouton Facturation
    def OnBoutonFacturation(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("facturation_factures", "creer") == False :
            return
        self.Sauvegarde()
        IDcompte_payeur = self.GetIDcomptePayeur()
        dictDonnees = {'IDfamille': self.IDfamille,'IDcompte_payeur': IDcompte_payeur}
        #JB
        from Dlg import DLG_FacturationPieces
        dlg = DLG_FacturationPieces.Dialog(self,dictDonnees["IDcompte_payeur"])
        dlg.ShowModal()
        #if dlg.ShowModal() == wx.ID_OK:
        self.MAJpageActive()
        try :
            dlg.Destroy()
        except :
            pass

    def OuvrirGrilleIndividu(self, IDindividu=None):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("consommations_conso", "consulter") == False : return
        self.Sauvegarde()
        from Dlg import DLG_Grille
        dlg = DLG_Grille.Dialog(self, IDfamille=self.IDfamille, selectionIndividus=[IDindividu,])
        if dlg.ShowModal() == wx.ID_OK:
            self.MAJpageActive() 
        try :
            dlg.Destroy()
        except :
            pass
    
    def OuvrirFicheIndividu(self, IDindividu=None):
        self.ctrl_composition.Modifier_individu(IDindividu)
        
    def OnBoutonSaisieReglement(self, event):
        self.notebook.AffichePage("reglements")
        pageReglements = self.notebook.GetPageAvecCode("reglements")
        pageReglements.MAJ()
        pageReglements.OnBoutonAjouter(None)
    
    def ReglerFacture(self, IDfacture=None):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_reglements", "creer") == False : return
        self.notebook.AffichePage("reglements")
        pageReglements = self.notebook.GetPageAvecCode("reglements")
        pageReglements.MAJ()
        pageReglements.ReglerFacture(IDfacture)
        
    def OnBoutonAnnuler(self, event):
        self.Annuler()
    
    def OnClose(self, event):
        self.MemoriseTailleFenetre() 
        self.Annuler()
        
    def MemoriseTailleFenetre(self):
        # M�morisation du param�tre de la taille d'�cran
        if self.IsMaximized() == True :
            taille_fenetre = (0, 0)
        else:
            taille_fenetre = tuple(self.GetSize())
        UTILS_Config.SetParametre("taille_fenetre_famille", taille_fenetre)

    def Sauvegarde(self):
        # Validation des donn�es avant sauvegarde
        listePages = ("questionnaire", "caisse", "divers")
        for codePage in listePages :
            page = self.notebook.GetPageAvecCode(codePage)
            if page.majEffectuee == True and page.ValidationData() == False : 
                self.notebook.AffichePage(codePage)
                return False
        # Sauvegarde des donn�es
        for codePage in listePages :
            page = self.notebook.GetPageAvecCode(codePage)
            if page.majEffectuee == True :
                page.Sauvegarde()
        return True

    def OnBoutonOk(self, event):
        # Sauvegarde
        etat = self.Sauvegarde() 
        if etat == False :
            return
        # M�morise taille fen�tre
        self.MemoriseTailleFenetre()
        self.Final()

    def Annuler(self):
        """ Annulation des modifications """
        if self.nouvelleFiche == True :
            self.Final()
            return
        # Sauvegarde
        self.Sauvegarde()
        self.Final()

    def Final(self):
        # Fermeture de la fen�tre
        try :
            if not self.parent:
                GestionDB.AfficheConnexionsOuvertes()
            self.DB.Close(all=True)
            self.EndModal(wx.ID_OK)
        except Exception as err:
            print(("Erreur sortie fiche famille: ",err))
            self.EndModal(wx.ID_NONE)

    def CreateIDfamille(self,DB=None):
        """ Cr�e la fiche famille dans la base de donn�es afin d'obtenir un IDfamille et un IDcompte_payeur """
        self.IDfamille = CreateIDfamille(DB)
        IDcompte_payeur = self.GetIDcomptePayeur()
        # M�morise l'action dans l'historique
        UTILS_Historique.InsertActions([{
                "IDfamille" : self.IDfamille,
                "IDcategorie" : 4, 
                "action" : _("Cr�ation de la famille ID%d") % self.IDfamille,
                },])
    
    def SupprimerFamille(self,IDfamille=None):
        # si l'ID famille est envoy�, c'est pour confirmation de la juste navigation
        if IDfamille and IDfamille != self.IDfamille:
            wx.MessageBox("Probl�me de programmation\n\n incoh�rence IDfamille en DLG_Famille.SupprimerFamille","Impossible")
        # R�cup�ration du IDcompte_payeur
        req = """SELECT IDcompte_payeur FROM comptes_payeurs WHERE IDfamille=%d""" % self.IDfamille
        self.DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = self.DB.ResultatReq()
        mess = None
        try:
            IDcompte_payeur = listeDonnees[0][0]
            nblignes = 0
            for table in ('prestations','reglements','inscriptions'):
                req = """SELECT IDcompte_payeur
                        FROM %s
                        WHERE IDcompte_payeur=%d""" %(table, IDcompte_payeur)
                self.DB.ExecuterReq(req,MsgBox="ExecuterReq")
                recordset = self.DB.ResultatReq()
                nblignes += len(recordset)
            if nblignes == 0:
                """ Suppression de la fiche famille """
                # Suppression des tables rattach�es
                self.DB.ReqDEL("payeurs", "IDcompte_payeur", IDcompte_payeur)
                self.DB.ReqDEL("aides", "IDcompte_payeur", self.IDfamille)
                self.DB.ReqDEL("deductions", "IDcompte_payeur", IDcompte_payeur)
                self.DB.ReqDEL("rappels", "IDcompte_payeur", IDcompte_payeur)
                self.DB.ReqDEL("quotients", "IDfamille", self.IDfamille)
                self.DB.ReqDEL("attestations", "IDfamille", self.IDfamille)
                self.DB.ReqDEL("messages", "IDfamille", self.IDfamille)
                self.DB.ReqDEL("comptes_payeurs", "IDfamille", self.IDfamille)
                self.DB.ReqDEL("familles", "IDfamille", self.IDfamille)
                mess = _("La fiche famille a �t� supprim�e.")
            else: mess = _("La fiche famille a �t� conserv�e vide.")
        except: pass

        if mess:
            dlg = wx.MessageDialog(self, mess, _("Suppression"), wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
        #self.Destroy()

    def SupprimerFicheFamille(self,IDfamille=None):
            self.SupprimerFamille(IDfamille) # et affiche la suppression

    def OnBoutonAjouterIndividu(self, event):
        """ Cr�er ou rattacher un individu """
        IDindividu = 5
        IDcategorie = 2
        titulaire = 0
        # Enregistrement du rattachement
        listeDonnees = [
            ("IDindividu", IDindividu),
            ("IDfamille", self.IDfamille),
            ("IDcategorie", IDcategorie),
            ("titulaire", titulaire),
            ]
        IDrattachement = self.DB.ReqInsert("rattachements", listeDonnees)

    def MenuEditionEtiquettes(self, event):
        from Dlg import DLG_Impression_etiquettes
        dlg = DLG_Impression_etiquettes.Dialog(self, IDfamille=self.IDfamille)
        dlg.ShowModal() 
        dlg.Destroy()        
        
    def MenuHistorique(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_historique", "consulter") == False : return
        from Dlg import DLG_Historique
        dlg = DLG_Historique.Dialog(self, IDfamille=self.IDfamille)
        dlg.ShowModal() 
        dlg.Destroy()

    def MenuChronologie(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_chronologie", "consulter") == False : return
        from Dlg import DLG_Chronologie
        dlg = DLG_Chronologie.Dialog(self, IDfamille=self.IDfamille)
        dlg.ShowModal()
        dlg.Destroy()
    
    def MenuEnvoyerMail(self, event):
        """ Envoyer un Email """
        from Utils import UTILS_Envoi_email
        listeAdresses = UTILS_Envoi_email.GetAdresseFamille(self.IDfamille)
        if len(listeAdresses) == 0 :
            return
        
        # Depuis l'�diteur d'Emails de Noethys
        if event.GetId() == 200 :
            from Dlg import DLG_Mailer
            dlg = DLG_Mailer.Dialog(self)
            listeDonnees = []
            for adresse in listeAdresses :
                listeDonnees.append({"adresse" : adresse, "pieces" : [], "champs" : {},})
            dlg.SetDonnees(listeDonnees, modificationAutorisee=False)
            dlg.ShowModal() 
            dlg.Destroy()
        
        # Depuis le client de messagerie par d�faut
        if event.GetId() == 210 :
            FonctionsPerso.EnvoyerMail(adresses=listeAdresses, sujet="", message="")

    def AfficheMessagesOuverture(self):
        """ Affiche les messages � l'ouverture de la fiche famille """
        listeMessages = self.notebook.GetPageAvecCode("informations").GetListeMessages()
        for track in listeMessages :
            if track.rappel_famille == 1 :
                texteToaster = track.texte
                if track.priorite == "HAUTE" :
                    couleurFond="#FFA5A5"
                else:
                    couleurFond="#FDF095"
                self.AfficheToaster(titre="Message", texte=texteToaster, couleurFond=couleurFond)

    def AfficheToaster(self, titre=u"", texte=u"", taille=(200, 100), couleurFond="#F0FBED"):
        """ Affiche une bo�te de dialogue temporaire """
        largeur, hauteur = taille
        tb = Toaster.ToasterBox(wx.GetApp().GetTopWindow(), Toaster.TB_SIMPLE, Toaster.TB_DEFAULT_STYLE, Toaster.TB_ONTIME)  # TB_CAPTION
        tb.SetTitle(titre)
        tb.SetPopupSize((largeur, hauteur))
        largeurEcran, hauteurEcran = wx.ScreenDC().GetSizeTuple()
        tb.SetPopupPosition((largeurEcran - largeur - 10, hauteurEcran - hauteur - 50))
        tb.SetPopupPauseTime(3000)
        tb.SetPopupScrollSpeed(8)
        tb.SetPopupBackgroundColour(couleurFond)
        tb.SetPopupTextColour("#000000")
        tb.SetPopupText(texte)
        tb.Play()

if __name__ == "__main__":
    import os
    os.chdir("..")
    app = wx.App(0)
    import time
    heure_debut = time.time()
    # ramel 567; perez marc 1724; bartoOliv 1861; branco 4499;  bourrel 6191
    #7735 parrainage; 8107 multifactures; 709 Brunel jacques
    dialog_1 = Dialog(None, IDfamille= 9)
    print("Temps de chargement fiche famille =", time.time() - heure_debut)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()

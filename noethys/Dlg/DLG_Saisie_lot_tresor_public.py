#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-20 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import wx.html as html
import os
import six
import GestionDB
import datetime
import gzip
import shutil
import base64
import os.path
import wx.propgrid as wxpg
from Ctrl import CTRL_Propertygrid
from Ctrl import CTRL_Bandeau
from Utils import UTILS_Dates
from Ol import OL_Modes_reglements
from Ol import OL_PES_pieces
import FonctionsPerso
import wx.lib.dialogs as dialogs
import wx.lib.agw.hyperlink as Hyperlink
from Utils import UTILS_Facturation
from Utils import UTILS_Parametres
from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "�")

if 'phoenix' in wx.PlatformInfo:
    from wx.adv import CommandLinkButton
else :
    from wx import CommandLinkButton

FORMATS = [
    {"code": "pes", "label": _("PES v2 ORMC Recette"), "description": _("Export vers le logiciel H�lios du Tr�sor Public diffus� par la DGFIP.")},
    {"code": "magnus", "label": _("Magnus Berger-Levrault"), "description": _("Export vers le logiciel Magnus de la soci�t� Berger-Levrault.")},
    {"code": "jvs", "label": _("Millesime Online JVS"), "description": _("Export vers le logiciel Millesime Online de la soci�t� JVS-MAIRISTEM.")},
]

def GetFormatByCode(code=""):
    for dict_format in FORMATS:
        if dict_format["code"] == code:
            return dict_format
    return FORMATS[0]

def Supprime_accent(texte):
    liste = [ (u"�", "e"), (u"�", "e"), (u"�", "e"), (u"�", "e"), (u"�", "a"), (u"�", "u"), (u"�", "o"), (u"�", "c"), (u"�", "i"), (u"�", "i"),]
    for a, b in liste :
        texte = texte.replace(a, b)
        texte = texte.replace(a.upper(), b.upper())
    return texte

def GetMoisStr(numMois, majuscules=False, sansAccents=False) :
    listeMois = (u"_", _("janvier"), _("f�vrier"), _("mars"), _("avril"), _("mai"), _("juin"), _("juillet"), _("ao�t"), _("septembre"), _("octobre"), _("novembre"), _("d�cembre"))
    nom = listeMois[numMois]
    if sansAccents == True : 
        nom = Supprime_accent(nom)
    if majuscules == True :
        nom = nom.upper() 
    return nom    



class CTRL_Parametres(CTRL_Propertygrid.CTRL):
    def __init__(self, parent, IDlot=None):
        self.parent = parent
        self.IDlot = IDlot
        CTRL_Propertygrid.CTRL.__init__(self, parent)
        self.SetExtraStyle(wxpg.PG_EX_HELP_AS_TOOLTIPS)
        couleurFond = "#dcf7d4"
        self.SetCaptionBackgroundColour(couleurFond)
        self.Bind(wxpg.EVT_PG_CHANGED, self.OnPropGridChange)

    def Remplissage(self):
        pass

    def Importation(self):
        """ Importation des donn�es """
        pass

    def MAJ_comptes(self):
        DB = GestionDB.DB()
        req = """SELECT IDcompte, nom, numero, defaut, raison, code_etab, code_guichet, code_nne, cle_rib, cle_iban, iban, bic, code_ics
        FROM comptes_bancaires
        ORDER BY nom;"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        self.dictComptes = {}
        choix = wxpg.PGChoices()
        for IDcompte, nom, numero, defaut, raison, code_etab, code_guichet, code_nne, cle_rib, cle_iban, iban, bic, code_ics in listeDonnees :
            self.dictComptes[IDcompte] = { 
                "nom" : nom, "numero" : numero, "defaut" : defaut,
                "raison" : raison, "code_etab" : code_etab, "code_guichet" : code_guichet, 
                "code_nne" : code_nne, "cle_rib" : cle_rib, "cle_iban" : cle_iban,
                "iban" : iban, "bic" : bic, "code_ics" : code_ics,
                }
            if 'phoenix' in wx.PlatformInfo:
                choix.Add(label=nom, value=IDcompte)
            else:
                choix.Add(nom, IDcompte)
        propriete = self.GetPropertyByName("IDcompte")
        propriete.SetChoices(choix)
        self.RefreshProperty(propriete) 

    def MAJ_modes(self):
        DB = GestionDB.DB()
        req = """SELECT IDmode, label, numero_piece, nbre_chiffres, 
        frais_gestion, frais_montant, frais_pourcentage, frais_arrondi, frais_label, image
        FROM modes_reglements
        ORDER BY label;"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        self.dictModes = {}
        choix = wxpg.PGChoices()
        for IDmode, label, numero_piece, nbre_chiffres, frais_gestion, frais_montant, frais_pourcentage, frais_arrondi, frais_label, image in listeDonnees :
            self.dictModes[IDmode] = { 
                "label" : label, "numero_piece" : numero_piece, "nbre_chiffres" : nbre_chiffres,
                "frais_gestion" : frais_gestion, "frais_montant" : frais_montant, "frais_pourcentage" : frais_pourcentage, 
                "frais_arrondi" : frais_arrondi, "frais_label" : frais_label, "image" : image,
                }
            bmp = OL_Modes_reglements.GetImage(image)
            if 'phoenix' in wx.PlatformInfo:
                choix.Add(label=label, bitmap=bmp, value=IDmode)
            else:
                choix.Add(label, bmp, IDmode)
        propriete = self.GetPropertyByName("IDmode")
        propriete.SetChoices(choix)
        self.RefreshProperty(propriete) 


    def OnBoutonParametres(self, propriete=None):
        ancienneValeur = propriete.GetValue() 
        if propriete.GetName() == "IDcompte" :
            from Dlg import DLG_Comptes_bancaires
            dlg = DLG_Comptes_bancaires.Dialog(self)
            dlg.ShowModal()
            dlg.Destroy()
            self.MAJ_comptes() 
        if propriete.GetName() == "IDmode" :
            from Dlg import DLG_Modes_reglements
            dlg = DLG_Modes_reglements.Dialog(self)
            dlg.ShowModal()
            dlg.Destroy()
            self.MAJ_modes() 
        try :
            propriete.SetValue(ancienneValeur)
        except :
            pass

    def OnPropGridChange(self, event):
        propriete = event.GetProperty()
        if propriete.GetName() == "reglement_auto" :
            self.parent.ctrl_pieces.reglement_auto = propriete.GetValue()

    
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class CTRL_Infos(html.HtmlWindow):
    def __init__(self, parent, texte="", hauteur=32,  couleurFond=(255, 255, 255), style=0):
        html.HtmlWindow.__init__(self, parent, -1, style=style)
        self.parent = parent
        if "gtk2" in wx.PlatformInfo:
            self.SetStandardFonts()
        self.SetBorders(3)
        self.SetMinSize((-1, hauteur))
        self.couleurFond = couleurFond
        font = self.parent.GetFont()
        self.SetFont(font)
        self.SetLabel(texte)
    
    def SetLabel(self, texte=""):
        self.SetPage(u"""<BODY><FONT SIZE=2 COLOR='#000000'>%s</FONT></BODY>""" % texte)
        self.SetBackgroundColour(self.couleurFond)
    

# ---------------------------------------------------------------------------------------------------------------------------------------

class Hyperlien(Hyperlink.HyperLinkCtrl):
    def __init__(self, parent, id=-1, label="", infobulle="", URL=""):
        Hyperlink.HyperLinkCtrl.__init__(self, parent, id, label, URL=URL)
        self.parent = parent
        self.URL = URL
        self.AutoBrowse(False)
        self.SetColours("BLUE", "BLUE", "BLUE")
        self.SetUnderlines(False, False, True)
        self.SetBold(False)
        self.EnableRollover(True)
        self.SetToolTip(wx.ToolTip(infobulle))
        self.UpdateLink()
        self.DoPopup(False)
        self.Bind(Hyperlink.EVT_HYPERLINK_LEFT, self.OnLeftLink)
        
    def OnLeftLink(self, event):
        if self.URL == "selection_tout" :
            self.parent.ctrl_pieces.CocheTout() 
        if self.URL == "selection_rien" :
            self.parent.ctrl_pieces.CocheRien() 
        if self.URL == "etat_valide" :
            self.parent.ctrl_pieces.SetStatut("valide")
        if self.URL == "etat_attente" :
            self.parent.ctrl_pieces.SetStatut("attente")
        if self.URL == "etat_refus" :
            self.parent.ctrl_pieces.SetStatut("refus")
        if self.URL == "reglements_tout" :
            self.parent.ctrl_pieces.SetRegle(True)
        if self.URL == "reglements_rien" :
            self.parent.ctrl_pieces.SetRegle(False)
        if self.URL == "creer_mode" :
            self.parent.CreerMode()
        self.UpdateLink()





class DLG_Choix_format(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, name="DLG_Choix_format", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX)
        self.parent = parent
        self.format = None

        # Bandeau
        titre = _("S�lection du format")
        intro = _("Cliquez sur le format d'export souhait�.")
        self.SetTitle(titre)
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/32x32/Helios.png")

        self.liste_boutons = []
        for dict_format in FORMATS:
            ctrl = CommandLinkButton(self, -1, dict_format["label"], dict_format["description"], size=(200, -1))
            ctrl.SetMinSize((500, -1))
            self.Bind(wx.EVT_BUTTON, self.OnBoutonChoix, ctrl)
            self.liste_boutons.append({"id": ctrl.GetId(), "ctrl": ctrl, "dict_format": dict_format})

        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Annuler"), cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Obtenir de l'aide")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Annuler")))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)

        grid_sizer_contenu = wx.FlexGridSizer(rows=10, cols=1, vgap=10, hgap=10)
        for dict_ctrl in self.liste_boutons:
            grid_sizer_contenu.Add(dict_ctrl["ctrl"], 0, wx.EXPAND, 10)

        grid_sizer_contenu.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_contenu, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=3, vgap=10, hgap=10)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.SetMinSize(self.GetSize())
        self.CenterOnScreen()

    def OnBoutonChoix(self, event):
        for dict_ctrl in self.liste_boutons:
            if dict_ctrl["id"] == event.GetId():
                self.format = dict_ctrl["dict_format"]["code"]
                self.EndModal(wx.ID_OK)

    def GetFormat(self):
        return self.format

# ---------------------------------------------------------------------------------------------------------------------------------


class Dialog(wx.Dialog):
    def __init__(self, parent, IDlot=None, format=None, ctrl_parametres=None):
        wx.Dialog.__init__(self, parent, -1, name="DLG_Saisie_lot_tresor_public", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent  
        self.IDlot = IDlot
        self.format = format

        # G�n�ralit�s
        self.box_generalites_staticbox = wx.StaticBox(self, -1, _("Caract�ristiques"))

        self.label_format = wx.StaticText(self, -1, _("Format :"))
        self.ctrl_format = wx.TextCtrl(self, -1, GetFormatByCode(self.format)["label"])
        self.ctrl_format.Enable(False)

        self.label_nom = wx.StaticText(self, -1, _("Nom du lot :"))
        self.ctrl_nom = wx.TextCtrl(self, -1, "")
        self.ctrl_nom.SetMinSize((230, -1))
        self.label_observations = wx.StaticText(self, -1, _("Observations :"))
        self.ctrl_observations = wx.TextCtrl(self, -1, "", style=wx.TE_MULTILINE)
        self.label_verrouillage = wx.StaticText(self, -1, _("Verrouillage :"))
        self.ctrl_verrouillage = wx.CheckBox(self, -1, "")
        
        # Param�tres
        self.box_parametres_staticbox = wx.StaticBox(self, -1, _("Param�tres"))
        self.ctrl_parametres = ctrl_parametres(self, IDlot=self.IDlot)

        # Pi�ces
        self.box_pieces_staticbox = wx.StaticBox(self, -1, _("Pi�ces"))
        
        self.ctrl_pieces = OL_PES_pieces.ListView(self, id=-1, IDlot=self.IDlot, style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        self.ctrl_pieces.SetMinSize((50, 50)) 
        
        self.bouton_ajouter = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_modifier = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Modifier.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_supprimer = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_apercu = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Apercu.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_imprimer = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_ANY))
        
        
        self.label_actions = wx.StaticText(self, -1, _("Actions sur pr�l�vements coch�s :"))

        self.hyper_etat_attente = Hyperlien(self, label=_("Attente"), infobulle=_("Cliquez ici pour mettre en attente les pr�l�vements coch�s"), URL="etat_attente")
        self.label_separation_1 = wx.StaticText(self, -1, "|")
        self.hyper_etat_valide = Hyperlien(self, label=_("Valide"), infobulle=_("Cliquez ici pour valider les pr�l�vements coch�s"), URL="etat_valide")
        self.label_separation_2 = wx.StaticText(self, -1, "|")
        self.hyper_etat_refus = Hyperlien(self, label=_("Refus"), infobulle=_("Cliquez ici pour refuser les pr�l�vements coch�s"), URL="etat_refus")

        self.hyper_reglements_tout = Hyperlien(self, label=_("R�gler"), infobulle=_("Cliquez ici pour r�gler les pr�l�vements coch�s"), URL="reglements_tout")
        self.label_separation_3 = wx.StaticText(self, -1, "|")
        self.hyper_reglements_rien = Hyperlien(self, label=_("Ne pas r�gler"), infobulle=_("Cliquez ici pour ne pas r�gler les pr�l�vements coch�s"), URL="reglements_rien")

        self.hyper_selection_tout = Hyperlien(self, label=_("Tout cocher"), infobulle=_("Cliquez ici pour tout cocher la s�lection"), URL="selection_tout")
        self.label_separation_4 = wx.StaticText(self, -1, "|")
        self.hyper_selection_rien = Hyperlien(self, label=_("Tout d�cocher"), infobulle=_("Cliquez ici pour tout d�cocher la s�lection"), URL="selection_rien")

        self.ctrl_totaux = CTRL_Infos(self, hauteur=40, couleurFond="#F0FBED" , style=wx.html.HW_NO_SELECTION | wx.html.HW_SCROLLBAR_NEVER | wx.SUNKEN_BORDER)

        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_fichier = CTRL_Bouton_image.CTRL(self, texte=_("G�n�rer le fichier d'export %s") % GetFormatByCode(self.format)["label"], cheminImage="Images/32x32/Disk.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ok"), cheminImage="Images/32x32/Valider.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Annuler"), cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAjouter, self.bouton_ajouter)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonModifier, self.bouton_modifier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSupprimer, self.bouton_supprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonApercu, self.bouton_apercu)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonImprimer, self.bouton_imprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonFichier, self.bouton_fichier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)
        
        # Init contr�les
        self.Importation() 
        
        self.tracks = OL_PES_pieces.GetTracks(self.IDlot)
        self.ctrl_pieces.MAJ(tracks=self.tracks) 
        self.ctrl_pieces.MAJtotaux() 

    def __set_properties(self):
        self.SetTitle(_("Saisie d'un lot %s") % GetFormatByCode(self.format)["label"])
        self.ctrl_nom.SetToolTip(wx.ToolTip(_("Saisissez un nom pour ce lot (Ex : 'Janvier 2013', etc...). Nom interne � Noethys.")))
        self.ctrl_verrouillage.SetToolTip(wx.ToolTip(_("Cochez cette case pour verrouiller le lot lorsque vous consid�rez qu'il est finalis�")))
        self.ctrl_observations.SetToolTip(wx.ToolTip(_("Saisissez ici des observations sur ce lot")))
        self.bouton_ajouter.SetToolTip(wx.ToolTip(_("Cliquez ici pour ajouter une pi�ce")))
        self.bouton_modifier.SetToolTip(wx.ToolTip(_("Cliquez ici pour modifier la pi�ce s�lectionn�e dans la liste")))
        self.bouton_supprimer.SetToolTip(wx.ToolTip(_("Cliquez ici pour retirer la pi�ce s�lectionn�e dans la liste")))
        self.bouton_apercu.SetToolTip(wx.ToolTip(_("Cliquez ici pour afficher un aper�u avant impression de la liste des pi�ces")))
        self.bouton_imprimer.SetToolTip(wx.ToolTip(_("Cliquez ici pour imprimer la liste des pi�ces de ce lot")))
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici pour obtenir de l'aide")))
        self.bouton_fichier.SetToolTip(wx.ToolTip(_("Cliquez ici pour g�n�rer un fichier au format %s") % GetFormatByCode(self.format)["label"]))
        self.bouton_ok.SetToolTip(wx.ToolTip(_("Cliquez ici pour valider les donn�es")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Cliquez ici pour annuler")))
        self.SetMinSize((900, 780))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
                
        grid_sizer_haut = wx.FlexGridSizer(rows=1, cols=2, vgap=10, hgap=10)
        
        # G�n�ralit�s
        box_generalites = wx.StaticBoxSizer(self.box_generalites_staticbox, wx.VERTICAL)
        
        grid_sizer_generalites = wx.FlexGridSizer(rows=4, cols=2, vgap=10, hgap=10)
        grid_sizer_generalites.Add(self.label_format, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_generalites.Add(self.ctrl_format, 0, wx.EXPAND, 0)
        grid_sizer_generalites.Add(self.label_nom, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_generalites.Add(self.ctrl_nom, 0, wx.EXPAND, 0)
        grid_sizer_generalites.Add(self.label_observations, 0, wx.ALIGN_RIGHT, 0)
        grid_sizer_generalites.Add(self.ctrl_observations, 0, wx.EXPAND, 0)
        grid_sizer_generalites.Add(self.label_verrouillage, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_generalites.Add(self.ctrl_verrouillage, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        box_generalites.Add(grid_sizer_generalites, 1, wx.ALL|wx.EXPAND, 10)
        
        grid_sizer_generalites.AddGrowableRow(2)
        grid_sizer_haut.Add(box_generalites, 1, wx.EXPAND, 0)
        
        # Param�tres
        box_parametres = wx.StaticBoxSizer(self.box_parametres_staticbox, wx.VERTICAL)
        box_parametres.Add(self.ctrl_parametres, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_haut.Add(box_parametres, 1, wx.EXPAND, 0)

        grid_sizer_haut.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_haut, 1, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 10)
        
        # Pi�ces
        box_pieces = wx.StaticBoxSizer(self.box_pieces_staticbox, wx.VERTICAL)
        grid_sizer_pieces = wx.FlexGridSizer(rows=3, cols=2, vgap=5, hgap=5)
        grid_sizer_pieces.Add(self.ctrl_pieces, 1, wx.EXPAND, 0)
        
        grid_sizer_boutons_liste = wx.FlexGridSizer(rows=6, cols=1, vgap=5, hgap=5)
        grid_sizer_boutons_liste.Add(self.bouton_ajouter, 0, 0, 0)
        grid_sizer_boutons_liste.Add(self.bouton_modifier, 0, 0, 0)
        grid_sizer_boutons_liste.Add(self.bouton_supprimer, 0, 0, 0)
        grid_sizer_boutons_liste.Add((10, 10), 0, wx.EXPAND, 0)
        grid_sizer_boutons_liste.Add(self.bouton_apercu, 0, 0, 0)
        grid_sizer_boutons_liste.Add(self.bouton_imprimer, 0, 0, 0)
        
        grid_sizer_pieces.Add(grid_sizer_boutons_liste, 1, wx.EXPAND, 0)
        
        # Commandes
        grid_sizer_commandes = wx.FlexGridSizer(rows=1, cols=16, vgap=5, hgap=5)
        
        grid_sizer_commandes.Add(self.label_actions, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        
        grid_sizer_commandes.Add((10, 10), 0, wx.EXPAND, 0)
        
        grid_sizer_commandes.Add(self.hyper_etat_attente, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_commandes.Add(self.label_separation_1, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_commandes.Add(self.hyper_etat_valide, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_commandes.Add(self.label_separation_2, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_commandes.Add(self.hyper_etat_refus, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        grid_sizer_commandes.Add((10, 10), 0, wx.EXPAND, 0)
        
        grid_sizer_commandes.Add(self.hyper_reglements_tout, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_commandes.Add(self.label_separation_3, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_commandes.Add(self.hyper_reglements_rien, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        
        grid_sizer_commandes.Add((10, 10), 0, wx.EXPAND, 0)
        
        grid_sizer_commandes.Add(self.hyper_selection_tout, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_commandes.Add(self.label_separation_4, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_commandes.Add(self.hyper_selection_rien, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        grid_sizer_commandes.AddGrowableCol(10)
        
        grid_sizer_pieces.Add(grid_sizer_commandes, 1, wx.EXPAND, 0)
        
        grid_sizer_pieces.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_pieces.Add(self.ctrl_totaux, 0, wx.EXPAND, 0)
        grid_sizer_pieces.AddGrowableRow(0)
        grid_sizer_pieces.AddGrowableCol(0)
        box_pieces.Add(grid_sizer_pieces, 1, wx.ALL|wx.EXPAND, 10)
        
        grid_sizer_base.Add(box_pieces, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=6, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_fichier, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(2)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()
        
        wx.CallLater(0, self.Layout) # Contre pb d'affichage du wx.Choice
    
    def GetVerrouillage(self):
        return self.ctrl_verrouillage.GetValue() 
        
    def OnBoutonAjouter(self, event): 
        self.ctrl_pieces.Saisie_factures()

    def OnBoutonModifier(self, event): 
        self.ctrl_pieces.Modifier()

    def OnBoutonSupprimer(self, event): 
        self.ctrl_pieces.Supprimer()

    def OnBoutonApercu(self, event): 
        self.ctrl_pieces.Apercu()

    def OnBoutonImprimer(self, event): 
        self.ctrl_pieces.Imprimer()

    def OnBoutonAide(self, event=None): 
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("ExportversHelios")

    def OnBoutonAnnuler(self, event): 
        self.EndModal(wx.ID_CANCEL)

    def GetLabelParametres(self):
        """ Renvoie les param�tres pour impression """
        nom = self.ctrl_nom.GetValue()
        texte = _("Lot : '%s'") % nom
        return texte
    
    def Importation(self):
        """ Importation des donn�es """
        if self.IDlot == None :
            # Donn�es du dernier lot
            DB = GestionDB.DB()
            req = """SELECT reglement_auto, IDcompte, IDmode, exercice, mois, objet_dette, date_emission, date_prelevement, date_envoi, id_bordereau, id_poste, id_collectivite, code_collectivite, code_budget, code_prodloc, code_etab, prelevement_libelle, objet_piece, format, options
            FROM pes_lots
            WHERE format='%s'
            ORDER BY IDlot;""" % self.format
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            listeDonnees = DB.ResultatReq()
            DB.Close()
            if len(listeDonnees) == 0 :
                return
            reglement_auto, IDcompte, IDmode, exercice, mois, objet_dette, date_emission, date_prelevement, date_envoi, id_bordereau, id_poste, id_collectivite, code_collectivite, code_budget, code_prodloc, code_etab, prelevement_libelle, objet_piece, format, options = listeDonnees[-1]
            nom = ""
            verrouillage = False
            observations = ""

        else :
            # Importation
            DB = GestionDB.DB()
            req = """SELECT nom, verrouillage, observations, reglement_auto, IDcompte, IDmode, exercice, mois, objet_dette, date_emission, date_prelevement, date_envoi, id_bordereau, id_poste, id_collectivite, code_collectivite, code_budget, code_prodloc, code_etab, prelevement_libelle, objet_piece, format, options 
            FROM pes_lots
            WHERE IDlot=%d
            ;""" % self.IDlot
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            listeDonnees = DB.ResultatReq()
            DB.Close()
            if len(listeDonnees) == 0 :
                return
            nom, verrouillage, observations, reglement_auto, IDcompte, IDmode, exercice, mois, objet_dette, date_emission, date_prelevement, date_envoi, id_bordereau, id_poste, id_collectivite, code_collectivite, code_budget, code_prodloc, code_etab, prelevement_libelle, objet_piece, format, options = listeDonnees[0]

        # Attribution des donn�es aux contr�les
        self.ctrl_nom.SetValue(nom)
        self.ctrl_verrouillage.SetValue(verrouillage)
        self.ctrl_observations.SetValue(observations)
        if reglement_auto == 1 :
            self.ctrl_pieces.reglement_auto = True
        if prelevement_libelle in ("", None):
            prelevement_libelle = "{NOM_ORGANISATEUR} - {LIBELLE_FACTURE}"
        if objet_piece in ("", None):
            objet_piece = _("FACTURE NUM{NUM_FACTURE} {MOIS_LETTRES} {ANNEE}")
            
            
        listeValeurs = [
            ("exercice", exercice),
            ("mois", mois),
            ("objet_dette", objet_dette),
            ("date_emission", UTILS_Dates.DateEngEnDateDD(date_emission)),
            ("date_prelevement", UTILS_Dates.DateEngEnDateDD(date_prelevement)),
            ("date_envoi", UTILS_Dates.DateEngEnDateDD(date_envoi)),
            ("id_bordereau", id_bordereau),
            ("id_poste", id_poste),
            ("id_collectivite", id_collectivite),
            ("code_collectivite", code_collectivite),
            ("code_budget", code_budget),
            ("code_prodloc", code_prodloc),
            ("code_etab", code_etab),
            ("reglement_auto", reglement_auto),
            ("IDcompte", IDcompte),
            ("IDmode", IDmode),
            ("prelevement_libelle", prelevement_libelle),
            ("objet_piece", objet_piece),
            ]
            
        for code, valeur in listeValeurs:
            try:
                self.ctrl_parametres.SetPropertyValue(code, valeur)
            except:
                pass

    def ValidationDonnees(self):
        """ V�rifie que les donn�es saisies sont exactes """
        # G�n�ralit�s
        nom = self.ctrl_nom.GetValue()
        if nom == "" :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement saisir un nom de lot (Ex : 'Janvier 2013'...) !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_nom.SetFocus() 
            return False
 
        for caract in nom :
            if caract in ("_",) :
                dlg = wx.MessageDialog(self, _("Le caract�re '%s' n'est pas autoris� dans le nom du lot !") % caract, _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                self.ctrl_nom.SetFocus() 
                return False
       
        # V�rifie que le nom n'est pas d�j� attribu�
        if self.IDlot == None :
            IDlotTemp = 0
        else :
            IDlotTemp = self.IDlot
        DB = GestionDB.DB()
        req = """SELECT IDlot, nom
        FROM pes_lots
        WHERE nom='%s' AND IDlot!=%d;""" % (nom, IDlotTemp)
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if len(listeDonnees) > 0 :
            dlg = wx.MessageDialog(self, _("Ce nom de lot a d�j� �t� attribu� � un autre lot.\n\nChaque lot doit avoir un nom unique. Changez le nom."), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_nom.SetFocus() 
            return False
        
        observations = self.ctrl_observations.GetValue()
        
        if self.ctrl_verrouillage.GetValue() == True :
            verrouillage = 1
        else :
            verrouillage = 0

        # R�cup�ration des donn�es du CTRL Param�tres
        exercice = self.ctrl_parametres.GetPropertyValue("exercice")
        mois = self.ctrl_parametres.GetPropertyValue("mois")
        objet_dette = self.ctrl_parametres.GetPropertyValue("objet_dette")
        date_emission = self.ctrl_parametres.GetPropertyValue("date_emission")
        date_prelevement = self.ctrl_parametres.GetPropertyValue("date_prelevement")
        date_envoi = self.ctrl_parametres.GetPropertyValue("date_envoi")
        id_bordereau = self.ctrl_parametres.GetPropertyValue("id_bordereau")
        id_poste = self.ctrl_parametres.GetPropertyValue("id_poste")
        id_collectivite = self.ctrl_parametres.GetPropertyValue("id_collectivite")
        code_collectivite = self.ctrl_parametres.GetPropertyValue("code_collectivite")
        code_budget = self.ctrl_parametres.GetPropertyValue("code_budget")
        code_prodloc = self.ctrl_parametres.GetPropertyValue("code_prodloc")
        code_etab = self.ctrl_parametres.GetPropertyValue("code_etab")
        reglement_auto = int(self.ctrl_parametres.GetPropertyValue("reglement_auto"))
        IDcompte = self.ctrl_parametres.GetPropertyValue("IDcompte")
        IDmode = self.ctrl_parametres.GetPropertyValue("IDmode")
        
        # V�rification du compte � cr�diter
        if reglement_auto == 1 :
            if IDcompte == None :
                dlg = wx.MessageDialog(self, _("Vous devez obligatoirement s�lectionner un compte � cr�diter !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return False
            if IDmode == None :
                dlg = wx.MessageDialog(self, _("Vous devez obligatoirement s�lectionner un mode de r�glement pour le r�glement automatique !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return False

        # V�rification des param�tres du bordereau
        listeVerifications = [
            (exercice, "exercice", _("l'ann�e de l'exercice")),
            (mois, "mois", _("le mois")),
            (objet_dette, "objet_dette", _("l'objet de la dette")),
            (date_emission, "date_emission", _("la date d'�mission")),
            (date_prelevement, "date_prelevement", _("la date souhait�e du pr�l�vement")),
            (date_envoi, "date_envoi", _("la date d'envoi")),
            (id_bordereau, "id_bordereau", _("l'ID bordereau")),
            (id_poste, "id_poste", _("l'ID poste")),
            (id_collectivite, "id_collectivite", _("l'ID collectivit�")),
            (code_collectivite, "code_collectivite", _("le Code Collectivit�")),
            (code_budget, "code_budget", _("le Code Bugdet")),
            (code_prodloc, "code_prodloc", _("le code Produit Local")),
            (code_etab, "code_etab", _("le code Etablissement")),
            ]
            
        for donnee, code, label in listeVerifications :
            if donnee == None or donnee == "" :
                dlg = wx.MessageDialog(self, _("Vous devez obligatoirement saisir %s dans les param�tres du lot !") % label, _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return False

            if code == "id_bordereau" :
                try :
                    test = int(donnee) 
                except :
                    dlg = wx.MessageDialog(self, _("Vous devez saisir une valeur num�rique valide pour le param�tre de bordereau 'ID Bordereau' !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
                    dlg.ShowModal()
                    dlg.Destroy()
                    return False

            if code == "id_collectivite" :
                try :
                    test = int(donnee) 
                except :
                    dlg = wx.MessageDialog(self, _("Vous devez saisir une valeur num�rique valide pour le param�tre de bordereau 'ID Collectivit�' !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
                    dlg.ShowModal()
                    dlg.Destroy()
                    return False



        # V�rification des pi�ces
        listeErreurs = []
        listeTemp1 = []
        for track in self.ctrl_pieces.GetObjects() :

            if track.analysePiece == False :
                listeErreurs.append(_("- Facture n�%s : %s") % (track.IDfacture, track.analysePieceTexte))
                
            # V�rifie qu'un OOFF ou un FRST n'est pas attribu� 2 fois � un seul mandat
            if track.prelevement == 1 :
                if track.prelevement_sequence in ("OOFF", "FRST") :
                    key = (track.prelevement_IDmandat, track.prelevement_sequence)
                    if key in listeTemp1 :
                        if track.prelevement_sequence == "OOFF" : 
                            listeErreurs.append(_("- Facture n�%s : Le mandat n�%s de type ponctuel a d�j� �t� utilis� une fois !") % (track.IDfacture, track.prelevement_IDmandat))
                        if track.prelevement_sequence == "FRST" : 
                            listeErreurs.append(_("- Facture n�%s : Mandat n�%s d�j� initialis�. La s�quence doit �tre d�finie sur 'RCUR' !") % (track.IDfacture, track.prelevement_IDmandat))
                    listeTemp1.append(key)
            
        if len(listeErreurs) > 0 :
            message1 = _("Le bordereau ne peut �tre valid� en raison des erreurs suivantes :")
            message2 = "\n".join(listeErreurs)
            dlg = dialogs.MultiMessageDialog(self, message1, caption=_("Erreur"), msg2=message2, style = wx.ICON_EXCLAMATION |wx.OK, icon=None, btnLabels={wx.ID_OK : _("Ok")})
            reponse = dlg.ShowModal() 
            dlg.Destroy() 
            return False

        return True
    
    def Memorisation_parametres(self):
        """ Est surcharg�e """
        pass

    def OnBoutonOk(self, event): 
        # Validation des donn�es
        if self.ValidationDonnees() == False :
            return
        
        if self.ctrl_verrouillage.GetValue() == False :
            dlg = wx.MessageDialog(self, _("Pour cl�turer le traitement d'un lot, vous devez valider ou refuser les pi�ces puis verrouiller le lot.\n\nSouhaitez-vous le faire maintenant ?"), _("Information"), wx.YES_NO|wx.CANCEL|wx.NO_DEFAULT|wx.ICON_INFORMATION)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse != wx.ID_NO :
                return
            
        # R�cup�ration des donn�es
        nom = self.ctrl_nom.GetValue()
        observations = self.ctrl_observations.GetValue()
        if self.ctrl_verrouillage.GetValue() == True :
            verrouillage = 1
        else :
            verrouillage = 0

        exercice = self.ctrl_parametres.GetPropertyValue("exercice")
        mois = self.ctrl_parametres.GetPropertyValue("mois")
        objet_dette = self.ctrl_parametres.GetPropertyValue("objet_dette")
        if 'phoenix' in wx.PlatformInfo:
            date_emission = self.ctrl_parametres.GetPropertyValue("date_emission").FormatISODate()
            date_prelevement = self.ctrl_parametres.GetPropertyValue("date_prelevement").FormatISODate()
            date_envoi = self.ctrl_parametres.GetPropertyValue("date_envoi").FormatISODate()
        else:
            date_emission = self.ctrl_parametres.GetPropertyValue("date_emission").strftime("%Y-%m-%d")
            date_prelevement = self.ctrl_parametres.GetPropertyValue("date_prelevement").strftime("%Y-%m-%d")
            date_envoi = self.ctrl_parametres.GetPropertyValue("date_envoi").strftime("%Y-%m-%d")
        try:
            id_bordereau = self.ctrl_parametres.GetPropertyValue("id_bordereau")
        except:
            id_bordereau = None
        id_poste = self.ctrl_parametres.GetPropertyValue("id_poste")
        try:
            id_collectivite = self.ctrl_parametres.GetPropertyValue("id_collectivite")
        except:
            id_collectivite = None
        code_collectivite = self.ctrl_parametres.GetPropertyValue("code_collectivite")
        code_budget = self.ctrl_parametres.GetPropertyValue("code_budget")
        code_prodloc = self.ctrl_parametres.GetPropertyValue("code_prodloc")
        try:
            code_etab = self.ctrl_parametres.GetPropertyValue("code_etab")
        except:
            code_etab = None
        reglement_auto = int(self.ctrl_parametres.GetPropertyValue("reglement_auto"))
        IDcompte = self.ctrl_parametres.GetPropertyValue("IDcompte")
        IDmode = self.ctrl_parametres.GetPropertyValue("IDmode")
        prelevement_libelle = self.ctrl_parametres.GetPropertyValue("prelevement_libelle")
        objet_piece = self.ctrl_parametres.GetPropertyValue("objet_piece")

        # Sauvegarde du lot
        listeDonnees = [
            ("nom", nom ),
            ("verrouillage", verrouillage),
            ("observations", observations),
            ("reglement_auto", reglement_auto),
            ("IDcompte", IDcompte),
            ("IDmode", IDmode),
            ("exercice", exercice),
            ("mois", mois),
            ("objet_dette", objet_dette),
            ("date_emission", date_emission),
            ("date_prelevement", date_prelevement),
            ("date_envoi", date_envoi),
            ("id_bordereau", id_bordereau),
            ("id_poste", id_poste),
            ("id_collectivite", id_collectivite),
            ("code_collectivite", code_collectivite),
            ("code_budget", code_budget),
            ("code_prodloc", code_prodloc),
            ("code_etab", code_etab),
            ("prelevement_libelle", prelevement_libelle),
            ("objet_piece", objet_piece),
            ("format", self.format),
            ]

        DB = GestionDB.DB()
        if self.IDlot == None :
            # Ajout
            self.IDlot = DB.ReqInsert("pes_lots", listeDonnees)
        else :
            # Modification
            DB.ReqMAJ("pes_lots", listeDonnees, "IDlot", self.IDlot)
        DB.Close() 
        
        # Sauvegarde des pr�l�vements du lot
        self.ctrl_pieces.Sauvegarde(IDlot=self.IDlot, datePrelevement=date_prelevement, IDcompte=IDcompte, IDmode=IDmode) 

        # M�morisation des pr�f�rences
        self.Memorisation_parametres()

        # Fermeture
        self.EndModal(wx.ID_OK)

    def GetIDlot(self):
        return self.IDlot

    def Assistant(self, filtres=[], nomLot=None):
        # Saisie du titre du lot
        if nomLot != None :
            self.ctrl_nom.SetValue(nomLot)       
        
        # Saisie des factures
        from Ctrl import CTRL_Liste_factures
        ctrl_factures = CTRL_Liste_factures.CTRL(self, filtres=filtres)
        ctrl_factures.ctrl_factures.CocheTout()
        tracksFactures = ctrl_factures.GetTracksCoches()
        self.ctrl_pieces.AjoutFactures(tracksFactures)
        
        # Coche tous les pr�l�vements
        self.ctrl_pieces.CocheTout()

        # Ferme ctrl_factures (utilise CallAfter pour �viter bug)
        wx.CallAfter(self.FermeAssistant, ctrl_factures)

    def FermeAssistant(self, ctrl_factures=None):
        ctrl_factures.Destroy()
        del ctrl_factures

    def OnBoutonFichier(self, event):
        """ G�n�ration d'un fichier normalis� """
        pass






if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dlg = Dialog(None, IDlot=1)
    filtres = [
        {"type": "numero_intervalle", "numero_min": 1983, "numero_max": 2051},
    ]
    dlg.Assistant(filtres=filtres, nomLot="Nom de lot exemple")
    app.SetTopWindow(dlg)
    dlg.ShowModal()
    app.MainLoop()

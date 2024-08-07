#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
import wx.html as html
import datetime, re, os
import GestionDB
import FonctionsPerso
from Ctrl import CTRL_Bouton_image
from Utils import UTILS_Envoi_email
from Utils import UTILS_Facturation
from Utils import UTILS_Dates
from Utils import UTILS_Texte
from Utils import UTILS_Dialogs
from Dlg import DLG_Badgeage_grille
from Utils.UTILS_Decimal import FloatToDecimal as FloatToDecimal
from Utils import UTILS_Config
from Utils import UTILS_Parametres
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "�")

if 'phoenix' in wx.PlatformInfo:
    from wx.adv import DatePickerCtrl, DP_DROPDOWN, EVT_DATE_CHANGED
else :
    from wx import DatePickerCtrl, DP_DROPDOWN, EVT_DATE_CHANGED


DICT_RENSEIGNEMENTS = {"nom" : "Nom", "prenom" : "Pr�nom", "date_naiss" : "Date de naissance", "cp_naiss" : "CP de naissance", "ville_naiss" : "Ville de naissance", "rue_resid" : "Adresse - Rue", "cp_resid" : "Adresse - CP", "ville_resid" : "Adresse - Ville",
                    "tel_domicile" : "T�l. Domicile", "tel_mobile" : "T�l. Mobile", "mail" : "Email", "profession" : "Profession", "employeur" : "Employeur", "travail_tel" : "T�l. Pro.", "travail_mail" : "Email Pro."}



class CTRL_Html(html.HtmlWindow):
    def __init__(self, parent, texte="", couleurFond=(255, 255, 255), style=wx.SIMPLE_BORDER):
        html.HtmlWindow.__init__(self, parent, -1, style=style)  # , style=wx.html.HW_NO_SELECTION | wx.html.HW_SCROLLBAR_NEVER | wx.NO_FULL_REPAINT_ON_RESIZE)
        self.parent = parent
        self.texte = ""
        if "gtk2" in wx.PlatformInfo:
            self.SetStandardFonts()
        self.SetBorders(3)
        self.couleurFond = couleurFond
        font = self.parent.GetFont()
        self.SetFont(font)
        self.SetTexte(texte)

    def SetTexte(self, texte=""):
        self.texte = texte
        self.SetPage(u"""<BODY><FONT SIZE=2 COLOR='#000000'>%s</FONT></BODY>""" % texte)
        #self.SetBackgroundColour(self.couleurFond)

    def GetTexte(self):
        return self.texte



class MyDatePickerCtrl(DatePickerCtrl):
    def __init__(self, parent):
        DatePickerCtrl.__init__(self, parent, -1, style=DP_DROPDOWN)
        self.parent = parent
        self.Bind(EVT_DATE_CHANGED, self.OnDateChanged)
        self.Bind(wx.EVT_CHILD_FOCUS, self.OnFocus)

    def OnFocus(self,event):
        event.Skip(False)       #�vite la propagation vers le 'PySwigObject' object

    def SetDate(self, dateDD=None):
        jour = dateDD.day
        mois = dateDD.month-1
        annee = dateDD.year
        date = wx.DateTime()
        date.Set(jour, mois, annee)
        self.SetValue(date)

    def GetDate(self):
        date = self.GetValue()
        dateDD = datetime.date(date.GetYear(), date.GetMonth()+1, date.GetDay())
        return dateDD

    def OnDateChanged(self, event):
        self.GetParent().Sauvegarde()


# -------------------------------------------------------------------------------------------------------------------------------------------

class CTRL_Choix_modele(wx.Choice):
    def __init__(self, parent, categorie=None):
        wx.Choice.__init__(self, parent, -1)
        self.parent = parent
        self.categorie = categorie
        self.defaut = None
        self.MAJ()

    def SetCategorie(self, categorie=""):
        self.categorie = categorie
        self.defaut = None
        self.MAJ()
        self.SetID(self.defaut)

    def MAJ(self):
        selectionActuelle = self.GetID()
        listeItems = self.GetListeDonnees()
        #if len(listeItems) == 0 :
        #    self.Enable(False)
        #else:
        #    self.Enable(True)
        self.SetItems(listeItems)
        # Re-s�lection apr�s MAJ
        if selectionActuelle != None :
            self.SetID(selectionActuelle)
        else:
            # S�lection par d�faut
            self.SetID(self.defaut)

    def GetListeDonnees(self):
        listeItems = []
        self.dictDonnees = {}
        if self.categorie == None :
            return listeItems

        DB = GestionDB.DB()
        req = """SELECT IDmodele, nom, description, defaut
        FROM modeles_emails
        WHERE categorie='%s'
        ORDER BY nom;""" % self.categorie
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        index = 0
        for IDmodele, nom, description, defaut in listeDonnees :
            listeItems.append(nom)
            self.dictDonnees[index] = {"ID" : IDmodele}
            if defaut == 1 :
                self.defaut = IDmodele
            index += 1
        return listeItems

    def SetID(self, ID=None):
        for index, values in self.dictDonnees.items():
            if values != None and values["ID"] == ID :
                 self.SetSelection(index)

    def GetID(self):
        index = self.GetSelection()
        if index == -1 : return None
        return self.dictDonnees[index]["ID"]

# -------------------------------------------------------------------------------------------------------------------------------------------

class CTRL_Solde(wx.TextCtrl):
    def __init__(self, parent):
        wx.TextCtrl.__init__(self, parent, id=-1, size=(90, -1), name="panel_solde", style=wx.ALIGN_RIGHT|wx.TE_READONLY)
        self.parent = parent
        font = self.GetFont()
        font.SetWeight(wx.BOLD)
        self.SetFont(font)
        self.SetToolTip(wx.ToolTip(_("Solde du compte de la famille")))

    def MAJ(self, IDfamille=None):
        if IDfamille == None :
            self.SetSolde(FloatToDecimal(0.0))
            return

        DB = GestionDB.DB()
        req = """SELECT IDfamille, SUM(montant)
        FROM reglements
        LEFT JOIN comptes_payeurs ON comptes_payeurs.IDcompte_payeur = reglements.IDcompte_payeur
        WHERE IDfamille=%d
        GROUP BY IDfamille
        ;""" % IDfamille
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeReglements = DB.ResultatReq()
        dictReglements = {}
        for IDfamille, montant in listeReglements :
            if (IDfamille in dictReglements) == False :
                dictReglements[IDfamille] = FloatToDecimal(0.0)
                dictReglements[IDfamille] += FloatToDecimal(montant)

        # R�cup�ration des prestations
        req = """SELECT IDfamille, SUM(montant)
        FROM prestations
        WHERE IDfamille=%d
        GROUP BY IDfamille
        ;""" % IDfamille
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listePrestations = DB.ResultatReq()
        dict_soldes = {}
        for IDfamille, montant in listePrestations :
            montant = FloatToDecimal(montant)
            if (IDfamille in dictReglements) == True :
                regle = dictReglements[IDfamille]
            else :
                regle = FloatToDecimal(0.0)
            dict_soldes[IDfamille] = regle - montant

        DB.Close()

        # Affichage du solde
        if IDfamille in dict_soldes :
            solde = dict_soldes[IDfamille]
        else :
            solde = FloatToDecimal(0.0)
        self.SetSolde(solde)


    def SetSolde(self, montant=FloatToDecimal(0.0)):
        """ MAJ integrale du controle avec MAJ des donnees """
        if montant > FloatToDecimal(0.0):
            label = "+ %.2f %s" % (montant, SYMBOLE)
            self.SetBackgroundColour("#C4BCFC")  # Bleu
        elif montant == FloatToDecimal(0.0):
            label = "0.00 %s" % SYMBOLE
            self.SetBackgroundColour("#5DF020")  # Vert
        else:
            label = "- %.2f %s" % (-montant, SYMBOLE)
            self.SetBackgroundColour("#F81515")  # Rouge
        self.SetValue(label)
        self.Layout()
        self.Refresh()



# -------------------------------------------------------------------------------------------------------------------------------------------

class Dialog(wx.Dialog):
    def __init__(self, parent, track=None, tracks=[]):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.track = track
        self.tracks = tracks

        # Bandeau sp�cial
        self.panel_bandeau = wx.Panel(self, -1)
        self.panel_bandeau.SetBackgroundColour(wx.Colour(255, 255, 255))

        self.ctrl_image = wx.StaticBitmap(self.panel_bandeau, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/32x32/Calendrier_modifier.png"), wx.BITMAP_TYPE_ANY))
        self.label_action = wx.StaticText(self.panel_bandeau, -1, _("R�servation de dates"))
        self.label_action.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.ligne1 = wx.StaticLine(self.panel_bandeau, -1)
        self.label_horodatage = wx.StaticText(self.panel_bandeau, -1, _("Mardi 26 juillet a 14h10"))
        self.label_horodatage.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))

        # Navigation
        self.bouton_premier = wx.BitmapButton(self.panel_bandeau, 10, wx.Bitmap(Chemins.GetStaticPath(u"Images/32x32/Premier.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_precedent = wx.BitmapButton(self.panel_bandeau, 20, wx.Bitmap(Chemins.GetStaticPath(u"Images/32x32/Precedent.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_precedent.SetMinSize((60, -1))
        self.bouton_suivant = wx.BitmapButton(self.panel_bandeau, 30, wx.Bitmap(Chemins.GetStaticPath(u"Images/32x32/Suivant.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_suivant.SetMinSize((60, -1))
        self.bouton_dernier = wx.BitmapButton(self.panel_bandeau, 40, wx.Bitmap(Chemins.GetStaticPath(u"Images/32x32/Dernier.png"), wx.BITMAP_TYPE_ANY))
        self.ligne2 = wx.StaticLine(self.panel_bandeau, -1)

        # Demande
        self.box_demande_staticbox = wx.StaticBox(self, wx.ID_ANY, _("Demande"))

        self.label_famille = wx.StaticText(self, -1, _("Famille :"))
        self.ctrl_famille = wx.TextCtrl(self, -1, "", style=wx.TE_READONLY)
        self.ctrl_famille.SetBackgroundColour(wx.WHITE)
        font = self.ctrl_famille.GetFont()
        font.SetWeight(wx.BOLD)
        self.ctrl_famille.SetFont(font)

        self.bouton_famille = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Famille.png"), wx.BITMAP_TYPE_ANY))

        self.label_solde = wx.StaticText(self, -1, _("Solde :"))
        self.ctrl_solde = CTRL_Solde(self)

        self.label_description = wx.StaticText(self, -1, _("Description :"))
        self.ctrl_description = CTRL_Html(self, couleurFond=self.GetBackgroundColour())
        self.ctrl_description.SetMinSize((-1, 130))

        self.label_commentaire = wx.StaticText(self, -1, _("Commentaire :"))
        self.ctrl_commentaire = CTRL_Html(self, couleurFond=self.GetBackgroundColour())
        self.ctrl_commentaire.SetMinSize((-1, 40))

        self.label_informations = wx.StaticText(self, -1, _("Informations :"))
        self.ctrl_informations = CTRL_Html(self, couleurFond=self.GetBackgroundColour())
        self.ctrl_informations.SetMinSize((-1, 40))

        # Traitement
        self.box_traitement_staticbox = wx.StaticBox(self, wx.ID_ANY, _("Traitement"))

        self.label_etat = wx.StaticText(self, -1, _("Etat :"), style=wx.ALIGN_RIGHT)
        self.radio_attente = wx.RadioButton(self, -1, _("En attente"), style=wx.RB_GROUP)
        self.radio_validation = wx.RadioButton(self, -1, _("Trait� le"))
        self.ctrl_date_validation = MyDatePickerCtrl(self)

        self.image_email_reponse = wx.StaticBitmap(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Emails_exp.png"), wx.BITMAP_TYPE_ANY))
        self.label_email_reponse = wx.StaticText(self, -1, "")

        self.label_reponse = wx.StaticText(self, -1, _("R�ponse :"))
        self.ctrl_reponse = wx.TextCtrl(self, -1, "", style=wx.TE_MULTILINE)
        self.ctrl_reponse.SetMinSize((-1, 60))

        # Email
        self.label_email = wx.StaticText(self, -1, _("Email :"))
        self.bouton_envoyer = CTRL_Bouton_image.CTRL(self, texte=_("Envoyer"), cheminImage="Images/32x32/Emails_exp.png")
        self.bouton_editeur = CTRL_Bouton_image.CTRL(self, texte=_("Editeur d'Emails"), cheminImage="Images/32x32/Editeur_email.png")
        self.label_modele = wx.StaticText(self, -1, _("Mod�le :"))
        self.ctrl_modele_email = CTRL_Choix_modele(self, categorie=None)
        self.ctrl_modele_email.SetMinSize((280, -1))
        self.bouton_gestion_modeles = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Mecanisme.png"), wx.BITMAP_TYPE_ANY))

        # CTRL Grille des conso
        self.ctrl_grille = DLG_Badgeage_grille.CTRL(self)
        self.ctrl_grille.Show(False)

        # Commandes
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_automatique = CTRL_Bouton_image.CTRL(self, texte=_("Automatique"), cheminImage="Images/32x32/Magique.png")
        self.bouton_manuel = CTRL_Bouton_image.CTRL(self, texte=_("Manuel"), cheminImage="Images/32x32/Edition.png")
        self.bouton_fermer = CTRL_Bouton_image.CTRL(self, texte=_("Fermer"), cheminImage="Images/32x32/Fermer.png")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnNavigation, self.bouton_premier)
        self.Bind(wx.EVT_BUTTON, self.OnNavigation, self.bouton_precedent)
        self.Bind(wx.EVT_BUTTON, self.OnNavigation, self.bouton_suivant)
        self.Bind(wx.EVT_BUTTON, self.OnNavigation, self.bouton_dernier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonFamille, self.bouton_famille)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioEtat, self.radio_attente)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioEtat, self.radio_validation)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonEnvoyer, self.bouton_envoyer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonEditeur, self.bouton_editeur)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonModeles, self.bouton_gestion_modeles)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAutomatique, self.bouton_automatique)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonManuel, self.bouton_manuel)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonFermer, self.bouton_fermer)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # Init
        self.Importation()
        self.MAJ()


    def __set_properties(self):
        self.SetTitle(_("Traitement des demandes"))
        self.bouton_premier.SetToolTip(wx.ToolTip(_("Cliquez ici pour acc�der � la premi�re demande de la liste")))
        self.bouton_precedent.SetToolTip(wx.ToolTip(_("Cliquez ici pour acc�der � la demande pr�c�dente dans la liste")))
        self.bouton_suivant.SetToolTip(wx.ToolTip(_("Cliquez ici pour acc�der � la demande suivante dans la liste")))
        self.bouton_dernier.SetToolTip(wx.ToolTip(_("Cliquez ici pour acc�der � la derni�re demande de la liste")))
        self.bouton_famille.SetToolTip(wx.ToolTip(_("Cliquez ici pour ouvrir la fiche famille")))
        self.radio_attente.SetToolTip(wx.ToolTip(_("Demande en attente")))
        self.radio_validation.SetToolTip(wx.ToolTip(_("Demande trait�e")))
        self.ctrl_date_validation.SetToolTip(wx.ToolTip(_("Date de traitement de la demande")))
        self.ctrl_reponse.SetToolTip(wx.ToolTip(_("Cette r�ponse appara�tra sur le portail et dans l'email de confirmation (si vous utilisez le mot-cl� {DEMANDE_REPONSE} dans l'email). Cette r�ponse est g�n�r�e automatiquement par Noethys mais vous pouvez la modifier librement.")))
        self.bouton_envoyer.SetToolTip(wx.ToolTip(_("Cliquez ici pour envoyer directement un email de r�ponse � la famille sans passer par l'�diteur d'Emails.")))
        self.bouton_editeur.SetToolTip(wx.ToolTip(_("Cliquez ici pour ouvrir l'�diteur d'Email afin d'envoyer un email de r�ponse � la famille")))
        self.ctrl_modele_email.SetToolTip(wx.ToolTip(_("S�lectionnez un mod�le d'email")))
        self.bouton_gestion_modeles.SetToolTip(wx.ToolTip(_("Cliquez ici pour acc�der � la gestion des mod�les d'emails")))
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici pour obtenir de l'aide")))
        self.bouton_automatique.SetToolTip(wx.ToolTip(_("Cliquez ici pour lancer le traitement automatique de cette demande")))
        self.bouton_manuel.SetToolTip(wx.ToolTip(_("Cliquez ici pour lancer le traitement manuel de cette demande")))
        self.bouton_fermer.SetToolTip(wx.ToolTip(_("Cliquez ici pour fermer la fen�tre")))
        self.SetMinSize((800, 670))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=10, hgap=10)

        # Bandeau
        sizer_bandeau = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_bandeau = wx.FlexGridSizer(rows=1, cols=3, vgap=10, hgap=10)

        # Image
        grid_sizer_bandeau.Add(self.ctrl_image, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        # Titre
        sizer_titre = wx.BoxSizer(wx.VERTICAL)

        sizer_titre.Add(self.label_action, 0, 0, 0)
        sizer_titre.Add(self.ligne1, 0, wx.BOTTOM | wx.EXPAND | wx.TOP, 1)
        sizer_titre.Add(self.label_horodatage, 0, 0, 0)
        grid_sizer_bandeau.Add(sizer_titre, 1, wx.EXPAND, 0)

        # Navigation
        grid_sizer_navigation = wx.FlexGridSizer(rows=1, cols=4, vgap=5, hgap=5)
        grid_sizer_navigation.Add(self.bouton_premier, 0, 0, 0)
        grid_sizer_navigation.Add(self.bouton_precedent, 0, 0, 0)
        grid_sizer_navigation.Add(self.bouton_suivant, 0, 0, 0)
        grid_sizer_navigation.Add(self.bouton_dernier, 0, 0, 0)
        grid_sizer_bandeau.Add(grid_sizer_navigation, 1, wx.EXPAND, 0)

        grid_sizer_bandeau.AddGrowableCol(1)
        sizer_bandeau.Add(grid_sizer_bandeau, 1, wx.EXPAND | wx.ALL, 10)
        sizer_bandeau.Add(self.ligne2, 0, wx.EXPAND, 0)
        self.panel_bandeau.SetSizer(sizer_bandeau)
        grid_sizer_base.Add(self.panel_bandeau, 1, wx.EXPAND, 0)

        # Contenu
        grid_sizer_contenu = wx.FlexGridSizer(rows=2, cols=1, vgap=10, hgap=10)

        # Demande
        box_demande = wx.StaticBoxSizer(self.box_demande_staticbox, wx.VERTICAL)
        grid_sizer_demande = wx.FlexGridSizer(rows=4, cols=2, vgap=10, hgap=10)

        # Famille
        grid_sizer_demande.Add(self.label_famille, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 0)

        grid_sizer_famille = wx.FlexGridSizer(rows=1, cols=5, vgap=5, hgap=5)
        grid_sizer_famille.Add(self.ctrl_famille, 1, wx.EXPAND, 0)
        grid_sizer_famille.Add(self.bouton_famille, 0, 0, 0)
        grid_sizer_famille.Add( (20, 5), 0, 0, 0)
        grid_sizer_famille.Add(self.label_solde, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 0)
        grid_sizer_famille.Add(self.ctrl_solde, 0, 0, 0)
        grid_sizer_famille.AddGrowableCol(0)
        grid_sizer_demande.Add(grid_sizer_famille, 1, wx.EXPAND, 0)

        # Description
        grid_sizer_demande.Add(self.label_description, 0, wx.ALIGN_RIGHT, 0)
        grid_sizer_demande.Add(self.ctrl_description, 0, wx.EXPAND, 0)

        # Commentaire
        grid_sizer_demande.Add(self.label_commentaire, 0, wx.ALIGN_RIGHT, 0)
        grid_sizer_demande.Add(self.ctrl_commentaire, 0, wx.EXPAND, 0)

        # Informations
        grid_sizer_demande.Add(self.label_informations, 0, wx.ALIGN_RIGHT, 0)
        grid_sizer_demande.Add(self.ctrl_informations, 0, wx.EXPAND, 0)

        grid_sizer_demande.AddGrowableRow(1)
        grid_sizer_demande.AddGrowableCol(1)

        box_demande.Add(grid_sizer_demande, 1, wx.ALL | wx.EXPAND, 10)
        grid_sizer_contenu.Add(box_demande, 0, wx.EXPAND, 0)

        # Traitement
        box_traitement = wx.StaticBoxSizer(self.box_traitement_staticbox, wx.VERTICAL)
        grid_sizer_traitement = wx.FlexGridSizer(rows=3, cols=2, vgap=10, hgap=10)

        # Etat
        grid_sizer_traitement.Add(self.label_etat, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 0)
        self.label_etat.SetMinSize((self.label_commentaire.GetSize()[0], -1))

        self.grid_sizer_etat = wx.FlexGridSizer(rows=1, cols=6, vgap=5, hgap=5)
        self.grid_sizer_etat.Add(self.radio_attente, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        self.grid_sizer_etat.Add(self.radio_validation, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        self.grid_sizer_etat.Add(self.ctrl_date_validation, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        self.grid_sizer_etat.Add( (5, 5), 0, wx.EXPAND, 0)
        self.grid_sizer_etat.Add(self.image_email_reponse, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        self.grid_sizer_etat.Add(self.label_email_reponse, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        self.grid_sizer_etat.AddGrowableCol(3)
        grid_sizer_traitement.Add(self.grid_sizer_etat, 1, wx.EXPAND, 0)

        # R�ponse
        grid_sizer_traitement.Add(self.label_reponse, 0, wx.ALIGN_RIGHT, 0)
        grid_sizer_traitement.Add(self.ctrl_reponse, 0, wx.EXPAND, 0)

        # Email
        grid_sizer_traitement.Add( self.label_email, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)

        grid_sizer_email = wx.FlexGridSizer(rows=1, cols=6, vgap=5, hgap=5)
        grid_sizer_email.Add(self.bouton_envoyer, 0, wx.EXPAND, 0)
        grid_sizer_email.Add(self.bouton_editeur, 0, wx.EXPAND, 0)
        grid_sizer_email.Add( (5, 5), 0, 0, 0)
        grid_sizer_email.Add(self.label_modele, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_email.Add(self.ctrl_modele_email, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_email.Add(self.bouton_gestion_modeles, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        #grid_sizer_email.AddGrowableCol(2)
        grid_sizer_traitement.Add(grid_sizer_email, 1, wx.EXPAND, 0)

        grid_sizer_traitement.AddGrowableRow(1)
        grid_sizer_traitement.AddGrowableCol(1)

        box_traitement.Add(grid_sizer_traitement, 1, wx.ALL | wx.EXPAND, 10)
        grid_sizer_contenu.Add(box_traitement, 0, wx.EXPAND, 0)

        grid_sizer_contenu.AddGrowableRow(0)
        grid_sizer_contenu.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_contenu, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        grid_sizer_base.Add(self.ctrl_grille, 1, wx.ALL | wx.EXPAND, 10)

        # Commandes
        grid_sizer_commandes = wx.FlexGridSizer(rows=1, cols=5, vgap=10, hgap=10)
        grid_sizer_commandes.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_commandes.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_commandes.Add(self.bouton_automatique, 0, 0, 0)
        grid_sizer_commandes.Add(self.bouton_manuel, 0, 0, 0)
        grid_sizer_commandes.Add(self.bouton_fermer, 0, 0, 0)
        grid_sizer_commandes.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_commandes, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        UTILS_Dialogs.AjusteSizePerso(self, __file__)
        self.CenterOnScreen()

    def Importation(self):
        DB = GestionDB.DB()

        # R�cup�ration des unit�s de r�servations
        req = """SELECT IDunite, IDactivite, nom, unites_principales, unites_secondaires, ordre
        FROM portail_unites;"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        self.dictUnites = {}
        for IDunite, IDactivite, nom, unites_principales, unites_secondaires, ordre in listeDonnees :
            unites_principales = UTILS_Texte.ConvertStrToListe(unites_principales)
            unites_secondaires = UTILS_Texte.ConvertStrToListe(unites_secondaires)
            self.dictUnites[IDunite] = {
                "IDactivite" : IDactivite, "nom" : nom, "unites_principales" : unites_principales,
                "unites_secondaires" : unites_secondaires, "ordre" : ordre,
                }

        # R�cup�ration des activit�s
        req = """SELECT IDactivite, nom, portail_reservations_limite, portail_reservations_absenti
        FROM activites;"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        self.dictActivites = {}
        for IDactivite, nom, portail_reservations_limite, portail_reservations_absenti in listeDonnees :
            self.dictActivites[IDactivite] = {
                "nom" : nom, "portail_reservations_limite" : portail_reservations_limite,
                "portail_reservations_absenti" : portail_reservations_absenti,
                }

        DB.Close()

    def OnClose(self, event):
        UTILS_Dialogs.SaveSizePerso(self, __file__)
        self.Sauvegarde()
        event.Skip()

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Traiterlesdemandesduportail")

    def OnBoutonFermer(self, event):
        UTILS_Dialogs.SaveSizePerso(self, __file__)
        self.Sauvegarde()
        self.EndModal(wx.ID_CANCEL)

    def OnRadioEtat(self, event=None):
        self.ctrl_date_validation.Enable(self.radio_validation.GetValue())
        self.ctrl_reponse.Enable(self.radio_validation.GetValue())
        self.bouton_envoyer.Enable(self.radio_validation.GetValue())
        self.bouton_editeur.Enable(self.radio_validation.GetValue())
        self.label_modele.Enable(self.radio_validation.GetValue())
        self.ctrl_modele_email.Enable(self.radio_validation.GetValue())
        self.bouton_gestion_modeles.Enable(self.radio_validation.GetValue())
        if self.track.action != "paiement_en_ligne" :
            self.bouton_automatique.Enable(not self.radio_validation.GetValue())
        else :
            self.bouton_automatique.Enable(False)
        ##self.bouton_automatique.Enable(not self.radio_validation.GetValue())
        self.bouton_manuel.Enable(not self.radio_validation.GetValue())

        if self.radio_validation.GetValue() == True :
            self.panel_bandeau.SetBackgroundColour(wx.Colour(220, 255, 220))
        else :
            self.panel_bandeau.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.panel_bandeau.Refresh()

    def OnBoutonModeles(self, event):
        from Dlg import DLG_Modeles_emails
        dlg = DLG_Modeles_emails.Dialog(self, categorie=self.categorie_email)
        dlg.ShowModal()
        dlg.Destroy()
        ID = self.ctrl_modele_email.GetID()
        self.ctrl_modele_email.MAJ()
        self.ctrl_modele_email.SetID(ID)

    def Sauvegarde(self):
        if self.radio_validation.GetValue() == True :
            etat = "validation"
            if self.ctrl_reponse.GetValue() == "" :
                reponse = None
            else :
                reponse = self.ctrl_reponse.GetValue()
            traitement_date = self.ctrl_date_validation.GetDate()
            self.ctrl_date_validation.Enable(True)
            self.panel_bandeau.SetBackgroundColour(wx.Colour(220, 255, 220))
        else :
            etat = "attente"
            traitement_date = None
            reponse = None
            self.ctrl_date_validation.SetDate(datetime.date.today())
            self.ctrl_date_validation.Enable(False)
            self.panel_bandeau.SetBackgroundColour(wx.Colour(255, 255, 255))

        # MAJ du track
        self.track.reponse = reponse
        self.track.etat = etat
        self.track.traitement_date = traitement_date
        self.panel_bandeau.Refresh()
        self.track.Refresh()

        # Sauvegarde dans la base
        DB = GestionDB.DB()
        DB.ReqMAJ("portail_actions", [("etat", etat), ("reponse", reponse), ("traitement_date", traitement_date), ("email_date", self.track.email_date)], "IDaction", self.track.IDaction)
        DB.Close()

    def GetEtat(self):
        if self.radio_attente.GetValue() == True:
            return "attente"
        else:
            return "validation"

    def SetEtat(self, etat="attente", traitement_date=None):
        if etat == "attente" :
            self.radio_attente.SetValue(True)
        else :
            self.radio_validation.SetValue(True)
            if traitement_date != None :
                self.ctrl_date_validation.SetDate(traitement_date)
        self.OnRadioEtat()

    def MAJ(self):
        if self.track == None :
            return

        # Cat�gorie de l'action
        self.label_action.SetLabel(self.track.categorie_label)

        # Image de la cat�gorie
        dict_images = {
            "reglements" : "Reglement.png",
            "factures" : "Facture.png",
            "inscriptions" : "Activite.png",
            "reservations" : "Calendrier_modifier.png",
            "renseignements": "Cotisation.png",
            "locations": "Location.png",
            "pieces": "Piece.png",
            "compte": "Mecanisme.png",
            }
        self.ctrl_image.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/32x32/%s" % dict_images[self.track.categorie]), wx.BITMAP_TYPE_PNG))

        # Horodatage
        dt = UTILS_Dates.DateEngEnDateDDT(self.track.horodatage)
        self.label_horodatage.SetLabel(dt.strftime("%d/%m/%Y  %H:%M:%S"))

        # Famille
        self.ctrl_famille.SetValue(self.track.nom)
        self.ctrl_solde.MAJ(IDfamille=self.track.IDfamille)
        self.ctrl_solde.Enable(self.track.IDfamille != None)

        # Description
        description = self.track.description

        if self.track.categorie == "reservations" :

            # Recherche si d'autres r�servations existent pour le m�me individu et la m�me p�riode
            liste_demandes_avant = []
            liste_demandes_apres = []
            for track in self.tracks :
                if track.IDfamille == self.track.IDfamille and track.IDindividu == self.track.IDindividu and track.IDperiode == self.track.IDperiode :
                    if track.horodatage < self.track.horodatage :
                        liste_demandes_avant.append(track)
                    if track.horodatage > self.track.horodatage :
                        liste_demandes_apres.append(track)


            if len(liste_demandes_avant) > 1 :
                affiche_s_avant = "s"
            else :
                affiche_s_avant = ""
            if len(liste_demandes_apres) > 1:
                affiche_s_apres = "s"
            else :
                affiche_s_apres = ""

            if len(liste_demandes_avant) > 0 and len(liste_demandes_apres) == 0 :
                texte_autres_demandes = _("\n(Remarque : Il existe pour la m�me p�riode %d r�servation%s plus ancienne%s)") % (len(liste_demandes_avant), affiche_s_avant, affiche_s_avant)
            elif len(liste_demandes_avant) == 0 and len(liste_demandes_apres) > 0 :
                texte_autres_demandes = _("\n(Remarque : Il existe pour la m�me p�riode %d r�servation%s plus r�cente%s)") % (len(liste_demandes_apres), affiche_s_apres, affiche_s_apres)
            elif len(liste_demandes_avant) > 0 and len(liste_demandes_apres) > 0 :
                texte_autres_demandes = _("\n(Remarque : Il existe pour la m�me p�riode %d r�servation%s plus ancienne%s et %d plus r�cente%s)") % (len(liste_demandes_avant), affiche_s_avant, affiche_s_avant, len(liste_demandes_apres), affiche_s_apres)
            else :
                texte_autres_demandes = ""

            # Recherche le d�tail des r�servations associ�es
            DB = GestionDB.DB()
            req = """SELECT IDreservation, date, IDinscription, portail_reservations.IDunite, etat, portail_unites.nom
            FROM portail_reservations
            LEFT JOIN portail_unites ON portail_unites.IDunite = portail_reservations.IDunite
            WHERE IDaction=%d ORDER BY date, portail_reservations.IDunite;""" % self.track.IDaction
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            listeDonnees = DB.ResultatReq()
            DB.Close()
            liste_lignes = []
            for IDreservation, date, IDinscription, IDunite, etat, nom_unite in listeDonnees :
                date = UTILS_Dates.DateEngEnDateDD(date)
                if etat == 1 :
                    action = _("Ajout")
                else :
                    action = _("Suppression")
                ligne = _("<li>%s du %s (%s)</li>") % (action, UTILS_Dates.DateComplete(date), nom_unite)
                liste_lignes.append(ligne)

            description += " :"

            # Rajout du texte autres demandes
            if len(texte_autres_demandes) > 0 :
                description += "<br><FONT SIZE=2 COLOR='red'>%s</FONT>" % texte_autres_demandes

            # Rajout du d�tail des r�servations
            description += "<p><ul>%s</ul></p>" % "".join(liste_lignes)


        if self.track.categorie == "renseignements" :

            # Recherche le d�tail des renseignements associ�s
            DB = GestionDB.DB()
            req = """SELECT champ, valeur
            FROM portail_renseignements
            WHERE IDaction=%d;""" % self.track.IDaction
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            listeDonnees = DB.ResultatReq()
            DB.Close()
            liste_lignes = []
            for champ, valeur in listeDonnees :

                label = None
                if champ in DICT_RENSEIGNEMENTS:
                    label = _("<li>%s : %s</li>") % (DICT_RENSEIGNEMENTS[champ], valeur)

                if champ == "adresse_auto" and valeur != None:
                    IDindividuTemp = int(valeur)
                    DB = GestionDB.DB()
                    req = """SELECT nom, prenom FROM individus WHERE IDindividu=%d;""" % IDindividuTemp
                    DB.ExecuterReq(req,MsgBox="ExecuterReq")
                    listeIndividus = DB.ResultatReq()
                    DB.Close()
                    if len(listeIndividus) > 0 :
                        prenom = listeIndividus[0][1]
                    else :
                        prenom = "?"
                    label = _("<li>Adresse associ�e � celle de %s</li>") % prenom

                if label != None:
                    liste_lignes.append(label)

            description += " :"

            # Rajout du d�tail des renseignements
            description += "<p><ul>%s</ul></p>" % "".join(liste_lignes)

        if self.track.categorie == "locations" :

            # Recherche le d�tail des r�servations associ�es
            DB = GestionDB.DB()
            req = """SELECT IDreservation, date_debut, date_fin, partage, IDlocation, portail_reservations_locations.IDproduit, etat, produits.nom
            FROM portail_reservations_locations
            LEFT JOIN produits ON produits.IDproduit = portail_reservations_locations.IDproduit
            WHERE IDaction=%d ORDER BY date_debut;""" % self.track.IDaction
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            listeDonnees = DB.ResultatReq()
            DB.Close()
            liste_lignes = []
            for IDreservation, date_debut, date_fin, partage, IDlocation, IDproduit, etat, nom_produit in listeDonnees :
                date_debut = UTILS_Dates.DateEngEnDateDDT(date_debut)
                date_fin = UTILS_Dates.DateEngEnDateDDT(date_fin)
                if etat == "ajouter":
                    action = _("Ajout")
                elif etat == "modifier":
                    action = _("Modification")
                else :
                    action = _("Suppression")
                if partage:
                    nom_produit += " - Partage autoris�"
                ligne = _("<li>%s du %s au %s (%s)</li>") % (action, date_debut.strftime("%d/%m/%Y %H:%M"), date_fin.strftime("%d/%m/%Y %H:%M"), nom_produit)
                liste_lignes.append(ligne)

            description += " :"

            # Rajout du d�tail des r�servations
            description += "<p><ul>%s</ul></p>" % "".join(liste_lignes)

        self.ctrl_description.SetTexte(description)

        # Commentaire
        if self.track.commentaire != None :
            self.ctrl_commentaire.SetTexte(self.track.commentaire)

        # Informations
        self.MAJ_informations()

        # Etat
        self.SetEtat(self.track.etat, self.track.traitement_date)

        # R�ponse
        if self.track.reponse != None :
            reponse = self.track.reponse
        else :
            reponse = ""
        self.ctrl_reponse.SetValue(reponse)

        # Email
        if self.track.categorie == "reservations" : self.categorie_email = "portail_demande_reservation"
        elif self.track.categorie == "reglements" : self.categorie_email = "portail_demande_recu_reglement"
        elif self.track.categorie == "factures" : self.categorie_email = "portail_demande_facture"
        elif self.track.categorie == "inscriptions" : self.categorie_email = "portail_demande_inscription"
        elif self.track.categorie == "renseignements": self.categorie_email = "portail_demande_renseignement"
        elif self.track.categorie == "locations": self.categorie_email = "portail_demande_location"
        elif self.track.categorie == "pieces": self.categorie_email = "portail_demande_piece"
        else : self.categorie_email = None
        self.ctrl_modele_email.SetCategorie(self.categorie_email)

        self.MAJ_email_date()

        # S�lection du mod�le attribu� � la p�riode
        if self.track.categorie == "reservations" and self.track.periode_IDmodele != None :
            self.ctrl_modele_email.SetID(self.track.periode_IDmodele)

        # Navigation
        index = self.tracks.index(self.track)
        self.bouton_premier.Enable(index > 0)
        self.bouton_precedent.Enable(index > 0)
        self.bouton_suivant.Enable(index < len(self.tracks)-1)
        self.bouton_dernier.Enable(index < len(self.tracks)-1)

        # Titre de la fen�tre
        self.SetTitle(_("Traitement des demandes [%d/%d]") % (index+1, len(self.tracks)))

        # S�lection du track dans le listview
        self.Freeze()
        self.track.Select()
        self.Thaw()

    def MAJ_email_date(self):
        if self.track.email_date != None :
            self.image_email_reponse.Show(True)
            self.label_email_reponse.Show(True)
            self.label_email_reponse.SetLabel(_("Email de r�ponse envoy� le %s") % UTILS_Dates.DateDDEnFr(self.track.email_date))
        else :
            self.image_email_reponse.Show(False)
            self.label_email_reponse.Show(False)
        self.grid_sizer_etat.Layout()

    def MAJ_informations(self):
        texte = ""

        # Affiche le solde pour la p�riode de la r�servation
        if self.track.categorie == "reservations":
            # Calcule le solde actuel de la p�riode de r�servations
            traitement = Traitement(parent=self, track=self.track)
            montants = traitement.Get_montants_reservations()
            texte_solde = "%.2f %s" % (montants["solde"], SYMBOLE)
            if montants["solde"] > FloatToDecimal(0.0):
                texte_solde = "<FONT COLOR='red'>%s</FONT>" % texte_solde
            texte = _("Total pour la p�riode : %.2f %s | R�gl� : %.2f %s | Solde � r�gler : %s") % (montants["total"], SYMBOLE, montants["regle"], SYMBOLE, texte_solde)

        # Affiche la ventilation du paiement en ligne
        if self.track.categorie == "reglements" and self.track.action == "paiement_en_ligne":
            # Analyse de la ventilation
            dict_paiements = {"facture": {}, "periode": {}}
            for texte in self.track.ventilation.split(","):
                if texte[0] == "F": type_impaye = "facture"
                if texte[0] == "P": type_impaye = "periode"
                ID, montant = texte[1:].split("#")
                dict_paiements[type_impaye][int(ID)] = float(montant)

            DB = GestionDB.DB()

            # Importation des p�riodes
            if len(dict_paiements["periode"]) > 0:
                req = """SELECT IDperiode, portail_periodes.nom, activites.nom
                FROM portail_periodes
                LEFT JOIN activites ON activites.IDactivite = portail_periodes.IDactivite
                WHERE IDperiode IN %s;""" % GestionDB.ConvertConditionChaine(list(dict_paiements["periode"].keys()))
                DB.ExecuterReq(req,MsgBox="ExecuterReq")
                listePeriodes = DB.ResultatReq()
                dict_periodes = {}
                for IDperiode, nom_periode, nom_activite in listePeriodes :
                    dict_periodes[IDperiode] = "%s - %s" % (nom_periode, nom_activite)

            if len(dict_paiements["facture"]) > 0:
                req = """SELECT IDfacture, numero, date_debut, date_fin
                FROM factures
                WHERE IDfacture IN %s;""" % GestionDB.ConvertConditionChaine(list(dict_paiements["facture"].keys()))
                DB.ExecuterReq(req,MsgBox="ExecuterReq")
                listeFactures = DB.ResultatReq()
                dict_factures = {}
                for IDfacture, numero, date_debut, date_fin in listeFactures :
                    dict_factures[IDfacture] = _("Facture n�%s du %s au %s") % (numero, UTILS_Dates.DateEngFr(date_debut), UTILS_Dates.DateEngFr(date_fin))

            DB.Close()

            liste_textes = []
            for type_impaye in ("facture", "periode"):
                for ID, montant in dict_paiements[type_impaye].items():
                    texte = ""
                    if type_impaye == "periode":
                        if ID in dict_periodes:
                            texte = dict_periodes[ID]
                        else:
                            texte = _("P�riode inconnue")
                    if type_impaye == "facture":
                        if ID in dict_factures:
                            texte = dict_factures[ID]
                        else:
                            texte = _("Facture inconnue")
                    texte += " (%.2f %s)" % (montant, SYMBOLE)
                    liste_textes.append(texte)
            texte = _("En r�glement de : %s") % ", ".join(liste_textes)


        self.ctrl_informations.SetTexte(texte)

    def OnNavigation(self, event):
        self.Sauvegarde()

        ID = event.GetId()
        index = self.tracks.index(self.track)
        if ID == 10 :
            # Premier
            self.track = self.tracks[0]
        elif ID == 20 :
            # Pr�c�dent
            self.track = self.tracks[index-1]
        elif ID == 30 :
            # Suivant
            self.track = self.tracks[index+1]
        elif ID == 40 :
            # Dernier
            self.track = self.tracks[len(self.tracks)-1]

        self.MAJ()

    def OnBoutonFamille(self, event):
        from Dlg import DLG_Famille
        dlg = DLG_Famille.Dialog(self, self.track.IDfamille)
        dlg.ShowModal()
        dlg.Destroy()
        self.ctrl_solde.MAJ(IDfamille=self.track.IDfamille)
        self.MAJ_informations()

    def OnBoutonAutomatique(self, event):
        self.Traitement(mode="automatique")

    def OnBoutonManuel(self, event):
        self.Traitement(mode="manuel")

    def Traitement(self, mode="automatique"):
        traitement = Traitement(parent=self, track=self.track, mode=mode)
        resultat = traitement.Traiter()

        # Sauvegarde de l'�tat
        if resultat != False :
            if resultat["etat"] == True :

                # La demande a �t� valid�e
                self.SetEtat(etat="valide", traitement_date=datetime.date.today())

                # M�morisation de la r�ponse
                if "reponse" in resultat and resultat["reponse"] not in (None, "") :
                    self.ctrl_reponse.SetValue(resultat["reponse"])

                # Enregistrement de la demande
                self.Sauvegarde()

        # R�actualise le solde
        self.ctrl_solde.MAJ(IDfamille=self.track.IDfamille)
        self.MAJ_informations()

        # Automatique : Tout traiter
        # index = self.tracks.index(self.track)
        # if index < len(self.tracks) - 1:
        #     # Passage � la demande suivante
        #     self.track = self.tracks[index + 1]
        #     self.MAJ()
        #     # Traitement automatique de la demande
        #     self.Traitement(mode="automatique")
        #     # Envoi par email
        #     self.Envoyer(visible=False)



    def OnBoutonEnvoyer(self, event=None):
        self.Envoyer(visible=False)

    def OnBoutonEditeur(self, event=None):
        self.Envoyer(visible=True)

    def Envoyer(self, visible=True):
        """ Envoyer la r�ponse par email """
        if self.ctrl_reponse.GetValue() == "" :
            dlg = wx.MessageDialog(self, _("Vous n'avez saisi aucune r�ponse.\n\nSouhaitez-vous tout de m�me envoyer l'email ?"), _("Avertissement"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_QUESTION)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse != wx.ID_YES :
                return False

        IDmodele = self.ctrl_modele_email.GetID()
        if IDmodele == None :
            dlg = wx.MessageDialog(self, _("Vous devez s�lectionner un mod�le d'Email dans la liste propos�e !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        # Envoi par Email
        if self.track.categorie == "reservations" :
            nomDoc = FonctionsPerso.GenerationNomDoc("RESERVATIONS", "pdf")
        else :
            nomDoc = False

        resultat = UTILS_Envoi_email.EnvoiEmailFamille(parent=self, IDfamille=self.track.IDfamille, nomDoc=nomDoc, categorie=self.categorie_email, listeAdresses=[], visible=visible, log=self.track, CreationPDF=self.CreationPDF, IDmodele=IDmodele)

        # M�morise la date de l'envoi de l'email
        if resultat == True :
            self.track.email_date = datetime.date.today()
            self.MAJ_email_date()

    def CreationPDF(self, nomDoc="", afficherDoc=True):
        """ Cr�ation du PDF pour Email """

        # G�n�ration des champs de fusion de la demande
        dict_champs = {}
        dict_champs["{DEMANDE_HORODATAGE}"] = UTILS_Dates.DateEngEnDateDDT(self.track.horodatage).strftime("%d/%m/%Y %Hh%M")
        dict_champs["{DEMANDE_DESCRIPTION}"] = self.track.description
        dict_champs["{DEMANDE_COMMENTAIRE}"] = self.track.commentaire
        dict_champs["{DEMANDE_TRAITEMENT_DATE}"] = UTILS_Dates.DateDDEnFr(self.ctrl_date_validation.GetDate())
        dict_champs["{DEMANDE_REPONSE}"] = self.ctrl_reponse.GetValue()

        # G�n�ration des autres champs de fusion
        if self.track.categorie == "reservations" :
            dict_champs["{PERIODE_NOM}"] = self.track.periode_nom
            dict_champs["{PERIODE_DATE_DEBUT}"] = UTILS_Dates.DateDDEnFr(self.track.periode_date_debut)
            dict_champs["{PERIODE_DATE_FIN}"] = UTILS_Dates.DateDDEnFr(self.track.periode_date_fin)

            # G�n�ration du PDF des r�servations
            traitement = Traitement(parent=self, track=self.track)
            traitement.Init_grille(ctrl_grille=self.ctrl_grille)
            dict_champs_reservations = self.ctrl_grille.grille.CreationPDF(nomDoc=nomDoc, afficherDoc=afficherDoc)
            dict_champs.update(dict_champs_reservations)

            # Calcule le solde actuel de la p�riode de r�servations
            traitement = Traitement(parent=self, track=self.track)
            montants = traitement.Get_montants_reservations()
            dict_champs["{TOTAL}"] = "%.2f %s" % (montants["total"], SYMBOLE)
            dict_champs["{REGLE}"] = "%.2f %s" % (montants["regle"], SYMBOLE)
            dict_champs["{SOLDE}"] = "%.2f %s" % (montants["solde"], SYMBOLE)

        return dict_champs


# ----------------------------------------------------------------------------------------------

class Traitement():
    def __init__(self, parent=None, track=None, mode="automatique"):
        """ Mode = automatique ou manuel """
        self.parent = parent
        self.track = track
        self.mode = mode

        # R�cup�ration des param�tres de l'action
        self.dict_parametres = self.GetParametres()

    def EcritLog(self, message="", log_jumeau=None):
        self.track.EcritLog(message)
        if log_jumeau != None :
            log_jumeau.EcritLog(message)

    def GetParametres(self):
        """ R�cup�ration des param�tres de l'action """
        dict_parametres = {}
        if self.track.parametres and len(self.track.parametres) > 0 :
            for donnee in self.track.parametres.split("#") :
                donnees = donnee.split("=")
                if len(donnees) > 1 :
                    key, valeur = donnees
                    dict_parametres[key] = valeur
        return dict_parametres

    def Traiter(self):
        """ Traitement des actions en fonction de la cat�gorie """
        self.EcritLog(_("Lancement du traitement de la demande..."))
        resultat = False

        # Traitement des re�us de r�glements
        if self.track.categorie == "reglements" and self.track.action == "recevoir":
            resultat = self.Traitement_recus()

        # Traitement des paiements en ligne
        if self.track.categorie == "reglements" and self.track.action == "paiement_en_ligne":
            resultat = self.Traitement_paiement_en_ligne()

        # Traitement des factures
        if self.track.categorie == "factures" :
            resultat = self.Traitement_factures()

        # Traitement des inscriptions
        if self.track.categorie == "inscriptions" :
            resultat = self.Traitement_inscriptions()
            self.Verifier_ventilation()

        # Traitement des r�servations
        if self.track.categorie == "reservations" :
            resultat = self.Traitement_reservations()
            self.Verifier_ventilation()

        # Traitement des renseignements
        if self.track.categorie == "renseignements" :
            resultat = self.Traitement_renseignements()

        # Traitement des locations
        if self.track.categorie == "locations" :
            resultat = self.Traitement_locations()

        # Traitement des pi�ces
        if self.track.categorie == "pieces" :
            resultat = self.Traitement_pieces()

        # Traitement du compte
        if self.track.categorie == "compte" :
            resultat = self.Traitement_compte()

        self.EcritLog(_("Fin du traitement."))

        # S�lection de l'�tat 'Trait�'
        return resultat

    def Traitement_recus(self):
        # R�cup�ration des param�tres
        IDreglement = int(self.dict_parametres["IDreglement"])

        # Ouverture de la fen�tre d'�dition d'un re�u
        from Dlg import DLG_Impression_recu
        dlg_impression = DLG_Impression_recu.Dialog(self.parent, IDreglement=IDreglement)

        # Traitement manuel
        if self.mode == "manuel" :
            self.EcritLog(_("Ouverture de la fen�tre d'�dition d'un re�u."))
            if self.dict_parametres["methode_envoi"] == "email" :
                self.EcritLog(_("Veuillez envoyer ce re�u de r�glement par Email."))
                reponse = _("Re�u de r�glement envoy� par Email.")
            elif self.dict_parametres["methode_envoi"] == "courrier" :
                self.EcritLog(_("Veuillez imprimer le re�u de r�glement pour un envoi par courrier."))
                reponse = _("Re�u de r�glement envoy� par courrier.")
            else :
                self.EcritLog(_("Veuillez imprimer le re�u de r�glement pour un retrait sur site."))
                reponse = _("Re�u de r�glement disponible au retrait.")
            dlg_impression.ShowModal()
            dlg_impression.Destroy()

            return {"etat" : True, "reponse" : reponse}

        # Traitement automatique
        if self.mode == "automatique" :
            nomDoc = FonctionsPerso.GenerationNomDoc("RECU", "pdf")
            categorie = "recu_reglement"

            # Affichage du PDF pour envoi par courrier ou retrait sur site
            if self.dict_parametres["methode_envoi"] != "email" :
                message = _("Le re�u de r�glement va �tre g�n�r� au format PDF et ouvert dans votre lecteur de PDF.\n\n")
                if self.dict_parametres["methode_envoi"] == "courrier" :
                    message += _("Veuillez l'imprimer et l'envoyer par courrier.")
                else :
                    message += _("Veuillez l'imprimer et le conserver pour un retrait sur site.")
                dlg = wx.MessageDialog(self.parent, message, _("Impression d'un re�u"), wx.OK|wx.OK_DEFAULT|wx.CANCEL|wx.ICON_QUESTION)
                reponse = dlg.ShowModal()
                dlg.Destroy()
                if reponse == wx.ID_CANCEL :
                    self.EcritLog(_("Interruption du traitement par l'utilisateur."))
                    return False

                dictChamps = dlg_impression.CreationPDF(nomDoc=nomDoc, afficherDoc=True)
                if dictChamps == False :
                    dlg_impression.Destroy()
                    self.EcritLog(_("[ERREUR] La g�n�ration du re�u au format PDF a rencontr� une erreur."))
                    return False

                self.EcritLog(_("La g�n�ration du re�u est termin�e."))
                if self.dict_parametres["methode_envoi"] == "courrier" :
                    self.EcritLog(_("Veuillez imprimer le re�u de r�glement pour un envoi par courrier."))
                    reponse = _("Re�u de r�glement envoy� par courrier.")
                else :
                    self.EcritLog(_("Veuillez imprimer le re�u de r�glement pour un retrait sur site."))
                    reponse = _("Re�u de r�glement disponible au retrait.")

            # Envoi par Email
            if self.dict_parametres["methode_envoi"] == "email" :
                resultat = UTILS_Envoi_email.EnvoiEmailFamille(parent=dlg_impression, IDfamille=self.track.IDfamille, nomDoc=nomDoc, categorie=categorie, visible=False, log=self.track)
                reponse = _("Re�u de r�glement envoy� par Email.")

            # M�morisation de l'�dition du re�u
            dlg_impression.Sauvegarder(demander=False)
            dlg_impression.Destroy()

            return {"etat" : True, "reponse" : reponse}


    def Traitement_paiement_en_ligne(self):
        # R�cup�ration des param�tres
        IDmode_reglement = UTILS_Parametres.Parametres(mode="get", categorie="portail", nom="paiement_ligne_mode_reglement", valeur=None)
        if IDmode_reglement in ("None","",None):
            IDmode_reglement = None
        else:
            IDmode_reglement = int(IDmode_reglement)
        if IDmode_reglement in (None, 0):
            dlg = wx.MessageDialog(self.parent, _("Vous devez obligatoirement commencer par renseigner un mode de r�glement dans la configuration de Connecthys (Menu Outils > Connecthys > Rubrique Paiement en ligne) !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        IDfamille = self.track.IDfamille
        IDcompte_payeur = self.track.IDcompte_payeur
        IDpaiement = self.track.IDpaiement
        #factures_ID = self.dict_parametres["factures_ID"]
        systeme_paiement = self.dict_parametres.get("systeme_paiement", "Syst�me inconnu")
        IDtransaction = self.dict_parametres["IDtransaction"].split("_")[1] if "_" in self.dict_parametres["IDtransaction"] else self.dict_parametres["IDtransaction"]
        montant_reglement = float(self.dict_parametres["montant"])
        ventilation = self.track.ventilation

        # Analyse de la ventilation
        dict_paiements = {"facture": {}, "periode": {}}
        for texte in ventilation.split(","):
            if texte[0] == "F": type_impaye = "facture"
            if texte[0] == "P": type_impaye = "periode"
            ID, montant = texte[1:].split("#")
            dict_paiements[type_impaye][int(ID)] = float(montant)

        DB = GestionDB.DB()

        # Importation des p�riodes
        req = """SELECT IDperiode, IDactivite, date_debut, date_fin
        FROM portail_periodes
        WHERE IDperiode IN %s;""" % GestionDB.ConvertConditionChaine(list(dict_paiements["periode"].keys()))
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listePeriodes = DB.ResultatReq()
        dict_periodes = {}
        for IDperiode, IDactivite, date_debut, date_fin in listePeriodes :
            date_debut = UTILS_Dates.DateEngEnDateDD(date_debut)
            date_fin = UTILS_Dates.DateEngEnDateDD(date_fin)
            dict_periodes[IDperiode] = {"IDactivite": IDactivite, "date_debut": date_debut, "date_fin":date_fin}

        # On r�cup�re l'ID du compte bancaire de la r�gie si la facture est li�e a une r�gie
        IDcompte_bancaire = None
        num_piece = ""
        liste_paiements = [(montant_reglement, datetime.date.today())]

        if "payzen" in systeme_paiement :
            num_piece = IDtransaction
            vads_payment_config = self.dict_parametres.get("config", "SINGLE")
            if vads_payment_config.startswith("MULTI"):
                # Paiement en plusieurs fois
                liste_paiements = [(float(montant)/100, datetime.datetime.strptime(date, "%Y%m%d")) for date, montant in re.findall(r"([0-9]+)>([0-9]+)", vads_payment_config)]

        if "tipi" in systeme_paiement :
            IDfacture = list(dict_paiements.keys())[0]
            req = """SELECT factures_regies.IDcompte_bancaire
            FROM factures
            LEFT JOIN factures_regies ON factures_regies.IDregie = factures.IDregie
            WHERE IDfacture=%d;""" % IDfacture
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            IDcompte_bancaire = DB.ResultatReq()[0][0]
            num_piece = "auth_num-" + self.dict_parametres["numauto"]

        DB.Close()

        if len(liste_paiements) > 1:
            dlg = wx.MessageDialog(None, _("Il s'agit d'un paiement en %d fois. Noethys va donc vous demander de saisir successivement %d r�glements.") % (len(liste_paiements), len(liste_paiements)), _("Information"), wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()

        if self.mode == "manuel" :
            from Dlg import DLG_Saisie_reglement
            for index, (montant_paiement, date_paiement) in enumerate(liste_paiements, start=1):
                dlg = DLG_Saisie_reglement.Dialog(None, IDcompte_payeur=IDcompte_payeur, IDreglement=None)
                # dlg.SelectionneFacture(liste_IDfacture=list(dict_paiements["facture"].keys()))
                dlg.ctrl_date.SetDate(str(date_paiement))
                dlg.ctrl_montant.SetMontant(montant_paiement)
                dlg.ctrl_numero.SetValue(num_piece)
                dlg.ctrl_mode.SetID(IDmode_reglement)
                dlg.OnChoixMode(None)
                observations = _("Transaction n�%s sur %s (IDpaiement %d).") % (IDtransaction, systeme_paiement, IDpaiement)
                if len(liste_paiements) > 1:
                    observations += _(" Paiement en %d fois du %s (%d/%d).") % (len(liste_paiements), UTILS_Dates.DateDDEnFr(datetime.date.today()), index, len(liste_paiements))
                dlg.ctrl_observations.SetValue(observations)
                if IDcompte_bancaire not in (0, None):
                    dlg.ctrl_compte.SetID(IDcompte_bancaire)

                # Coche les prestations � ventiler
                resteVentilation = FloatToDecimal(montant_paiement)
                for ligne_prestation in dlg.ctrl_ventilation.ctrl_ventilation.listeLignesPrestations:
                    valide = False
                    if ligne_prestation.IDfacture in list(dict_paiements["facture"].keys()):
                        valide = True
                    else:
                        for IDperiode, dict_periode in dict_periodes.items():
                            if ligne_prestation.IDactivite == dict_periode["IDactivite"] and ligne_prestation.date >= dict_periode["date_debut"] and ligne_prestation.date <= dict_periode["date_fin"]:
                                valide = True
                    if valide:
                        aVentiler = resteVentilation
                        if aVentiler > FloatToDecimal(ligne_prestation.resteAVentiler):
                            aVentiler = FloatToDecimal(ligne_prestation.resteAVentiler)
                        if aVentiler > FloatToDecimal(0.0):
                            montant = aVentiler + ligne_prestation.ventilationActuelle
                            ligne_prestation.SetEtat(etat=True, montant=montant, majTotaux=False)
                            resteVentilation -= FloatToDecimal(aVentiler)

                # MAJ des totaux de ventilation
                dlg.ctrl_ventilation.ctrl_ventilation.MAJtotaux()

                reponse = dlg.ShowModal()
                dlg.Destroy()
                if reponse != wx.ID_OK:
                    return False

            reponse = ""
            return {"etat" : True, "reponse" : reponse}

        # Traitement automatique (desactiv� par choix dans Dialog.OnRadioEtat)
        if self.mode == "automatique" :
            reponse = ""
            return {"etat" : False, "reponse" : reponse}


    def Traitement_factures(self):
        # R�cup�ration des param�tres
        IDfacture = int(self.dict_parametres["IDfacture"])
        edition = Edition_facture(parent=self.parent, IDfacture=IDfacture, IDfamille=self.track.IDfamille)

        # Traitement manuel
        if self.mode == "manuel" :
            if self.dict_parametres["methode_envoi"] == "email" :
                self.EcritLog(_("Veuillez envoyer cette facture par Email."))

                resultat = edition.EnvoyerEmail(visible=True)
                if resultat == False :
                    self.EcritLog(_("La facture n'a pas �t� envoy�e par Email."))
                    return False

                reponse = _("Facture envoy�e par Email.")

            elif self.dict_parametres["methode_envoi"] == "courrier" :
                self.EcritLog(_("Veuillez imprimer la facture pour un envoi par courrier."))
                reponse = _("Facture envoy�e par courrier.")
                edition.Reedition()
            else :
                self.EcritLog(_("Veuillez imprimer la facture pour un retrait sur site."))
                reponse = _("Facture disponible au retrait.")
                edition.Reedition()

            return {"etat" : True, "reponse" : reponse}

        # Traitement automatique
        if self.mode == "automatique" :

            # Affichage du PDF pour envoi par courrier ou retrait sur site
            if self.dict_parametres["methode_envoi"] != "email" :
                message = _("La facture va �tre g�n�r�e au format PDF et ouverte dans votre lecteur de PDF.\n\n")
                if self.dict_parametres["methode_envoi"] == "courrier" :
                    message += _("Veuillez l'imprimer et l'envoyer par courrier.")
                else :
                    message += _("Veuillez l'imprimer et le conserver pour un retrait sur site.")
                dlg = wx.MessageDialog(self.parent, message, _("Impression d'une facture"), wx.OK|wx.OK_DEFAULT|wx.CANCEL|wx.ICON_QUESTION)
                reponse = dlg.ShowModal()
                dlg.Destroy()
                if reponse == wx.ID_CANCEL :
                    self.EcritLog(_("Interruption du traitement par l'utilisateur."))
                    return False

                edition.Reedition(afficherOptions=False)

                self.EcritLog(_("La g�n�ration de la facture est termin�e."))
                if self.dict_parametres["methode_envoi"] == "courrier" :
                    self.EcritLog(_("Veuillez imprimer la facture pour un envoi par courrier."))
                    reponse = _("Facture envoy�e par courrier.")
                else :
                    self.EcritLog(_("Veuillez imprimer la facture pour un retrait sur site."))
                    reponse = _("Facture disponible au retrait.")

            # Envoi par Email
            if self.dict_parametres["methode_envoi"] == "email" :
                # if len(listeAdresses) == 0 :
                #     self.EcritLog(_("Aucune adresse Email n'a �t� s�lectionn�e."))
                #     return False

                resultat = edition.EnvoyerEmail(visible=False)
                if resultat == False :
                    self.EcritLog(_("La facture n'a pas �t� envoy�e par Email."))
                    return False

                reponse = _("Facture envoy�e par Email.")

            return {"etat" : True, "reponse" : reponse}


    def Traitement_inscriptions(self):
        # R�cup�ration des param�tres
        IDactivite = int(self.dict_parametres["IDactivite"])
        IDgroupe = int(self.dict_parametres["IDgroupe"])

        # Traitement manuel ou automatique
        if self.mode == "manuel" or self.mode == "automatique" :

            # Cr�ation du texte d'intro
            DB = GestionDB.DB()
            req = """SELECT nom, prenom, date_naiss FROM individus WHERE IDindividu=%d;""" % self.track.IDindividu
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            listeDonnees = DB.ResultatReq()
            DB.Close()
            if len(listeDonnees) > 0 :
                nom, prenom, date_naiss = listeDonnees[0]
                if date_naiss != None :
                    date_naiss = UTILS_Dates.DateEngEnDateDD(date_naiss)
                    today = datetime.date.today()
                    age = _("%d ans") % ((today.year - date_naiss.year) - int((today.month, today.day) < (date_naiss.month, date_naiss.day)))
                else :
                    age = _("�ge inconnu")
            intro = _("Confirmez l'inscription de %s (%s) � l'activit� s�lectionn�e et sur le groupe demand� par la famille." % (prenom, age))

            from Dlg import DLG_Inscription
            dlg = DLG_Inscription.Dialog(self.parent, mode="saisie", IDindividu=self.track.IDindividu, IDfamille=self.track.IDfamille, intro=intro)
            dlg.ctrl_famille.Enable(False)
            dlg.GetPageActivite().CacheBoutonActivite()
            dlg.GetPageActivite().SetIDactivite(IDactivite)
            dlg.GetPageActivite().SetIDgroupe(IDgroupe)
            reponse = dlg.ShowModal()
            statut = dlg.GetStatut()
            dlg.Destroy()
            if reponse == wx.ID_OK :
                self.EcritLog(_("Inscription de %s enregistr�e.") % prenom)
                if statut == "attente" :
                    reponse = _("Inscription de %s mise en attente.") % prenom
                elif statut == "refus" :
                    reponse = _("Inscription de %s refus�e.") % prenom
                else :
                    reponse = _("Inscription de %s valid�e.") % prenom
                return {"etat" : True, "reponse" : reponse}
            else :
                self.EcritLog(_("Inscription de %s annul�e.") % prenom)
                return False

    def Traitement_reservations(self):
        if self.mode == "manuel" :
            from Dlg import DLG_Portail_reservations
            dlg = DLG_Portail_reservations.Dialog(self, track=self.track)
            reponse_modal = dlg.ShowModal()
            reponse = dlg.GetReponse()
            dlg.Destroy()
            if reponse_modal == wx.ID_OK :
                self.Save_grille(dlg.ctrl_grille)
                self.EcritLog(_("Enregistrement des consommations"))
                if reponse == "" :
                    return {"etat" : False, "reponse" : reponse}
                else :
                    return {"etat" : True, "reponse" : reponse}
            else :
                self.EcritLog(_("Traitement annul� par l'utilisateur"))
                return {"etat" : False}

        if self.mode == "automatique" :
            ctrl_grille = self.parent.ctrl_grille
            self.Init_grille(ctrl_grille=ctrl_grille)
            reponse = self.Appliquer_reservations(ctrl_grille=ctrl_grille)
            self.Save_grille(ctrl_grille)
            self.EcritLog(_("Enregistrement des consommations"))
            if reponse == "":
                return {"etat" : False, "reponse" : reponse}
            else :
                return {"etat" : True, "reponse" : reponse}

    def Traitement_renseignements(self):
        if self.mode == "manuel" :
            from Dlg import DLG_Portail_renseignements
            dlg = DLG_Portail_renseignements.Dialog(self, track=self.track)
            reponse_modal = dlg.ShowModal()
            reponse = dlg.GetReponse()
            dlg.Destroy()
            if reponse_modal == wx.ID_OK :
                self.EcritLog(_("Enregistrement des renseignements"))
                if reponse == "" :
                    return {"etat" : False, "reponse" : reponse}
                else :
                    return {"etat" : True, "reponse" : reponse}
            else :
                self.EcritLog(_("Traitement annul� par l'utilisateur"))
                return {"etat" : False}

        if self.mode == "automatique" :
            from Dlg import DLG_Portail_renseignements
            dlg = DLG_Portail_renseignements.Dialog(self, track=self.track)
            dlg.OnBoutonTraiter()
            dlg.OnBoutonOk()
            reponse = dlg.GetReponse()
            if reponse == "" :
                if dlg.ShowModal() == wx.ID_OK :
                    dlg.Destroy()
                    self.EcritLog(_("Enregistrement des renseignements"))
                    if reponse == "" :
                        return {"etat" : False, "reponse" : reponse}
                    else :
                        return {"etat" : True, "reponse" : reponse}
                else :
                    self.EcritLog(_("Traitement annul� par l'utilisateur"))
                    return {"etat" : False}

            else :
                dlg.Destroy()
                return {"etat": True, "reponse": reponse}

    def Traitement_locations(self):
        if self.mode == "manuel":
            from Dlg import DLG_Portail_locations
            dlg = DLG_Portail_locations.Dialog(self, track=self.track)
            reponse_modal = dlg.ShowModal()
            reponse = dlg.GetReponse()
            dlg.Destroy()
            if reponse_modal == wx.ID_OK :
                self.EcritLog(_("Enregistrement des locations"))
                if reponse == "":
                    return {"etat": False, "reponse": reponse}
                else :
                    return {"etat": True, "reponse": reponse}
            else :
                self.EcritLog(_("Traitement annul� par l'utilisateur"))
                return {"etat": False}

        if self.mode == "automatique":
            from Dlg import DLG_Portail_locations
            dlg = DLG_Portail_locations.Dialog(self, track=self.track)
            dlg.OnBoutonTraiter()
            reponse = dlg.GetReponse()
            dlg.OnBoutonFermer()
            self.EcritLog(_("Enregistrement des locations"))
            if reponse == "":
                return {"etat": False, "reponse": reponse}
            else :
                return {"etat": True, "reponse": reponse}

    def Traitement_pieces(self):
        chemin = self.dict_parametres.get("chemin", "")
        IDtype_piece = int(self.dict_parametres.get("IDtype_piece", 0))
        titre_piece = self.track.description.replace(u"Envoi de la pi�ce ", "")

        # T�l�chargement du fichier
        from Utils import UTILS_Portail_synchro
        dlgAttente = wx.BusyInfo(_("T�l�chargement de la pi�ce en cours..."), None)
        if 'phoenix' not in wx.PlatformInfo:
            wx.Yield()
        else:
            wx.SafeYield(self, True)
        synchro = UTILS_Portail_synchro.Synchro(log=self.track)
        chemin_fichier = synchro.ConnectEtTelechargeFichier(nomFichier=os.path.basename(chemin), repFichier="pieces/", lecture=False)
        del dlgAttente

        if chemin_fichier == False:
            dlg = wx.MessageDialog(self.parent, _("Le fichier ne peut pas �tre t�l�charg� !\n\nIl n'est pas accessible ou a �t� supprim� du serveur."), "Erreur", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return {"etat": False}

        # D�cryptage du fichier
        from Utils import UTILS_Cryptage_fichier
        cryptage_mdp = synchro.dict_parametres["secret_key"][:10]
        UTILS_Cryptage_fichier.DecrypterFichier(chemin_fichier, chemin_fichier, cryptage_mdp)

        # Ouverture de la DLG
        from Dlg import DLG_Saisie_piece
        dlg = DLG_Saisie_piece.Dialog(self.parent, IDpiece=None, IDfamille=self.track.IDfamille)
        dlg.SetValeurs(IDfamille=self.track.IDfamille, IDtype_piece=IDtype_piece, IDindividu=self.track.IDindividu, titre=titre_piece)
        dlg.CalcValiditeDefaut()
        dlg.ctrl_pages.AjouterPageManuellement(fichier=chemin_fichier, titre=titre_piece)

        if self.mode == "manuel":
            if dlg.ShowModal() == wx.ID_OK:
                IDpiece = dlg.GetIDpiece()
                dlg.Destroy()
                self.EcritLog(_("Enregistrement manuel de la pi�ce ID%d") % IDpiece)
                return {"etat": True, "reponse": _("La pi�ce %s a bien �t� enregistr�e") % titre_piece}

        if self.mode == "automatique":
            if dlg.Sauvegarde() == True:
                IDpiece = dlg.GetIDpiece()
                dlg.Destroy()
                self.EcritLog(_("Enregistrement automatique de la pi�ce ID%d") % IDpiece)
                return {"etat": True, "reponse": _("La pi�ce %s a bien �t� enregistr�e") % titre_piece}
            else:
                if dlg.ShowModal() == wx.ID_OK:
                    IDpiece = dlg.GetIDpiece()
                    self.EcritLog(_("Enregistrement manuel de la pi�ce ID%d") % IDpiece)
                    return {"etat": True, "reponse": _("La pi�ce %s a bien �t� enregistr�e") % titre_piece}
                dlg.Destroy()

        return {"etat": False}

    def Traitement_compte(self):
        # Traitement manuel ou automatique
        if self.mode == "manuel" or self.mode == "automatique" :

            if self.mode == "manuel" :
                dlg = wx.MessageDialog(None, _("Confirmez-vous l'enregistrement du nouveau mot de passe personnalis� de %s ?") % self.track.nom, _("Mise � jour du mot de passe"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_QUESTION)
                reponse = dlg.ShowModal()
                dlg.Destroy()
                if reponse != wx.ID_YES :
                    return False

            # Mise � jour de mot de passe
            if self.track.action == "maj_password" :
                DB = GestionDB.DB()

                # Famille
                if self.track.IDfamille != None :
                    DB.ReqMAJ("familles", [("internet_mdp", self.track.parametres)], "IDfamille", self.track.IDfamille)

                # Utilisateur
                if self.track.IDutilisateur != None :
                    DB.ReqMAJ("utilisateurs", [("internet_mdp", self.track.parametres)], "IDutilisateur", self.track.IDutilisateur)

                DB.Close()

                self.EcritLog(_("Mise � jour du mot de passe de %s") % self.track.nom)
                return {"etat" : True, "reponse" : ""}

        return False

    def Init_grille(self, ctrl_grille=None):
        # R�cup�ration des param�tres
        IDactivite = int(self.dict_parametres["IDactivite"])
        date_debut_periode = UTILS_Dates.DateEngEnDateDD(self.dict_parametres["date_debut_periode"])
        date_fin_periode = UTILS_Dates.DateEngEnDateDD(self.dict_parametres["date_fin_periode"])

        # Init de la grille des conso
        ctrl_grille.InitGrille(IDindividu=self.track.IDindividu, IDfamille=self.track.IDfamille, IDactivite=IDactivite, periode=(date_debut_periode, date_fin_periode))

    def Save_grille(self, ctrl_grille=None):
        """ Sauvegarde de la grille des conso """
        ctrl_grille.Sauvegarde()

    def Appliquer_reservations(self, ctrl_grille=None, log_jumeau=None):
        """ Appliquer la saisie ou suppression des r�servations """
        # R�cup�ration des param�tres
        IDactivite = int(self.dict_parametres["IDactivite"])
        date_debut_periode = UTILS_Dates.DateEngEnDateDD(self.dict_parametres["date_debut_periode"])
        date_fin_periode = UTILS_Dates.DateEngEnDateDD(self.dict_parametres["date_fin_periode"])

        self.EcritLog(_("Traitement des r�servations de %s sur la p�riode du %s au %s") % (ctrl_grille.ctrl_titre.GetNom(), UTILS_Dates.DateDDEnFr(date_debut_periode), UTILS_Dates.DateDDEnFr(date_fin_periode)), log_jumeau)

        # Lecture des r�servations
        DB = GestionDB.DB()
        req = """SELECT IDreservation, date, IDinscription, portail_reservations.IDunite, etat, portail_unites.nom
        FROM portail_reservations
        LEFT JOIN portail_unites ON portail_unites.IDunite = portail_reservations.IDunite
        WHERE IDaction=%d
        ORDER BY date, etat;""" % self.track.IDaction
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        listeReservations = []
        dictUnitesResaParDate = {}
        for IDreservation, date, IDinscription, IDunite, etat, nom_unite_reservation in listeDonnees :
            date = UTILS_Dates.DateEngEnDateDD(date)
            listeReservations.append({"IDreservation" : IDreservation, "date" : date, "IDinscription" : IDinscription, "IDunite" : IDunite, "etat" : etat, "nom_unite_reservation" : nom_unite_reservation})

        # Traitement des r�servations
        liste_resultats = []
        dict_reponses = {"suppression" : 0, "reservation" : 0, "attente" : 0}

        liste_erreurs = []
        for reservation in listeReservations :
            date = reservation["date"]
            IDunite_resa = reservation["IDunite"]
            dict_unite_resa = self.parent.dictUnites[IDunite_resa]
            liste_unites_conso = dict_unite_resa["unites_principales"] + dict_unite_resa["unites_secondaires"]
            nom_unite_reservation = reservation["nom_unite_reservation"]

            # Suppression de la r�servation
            if reservation["etat"] == 0 :

                for IDunite in liste_unites_conso :

                    # Ecrit suppression dans log
                    nomUnite = ctrl_grille.grille.dictUnites[IDunite]["nom"]
                    self.EcritLog(_("Suppression de l'unit� %s du %s") % (nomUnite, UTILS_Dates.DateDDEnFr(date)), log_jumeau)

                    # V�rifie s'il faut appliquer l'�tat Absence Injustifi�e
                    portail_reservations_absenti = self.parent.dictActivites[IDactivite]["portail_reservations_absenti"]
                    absenti = False
                    if portail_reservations_absenti != None :
                        nbre_jours, heure = portail_reservations_absenti.split("#")
                        dt_limite = datetime.datetime(year=date.year, month=date.month, day=date.day, hour=int(heure[:2]), minute=int(heure[3:])) - datetime.timedelta(days=int(nbre_jours))
                        if self.track.horodatage > dt_limite :
                            absenti = True

                    if absenti == True :
                        ctrl_grille.ModifieEtat(IDunite=IDunite, etat="absenti", date=date)
                    else :
                        ctrl_grille.SupprimeConso(IDunite=IDunite, date=date)

                liste_resultats.append(("suppression", date, nom_unite_reservation))
                dict_reponses["suppression"] += 1


            # Ajout de la r�servation
            if reservation["etat"] == 1 :

                # V�rifie s'il y a de la place sur chaque unit� de conso associ�e � l'unit� de r�servation
                hasPlaces = True
                for IDunite in liste_unites_conso :
                    if ctrl_grille.IsOuvert(IDunite=IDunite, date=date) :
                        if ctrl_grille.GetCase(IDunite, date) != None and ctrl_grille.HasPlacesDisponibles(IDunite=IDunite, date=date) == False :
                            hasPlaces = False

                # Si plus de places, met les unit�s de conso en mode "attente"
                if hasPlaces == True :
                    mode = "reservation"
                    mode_label = _("r�servation")
                else :
                    mode = "attente"
                    mode_label = _("attente")

                # Saisie les conso
                for IDunite in liste_unites_conso :
                    if ctrl_grille.IsOuvert(IDunite=IDunite, date=date) :

                        if IDunite in ctrl_grille.grille.dictUnites:
                            nomUnite = ctrl_grille.grille.dictUnites[IDunite]["nom"]
                            texte = _("Saisie de l'unit� %s du %s en mode %s") % (nomUnite, UTILS_Dates.DateDDEnFr(date), mode_label)
                            self.EcritLog(texte, log_jumeau)
                            resultat = ctrl_grille.SaisieConso(IDunite=IDunite, date=date, mode=mode)
                        else :
                            resultat = _("L'unit� ID%d est inconnue. V�rifiez le param�trage des unit�s de r�servation." % IDunite)

                        if resultat != True :
                            self.EcritLog(_("[ERREUR] %s") % resultat, log_jumeau)
                            liste_erreurs.append(u"> %s :\n    %s" % (texte, resultat))

                liste_resultats.append(("saisie", date, nom_unite_reservation, mode))
                if mode == "reservation" :
                    dict_reponses["reservation"] += 1
                if mode == "attente" :
                    dict_reponses["attente"] += 1


        # Cr�ation de la r�ponse
        if len(liste_erreurs) > 0 :

            # Si erreurs
            from Dlg import DLG_Messagebox
            if len(liste_erreurs) == 1 :
                introduction = _("Une anomalie a �t� d�tect�e durant l'application de la demande :")
            else :
                introduction = _("%s anomalies ont �t� d�tect�es durant l'application de la demande :") % len(liste_erreurs)
            detail = "\n".join(liste_erreurs)
            dlg = DLG_Messagebox.Dialog(None, titre=_("Avertissement"), introduction=introduction, detail=detail, icone=wx.ICON_EXCLAMATION, boutons=[_("Ok"), ])
            dlg.ShowModal()
            dlg.Destroy()
            return ""
        else :

            # Si aucune erreur
            reponse_temp = []

            nbre_suppressions = dict_reponses["suppression"]
            if nbre_suppressions == 1 :
                reponse_temp.append(_("1 suppression effectu�e"))
            if nbre_suppressions > 1 :
                reponse_temp.append(_("%d suppressions effectu�es") % nbre_suppressions)

            nbre_reservations = dict_reponses["reservation"]
            if nbre_reservations == 1 :
                reponse_temp.append(_("1 r�servation valid�e"))
            if nbre_reservations > 1 :
                reponse_temp.append(_("%d r�servations valid�es") % nbre_reservations)

            nbre_attentes = dict_reponses["attente"]
            if nbre_attentes == 1 :
                reponse_temp.append(_("1 r�servation en attente"))
            if nbre_attentes > 1 :
                reponse_temp.append(_("%d r�servations en attente") % nbre_attentes)

            # Formatage de la r�ponse
            if len(reponse_temp) == 0 :
                reponse = _("Aucune modification.")
            elif len(reponse_temp) == 1 :
                reponse = reponse_temp[0] + "."
            elif len(reponse_temp) == 2 :
                reponse = _(" et ").join(reponse_temp) + "."
            else :
                reponse = _("%s et %s.") % (u", ".join(reponse_temp[:-1]), reponse_temp[-1])

            self.EcritLog(_("R�ponse : %s") % reponse, log_jumeau)
            return reponse

    def Verifier_ventilation(self):
        from Dlg import DLG_Verification_ventilation
        tracks = DLG_Verification_ventilation.Verification(self.track.IDcompte_payeur)
        if len(tracks) > 0 :
            dlg = wx.MessageDialog(None, _("Un ou plusieurs r�glements peuvent �tre ventil�s.\n\nSouhaitez-vous le faire maintenant (conseill�) ?"), _("Ventilation"), wx.YES_NO|wx.YES_DEFAULT|wx.CANCEL|wx.ICON_EXCLAMATION)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse == wx.ID_YES :
                dlg = DLG_Verification_ventilation.Dialog(None, tracks=tracks, IDcompte_payeur=self.track.IDcompte_payeur)
                dlg.ShowModal()
                dlg.Destroy()
            if reponse == wx.ID_CANCEL :
                return False
        return True

    def Get_montants_reservations(self):
        # R�cup�ration des variables
        IDactivite = int(self.dict_parametres["IDactivite"])
        date_debut = UTILS_Dates.DateEngEnDateDD(self.dict_parametres["date_debut_periode"])
        date_fin = UTILS_Dates.DateEngEnDateDD(self.dict_parametres["date_fin_periode"])
        IDindividu = self.track.IDindividu
        IDfamille = self.track.IDfamille

        # R�cup�re les prestations
        DB = GestionDB.DB()
        req = """SELECT IDprestation, montant
        FROM prestations
        WHERE IDactivite=%d AND IDfamille=%d AND IDindividu=%d AND date>='%s' AND date<='%s'
        ;""" % (IDactivite, IDfamille, IDindividu, date_debut, date_fin)
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listePrestations = DB.ResultatReq()
        total_prestations = FloatToDecimal(0.0)
        liste_IDprestation = []
        for IDprestation, montant in listePrestations:
            liste_IDprestation.append(IDprestation)
            total_prestations += FloatToDecimal(montant)

        # R�cup�re la ventilation
        req = """SELECT SUM(ventilation.montant)
        FROM ventilation
        LEFT JOIN prestations ON prestations.IDprestation = ventilation.IDprestation
        WHERE prestations.IDprestation IN %s
        ;""" % GestionDB.ConvertConditionChaine(liste_IDprestation)
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeVentilations = DB.ResultatReq()
        DB.Close()
        total_ventilation = FloatToDecimal(0.0)
        if len(listeVentilations) > 0 :
            total_ventilation = FloatToDecimal(listeVentilations[0][0])

        # Calcul du solde
        solde = total_prestations - total_ventilation
        return {"total": total_prestations, "regle": total_ventilation, "solde": solde}



class Edition_facture():
    """ Classe sp�ciale pour l'�dition des factures """
    def __init__(self, parent=None, IDfacture=None, IDfamille=None):
        self.parent = parent
        self.IDfacture = IDfacture
        self.IDfamille = IDfamille

    def Reedition(self, afficherOptions=True):
        self.afficherOptions = afficherOptions
        facturation = UTILS_Facturation.Facturation()
        facturation.Impression(listeFactures=[self.IDfacture,], afficherOptions=afficherOptions)

    def EnvoyerEmail(self, visible=True):
        self.afficherOptions = visible
        resultat = UTILS_Envoi_email.EnvoiEmailFamille(parent=self.parent, IDfamille=self.IDfamille, nomDoc=FonctionsPerso.GenerationNomDoc("FACTURE", "pdf"), categorie="facture", visible=visible, CreationPDF=self.CreationPDF)
        return resultat

    def CreationPDF(self, nomDoc="", afficherDoc=True):
        """ Cr�ation du PDF pour Email """
        facturation = UTILS_Facturation.Facturation()
        resultat = facturation.Impression(listeFactures=[self.IDfacture,], nomDoc=nomDoc, afficherDoc=afficherDoc, afficherOptions=self.afficherOptions)
        if resultat == False :
            return False
        dictChampsFusion, dictPieces = resultat
        return dictChampsFusion[self.IDfacture]






if __name__ == "__main__":
    app = wx.App(0)
    dialog_1 = Dialog(None)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()

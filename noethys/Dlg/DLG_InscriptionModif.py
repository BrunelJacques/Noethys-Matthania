#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:          Ivan LUCAS, JB, Jacques Brunel
# Licence:         Licence GNU GPL
# Gestion de la piece en modification
# Adapté à partir de DLG_ValidationPiece
#------------------------------------------------------------------------

from Utils.UTILS_Traduction import _
import Chemins
import wx
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Saisie_euros
from Utils import UTILS_Utilisateurs
import datetime
import copy
from Dlg import DLG_Inscription
from Gest import GestionArticle
from Gest import GestionPieces
import GestionDB
from Dlg import DLG_PrixActivite
from Gest import GestionInscription
from Dlg import DLG_ValidationPiece
from Dlg import DLG_InscriptionComplements
from Data import DATA_Tables
from Ctrl import CTRL_Bandeau

def Cchaine(valeur):
    chaine = valeur
    if valeur == None: chaine = "-"
    if type(valeur) in (int, int, float): chaine = str(valeur)
    return chaine

def Decod(valeur):
    return GestionDB.Decod(valeur)


def DateEngEnDateDD(dateEng):
    if dateEng and not isinstance(dateEng,str): dateEng = str(dateEng)
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

# -----------------------------------------------------------------------------------------------------------------
class Dialog(wx.Dialog):
    def __init__(self, parent, dictPiece,dictFamillesRattachees):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE)
        self.dictDonneesOrigine = dictPiece
        self.dictFamillesRattachees = dictFamillesRattachees
        self.module = "DLG_InscriptionModif.Dialog"
        self.parent = parent
        self.titre = ("Gestion de la modification de la pièce")
        intro = ("Les pièces transférées en compta ne sont pas modifiables")
        self.SetTitle(self.module)
        self.rw = True
        if dictPiece["nature"] in ("FAC","AVO"): self.rw = False
        droitModif = UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_inscriptions", "modifier")
        if not droitModif : self.rw = False

        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=self.titre, texte=intro,  hauteurHtml=15, nomImage="Images/22x22/Smiley_nul.png")
        self.staticbox_TIERS = wx.StaticBox(self, -1, _("Tiers"))
        self.label_individu = wx.StaticText(self, -1, _("Individu inscrit :"))
        self.ctrl_nom_individu = wx.TextCtrl(self, -1, "",size=(50, 20))
        self.label_famille = wx.StaticText(self, -1,  _("Famille :"))
        self.ctrl_nom_famille = wx.TextCtrl(self, -1, "",size=(50, 20))
        self.bouton_famille = wx.Button(self, -1, "...", size=(20, 20))
        self.label_payeur = wx.StaticText(self, -1, _("Tiers payeur :"))
        self.ctrl_nom_payeur = wx.TextCtrl(self, -1, "",size=(50, 20))

        self.staticbox_CAMPgauche = wx.StaticBox(self, -1, _("Activite"))
        self.label_activite = wx.StaticText(self, -1, _("Activité (hors cotisation et transport):"))
        self.ctrl_nom_activite = wx.TextCtrl(self, -1, "",size=(50, 20))
        self.bouton_activite = wx.Button(self, -1, "...", size=(20, 20))
        self.label_groupe = wx.StaticText(self, -1,  _("Groupe :"))
        self.ctrl_nom_groupe = wx.TextCtrl(self, -1, "",size=(50, 20))
        self.label_tarif = wx.StaticText(self, -1, _("Catégorie Tarif:"))
        self.ctrl_nom_tarif = wx.TextCtrl(self, -1, "",size=(50, 20))

        self.staticbox_PRIX = wx.StaticBox(self, -1,_("Prix de l'activité"))
        self.label_prix1 = wx.StaticText(self, -1, _("Actuel :"))
        self.ctrl_prix1 = CTRL_Saisie_euros.CTRL(self)
        self.bouton_prix1 = wx.Button(self, -1, "...", size=(20, 20))
        self.label_prix2 = wx.StaticText(self, -1, _("Nouveau :"))
        self.ctrl_prix2 = CTRL_Saisie_euros.CTRL(self)
        self.bouton_prix2 = wx.Button(self, -1, "...", size=(20, 20))

        self.staticbox_PIECEgauche = wx.StaticBox(self, -1, _("Pièce"))
        self.label_nature = wx.StaticText(self, -1, _("Nature :"))
        self.ctrl_nom_nature = wx.TextCtrl(self, -1, "",size=(150, 20))
        self.bouton_piece = wx.Button(self, -1, "...", size=(20, 20))
        self.label_etat = wx.StaticText(self, -1,  _("Etat pièce :"))
        self.ctrl_nom_etat = wx.TextCtrl(self, -1, "",size=(150, 20))

        self.staticbox_CONTENU = wx.StaticBox(self, -1, _("Contenu"))
        self.label_commentaire = wx.StaticText(self, -1, _("Notes\nmodifiables :"))
        self.txt_commentaire = wx.TextCtrl(self, -1, "", style=wx.TE_MULTILINE,size = (150,60))
        self.label_infos = wx.StaticText(self, -1, _("Infos pièce :"))
        self.choice_infos = wx.Choice(self, -1, choices=[],size = (150,20))
        self.staticbox_BOUTONS= wx.StaticBox(self, -1, )
        if dictPiece["nature"] == "FAC":
            self.bouton_avoir = CTRL_Bouton_image.CTRL(self, texte=_("Avoir\nGlobal"), cheminImage="Images/32x32/Places_refus.png")
        else:
            self.bouton_avoir = CTRL_Bouton_image.CTRL(self, texte=_(" "), cheminImage="Images/32x32/Rectangle.png")
        self.bouton_ok_direct = CTRL_Bouton_image.CTRL(self, texte=_("OK vers\nFamille"), cheminImage="Images/32x32/Suivant.png")
        if self.rw:
            self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("OK via\nTransp."), cheminImage="Images/32x32/Suivant.png")
        else:
            self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Voir\nTransp."), cheminImage="Images/32x32/Suivant.png")
        if self.rw:
            self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Abandon"), cheminImage="Images/32x32/Annuler.png")
        else:
            self.bouton_annuler = wx.BitmapButton(self, wx.ID_CANCEL,wx.Bitmap(Chemins.GetStaticPath("Images/BoutonsImages/Retour_L72.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_compl = CTRL_Bouton_image.CTRL(self, texte=_("Correctif\n+ ou -"), cheminImage="Images/32x32/Questionnaire.png")

        self.__set_data()
        self.__set_properties()
        self.__do_layout()

    def __set_data(self):
        self.modifPrestations = False
        self.modifConsommations = False
        self.modifInscriptions = False
        self.modifPieces = False
        self.dictDonnees = {}
        self.listeNoms = []
        self.listeFamille = []
        self.dictFamillesRattachees = self.parent.dictFamillesRattachees

        #alimente Choice des listeInfo
        self.listeChamps = sorted(self.dictDonneesOrigine.keys())
        for champ in self.listeChamps:
            self.dictDonnees[champ] = self.dictDonneesOrigine[champ]
            tip = type(self.dictDonneesOrigine[champ])
            if tip in ( str, str):
                valeur = self.dictDonneesOrigine[champ]
            elif tip in (int, float):
                valeur = str(self.dictDonneesOrigine[champ])
            elif self.dictDonneesOrigine[champ] == None:
                valeur = "  -"
            elif tip == list:
                valeur = str(len(self.dictDonneesOrigine[champ])) +" lignes"
            else:
                valeur = str(tip)
            text = "%s :%s" %(champ,"_"*18)
            try:
                text = text[:20] + GestionDB.Decod(valeur)
            except:
                pass
            self.choice_infos.Append(text)
        self.choice_infos.Select(16)

        # transposition de la nature et de l'état de la pièce
        self.liste_naturesPieces = copy.deepcopy(GestionArticle.LISTEnaturesPieces)
        self.liste_codesNaturePiece = []
        for a,b,c in self.liste_naturesPieces: self.liste_codesNaturePiece.append(a)
        self.liste_etatsPieces = copy.deepcopy(GestionArticle.LISTEetatsPieces)
        #ajout de l'avoir pour usage en lecture seule
        self.liste_naturesPieces.extend(GestionArticle.LISTEnaturesPiecesFac)
        nature,etat = self.GetNomsNatureEtat(self.dictDonneesOrigine)
        self.ctrl_nom_nature.SetValue(nature)
        self.ctrl_nom_etat.SetValue(etat)

        #Calcul du prix
        prix = 0.00
        listeLignes = self.dictDonneesOrigine["lignes_piece"]
        for dictLigne in listeLignes:
            if dictLigne["montant"]==0:
                prix +=  dictLigne["quantite"] * dictLigne["prixUnit"]
            else: prix += dictLigne["montant"]
        self.ctrl_prix1.SetValue(str("{:10.2f}".format((prix))))
        self.AffichePrix2()
        #Autre elements gérés, appel des données
        self.txt_commentaire.SetValue(Decod(self.dictDonneesOrigine["commentaire"]))
        self.ctrl_nom_individu.SetValue(Cchaine(self.dictDonneesOrigine["nom_individu"]))
        self.ctrl_nom_famille.SetValue(Cchaine(self.dictDonneesOrigine["nom_famille"]))
        self.ctrl_nom_payeur.SetValue(Cchaine(self.dictDonneesOrigine["nom_payeur"]))
        self.ctrl_nom_activite.SetValue(Cchaine(self.dictDonneesOrigine["nom_activite"]))
        self.ctrl_nom_groupe.SetValue(Cchaine(self.dictDonneesOrigine["nom_groupe"]))
        self.ctrl_nom_tarif.SetValue(Cchaine(self.dictDonneesOrigine["nom_categorie_tarif"]))
        # éléments pour modif
        self.IDindividu = self.dictDonneesOrigine["IDindividu"]
        self.IDfamille = self.dictDonneesOrigine["IDfamille"]
        self.IDpayeur = self.dictDonneesOrigine["IDcompte_payeur"]
        self.dictDonnees["origine"]= "modif"
        #fin SetData

    def __set_properties(self):
        self.SetMinSize((500, 600))
        self.bouton_famille.SetToolTip(_("Cliquez pour modifier les éléments tiers"))
        self.bouton_activite.SetToolTip(_("Cliquez pour modifier les éléments acitivité"))
        self.bouton_prix1.SetToolTip(_("Cliquez pour consulter la composition du prix"))
        self.bouton_prix2.SetToolTip(_("Cliquez pour modifier la tarification actuelle"))
        self.bouton_piece.SetToolTip(_("Cliquez pour modifier la nature de la pièce, l'état en découle"))
        self.choice_infos.SetToolTip(_("Pour info seulement, contenu du fichier pièce"))
        self.txt_commentaire.SetToolTip(_("Ces infos sont générées automatiquement lors de la création mais vous pouvez les modifier"))
        self.bouton_avoir.SetToolTip(_("L'avoir compense une facture sans la supprimer"))
        self.bouton_ok.SetToolTip(_("Cliquez ici pour valider passer par transports avant famille"))
        self.bouton_ok_direct.SetToolTip(_("Cliquez ici pour valider et aller vers le niveau famille"))
        self.bouton_compl.SetToolTip(_("Cliquez ici pour créer une nouvelle pièce"))
        self.bouton_annuler.SetToolTip(_("Cliquez ici pour annuler et fermer"))
        self.ctrl_nom_famille.SetToolTip(_("Cliquez sur le bouton pour modifier les éléments tiers"))
        self.ctrl_nom_payeur.SetToolTip(_("Le payeur est celui de la famille"))
        self.ctrl_nom_activite.SetToolTip(_("Cliquez sur le bouton pour modifier les éléments acitivité"))
        self.ctrl_nom_groupe.SetToolTip(_("Cliquez sur le bouton pour modifier les éléments acitivité"))
        self.ctrl_nom_tarif.SetToolTip(_("Cliquez sur le bouton pour modifier les éléments acitivité"))
        self.ctrl_prix1.SetToolTip(_("Ne modifiez pas ce prix !"))
        self.ctrl_prix2.SetToolTip(_("Cliquez sur le bouton pour modifier la tarification actuelle"))
        self.ctrl_nom_nature.SetToolTip(_("Cliquez sur le bouton pour changer la nature de la pièce, l'état en découle"))

        self.Bind(wx.EVT_BUTTON, self.On_famille, self.bouton_famille)
        self.ctrl_nom_famille.Bind(wx.EVT_SET_FOCUS, self.On_ctrl_famille)
        self.Bind(wx.EVT_BUTTON, self.On_activite, self.bouton_activite)
        self.ctrl_nom_activite.Bind(wx.EVT_SET_FOCUS, self.On_ctrl_activite)
        self.ctrl_nom_groupe.Bind(wx.EVT_SET_FOCUS, self.On_ctrl_activite)
        self.ctrl_nom_tarif.Bind(wx.EVT_SET_FOCUS, self.On_ctrl_activite)
        self.Bind(wx.EVT_BUTTON, self.On_prix1, self.bouton_prix1)
        self.Bind(wx.EVT_BUTTON, self.On_prix2, self.bouton_prix2)
        self.ctrl_prix2.Bind(wx.EVT_SET_FOCUS, self.On_ctrl_prix2)
        self.Bind(wx.EVT_BUTTON, self.On_piece, self.bouton_piece)
        self.ctrl_nom_nature.Bind(wx.EVT_SET_FOCUS, self.On_ctrl_nom_nature)
        self.txt_commentaire.Bind(wx.EVT_KILL_FOCUS, self.On_commentaire)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAvoir, self.bouton_avoir)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOkDirect, self.bouton_ok_direct)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonCompl, self.bouton_compl)
        self.label_individu.Enable(False)
        self.label_etat.Enable(False)
        self.ctrl_nom_etat.Enable(False)
        self.ctrl_nom_individu.Enable(False)
        self.ctrl_nom_payeur.Enable(False)
        self.ctrl_prix1.Enable(True)
        self.bouton_famille.Enable(self.rw)
        self.bouton_prix2.Enable(self.rw)
        self.bouton_piece.Enable(self.rw)
        self.bouton_activite.Enable(self.rw)
        self.ctrl_nom_etat.Enable(self.rw)
        self.ctrl_prix2.Enable(self.rw)
        self.ctrl_nom_nature.Enable(self.rw)
        self.ctrl_nom_famille.Enable(self.rw)
        self.ctrl_nom_activite.Enable(self.rw)
        self.ctrl_nom_groupe.Enable(self.rw)
        self.ctrl_nom_tarif.Enable(self.rw)
        self.ctrl_nom_nature.Enable(self.rw)
        self.ctrl_nom_etat.Enable(self.rw)
        if self.dictDonneesOrigine["nature"] in  ("FAC","AVO"):
            self.ctrl_nom_nature.Enable(False)
            self.label_nature.Enable(False)
            self.bouton_piece.Enable(False)
            #self.bouton_ok.Enable(False)
            self.bouton_ok_direct.Enable(False)
        if self.dictDonneesOrigine["nature"] in  ("FAC"):
            self.bouton_avoir.Enable(True)
        else:
            self.bouton_avoir.Enable(False)
        #fin _set_properties

    def __do_layout(self):
        gridsizer_BASE = wx.FlexGridSizer(rows=7, cols=1, vgap=0, hgap=0)
        gridsizer_BASE.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)

        staticsizer_TIERS = wx.StaticBoxSizer(self.staticbox_TIERS, wx.VERTICAL)
        gridsizer_TIERS = wx.FlexGridSizer(rows=2, cols=1, vgap=0, hgap=0)
        gridsizer_TIERShaut = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        gridsizer_TIERShaut.Add(self.label_individu, 1, wx.LEFT, 15)
        gridsizer_TIERShaut.Add(self.ctrl_nom_individu, 1, wx.LEFT|wx.EXPAND, 0)
        gridsizer_TIERShaut.AddGrowableCol(1)
        gridsizer_TIERS.Add(gridsizer_TIERShaut, 1, wx.BOTTOM|wx.EXPAND, 5)

        gridsizer_TIERSbas = wx.FlexGridSizer(rows=2, cols=3, vgap=5, hgap=5)
        gridsizer_TIERSbas.Add(self.label_famille, 1, wx.LEFT, 15)
        gridsizer_TIERSbas.Add(self.ctrl_nom_famille, 1, wx.LEFT|wx.EXPAND, 15)
        gridsizer_TIERSbas.Add(self.bouton_famille, 1, wx.LEFT, 10)
        gridsizer_TIERSbas.Add(self.label_payeur, 1, wx.LEFT, 15)
        gridsizer_TIERSbas.Add(self.ctrl_nom_payeur, 1, wx.LEFT|wx.EXPAND, 15)
        gridsizer_TIERSbas.AddGrowableCol(1)
        gridsizer_TIERS.Add(gridsizer_TIERSbas, 1,wx.BOTTOM|wx.EXPAND, 5)
        gridsizer_TIERS.AddGrowableCol(0)
        staticsizer_TIERS.Add(gridsizer_TIERS, 1, wx.RIGHT|wx.EXPAND,5)
        gridsizer_BASE.Add(staticsizer_TIERS, 1,wx.ALL|wx.EXPAND, 3)

        gridsizer_CAMP = wx.FlexGridSizer(rows=1, cols=2, vgap=0, hgap=0)
        staticsizer_CAMPgauche = wx.StaticBoxSizer(self.staticbox_CAMPgauche, wx.VERTICAL)
        gridsizer_CAMPgauche = wx.FlexGridSizer(rows=3, cols=2, vgap=5, hgap=5)
        gridsizer_CAMPgauche.Add(self.label_activite, 1, wx.LEFT,15)
        gridsizer_CAMPgauche.Add(self.ctrl_nom_activite, 1, wx.TOP|wx.EXPAND, 0)
        gridsizer_CAMPgauche.Add(self.label_groupe, 1, wx.LEFT, 15)
        gridsizer_CAMPgauche.Add(self.ctrl_nom_groupe, 1, wx.LEFT|wx.EXPAND, 0)
        gridsizer_CAMPgauche.Add(self.label_tarif, 1, wx.LEFT, 15)
        gridsizer_CAMPgauche.Add(self.ctrl_nom_tarif, 1, wx.LEFT|wx.EXPAND, 0)
        gridsizer_CAMPgauche.AddGrowableCol(1)
        staticsizer_CAMPgauche.Add(gridsizer_CAMPgauche, 1, wx.RIGHT|wx.EXPAND,10)
        gridsizer_CAMP.Add(staticsizer_CAMPgauche, 1, wx.BOTTOM|wx.EXPAND, 5)

        gridsizer_CAMPdroite = wx.FlexGridSizer(rows=1, cols=1, vgap=5, hgap=5)
        gridsizer_CAMPdroite.Add(self.bouton_activite, 1, wx.TOP, 30)
        gridsizer_CAMP.Add(gridsizer_CAMPdroite, 1, wx.ALL, 5)

        gridsizer_CAMP.AddGrowableCol(0)
        gridsizer_BASE.Add(gridsizer_CAMP, 1,wx.ALL|wx.EXPAND, 3)

        staticsizer_PRIX = wx.StaticBoxSizer(self.staticbox_PRIX, wx.VERTICAL)
        gridsizer_PRIX = wx.FlexGridSizer(rows=1, cols=6, vgap=5, hgap=5)
        gridsizer_PRIX.Add(self.label_prix1, 1, wx.LEFT, 10)
        gridsizer_PRIX.Add(self.ctrl_prix1, 1, wx.LEFT|wx.EXPAND, 0)
        gridsizer_PRIX.Add(self.bouton_prix1, 1, wx.LEFT, 0)
        gridsizer_PRIX.Add(self.label_prix2, 1, wx.LEFT, 10)
        gridsizer_PRIX.Add(self.ctrl_prix2, 1, wx.LEFT|wx.EXPAND, 0)
        gridsizer_PRIX.Add(self.bouton_prix2, 1, wx.LEFT, 0)
        staticsizer_PRIX.Add(gridsizer_PRIX, 1, wx.RIGHT|wx.EXPAND,0)
        gridsizer_PRIX.AddGrowableCol(1)
        gridsizer_PRIX.AddGrowableCol(4)
        gridsizer_BASE.Add(staticsizer_PRIX, 1,wx.ALL|wx.EXPAND, 3)

        gridsizer_PIECE = wx.FlexGridSizer(rows=1, cols=2, vgap=0, hgap=0)
        staticsizer_PIECEgauche = wx.StaticBoxSizer(self.staticbox_PIECEgauche, wx.VERTICAL)
        gridsizer_PIECEgauche = wx.FlexGridSizer(rows=3, cols=2, vgap=5, hgap=5)
        gridsizer_PIECEgauche.Add(self.label_nature, 1, wx.LEFT,15)
        gridsizer_PIECEgauche.Add(self.ctrl_nom_nature, 1, wx.TOP, 0)
        gridsizer_PIECEgauche.Add(self.label_etat, 1, wx.LEFT, 15)
        gridsizer_PIECEgauche.Add(self.ctrl_nom_etat, 1, wx.LEFT|wx.EXPAND, 0)
        gridsizer_PIECEgauche.AddGrowableCol(1)
        staticsizer_PIECEgauche.Add(gridsizer_PIECEgauche, 1, wx.RIGHT|wx.EXPAND,10)
        gridsizer_PIECE.Add(staticsizer_PIECEgauche, 1, wx.BOTTOM|wx.EXPAND, 5)
        gridsizer_PIECEdroite = wx.FlexGridSizer(rows=1, cols=1, vgap=5, hgap=5)
        gridsizer_PIECEdroite.Add(self.bouton_piece, 1, wx.TOP, 15)
        gridsizer_PIECE.Add(gridsizer_PIECEdroite, 1, wx.ALL, 5)
        gridsizer_PIECE.AddGrowableCol(0)
        gridsizer_BASE.Add(gridsizer_PIECE, 1,wx.ALL|wx.EXPAND, 3)

        staticsizer_CONTENU = wx.StaticBoxSizer(self.staticbox_CONTENU, wx.VERTICAL)
        gridsizer_CONTENU = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)
        gridsizer_CONTENU.Add(self.label_commentaire, 1, wx.LEFT, 10)
        gridsizer_CONTENU.Add(self.txt_commentaire, 1, wx.LEFT|wx.EXPAND, 0)
        gridsizer_CONTENU.Add(self.label_infos, 1, wx.LEFT, 10)
        gridsizer_CONTENU.Add(self.choice_infos, 1, wx.LEFT|wx.EXPAND, 0)
        gridsizer_CONTENU.AddGrowableCol(1)
        staticsizer_CONTENU.Add(gridsizer_CONTENU, 1, wx.RIGHT|wx.EXPAND,0)
        gridsizer_BASE.Add(staticsizer_CONTENU, 1,wx.ALL|wx.EXPAND, 3)

        gridsizer_BOUTONS = wx.FlexGridSizer(rows=1, cols=7, vgap=10, hgap=5)
        staticsizer_BOUTONS = wx.StaticBoxSizer(self.staticbox_BOUTONS, wx.VERTICAL)
        gridsizer_BOUTONS.Add(self.bouton_avoir, 0, 0, 0)
        gridsizer_BOUTONS.Add(self.bouton_compl, 0, 0, 0)
        gridsizer_BOUTONS.Add((15, 15), 0, 0, 0)
        gridsizer_BOUTONS.Add(self.bouton_ok_direct, 0, 0, 0)
        gridsizer_BOUTONS.Add(self.bouton_ok, 0, 0, 0)
        gridsizer_BOUTONS.Add(self.bouton_annuler, 0, 0, 0)
        gridsizer_BOUTONS.AddGrowableCol(1)
        staticsizer_BOUTONS.Add(gridsizer_BOUTONS, 1, wx.RIGHT|wx.EXPAND, 5)
        gridsizer_BASE.Add(staticsizer_BOUTONS, 1, wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND, 5)

        self.SetSizer(gridsizer_BASE)
        gridsizer_BASE.Fit(self)
        gridsizer_BASE.AddGrowableRow(5)
        gridsizer_BASE.AddGrowableCol(0)
        self.Layout()
        self.CentreOnScreen()
        #fin do_layout

    def GetNomsNatureEtat(self,dictDonnees):
        nature, etat = "",""
        IDnature,i = 0,0
        self.naturePiece = dictDonnees["nature"]
        for a,b,c in self.liste_naturesPieces:
            if a == self.naturePiece:
                nature = b
                IDnature=i
            i+=1
        codeEtat = dictDonnees["etat"][IDnature]
        for a,b,c in self.liste_etatsPieces:
            if a == codeEtat: etat = dictDonnees["etat"]+" "+b+" : "+ c
            if a == dictDonnees["etat"][5:6] : etat += " "+b+" : "+ c

        return nature, etat
        #fin GetNomsNatureEtat

    def AffichePrix2(self):
        prix = 0.00
        listeLignes = self.dictDonnees["lignes_piece"]
        for dictLigne in listeLignes:
            if dictLigne["montant"] == 0:
                prix +=  dictLigne["quantite"] * dictLigne["prixUnit"]
            else: prix += dictLigne["montant"]
        self.ctrl_prix2.SetValue(str("{:10.2f}".format((prix))))
        if self.dictDonnees["nature"] == "AVO":
            self.ctrl_prix2.SetValue("0")

    def On_ctrl_famille(self, event):
            self.ctrl_nom_famille.Enable(False)
            msg = GestionDB.Messages()
            msg.Box(message = "Pour modifier les éléments de la famille il faut passer par le bouton plus à droite !")

    def On_ctrl_nom_nature(self, event):
            self.ctrl_nom_nature.Enable(False)
            msg = GestionDB.Messages()
            msg.Box(message = "Pour modifier l'état de la pièce il faut passer par le bouton plus à droite !")

    def On_ctrl_activite(self, event):
            self.ctrl_nom_activite.Enable(False)
            self.ctrl_nom_groupe.Enable(False)
            self.ctrl_nom_tarif.Enable(False)
            msg = GestionDB.Messages()
            msg.Box(message = "Pour modifier les éléments de l'activité il faut passer par le bouton plus à droite !")

    def On_ctrl_prix2(self, event):
            self.ctrl_prix2.Enable(False)
            msg = GestionDB.Messages()
            msg.Box(message = "Pour modifier les éléments de prix il faut passer par le bouton plus à droite !")

    def On_famille(self, event):
        self.ctrl_nom_famille.Enable(True)
        self.nom_famille = ""
        DB = GestionDB.DB()
        fGest = GestionInscription.Forfaits(self.parent,DB=DB)
        #dlg = DLG_Inscription.Dialog(self)
        appel = fGest.GetFamille(self)
        if not appel:
            msg = GestionDB.Messages()
            msg.Box(message = "Pour ajouter des familles associées à un individu il faut entrer dans la famille manquante et créer des rattachements !")
            msg.Destroy()
            return
        self.IDcompte_payeur = fGest.GetPayeurFamille(self,self.IDfamille)
        self.nom_famille = DB.GetNomFamille( self.IDcompte_payeur)
        self.nom_payeur = self.nom_famille
        self.ctrl_nom_famille.SetValue(self.nom_famille)
        self.ctrl_nom_payeur.SetValue(self.nom_payeur)
        commentaire = Decod(self.dictDonnees["commentaire"])
        commentaire = str(datetime.date.today()) + " Famille : " + self.nom_famille + "\n" + commentaire
        self.listeDonnees = [
            ("IDfamille", self.IDfamille ),
            ("IDcompte_payeur", self.IDcompte_payeur),
            ("nom_famille", self.nom_famille),
            ("nom_payeur", self.nom_payeur),
            ]
        self.dictDonnees = fGest.ModifDictDonnees(self,self.listeDonnees)
        DB.Close()
        self.modifPrestations = True
        self.modifConsommations = True
        self.modifInscriptions = True
        self.modifPieces = True
        fGest.DB.Close()

    def On_activite(self, event):
        self.ctrl_nom_activite.Enable(True)
        self.ctrl_nom_groupe.Enable(True)
        self.ctrl_nom_tarif.Enable(True)
        # Ouverture de la fenêtre d'inscription choix de l'activité, groupe, catTarif
        dlg = DLG_Inscription.Dialog(self,IDindividu=self.IDindividu)
        dlg.SetFamille(self.listeNoms, self.listeFamille, self.IDfamille, False)
        choixInscription = dlg.ShowModal()
        if choixInscription != wx.ID_OK:
            dlg.Destroy()
            return
        IDgroupe =  dlg.GetIDgroupe()
        IDcategorie_tarif = dlg.GetIDcategorie()
        if IDgroupe == None or IDcategorie_tarif == None :
            GestionDB.MessageBox(self,"Pour une inscription il faut préciser une activité, un groupe et une catégorie de tarif!\nIl y a aussi la possibilité de facturer sans inscription")
            dlg.Destroy()
            return
        nom_activite = dlg.GetNomActivite()
        nom_groupe = dlg.GetNomGroupe()
        nom_categorie = dlg.GetNomCategorie()
        self.ctrl_nom_activite.SetValue(nom_activite)
        self.ctrl_nom_groupe.SetValue(nom_groupe)
        self.ctrl_nom_tarif.SetValue(nom_categorie)
        self.IDactivite = dlg.GetIDactivite()
        fGest = GestionInscription.Forfaits(self.parent)
        self.IDcompte_payeur = fGest.GetPayeurFamille(self,self.IDfamille)
        if self.dictDonneesOrigine["IDcategorie_tarif"] != IDcategorie_tarif or self.dictDonneesOrigine["IDgroupe"] != IDgroupe :
            commentaire = Decod(self.dictDonnees["commentaire"])
            commentaire = str(datetime.date.today()) + " Modifié: " + nom_activite + "-" + nom_groupe + "\n" + commentaire
            self.listeDonnees = [
                ("IDactivite", self.IDactivite),
                ("nom_activite", nom_activite),
                ("nom_groupe", nom_groupe),
                ("IDgroupe", IDgroupe),
                ("IDcategorie_tarif", IDcategorie_tarif),
                ("commentaire", commentaire),
                ]
            self.txt_commentaire.SetValue(commentaire)
            self.dictDonnees = fGest.ModifDictDonnees(self,self.listeDonnees)
            self.modifPrestations = True
            self.modifConsommations = True
            self.modifInscriptions = True
            self.modifPieces = True
            self.bouton_ok_direct.Enable(False)
            #self.bouton_compl.Enable(False)
            self.dictDonnees["origine"]= "ajout"
            self.On_prix2(event)
            self.dictDonnees["origine"]= "modif"
        fGest.DB.Close()
        del fGest
        dlg.Destroy()

    def On_prix1(self, event):
        origine = self.dictDonneesOrigine["origine"]
        self.dictDonneesOrigine["origine"]= "lecture"
        fTar = DLG_PrixActivite.DlgTarification(self,self.dictDonneesOrigine)
        fTar.ShowModal()
        self.dictDonneesOrigine["origine"]= origine

    def On_prix2(self, event):
        # récupération des lignes de l'inscription génération de la piece
        fTar = DLG_PrixActivite.DlgTarification(self,self.dictDonnees)
        tarification = fTar.ShowModal()
        if not(tarification == wx.ID_OK): return
        etatPiece = self.dictDonneesOrigine["etat"]
        listeLignesPiece = fTar.listeLignesPiece
        #la nature de pièce a changé
        if (self.naturePiece != fTar.codeNature) and (fTar.codeNature != None):
            self.naturePiece = fTar.codeNature
            self.dictDonnees["nature"] = self.naturePiece
            i = self.liste_codesNaturePiece.index(self.naturePiece)
            # Mise à "1" du caractère en la position correspondant à la nature de la pièce (ex: FAC = 4eme)
            etatPiece = etatPiece[:i]+"1"+ etatPiece[i+1:]
            self.dictDonnees["etat"] = etatPiece
            nature, etat = self.GetNomsNatureEtat(self.dictDonnees)
            self.ctrl_nom_nature.SetValue(nature)
            self.ctrl_nom_etat.SetValue(etat)
            commentaire = Decod(self.dictDonnees["commentaire"])
            commentaire = str(datetime.date.today()) + " Nature: " + nature + "\n" + commentaire
            self.dictDonnees["commentaire"] = commentaire
            self.txt_commentaire.SetValue(commentaire)
        #si le montant a changé
        if self.dictDonnees["lignes_piece"] != listeLignesPiece:
            self.dictDonnees["lignes_piece"] = listeLignesPiece
            self.AffichePrix2()
            commentaire = Decod(self.dictDonnees["commentaire"])
            commentaire = "%s Montant modifié " % str((datetime.date.today()))+ "\n" + commentaire
            self.dictDonnees["commentaire"] = commentaire
            self.txt_commentaire.SetValue(commentaire)
        # récup parrainage
        self.dictDonnees["IDparrain"] = fTar.IDparrain
        self.dictDonnees["parrainAbandon"] = fTar.parrainAbandon
        self.modifPrestations = True
        self.modifPieces = True

    def On_piece(self, event):
        fGest = GestionInscription.Forfaits(self.parent)
        self.ctrl_nom_nature.Enable(True)
        interroChoix = wx.ID_CANCEL
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_factures", "creer")  :
            dlg = DLG_ValidationPiece.Dialog(self,"modif")
            interroChoix = dlg.ShowModal()
            self.codeNature = dlg.codeNature
            #dlg.Destroy()
        if interroChoix != wx.ID_OK :
            return
        etatPiece = self.dictDonnees["etat"]
        i = self.liste_codesNaturePiece.index(self.codeNature)
        # Mise à "1" du caractère en la position correspondant à la nature de la pièce (ex: FAC = 4eme)
        etatPiece = etatPiece[:i]+"1"+ etatPiece[i+1:]
        self.dictDonnees["etat"] = etatPiece
        commentaire = Decod(self.dictDonnees["commentaire"])
        commentaire = str(datetime.date.today()) + " Nature: " + self.codeNature + "\n" + commentaire
        self.dictDonnees["commentaire"] = commentaire
        self.txt_commentaire.SetValue(commentaire)
        self.listeDonnees = [
            ("nature", self.codeNature),
            ("etat", etatPiece),
            ]
        self.dictDonnees = fGest.ModifDictDonnees(self,self.listeDonnees)
        nature,etat = self.GetNomsNatureEtat(self.dictDonnees)
        self.ctrl_nom_nature.SetValue(nature)
        self.ctrl_nom_etat.SetValue(etat)
        self.modifPrestations = True
        self.modifConsommations = True
        self.modifPieces = True
        fGest.DB.Close()
        del fGest
        #fin OnPiece

    def On_commentaire(self, event):
        fGest = GestionInscription.Forfaits(self.parent)
        self.listeDonnees = [
            ("commentaire", self.txt_commentaire.GetValue()),
            ]
        self.dictDonnees = fGest.ModifDictDonnees(self,self.listeDonnees)        
        self.modifPieces = True
        fGest.DB.Close()
        del fGest

    def OnBoutonAvoir(self,event):
        if not UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_factures", "creer")  :
            return
        # generation de l'avoir dans les tables factures et pièces
        pGest = GestionPieces.Forfaits(self)
        ret = pGest.GenereAvoir(self.dictDonnees)
        if ret == wx.ID_ABORT:
            self.EndModal(wx.ID_ABORT)
            return wx.ID_ABORT
        self.txt_commentaire.SetValue(Decod(self.dictDonnees["commentaire"]))
        nature,etat = self.GetNomsNatureEtat(self.dictDonnees)
        self.rw = False
        self.ctrl_nom_etat.SetValue(etat)
        self.bouton_ok_direct.Enable(False)
        self.bouton_ok.Enable(False)
        self.EndModal(wx.ID_BOTTOM)
        #fin OnBoutonAvoir

    def OnBoutonCompl(self, event):
        # par le retour ID_APPLY le traitement  d'un complément sera lancé par DLG_InscriptionMenu
        self.EndModal(wx.ID_APPLY)
        self.Destroy()

    def OnBoutonOkDirect(self, event):
        fGest = GestionInscription.Forfaits(self)
        self.dictDonnees["IDprestation"] = None
        if not self.rw:
            # Enregistre dans Pieces pour les commentaires modifiés seulement
            fGest.ModifiePiece(self, self.dictDonnees)
            self.Destroy()
            return
        fGest.DB.Close()
        del fGest
        self.Final()

    def OnBoutonOk(self, event):
        self.dictDonnees["IDprestation"] = None
        if not self.rw:
            fTransp = DLG_InscriptionComplements.DlgTransports(self.dictDonnees,modeVirtuel = True)
            transports = fTransp.ShowModal()
            self.Destroy()
            return
        # Gestion des compléments de facturation
        fTransp = DLG_InscriptionComplements.DlgTransports(self.dictDonnees)
        transports = fTransp.ShowModal()
        self.dictDonnees = fTransp.GetDictDonnees(self.dictDonnees)
        if transports != wx.ID_OK:
           # Demande d'annulation des transports
            dlg = wx.MessageDialog(self, _("Souhaitez-vous supprimer les transports?\nSinon ils resteront en l'état"), _("Confirmation de suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
            rep = dlg.ShowModal()
            if rep == wx.ID_YES :
                fGest = GestionInscription.Forfaits(self)
                self.dictDonnees["prixTranspAller"] = None
                self.dictDonnees["prixTranspRetour"] = None
                fGest.SupprimeTransport(self.dictDonnees["IDtranspAller"])
                fGest.SupprimeTransport(self.dictDonnees["IDtranspRetour"])
                self.dictDonnees["IDtranspAller"] = None
                self.dictDonnees["IDtranspRetour"] = None
                fGest.DB.Close()
                del fGest
            else:
                GestionDB.MessageBox(self, "Vous n'avez pas géré les transports !\nIls restent en l'état antérieur")
                self.dictDonnees["prixTranspAller"] = self.dictDonneesOrigine["prixTranspAller"]
                self.dictDonnees["prixTranspRetour"] = self.dictDonneesOrigine["prixTranspRetour"]
            dlg.Destroy()
        fTransp.Destroy()
        if (self.dictDonnees["prixTranspAller"],self.dictDonnees["prixTranspRetour"]) != (self.dictDonneesOrigine["prixTranspAller"],self.dictDonneesOrigine["prixTranspRetour"]):
            self.modifPrestations = True
        self.Final()

    def NbreJours(self,fGest):
        # Gestion du nombre de jours modifié
        if "nbreJours" in self.dictDonnees:
            fGest.ModifieNbreJours(self,self.dictDonnees)
        return

    def Final(self):
        fGest = GestionInscription.Forfaits(self)
        # Enregistre l'inscription façon noethys
        if self.modifInscriptions == True:
            fGest.ModifieInscription(self,self.dictDonnees)

        # Enregistre dans Pieces
        fGest.ModifiePiece(self,self.dictDonnees)

        # arret du traitement si seulement devis
        if self.naturePiece == "DEV":
            fGest.DelConsommations(self)
            fGest.DelPrestations(self)
            self.NbreJours(fGest)
            self.EndModal(wx.ID_OK)
            fGest.DB.Close()
            self.Destroy()
            return
            # Enregistre les consommations
        if self.modifConsommations == True:
            fGest.DelConsommations(self)
            ajout = fGest.AjoutConsommations(self,self.dictDonnees)
            if not ajout :
                self.dictDonnees["nature"] = "DEV"
                id = fGest.ModifiePieceCree(self,self.dictDonnees)
                self.NbreJours(fGest)
                self.EndModal(wx.ID_OK)
                fGest.DB.Close()
                self.Destroy()
                return
        self.NbreJours(fGest)
        # arret du traitement si seulement réservation
        if self.naturePiece not in ("COM","FAC","AVO"):
            fGest.DelPrestations(self)
            fGest.DB.Close()
            self.EndModal(wx.ID_OK)
            self.Destroy()
            return
        # Enregistre la prestation
        self.dictDonnees["IDprestation"] = self.dictDonneesOrigine["IDprestation"]
        if self.modifPrestations == True:
            IDprestation = fGest.AjoutPrestation(self,self.dictDonnees,modif=True)
            if IDprestation > 0:
                self.dictDonnees["IDprestation"] = IDprestation
            fGest.ModifieConsoCree(self,self.dictDonnees)
            fGest.ModifiePieceCree(self,self.dictDonnees)
        else:
            fGest.ModifiePieceCree(self,self.dictDonnees)
        self.EndModal(wx.ID_OK)
        fGest.DB.Close()
        del fGest
        self.Destroy()
        #fin final

if __name__ == "__main__":
    app = wx.App(0)
    listeDonnees = [
        ("IDinscription",6938),
        ("IDindividu", 13481),
        ("IDfamille", 5325),
        ("origine", "lecture"),
        ("etat", "00000"),
        ("IDactivite", 221),
        ("IDgroupe", 442),
        ("IDcategorie_tarif", 795),
        ("IDcompte_payeur", 6163),
        ("date_inscription", "2016-01-01"),
        ("parti", False),
        ("nature", "COM"),
        ("nom_activite", "Sejour 41 Mon activite"),
        ("nom_groupe", "Groupe Pasto Plus"),
        ("nom_payeur", "celui qui paye"),
        ("nom_categorie_tarif", "Tarif Normal"),
        ("nom_individu", "nom de  l'individu"),
        ("commentaire", "differents commentaires"),
        ("nom_famille", "nom de la famille"),
        ("lignes_piece",[{'utilisateur': 'NoName', 'quantite': 1.0, 'montant': 800.0, 'codeArticle': 'SEJ_CORSE_S1', 'libelle': 'Sejour Jeunes Corse S1', 'IDnumPiece': 10, 'prixUnit': 500.0, 'date': '2016-07-27', 'IDnumLigne': 190}, {'utilisateur': 'NoName', 'quantite': 1.0, 'montant': 10.0, 'codeArticle': 'ZLUN', 'libelle': 'Option lunettes de soleil', 'IDnumPiece': 10, 'prixUnit': 10.0, 'date': '2016-07-27', 'IDnumLigne': 191}, {'utilisateur': 'NoName', 'quantite': 1.0, 'montant': 90.0, 'codeArticle': 'ART4', 'libelle': 'Quatrieme article', 'IDnumPiece': 10, 'prixUnit': 90.0, 'date': '2016-07-27', 'IDnumLigne': 192}]),
        ]
    dictDonnees = {}
    listeChamps = []
    listeValeurs = []
    for donnee in listeDonnees:
        champ = donnee[0]
        valeur = donnee[1]
        dictDonnees[champ] = valeur
        listeChamps.append(champ)
        listeValeurs.append(valeur)
    dlg = Dialog(None,dictDonnees,None)
    app.SetTopWindow(dlg)
    dlg.ShowModal()
    chaine = Cchaine(None)
    app.MainLoop()
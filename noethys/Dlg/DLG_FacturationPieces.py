#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Licence:         Licence GNU GPL
# Gestion des pieces niveau payeur en vue de facturation
# Derive de DLG_Famille_prestations
#------------------------------------------------------------------------

from Utils.UTILS_Traduction import _
import Chemins
import wx
import copy
import GestionDB
import datetime

from Ol import OL_FacturationPieces
from Dlg import DLG_PrixFamille
from Gest import GestionArticle
from Gest import GestionInscription
from Gest import GestionPieces
from Gest import GestionCoherence
import wx.lib.agw.hyperlink as Hyperlink
from Ctrl import CTRL_Bandeau
from Ctrl import CTRL_Bouton_image
from Utils import UTILS_Utilisateurs
from Utils import UTILS_Config

SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")

class Hyperlien(Hyperlink.HyperLinkCtrl):
    def __init__(self, parent, id=-1, label="", infobulle="", URL="", listeChoix=[], indexChoixDefaut=None, champFiltre="", labelDefaut="", size=(-1, -1), pos=(0, 0)):
        Hyperlink.HyperLinkCtrl.__init__(self, parent, id, label, URL=URL, size=size, pos=pos)
        self.parent = parent
        self.listeChoix = listeChoix
        self.indexChoixDefaut = indexChoixDefaut
        self.champFiltre = champFiltre
        self.labelDefaut = labelDefaut

        if self.GetGrandParent().GetName() == "notebook" :
            self.SetBackgroundColour(self.GetGrandParent().GetThemeBackgroundColour())

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
    
    def SetListeChoix(self, listeChoix=[]):
        self.listeChoix = listeChoix
        
    def OnLeftLink(self, event):
        self.listeChoix.sort()
        listeItems = [self.labelDefaut,]
        for label, ID in self.listeChoix :
            listeItems.append(label)
        dlg = wx.SingleChoiceDialog(self, _("Choisissez un filtre dans la liste suivante :"), _("Filtrer la liste"), listeItems, wx.CHOICEDLG_STYLE)
        if self.indexChoixDefaut != None and self.indexChoixDefaut < len(self.listeChoix) :
            dlg.SetSelection(self.indexChoixDefaut)
        if dlg.ShowModal() == wx.ID_OK:
            indexChoix = dlg.GetSelection() - 1
            # Modification du label de l'hyperlien
            if indexChoix == -1 :
                self.SetLabel(self.labelDefaut)
                self.indexChoixDefaut = None
                ID = None
            else:
                self.SetLabel(self.listeChoix[indexChoix][0])
                self.indexChoixDefaut = self.listeChoix[indexChoix][1]
                ID = self.listeChoix[indexChoix][1]
            # MAJ
            self.parent.olv_piecesFiltrees.SetFiltre(self.champFiltre, ID)
            self.parent.gridsizer_options.Layout()
            self.parent.Refresh() 
        dlg.Destroy()
        self.UpdateLink()

# -----------------------------------------------------------------------------------------------------------------------
    def MAJ(self):
        self.listeDonnees = []
        self.Importation_factures()
        listeItems = []
        if len(self.listeDonnees) > 0 :
            for dictValeurs in self.listeDonnees :
                label = dictValeurs["nom"]
                if label == None :
                    label = "Inconnu (ID%d)" % dictValeurs["ID"]
                listeItems.append(label)
        self.Set(listeItems)

    def Importation_factures(self):
        db = GestionDB.DB()
        req = """SELECT activites.IDactivite, nom, nbre_inscrits_max, COUNT(inscriptions.IDinscription)
        FROM activites
        LEFT JOIN inscriptions ON inscriptions.IDactivite = activites.IDactivite
        %s
        GROUP BY activites.IDactivite, nom, nbre_inscrits_max, 
        ORDER BY nom; """
        db.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = db.ResultatReq()
        db.Close()
        for IDactivite, nom, nbre_inscrits_max, nbre_inscrits in listeDonnees :
            valeurs = { "ID" : IDactivite, "nom" : nom, "nbre_inscrits_max" : nbre_inscrits_max, "nbre_inscrits" : nbre_inscrits }
            self.listeDonnees.append(valeurs)

class PnlFactures(wx.Panel):
    def __init__(self, parent,IDpayeur=None):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.DB = parent.DB
        self.parent = parent
        self.IDpayeur = IDpayeur
        self.listviewAvecFooter = OL_FacturationPieces.ListviewAvecFooter(self, kwargs={"IDpayeur" : IDpayeur, "factures" : True, "parent" : self.parent})
        self.olv_piecesFiltrees = self.listviewAvecFooter.GetListview()

        gridsizer_base = wx.FlexGridSizer(rows=1, cols=1, vgap=0, hgap=0)
        gridsizer_base.Add(self.listviewAvecFooter, 1, wx.EXPAND, 0)
        self.SetSizer(gridsizer_base)
        #gridsizer_base.Fit(self)
        gridsizer_base.AddGrowableCol(0)
        gridsizer_base.AddGrowableRow(0)
        self.Layout()
        self.olv_piecesFiltrees.CocheRien()
        #
        #self.olv_piecesFiltrees.MAJ()
        #self.Refresh()

class Dialog(wx.Dialog):
    def __init__(self, parent, IDpayeur=None):
        wx.Dialog.__init__(self, parent, -1, pos=(3,3),  style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX)
        self.parent = parent
        self.DB = GestionDB.DB()
        self.fGest = GestionInscription.Forfaits(self,self.DB)

        self.IDuser = self.DB.IDutilisateurActuel()
        self.rw = UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_facturation", "creer", afficheMessage=False)
        nomPayeur = self.DB.GetNomIndividu(IDpayeur)

        diag = GestionCoherence.Diagnostic(self,IDpayeur)
        del diag

        self.titre = ("PIECES DEJA FACTUREES et PIECES A FACTURER")
        intro = "Payeur " + nomPayeur
        self.SetTitle("DLG_FacturationPieces")
        self.IDpayeur = IDpayeur
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=self.titre, texte=intro,  hauteurHtml=15, nomImage="Images/22x22/Smiley_nul.png")
        self.staticbox_factures = wx.StaticBox(self, -1, _("Factures de l'exercice"))
        self.ctrl_factures = PnlFactures(self,self.IDpayeur)
        self.ctrl_factures.SetMinSize((-1, 80))

        self.staticbox_pieces = wx.StaticBox(self, -1, _("Pieces non facturées"))
        # OL Pieces
        self.listviewAvecFooter = OL_FacturationPieces.ListviewAvecFooter(self, kwargs={"IDpayeur" : IDpayeur,
                                                                                        "factures" : False,
                                                                                        "parent" : self})
        self.olv_piecesFiltrees = self.listviewAvecFooter.GetListview()
        self.ctrl_recherche = OL_FacturationPieces.CTRL_Outils(self, listview=self.olv_piecesFiltrees, afficherCocher=True)
        self.ctrl_recherche.SetBackgroundColour((255, 255, 255))

        # Commandes boutons à droite Haut
        self.bouton_imprimerFact = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_mailerFact = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Emails_exp.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_supprimerFact = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_ANY))
        # Commandes boutons à droite Bas
        self.bouton_monter = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Fleche_haut.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_descendre = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Fleche_bas.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_supprimer = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_imprimerDev = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_mailerDev = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Emails_exp.png"), wx.BITMAP_TYPE_ANY))

        # Pied
        #self.staticbox_pied= wx.StaticBox(self, -1, )
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Facturer\n les devis"), cheminImage="Images/32x32/Generation.png")
        self.bouton_devis = CTRL_Bouton_image.CTRL(self, texte=_("Imprimer\nEnsemble"), cheminImage="Images/32x32/Imprimante.png")
        self.bouton_modif = CTRL_Bouton_image.CTRL(self, texte=_("Modifier\nTypeDevis"), cheminImage="Images/32x32/zoom_tout.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Fermer"), cheminImage="Images/32x32/Annuler.png")

        #self.__set_data()
        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.SetMinSize((1000, 600))
        self.bouton_ok.Enable(self.rw)
        self.bouton_devis.Enable(self.rw)
        self.bouton_modif.Enable(self.rw)
        # Binds
        self.Bind(wx.EVT_BUTTON, self.OnBoutonImprimerFact, self.bouton_imprimerFact)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonMailerFact, self.bouton_mailerFact)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSupprimerFact, self.bouton_supprimerFact)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonMonter, self.bouton_monter)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonDescendre, self.bouton_descendre)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSupprimer, self.bouton_supprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonImprimerDev, self.bouton_imprimerDev)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonMailerDev, self.bouton_mailerDev)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOK, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonImprimerTout, self.bouton_devis)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonModif, self.bouton_modif)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)

        # Propriétés
        self.bouton_imprimerFact.SetToolTip(_("Cliquez ici pour imprimer les factures"))
        self.bouton_mailerFact.SetToolTip(_("Cliquez ici pour envoyer par mail les factures"))
        self.bouton_supprimerFact.SetToolTip(_("Cliquez ici pour supprimer la facture selectionnée"))
        self.bouton_monter.SetToolTip(_("Cliquez ici pour monter la pièce sélectionnée d'un niveau"))
        self.bouton_descendre.SetToolTip(_("Cliquez ici pour descendre la pièce sélectionnée d'un niveau"))
        self.bouton_supprimer.SetToolTip(_("Cliquez ici pour supprimer la piece sélectionnée"))
        self.bouton_imprimerDev.SetToolTip(_("Cliquez ici pour imprimer les devis"))
        self.bouton_mailerDev.SetToolTip(_("Cliquez ici pour envoyer par mail les devis"))
        self.bouton_ok.SetToolTip(_("Facturer en une seule facture, les pièces devis cochées"))
        self.bouton_devis.SetToolTip(_("Imprimer toutes les pièces cochées y compris factures"))
        self.bouton_modif.SetToolTip(_("Modifier la nature des pièces devis cochées"))
        self.olv_piecesFiltrees.SetToolTip(_("DéCochez les pièces que vous ne voulez pas ensemble"))

    def __do_layout(self):
        # Layout
        gridsizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=5, hgap=5)
        gridsizer_base.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)
        staticbox_factures = wx.StaticBoxSizer(self.staticbox_factures, wx.VERTICAL)
        gridsizer_factures = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        gridsizer_factures.Add(self.ctrl_factures, 5, wx.EXPAND, 0)
        gridsizer_btnFact = wx.FlexGridSizer(rows=6, cols=1, vgap=5, hgap=5)
        gridsizer_btnFact.Add((10,30), 1,0, 0)
        gridsizer_btnFact.Add(self.bouton_supprimerFact, 1,0, 0)
        gridsizer_btnFact.Add((10,10), 1,0, 0)
        gridsizer_btnFact.Add(self.bouton_imprimerFact, 1, 0, 0)
        gridsizer_btnFact.Add(self.bouton_mailerFact, 1, 0, 0)
        gridsizer_btnFact.Add((10,110), 1, wx.EXPAND, 0)

        gridsizer_factures.Add(gridsizer_btnFact, 1, wx.EXPAND, 0)
        gridsizer_factures.AddGrowableCol(0)
        gridsizer_factures.AddGrowableRow(0)
        staticbox_factures.Add(gridsizer_factures, 5, wx.EXPAND|wx.ALL, 5)
        gridsizer_base.Add(staticbox_factures, 5, wx.EXPAND|wx.ALL, 5)

        staticbox_pieces = wx.StaticBoxSizer(self.staticbox_pieces, wx.VERTICAL)

        gridsizer_BAS = wx.FlexGridSizer(rows=2, cols=1, vgap=5, hgap=5)
        gridsizer_pieces = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)
        
        gridsizer_pieces.Add(self.listviewAvecFooter, 1, wx.EXPAND, 0)
        
        gridsizer_boutons = wx.FlexGridSizer(rows=6, cols=1, vgap=5, hgap=5)
        gridsizer_boutons.Add(self.bouton_monter, 0, wx.ALL, 0)
        gridsizer_boutons.Add(self.bouton_descendre, 0, wx.ALL, 0)
        gridsizer_boutons.Add(self.bouton_supprimer, 0, wx.ALL, 0)
        gridsizer_boutons.Add( (10, 10), 0, wx.ALL, 0)
        gridsizer_boutons.Add(self.bouton_imprimerDev, 0, wx.ALL, 0)
        gridsizer_boutons.Add(self.bouton_mailerDev, 0, wx.ALL, 0)
        gridsizer_pieces.Add(gridsizer_boutons, 1, wx.ALL, 0)
        
        gridsizer_pieces.Add(self.ctrl_recherche, 0, wx.EXPAND|wx.ALL, 0)
        gridsizer_pieces.AddGrowableCol(0)
        gridsizer_pieces.AddGrowableRow(0)

        gridsizer_BAS.Add(gridsizer_pieces, 1, wx.EXPAND|wx.ALL, 5)

        gridsizer_pied = wx.FlexGridSizer(rows=1, cols=5, vgap=10, hgap=10)
        gridsizer_pied.Add((15, 15), 0, wx.EXPAND, 0)
        gridsizer_pied.Add(self.bouton_devis, 0, 0, 0)
        gridsizer_pied.Add(self.bouton_modif, 0, 0, 0)
        gridsizer_pied.Add(self.bouton_ok, 0, 0, 0)
        gridsizer_pied.Add(self.bouton_annuler, 0, 0, 0)
        gridsizer_pied.AddGrowableCol(0)
        gridsizer_pied.AddGrowableRow(0)
        gridsizer_BAS.Add(gridsizer_pied, 1, wx.EXPAND|wx.ALL, 5)
        gridsizer_BAS.AddGrowableCol(0)
        gridsizer_BAS.AddGrowableRow(0)
        staticbox_pieces.Add(gridsizer_BAS, 1, wx.EXPAND|wx.ALL, 5)

        gridsizer_base.Add(staticbox_pieces, 1, wx.EXPAND|wx.ALL, 5)

        self.SetSizer(gridsizer_base)
        gridsizer_base.Fit(self)
        gridsizer_base.AddGrowableCol(0)
        gridsizer_base.AddGrowableRow(1)
        gridsizer_base.AddGrowableRow(2)

    def OnBoutonImprimerFact(self, event):
        fOl = self.ctrl_factures.olv_piecesFiltrees
        fOl.ImprimerPieces(None)
        #fin OnBoutonImprimerFact

    def OnBoutonMailerFact(self, event):
        self.ctrl_factures.olv_piecesFiltrees.EnvoyerEmail(None)

    def OnBoutonSupprimerFact(self, event):
        # Supprime les pièces facturées
        droitModif = UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("facturation_factures", "creer")
        if droitModif:
            self.ctrl_factures.olv_piecesFiltrees.Supprimer(None)
            #self.ctrl_factures.Refresh()
            self.olv_piecesFiltrees.MAJ()
        else:
            GestionDB.MessageBox(self, "Vous ne disposez pas des droits 'facturation_factures', 'creer' !", titre = "Utilisateur Noethys")

    def OnBoutonMonter(self, event):
        self.olv_piecesFiltrees.Monter(None)

    def OnBoutonDescendre(self, event):
        self.olv_piecesFiltrees.Descendre(None)

    def OnBoutonImprimerDev(self, event):
        fOl = self.olv_piecesFiltrees
        fOl.ImprimerPieces(None)
        #fin OnBoutonImprimerFact

    def OnBoutonImprimerTout(self, event):
        prefix = ""
        fOl = self.olv_piecesFiltrees
        listePieces = fOl.GetListeIDpieces()
        if len(listePieces) > 0:
            prefix = "DEV"
        fOl2 = self.ctrl_factures.olv_piecesFiltrees
        if len(fOl2.GetCheckedObjects()) > 0:
            prefix = "_".join([prefix,"FAC"])
            listeFactures = fOl2.GetListeIDpieces()
            listePieces += listeFactures
        if listePieces and len(listePieces) > 0 :
                fOl.LanceImpression(prefix,listePieces)

    def OnBoutonModif(self,event):
        objects = self.olv_piecesFiltrees.GetChoicesObjects()
        if len(objects) == 0:
            return
        if not self.VerifierFamille(objects):
            return
        from Dlg import DLG_ChoixTypePiece
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_factures", "creer")  :
            dlg = DLG_ChoixTypePiece.Dialog(self,"modif")
            interroChoix = dlg.ShowModal()
            self.codeNature = dlg.codeNature
            dlg.Destroy()
            if interroChoix != wx.ID_OK :
                return
        # Saisie du nouveau  code nature
        for selection in objects:
            listeChamps = GestionInscription.StandardiseNomsChamps(self.olv_piecesFiltrees.listeChamps)
            self.dictDonnees = OL_FacturationPieces.OlvToDict(self,listeChamps,selection)
            self.codeNatureOld = copy.deepcopy(self.dictDonnees["nature"])
            if self.codeNature == self.codeNatureOld :
                continue

            #Gestion de la modification
            self.fGest.ChangeNaturePiece(self,self.dictDonnees,self.codeNature)

        self.olv_piecesFiltrees.InitObjectListView()
        self.Refresh()
        #fin OnBoutonModif

    def OnBoutonAnnuler(self,event):
        self.listviewAvecFooter.ctrl_footer.listview.DB.Close()
        self.DB.Close()
        if self.IsModal():
            self.EndModal(wx.ID_OK)
        else: self.Destroy()

    def OnBoutonMailerDev(self, event):
        self.olv_piecesFiltrees.EnvoyerEmail(None)

    def OnBoutonSupprimer(self, event):
        # Supprime les pièces non facturées
        droitModif = UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_inscriptions", "modifier")
        if droitModif:
            ret = self.olv_piecesFiltrees.Supprimer(None)
            if ret == wx.OK:
                objects = self.olv_piecesFiltrees.GetObjects()
                if not self.VerifierFamille(objects):
                    wx.MessageBox("Il vous faut retourner dans 'Famille' pour réinitialiser les réductions !",
                                    titre="Après cette suppression")
            self.Refresh()
        else:
            GestionDB.MessageBox(self, "Vous ne disposez pas des droits 'individus_inscriptions' 'modifier' !", titre = "Utilisateur Noethys")

    def OnBoutonImprimer(self, event):
        if len(self.olv_piecesFiltrees.GetSelectedObjects()) == 0:
            noSelection = True
        else:
            noSelection = False
            ID = self.olv_piecesFiltrees.GetSelectedObjects()[0].IDnumPiece
                
        # Création du menu contextuel
        menuPop = wx.Menu()
        
        # Item Apercu avant impression
        item = wx.MenuItem(menuPop, 20, _("Aperçu avant impression"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=20)
        
        # Item Imprimer
        item = wx.MenuItem(menuPop, 30, _("Imprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=30)
        
        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Apercu(self, event):
        self.olv_piecesFiltrees.Apercu(None)

    def Imprimer(self, event):
        self.olv_piecesFiltrees.Imprimer(None)

    def Facturer(self,IDpayeur,objects):
        # Création d'une facture avec toutes les pièces cochées
        lstIDpieces = []
        for obj in objects:
            listeChamps = GestionInscription.StandardiseNomsChamps(self.olv_piecesFiltrees.listeChamps)
            dictDonnees = OL_FacturationPieces.OlvToDict(self,listeChamps,obj)
            lstIDpieces.append(dictDonnees['IDnumPiece'])
        if len(lstIDpieces) > 0:
            pGest = GestionPieces.Forfaits(self)
            ret = pGest.CreeFacture(IDpayeur,lstIDpieces,self.IDuser)
            if not ret:
                wx.MessageBox("Abandon de la facturation","Echec")

    def OnBoutonOK(self,event):
        objects = self.olv_piecesFiltrees.GetCheckedObjects()
        if len(objects) == 0:
            GestionDB.MessageBox(self,"Vous n'avez coché aucune ligne ! ",titre="Continuation impossible")
            return
        if not self.VerifierFamille(objects):
            return
        self.Facturer(self.IDpayeur,objects)
        self.MAJ()
        #fin OnBoutonOK

    def GetPieceFamille(self,annee):
        # return liste d'objets track de pièces niveau famille
        fGest = GestionInscription.Forfaits(self, DB=self.DB)
        ldPiece = fGest.GetPieceModif999(self,self.IDpayeur,annee)
        return  [OL_FacturationPieces.Track(x) for x in ldPiece]

    def Is999inObjects(self,piece,objects):
        ok = False
        for obj in objects:
            if piece == obj:
                ok = True
        return ok

    def VerifierFamille(self,objects):
        # Recherche de l'année des pièces devant migrer
        lstActivites = []
        lstAnnees = []
        dictDonnees = {}
        IDfamille = None
        okfin = True
        for track in objects:
            if track.IDactivite in lstActivites:
                continue
            IDfamille = track.IDcompte_payeur
            # Les pieces niveau familles n'ont pas IDactivite, mais IDinscription est l'année
            if not track.IDactivite:
                dte = datetime.date(track.IDinscription,1,1)
            else: dte = None
            (exerciceDeb, exerciceFin) = GestionArticle.AnneeAcad(self.DB,track.IDactivite,
                                                                  dte)
            if not exerciceFin.year in lstAnnees:
                lstAnnees.append(exerciceFin.year)
                lstActivites.append(track.IDactivite)

        dlg = None
        for annee in sorted(lstAnnees,reverse=True):
            ok = True
            dictDonnees["IDactivite"] = 0
            dictDonnees["pieIDinscription"] = annee
            dictDonnees["IDcompte_payeur"] = IDfamille
            dictDonnees["annee"] =annee
            dictDonnees['lanceur'] = 'facturation'
            if not dlg:
                dlg = DLG_PrixFamille.DlgTarification(self,dictDonnees)
            else:
                dlg.SetExercice(annee)
            lstAnomalies = dlg.TestReprise()
            if lstAnomalies:
                ok = False
                mess = "Anomalies dans la pièce 'Niveau famille'\n\n"
                for txt in lstAnomalies:
                    mess += txt +"\n"
                mess += "\nVoulez vous consulter ou modifier une proposition de correction?"
                ret = wx.MessageBox(mess,"RECALCUL FAMILLE",style= wx.YES_NO|wx.ICON_WARNING)
                if ret == wx.YES:
                    ret = dlg.ShowModal()
                if ret in (wx.ID_OK,):
                    ok = True
                    # Ajout la pièce niveau famille à la liste si elle n'y était pas
                    lstPiece999 = self.GetPieceFamille(annee)
                    for piece in lstPiece999:
                        if not self.Is999inObjects(piece,objects):
                            objects.append(piece)
            if not ok:
                okfin = False
                break
        if dlg:
            dlg.Destroy()
        # Mise à jour de l'affichage
        self.MAJ()
        return okfin

    def MAJ(self):
        """ MAJ integrale du controle avec MAJ des donnees """
        self.olv_piecesFiltrees.MAJ()
        self.ctrl_factures.olv_piecesFiltrees.MAJ()
        self.Refresh()

    def ValidationData(self):
        """ Return True si les données sont valides et pretes à être sauvegardées """
        return True
    
    def Sauvegarde(self):
        pass

if __name__ == '__main__':
    app = wx.App(0)
    dlg = Dialog(None, 4616)
    app.SetTopWindow(dlg)
    dlg.Show()
    app.MainLoop()


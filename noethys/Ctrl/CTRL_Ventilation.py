#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys Matthania pour saisies montants nuls
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB, Jacques Brunel
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#-----------------------------------------------------------


from Utils.UTILS_Traduction import _

import wx
import Chemins
import wx.grid as gridlib
import wx.lib.agw.hyperlink as Hyperlink
import datetime
import decimal
import sys

from Utils.UTILS_Decimal import FloatToDecimal as Ftd

from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "�")

import GestionDB
from Ctrl import CTRL_Saisie_euros

COULEUR_FOND_REGROUPEMENT = (200, 200, 200)
COULEUR_TEXTE_REGROUPEMENT = (140, 140, 140)

COULEUR_CASE_MODIFIABLE_ACTIVE = (255, 255, 255)
COULEUR_CASE_MODIFIABLE_INACTIVE = (230, 230, 230)

COULEUR_NUL = (255, 0, 0)
COULEUR_PARTIEL = (255, 193, 37)
COULEUR_TOTAL = (0, 238, 0)
            
def DateEngFr(textDate):
    if textDate == None: return ""
    textDate = str(textDate)
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text

def DateComplete(dateDD):
    """ Transforme une date DD en date compl�te : Ex : lundi 15 janvier 2008 """
    listeJours = (_("Lundi"), _("Mardi"), _("Mercredi"), _("Jeudi"), _("Vendredi"), _("Samedi"), _("Dimanche"))
    listeMois = (_("janvier"), _("f�vrier"), _("mars"), _("avril"), _("mai"), _("juin"), _("juillet"), _("ao�t"), _("septembre"), _("octobre"), _("novembre"), _("d�cembre"))
    dateComplete = listeJours[dateDD.weekday()] + " " + str(dateDD.day) + " " + listeMois[dateDD.month-1] + " " + str(dateDD.year)
    return dateComplete

def DateEngEnDateDD(dateEng):
    if dateEng and not isinstance(dateEng,str): dateEng = str(dateEng)
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))
        
def PeriodeComplete(mois, annee):
    listeMois = (_("Janvier"), _("F�vrier"), _("Mars"), _("Avril"), _("Mai"), _("Juin"), _("Juillet"), _("Ao�t"), _("Septembre"), _("Octobre"), _("Novembre"), _("D�cembre"))
    periodeComplete = "%s %d" % (listeMois[mois-1], annee)
    return periodeComplete

# --------------------------------------------------------------------------------------------------------------------

class Hyperlien(Hyperlink.HyperLinkCtrl):
    def __init__(self, parent, id=-1, label="", infobulle="", URL="", listeChoix=[], size=(-1, -1), pos=(0, 0)):
        Hyperlink.HyperLinkCtrl.__init__(self, parent, id, label, URL=URL, size=size, pos=pos)
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
        if self.URL == "automatique" : self.parent.VentilationAuto() 
        if self.URL == "tout" : self.parent.VentilationTout() 
        if self.URL == "rien" : self.parent.VentilationRien() 
        self.UpdateLink()

class Ligne_regroupement(object):
    def __init__(self, grid=None, numLigne=0, dictRegroupement={}):
        self.grid = grid
        self.type_ligne = "regroupement"
        self.numLigne = numLigne
        self.dictRegroupement = dictRegroupement
        self.listeLignesPrestations = []
        
        # Init ligne
        hauteurLigne = 20
        grid.SetRowSize(numLigne, hauteurLigne)

        # Attributs communes � toutes les colonnes
        for numColonne in range(0, 8) :
            self.grid.SetCellBackgroundColour(self.numLigne, numColonne, COULEUR_FOND_REGROUPEMENT)
            self.grid.SetReadOnly(self.numLigne, numColonne, True)

        # Case � cocher
        numColonne = 0
        self.grid.SetCellRenderer(self.numLigne, numColonne, gridlib.GridCellBoolRenderer())

        # Label du groupe
        self.grid.SetCellValue(self.numLigne, 1, self.dictRegroupement["label"])
        
        font = self.grid.GetFont() 
        font.SetWeight(wx.BOLD)
        self.grid.SetCellFont(self.numLigne, 1, font)
                
        # Montant prestation
        numColonne = 5
        self.grid.SetCellRenderer(self.numLigne, numColonne, RendererCaseMontant())
        font = self.grid.GetFont() 
        font.SetPointSize(8)
        self.grid.SetCellFont(self.numLigne, numColonne, font)

        # Montant d�j� ventil�
        numColonne = 6
        self.grid.SetCellRenderer(self.numLigne, numColonne, RendererCaseMontant())
        font = self.grid.GetFont() 
        font.SetPointSize(8)
        self.grid.SetCellFont(self.numLigne, numColonne, font)

        # Ventilation actuelle
        numColonne = 7
        self.grid.SetCellRenderer(self.numLigne, numColonne, RendererCaseMontant())
        font = self.grid.GetFont() 
        font.SetPointSize(8)
        self.grid.SetCellFont(self.numLigne, numColonne, font)
        
    def MAJ(self):
        # Calcul des totaux
        total_prestation = Ftd(0.0)
        total_aVentiler = Ftd(0.0)
        total_ventilationActuelle = Ftd(0.0)
        for ligne in self.listeLignesPrestations :
            total_prestation += ligne.montant
            total_aVentiler += ligne.resteAVentiler
            total_ventilationActuelle += ligne.ventilationActuelle
        
        # Affichage des totaux
        self.grid.SetCellValue(self.numLigne, 5, str(total_prestation))
        self.grid.SetCellValue(self.numLigne, 6, str(total_aVentiler))
        self.grid.SetCellValue(self.numLigne, 7, str(total_ventilationActuelle))

    def GetEtat(self):
        valeur = self.grid.GetCellValue(self.numLigne, 0)
        if valeur == "1" :
            return True
        else :
            return False
    
    def SetEtat(self, etat=False, majTotaux=True):
        self.grid.SetCellValue(self.numLigne, 0, str(int(etat)))

        # Coche ou d�coche les prestations du groupe
        for ligne in self.listeLignesPrestations :
            ligne.SetEtat(etat, majTotaux=False)
        
        # MAJ des totaux
        self.grid.MAJtotaux()
        
    def OnCheck(self):
        etat = not self.GetEtat() 
        self.SetEtat(etat)

class Ligne_prestation(object):
    def __init__(self, grid=None, donnees={}):
        self.grid = grid
        self.type_ligne = "prestation"

        # R�cup�ration des donn�es
        self.IDprestation = donnees["IDprestation"]
        self.IDcompte_payeur = donnees["IDcompte_payeur"]
        self.date = donnees["date"]
        self.date_complete = DateComplete(self.date)
        self.mois = self.date.month
        self.annee = self.date.year
        self.periode = (self.annee, self.mois)
        self.periode_complete = PeriodeComplete(self.mois, self.annee)
        self.categorie = donnees["categorie"]
        self.label = donnees["label"]
        self.montant = donnees["montant"]
        self.IDactivite = donnees["IDactivite"]
        self.nomActivite = donnees["nomActivite"]
        self.IDtarif = donnees["IDtarif"]
        self.nomTarif = donnees["nomTarif"]
        self.nomCategorieTarif = donnees["nomCategorieTarif"]
        self.IDfacture = donnees["IDfacture"]
        if self.IDfacture == None or self.IDfacture == "" :
            self.label_facture = _("Non factur�")
        else:
            num_facture = donnees["num_facture"]
            date_facture = donnees["date_facture"]
            if type(num_facture) == int :
                num_facture = str(num_facture)
            self.label_facture = "n�%s" % num_facture
        self.IDfamille = donnees["IDfamille"]
        self.IDindividu = donnees["IDindividu"]
        self.nomIndividu = donnees["nomIndividu"]
        self.prenomIndividu = donnees["prenomIndividu"]
        if self.prenomIndividu == None :
            self.prenomIndividu = ""
        if self.nomIndividu != None :
            self.nomCompletIndividu = "%s %s" % (self.nomIndividu, self.prenomIndividu)
        else:
            self.nomCompletIndividu = ""
        self.ventilationPassee = donnees["ventilationPassee"]
        if self.ventilationPassee == None :
            self.ventilationPassee = Ftd(0.0)
        self.ventilationActuelle = Ftd(0.0)
        self.resteAVentiler = self.montant - self.ventilationPassee - self.ventilationActuelle
                        
    def Draw(self, numLigne=0, ligneRegroupement=None):
        """ Dessine la ligne dans la grid """
        self.numLigne = numLigne
        self.ligneRegroupement = ligneRegroupement
        
        # Init ligne
        hauteurLigne = 25
        self.grid.SetRowSize(numLigne, hauteurLigne)
        
        # Case � cocher
        numColonne = 0
        self.grid.SetCellRenderer(self.numLigne, numColonne, gridlib.GridCellBoolRenderer())
        self.grid.SetReadOnly(self.numLigne, numColonne, True)
        
        # Date
        numColonne = 1
        self.grid.SetReadOnly(self.numLigne, numColonne, True)
        self.grid.SetCellAlignment(self.numLigne, numColonne, wx.ALIGN_LEFT, wx.ALIGN_CENTRE)

        # Individu
        numColonne = 2
        self.grid.SetReadOnly(self.numLigne, numColonne, True)
        self.grid.SetCellAlignment(self.numLigne, numColonne, wx.ALIGN_LEFT, wx.ALIGN_CENTRE)
        
        # Label prestation
        numColonne = 3
        self.grid.SetReadOnly(self.numLigne, numColonne, True)
        self.grid.SetCellAlignment(self.numLigne, numColonne, wx.ALIGN_LEFT, wx.ALIGN_CENTRE)

        # Facture
        numColonne = 4
        self.grid.SetCellAlignment(self.numLigne, numColonne, wx.ALIGN_CENTER, wx.ALIGN_CENTRE)
        self.grid.SetReadOnly(self.numLigne, numColonne, True)
        
        # Montant prestation
        numColonne = 5
        self.grid.SetCellRenderer(self.numLigne, numColonne, RendererCaseMontant())
        self.grid.SetReadOnly(self.numLigne, numColonne, True)
        
        # Montant d�j� ventil�
        numColonne = 6
        self.grid.SetCellRenderer(self.numLigne, numColonne, RendererCaseMontant())
        self.grid.SetReadOnly(self.numLigne, numColonne, True)

        # Ventilation actuelle
        numColonne = 7
        self.grid.SetCellRenderer(self.numLigne, numColonne, RendererCaseMontant())
        self.grid.SetCellEditor(self.numLigne, numColonne, EditeurMontant(ligne=self))

    def MAJ(self, majTotaux=True):
        """ MAJ les donn�es et l'affichage de la ligne """
        # MAJ des donn�es
        if type(self.ventilationActuelle) != decimal.Decimal :
            self.ventilationActuelle = Ftd(self.ventilationActuelle)

        self.resteAVentiler = self.montant - self.ventilationPassee - self.ventilationActuelle
        
        # Coche
        if self.ventilationActuelle != Ftd(0.0) :
            etat = True
        else :
            etat = False
        self.grid.SetCellValue(self.numLigne, 0, str(int(etat)))

        # Label
        self.grid.SetCellValue(self.numLigne, 1, DateComplete(self.date))
        
        # Individu
        self.grid.SetCellValue(self.numLigne, 2, self.prenomIndividu)

        # Label de la prestation
        self.grid.SetCellValue(self.numLigne, 3, self.label)

        # Facture
        self.grid.SetCellValue(self.numLigne, 4, self.label_facture)

        # Montant de la prestation
        self.grid.SetCellValue(self.numLigne, 5, str(self.montant))

        # Montant d�j� ventil�
        self.grid.SetCellValue(self.numLigne, 6, str(self.resteAVentiler))
        
        if self.resteAVentiler == 0.0 and self.GetEtat() == True : 
            self.grid.SetCellBackgroundColour(self.numLigne, 6, COULEUR_TOTAL)
        elif self.resteAVentiler == self.montant : 
            self.grid.SetCellBackgroundColour(self.numLigne, 6, COULEUR_NUL)
        else: 
            self.grid.SetCellBackgroundColour(self.numLigne, 6, COULEUR_PARTIEL)

        # Montant ventil�
        self.grid.SetCellValue(self.numLigne, 7, str(self.ventilationActuelle))
        self.grid.SetReadOnly(self.numLigne, 7, not self.GetEtat())

        if self.GetEtat() == True : 
            self.grid.SetCellBackgroundColour(self.numLigne, 7, COULEUR_CASE_MODIFIABLE_ACTIVE)
        else :
            self.grid.SetCellBackgroundColour(self.numLigne, 7, COULEUR_CASE_MODIFIABLE_INACTIVE)
        
        # MAJ de la ligne de regroupement
        if majTotaux == True :
            self.ligneRegroupement.MAJ() 
            self.grid.MAJbarreInfos()
        
    def GetEtat(self):
        valeur = self.grid.GetCellValue(self.numLigne, 0)
        if valeur == "1" :
            return True
        else :
            return False
    
    def SetEtat(self, etat=False, montant=None, majTotaux=True):
        # Coche la case
        self.grid.SetCellValue(self.numLigne, 0, str(int(etat)))
        
        # Attribue le montant
        if etat == False :
            montant = 0.0 
            
        if montant != None :
            # Tout ventiler
            self.ventilationActuelle = montant
        else:
            # Ventiler uniquement le montant donn�
            self.ventilationActuelle = self.resteAVentiler
            
        self.MAJ(majTotaux) 
        
    def OnCheck(self):
        etat = not self.GetEtat() 
        montant = None
        
        # Attribue uniquement du cr�dit encore disponible
        if etat == True :
            montant = self.grid.GetCreditAventiler()
            """
            if self.grid.parent.negatif:
                if montant < self.resteAVentiler or self.grid.bloquer_ventilation == False :
                    montant = self.resteAVentiler
            """
            if not self.grid.parent.negatif:
                if montant > self.resteAVentiler or self.grid.bloquer_ventilation == False :
                    montant = self.resteAVentiler
                
        # Modifie la ligne
        self.SetEtat(etat, montant)
        
        # D�coche le groupe si aucune prestation coch�e dedans
        if etat == False :
            auMoinsUneCochee = False
            for ligne in self.ligneRegroupement.listeLignesPrestations :
                if ligne.GetEtat() == True :
                    auMoinsUneCochee = True
            if auMoinsUneCochee == False :
                self.ligneRegroupement.SetEtat(False)

class RendererCaseMontant(gridlib.PyGridCellRenderer):
    def __init__(self):
        gridlib.PyGridCellRenderer.__init__(self)
        self.grid = None

    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        self.grid = grid
            
        # Dessin du fond de couleur
        couleurFond = self.grid.GetCellBackgroundColour(row, col)
        dc.SetBackgroundMode(wx.SOLID)
        dc.SetBrush(wx.Brush(couleurFond, wx.SOLID))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangle(rect)
                
        # Ecrit les restrictions
        texte = self.grid.GetCellValue(row, col)
        if texte != "" :
            texte = "%.2f %s " % (float(texte), SYMBOLE)
        
        dc.SetBackgroundMode(wx.TRANSPARENT)
        dc.SetFont(attr.GetFont())
        hAlign, vAlign = grid.GetCellAlignment(row, col)
        
        # Alignement � droite
        largeur, hauteur = dc.GetTextExtent(texte)
        x = rect[0] + rect[2] - largeur - 2
        y = rect[1] + ((rect[3] - hauteur) / 2.0)
        dc.DrawText(texte, x, y)
        
    def GetBestSize(self, grid, attr, dc, row, col):
        text = grid.GetCellValue(row, col)
        dc.SetFont(attr.GetFont())
        w, h = dc.GetTextExtent(text)
        return wx.Size(w, h)

    def Clone(self):
        return RendererCaseMontant()

class EditeurMontant(gridlib.PyGridCellEditor):
    def __init__(self, ligne=None):
        self.ligne = ligne
        gridlib.PyGridCellEditor.__init__(self)

    def Create(self, parent, id, evtHandler):
        self._tc = CTRL_Saisie_euros.CTRL(parent, style=wx.TE_RIGHT|wx.TE_PROCESS_ENTER)
        self._tc.SetInsertionPoint(0)
        self.SetControl(self._tc)
        if evtHandler:
            self._tc.PushEventHandler(evtHandler)
        
    def BeginEdit(self, row, col, grid):
        self.startValue = grid.GetTable().GetValue(row, col)
        self._tc.SetValue(self.startValue)
        self._tc.SetInsertionPointEnd()
        self._tc.SetFocus()
        # For this example, select the text
        self._tc.SetSelection(0, self._tc.GetLastPosition())

    def EndEdit(self, row, col, grid, oldVal):
        changed = False
        valeur = self._tc.GetMontant()
        # Validation du montant saisi
        if self._tc.Validation() == False :
            valeur = None
        # V�rifie si montant saisi pas sup�rieur � montant � ventil�
        if valeur != None :
            resteAVentiler = self.ligne.montant - self.ligne.ventilationPassee - Ftd(valeur)
            if resteAVentiler < 0 :
                dlg = wx.MessageDialog(grid, _("Le montant saisi ne peut pas �tre sup�rieur au montant � ventiler !"), _("Erreur"), wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                valeur = None
        # Renvoie la valeur
        if valeur != oldVal:  
            return valeur
        else:
            return None
    
    def ApplyEdit(self, row, col, grid):
        valeur = self._tc.GetMontant()
        grid.GetTable().SetValue(row, col, str(valeur))
        self.startValue = ''
        self._tc.SetValue('')
        # MAJ de la ligne
        self.ligne.ventilationActuelle = Ftd(valeur)
        self.ligne.MAJ() 
    
    def Reset(self):
        self._tc.SetValue(self.startValue)
        self._tc.SetInsertionPointEnd()

    def Destroy(self):
        super(EditeurMontant, self).Destroy()

    def Clone(self):
        return EditeurMontant()

# -------------------------------------------------------------------------------------------------------------------

class CTRL_Ventilation(gridlib.Grid): 
    def __init__(self, parent, IDcompte_payeur=None, IDreglement=None): 
        gridlib.Grid.__init__(self, parent, -1, style=wx.WANTS_CHARS)
        self.parent = parent
        self.IDcompte_payeur = IDcompte_payeur
        self.IDreglement = IDreglement
        self.listeTracks = []
        self.dictVentilation = {}
        self.dictVentilationInitiale = {}
        self.ventilationValide = True
        self.montant_reglement = Ftd(0.0)
        self.dictLignes = {}
        
        # Options
        self.bloquer_ventilation = False

        # Key de regroupement
        self.KeyRegroupement = "periode" # individu, facture, date, periode
        
        # Binds
        self.Bind(gridlib.EVT_GRID_CELL_LEFT_CLICK, self.OnLeftClick)
##        self.Bind(gridlib.EVT_GRID_CELL_RIGHT_CLICK, self.OnRightClick)
        self.GetGridWindow().Bind(wx.EVT_MOTION, self.OnMouseOver)
    
    def InitGrid(self):
        """ Cr�ation de la grid et importation initiale des donn�es """
        listeColonnes = [
            ( _(""), 20),
            ( _("Date"), 175),
            ( _("Individu"), 124),
            ( _("Intitul�"), 185),
            ( _("N� Facture"), 75),
            ( _("Montant"), 65),
            ( _("A ventiler"), 65),
            ( _("Ventil�"), 65),
            ]
        
        # Initialisation de la grid
        self.SetMinSize((10, 10))
        self.moveTo = None
        self.CreateGrid(0, len(listeColonnes))
        self.SetRowLabelSize(1)
        self.DisableDragColSize()
        self.DisableDragRowSize()
        self.modeDisable = False
        
        # Cr�ation des colonnes
        self.SetColLabelSize(22)
        numColonne = 0
        for label, largeur in listeColonnes :
            self.SetColLabelValue(numColonne, label)
            self.SetColSize(numColonne, largeur)
            numColonne += 1
        
        # Importation des donn�es
        self.listeLignesPrestations = self.Importation()
        
        # MAJ de l'affichage de la grid
        self.MAJ() 
        
        # Importation des ventilations existantes du r�glement
        for ligne_prestation in self.listeLignesPrestations :
            if ligne_prestation.IDprestation in self.dictVentilation :
                montant = self.dictVentilation[ligne_prestation.IDprestation]
                ligne_prestation.SetEtat(True, montant, majTotaux=False)
        self.MAJtotaux() 

    def Importation(self):
        if self.IDreglement == None :
            IDreglement = 0
        else:
            IDreglement = self.IDreglement
        
        # Importation des ventilations de ce r�glement
        DB = GestionDB.DB()
        req = """SELECT IDventilation, IDprestation, montant
        FROM ventilation
        WHERE IDreglement=%d
        ;""" % IDreglement
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()     
        self.dictVentilation = {}
        self.dictVentilationInitiale = {}
        for IDventilation, IDprestation, montant in listeDonnees :
            self.dictVentilation[IDprestation] = Ftd(montant)
            self.dictVentilationInitiale[IDprestation] = IDventilation

        # Importation des donn�es
        req = """
        SELECT prestations.IDprestation, prestations.IDcompte_payeur, date, categorie, label, prestations.montant, 
        prestations.IDactivite, activites.nom,
        prestations.IDtarif, noms_tarifs.nom, categories_tarifs.nom, 
        prestations.IDfacture, factures.numero, factures.date_edition,
        IDfamille, prestations.IDindividu, 
        individus.nom, individus.prenom,
        SUM(ventilation.montant) AS montant_ventilation
        FROM prestations
        LEFT JOIN ventilation ON prestations.IDprestation = ventilation.IDprestation
        LEFT JOIN activites ON prestations.IDactivite = activites.IDactivite
        LEFT JOIN individus ON prestations.IDindividu = individus.IDindividu
        LEFT JOIN tarifs ON prestations.IDtarif = tarifs.IDtarif
        LEFT JOIN noms_tarifs ON tarifs.IDnom_tarif = noms_tarifs.IDnom_tarif
        LEFT JOIN categories_tarifs ON tarifs.IDcategorie_tarif = categories_tarifs.IDcategorie_tarif
        LEFT JOIN factures ON prestations.IDfacture = factures.IDfacture
        WHERE prestations.IDcompte_payeur = %d 
        GROUP BY prestations.IDprestation, prestations.IDcompte_payeur, date, categorie, label, prestations.montant, 
                prestations.IDactivite, activites.nom,
                prestations.IDtarif, noms_tarifs.nom, categories_tarifs.nom, 
                prestations.IDfacture, factures.numero, factures.date_edition,
                IDfamille, prestations.IDindividu, 
                individus.nom, individus.prenom
        ORDER BY date
        ;""" % self.IDcompte_payeur
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()     
        DB.Close()
        listeLignesPrestations = []
        for IDprestation, IDcompte_payeur, date, categorie, label, montant, IDactivite, nomActivite, IDtarif, nomTarif, \
            nomCategorieTarif, IDfacture, num_facture, date_facture, IDfamille, IDindividu, nomIndividu, prenomIndividu,\
            montantVentilation in listeDonnees :
            montant = Ftd(montant)
            montantVentilation = Ftd(montantVentilation)
            if num_facture == None : num_facture = 0
            # V�rif coh�rence
            if (montant >= Ftd(0.0) and Ftd(montantVentilation) > montant) \
                    or (montant < Ftd(0.0) and Ftd(montantVentilation) < montant)\
                    or ((montant * Ftd(montantVentilation)) < 0.0):
                montant,montantVentilation = self.CorrigeVentilation(IDprestation)

            # Composition des donn�es OLV
            if (montant >= Ftd(0.0) and Ftd(montantVentilation) < montant) \
                    or (montant < Ftd(0.0) and Ftd(montantVentilation) > montant) \
                    or IDprestation in list(self.dictVentilation.keys()) :
                # On garde cette prestation pour pouvoir affecter le r�glement
                date = DateEngEnDateDD(date)
                if IDprestation in self.dictVentilation :
                    montantVentilation = montantVentilation - self.dictVentilation[IDprestation] 

                dictTemp = {
                    "IDprestation" : IDprestation, "IDcompte_payeur" : IDcompte_payeur, "date" : date, "categorie" : categorie,
                    "label" : label, "montant" : montant, "IDactivite" : IDactivite, "nomActivite" : nomActivite, "IDtarif" : IDtarif, "nomTarif" : nomTarif, 
                    "nomCategorieTarif" : nomCategorieTarif, "IDfacture" : IDfacture, "num_facture" : num_facture, "date_facture" : date_facture, 
                    "IDfamille" : IDfamille, "IDindividu" : IDindividu, "nomIndividu" : nomIndividu, "prenomIndividu" : prenomIndividu,
                    "ventilationPassee" : montantVentilation,
                    }
                ligne_prestation = Ligne_prestation(grid=self, donnees=dictTemp)
                listeLignesPrestations.append(ligne_prestation)
        return listeLignesPrestations

    def CorrigeVentilation(self,IDprestation):
        DB = GestionDB.DB()
        # suppression de ventilations orphelines de leur r�glement
        req = """DELETE ventilation
                FROM ventilation 
                    LEFT JOIN reglements ON ventilation.IDreglement = reglements.IDreglement
                WHERE ((reglements.IDreglement Is Null) AND (ventilation.IDprestation= %d))
                ;"""% IDprestation
        DB.ExecuterReq(req,MsgBox="CTRL_Ventilation.CorrigeVentil1")
        DB.Close()
        DB = GestionDB.DB()

        # appel du d�tail des ventilations.
        req = """SELECT ventilation.IDventilation,ventilation.montant, prestations.montant, reglements.IDreglement
                FROM (  ventilation 
                        LEFT JOIN reglements ON ventilation.IDreglement = reglements.IDreglement) 
                        INNER JOIN prestations ON ventilation.IDprestation = prestations.IDprestation
                WHERE ventilation.IDprestation=%d
                ORDER BY reglements.date_saisie
                ;""" % IDprestation
        DB.ExecuterReq(req,MsgBox="CTRL_Ventilation.CorrigeVentil2")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        lstSupprime = []
        mttcum = Ftd(0.0)
        montant = 0.0
        for IDventilation, ventile, montant, IDreglement in listeDonnees:
            montant = Ftd(montant)
            ventile = Ftd(ventile)
            # suppression de ventilation de signe invers�
            if (montant * ventile) < 0:
                lstSupprime.append(IDventilation)
                continue
            # suppression d'exc�dent d'affectation
            elif abs(montant) < abs(mttcum + ventile):
                lstSupprime.append(IDventilation)
                continue
            mttcum += ventile
        DB.Close()

        for IDventilation in lstSupprime:
            DB = GestionDB.DB()
            ret = DB.ReqDEL('ventilation','IDventilation',IDventilation,MsgBox=True)
            DB.Close()
        return montant,mttcum

    def OnLeftClick(self, event):
        numLigne = event.GetRow()
        numColonne = event.GetCol()
        # Checkbox
        if numLigne in self.dictLignes :
            ligne = self.dictLignes[numLigne]
            if numColonne == 7 and ligne.GetEtat() == True :
                pass
            else :
                ligne.OnCheck()
        # Case montant modifiable
        if numColonne == 7 and numLigne in self.dictLignes :
            ligne = self.dictLignes[numLigne]
            if ligne.type_ligne == "prestation" and ligne.GetEtat() == True :
                event.Skip()
    
    def OnMouseOver(self, event):    
        return
        
    def MAJ(self):
        """ Met � jour (redessine) tout le contr�le """
        self.Freeze()
        if self.GetNumberRows() > 0 : 
            self.DeleteRows(0, self.GetNumberRows())
        self.Remplissage()
        self.Thaw() 

    def Remplissage(self):
        # Regroupement
        self.dictRegroupements = {}
        listeKeys = []
        nbreLignes = 0
        for ligne_prestation in self.listeLignesPrestations :
            if self.KeyRegroupement == "individu" : 
                key = ligne_prestation.IDindividu
                if key == 0 or key == None :
                    label = _("Prestations familiales")
                else:
                    label = ligne_prestation.nomCompletIndividu
            if self.KeyRegroupement == "facture" : 
                key = ligne_prestation.IDfacture
                label = ligne_prestation.label_facture
            if self.KeyRegroupement == "date" : 
                key = ligne_prestation.date
                label = ligne_prestation.date_complete
            if self.KeyRegroupement == "periode" : 
                key = ligne_prestation.periode
                label = ligne_prestation.periode_complete
            
            if (key in self.dictRegroupements) == False :
                self.dictRegroupements[key] = { "label" : label, "total" : Ftd(0.0), "prestations" : [], "ligne_regroupement" : None}
                listeKeys.append(key)
                nbreLignes += 1
                
            self.dictRegroupements[key]["prestations"].append(ligne_prestation)
            self.dictRegroupements[key]["total"] += ligne_prestation.montant
            nbreLignes += 1
        
        # Tri des Keys
        listeKeys.sort()
        
        # Cr�ation des lignes
        self.AppendRows(nbreLignes)
        
        # Cr�ation des branches
        numLigne = 0
        self.dictLignes = {}
        for key in listeKeys :
            
            # Niveau 1 : Regroupement
            dictRegroupement = self.dictRegroupements[key]
            ligne_regroupement = Ligne_regroupement(self, numLigne, dictRegroupement)
            self.dictLignes[numLigne] = ligne_regroupement
            self.dictRegroupements[key]["ligne_regroupement"] = ligne_regroupement
            numLigne += 1
            
            # Niveau 2 : Prestations
            for ligne_prestation in self.dictRegroupements[key]["prestations"] :
                ligne_prestation.Draw(numLigne, ligne_regroupement)
                ligne_prestation.MAJ(majTotaux=False)
                ligne_regroupement.listeLignesPrestations.append(ligne_prestation)
                self.dictLignes[numLigne] = ligne_prestation
                numLigne += 1
        
        # MAJ de tous les totaux
        self.MAJtotaux() 
        
    def MAJtotaux(self):
        """ Mise � jour de tous les totaux regroupements + barreInfos """
        # MAJ de tous les totaux de regroupement
        for key, dictRegroupement in self.dictRegroupements.items() :
            ligne_regroupement = dictRegroupement["ligne_regroupement"]
            ligne_regroupement.MAJ() 
        # MAJ de la barre d'infos
        self.MAJbarreInfos() 
        
    def SetRegroupement(self, key):
        self.KeyRegroupement = key
        self.MAJ() 

    def MAJbarreInfos(self, erreur=None):
        total = Ftd(0.0)
        for ligne in self.listeLignesPrestations :
            total += ligne.ventilationActuelle
        self.parent.MAJbarreInfos(total, erreur)

    def SelectionneFacture(self, IDfacture=None):
        # Afficher par facture
        self.SetRegroupement("facture")
        # Coche les prestations li�es � la facture donn�es
        for key, dictRegroupement in self.dictRegroupements.items():
            if key == IDfacture :
                ligne_regroupement = dictRegroupement["ligne_regroupement"]
                ligne_regroupement.SetEtat(True)

    def GetCreditAventiler(self):
        creditAVentiler = self.montant_reglement - self.GetTotalVentile()
        return creditAVentiler

    def GetTotalVentile(self):
        total = Ftd(0.0)
        for ligne in self.listeLignesPrestations :
            total += ligne.ventilationActuelle
        return total

    def GetTotalRestePrestationsAVentiler(self):
        total = Ftd(0.0)
        for ligne in self.listeLignesPrestations :
            total += ligne.resteAVentiler
        return total
    
    def Sauvegarde(self, IDreglement=None):
        """ Sauvegarde des donn�es """
        DB = GestionDB.DB()
        
        for ligne in self.listeLignesPrestations :
            IDprestation = ligne.IDprestation
            montant = float(ligne.ventilationActuelle)
            
            if IDprestation in self.dictVentilationInitiale :
                IDventilation = self.dictVentilationInitiale[IDprestation]
            else:
                IDventilation = None
            
            if ligne.GetEtat() == True :
                # Ajout ou modification
                listeDonnees = [    
                        ("IDreglement", IDreglement),
                        ("IDcompte_payeur", self.IDcompte_payeur),
                        ("IDprestation", IDprestation),
                        ("montant", montant),
                    ]
                if IDventilation == None :
                    IDventilation = DB.ReqInsert("ventilation", listeDonnees)
                else:
                    DB.ReqMAJ("ventilation", listeDonnees, "IDventilation", IDventilation)
            else :
                # Suppression
                if IDventilation != None :
                    DB.ReqDEL("ventilation", "IDventilation", IDventilation)
        
        DB.Close()
        
        return True

# -----------------------------------------------------------------------------------------------------------------------

class CTRL(wx.Panel):
    def __init__(self, parent, IDcompte_payeur=None, IDreglement=None):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.IDcompte_payeur = IDcompte_payeur
        self.IDreglement = IDreglement
        self.montant_reglement = Ftd(0.0)
        self.total_ventilation = Ftd(0.0)
        self.validation = True
        
        if "linux" in sys.platform :
            defaultFont = self.GetFont()
            defaultFont.SetPointSize(8)
            self.SetFont(defaultFont)

        # Regroupement
        self.label_regroupement = wx.StaticText(self, -1, _("Regrouper par :"))
        self.radio_periode = wx.RadioButton(self, -1, _("Mois"), style = wx.RB_GROUP)
        self.radio_facture = wx.RadioButton(self, -1, _("Facture"))
        self.radio_individu = wx.RadioButton(self, -1, _("Individu"))
        self.radio_date = wx.RadioButton(self, -1, _("Date"))
        
        # Commandes rapides
        self.label_hyperliens_1 = wx.StaticText(self, -1, _("Ventiler "))
        self.hyper_automatique = Hyperlien(self, label=_("automatiquement"), infobulle=_("Cliquez ici pour ventiler automatiquement le cr�dit restant"), URL="automatique")
        self.label_hyperliens_2 = wx.StaticText(self, -1, " | ")
        self.hyper_tout = Hyperlien(self, label=_("tout"), infobulle=_("Cliquez ici pour tout ventiler"), URL="tout")
        self.label_hyperliens_3 = wx.StaticText(self, -1, " | ")
        self.hyper_rien = Hyperlien(self, label=_("rien"), infobulle=_("Cliquez ici pour ne rien ventiler"), URL="rien")
        
        # Liste de la ventilation
        self.ctrl_ventilation = CTRL_Ventilation(self, IDcompte_payeur, IDreglement)
        
        # Etat de la ventilation
        self.imgOk = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ok4.png"), wx.BITMAP_TYPE_PNG)
        self.imgErreur = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Interdit2.png"), wx.BITMAP_TYPE_PNG)
        self.imgAddition = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Addition.png"), wx.BITMAP_TYPE_PNG)
        self.ctrl_image = wx.StaticBitmap(self, -1, self.imgAddition)
        
        self.ctrl_info = wx.StaticText(self, -1, _("Vous pouvez encore ventiler 30.90 �"))
        self.ctrl_info.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        
        self.__do_layout()
        
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioRegroupement, self.radio_periode)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioRegroupement, self.radio_facture)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioRegroupement, self.radio_individu)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioRegroupement, self.radio_date)
        
        # Init
        self.ctrl_ventilation.InitGrid() 

                
    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=0, hgap=0)
        
        grid_sizer_barre_haut = wx.FlexGridSizer(rows=1, cols=12, vgap=5, hgap=1)
        grid_sizer_barre_haut.Add(self.label_regroupement, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_barre_haut.Add(self.radio_periode, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)
        grid_sizer_barre_haut.Add(self.radio_facture, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)
        grid_sizer_barre_haut.Add(self.radio_individu, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)
        grid_sizer_barre_haut.Add(self.radio_date, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)
        grid_sizer_barre_haut.Add( (5, 5), 0, wx.EXPAND, 0)
        grid_sizer_barre_haut.Add(self.label_hyperliens_1, 0, 0, 0)
        grid_sizer_barre_haut.Add(self.hyper_automatique, 0, 0, 0)
        grid_sizer_barre_haut.Add(self.label_hyperliens_2, 0, 0, 0)
        grid_sizer_barre_haut.Add(self.hyper_tout, 0, 0, 0)
        grid_sizer_barre_haut.Add(self.label_hyperliens_3, 0, 0, 0)
        grid_sizer_barre_haut.Add(self.hyper_rien, 0, 0, 0)
        grid_sizer_barre_haut.AddGrowableCol(5)
        grid_sizer_base.Add(grid_sizer_barre_haut, 1, wx.EXPAND|wx.BOTTOM, 5)

        grid_sizer_base.Add(self.ctrl_ventilation, 1, wx.EXPAND, 0)
        
        grid_sizer_barre_bas = wx.FlexGridSizer(rows=1, cols=3, vgap=5, hgap=5)
        grid_sizer_barre_bas.Add( (400, 5), 0, 0, 0)
        grid_sizer_barre_bas.Add(self.ctrl_image, 0, 0, 0)
        grid_sizer_barre_bas.Add(self.ctrl_info, 0, wx.EXPAND, 0)
        grid_sizer_base.Add(grid_sizer_barre_bas, 1, wx.EXPAND|wx.TOP, 5)
        
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
    
    def OnRadioRegroupement(self, event):
        if self.radio_periode.GetValue() == True : key = "periode"
        if self.radio_facture.GetValue() == True : key = "facture"
        if self.radio_individu.GetValue() == True : key = "individu"
        if self.radio_date.GetValue() == True : key = "date"
        self.ctrl_ventilation.SetRegroupement(key)
    
    def MAJ(self):
        self.ctrl_ventilation.MAJ() 
        self.MAJinfos() 
    
    def SetMontantReglement(self, montant=Ftd(0.0)):
        if montant == None : return
        if type(montant) != decimal.Decimal :
            montant = Ftd(montant)
        self.montant_reglement = montant
        self.ctrl_ventilation.montant_reglement = montant
        self.MAJinfos() 
    
    def MAJbarreInfos(self, total=Ftd(0.0), erreur=None):
        self.total_ventilation = total
        self.MAJinfos(erreur) 
    
    def MAJinfos(self, erreur=None):
        self.negatif = False
        if self.montant_reglement < 0.00: self.negatif = True
        """ Recherche l'�tat """
        if self.montant_reglement == Ftd(0.0) :
            self.ctrl_image.SetBitmap(self.imgErreur)
            self.ctrl_info.SetLabel(_("Le montant de ce r�glement est Nul !"))
            #return

        if erreur == True :
            self.validation = "erreur"
            self.ctrl_image.SetBitmap(self.imgErreur)
            self.ctrl_info.SetLabel(_("Vous avez saisi un montant non valide !"))
            return
        
        creditAVentiler = Ftd(self.montant_reglement) - Ftd(self.total_ventilation)
        
        totalRestePrestationsAVentiler = Ftd(self.ctrl_ventilation.GetTotalRestePrestationsAVentiler())

        # Recherche de l'�tat
        if self.negatif == False:
            if creditAVentiler > totalRestePrestationsAVentiler :
                creditAVentiler = totalRestePrestationsAVentiler
            if creditAVentiler == Ftd(0.0) :
                self.validation = "ok"
                label = _("Ventilation compl�te !")
            elif creditAVentiler > Ftd(0.0) :
                self.validation = "addition"
                label = _("Reste � ventiler %.2f %s !") % (creditAVentiler, SYMBOLE)
            elif creditAVentiler < Ftd(0.0) :
                self.validation = "trop"
                label = _("Ventilation de %.2f %s en trop !") % (-creditAVentiler, SYMBOLE)
        else:
            #cas d'un montant n�gatif
            if creditAVentiler == Ftd(0.0) :
                self.validation = "ok"
                label = _("Ventilation compl�te !")
            elif creditAVentiler > Ftd(0.0) :
                self.validation = "addition"
                label = _("Ventilation de %.2f %s en trop !") % (-creditAVentiler, SYMBOLE)
            elif creditAVentiler < Ftd(0.0) :
                self.validation = "trop"
                label = _("Reste � ventiler %.2f %s !") % (creditAVentiler, SYMBOLE)
        # Affiche l'image
        if self.validation == "ok" : self.ctrl_image.SetBitmap(self.imgOk)
        if self.validation == "addition" : self.ctrl_image.SetBitmap(self.imgAddition)
        if self.validation == "trop" : self.ctrl_image.SetBitmap(self.imgErreur)
        # MAJ le label d'infos
        if label != self.ctrl_info.GetLabel() :
            self.ctrl_info.SetLabel(label)
        # Colore Label Ventilation Auto
        self.ColoreLabelVentilationAuto() 
        
    def Validation(self):
        creditAVentiler = Ftd(self.montant_reglement) - Ftd(self.total_ventilation)
        if self.validation == "ok" :
            return True
        if self.validation == "addition" :
            totalRestePrestationsAVentiler = Ftd(self.ctrl_ventilation.GetTotalRestePrestationsAVentiler())
            if creditAVentiler > totalRestePrestationsAVentiler :
                creditAVentiler = totalRestePrestationsAVentiler
            if creditAVentiler > Ftd(0.0) :
                dlg = wx.MessageDialog(self, _("Vous devez encore ventiler %.2f %s.\n\nEtes-vous s�r de quand m�me vouloir valider et fermer ?") % (creditAVentiler, SYMBOLE), _("Confirmation"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_EXCLAMATION)
                if self.negatif: dlg = wx.MessageDialog(self, _("Vous avez ventil� %.2f %s en trop !\n\nEtes-vous s�r de quand m�me vouloir valider et fermer ?") % (creditAVentiler, SYMBOLE), _("Confirmation"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_EXCLAMATION)
                reponse = dlg.ShowModal()
                dlg.Destroy()
                if reponse !=  wx.ID_YES :
                    return False
        if self.validation == "trop" :
            dlg = wx.MessageDialog(self, _("Vous avez ventil� %.2f %s en trop !\n\nEtes-vous s�r de quand m�me vouloir valider et fermer ?") % (creditAVentiler, SYMBOLE), _("Confirmation"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_EXCLAMATION)
            if self.negatif : dlg = wx.MessageDialog(self, _("Vous devez encore ventiler %.2f %s.\n\nEtes-vous s�r de quand m�me vouloir valider et fermer ?") % (creditAVentiler, SYMBOLE), _("Confirmation"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_EXCLAMATION)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse !=  wx.ID_YES :
                return False
        if self.validation == "erreur" :
            dlg = wx.MessageDialog(self, _("La ventilation n'est pas valide. Veuillez la v�rifier..."), _("Erreur de saisie"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        return True
        
    def Sauvegarde(self, IDreglement=None):
        self.ctrl_ventilation.Sauvegarde(IDreglement) 

    def SelectionneFacture(self, IDfacture=None):
        self.radio_facture.SetValue(True)
        self.ctrl_ventilation.SelectionneFacture(IDfacture)
    
    def ColoreLabelVentilationAuto(self):
        aVentiler = Ftd(0.0)
        for ligne in self.ctrl_ventilation.listeLignesPrestations :
             aVentiler += Ftd(ligne.montant) - Ftd(ligne.ventilationPassee)
        if self.montant_reglement == aVentiler :
            couleur = wx.Colour(0, 200, 0)
        else :
            couleur = "BLUE"
        self.hyper_automatique.SetColours(couleur, couleur, couleur)
        self.hyper_automatique.UpdateLink()

    def VentilationAuto(self):
        """ Proc�dure de ventilation automatique """
        # Traitement par pointage des prestations n�gatives
        presenceNegatif = False
        for ligne in self.ctrl_ventilation.listeLignesPrestations :
            aVentiler = Ftd(ligne.resteAVentiler)
            if Ftd(ligne.montant) < Ftd(0.0) and aVentiler != 0.0:
                presenceNegatif = True
                montant = aVentiler + ligne.ventilationActuelle
                ligne.SetEtat(etat=True, montant=montant, majTotaux=False)
        if presenceNegatif:
                dlg = wx.MessageDialog(None, _("Pr�sence de prestations aux valeurs n�gatives !\n\nLa ventilation automatique affecte prioritairement tous les montants n�gatifs !"), _("Information"), wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
        # Ventilation automatique
        totalVentilation = Ftd(self.ctrl_ventilation.GetTotalVentile())
        resteVentilation = self.montant_reglement - totalVentilation
        if resteVentilation <= Ftd(0.0) :
            dlg = wx.MessageDialog(self, _("Vous avez d�j� ventil� tout le cr�dit disponible !"), _("Erreur"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        for ligne in self.ctrl_ventilation.listeLignesPrestations :
            aVentiler = resteVentilation
            if aVentiler > Ftd(ligne.resteAVentiler) :
                aVentiler = Ftd(ligne.resteAVentiler)
            if aVentiler > Ftd(0.0) :
                montant = aVentiler + ligne.ventilationActuelle
                ligne.SetEtat(etat=True, montant=montant, majTotaux=False)
                resteVentilation -= Ftd(aVentiler)
        self.ctrl_ventilation.MAJtotaux()
        
    def VentilationTout(self):
        for ligne in self.ctrl_ventilation.listeLignesPrestations :
            aVentiler = ligne.montant - ligne.ventilationPassee
            ligne.SetEtat(etat=True, montant=aVentiler, majTotaux=False)
        self.ctrl_ventilation.MAJtotaux()
        
    def VentilationRien(self):
        for ligne in self.ctrl_ventilation.listeLignesPrestations :
            ligne.SetEtat(False, majTotaux=False)
        self.ctrl_ventilation.MAJtotaux()

# -------------------------------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        
        self.ctrl = CTRL(panel, IDcompte_payeur=2676, IDreglement=22930)
        self.ctrl.SetMontantReglement(600.00)
    
        self.bouton_test = wx.Button(panel, -1, _("Bouton de test"))
        self.Bind(wx.EVT_BUTTON, self.OnBoutonTest, self.bouton_test)
        
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.ALL|wx.EXPAND, 4)
        sizer_2.Add(self.bouton_test, 0, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.SetSize((900, 500))
        self.Layout()
        self.CenterOnScreen()
    
    def OnBoutonTest(self, event):
        """ Bouton de test """
        self.ctrl.VentilationAuto()
                    
        

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "OL TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()

#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys branche Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#-----------------------------------------------------------


import Chemins
from Utils.UTILS_Traduction import _
import wx
import wx.grid as gridlib
import wx.lib.wordwrap as wordwrap
#import wx.lib.mixins.gridlabelrenderer as glr
import Outils.gridlabelrenderer as glr
import datetime
from wx.grid import GridCellRenderer

import GestionDB
from Utils import UTILS_Config
from Utils import UTILS_Texte
from Utils.UTILS_Dates import CalculeAge

# Colonnes unit�s
LARGEUR_COLONNE_UNITE = 60
ABREGE_GROUPES = 0
AFFICHE_TOTAUX = 1

# Colonnes Activit�s
LARGEUR_COLONNE_ACTIVITE = 18
COULEUR_COLONNE_ACTIVITE = (205, 144, 233)

COULEUR_COLONNE_TOTAL = "#C5DDFA"

# Cases
COULEUR_RESERVATION = (252, 213, 0) # ancien vert : "#A6FF9F"
COULEUR_ATTENTE = "YELLOW"
COULEUR_REFUS = "RED"
COULEUR_DISPONIBLE = "#E3FEDB"
COULEUR_ALERTE = "#FEFCDB"
COULEUR_COMPLET = "#F7ACB2"
COULEUR_NORMAL = "WHITE"
COULEUR_FERME = (220, 220, 220)

def DateComplete(dateDD):
    """ Transforme une date DD en date compl�te : Ex : lundi 15 janvier 2008 """
    listeJours = (_("Lundi"), _("Mardi"), _("Mercredi"), _("Jeudi"), _("Vendredi"), _("Samedi"), _("Dimanche"))
    listeMois = (_("janvier"), _("f�vrier"), _("mars"), _("avril"), _("mai"), _("juin"), _("juillet"), _("ao�t"), _("septembre"), _("octobre"), _("novembre"), _("d�cembre"))
    dateComplete = listeJours[dateDD.weekday()] + " " + str(dateDD.day) + " " + listeMois[dateDD.month-1] + " " + str(dateDD.year)
    return dateComplete

def DateEngEnDateDD(dateEng):
    if dateEng and not isinstance(dateEng,str): dateEng = str(dateEng)
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

def HeureStrEnTime(heureStr):
    if heureStr == None or heureStr == "" : return datetime.time(0, 0)
    heures, minutes = heureStr.split(":")
    return datetime.time(int(heures), int(minutes))

class CaseSeparationActivite():
    def __init__(self, ligne, grid, numLigne=None, numColonne=None, IDactivite=None):
        self.typeCase = "activite"
        self.IDactivite = IDactivite
        self.couleurFond = COULEUR_COLONNE_ACTIVITE
        
        # Dessin de la case
        self.renderer = RendererCaseActivite(self)
        if self.IDactivite != None :
            if grid.dictActivites != None :
                labelActivite = grid.dictActivites[IDactivite]["nom"]
            else:
                labelActivite = _("Activit� ID%d") % IDactivite
        grid.SetCellValue(numLigne, numColonne, labelActivite)
        grid.SetCellAlignment(numLigne, numColonne, wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)
        grid.SetCellRenderer(numLigne, numColonne, self.renderer)
        grid.SetReadOnly(numLigne, numColonne, True)
    
    def OnClick(self):
        pass
    
    def OnContextMenu(self):
        pass

    def GetTexteInfobulle(self):
        return ""

class Case():
    def __init__(self, ligne, grid, numLigne=None, numColonne=None, date=None, IDunite=None, IDactivite=None, IDgroupe=None, estTotal=False, total=None):
        self.typeCase = "consommation"
        self.grid = grid
        self.ligne = ligne
        self.numLigne = numLigne
        self.numColonne = numColonne
        self.IDgroupe = IDgroupe
        self.date = date
        self.IDunite = IDunite
        self.IDactivite = IDactivite
        self.estTotal = estTotal
        self.total = total
                
        # Recherche si l'activit� est ouverte
        self.ouvert = self.EstOuvert()

        # R�cup�re les infos de remplissage de la case
        self.dictInfosPlaces = self.GetInfosPlaces() 
        
        # D�finition des couleurs de la case
        self.couleurFond = self.GetCouleur()

        # Dessin de la case
        self.renderer = RendererCase(self)
        self.valeurCase = self.dictInfosPlaces[self.ligne.modeAffichage] 
        # "nbrePlacesInitial" , "nbrePlacesPrises", "nbrePlacesRestantes", "seuil_alerte", "nbreAttente"
        
        if self.valeurCase == None or self.ouvert == False or self.valeurCase == 0 :
            self.valeurCase = ""
        
        if self.estTotal == True :
            if self.total != 0 :
                self.valeurCase = self.total 
            else:
                self.valeurCase = ""
            
        self.grid.SetCellValue(self.numLigne, self.numColonne, str(self.valeurCase))
        self.grid.SetCellAlignment(self.numLigne, self.numColonne, wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
        self.grid.SetCellRenderer(self.numLigne, self.numColonne, self.renderer)
        self.grid.SetReadOnly(self.numLigne, self.numColonne, True)
    
    def GetInfosPlaces(self):
        IDunite_remplissage = self.IDunite
        
        # Recherche des nbres de places
        try :
            nbrePlacesPrises = self.grid.dictRemplissage[self.IDunite][self.date][self.IDgroupe]["nbrePlacesPrises"]
        except :
            nbrePlacesPrises = 0
        try :
            nbrePlacesInitial = self.grid.dictRemplissage[self.IDunite][self.date][self.IDgroupe]["nbrePlacesInitial"]
            nbrePlacesRestantes = nbrePlacesInitial - nbrePlacesPrises
        except :
            nbrePlacesInitial = None
            nbrePlacesRestantes = None
        try :
            seuil_alerte = self.grid.dictRemplissage[self.IDunite]["seuil_alerte"]
        except :
            seuil_alerte = None
        # Attente
        try :
            nbreAttente = self.grid.dictConsoAttente[self.date][self.IDgroupe][self.IDunite]
        except : 
            nbreAttente = 0


        # R�cup�re le nombre de places restantes pour l'ensemble des groupes
        nbrePlacesInitialTousGroupes = 0
        try :
            nbrePlacesInitialTousGroupes = self.grid.dictRemplissage[IDunite_remplissage][self.date][None]["nbrePlacesInitial"]
        except :
            pass

        if nbrePlacesInitialTousGroupes > 0 :
            nbrePlacesPrisesTousGroupes = 0
            try :
                for IDgroupe, d in self.grid.dictRemplissage[IDunite_remplissage][self.date].items() :
                    nbrePlacesPrisesTousGroupes += d["nbrePlacesPrises"]
            except :
                pass

            nbrePlacesRestantesTousGroupes = nbrePlacesInitialTousGroupes - nbrePlacesPrisesTousGroupes
            if nbrePlacesRestantesTousGroupes < nbrePlacesRestantes or nbrePlacesInitial == 0 :
                nbrePlacesInitial = nbrePlacesInitialTousGroupes
                #nbrePlacesPrises = nbrePlacesPrisesTousGroupes
                nbrePlacesRestantes = nbrePlacesRestantesTousGroupes

        # Cr�ation d'un dictionnaire de r�ponses
        dictInfosPlaces = {
            "nbrePlacesInitial" : nbrePlacesInitial, 
            "nbrePlacesPrises" : nbrePlacesPrises, 
            "nbrePlacesRestantes" : nbrePlacesRestantes, 
            "seuil_alerte" : seuil_alerte,
            "nbreAttente" : nbreAttente,
            }
        return dictInfosPlaces
                
    def GetCouleur(self):
        """ Obtient la couleur � appliquer � la case """    
        if self.estTotal == True :
            return COULEUR_COLONNE_TOTAL

        # Si ferm�e
        if self.ouvert == False : return COULEUR_FERME

        if self.dictInfosPlaces["nbrePlacesInitial"] != None :
            nbrePlacesRestantes = self.dictInfosPlaces["nbrePlacesRestantes"]
            seuil_alerte = self.dictInfosPlaces["seuil_alerte"]
            if nbrePlacesRestantes > seuil_alerte : return COULEUR_DISPONIBLE
            if nbrePlacesRestantes > 0 and nbrePlacesRestantes <= seuil_alerte : return COULEUR_ALERTE
            if nbrePlacesRestantes <= 0 : return COULEUR_COMPLET
        
        return COULEUR_NORMAL
        
    def EstOuvert(self):
        """ Recherche si l'unit� est ouverte � cette date """
        ouvert = False
        if self.date in self.grid.dictOuvertures:
            if self.IDgroupe in self.grid.dictOuvertures[self.date]:
                ouvert = True
        
        date_debut = self.grid.dictRemplissage[self.IDunite]["date_debut"]
        date_fin = self.grid.dictRemplissage[self.IDunite]["date_fin"]
        if self.date < date_debut or self.date > date_fin :
            ouvert = False
        return ouvert
    
    def GetTexteInfobulle(self):
        """ Renvoie le texte pour l'infobulle de la case """
        nomUnite = self.grid.dictUnites[self.IDunite]["nom"]
        dateComplete = DateComplete(self.date)
        texte = "%s du %s\n\n" % (nomUnite, dateComplete)
        texte = texte.upper()
        # Heures de la consommation
        if self.etat in ("reservation", "attente", "present") :
            if self.heure_debut == None or self.heure_fin == None :
                texte += _("Horaire de la consommation non sp�cifi�\n")
            else:
                texte += _("De %s � %s\n") % (self.heure_debut.replace(":","h"), self.heure_fin.replace(":","h"))
            texte += _("Sur le groupe %s \n") % self.grid.dictGroupes[self.IDgroupe]["nom"]
        texte += "-------------------------------------------------------------------\n"
        
        # Si unit� ferm�e
        if self.ouvert == False :
            return _("Unit� ferm�e")
        # Nbre de places
        if self.dictInfosPlaces != None :
            nbrePlacesInitial = self.dictInfosPlaces["nbrePlacesInitial"]
            nbrePlacesPrises = self.dictInfosPlaces["nbrePlacesPrises"]
            nbrePlacesRestantes = self.dictInfosPlaces["nbrePlacesRestantes"]
            seuil_alerte = self.dictInfosPlaces["seuil_alerte"]
            nbreAttente = self.dictInfosPlaces["nbreAttente"]
            texte += _("Nbre initial de places  : %d \n") % nbrePlacesInitial
            texte += _("Nbre de places prises : %d \n") % nbrePlacesPrises
            texte += _("Nbre de places disponibles : %d \n") % nbrePlacesRestantes
            texte += _("Seuil d'alerte : %d \n") % seuil_alerte
            texte += _("Nbre d'individus sur liste d'attente : %d \n") % nbreAttente
        else:
            texte += _("Aucune limitation du nombre de places\n")
        # Etat de la case
        texte += "-------------------------------------------------------------------\n"
        if self.etat in ("reservation", "attente", "present") :
            date_saisie_FR = DateComplete(self.date_saisie)
            if self.etat == "reservation" or self.etat == "present" : texte += _("Consommation r�serv�e le %s\n") % date_saisie_FR
            if self.etat == "attente" : texte += _("Consommation mise en attente le %s\n") % date_saisie_FR
            if self.IDutilisateur != None :
                texte += _("Par l'utilisateur ID%d\n") % self.IDutilisateur
            texte += "-------------------------------------------------------------------\n"
        # Infos Individu
        nom = self.grid.dictInfosIndividus[self.IDindividu]["nom"]
        prenom = self.grid.dictInfosIndividus[self.IDindividu]["prenom"]
        texte += _("Informations concernant %s %s : \n") % (prenom, nom)
        date_naiss = self.grid.dictInfosIndividus[self.IDindividu]["date_naiss"]
        if date_naiss != None :
            ageActuel = CalculeAge(datetime.date.today(), date_naiss)
            texte += _("Age actuel : %d ans \n") % ageActuel
            if self.etat != None :
                ageConso = CalculeAge(self.date, date_naiss)
                texte += _("Age lors de la consommation : %d ans \n") % ageConso
        else:
            texte += _("Date de naissance inconnue ! \n")
        # Infos inscription :
        nom_categorie_tarif = self.dictInfosInscriptions["nom_categorie_tarif"]
        if self.etat in ("reservation", "absent", "present") :
            texte += "-------------------------------------------------------------------\n"
            texte += _("Cat�gorie de tarif : '%s'\n") % nom_categorie_tarif
        
        return texte
    
    def OnContextMenu(self):
        if self.ouvert == False :
            return
        
        # Cr�ation du menu contextuel
        menuPop = wx.Menu()

        # Item IDENTIFICATION DE LA CASE
        nomUnite = self.grid.dictUnites[self.IDunite]["nom"]
        dateComplete = DateComplete(self.date)
        texteItem = "%s du %s" % (nomUnite, dateComplete)
        item = wx.MenuItem(menuPop, 10, texteItem)
        menuPop.Append(item)
        item.Enable(False)
        
        # Etat de la consommation
        if self.etat in ("reservation", "present", "absent") :
            menuPop.AppendSeparator()
            item = wx.MenuItem(menuPop, 60, _("Pointage en attente"), kind=wx.ITEM_RADIO)
            menuPop.Append(item)
            if self.etat == "reservation" : item.Check(True)
            self.grid.Bind(wx.EVT_MENU, self.SetPresentAbsent, id=60)
            item = wx.MenuItem(menuPop, 70, _("Pr�sent"), kind=wx.ITEM_RADIO)
            menuPop.Append(item)
            if self.etat == "present" : item.Check(True)
            self.grid.Bind(wx.EVT_MENU, self.SetPresentAbsent, id=70)
            item = wx.MenuItem(menuPop, 80, _("Absent"), kind=wx.ITEM_RADIO)
            menuPop.Append(item)
            if self.etat == "absent" : item.Check(True)
            self.grid.Bind(wx.EVT_MENU, self.SetPresentAbsent, id=80)
        
        if self.etat in ("reservation", "attente", "refus") :
            menuPop.AppendSeparator()
            item = wx.MenuItem(menuPop, 30, _("R�servation"), kind=wx.ITEM_RADIO)
            menuPop.Append(item)
            if self.etat == "reservation" : item.Check(True)
            self.grid.Bind(wx.EVT_MENU, self.SetEtat, id=30)
            item = wx.MenuItem(menuPop, 40, _("Attente"), kind=wx.ITEM_RADIO)
            menuPop.Append(item)
            if self.etat == "attente" : item.Check(True)
            self.grid.Bind(wx.EVT_MENU, self.SetEtat, id=40)
            item = wx.MenuItem(menuPop, 50, _("Refus"), kind=wx.ITEM_RADIO)
            menuPop.Append(item)
            if self.etat == "refus" : item.Check(True)
            self.grid.Bind(wx.EVT_MENU, self.SetEtat, id=50)
        
        # Changement de Groupe
        listeGroupes = []
        for IDgroupe, dictGroupe in self.grid.dictGroupes.items():
            if dictGroupe["IDactivite"] == self.IDactivite :
                listeGroupes.append( (dictGroupe["nom"], IDgroupe) )
        listeGroupes.sort() 
        if len(listeGroupes) > 0 and self.etat in ("reservation", "attente", "refus") :
            menuPop.AppendSeparator()
            for nomGroupe, IDgroupe in listeGroupes :
                IDitem = 10000 + IDgroupe
                item = wx.MenuItem(menuPop, IDitem, nomGroupe, kind=wx.ITEM_RADIO)
                menuPop.Append(item)
                if self.IDgroupe == IDgroupe : item.Check(True)
                self.grid.Bind(wx.EVT_MENU, self.SetGroupe, id=IDitem)
                
        # D�tail de la consommation
        if self.etat in ("reservation", "present", "absent", "attente", "refus") :
            menuPop.AppendSeparator()
            item = wx.MenuItem(menuPop, 20, _("D�tail de la consommation"))
            bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Calendrier_zoom.png"), wx.BITMAP_TYPE_PNG)
            item.SetBitmap(bmp)
            menuPop.Append(item)
            self.grid.Bind(wx.EVT_MENU, self.DLG_detail, id=20)
            
        # Item Verrouillage
##        if self.verrouillage == 0 and self.etat != None :
##            item = wx.MenuItem(menuPop, 10, _("Verrouiller cette consommation"))
##            bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Cadenas_ferme.png"), wx.BITMAP_TYPE_PNG)
##            item.SetBitmap(bmp)
##            menuPop.Append(item)
##            self.grid.Bind(wx.EVT_MENU, self.Verrouillage, id=10)
##        if self.verrouillage == 1 and self.etat != None :
##            item = wx.MenuItem(menuPop, 10, _("D�verrouiller cette consommation"))
##            bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Cadenas.png"), wx.BITMAP_TYPE_PNG)
##            item.SetBitmap(bmp)
##            menuPop.Append(item)
##            self.grid.Bind(wx.EVT_MENU, self.Deverrouillage, id=10)
        
                
        self.grid.PopupMenu(menuPop)
        menuPop.Destroy()
        
class Ligne():
    def __init__(self, grid, numLigne, date, dictGroupeTemp, dictListeRemplissage, modeAffichage):
        self.grid = grid
        self.numLigne = numLigne
        self.date = date
        self.modeAffichage = modeAffichage
        
        # Label de la ligne
        self.labelLigne = DateComplete(self.date)
        
        # Couleurs de label
        couleurLigneDate = "#C0C0C0"
        self.couleurOuverture = (0, 230, 0)
        self.couleurFermeture = "#F7ACB2"
        couleurVacances = "#F3FD89"
        
        # Cr�ation du label de ligne
        hauteurLigne = 30
        self.grid.SetRowLabelValue(numLigne, self.labelLigne)
        self.grid.SetRowSize(numLigne, hauteurLigne)
        if self.EstEnVacances(self.date) == True :
            couleurCase = couleurVacances
        else:
            couleurCase = None
        self.renderer = MyRowLabelRenderer(couleurCase, self.date)
        self.grid.SetRowLabelRenderer(numLigne, self.renderer)
        self.grid.dictLignes[numLigne] = self.renderer
        
        # Cr�ation des cases
        self.dictCases = {}
        self.dictTotaux = {}
        numColonne = 0
        for IDactivite in self.grid.listeActivites :
            
            # Cr�ation de la colonne activit�
            if len(self.grid.listeActivites) > 1 and IDactivite in dictGroupeTemp :
                case = CaseSeparationActivite(self, self.grid, self.numLigne, numColonne, IDactivite)
                self.dictCases[numColonne] = case
                numColonne += 1
                
            # Cr�ation des cases unit�s de remplissage
            if IDactivite in dictGroupeTemp:
                for IDgroupe in dictGroupeTemp[IDactivite] :
                    if IDactivite in dictListeRemplissage :
                        for ordre, IDunite_remplissage in dictListeRemplissage[IDactivite] :
                            case = Case(self, self.grid, self.numLigne, numColonne, self.date, IDunite_remplissage, IDactivite, IDgroupe)
                            if (IDunite_remplissage in self.dictTotaux) == False :
                                self.dictTotaux[IDunite_remplissage] = 0
                            if case.valeurCase != "" and case.valeurCase != None :
                                self.dictTotaux[IDunite_remplissage] += case.valeurCase
                            self.dictCases[numColonne] = case
                            numColonne += 1
                        
            # Cr�ation des colonnes totaux
            if AFFICHE_TOTAUX == 1 and IDactivite in dictListeRemplissage and IDactivite in dictGroupeTemp :
                if len(dictListeRemplissage[IDactivite]) > 0 and len(dictGroupeTemp[IDactivite]) > 0 :
                    for ordre, IDunite_remplissage in dictListeRemplissage[IDactivite] :
                        if IDunite_remplissage in self.dictTotaux :
                            total = self.dictTotaux[IDunite_remplissage]
                        else:
                            total = None
                        case = Case(self, self.grid, self.numLigne, numColonne, self.date, IDunite_remplissage, IDactivite, None, True, total)
                        self.dictCases[numColonne] = case
                        numColonne += 1

    def EstEnVacances(self, dateDD):
        date = str(dateDD)
        for valeurs in self.grid.listeVacances :
            date_debut = valeurs[0]
            date_fin = valeurs[1]
            if date >= date_debut and date <= date_fin :
                return True
        return False

    def OnContextMenu(self):
        # Cr�ation du menu contextuel
        menuPop = wx.Menu()

        # Item IDENTIFICATION DE LA LIGNE
        item = wx.MenuItem(menuPop, 10, self.labelLigne)
        menuPop.Append(item)
        item.Enable(False)
        
        menuPop.AppendSeparator()

##        # Item Verrouillage
##        item = wx.MenuItem(menuPop, 10, _("Verrouiller toutes les consommations"))
##        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Cadenas_ferme.png"), wx.BITMAP_TYPE_PNG)
##        item.SetBitmap(bmp)
##        menuPop.Append(item)
##        self.grid.Bind(wx.EVT_MENU, self.Verrouillage, id=10)
##        
##        item = wx.MenuItem(menuPop, 20, _("D�verrouiller toutes les consommations"))
##        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Cadenas.png"), wx.BITMAP_TYPE_PNG)
##        item.SetBitmap(bmp)
##        menuPop.Append(item)
##        self.grid.Bind(wx.EVT_MENU, self.Deverrouillage, id=20)
        
        # Etat des consommations de la ligne
        nbreCasesReservations = 0
        for numColonne, case in self.dictCases.items() :
            if case.typeCase == "consommation" :
                if case.etat in ("reservation", "present", "absent") :
                    nbreCasesReservations += 1
                    
        if nbreCasesReservations > 0 :
            item = wx.MenuItem(menuPop, 30, _("D�finir toutes les pointages de la ligne comme 'Pointage en attente'"))
            menuPop.Append(item)
            self.grid.Bind(wx.EVT_MENU, self.SetPresentAbsent, id=30)
            item = wx.MenuItem(menuPop, 40, _("Pointer toutes les consommations de la ligne sur 'Pr�sent'"))
            bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ok.png"), wx.BITMAP_TYPE_PNG)
            item.SetBitmap(bmp)
            menuPop.Append(item)
            self.grid.Bind(wx.EVT_MENU, self.SetPresentAbsent, id=40)
            item = wx.MenuItem(menuPop, 50, _("Pointer toutes les consommations de la ligne sur 'Absent'"))
            bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Interdit.png"), wx.BITMAP_TYPE_PNG)
            item.SetBitmap(bmp)
            menuPop.Append(item)
            self.grid.Bind(wx.EVT_MENU, self.SetPresentAbsent, id=50)
            
        self.grid.PopupMenu(menuPop)
        menuPop.Destroy()

class RendererCase(GridCellRenderer):
    def __init__(self, case):
        GridCellRenderer.__init__(self)
        self.case = case

    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        self.grid = grid
        dc.SetBackgroundMode(wx.SOLID)
        dc.SetBrush(wx.Brush(self.case.couleurFond, wx.SOLID))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangle(rect)

        dc.SetBackgroundMode(wx.TRANSPARENT)
        dc.SetFont(attr.GetFont())
        
        hAlign, vAlign = grid.GetCellAlignment(row, col)
        texte = grid.GetCellValue(row, col)
        largeurTexte, hauteurTexte = dc.GetTextExtent(texte)
        if self.case.ouvert == True or self.case.estTotal == True :
            self.DrawBorder(grid, dc, rect)
        x = rect[0] + rect[2]/2.0 - largeurTexte/2.0
        y = rect[1] + rect[3]/2.0 - hauteurTexte/2.0
        dc.DrawText(texte, int(x),int(y))
            
    def MAJ(self):
        self.grid.Refresh()

    def GetBestSize(self, grid, attr, dc, row, col):
        text = grid.GetCellValue(row, col)
        dc.SetFont(attr.GetFont())
        w, h = dc.GetTextExtent(text)
        return wx.Size(w, h)

    def Clone(self):
        return RendererCase()

    def DrawBorder(self, grid, dc, rect):
        """
        Draw a standard border around the label, to give a simple 3D
        effect like the stock wx.grid.Grid labels do.
        """
        top = rect.top
        bottom = rect.bottom
        left = rect.left
        right = rect.right        
        dc.SetPen(wx.Pen(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DSHADOW)))
        dc.DrawLine(right, top, right, bottom)
        dc.DrawLine(left, top, left, bottom)
        dc.DrawLine(left, bottom, right, bottom)
        dc.SetPen(wx.WHITE_PEN)
        dc.DrawLine(left+1, top, left+1, bottom)
        dc.DrawLine(left+1, top, right, top)
    
    def AdapteTailleTexte(self, dc, texte, tailleMaxi):
        """ Raccourcit le texte de l'intitul� en fonction de la taille donn�e """
        # Pas de retouche n�cessaire
        if dc.GetTextExtent(texte)[0] < tailleMaxi : return texte
        # Renvoie aucun texte si tailleMaxi trop petite
        if tailleMaxi <= dc.GetTextExtent("W...")[0] : return "..."
        # Retouche n�cessaire
        tailleTexte = dc.GetTextExtent(texte)[0]
        texteTemp = ""
        texteTemp2 = ""
        for lettre in texte :
            texteTemp += lettre
            if dc.GetTextExtent(texteTemp +"...")[0] < tailleMaxi :
               texteTemp2 = texteTemp 
            else:
                return texteTemp2 + "..." 

class RendererCaseActivite(GridCellRenderer):
    def __init__(self, case):
        GridCellRenderer.__init__(self)
        self.case = case

    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        self.grid = grid
        dc.SetBackgroundMode(wx.SOLID)
        dc.SetBrush(wx.Brush(self.case.couleurFond, wx.SOLID))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangle(rect)

        dc.SetBackgroundMode(wx.TRANSPARENT)
        dc.SetFont(attr.GetFont())
        
        hAlign, vAlign = grid.GetCellAlignment(row, col)
        text = grid.GetCellValue(row, col)
##        dc.DrawText(text, rect[0], rect[1])
        if row == 0 :
            largeurTexte, hauteurTexte = dc.GetTextExtent(text)
            dc.DrawRotatedText(text, rect[0], rect[1]+largeurTexte+10, 90)
                    
    def MAJ(self):
        self.grid.Refresh()

    def GetBestSize(self, grid, attr, dc, row, col):
        text = grid.GetCellValue(row, col)
        dc.SetFont(attr.GetFont())
        w, h = dc.GetTextExtent(text)
        return wx.Size(w, h)

    def Clone(self):
        return RendererCase()

class MyRowLabelRenderer(glr.GridLabelRenderer):
    def __init__(self, bgcolor, date):
        self._bgcolor = bgcolor
        self.date = date
        
    def Draw(self, grid, dc, rect, row):
        if self._bgcolor != None :
            dc.SetBrush(wx.Brush(self._bgcolor))
            dc.SetPen(wx.TRANSPARENT_PEN)
            dc.DrawRectangle(rect)
        else:
            pass
        hAlign, vAlign = grid.GetRowLabelAlignment()
        text = grid.GetRowLabelValue(row)
        self.DrawBorder(grid, dc, rect)
        self.DrawText(grid, dc, rect, text, hAlign, vAlign)

        # Indicateur date du jour
        if self.date == datetime.date.today() :
            dc.SetBrush(wx.Brush(wx.Colour(255, 0, 0), wx.SOLID))
            dc.SetPen(wx.TRANSPARENT_PEN)
            dc.DrawPolygon([(0, 0), (-7, 0), (0, 7)], xoffset=rect[2]-2, yoffset=rect[1]+1)
            
    
    def MAJ(self, couleur):
        self._bgcolor = couleur

class MyColLabelRenderer(glr.GridLabelRenderer):
    def __init__(self, typeColonne=None, bgcolor=None):
        self.typeColonne = typeColonne
        self._bgcolor = bgcolor
        
    def Draw(self, grid, dc, rect, col):
        if self._bgcolor != None :
            dc.SetBrush(wx.Brush(self._bgcolor))
            dc.SetPen(wx.TRANSPARENT_PEN)
            dc.DrawRectangle(rect)
        hAlign, vAlign = grid.GetColLabelAlignment()
        text = grid.GetColLabelValue(col)
        if self.typeColonne == "unite" :
            text = wordwrap.wordwrap(text, LARGEUR_COLONNE_UNITE, dc)
        if self.typeColonne == "unite" :
            self.DrawBorder(grid, dc, rect)
        self.DrawText(grid, dc, rect, text, hAlign, vAlign)

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------

class CTRL(gridlib.Grid, glr.GridWithLabelRenderersMixin): 
    def __init__(self, parent, dictDonnees=None):
        gridlib.Grid.__init__(self, parent, -1, size=(1, 1), style=wx.WANTS_CHARS)
        glr.GridWithLabelRenderersMixin.__init__(self)
        self.listePeriodes = []
        self.listeActivites = []
        self.SetModeAffichage("nbrePlacesPrises")
        self.moveTo = None
        self.GetGridWindow().SetToolTip("")
        self.caseSurvolee = None

        global LARGEUR_COLONNE_UNITE
        LARGEUR_COLONNE_UNITE = UTILS_Config.GetParametre("largeur_colonne_unite_remplissage", 60)

        global ABREGE_GROUPES
        ABREGE_GROUPES = UTILS_Config.GetParametre("remplissage_abrege_groupes", 0)

        global AFFICHE_TOTAUX
        AFFICHE_TOTAUX = UTILS_Config.GetParametre("remplissage_affiche_totaux", 1)

        # Cr�ation initiale de la grille
        self.CreateGrid(0, 0)
        self.SetRowLabelSize(180)
        self.EnableGridLines(False)
        self.DisableDragColSize()
        self.DisableDragRowSize()
        self.SetDefaultCellBackgroundColour(self.GetBackgroundColour())

        # Dict de donn�es de s�lection
        self.dictDonnees = dictDonnees
        self.MAJ()
        if self.GetNumberCols() == 0:
            self.dictDonnees = self.GetDonneesDefaut()
            self.MAJ()

    def SetDictDonnees(self, dictDonnees=None):
            self.dictDonnees = dictDonnees
            self.listeActivites = self.dictDonnees["listeActivites"]
            self.listePeriodes = self.dictDonnees["listePeriodes"]
            self.SetModeAffichage(self.dictDonnees["modeAffichage"])

    def GetDonneesDefaut(self):
        """ Commande de test pour le d�veloppement """
        DB = GestionDB.DB()
        req = """SELECT IDactivite
        FROM activites
        ORDER BY activites.IDactivite DESC
        LIMIT 5;"""
        DB.ExecuterReq(req,MsgBox="CTRL_Remplissage.CTRL.Tests")
        listeActivites = [ x for (x,) in DB.ResultatReq()]
        DB.Close()
        return {
                "listePeriodes":[[datetime.date(2000,1,1),datetime.date(2999,12,31)]],
                "listeActivites":listeActivites,
                "modeAffichage":"nbrePlacesPrises",
            }

    def SetListeActivites(self, listeActivites=[]):
        self.listeActivites = listeActivites

    def SetListePeriodes(self, listePeriodes=[]):
        self.listePeriodes = listePeriodes
    
    def SetModeAffichage(self, mode):
        # "nbrePlacesInitial" , "nbrePlacesPrises", "nbrePlacesRestantes", "seuil_alerte", "nbreAttente"
        self.modeAffichage = mode

    def MAJ(self):
        self.Freeze()
        self.MAJ_donnees()
        self.MAJ_affichage()
        self.Thaw()
            
    def MAJ_donnees(self):
        if self.dictDonnees != None :
            self.SetDictDonnees(self.dictDonnees)
        # R�cup�ration des donn�es
        self.DB = GestionDB.DB() 
        self.dictActivites = self.Importation_activites()
        self.dictOuvertures, listeUnitesUtilisees, self.listeGroupesUtilises = self.GetDictOuvertures(self.listeActivites, self.listePeriodes)
        self.listeVacances = self.GetListeVacances() 
        self.dictRemplissage, self.dictUnitesRemplissage, self.dictConsoAttente = self.GetDictRemplissage(self.listeActivites, self.listePeriodes)
        self.dictGroupes = self.GetDictGroupes()
        self.DB.Close()

    def MAJ_affichage(self):
        if self.GetNumberRows() > 0 :
            self.DeleteRows(0, self.GetNumberRows())
        if self.GetNumberCols() > 0 : 
            self.DeleteCols(0, self.GetNumberCols())
        self.ClearGrid()
        self.InitGrid()
        self.Refresh()
                
    def InitGrid(self):
        # ----------------- Cr�ation des colonnes -------------------------
        # R�cup�ration des groupes
        dictGroupeTemp = {}
        for IDgroupe, dictGroupe in self.dictGroupes.items() : 
            IDactivite = dictGroupe["IDactivite"]
            ordre = dictGroupe["ordre"]
            if (IDactivite in dictGroupeTemp) == False :
                dictGroupeTemp[IDactivite] = []
            dictGroupeTemp[IDactivite].append((ordre, IDgroupe))
            dictGroupeTemp[IDactivite].sort()
        
        for IDactivite, listeGroupesTemp in dictGroupeTemp.items() :
            listeTemp = []
            for ordre, IDgroupe in listeGroupesTemp :
                listeTemp.append(IDgroupe)
            dictGroupeTemp[IDactivite] = listeTemp
            
        # R�cup�ration des unit�s de remplissage
        dictListeRemplissage = {}
        for IDunite_remplissage, dictRemplissage in self.dictRemplissage.items() :
            if "IDactivite" in dictRemplissage :
                IDactivite = dictRemplissage["IDactivite"]
                ordre = dictRemplissage["ordre"]
                donnees = (ordre, IDunite_remplissage)
                if (IDactivite in dictListeRemplissage) == True :
                    dictListeRemplissage[IDactivite].append(donnees)
                else:
                    dictListeRemplissage[IDactivite] = [(donnees),]
                dictListeRemplissage[IDactivite].sort()
        
        nbreColonnes = 0
        for IDactivite in self.listeActivites :
            # Compte colonne titre activit�
            if len(self.listeActivites) > 1 and IDactivite in dictGroupeTemp :
                nbreColonnes += 1
            if IDactivite in dictGroupeTemp :
                for IDgroupe in dictGroupeTemp[IDactivite] :
                    if IDactivite in dictListeRemplissage :
                        for ordre, IDunite_remplissage in dictListeRemplissage[IDactivite] :
                            nbreColonnes += 1
                if AFFICHE_TOTAUX == 1 and IDactivite in dictListeRemplissage and len(dictListeRemplissage[IDactivite]) > 0 and len(dictGroupeTemp[IDactivite]) > 0 :
                    nbreColonnes += len(dictListeRemplissage[IDactivite])
        if nbreColonnes == 0:
            return
        self.AppendCols(nbreColonnes)

        # Colonnes
        self.SetColLabelSize(45)
        largeurColonne= LARGEUR_COLONNE_UNITE
        numColonne = 0
        listeColonnesActivites = []
        for IDactivite in self.listeActivites :
            # Cr�ation de la colonne activit�
            if len(self.listeActivites) > 1 and IDactivite in dictGroupeTemp :
                renderer = MyColLabelRenderer("activite", COULEUR_COLONNE_ACTIVITE)
                self.SetColLabelRenderer(numColonne, renderer)
                self.SetColSize(numColonne, LARGEUR_COLONNE_ACTIVITE)
                self.SetColLabelValue(numColonne, "")
                listeColonnesActivites.append(numColonne)
                numColonne += 1
            # Cr�ation des colonnes unit�s
            if IDactivite in dictGroupeTemp:
                # Parcours des groupes
                if IDactivite in dictListeRemplissage :
                    for IDgroupe in dictGroupeTemp[IDactivite] :
                        for ordre, IDunite_remplissage in dictListeRemplissage[IDactivite] :
                            renderer = MyColLabelRenderer("unite", None)
                            self.SetColLabelRenderer(numColonne, renderer)
                            if ABREGE_GROUPES == 0 :
                                nomGroupe = self.dictGroupes[IDgroupe]["nom"]
                            else :
                                nomGroupe = self.dictGroupes[IDgroupe]["abrege"]
                            if nomGroupe != "" : nomGroupe += "\n"
                            nomUniteRemplissage = self.dictRemplissage[IDunite_remplissage]["abrege"]
                            labelColonne = "%s%s" % (nomGroupe, nomUniteRemplissage)
                            self.SetColSize(numColonne, largeurColonne)
                            self.SetColLabelValue(numColonne, labelColonne)
                            numColonne += 1
                    # Cr�ation des colonnes totaux
                    if len(dictListeRemplissage[IDactivite]) > 1 and len(dictGroupeTemp[IDactivite]) > 1 :
                        for ordre, IDunite_remplissage in dictListeRemplissage[IDactivite] :
                            renderer = MyColLabelRenderer("unite", None)
                            self.SetColLabelRenderer(numColonne, renderer)
                            nomUniteRemplissage = self.dictRemplissage[IDunite_remplissage]["abrege"]
                            labelColonne = _("Total\n%s") % nomUniteRemplissage
                            self.SetColSize(numColonne, largeurColonne)
                            self.SetColLabelValue(numColonne, labelColonne)
                            numColonne += 1
        
        # ------------------ Cr�ation des lignes -----------------------------
        
        # Tri des dates
        listeDatesTmp = list(self.dictOuvertures.keys())
        listeDates = []
        for dateDD in listeDatesTmp :
            listeDates.append(dateDD)
        listeDates.sort()
        nbreDates = len(listeDates)
        
        # Calcul du nombre de lignes
        self.AppendRows(nbreDates)
        
        # Span des colonnes Activit�s
        if nbreDates > 0 :
            for numColonneActivite in listeColonnesActivites :
                self.SetCellSize(0, numColonneActivite, nbreDates, 1)
        
        # Cr�ation des lignes
        self.dictLignes = {}
        numLigne = 0
        for dateDD in listeDates :
            ligne = Ligne(self, numLigne, dateDD, dictGroupeTemp, dictListeRemplissage, self.modeAffichage)
            self.dictLignes[numLigne] = ligne
            numLigne += 1

    def OnCellLeftDClick(self, event):
        numLigne = event.GetRow()
        numColonne = event.GetCol()
        ligne = self.dictLignes[numLigne]
        #if ligne.estSeparation == True:
        #    return
        case = ligne.dictCases[numColonne]

        # Recherche des conso
        try :
            listeConsoPresents = self.dictRemplissage[case.IDunite][case.date][case.IDgroupe]["listeConsoPresents"]
        except :
            listeConsoPresents = []

        if len(listeConsoPresents) > 0 :
            from Dlg import DLG_Liste_presents
            dlg = DLG_Liste_presents.Dialog(self, listeIDconso=listeConsoPresents)
            dlg.ShowModal()
            dlg.Destroy()

        event.Skip()

    def OnCellLeftClick(self, event):
        numLigne = event.GetRow()
        numColonne = event.GetCol()
        ligne = self.dictLignes[numLigne]
        if ligne.estSeparation == True :
            return
        case = ligne.dictCases[numColonne]
        case.OnClick()
        self.ClearSelection()
        event.Skip()
    
    def OnCellRightClick(self, event):
        numLigne = event.GetRow()
        numColonne = event.GetCol()
        ligne = self.dictLignes[numLigne]
        if ligne.estSeparation == True :
            return
        case = ligne.dictCases[numColonne]
        case.OnContextMenu()
        event.Skip()

    def OnLabelRightClick(self, event):
        numLigne = event.GetRow()
        if numLigne == -1 : return
        ligne = self.dictLignes[numLigne]
        ligne.OnContextMenu()
        event.Skip()
    
    def OnMouseOver(self, event):
        x, y = self.CalcUnscrolledPosition(event.GetPosition())
        numLigne = self.YToRow(y)
        numColonne = self.XToCol(x)
        if numLigne != -1 and numColonne != -1 : 
            ligne = self.dictLignes[numLigne]
            if ligne.estSeparation == True : 
                return
            case = ligne.dictCases[numColonne]
            if case != self.caseSurvolee :
                # Attribue une info-bulle
                self.GetGridWindow().SetToolTip(wx.ToolTip(case.GetTexteInfobulle()))
                tooltip = self.GetGridWindow().GetToolTip()
                tooltip.SetDelay(1500)
                self.caseSurvolee = case
        else:
            self.caseSurvolee = None
            self.GetGridWindow().SetToolTip(wx.ToolTip(""))
        event.Skip()
        
    def GetListeVacances(self):
        req = """SELECT date_debut, date_fin, nom, annee
        FROM vacances 
        ORDER BY date_debut; """
        self.DB.ExecuterReq(req,MsgBox="CTRL_Remplissage")
        listeDonnees = self.DB.ResultatReq()
        return listeDonnees
        
    def GetListeUnites(self, listeUnitesUtilisees):
        dictListeUnites = {}
        dictUnites = {}
        conditionSQL = "AND IDactivite in ( %s )"%str(self.listeActivites)[1:-1]
        if len(listeUnitesUtilisees) == 0 : conditionSQL = "()"
        elif len(listeUnitesUtilisees) == 1 : conditionSQL = "(%d)" % listeUnitesUtilisees[0]
        else : conditionSQL = str(tuple(listeUnitesUtilisees))
        # R�cup�re la liste des unit�s
        req = """SELECT IDunite, IDactivite, nom, abrege, type, heure_debut, heure_fin, date_debut, date_fin, ordre, touche_raccourci
        FROM unites 
        WHERE IDunite IN %s %s
        ORDER BY ordre; """ % (conditionSQL, conditionSQL)
        self.DB.ExecuterReq(req,MsgBox="CTRL_Remplissage")
        listeDonnees = self.DB.ResultatReq()
        for IDunite, IDactivite, nom, abrege, type, heure_debut, heure_fin, date_debut, date_fin, ordre, touche_raccourci in listeDonnees :
            dictTemp = { "unites_incompatibles" : [], "IDunite" : IDunite, "IDactivite" : IDactivite, "nom" : nom, "abrege" : abrege, "type" : type, "heure_debut" : heure_debut, "heure_fin" : heure_fin, "date_debut" : date_debut, "date_fin" : date_fin, "ordre" : ordre, "touche_raccourci" : touche_raccourci}
            if IDactivite in dictListeUnites :
                dictListeUnites[IDactivite].append(dictTemp)
            else:
                dictListeUnites[IDactivite] = [dictTemp,]
            dictUnites[IDunite] = dictTemp
        return dictListeUnites, dictUnites
        
    def GetDictOuvertures(self, listeActivites=[], listePeriodes=[]):
        dictOuvertures = {}
        listeUnitesUtilisees = []
        listeGroupesUtilises = []
        # Get Conditions
        conditions = self.GetSQLdates(listePeriodes)
        if len(conditions) > 0 :
            conditionDates = " AND %s" % conditions
        else:
            conditionDates = ""
        if len(listeActivites) == 0 : conditionActivites = "()"
        elif len(listeActivites) == 1 : conditionActivites = "(%d)" % listeActivites[0]
        else : conditionActivites = str(tuple(listeActivites))
        req = """SELECT IDouverture, IDunite, IDgroupe, date
        FROM ouvertures 
        WHERE IDactivite IN %s %s
        ORDER BY date; """ % (conditionActivites, conditionDates)
        self.DB.ExecuterReq(req,MsgBox="CTRL_Remplissage")
        listeDonnees = self.DB.ResultatReq()
        for IDouverture, IDunite, IDgroupe, date in listeDonnees :
            if IDunite not in listeUnitesUtilisees :
                listeUnitesUtilisees.append(IDunite)
            if IDgroupe not in listeGroupesUtilises :
                listeGroupesUtilises.append(IDgroupe)
            dateDD = DateEngEnDateDD(date)
            dictValeurs = { "IDouverture" : IDouverture, "etat" : True, "initial" : True}
            if (dateDD in dictOuvertures) == False :
                dictOuvertures[dateDD] = {}
            if (IDgroupe in dictOuvertures[dateDD]) == False :
                dictOuvertures[dateDD][IDgroupe] = {}
            if (IDunite in dictOuvertures[dateDD][IDgroupe]) == False :
                dictOuvertures[dateDD][IDgroupe][IDunite] = {}
        return dictOuvertures, listeUnitesUtilisees, listeGroupesUtilises

    def GetDictRemplissage(self, listeActivites=[], listePeriodes=[]):
        dictRemplissage = {}
        dictUnitesRemplissage = {}
        dictConsoAttente = {}
        
        # Get Conditions
        conditions = self.GetSQLdates(listePeriodes)
        if len(conditions) > 0 :
            conditionDates = " AND %s" % conditions
        else:
            conditionDates = ""
        
        conditions2 = self.GetSQLdates2(listePeriodes)
        if len(conditions2) > 0 :
            conditionDates2 = " AND %s" % conditions2
        else:
            conditionDates2 = ""
            
        if len(listeActivites) == 0 : conditionActivites = "()"
        elif len(listeActivites) == 1 : conditionActivites = "(%d)" % listeActivites[0]
        else : conditionActivites = str(tuple(listeActivites))
        
        # R�cup�ration des unit�s de remplissage
        req = """SELECT IDunite_remplissage_unite, IDunite_remplissage, IDunite
        FROM unites_remplissage_unites; """ 
        self.DB.ExecuterReq(req,MsgBox="CTRL_Remplissage")
        listeUnites = self.DB.ResultatReq()
        for IDunite_remplissage_unite, IDunite_remplissage, IDunite in listeUnites :
            if (IDunite in dictUnitesRemplissage) == False :
                dictUnitesRemplissage[IDunite] = [IDunite_remplissage,]
            else:
                dictUnitesRemplissage[IDunite].append(IDunite_remplissage)
                                
        # R�cup�ration des unit�s de remplissage
        req = """SELECT IDunite_remplissage, IDactivite, ordre, nom, abrege, date_debut, date_fin, seuil_alerte, heure_min, heure_max, etiquettes
        FROM unites_remplissage 
        WHERE IDactivite IN %s %s
        AND (afficher_page_accueil IS NULL OR afficher_page_accueil=1)
        ;""" % (conditionActivites, conditionDates2)
        self.DB.ExecuterReq(req,MsgBox="CTRL_Remplissage")
        listeUnitesRemplissage = self.DB.ResultatReq()
        for IDunite_remplissage, IDactivite, ordre, nom, abrege, date_debut, date_fin, seuil_alerte, heure_min, heure_max, etiquettes in listeUnitesRemplissage :
            etiquettes = UTILS_Texte.ConvertStrToListe(etiquettes)
            dictRemplissage[IDunite_remplissage] = {"IDactivite" : IDactivite,
                                                                        "ordre" : ordre,
                                                                        "nom" : nom,
                                                                        "abrege" : abrege,
                                                                        "date_debut" : DateEngEnDateDD(date_debut),
                                                                        "date_fin" : DateEngEnDateDD(date_fin),
                                                                        "seuil_alerte" : seuil_alerte,
                                                                        "heure_min" : heure_min,
                                                                        "heure_max" : heure_max,
                                                                        "etiquettes" : etiquettes,
                                                                        }
                                                                        
        # R�cup�ration des param�tres de remplissage
        req = """SELECT IDremplissage, IDactivite, IDunite_remplissage, IDgroupe, date, places
        FROM remplissage 
        WHERE IDactivite IN %s %s
        ORDER BY date;""" % (conditionActivites, conditionDates)
        self.DB.ExecuterReq(req,MsgBox="CTRL_Remplissage")
        listeRemplissage = self.DB.ResultatReq()
        for IDremplissage, IDactivite, IDunite_remplissage, IDgroupe, date, places in listeRemplissage :
            if places == 0 : places = None
            dateDD = DateEngEnDateDD(date)
            dictValeursTemp = { "nbrePlacesInitial" : places, "nbrePlacesPrises" : 0, "nbrePlacesAttente" : 0 }
            if (IDunite_remplissage in dictRemplissage) == False:
                dictRemplissage[IDunite_remplissage] = {}
            if (dateDD in dictRemplissage[IDunite_remplissage]) == False:
                dictRemplissage[IDunite_remplissage][dateDD] = {}
            if (IDgroupe in dictRemplissage[IDunite_remplissage][dateDD]) == False:
                dictRemplissage[IDunite_remplissage][dateDD][IDgroupe] = dictValeursTemp

        # R�cup�ration des consommations existantes 
        req = """SELECT IDactivite, date, IDunite, IDgroupe, heure_debut, heure_fin, etat, quantite, etiquettes
        FROM consommations 
        WHERE IDactivite IN %s %s; """ % (conditionActivites, conditionDates)
        self.DB.ExecuterReq(req,MsgBox="CTRL_Remplissage")
        listeConso = self.DB.ResultatReq()
        for IDactivite, date, IDunite, IDgroupe, heure_debut, heure_fin, etat, quantite, etiquettesConso in listeConso :
            dateDD = DateEngEnDateDD(date)
            etiquettesConso = UTILS_Texte.ConvertStrToListe(etiquettesConso)

            # Quantit�
            if quantite == None :
                quantite = 1
                        
            # M�morisation des nbre de places
            if IDunite in dictUnitesRemplissage :
                for IDunite_remplissage in dictUnitesRemplissage[IDunite] :
                    if (IDunite_remplissage in dictRemplissage) == False :
                        dictRemplissage[IDunite_remplissage] = {}
                    if (dateDD in dictRemplissage[IDunite_remplissage]) == False :
                        dictRemplissage[IDunite_remplissage][dateDD] = {}
                    if (IDgroupe in dictRemplissage[IDunite_remplissage][dateDD]) == False :
                        dictRemplissage[IDunite_remplissage][dateDD][IDgroupe] = {}
                    if ("nbrePlacesPrises" in dictRemplissage[IDunite_remplissage][dateDD][IDgroupe]) == False :
                        dictRemplissage[IDunite_remplissage][dateDD][IDgroupe]["nbrePlacesPrises"] = 0

                    # R�servations
                    if etat in ["reservation", "present"] :
                        valide = True
                        
                        # V�rifie s'il y a une plage horaire conditionnelle :
                        try :
                            heure_min = dictRemplissage[IDunite_remplissage]["heure_min"]
                            heure_max = dictRemplissage[IDunite_remplissage]["heure_max"]
                            if heure_min != None and heure_max != None and heure_debut != None and heure_fin != None :
                                heure_min_TM = HeureStrEnTime(heure_min)
                                heure_max_TM = HeureStrEnTime(heure_max)
                                heure_debut_TM = HeureStrEnTime(heure_debut)
                                heure_fin_TM = HeureStrEnTime(heure_fin)
                                
                                if heure_debut_TM <= heure_max_TM and heure_fin_TM >= heure_min_TM :
                                    valide = True
                                else:
                                    valide = False
                        except :
                            pass
                        
                        # V�rifie si condition �tiquettes
                        if "etiquettes" in dictRemplissage[IDunite_remplissage] :
                            etiquettes = dictRemplissage[IDunite_remplissage]["etiquettes"]
                            if len(etiquettes) > 0 :
                                etiquettesCommunes = set(etiquettes) & set(etiquettesConso)
                                if len(etiquettesCommunes) == 0 :
                                    valide = False

                        # M�morisation de la place prise
                        if valide == True :
                            dictRemplissage[IDunite_remplissage][dateDD][IDgroupe]["nbrePlacesPrises"] += quantite

                    # M�morisation des places sur liste d'attente
                    if etat == "attente" :
                        if (dateDD in dictConsoAttente) == False :
                            dictConsoAttente[dateDD] = {}
                        if (IDgroupe in dictConsoAttente[dateDD]) == False :
                            dictConsoAttente[dateDD][IDgroupe] = {}
                        if (IDunite_remplissage in dictConsoAttente[dateDD][IDgroupe]) == False :
                            dictConsoAttente[dateDD][IDgroupe][IDunite_remplissage] = quantite
                        else:
                            dictConsoAttente[dateDD][IDgroupe][IDunite_remplissage] += quantite

        # Cloture de la BD
        return dictRemplissage, dictUnitesRemplissage, dictConsoAttente

    def GetDictGroupes(self):
        dictGroupes = {}
        req = """SELECT IDgroupe, IDactivite, nom, ordre, abrege
        FROM groupes
        ORDER BY nom;"""
        self.DB.ExecuterReq(req,MsgBox="CTRL_Remplissage")
        listeDonnees = self.DB.ResultatReq()
        dictGroupes[0] = { "IDactivite" : 0, "nom" : _("Sans groupe"), "ordre" : 0, "abrege" : _("SANS")}
        for IDgroupe, IDactivite, nom, ordre, abrege in listeDonnees :
            if IDgroupe in self.listeGroupesUtilises :
                if abrege == None : abrege = ""
                dictGroupes[IDgroupe] = { "IDactivite" : IDactivite, "nom" : nom, "ordre" : ordre, "abrege" : abrege }
        return dictGroupes
        
    def GetSQLdates(self, listePeriodes=[]):
        """ Avec date """
        texteSQL = ""
        for date_debut, date_fin in listePeriodes :
            texteSQL += "(date>='%s' AND date<='%s') OR " % (date_debut, date_fin)
        if len(texteSQL) > 0 :
            texteSQL = "(" + texteSQL[:-4] + ")"
        else:
            texteSQL = "date='3000-01-01'"
        return texteSQL

    def GetSQLdates2(self, listePeriodes=[]):
        """ Avec date_debut et date_fin """
        texteSQL = ""
        for date_debut, date_fin in listePeriodes :
            texteSQL += "(date_fin>='%s' AND date_debut<='%s') OR " % (date_debut, date_fin)
        if len(texteSQL) > 0 :
            texteSQL = "(" + texteSQL[:-4] + ")"
        else:
            texteSQL = "date_debut='3000-01-01'"
        return texteSQL    

    def Importation_activites(self):
        if len(self.listeActivites) == 0:
            return {}
        # Recherche les activites disponibles
        dictActivites = {}
        req = """SELECT activites.IDactivite, activites.nom, abrege, date_debut, date_fin
        FROM activites
        WHERE activites.IDactivite in ( %s )
        ORDER BY activites.nom;"""%str(self.listeActivites)[1:-1]
        self.DB.ExecuterReq(req,MsgBox="CTRL_Remplissage")
        listeActivites = self.DB.ResultatReq()
        for IDactivite, nom, abrege, date_debut, date_fin in listeActivites :
            if date_debut != None : date_debut = DateEngEnDateDD(date_debut)
            if date_fin != None : date_fin = DateEngEnDateDD(date_fin)
            dictTemp = { "nom" : nom, "abrege" : abrege, "date_debut" : date_debut, "date_fin" : date_fin }
            dictActivites[IDactivite] = dictTemp
        return dictActivites
    
    def GetEtatPlaces(self):
        """ Fonction qui sert au DLG_Attente pour savoir si des places se sont lib�r�es """
        dictEtatPlaces = {}
        # Parcours les lignes
        for numLigne, ligne in self.dictLignes.items() :
            # Parcours les cases :
            for numColonne, case in ligne.dictCases.items() :
                if case.typeCase == "consommation" :
                    dictInfosPlaces = case.dictInfosPlaces
                    date = case.date
                    IDgroupe = case.IDgroupe
                    IDuniteRemplissage = case.IDunite
                    IDactivite = case.IDactivite
                    # M�morisation dans un dict
                    dictEtatPlaces[(date, IDactivite, IDgroupe, IDuniteRemplissage)] = dictInfosPlaces
        return dictEtatPlaces
    
    def GetLargeurColonneUnite(self):
        return LARGEUR_COLONNE_UNITE

    def SetLargeurColonneUnite(self, largeur=60):
        global LARGEUR_COLONNE_UNITE
        LARGEUR_COLONNE_UNITE = largeur
        UTILS_Config.SetParametre("largeur_colonne_unite_remplissage", largeur)

    def GetAbregeGroupes(self):
        return ABREGE_GROUPES
    
    def SetAbregeGroupes(self, etat=0):
        global ABREGE_GROUPES
        ABREGE_GROUPES = int(etat)
        UTILS_Config.SetParametre("remplissage_abrege_groupes", etat)

    def GetAfficheTotaux(self):
        return AFFICHE_TOTAUX

    def SetAfficheTotaux(self, etat=0):
        global AFFICHE_TOTAUX
        AFFICHE_TOTAUX = int(etat)
        UTILS_Config.SetParametre("remplissage_affiche_totaux", etat)

    def GetDataImpression(self):
        from Outils import printout
##        import wx.lib.printout as printout
        
        prt = printout.PrintTable(None)
        prt.SetLandscape() 
        data = []
        
        nbreLignes = self.GetNumberRows()
        nbreColonnes = self.GetNumberCols()
        if nbreLignes == 0 or nbreColonnes == 0 :
            dlg = wx.MessageDialog(self, _("Il n'y a rien � imprimer !"), "Erreur", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return None
        
        # Entete des colonnes
        ligne = ["",]
        largeursColonnes = [1.8,]
        for numCol in range(0, nbreColonnes):
            valeur = self.GetColLabelValue(numCol)
            ligne.append(valeur.replace("\n", " "))
            largeursColonnes.append(0.5)
        data.append(ligne)
        
        # Contenu du tableau
        dictCouleurs = {}
        listeCouleursEntetes = {}
        for numLigne in range(0, nbreLignes):
            ligne = []
            labelLigne = self.GetRowLabelValue(numLigne)
            couleurEntete = self.dictLignes[numLigne].renderer._bgcolor
            listeCouleursEntetes[numLigne] = couleurEntete
            ligne.append(labelLigne)
            for numCol in range(0, nbreColonnes):
                couleur = self.GetCellRenderer(numLigne, numCol).case.couleurFond
                dictCouleurs[(numLigne, numCol)] = couleur
                ligne.append(self.GetCellValue(numLigne, numCol))
            data.append(ligne)
        
        prt.data = data
        prt.set_column = largeursColonnes
        prt.SetRowSpacing(4, 4)
        
        # Aligne toutes les colonnes au milieu
        for numCol in range(0, nbreColonnes+1):
            prt.SetColAlignment(numCol, wx.ALIGN_CENTRE)
        
        # Colore les entetes de colonnes
        for numCol in range(0, nbreColonnes+1) :
            prt.SetCellColour(0, numCol, (210, 210, 210) )
            
        # Colore les entetes de lignes
        for numLigne, couleur in listeCouleursEntetes.items() :
            prt.SetCellColour(numLigne+1, 0, couleur)
        
        # Colore les cases du contenu
        for coords, couleur in dictCouleurs.items() :
            numLigne, numCol = coords
            prt.SetCellColour(numLigne+1, numCol+1, couleur)
            
        prt.SetHeader(_("Effectifs"), colour = wx.NamedColour('BLACK'))
##        prt.SetHeader("Le ", type = "Date & Time", align=wx.ALIGN_RIGHT, indent = -1, colour = wx.NamedColour('BLACK'))
        prt.SetFooter("Page ", colour = wx.NamedColour('BLACK'), type ="Num")
        return prt

    def Apercu(self):
        from Utils import UTILS_Printer
        prt = self.GetDataImpression()
        if prt == None : return
        # Preview
        data = wx.PrintDialogData(prt.printData)
        printout = prt.GetPrintout()
        printout2 = prt.GetPrintout()
        preview = wx.PrintPreview(printout, printout2, data)
        if not preview.Ok():
            wx.MessageBox(_("D�sol�, un probl�me a �t� rencontr� dans l'aper�u avant impression..."), "Erreur", wx.OK)
            return
##        frm = UTILS_Printer.PreviewFrame(preview, None)
        frame = wx.GetApp().GetTopWindow() 
        frm = wx.PreviewFrame(preview, None, _("Aper�u avant impression"))
        frm.Initialize()
        frm.MakeModal(False)
        frm.SetPosition(frame.GetPosition())
        frm.SetSize(frame.GetSize())
        frm.Show(True)
    
    def Imprimer(self):
        prt = self.GetDataImpression()
        if prt == None : return
        prt.Print()

    def ExportTexte(self, event=None):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(grid=self, titre=_("Remplissage"))
        
    def ExportExcel(self, event=None):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(grid=self, titre=_("Remplissage"))

    def OnChangeColSize(self, event):
        numColonne = event.GetRowOrCol()
        largeur = self.GetColSize(numColonne)
        if len(self.dictLignes) == 0: return
        ligne = self.dictLignes[0]
        case = ligne.dictCases[numColonne]

        if case.typeCase == "activite":
            self.SetColSize(numColonne, LARGEUR_COLONNE_ACTIVITE)

        if case.typeCase == "consommation" and case.estTotal == True :
            self.SetColSize(numColonne, LARGEUR_COLONNE_UNITE)

        if case.typeCase == "consommation" and case.estTotal == False :
            DB = GestionDB.DB()
            DB.ReqMAJ("unites_remplissage", [("largeur", int(largeur)),], "IDunite_remplissage", case.IDunite)
            DB.Close()

# -------------------------------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        self.grille = CTRL(panel)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        if self.grille.GetNumberCols() == 0:
            self.grille = wx.StaticText(self, -1,"Aucune activit� remont�e...")
        sizer_2.Add(self.grille, 1, wx.EXPAND, 0)
        panel.SetSizer(sizer_2)
        self.SetSize((750, 400))
        self.Layout()
        
        

if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "TEST", name="test")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()

"""
try:
except Exception as err:
        print(err)
        raise
"""
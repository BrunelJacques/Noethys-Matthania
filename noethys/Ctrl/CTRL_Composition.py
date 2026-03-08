#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
# -----------------------------------------------------------
# Application :    Noethys branche Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
# -----------------------------------------------------------

import Chemins
from Utils.UTILS_Traduction import _
import wx
import GestionDB
import sys

import wx.lib.agw.hypertreelist as HTL

from Data import DATA_Civilites as Civilites

from Utils import UTILS_Interface
from Gest.GestionComposition import GestCompo
#from Outils.testGestionComposition import GestCompo
from Utils import UTILS_Utilisateurs

class CadreIndividu():
    # Spécifique pour affichage graphique
    def __init__(self, parent, dc, IDindividu=None, listeTextes=[], genre="M", photo=None,
                 xCentre=None, yCentre=None,
                 largeur=None, hauteur=None, numCol=None, titulaire=0, correspondant=0,
                 calendrierActif=False):

        self.parent = parent
        self.zoom = 1
        self.zoomContenu = True

        self.selectionCadre = False
        self.survolCadre = False
        self.calendrierActif = calendrierActif
        self.survolCalendrier = False

        self.IDindividu = IDindividu
        self.dc = dc
        self.IDobjet = wx.Window.NewControlId()
        self.listeTextes = listeTextes
        self.genre = genre
        self.photo = photo
        self.numCol = numCol
        self.titulaire = titulaire
        self.correspondant = correspondant
        self.xCentre = xCentre
        self.yCentre = yCentre
        self.largeur = largeur
        self.hauteur = hauteur

        self.Draw()

    def Draw(self):
        largeur = self.largeur
        hauteur = self.hauteur

        # Création de l'ID pour le dictionnaire d'objets
        if self.IDobjet in self.parent.dictIDs:
            self.dc.RemoveId(self.IDobjet)
        self.dc.SetId(self.IDobjet)

        # Zoom Cadre
        if self.zoom != 1:
            largeur, hauteur = largeur * self.zoom, hauteur * self.zoom

        # Zoom Contenu
        if self.zoomContenu == True:
            self.zoomContenuRatio = self.zoom
        else:
            self.zoomContenuRatio = 1

        # Paramètres du cadre
        x, y = int(self.xCentre - (largeur / 2)), int(self.yCentre - (hauteur / 2))
        self.x, self.y = x, y
        if self.genre == "M":
            couleurFondHautCadre = (217, 212, 251)
            couleurFondBasCadre = (196, 188, 252)
        else:
            couleurFondHautCadre = (251, 212, 239)
            couleurFondBasCadre = (253, 193, 235)
        couleurBordCadre = (0, 0, 0)
        couleurSelectionCadre = (133, 236, 90)
        paddingCadre = 8 * self.zoomContenuRatio
        taillePhoto = (self.hauteur - (paddingCadre * 2)) * self.zoomContenuRatio

        # Dessin du cadre de sélection
        if self.selectionCadre == True:
            ecart = 5
            self.dc.SetBrush(wx.Brush((0, 0, 0), style=wx.TRANSPARENT))
            self.dc.SetPen(wx.Pen(couleurSelectionCadre, 1, wx.DOT))
            self.dc.DrawRoundedRectangle(
                wx.Rect(int(x - ecart), int(y - ecart), int(largeur + (ecart * 2)),
                        int(hauteur + (ecart * 2))), radius=int(5 * self.zoom))

        # Dessin du cadre
        self.dc.SetBrush(wx.Brush(couleurFondBasCadre))
        self.dc.SetPen(wx.Pen(couleurBordCadre, 1))
        if "linux" in sys.platform:
            self.dc.DrawRectangle(wx.Rect(int(x), int(y), int(largeur), int(hauteur)))
        else:
            self.dc.DrawRoundedRectangle(
                wx.Rect(int(x), int(y), int(largeur), int(hauteur)), radius=5 * self.zoom)

        if "linux" not in sys.platform:
            coordsSpline = [(int(x + 1), int(y + (hauteur / 3))),
                            (int(x + (largeur / 2.5)), int(y + (hauteur / 4.1))),
                            (int(x + largeur - 1), int(y + (hauteur / 1.8)))]
            self.dc.DrawSpline(coordsSpline)

            self.dc.SetBrush(wx.Brush(couleurFondHautCadre))
            self.dc.FloodFill(int(x + 5), int(y + 5), couleurBordCadre,
                              style=wx.FLOOD_BORDER)

            self.dc.SetPen(wx.Pen(couleurFondBasCadre, 1))
            self.dc.DrawSpline(coordsSpline)

        # Intégration de la photo
        if self.photo != None:
            try:
                img = self.photo.ConvertToImage()
                img = img.Rescale(width=int(taillePhoto), height=int(taillePhoto),
                                  quality=wx.IMAGE_QUALITY_HIGH)
                self.bmp = img.ConvertToBitmap()
                self.dc.DrawBitmap(self.bmp, int(x + paddingCadre), int(y + paddingCadre))
            except:
                pass

        # Dessin du texte
        largeurMaxiTexte = largeur - paddingCadre * 3 - taillePhoto
        hauteurMaxiTexte = hauteur - paddingCadre
        posXtexte = x + paddingCadre * 2 + taillePhoto - 2
        posYtexte = y + paddingCadre - 2
        for texte, tailleFont, styleFont in self.listeTextes:
            # Font
            font = self.parent.GetFont()
            font.SetPointSize(int(tailleFont * self.zoomContenuRatio))
            if styleFont == "normal": font.SetWeight(wx.FONTWEIGHT_NORMAL)
            if styleFont == "light": font.SetWeight(wx.FONTWEIGHT_LIGHT)
            if styleFont == "bold": font.SetWeight(wx.FONTWEIGHT_BOLD)
            self.parent.SetFont(font)
            self.dc.SetFont(font)
            # Texte
            largeurTexte, hauteurTexte = self.parent.GetTextExtent(texte)
            if (posYtexte - y + hauteurTexte) < hauteurMaxiTexte:
                if largeurTexte > largeurMaxiTexte:
                    texte = self.AdapteLargeurTexte(self.dc, texte, largeurMaxiTexte)
                if texte == "#SPACER#": texte = " "
                self.dc.DrawText(texte, int(posXtexte), int(posYtexte))
                posYtexte += hauteurTexte + 1

        # Dessin du cadre Accès aux consommations
        if self.calendrierActif == True and self.zoom > 1:
            # Image de calendrier
            if self.survolCalendrier == True:
                bmpConso = wx.Bitmap(
                    Chemins.GetStaticPath("Images/32x32/Calendrier_modifier.png"),
                    wx.BITMAP_TYPE_ANY)
            else:
                bmpConso = wx.Bitmap(Chemins.GetStaticPath("Images/32x32/Calendrier.png"),
                                     wx.BITMAP_TYPE_ANY)
            xBmpConso, yBmpConso = x + largeur - 5 - 32, y + 5
            self.dc.DrawBitmap(bmpConso, int(xBmpConso), int(yBmpConso))

        # Symboles de l'individu
        xSymbole = x + paddingCadre
        ySymbole = y + paddingCadre + 2

        # Dessin du symbole TITULAIRE
        if self.titulaire == 1:
            bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Titulaire.png"),
                            wx.BITMAP_TYPE_ANY)
            self.dc.DrawBitmap(bmp, int(xSymbole), int(ySymbole))
            xSymbole += 42
        if self.correspondant:
            bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Titulaire.png"),
                            wx.BITMAP_TYPE_ANY)
            self.dc.DrawBitmap(bmp, int(xSymbole), int(ySymbole))
            xSymbole += 16

        # Mémorisation dans le dictionnaire d'objets
        self.dc.SetIdBounds(self.IDobjet,
                            wx.Rect(int(x), int(y), int(largeur), int(hauteur)))
        self.parent.dictIDs[self.IDobjet] = ("individu", self.IDindividu)

    def SurvolCalendrier(self, x, y):
        largeurCadre, hauteurCadre = self.largeur * self.zoom, self.hauteur * self.zoom
        xBmpConso, yBmpConso = self.x + largeurCadre - 5 - 32, self.y + 5
        if (y >= self.y + 4 and y <= self.y + 6 + 32) and (
                x >= xBmpConso - 1 and x <= xBmpConso + 32 + 1):
            return True
        else:
            return False

    def AdapteLargeurTexte(self, dc, texte, tailleMaxi):
        """ Raccourcit le texte en fonction de la taille donnée """
        tailleTexte = self.parent.GetTextExtent(texte)[0]
        texteTemp, texteTemp2 = "", ""
        for lettre in texte:
            texteTemp += lettre
            if self.parent.GetTextExtent(texteTemp + "...")[0] <= tailleMaxi:
                texteTemp2 = texteTemp
            else:
                return texteTemp2 + "..."

    def Selectionne(self, etat=True):
        if etat == True:
            self.selectionCadre = True
        else:
            self.selectionCadre = False
        self.Draw()
        self.parent.Refresh()
        self.parent.Update()

    def ActiveCalendrier(self, etat):
        self.survolCalendrier = etat
        self.Draw()
        self.parent.Refresh()
        self.parent.Update()

    def ZoomAvant(self, coef=2, vitesse=1):
        if self.zoom == 1:
            for x in range(10, int(coef * 10)):
                self.zoom = (x * 0.1) + 0.1
                wx.MilliSleep(int(vitesse))
                self.Draw()
                self.parent.Refresh()
                self.parent.Update()

    def ZoomArriere(self, vitesse=0.5):
        if self.zoom > 1:
            for x in range(int(self.zoom * 10), 10 - 1, -1):
                self.zoom = (x * 0.1)
                wx.MilliSleep(int(vitesse))
                self.Draw()
                self.parent.Refresh()
                self.parent.Update()

# ----------Classes d'affichage des compositions -----------------------------------------

class CTRL_Graphique(wx.ScrolledWindow, GestCompo):
    def __init__(self, parent, IDfamille=None):
        wx.ScrolledWindow.__init__(self, parent, -1, (0, 0), size=wx.DefaultSize,
                                   name="graphique", style=wx.SUNKEN_BORDER)
        GestCompo.__init__(self,parent,IDfamille)

        if hasattr(self.Parent, "dlgFamille"):
            self.dlgFamille = self.Parent.dlgFamille
        elif hasattr(self.GrandParent, "dlgFamille"):
            self.dlgFamille = self.GrandParent.dlgFamille
        self.selectionCadre = None
        self.init_ok = False

        # Paramètres
        self.zoomActif = True  # Active ou non le zoom sur une case
        self.espaceVerticalDefaut = 22  # Hauteur entre 2 cases
        self.espaceHorizontalDefautCol1 = 40  # Espace après col 1
        self.espaceHorizontalDefautCol2 = 80  # Espace après col 2
        self.hauteurCaseDefaut = 75  # 70 # Hauteur par défaut d'une case
        self.largeurCaseDefaut = 210  # Largeur par défaut d'une case

        self.couleurFondCol1 = UTILS_Interface.GetValeur("couleur_tres_claire",
                                                         wx.Colour(238, 253, 252))
        self.couleurFondCol2 = UTILS_Interface.GetValeur("couleur_tres_claire",
                                                         wx.Colour(238, 253, 252))
        self.couleurFondCol3 = UTILS_Interface.GetValeur("couleur_tres_claire_2",
                                                         wx.Colour(214, 250, 199))

        self.bmp_responsables = wx.Bitmap(
            Chemins.GetStaticPath("Images/Special/GeneaResponsables.png"),
            wx.BITMAP_TYPE_PNG)
        self.bmp_enfants = wx.Bitmap(
            Chemins.GetStaticPath("Images/Special/GeneaEnfants.png"), wx.BITMAP_TYPE_PNG)
        self.bmp_contacts = wx.Bitmap(
            Chemins.GetStaticPath("Images/Special/GeneaContacts.png"), wx.BITMAP_TYPE_PNG)

        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDLeftDown)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeaveWindow)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnContextMenu)

        # create a PseudoDC to record our drawing
        self.pdc = wx.adv.PseudoDC()
        self.dictIDs = {}
        ##        self.DoDrawing(self.pdc)

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda x: None)

    def OnSize(self, event):
        self.DoDrawing(self.pdc)
        self.Refresh()
        event.Skip()

    def MAJ(self):
        # Récupération des self.getVal
        self.MAJ_common()

        # Actualisation du graphique
        if self.init_ok == False:
            self.Bind(wx.EVT_SIZE, self.OnSize)
            self.init_ok = True
        self.DoDrawing(self.pdc)
        self.Refresh()

    def OnPaint(self, event):
        # Create a buffered paint DC.  It will create the real
        # wx.PaintDC and then blit the bitmap to it when dc is
        # deleted.
        dc = wx.BufferedPaintDC(self)
        # use PrepateDC to set position correctly
        if wx.VERSION < (2, 9, 0, 0):
            self.PrepareDC(dc)
        # we need to clear the dc BEFORE calling PrepareDC
        colFond = wx.SystemSettings.GetColour(30)  # self.GetBackgroundColour()
        bg = wx.Brush(colFond)
        dc.SetBackground(bg)
        dc.Clear()
        # create a clipping rect from our position and size
        # and the Update Region
        xv, yv = self.GetViewStart()
        dx, dy = self.GetScrollPixelsPerUnit()
        x, y = (xv * dx, yv * dy)
        rgn = self.GetUpdateRegion()
        rgn.Offset(x, y)
        r = rgn.GetBox()
        # draw to the dc using the calculated clipping rect
        self.pdc.DrawToDCClipped(dc, r)

    def DoDrawing(self, dc):
        """ Creation du dessin dans le PseudoDC """
        dc.RemoveAll()
        # dc.BeginDrawing()
        tailleDC = self.GetSize()
        # Calcul des positions horizontales des cases
        largeurCase = self.largeurCaseDefaut
        largeurBloc = (
                                  3 * largeurCase) + self.espaceHorizontalDefautCol1 + self.espaceHorizontalDefautCol2
        xBloc = (tailleDC[0] / 2.0) - (largeurBloc / 2.0)
        xBloc1 = xBloc + (largeurCase / 2.0)

        posSeparationCol1 = xBloc1 + (largeurCase / 2.0) + (
                    self.espaceHorizontalDefautCol1 / 2.0)
        posSeparationCol2 = posSeparationCol1 + (
                    self.espaceHorizontalDefautCol1 / 2.0) + largeurCase + (
                                        self.espaceHorizontalDefautCol2 / 2.0)

        self.posSeparationCol1 = posSeparationCol1
        self.posSeparationCol2 = posSeparationCol2

        # Création des colonnes
        dictColonnes = {1: [], 2: [], 3: []}
        for IDindividu, valeurs in self.dictCadres.items():
            if valeurs["categorie"] == 1: dictColonnes[1].append(IDindividu)
            if valeurs["categorie"] == 2: dictColonnes[2].append(IDindividu)
            if valeurs["categorie"] == 3: dictColonnes[3].append(IDindividu)

        xCentre = xBloc1

        for numCol in [1, 2, 3]:
            nbreCases = len(dictColonnes[numCol])
            espaceVertical = self.espaceVerticalDefaut
            dc.SetId(numCol)

            # Diminue la hauteur des cases si la fenêtre est trop petite
            hauteurBloc = (nbreCases * self.hauteurCaseDefaut) + (
                        nbreCases - 1) * espaceVertical
            coef = (tailleDC[1] - 60) * 1.0 / hauteurBloc
            if coef < 1:
                hauteurCase = self.hauteurCaseDefaut * coef
                if hauteurCase < 28:
                    hauteurCase = 28
                if hauteurCase < 70:
                    espaceVertical = self.espaceVerticalDefaut * coef
            else:
                hauteurCase = self.hauteurCaseDefaut

            # Calcul des positions verticales des cases
            hauteurBloc = (nbreCases * hauteurCase) + (nbreCases - 1) * espaceVertical
            yBloc = (tailleDC[1] / 2.0) - (hauteurBloc / 2.0)
            yBloc1 = yBloc + (hauteurCase / 2.0) + 10

            # Dessin du fond de couleur
            paramFond = {
                1: {"couleurFond": self.couleurFondCol1, "x": 0,
                    "width": posSeparationCol1, "bmp": self.bmp_responsables},
                2: {"couleurFond": self.couleurFondCol2, "x": posSeparationCol1,
                    "width": posSeparationCol2 - posSeparationCol1,
                    "bmp": self.bmp_enfants},
                3: {"couleurFond": self.couleurFondCol3, "x": posSeparationCol2,
                    "width": tailleDC[0] - posSeparationCol2, "bmp": self.bmp_contacts},
            }
            if numCol in paramFond:
                dc.SetBrush(wx.Brush(paramFond[numCol]["couleurFond"]))
                dc.SetPen(wx.Pen(paramFond[numCol]["couleurFond"], 0))
                dc.DrawRectangle(x=int(paramFond[numCol]["x"]), y=0,
                                 width=int(paramFond[numCol]["width"]),
                                 height=int(tailleDC[1]))
                bmp = paramFond[numCol]["bmp"]
                dc.DrawBitmap(bmp, int(xCentre - (bmp.GetSize()[0] / 2.0)), 10)

            # Création des cases
            yCentre = yBloc1
            for IDindividu in dictColonnes[numCol]:
                listeTextes = self.dictCadres[IDindividu]["textes"]
                genre = self.dictCadres[IDindividu]["genre"]
                nomImage = self.dictCadres[IDindividu]["nomImage"]
                titulaire = self.dictCadres[IDindividu]["titulaire"]
                correspondant = self.dictCadres[IDindividu]["correspondant"]
                calendrierActif = self.dictCadres[IDindividu]["inscriptions"]
                photo = self.dictCadres[IDindividu]["photo"]
                cadre = CadreIndividu(self, dc, IDindividu, listeTextes, genre,
                                      photo, xCentre, yCentre, largeurCase,
                                      hauteurCase, numCol, titulaire, correspondant,
                                      calendrierActif)
                self.dictCadres[IDindividu]["ctrl"] = cadre
                yCentre += hauteurCase + espaceVertical

            if numCol == 1: xCentre += largeurCase + self.espaceHorizontalDefautCol1
            if numCol == 2: xCentre += largeurCase + self.espaceHorizontalDefautCol2

        # Dessin des liens de cadres
        dc.SetId(wx.Window.NewControlId())
        self.DrawLiens(dc)

        # dc.EndDrawing()

    def DrawLiensCouple(self, dc, listeLiensCouple, type=""):
        nbreLiensCouple = len(listeLiensCouple)
        for IDindividu1, IDindividu2 in listeLiensCouple:
            if IDindividu1 in self.dictCadres and IDindividu2 in self.dictCadres:
                dc.SetId(wx.Window.NewControlId())
                decalage = 20  # Décalage de la ligne de lien par rapport au bord du cadre
                listePoints = []
                for IDindividu in (IDindividu1, IDindividu2):
                    xCentre = int(self.dictCadres[IDindividu]["ctrl"].xCentre)
                    yCentre = int(self.dictCadres[IDindividu]["ctrl"].yCentre)
                    largeur = int(self.dictCadres[IDindividu]["ctrl"].largeur *
                                  self.dictCadres[IDindividu]["ctrl"].zoom)
                    bordCadre = (int(xCentre - largeur / 2.0 - 1), int(yCentre))
                    extremiteLigne = (
                    int(xCentre - largeur / 2.0 - decalage), int(yCentre))
                    dc.SetPen(wx.Pen((123, 241, 131), 1, wx.DOT))
                    dc.DrawLine(bordCadre, extremiteLigne)
                    listePoints.append(extremiteLigne)
                # Barre qui relie
                dc.DrawLine(listePoints[0], listePoints[1])
                # Dessin d'un bitmap
                if type == "ex-couple":
                    bmpCouple = wx.Bitmap(
                        Chemins.GetStaticPath("Images/16x16/Divorce.png"),
                        wx.BITMAP_TYPE_PNG)
                    dc.DrawBitmap(bmpCouple, extremiteLigne[0] - 8,
                                  int((listePoints[0][1] - listePoints[1][1]) / 2.0 +
                                      listePoints[1][1] - 8))

    def DrawLiens(self, dc):
        for numCol in [1, 2, 3]:
            # Dessin des liens de couple
            listeLiensCouple = self.dictLiensCadres[numCol]["couple"]
            if len(listeLiensCouple) > 0:
                self.DrawLiensCouple(dc, listeLiensCouple, type="couple")
            listeLiensCouple = self.dictLiensCadres[numCol]["ex-couple"]
            if len(listeLiensCouple) > 0:
                self.DrawLiensCouple(dc, listeLiensCouple, type="ex-couple")

            # Recherche des liens de filiation
            dictLiensFiliation = self.dictLiensCadres[numCol]["filiation"]
            dictParents = {}
            for IDenfant, listeParents in dictLiensFiliation.items():
                listeParents = tuple(listeParents)
                if (listeParents in dictParents) == False:
                    dictParents[listeParents] = [IDenfant, ]
                else:
                    dictParents[listeParents].append(IDenfant)

            nbreLiensFiliation = len(dictParents)

            posCentrale = [0,0,0]
            if nbreLiensFiliation == 1: posCentrale = [self.posSeparationCol1, ]
            if nbreLiensFiliation == 2: posCentrale = [self.posSeparationCol1 - 2,
                                                       self.posSeparationCol1 + 2]
            if nbreLiensFiliation == 3: posCentrale = [self.posSeparationCol1 - 4,
                                                       self.posSeparationCol1,
                                                       self.posSeparationCol1 + 4]
            if nbreLiensFiliation == 4: posCentrale = [self.posSeparationCol1 - 6,
                                                       self.posSeparationCol1 - 2,
                                                       self.posSeparationCol1 + 2,
                                                       self.posSeparationCol1 + 6]
            if nbreLiensFiliation == 5: posCentrale = [self.posSeparationCol1 - 8,
                                                       self.posSeparationCol1 - 4,
                                                       self.posSeparationCol1,
                                                       self.posSeparationCol1 + 4,
                                                       self.posSeparationCol1 + 8]

            # Dessin des liens de filiation
            index = 0
            for listeParents, listeEnfants in dictParents.items():
                posXLigneParents = int(posCentrale[index])
                posXLigneEnfants = int(posXLigneParents)

                # Dessine les liens ENFANTS
                listeYenfants = []
                for IDenfant in listeEnfants:
                    xCadreEnfant = int(self.dictCadres[IDenfant]["ctrl"].xCentre)
                    yCadreEnfant = int(self.dictCadres[IDenfant]["ctrl"].yCentre)
                    largeurCadreEnfant = int(self.dictCadres[IDenfant]["ctrl"].largeur *
                                             self.dictCadres[IDenfant]["ctrl"].zoom)
                    bordCadreEnfant = (
                    int(xCadreEnfant - largeurCadreEnfant / 2.0), int(yCadreEnfant))
                    extremiteLigneEnfant = (int(posXLigneEnfants), int(yCadreEnfant))
                    listeYenfants.append(yCadreEnfant)
                    dc.SetPen(wx.Pen((0, 0, 0), 1))
                    dc.DrawLine(bordCadreEnfant, extremiteLigneEnfant)
                # Relient les enfants par une ligne VERTICALE
                if len(listeYenfants) > 0:
                    dc.DrawLine(posXLigneEnfants, min(listeYenfants), posXLigneEnfants,
                                max(listeYenfants))
                centreYenfants = sum(listeYenfants) / len(listeYenfants)

                # Dessine les liens PARENTS
                listeYparents = []
                for IDparent in listeParents:
                    xCentre = int(self.dictCadres[IDparent]["ctrl"].xCentre)
                    yCentre = int(self.dictCadres[IDparent]["ctrl"].yCentre)
                    largeur = int(self.dictCadres[IDparent]["ctrl"].largeur *
                                  self.dictCadres[IDparent]["ctrl"].zoom)
                    bordCadre = (int(xCentre + largeur / 2.0), int(yCentre))
                    extremiteLigneParent = (int(posXLigneParents), int(yCentre))
                    listeYparents.append(yCentre)
                    dc.SetPen(wx.Pen((0, 0, 0), 1))
                    dc.DrawLine(bordCadre, extremiteLigneParent)
                # Relient les parents par une ligne VERTICALE
                if len(listeYparents) > 0:
                    dc.DrawLine(posXLigneParents, min(listeYparents), posXLigneParents,
                                max(listeYparents))
                centreYparents = sum(listeYparents) / len(listeYparents)

                # Relie la barre ENFANTS à la barre PARENTS
                hauteurBarreHorizontale = centreYenfants
                dc.DrawLine(int(posXLigneParents), int(hauteurBarreHorizontale),
                            int(posXLigneEnfants), int(hauteurBarreHorizontale))

                # Rallonge de la barre verticale adulte
                dc.DrawLine(int(posXLigneParents), int(hauteurBarreHorizontale),
                            int(posXLigneParents), int(max(listeYparents)))
                dc.DrawLine(int(posXLigneParents), int(hauteurBarreHorizontale),
                            int(posXLigneParents), int(min(listeYparents)))

                index += 1

    def RechercheCadre(self, x, y):
        """ Recherche le cadre présent sur x, y """
        listeObjets = self.pdc.FindObjectsByBBox(x, y)
        if len(listeObjets) != 0:
            IDobjet = listeObjets[0]
            if IDobjet in self.dictIDs:
                if self.dictIDs[IDobjet][0] == "individu":
                    IDindividu = self.dictIDs[IDobjet][1]
                    return IDindividu
        return None

    def DeselectionneTout(self, ExcepteIDindividu=None):
        """ Désélectionne tous les cadres du dc """
        for IDindividuTmp, valeurs in self.dictCadres.items():
            if ExcepteIDindividu != IDindividuTmp:
                cadre = self.dictCadres[IDindividuTmp]["ctrl"]
                if cadre.selectionCadre == True:
                    cadre.Selectionne(False)

    def DezoomTout(self, ExcepteIDindividu=None):
        """ Désélectionne tous les cadres du dc """
        for IDindividuTmp, valeurs in self.dictCadres.items():
            if ExcepteIDindividu != IDindividuTmp:
                cadre = self.dictCadres[IDindividuTmp]["ctrl"]
                if cadre != None and cadre.zoom != 1:
                    cadre.ZoomArriere(vitesse=0.1)

    def OnLeftDown(self, event):
        """ Sélection d'un cadre """
        x, y = event.GetPosition()
        IDindividu = self.RechercheCadre(x, y)
        #self.ActiveTooltip(False)
        if IDindividu != None:
            cadre = self.dictCadres[IDindividu]["ctrl"]
            # Si le calendrier est pointé, on l'ouvre
            if cadre.survolCalendrier == True:
                self.OuvrirCalendrier(IDindividu)
            else:
                # Sélectionne le cadre pointé
                self.DeselectionneTout(ExcepteIDindividu=IDindividu)
                if cadre.selectionCadre == False:
                    cadre.Selectionne(True)
                    self.selectionCadre = IDindividu
                else:
                    cadre.Selectionne(False)
                    self.selectionCadre = None
        else:
            # On désélectionne tout si on clique à côté
            self.selectionCadre = None
            self.DeselectionneTout()

    def OnDLeftDown(self, event):
        """ Un double-clic ouvre la fiche pointée """
        x, y = event.GetPosition()
        IDindividu = self.RechercheCadre(x, y)
        #self.ActiveTooltip(False)
        if IDindividu != None:
            self.Modifier(IDindividu)

    def OnMotion(self, event):
        x, y = event.GetPosition()
        IDindividu = self.RechercheCadre(x, y)
        if IDindividu != None:
            cadre = self.dictCadres[IDindividu]["ctrl"]
            # On met le tooltip
            #self.ActiveTooltip(actif=True, IDindividu=IDindividu)

            # Modification de la taille du cadre
            if self.zoomActif == True:
                self.DezoomTout(ExcepteIDindividu=IDindividu)
                cadre.ZoomAvant(coef=1.1, vitesse=0.5)
                # Recherche si l'image calendrier est survolée
                if cadre.calendrierActif == True:
                    survolCalendrier = cadre.SurvolCalendrier(x, y)
                    if survolCalendrier == True:
                        cadre.ActiveCalendrier(True)
                        self.SetCursor(wx.Cursor(wx.CURSOR_MAGNIFIER))
                    else:
                        cadre.ActiveCalendrier(False)
                        # Change le curseur de la souris
                        self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
                else:
                    # Change le curseur de la souris
                    self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        else:
            # Désactivation du toolTip
            #self.ActiveTooltip(actif=False)

            # Change le curseur de la souris
            self.SetCursor(wx.Cursor(wx.CURSOR_DEFAULT))
            # Dézoom tous les cadres
            self.DezoomTout()

    def OnLeaveWindow(self, event):
        """ Rétablit le zoom normal pour tous les cadres si le focus quitte la fenêtre """
        self.SetCursor(wx.Cursor(wx.CURSOR_DEFAULT))
        self.DezoomTout()
        #self.ActiveTooltip(False)

    def Calendrier_selection(self):
        IDindividu = self.selectionCadre

        if IDindividu == None:
            dlg = wx.MessageDialog(self,
                                   _("Vous devez d'abord sélectionner un individu dans le cadre Composition !"),
                                   _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        if self.getVal.dictIndividus[IDindividu]["inscriptions"] == False:
            dlg = wx.MessageDialog(self,
                                   _("L'individu sélectionné n'est inscrit à aucune activité !"),
                                   _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        self.OuvrirCalendrier(IDindividu)

    def OnContextMenu(self, event):
        x, y = event.GetPosition()
        #self.ActiveTooltip(False)

        # Recherche si un cadre est survolé
        IDindividu = self.RechercheCadre(x, y)
        self.IDindividu_menu = IDindividu

        # Désélectionne tous les cadres déjà sélectionnés
        self.DeselectionneTout()

        # Création du menu
        self.CreateMenu(self)


class CTRL_Liste(HTL.HyperTreeList, GestCompo):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.TR_HIDE_ROOT | wx.TR_HAS_BUTTONS | wx.TR_HAS_VARIABLE_ROW_HEIGHT,
                 IDfamille=None,
                 ):
        HTL.HyperTreeList.__init__(self, parent, id, pos, size, style,name='liste')
        GestCompo.__init__(self, parent, IDfamille)
        self.parent = parent
        self.IDfamille = IDfamille

        # Création de l'ImageList (Récupère les images attribuées aux civilités)
        il = wx.ImageList(16, 16)
        index = 0
        self.dictImages = {}
        for categorie, civilites in Civilites.LISTE_CIVILITES:
            for IDcivilite, label, abrege, img, sexe in civilites:
                setattr(self, "img%d" % index, il.Add(
                    wx.Bitmap(Chemins.GetStaticPath('Images/16x16/%s') % img,
                              wx.BITMAP_TYPE_PNG)))
                self.dictImages[IDcivilite] = getattr(self, "img%d" % index)
                index += 1
        self.dictImages[100] = il.Add(
            wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Titulaire.png"),
                      wx.BITMAP_TYPE_PNG))
        self.AssignImageList(il)

        # Creation des colonnes
        self.AddColumn(_("Individu"))
        self.SetColumnWidth(0, 260)

        self.AddColumn("", flag=wx.ALIGN_CENTRE, image=self.dictImages[100])
        self.SetColumnWidth(1, 20)

        self.AddColumn(_("Date de naissance"))
        self.SetColumnWidth(2, 155)

        self.AddColumn(_("Adresse"))
        self.SetColumnWidth(3, 200)

        self.AddColumn(_("Téléphones"))
        self.SetColumnWidth(4, 180)

        # Création des branches
        self.SetMainColumn(0)
        self.root = self.AddRoot(_("Composition"))

        self.SetSpacing(10)

        self.SetBackgroundColour(wx.WHITE)
        TR_COLUMN_LINES = HTL.TR_COLUMN_LINES
        self.SetAGWWindowStyleFlag(
            wx.TR_HIDE_ROOT | wx.TR_HAS_BUTTONS | wx.TR_FULL_ROW_HIGHLIGHT | wx.TR_HAS_VARIABLE_ROW_HEIGHT | TR_COLUMN_LINES | wx.TR_ROW_LINES)  # HTL.TR_NO_HEADER
        self.EnableSelectionVista(True)

        # Binds
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.Modifier)
        self.GetMainWindow().Bind(wx.EVT_RIGHT_UP, self.OnContextMenu)
        self.GetMainWindow().Bind(wx.EVT_MOTION, self.OnMotion)
        self.GetMainWindow().Bind(wx.EVT_LEAVE_WINDOW, self.OnLeaveWindow)

    def MAJ(self):
        self.MAJ_common()

        """ Met à jour (redessine) tout le contrôle """
        nbreBranches = self.GetChildrenCount(self.root)
        if nbreBranches > 1:
            self.DeleteChildren(self.root)
        self.CreationBranches()

    def CreationBranches(self):
        """ Création des branches """
        dictCategories = {1: [], 2: [], 3: []}
        for IDindividu, dictIndividu in self.getVal.dictIndividus.items():
            dictCategories[dictIndividu["categorie"]].append((IDindividu, dictIndividu))

        # Création des branche CATEGORIES
        for IDcategorie in (1, 2, 3):
            label = ""
            if IDcategorie == 1: label = _("Représentants")
            if IDcategorie == 2: label = _("Enfants")
            if IDcategorie == 3: label = _("Contacts")
            brancheCategorie = self.AppendItem(self.root, label)
            self.SetPyData(brancheCategorie,
                           {"type": "categorie", "IDcategorie": IDcategorie})
            self.SetItemBold(brancheCategorie, True)
            self.SetItemBackgroundColour(brancheCategorie, wx.Colour(227, 227, 227))

            # Création des branche INDIVIDUS
            for IDindividu, dictIndividu in dictCategories[IDcategorie]:

                nom = dictIndividu["nom"]
                prenom = dictIndividu["prenom"]
                IDcivilite = dictIndividu["IDcivilite"]
                categorieCivilite = Civilites.GetDictCivilites()[IDcivilite]["categorie"]
                if categorieCivilite == "ENFANT":
                    type = "E"
                else:
                    type = "A"
                sexe = Civilites.GetDictCivilites()[IDcivilite]["sexe"]

                brancheIndividu = self.AppendItem(brancheCategorie,
                                                  u"%s %s" % (nom, prenom))
                self.SetPyData(brancheIndividu,
                               {"type": "individu", "IDindividu": IDindividu})
                ##                if Civilites.GetDictCivilites()[dictIndividu["IDcivilite"]]["sexe"] == "M" :
                ##                    self.SetItemBackgroundColour(brancheIndividu, wx.Colour(217, 212, 251))
                ##                else :
                ##                    self.SetItemBackgroundColour(brancheIndividu, wx.Colour(251, 212, 239))

                # Images de l'individu
                self.SetItemImage(brancheIndividu, self.dictImages[IDcivilite],
                                  which=wx.TreeItemIcon_Normal)
                self.SetItemImage(brancheIndividu, self.dictImages[IDcivilite],
                                  which=wx.TreeItemIcon_Expanded)

                # Titulaire
                if dictIndividu["titulaire"] == 1:
                    self.SetItemText(brancheIndividu, "T", 1)

                # Date de naissance
                texte = self.getVal.GetTxtDateNaiss(self.getVal.dictIndividus,
                                                     IDindividu)
                if _("inconnue") in texte: texte = ""
                self.SetItemText(brancheIndividu, texte, 2)

                # Adresse
                ligne1 = dictIndividu["adresse_ligne1"]
                ligne2 = dictIndividu["adresse_ligne2"]
                self.SetItemText(brancheIndividu, "%s\n%s" % (ligne1, ligne2), 3)

                # Téléphones
                lstTelephones = []
                if dictIndividu["tel_domicile_complet"] != None: lstTelephones.append(
                    dictIndividu["tel_domicile_complet"])
                if dictIndividu["tel_mobile_complet"] != None: lstTelephones.append(
                    dictIndividu["tel_mobile_complet"])
                if dictIndividu["travail_tel_complet"] != None: lstTelephones.append(
                    dictIndividu["travail_tel_complet"])
                self.SetItemText(brancheIndividu, "\n".join(lstTelephones), 4)

            self.Expand(brancheCategorie)

    def GetSelectionIndividu(self, event):
        pt = event.GetPosition()
        item = self.HitTest(pt)[0]
        if item:
            self.SelectItem(item)
            dictItem = self.GetMainWindow().GetItemPyData(item)
            if dictItem["type"] == "individu":
                return dictItem["IDindividu"]
        self.UnselectAll()
        return None

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        IDindividu = self.GetSelectionIndividu(event)
        self.IDindividu_menu = IDindividu
        self.CreateMenu(self)

    def Calendrier_selection(self):
        self.OuvrirCalendrier()

    def Changer_categorie(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_fiche",
                                                                  "modifier") == False: return
        item = self.GetSelection()
        dictItem = self.GetMainWindow().GetItemPyData(item)
        type = dictItem["type"]
        if type != "individu":
            return
        IDindividu = dictItem["IDindividu"]

        IDcategorie = event.GetId() - 600
        IDrattachement = self.getVal.dictIndividus[IDindividu]["IDrattachement"]
        if IDcategorie != self.getVal.dictIndividus[IDindividu]["categorie"]:
            dlg = wx.MessageDialog(None,
                                   _("Souhaitez-vous vraiment modifier la catégorie de rattachement de cet individu ?"),
                                   _("Changement de catégorie"),
                                   wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_QUESTION)
            if dlg.ShowModal() == wx.ID_YES:
                DB = GestionDB.DB()
                DB.ReqMAJ("rattachements", [("IDcategorie", IDcategorie), ],
                          "IDrattachement", IDrattachement)
                DB.Close()
                self.MAJ()
                self.MAJnotebook()
            dlg.Destroy()

    def OnSetTitulaire(self, event):
        item = self.GetSelection()
        dictItem = self.GetMainWindow().GetItemPyData(item)
        type = dictItem["type"]
        if type != "individu":
            return
        IDindividu = dictItem["IDindividu"]

        if self.getVal.dictIndividus[IDindividu]["titulaire"] == 1:
            # Recherche s'il restera au moins un titulaire dans cette famille
            nbreTitulaires = 0
            for IDindividu, dictIndividu in self.getVal.dictIndividus.items():
                if dictIndividu["titulaire"] == 1:
                    nbreTitulaires += 1
            if nbreTitulaires == 1:
                dlg = wx.MessageDialog(self,
                                       _("Vous devez avoir un titulaire de dossier dans une famille !"),
                                       _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return
            etat = 0
        else:
            etat = 1
        DB = GestionDB.DB()
        req = "UPDATE rattachements SET titulaire=%d WHERE IDindividu=%d AND IDfamille=%d;" % (
        etat, IDindividu, self.IDfamille)
        DB.ExecuterReq(req, MsgBox="ExecuterReq")
        DB.Commit()
        DB.Close()
        self.MAJ()

    def OnMotion(self, event):
        item = self.HitTest(event.GetPosition())[0]
        IDindividu = None
        if item:
            dictItem = self.GetMainWindow().GetItemPyData(item)
            if dictItem["type"] == "individu":
                IDindividu = dictItem["IDindividu"]

        if IDindividu != None:
            # On met le tooltip
            self.ActiveTooltip(actif=True, IDindividu=IDindividu)
        else:
            # Désactivation du toolTip
            self.ActiveTooltip(actif=False)

        event.Skip()

    def OnLeaveWindow(self, event):
        self.ActiveTooltip(False)

# -------- Aiguillage vers les deux classes d'affichage ----------------------------------

class Notebook(wx.Notebook):
    def __init__(self, parent, IDfamille=None):
        if "linux" in sys.platform:
            style = wx.NB_BOTTOM
        else:
            style = wx.BK_LEFT
        wx.Notebook.__init__(self, parent, id=-1, style=style)
        self.parent = parent
        self.dlgFamille = parent
        self.IDfamille = IDfamille
        self.dictPages = {}

        listePages = [
            (_("graphique"), _("  Graphique  "),
             "CTRL_Graphique(self, IDfamille=IDfamille)", None),
            (_("liste"), _("  Liste  "), "CTRL_Liste(self, IDfamille=IDfamille)", None),
            ##            (_("liens"), _("  Liens  "), "DLG_Individu_liens.Notebook(self, IDfamille=IDfamille)", None),
        ]

        # ImageList pour le NoteBook
        il = wx.ImageList(16, 16)
        index = 0
        for codePage, labelPage, ctrlPage, imgPage in listePages:
            if imgPage != None:
                setattr(self, "img%d" % index, il.Add(
                    wx.Bitmap(Chemins.GetStaticPath('Images/16x16/%s') % imgPage,
                              wx.BITMAP_TYPE_PNG)))
                index += 1
        self.AssignImageList(il)

        # Création des pages
        index = 0
        for codePage, labelPage, ctrlPage, imgPage in listePages:
            setattr(self, "page%s" % index, eval(ctrlPage))
            self.AddPage(getattr(self, "page%s" % index), labelPage)
            if imgPage != None:
                self.SetPageImage(index, getattr(self, "img%d" % index))
            self.dictPages[codePage] = {'ctrl': getattr(self, "page%d" % index),
                                        'index': index}
            index += 1

        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)



    def GetPageAvecCode(self, codePage=""):
        return self.dictPages[codePage]["ctrl"]

    def GetCodePage(self):
        index = self.GetSelection()
        return self.listePages[index][0]

    def AffichePage(self, codePage=""):
        indexPage = self.dictPages[codePage]["index"]
        self.SetSelection(indexPage)

    def OnPageChanged(self, event):
        """ Quand une page du notebook est sélectionnée """
        indexPage = event.GetSelection()
        page = self.GetPage(indexPage)
        page.MAJ()
        event.Skip()

    # -------- relais pour le parent DLG --------------------------------------------

    def Sauvegarde(self):
        self.parent.Sauvegarde()

    def MAJpageActive(self):
        if hasattr(self.parent,'MAJpageActive'):
            self.parent.MAJpageActive()

    def MAJpage(self, codePage=""):
        self.parent.MAJpage(codePage)

    def SupprimerFicheFamille(self):
        self.parent.SupprimerFicheFamille()

    # -------- relais pour le ctrl composition affiché (graphique ou liste) ---------

    def Ajouter(self, event=None):
        page = self.GetPage(self.GetSelection())
        IDindividu = page.Ajouter(None)
        return IDindividu

    def Ajouter_individu(self, dictRattach):
        # relai vers GestionComposition
        self.dictRattach = dictRattach
        page = self.GetPage(self.GetSelection())
        IDindividu = page.Ajouter_individu(dictRattach)
        dictRattach['IDindividu'] = IDindividu
        return IDindividu

    def Modifier_selection(self, event=None):
        page = self.GetPage(self.GetSelection())
        page.Modifier_selection()

    def Modifier_individu(self, IDindividu=None):
        page = self.GetPage(self.GetSelection())
        page.Modifier(IDindividu)

    def Supprimer_selection(self, event=None):
        page = self.GetPage(self.GetSelection())
        page.Supprimer_selection()

    def Calendrier_selection(self, event=None):
        page = self.GetPage(self.GetSelection())
        page.Calendrier_selection()

    def MAJ(self, event=None):
        page = self.GetPage(self.GetSelection())
        page.MAJ()

    def DelToolTip(self,child):
        # Detruit le suraffichage sur les cadres individus
        child.tip.DoHideNow()
        #destroy the SuperToolTip.
        print("delChild")


# ---------- Pour Test -------------------------------------------------------------------

class MyFrameTest(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel_test = wx.Panel(self, -1, name='panel_test')

        self.myOlv = Notebook(panel_test, IDfamille=8578)
        self.myOlv.MAJ()
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.myOlv, 1, wx.ALL | wx.EXPAND, 4)
        panel_test.SetSizer(sizer_2)

        self.Layout()
        self.CentreOnScreen()
        def sauvegarde():
            return print("Lancé: MyFrameTest.Sauvegarde() : return None en test")
        panel_test.Sauvegarde = sauvegarde

if __name__ == '__main__':
    app = wx.App(0)
    import time

    heure_debut = time.time()
    # wx.InitAllImageHandlers()
    frame_1 = MyFrameTest(None, -1, "Olv", size=(900, 400))
    app.SetTopWindow(frame_1)
    print("Temps de chargement CTRL_Composition =", time.time() - heure_debut)
    frame_1.Show()
    app.MainLoop()
#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _

import wx
from Ctrl import CTRL_Bouton_image
import datetime


from Utils import UTILS_Interface
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils



LISTE_DONNEES = [
    (_("Pr�sence"), "Ok5", 1),
    (_("Absence justifi�e"), "absentj", 2),
    (_("Absence injustifi�e"), "absenti", 3),
    (_("Sans prestation"), "Gratuit", 5),
    (_("R�servation"), "Reservation", 6),
    (_("Attente"), "Attente2", 7),
    (_("Refus"), "Refus", 8),
    (_("Places disponibles"), "Disponible", 9),
    (_("Seuil d'alerte"), "Seuil_alerte", 10),
    (_("Complet"), "Complet", 11),
    (_("Forfait cr�dit"), "Forfait_credit", 11),
    ]



class Track(object):
    def __init__(self, donnees):
        self.label = donnees[0]
        self.nomImage = donnees[1]
        self.ordre = donnees[2]

    
class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        # Initialisation du listCtrl
        self.nom_fichier_liste = __file__
        FastObjectListView.__init__(self, *args, **kwds)
        self.InitModel()
        self.InitObjectListView()
        self.SetToolTip(wx.ToolTip(_("Retrouvez ici la liste des codes couleurs et ic�nes utilis�s dans la grille des consommations")))
                        
    def InitModel(self):
        self.donnees = self.GetTracks()
            
    def GetTracks(self):
        """ R�cup�ration des donn�es """
        listeListeView = []
        for donnees in LISTE_DONNEES :
            track = Track(donnees)
            listeListeView.append(track)
            
        return listeListeView
      
    def InitObjectListView(self):
        # Cr�ation du imageList
        indexTmp = 0
        for label, nomImage, ordre in LISTE_DONNEES :
            self.AddNamedImages(nomImage, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/%s.png" % nomImage), wx.BITMAP_TYPE_PNG))
        
        def GetImage(track):
            return track.nomImage
        
        # Couleur en alternance des lignes
        self.oddRowsBackColor = wx.Colour(255, 255, 255)
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
                
        liste_Colonnes = [
##            ColumnDefn(u"", "left", 0, "ordre"),
            ColumnDefn(_("Label"), 'left', 160, "label", imageGetter=GetImage, isSpaceFilling=True),
##            ColumnDefn(_("Ordre"), 'left', 0, "ordre"),
            ]
        
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_("Aucune l�gende"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, False, "Tekton"))
##        self.SetSortColumn(self.columns[0])
        self.SetObjects(self.donnees)
       

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.myOlv = ListView(panel, id=-1, name="OL_test", style=wx.LC_REPORT|wx.LC_NO_HEADER | wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.myOlv, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, _("OL l�gende grille des consommations"))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()


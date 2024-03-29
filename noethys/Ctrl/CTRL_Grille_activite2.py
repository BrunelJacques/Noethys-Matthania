#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

from Utils.UTILS_Traduction import _
import wx
from wx.lib.agw import ultimatelistctrl as ULC

LARGEUR_COLONNE_ACTIVITE = 190
LARGEUR_COLONNE_GROUPE = 120

class Choice_groupe(wx.Choice):
    def __init__(self, parent, IDactivite=None, IDindividu=None, listeGroupes=[], IDdefaut=None):
        """ typeIndividu = "A" ou "E" (adulte ou enfant) """
        """ sexeIndividu = "M" ou "F" (masculin ou f�minin) """
        """ Lien = ID type lien par d�faut """
        wx.Choice.__init__(self, parent, id=-1, size=(LARGEUR_COLONNE_GROUPE-2, -1)) 
        self.parent = parent

        # Adapte taille Police pour Linux
        from Utils import UTILS_Linux
        UTILS_Linux.AdaptePolice(self)

        self.IDactivite = IDactivite
        self.IDindividu = IDindividu
        self.listeGroupes = listeGroupes
        self.IDdefaut = IDdefaut
        self.MAJ()
        self.Bind(wx.EVT_CHOICE, self.OnChoice)
        self.SetToolTip(wx.ToolTip(
u"""Le groupe par d�faut est signal� par une *.\n 
Vous pouvez s�lectionner ponctuellement 
un autre groupe dans la liste. Le groupe par 
d�faut n'en sera pas pour autant modifi�."""))
        
    def MAJ(self):
        index = 0
        for ordreGroupe, nomGroupe, IDgroupe in self.listeGroupes :
            if self.IDdefaut == IDgroupe :
                self.Append(nomGroupe + "*", IDgroupe)
                self.SetSelection(index)
            else:
                self.Append(nomGroupe, IDgroupe)
            index += 1
                            
    def OnChoice(self, event):
        """ Met � jour la grille """
        if hasattr(self.parent.GetGrandParent(),'panel_grille'):
            self.parent.GetGrandParent().panel_grille.grille.MAJ()
        else: wx.MessageBox("Mise � jour non faite","info")
    def GetIDgroupe(self):
        if self.GetSelection() == -1 :
            return None
        else:
            return self.listeGroupes[self.GetSelection()][2]
    
    def SetIDgroupe(self, IDgroupe=None):
        index = 0
        for ordreGroupe, nomGroupe, IDgroupeTemp in self.listeGroupes :
            if IDgroupeTemp == IDgroupe :
                self.SetSelection(index)
                return
            index += 1

class CTRL_Activites(ULC.UltimateListCtrl):
    def __init__(self, parent, dictIndividus={}, dictActivites={}, dictGroupes={}, listeSelectionIndividus=[]):
        ULC.UltimateListCtrl.__init__(self, parent, -1, agwStyle=wx.LC_REPORT|wx.LC_VRULES|wx.LC_HRULES| ULC.ULC_HAS_VARIABLE_ROW_HEIGHT)
        self.parent = parent

        # Adapte taille Police pour Linux
        from Utils import UTILS_Linux
        UTILS_Linux.AdaptePolice(self)

        self.dictIndividus = dictIndividus
        self.dictActivites = dictActivites 
        self.dictGroupes = dictGroupes
        self.listeSelectionIndividus = listeSelectionIndividus
        self.listeActivites = []
        self.dictControles = {}
        self.dictInscriptions = {}
        # Binds
        self.Bind(ULC.EVT_LIST_ITEM_CHECKED, self.OnCheck)
        # Commandes
        self.MAJ()
        
    def MAJ(self):
        self.ClearAll()
        self.listeActivites = self.Importation()
        self.Remplissage()
        self.MAJaffichage() 
##        self.CocheTout()
        
    def SetListeSelectionIndividus(self, listeSelectionIndividus):
        self.listeSelectionIndividus = listeSelectionIndividus
        self.MAJ() 
        try :
            listeSelections = self.GetIDcoches()
            self.GetGrandParent().SetListeSelectionActivites(listeSelections)
        except :
            print("Erreur dans le SetListeSelectionIndividus du ultimatelistctrl.")
    
    def Importation(self):
        # R�cup�ration des activit�s
        listeActivites = []
        for IDindividu, dictIndividu in self.dictIndividus.items() :
            if IDindividu in self.listeSelectionIndividus :
                listeInscriptions = dictIndividu["inscriptions"]
                for dictInscription in listeInscriptions :
                    IDactivite = dictInscription["IDactivite"]
                    nomActivite = self.dictActivites[IDactivite]["nom"]
                    if (nomActivite, IDactivite) not in listeActivites :
                        listeActivites.append((nomActivite, IDactivite))
        listeActivites.sort(key=lambda item: item[1],reverse=True)
        return listeActivites

    def Remplissage(self):
        listeNomsIndividus = self.GetListeIndividus() 
        self.dictInscriptions = self.GetDictInscriptions()
        
        # Cr�ation des colonnes
        self.InsertColumn(0, "", width=LARGEUR_COLONNE_ACTIVITE)
        indexCol = 1
        for nomIndividu, IDindividu in listeNomsIndividus :
            if nomIndividu == '' and IDindividu:
                nomIndividu = "Individu: %d"%IDindividu
            self.InsertColumn(indexCol, nomIndividu, width=LARGEUR_COLONNE_GROUPE, format=ULC.ULC_FORMAT_RIGHT)
            indexCol +=1
        
        # Format : (nomItem, date_debut, date_fin)
        listeItems = []
        index = 0
        for nom, IDactivite in self.listeActivites :
            # Ecrit le nom de l'activit�
            self.InsertStringItem(index, nom, it_kind=1)
            self.SetItemPyData(index, IDactivite)
            # Ecrit le wx.Choice pour chaque individu
            indexCol = 1
            for nomIndividu, IDindividu in listeNomsIndividus :
                listeGroupes = self.GetListeGroupes(IDactivite)
                if IDindividu in self.dictInscriptions[IDactivite] :
                    if len(listeGroupes) > 0 :
                        IDdefaut = self.GetGroupeDefautIndividu(IDactivite, IDindividu)
                        item = self.GetItem(index, indexCol)
                        choice = Choice_groupe(self, IDactivite, IDindividu, listeGroupes, IDdefaut)
                        self.dictControles[(IDactivite, IDindividu)] = choice
                        item.SetWindow(choice)
                        self.SetItem(item)
                    else:
                        self.SetStringItem(index, indexCol, label=_("Groupe unique"))
                else:
                    # Si pas d'inscription pour cette activite : Coloration de la case en gris
                    self.SetStringItem(index, indexCol, label=u"")
                    item = self.GetItem(index, indexCol)
                    item.SetMask(ULC.ULC_MASK_BACKCOLOUR)
                    item.SetBackgroundColour(wx.Colour(220, 220, 220))
                    self.SetItem(item)
                    
                indexCol += 1
            index += 1

    def MAJaffichage(self):
        # Correction du bug d'affichage du ultimatelistctrl
        self.Layout() 
        self._mainWin.RecalculatePositions()
    
    def GetIDgroupe(self, IDactivite=None, IDindividu=None):
        """ Permet de r�cup�rer l'IDgroupe de l'individu � partir de la grille """
        if (IDactivite, IDindividu) in self.dictControles :
            controle = self.dictControles[(IDactivite, IDindividu)]
            return controle.GetIDgroupe() 
        else:
            return None
    
    def GetListeGroupes(self, IDactivite=None):
        listeGroupes = []
        for IDgroupe, dictGroupe in self.dictGroupes.items():
            if dictGroupe["IDactivite"] == IDactivite :
                listeGroupes.append( (dictGroupe["ordre"], dictGroupe["nom"], IDgroupe) )
        listeGroupes.sort() 
        return listeGroupes
    
    def GetListeIndividus(self):
        listeNomsIndividus = []
        for IDindividu, dictInfos in self.dictIndividus.items() :
            if IDindividu in self.listeSelectionIndividus :
                if len(dictInfos["inscriptions"]) > 0  :
                    nomIndividu = dictInfos["prenom"]
                    listeNomsIndividus.append( (nomIndividu, IDindividu) )
        listeNomsIndividus.sort()
        return listeNomsIndividus
    
    def GetDictInscriptions(self):
        dictInscriptions = {}
        for IDindividu, dictInfos in self.dictIndividus.items() :
            listeInscriptions = dictInfos["inscriptions"]
            for dictInscription in listeInscriptions :
                IDactivite = dictInscription["IDactivite"]
                if (IDactivite in dictInscriptions) == False :
                    dictInscriptions[IDactivite] = []
                dictInscriptions[IDactivite].append(IDindividu)
        return dictInscriptions

    def GetGroupeDefautIndividu(self, IDactivite, IDindividu):
        for dictInscriptions in self.dictIndividus[IDindividu]["inscriptions"] :
            if dictInscriptions["IDactivite"] == IDactivite :
                return dictInscriptions["IDgroupe"]
        return None

    def OnCheck(self, event=None):
        """ Quand une s�lection d'activit�s est effectu�e... """
        listeSelections = self.GetIDcoches()
        try :
            self.GetGrandParent().SetListeSelectionActivites(listeSelections)
            self.GetGrandParent().MAJ_grille(autoCocheActivites=False)
        except :
            print("Erreur dans le Check du ultimatelistctrl.", listeSelections)
        # D�selectionne l'item apr�s la coche
        if event != None :
            itemIndex = event.m_itemIndex
            self.Select(itemIndex, False)

    def CocheTout(self):
        for index in range(0, len(self.listeActivites)):
            item = self.GetItem(index, 0)
            item.Check(True)
            self.SetItem(item)

    def GetIDcoches(self):
        listeIDcoches = []
        for index in range(0, len(self.listeActivites)):
            item = self.GetItem(index, 0)
            if item.IsChecked() :
                listeIDcoches.append(self.listeActivites[index][1])
        return listeIDcoches

    def SetIDcoches(self, listeIDcoches=[]):
        for index in range(0, len(self.listeActivites)):
            item = self.GetItem(index, 0)
            ID = self.listeActivites[index][1]
            if ID in listeIDcoches :
                item.Check(True)
    
    def CocheActivitesOuvertes(self, date_min=None, date_max=None):
        """ Coche uniquement les activit�s ouvertes """
        listeIDactivites = []
        for index in range(0, len(self.listeActivites)):
            item = self.GetItem(index, 0)
            IDactivite = self.listeActivites[index][1]
            date_debut_activite = self.dictActivites[IDactivite]["date_debut"]
            date_fin_activite = self.dictActivites[IDactivite]["date_fin"]
            if date_debut_activite <= date_max and date_fin_activite >= date_min :
                item.Check(True)
                listeIDactivites.append(IDactivite)
            else :
                item.Check(False)
            self.SetItem(item)
        return listeIDactivites

class CTRL(wx.Panel):
    def __init__(self, parent, dictIndividus={}, dictActivites={}, dictGroupes={}, listeSelectionIndividus=[]):
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent

        
        self.ctrl_activites = CTRL_Activites(self, dictIndividus, dictActivites, dictGroupes, listeSelectionIndividus)

        grid_sizer_base = wx.FlexGridSizer(rows=2, cols=1, vgap=0, hgap=0)
        grid_sizer_base.Add(self.ctrl_activites, 0, wx.EXPAND, 0)
        grid_sizer_base.AddGrowableRow(0)
        grid_sizer_base.AddGrowableCol(0)
        self.SetSizerAndFit(grid_sizer_base)
        self.Layout()


# --------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.ctrl= CTRL(panel, **kwds)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()

if __name__ == '__main__':
    app = wx.App(0)
    import datetime
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1,
                      dictIndividus= {18912: {'IDcivilite': 90, 'civiliteAbrege': '', 'nom': 'AFNOM',
                                              'prenom': 'Secr�taire g�n�ral', 'date_naiss': None,
                                              'age': None, 'IDcategorie': 1, 'titulaire': 1,
                                              'inscriptions': [{'IDinscription': 21362, 'IDactivite': 678, 'IDgroupe': 1866,'IDcategorie_tarif': 1513, 'nomCategorie_tarif': 'Tarif PENSION COMPLETE'},
                                                               {'IDinscription': 23660, 'IDactivite': 736, 'IDgroupe': 2248,'IDcategorie_tarif': 1635,'nomCategorie_tarif': 'Tarif PENSION COMPLETE'},
                                                              ]
                                              },
                                      20644: {'IDcivilite': 90, 'civiliteAbrege': '', 'nom': 'ALSACE LORRAINE',
                                              'prenom': '-', 'date_naiss': None, 'age': None, 'IDcategorie': 1,
                                              'titulaire': 1,
                                              'inscriptions': [{'IDinscription': 21362, 'IDactivite': 678, 'IDgroupe': 1866, 'IDcategorie_tarif': 1513, 'nomCategorie_tarif': 'Tarif PENSION COMPLETE'},
                                                               {'IDinscription': 21766, 'IDactivite': 681, 'IDgroupe': 1878, 'IDcategorie_tarif': 1519, 'nomCategorie_tarif': 'Tarif PENSION COMPLETE'},
                                                               {'IDinscription': 21768, 'IDactivite': 682, 'IDgroupe': 1882, 'IDcategorie_tarif': 1521, 'nomCategorie_tarif': 'Tarif PENSION COMPLETE'},
                                                               {'IDinscription': 23261, 'IDactivite': 732, 'IDgroupe': 2246, 'IDcategorie_tarif': 1627, 'nomCategorie_tarif': 'Tarif PENSION COMPLETE'},
                                                               {'IDinscription': 23659, 'IDactivite': 735, 'IDgroupe': 2247, 'IDcategorie_tarif': 1633, 'nomCategorie_tarif': 'Tarif PENSION COMPLETE'},
                                                               {'IDinscription': 23660, 'IDactivite': 736, 'IDgroupe': 2248, 'IDcategorie_tarif': 1635, 'nomCategorie_tarif': 'Tarif PENSION COMPLETE'},
                                                               ]
                                              },
                                      },
                      dictActivites = {
                            678: {'nom': '11 CampPasto S1 - 2023', 'abrege': '20230711', 'date_debut': datetime.date(2023, 7, 9), 'date_fin': datetime.date(2023, 7, 22), 'tarifs': {}},
                            681: {'nom': '12 CampPasto S2 - 2023', 'abrege': '20230712', 'date_debut': datetime.date(2023, 7, 23), 'date_fin': datetime.date(2023, 8, 5), 'tarifs': {}},
                            682: {'nom': '12 CampPasto S2 - 2023', 'abrege': '20230712', 'date_debut': datetime.date(2023, 7, 23), 'date_fin': datetime.date(2023, 8, 5), 'tarifs': {}},
                            732: {'nom': '14 CampPasto S3 - 2023', 'abrege': '20230814', 'date_debut': datetime.date(2023, 8, 6), 'date_fin': datetime.date(2023, 8, 19), 'tarifs': {}},
                            735: {'nom': '191 PRE-CAMP S1 - 2023', 'abrege': '202307191', 'date_debut': datetime.date(2023, 7, 5), 'date_fin': datetime.date(2023, 7, 8), 'tarifs': {}},
                            736: {'nom': '192 PRE-CAMP S2 - 2023', 'abrege': '202307192', 'date_debut': datetime.date(2023, 7, 20), 'date_fin': datetime.date(2023, 7, 22), 'tarifs': {}},
                      },

                      dictGroupes= {2023:{'IDactivite': 788, 'nom': 'NOM groupe activite ', 'ordre': 1, 'nbreGroupesActivite': 1},},
                      listeSelectionIndividus=[18912, 20644]
                      )

    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()



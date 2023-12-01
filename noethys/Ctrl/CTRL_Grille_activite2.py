#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image

if wx.VERSION < (2, 9, 0, 0) :
    from Outils import ultimatelistctrl as ULC
else :
    from wx.lib.agw import ultimatelistctrl as ULC

import sys

import GestionDB


LARGEUR_COLONNE_ACTIVITE = 100
LARGEUR_COLONNE_GROUPE = 180


class Choice_groupe(wx.Choice):
    def __init__(self, parent, IDactivite=None, IDindividu=None, listeGroupes=[], IDdefaut=None):
        """ typeIndividu = "A" ou "E" (adulte ou enfant) """
        """ sexeIndividu = "M" ou "F" (masculin ou féminin) """
        """ Lien = ID type lien par défaut """
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
u"""Le groupe par défaut est signalé par une *.\n 
Vous pouvez sélectionner ponctuellement 
un autre groupe dans la liste. Le groupe par 
défaut n'en sera pas pour autant modifié."""))
        
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
        """ Met à jour la grille """
        self.parent.GetGrandParent().panel_grille.grille.MAJ() 
    
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
        # Récupération des activités
        listeActivites = []
        for IDindividu, dictIndividu in self.dictIndividus.items() :
            if IDindividu in self.listeSelectionIndividus :
                listeInscriptions = dictIndividu["inscriptions"]
                for dictInscription in listeInscriptions :
                    IDactivite = dictInscription["IDactivite"]
                    nomActivite = self.dictActivites[IDactivite]["nom"]
                    if (nomActivite, IDactivite) not in listeActivites :
                        listeActivites.append((nomActivite, IDactivite))
        listeActivites.sort()
        return listeActivites

    def Remplissage(self):
        listeNomsIndividus = self.GetListeIndividus() 
        self.dictInscriptions = self.GetDictInscriptions()
        
        # Création des colonnes
        self.InsertColumn(0, "", width=LARGEUR_COLONNE_ACTIVITE)
        indexCol = 1
        for nomIndividu, IDindividu in listeNomsIndividus :
            self.InsertColumn(indexCol, nomIndividu, width=LARGEUR_COLONNE_GROUPE, format=ULC.ULC_FORMAT_RIGHT)
            indexCol +=1
        
        # Format : (nomItem, date_debut, date_fin)
        listeItems = []
        index = 0
        for nom, IDactivite in self.listeActivites :
            # Ecrit le nom de l'activité
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
        """ Permet de récupérer l'IDgroupe de l'individu à partir de la grille """
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
        """ Quand une sélection d'activités est effectuée... """
        listeSelections = self.GetIDcoches()
        try :
            self.GetGrandParent().SetListeSelectionActivites(listeSelections)
            self.GetGrandParent().MAJ_grille(autoCocheActivites=False)
        except :
            print("Erreur dans le Check du ultimatelistctrl.", listeSelections)
        # Déselectionne l'item après la coche
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
        """ Coche uniquement les activités ouvertes """
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
##        self.ctrl_mode = CTRL_Mode(self)
        
        grid_sizer_base = wx.FlexGridSizer(rows=2, cols=1, vgap=0, hgap=0)
        grid_sizer_base.Add(self.ctrl_activites, 0, wx.EXPAND, 0)
##        grid_sizer_base.Add(self.ctrl_mode, 0, wx.EXPAND|wx.ALL, 5)
        grid_sizer_base.AddGrowableRow(0)
        grid_sizer_base.AddGrowableCol(0)
        self.SetSizer(grid_sizer_base)
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
                      dictIndividus= {18913: {'IDcivilite': 90, 'civiliteAbrege': '', 'nom': 'AFOCAL', 'prenom': 'Secrétaire général', 'date_naiss': None, 'age': None, 'IDcategorie': 1, 'titulaire': 1, 'inscriptions': []}, 18912: {'IDcivilite': 90, 'civiliteAbrege': '', 'nom': 'AFOCAL ALSACE LORRAINE', 'prenom': '-', 'date_naiss': None, 'age': None, 'IDcategorie': 1, 'titulaire': 1, 'inscriptions': [{'IDinscription': 21362, 'IDactivite': 678, 'IDgroupe': 1866, 'IDcategorie_tarif': 1513, 'nomCategorie_tarif': 'Tarif PENSION COMPLETE'}, {'IDinscription': 21766, 'IDactivite': 681, 'IDgroupe': 1878, 'IDcategorie_tarif': 1519, 'nomCategorie_tarif': 'Tarif PENSION COMPLETE'}, {'IDinscription': 21768, 'IDactivite': 682, 'IDgroupe': 1882, 'IDcategorie_tarif': 1521, 'nomCategorie_tarif': 'Tarif PENSION COMPLETE'}, {'IDinscription': 23261, 'IDactivite': 732, 'IDgroupe': 2246, 'IDcategorie_tarif': 1627, 'nomCategorie_tarif': 'Tarif PENSION COMPLETE'}, {'IDinscription': 23659, 'IDactivite': 735, 'IDgroupe': 2247, 'IDcategorie_tarif': 1633, 'nomCategorie_tarif': 'Tarif PENSION COMPLETE'}, {'IDinscription': 23660, 'IDactivite': 736, 'IDgroupe': 2248, 'IDcategorie_tarif': 1635, 'nomCategorie_tarif': 'Tarif PENSION COMPLETE'}]}, 20644: {'IDcivilite': 7, 'civiliteAbrege': '', 'nom': 'AFOCAL MARSEILLE', 'prenom': '', 'date_naiss': None, 'age': None, 'IDcategorie': 1, 'titulaire': 1, 'inscriptions': [{'IDinscription': 23834, 'IDactivite': 788, 'IDgroupe': 2313, 'IDcategorie_tarif': 1761, 'nomCategorie_tarif': 'Tarif PENSION COMPLETE'}]}},
                      dictActivites = {753: {'nom': '11 CampPasto S1 - 2023', 'abrege': '20230711', 'date_debut': datetime.date(2023, 7, 9), 'date_fin': datetime.date(2023, 7, 22), 'tarifs': {}}, 754: {'nom': '12 CampPasto S2 - 2023', 'abrege': '20230712', 'date_debut': datetime.date(2023, 7, 23), 'date_fin': datetime.date(2023, 8, 5), 'tarifs': {}}, 755: {'nom': '14 CampPasto S3 - 2023', 'abrege': '20230814', 'date_debut': datetime.date(2023, 8, 6), 'date_fin': datetime.date(2023, 8, 19), 'tarifs': {}}, 756: {'nom': '191 PRE-CAMP S1 - 2023', 'abrege': '202307191', 'date_debut': datetime.date(2023, 7, 5), 'date_fin': datetime.date(2023, 7, 8), 'tarifs': {}}, 757: {'nom': '192 PRE-CAMP S2 - 2023', 'abrege': '202307192', 'date_debut': datetime.date(2023, 7, 20), 'date_fin': datetime.date(2023, 7, 22), 'tarifs': {}}, 758: {'nom': '193 PRE-CAMP S3 - 2023', 'abrege': '202308193', 'date_debut': datetime.date(2023, 8, 3), 'date_fin': datetime.date(2023, 8, 5), 'tarifs': {}}, 741: {'nom': '31 Neige&Famille S1/AB 2023', 'abrege': '20230231', 'date_debut': datetime.date(2023, 2, 11), 'date_fin': datetime.date(2023, 2, 18), 'tarifs': {}}, 782: {'nom': '31 Neige&Famille S1/C 2024', 'abrege': '20240231', 'date_debut': datetime.date(2024, 2, 11), 'date_fin': datetime.date(2024, 2, 18), 'tarifs': {}}, 781: {'nom': '32 Neige&Famille S2/AC 2024', 'abrege': '20240232', 'date_debut': datetime.date(2024, 2, 18), 'date_fin': datetime.date(2024, 2, 24), 'tarifs': {}}, 742: {'nom': '32 Neige&Famille S2/BC 2023', 'abrege': '20230232', 'date_debut': datetime.date(2023, 2, 18), 'date_fin': datetime.date(2023, 2, 25), 'tarifs': {}}, 783: {'nom': '33 Neige&Famille S3/B 2024', 'abrege': '20240233', 'date_debut': datetime.date(2024, 3, 2), 'date_fin': datetime.date(2024, 3, 9), 'tarifs': {}}, 743: {'nom': '33 Neige&Famille S3/C 2023', 'abrege': '20230233', 'date_debut': datetime.date(2023, 2, 25), 'date_fin': datetime.date(2023, 3, 4), 'tarifs': {}}, 722: {'nom': '34 WINTER THEO SKI-2022', 'abrege': '20221234', 'date_debut': datetime.date(2022, 12, 26), 'date_fin': datetime.date(2023, 1, 2), 'tarifs': {}}, 775: {'nom': '34 WINTER THEO SKI-2023', 'abrege': '20231234', 'date_debut': datetime.date(2023, 12, 30), 'date_fin': datetime.date(2024, 1, 6), 'tarifs': {}}, 760: {'nom': "35 THEO'SUD-2023", 'abrege': '20230835', 'date_debut': datetime.date(2023, 8, 20), 'date_fin': datetime.date(2023, 8, 25), 'tarifs': {}}, 761: {'nom': '37 ESCAPADE FAM -23 LE ROCHER ANNOT', 'abrege': '20230837', 'date_debut': datetime.date(2023, 8, 12), 'date_fin': datetime.date(2023, 8, 19), 'tarifs': {}}, 763: {'nom': '38 TERRE 2 MISSIONS-2023', 'abrege': '20231038', 'date_debut': datetime.date(2023, 10, 24), 'date_fin': datetime.date(2023, 11, 5), 'tarifs': {}}, 762: {'nom': '39 TERRE INCONNUE - 2023', 'abrege': '20230739', 'date_debut': datetime.date(2023, 7, 23), 'date_fin': datetime.date(2023, 8, 5), 'tarifs': {}}, 764: {'nom': '41 CORSE 1 - 2023', 'abrege': '20230741', 'date_debut': datetime.date(2023, 7, 9), 'date_fin': datetime.date(2023, 7, 22), 'tarifs': {}}, 765: {'nom': '42 CORSE 2 - 2023', 'abrege': '20230742', 'date_debut': datetime.date(2023, 7, 23), 'date_fin': datetime.date(2023, 8, 5), 'tarifs': {}}, 766: {'nom': '43 CORSE 3 - 2023', 'abrege': '20230843', 'date_debut': datetime.date(2023, 8, 6), 'date_fin': datetime.date(2023, 8, 19), 'tarifs': {}}, 767: {'nom': '45 SUD TERRE AVENTURES 1 - 2023', 'abrege': '20230745', 'date_debut': datetime.date(2023, 7, 9), 'date_fin': datetime.date(2023, 7, 22), 'tarifs': {}}, 768: {'nom': '46 SUD TERRE AVENTURES 2 - 2023', 'abrege': '20230746', 'date_debut': datetime.date(2023, 7, 23), 'date_fin': datetime.date(2023, 8, 5), 'tarifs': {}}, 769: {'nom': '47 SUD TERRE AVENTURES 3 - 2023', 'abrege': '20230847', 'date_debut': datetime.date(2023, 8, 6), 'date_fin': datetime.date(2023, 8, 19), 'tarifs': {}}, 770: {'nom': '48 IMMERSION Road Trip- 2023', 'abrege': '20230748', 'date_debut': datetime.date(2023, 7, 9), 'date_fin': datetime.date(2023, 7, 22), 'tarifs': {}}, 771: {'nom': '49 SUD EVASION 2023', 'abrege': '20230849', 'date_debut': datetime.date(2023, 8, 6), 'date_fin': datetime.date(2023, 8, 19), 'tarifs': {}}, 772: {'nom': '52 Sensations MULTISPORTS S1-23', 'abrege': '20230752', 'date_debut': datetime.date(2023, 7, 9), 'date_fin': datetime.date(2023, 7, 22), 'tarifs': {}}, 773: {'nom': '53 Sensations MULTISPORTS S2-23', 'abrege': '20230853', 'date_debut': datetime.date(2023, 7, 23), 'date_fin': datetime.date(2023, 8, 5), 'tarifs': {}}, 744: {'nom': '60 PLONGEE ACTIVITES CLUB', 'abrege': '20230060', 'date_debut': datetime.date(2022, 10, 1), 'date_fin': datetime.date(2023, 9, 30), 'tarifs': {}}, 776: {'nom': '61-WE PLONGEE jeunes 2023', 'abrege': '20230661', 'date_debut': datetime.date(2023, 6, 30), 'date_fin': datetime.date(2023, 7, 2), 'tarifs': {}}, 777: {'nom': '62-WE PLONGEE jeunes EBTM 2023', 'abrege': '20230962', 'date_debut': datetime.date(2023, 9, 8), 'date_fin': datetime.date(2023, 9, 10), 'tarifs': {}}, 774: {'nom': '63 Plongée - 2023', 'abrege': '20230863', 'date_debut': datetime.date(2023, 8, 6), 'date_fin': datetime.date(2023, 8, 19), 'tarifs': {}}, 724: {'nom': '76 SMS - 2023/76', 'abrege': '20231076', 'date_debut': datetime.date(2022, 9, 17), 'date_fin': datetime.date(2023, 6, 30), 'tarifs': {}}, 778: {'nom': '76 SMS - 2024/76', 'abrege': '20230176', 'date_debut': datetime.date(2023, 9, 4), 'date_fin': datetime.date(2024, 6, 30), 'tarifs': {}}, 725: {'nom': '77 CAP GDJ - 2023/77', 'abrege': '20231077', 'date_debut': datetime.date(2022, 9, 17), 'date_fin': datetime.date(2023, 6, 30), 'tarifs': {}}, 779: {'nom': '77 CAP GDJ - 2024/77', 'abrege': '20240177', 'date_debut': datetime.date(2023, 9, 4), 'date_fin': datetime.date(2024, 6, 30), 'tarifs': {}}, 723: {'nom': '79 Samedi Aventures - 2023/79', 'abrege': '20231079', 'date_debut': datetime.date(2022, 9, 17), 'date_fin': datetime.date(2023, 6, 30), 'tarifs': {}}, 780: {'nom': '79 Samedi Aventures - 2024/79', 'abrege': '20240179', 'date_debut': datetime.date(2023, 9, 4), 'date_fin': datetime.date(2024, 6, 30), 'tarifs': {}}, 746: {'nom': '84 FEMMES en PROV - 2023', 'abrege': '20230584', 'date_debut': datetime.date(2023, 5, 12), 'date_fin': datetime.date(2023, 5, 14), 'tarifs': {}}, 729: {'nom': '85 ACCUEIL GROUPE - 2022/12', 'abrege': '20221285', 'date_debut': datetime.date(2022, 12, 1), 'date_fin': datetime.date(2022, 12, 31), 'tarifs': {}}, 730: {'nom': '85 ACCUEIL GROUPE - 2023/02', 'abrege': '20230285', 'date_debut': datetime.date(2023, 2, 1), 'date_fin': datetime.date(2023, 2, 28), 'tarifs': {}}, 731: {'nom': '85 ACCUEIL GROUPE - 2023/03', 'abrege': '20230385', 'date_debut': datetime.date(2023, 3, 1), 'date_fin': datetime.date(2023, 3, 31), 'tarifs': {}}, 732: {'nom': '85 ACCUEIL GROUPE - 2023/04', 'abrege': '20230485', 'date_debut': datetime.date(2023, 4, 1), 'date_fin': datetime.date(2023, 4, 30), 'tarifs': {}}, 733: {'nom': '85 ACCUEIL GROUPE - 2023/05', 'abrege': '20230585', 'date_debut': datetime.date(2023, 5, 1), 'date_fin': datetime.date(2023, 5, 31), 'tarifs': {}}, 734: {'nom': '85 ACCUEIL GROUPE - 2023/06', 'abrege': '20230685', 'date_debut': datetime.date(2023, 6, 1), 'date_fin': datetime.date(2023, 6, 30), 'tarifs': {}}, 735: {'nom': '85 ACCUEIL GROUPE - 2023/07', 'abrege': '20230785', 'date_debut': datetime.date(2023, 7, 1), 'date_fin': datetime.date(2023, 7, 31), 'tarifs': {}}, 736: {'nom': '85 ACCUEIL GROUPE - 2023/08', 'abrege': '20230885', 'date_debut': datetime.date(2023, 8, 1), 'date_fin': datetime.date(2023, 8, 31), 'tarifs': {}}, 737: {'nom': '85 ACCUEIL GROUPE - 2023/09', 'abrege': '20230985', 'date_debut': datetime.date(2023, 9, 1), 'date_fin': datetime.date(2023, 10, 1), 'tarifs': {}}, 738: {'nom': '85 ACCUEIL GROUPE - 2023/10', 'abrege': '20231085', 'date_debut': datetime.date(2023, 10, 1), 'date_fin': datetime.date(2023, 11, 2), 'tarifs': {}}, 739: {'nom': '85 ACCUEIL GROUPE - 2023/11', 'abrege': '20231185', 'date_debut': datetime.date(2023, 11, 1), 'date_fin': datetime.date(2023, 11, 30), 'tarifs': {}}, 740: {'nom': '85 ACCUEIL GROUPE - 2023/12', 'abrege': '20231285', 'date_debut': datetime.date(2023, 12, 1), 'date_fin': datetime.date(2023, 12, 31), 'tarifs': {}}, 787: {'nom': '85 ACCUEIL GROUPE - 2024/01', 'abrege': '20240185', 'date_debut': datetime.date(2024, 1, 1), 'date_fin': datetime.date(2024, 1, 31), 'tarifs': {}}, 788: {'nom': '85 ACCUEIL GROUPE - 2024/02', 'abrege': '20240285', 'date_debut': datetime.date(2024, 2, 1), 'date_fin': datetime.date(2024, 2, 29), 'tarifs': {}}, 789: {'nom': '85 ACCUEIL GROUPE - 2024/03', 'abrege': '20240385', 'date_debut': datetime.date(2024, 3, 1), 'date_fin': datetime.date(2024, 3, 31), 'tarifs': {}}, 790: {'nom': '85 ACCUEIL GROUPE - 2024/04', 'abrege': '20240485', 'date_debut': datetime.date(2024, 4, 1), 'date_fin': datetime.date(2024, 4, 30), 'tarifs': {}}, 791: {'nom': '85 ACCUEIL GROUPE - 2024/05', 'abrege': '20240585', 'date_debut': datetime.date(2024, 5, 1), 'date_fin': datetime.date(2024, 5, 31), 'tarifs': {}}, 792: {'nom': '85 ACCUEIL GROUPE - 2024/06', 'abrege': '20240685', 'date_debut': datetime.date(2024, 6, 1), 'date_fin': datetime.date(2024, 6, 30), 'tarifs': {}}, 793: {'nom': '85 ACCUEIL GROUPE - 2024/07', 'abrege': '20240785', 'date_debut': datetime.date(2024, 7, 1), 'date_fin': datetime.date(2024, 7, 31), 'tarifs': {}}, 794: {'nom': '85 ACCUEIL GROUPE - 2024/08', 'abrege': '20240885', 'date_debut': datetime.date(2024, 8, 1), 'date_fin': datetime.date(2024, 8, 31), 'tarifs': {}}, 795: {'nom': '85 ACCUEIL GROUPE - 2024/09', 'abrege': '20240985', 'date_debut': datetime.date(2024, 9, 1), 'date_fin': datetime.date(2024, 9, 30), 'tarifs': {}}, 750: {'nom': '86 BAFA APPRO AFOCAL - AVRIL 2023', 'abrege': '20230486', 'date_debut': datetime.date(2023, 4, 24), 'date_fin': datetime.date(2023, 4, 29), 'tarifs': {}}, 749: {'nom': '86 BAFA APPRO AFOCAL- AOUT 2023', 'abrege': '20230886', 'date_debut': datetime.date(2023, 8, 13), 'date_fin': datetime.date(2023, 8, 18), 'tarifs': {}}, 748: {'nom': '86 BAFA BASE AFOCAL - AVRIL 2023', 'abrege': '20230486', 'date_debut': datetime.date(2023, 4, 22), 'date_fin': datetime.date(2023, 4, 29), 'tarifs': {}}, 747: {'nom': '86 BAFA BASE AFOCAL JUILLET- 2023', 'abrege': '20230786', 'date_debut': datetime.date(2023, 7, 1), 'date_fin': datetime.date(2023, 7, 8), 'tarifs': {}}, 752: {'nom': '87 BAFD Appro AFOCAL AVRIL-2023', 'abrege': '20230487', 'date_debut': datetime.date(2023, 4, 24), 'date_fin': datetime.date(2023, 4, 29), 'tarifs': {}}, 751: {'nom': '87 BAFD base AFOCAL AVRIL-2023', 'abrege': '20230487', 'date_debut': datetime.date(2023, 4, 21), 'date_fin': datetime.date(2023, 4, 29), 'tarifs': {}}},
                      dictGroupes= {2013:{'IDactivite': 788, 'nom': 'ACTIVITE FORMATION', 'ordre': 5, 'nbreGroupesActivite': 5},},
                      listeSelectionIndividus=[18913, 20644]
                      )

    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()



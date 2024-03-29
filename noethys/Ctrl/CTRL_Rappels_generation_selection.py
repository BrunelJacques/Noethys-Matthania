#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys branche Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#-----------------------------------------------------------


from Utils.UTILS_Traduction import _
import Chemins
import wx
from Ctrl import CTRL_Bouton_image
import wx.lib.agw.hypertreelist as HTL
from wx.lib.agw.customtreectrl import EVT_TREE_ITEM_CHECKED
import datetime
import copy
import sys
import traceback
import decimal
import wx.lib.agw.pybusyinfo as PBI

from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "�")
MONNAIE_SINGULIER = UTILS_Config.GetParametre("monnaie_singulier", _("Euro"))
MONNAIE_DIVISION = UTILS_Config.GetParametre("monnaie_division", _("Centime"))

import GestionDB
import FonctionsPerso
from Utils import UTILS_Impression_rappel
from Dlg import DLG_Apercu_rappel
from Utils import UTILS_Rappels
from Utils import UTILS_Dates

from Dlg.DLG_Saisie_texte_rappel import MOTSCLES


            

class CTRL_document(wx.Choice):
    def __init__(self, parent, id=-1, branche=None, IDcompte_payeur=None, nbreJoursRetard=0, infobulle="" ):
        wx.Choice.__init__(self, parent, id=id, size=(162, -1) ) 
        self.parent = parent
        self.branche = branche
        self.IDcompte_payeur = IDcompte_payeur
        self.nbreJoursRetard = nbreJoursRetard
        choices=self.GetListe()
        self.SetItems(choices)
        self.SetToolTip(infobulle)
        self.Bind(wx.EVT_CHOICE, self.OnChoice)

        self.SetValeurDefaut() 
                
    def GetListe(self):
        listeChoix = []
        self.dictChoix = {}
        liste = [ (0, "-", (255, 255, 255), (0, 0), "", ""), ]
        try :
            donnees = self.parent.GetGrandParent().ctrl_textes.donnees
            for track in donnees :
                liste.append((track.IDtexte, track.label, track.couleur, (track.retard_min, track.retard_max), track.titre, track.texte ))
        except:
            pass
        if len(liste)>1:
            del liste[0]
        index = 0
        for IDtexte, label, couleur, retardDefaut, titre, texte in liste :
            listeChoix.append(label)
            self.dictChoix[index] = { "IDtexte" : IDtexte, "label" : label, "couleur" : couleur, "retardDefaut" : retardDefaut, "titre" : titre, "texte" : texte }
            index += 1
        return listeChoix
    
    def SetValeurDefaut(self):
        for index, dictDocument in self.dictChoix.items() :
            retardMin, retardMax = dictDocument["retardDefaut"]
            if self.nbreJoursRetard >= retardMin and self.nbreJoursRetard <= retardMax :
                self.SetSelection(index)
                self.GetGrandParent().SetCouleurLigne(self.branche, dictDocument["couleur"])
                return
        self.Select(0)
            
    def OnChoice(self, event):
        dictDocument = self.GetDictDocument() 
        if dictDocument != None :
            # Attribue la couleur de fond � la ligne
            self.GetGrandParent().SetCouleurLigne(self.branche, dictDocument["couleur"])
    
    def GetDictDocument(self):
        if self.GetSelection() == -1 :
            return None
        else:
            return self.dictChoix[self.GetSelection()]
    

# ---------------------------------------------------------------------------------------------------------------------------------
            
class CTRL(HTL.HyperTreeList):
    def __init__(self, parent): 
        HTL.HyperTreeList.__init__(self, parent, -1)
        self.parent = parent
        self.dictParametres = {}
        self.dictComptes = {}
                
        # Cr�ation des colonnes
        listeColonnes = [
            ( _("Famille/Individu"), 200, wx.ALIGN_LEFT),
            ( "Du", 70, wx.ALIGN_CENTER),
            ( _("Au"), 70, wx.ALIGN_CENTER),
            ( _("Retard"), 60, wx.ALIGN_CENTRE),
            ( _("Solde"), 60, wx.ALIGN_RIGHT),
            ( _("Document"), 170, wx.ALIGN_LEFT),
            ]
        numColonne = 0
        for label, largeur, alignement in listeColonnes :
            self.AddColumn(label)
            self.SetColumnWidth(numColonne, largeur)
            self.SetColumnAlignment(numColonne, alignement)
            numColonne += 1

        self.SetBackgroundColour(wx.WHITE)
        self.SetAGWWindowStyleFlag( HTL.TR_COLUMN_LINES | wx.TR_HAS_BUTTONS |wx.TR_HIDE_ROOT  | wx.TR_HAS_VARIABLE_ROW_HEIGHT | wx.TR_FULL_ROW_HIGHLIGHT | HTL.TR_AUTO_CHECK_CHILD | HTL.TR_AUTO_CHECK_PARENT) # HTL.TR_NO_HEADER
        self.EnableSelectionVista(True)

        # Binds
        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnContextMenu) 
        self.Bind(EVT_TREE_ITEM_CHECKED, self.OnCheckItem) 

    def SetParametres(self, dictParametres={}):
        self.dictParametres = dictParametres
        self.MAJ()

    def AfficheNbreComptes(self, nbreComptes=0):
        if self.parent.GetName() == "DLG_Rappels_generation_selection" :
            if nbreComptes == 0 : label = _("Aucune lettre de rappel s�lectionn�e")
            elif nbreComptes == 1 : label = _("1 lettre de rappel s�lectionn�e")
            else: label = _("%d lettres de rappel s�lectionn�es") % nbreComptes
            self.parent.box_rappels_staticbox.SetLabel(label)
        
    def OnCheckItem(self, event):
        if self.MAJenCours == False :
            item = event.GetItem()
            if self.GetItemData(item)["type"] == "individu" :
                # R�cup�re les donn�es sur le compte payeur
                itemParent = self.GetItemParent(item)
                IDcompte_payeur = self.GetItemData(itemParent)["valeur"]
                # R�cup�re les donn�es sur l'individu
                IDindividu = self.GetItemData(item)["valeur"]
            self.AfficheNbreComptes(len(self.GetCoches()))
                
    def CocheTout(self):
        self.MAJenCours = True
        item = self.root
        for index in range(0, self.GetChildrenCount(self.root)):
            item = self.GetNext(item) 
            self.CheckItem(item, True)
        self.MAJenCours = False
        self.AfficheNbreComptes(len(self.GetCoches()))

    def DecocheTout(self):
        self.MAJenCours = True
        item = self.root
        for index in range(0, self.GetChildrenCount(self.root)):
            item = self.GetNext(item) 
            self.CheckItem(item, False)
        self.MAJenCours = False
        self.AfficheNbreComptes(len(self.GetCoches()))
    
    def GetCoches(self):
        dictCoches = {}
        # Parcours des items COMPTE
        parent = self.root
        for index in range(0, self.GetChildrenCount(self.root)):
            parent = self.GetNext(parent) 
            if self.IsItemChecked(parent) :
                IDcompte_payeur = self.GetItemData(parent)["IDcompte_payeur"]
                dictCoches[IDcompte_payeur] = self.GetItemData(parent)
        return dictCoches
    
    def MAJ(self):
        """ Met � jour (redessine) tout le contr�le """
        self.DeleteAllItems()
        self.root = self.AddRoot(_("Racine"))
        self.Remplissage()
        self.CocheTout() 
    
    def Remplissage(self):
        lstIDfamilles = self.dictParametres["listeIDfamilles"]
        dlgAttente = PBI.PyBusyInfo(_("Recherche des impay�s en cours..."), parent=None, title=_("Veuillez patienter..."), icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
        try :
            facturation = UTILS_Rappels.Facturation(lstIDfamilles)
            self.dictComptes = facturation.GetDonnees(date_reference=self.dictParametres["date_reference"],
                                                    date_edition=self.dictParametres["date_edition"],
                                                    listeIDfamilles=lstIDfamilles,
                                                    )
            del dlgAttente
        except Exception as err:
            del dlgAttente
            traceback.print_exc(file=sys.stdout)
            dlg = wx.MessageDialog(self, _("D�sol�, le probl�me suivant a �t� rencontr� dans la recherche des rappels : \n\n%s") % err, _("Erreur"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        # Branches COMPTE
        listeNomsSansCivilite = []
        self.dictControles = {}
        for IDcompte_payeur, dictCompte in self.dictComptes.items() :
            listeNomsSansCivilite.append((dictCompte["nomSansCivilite"], IDcompte_payeur))
        listeNomsSansCivilite.sort() 
        
        dlgAttente = PBI.PyBusyInfo(_("Calcul des selectionn�s en cours..."), parent=None, title=_("Veuillez patienter..."), icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
        wx.Yield()
        index = 0
        for nomSansCivilite, IDcompte_payeur in listeNomsSansCivilite :
            dictCompte = self.dictComptes[IDcompte_payeur]
            IDfamille = IDcompte_payeur
            solde = dictCompte["solde"]
            date_debut = dictCompte["date_min"]
            date_fin = dictCompte["date_max"]
            nbreJoursRetard = (datetime.date.today() - date_fin).days
            
            # Texte du retard
            if nbreJoursRetard < 31 :
                texteRetard = _("%d jours") % nbreJoursRetard
            else :
                nbreMois = nbreJoursRetard / 30
                nbreJours = nbreJoursRetard - (nbreMois*30)
                texteRetard = _("%d jours") % nbreJoursRetard
                
            niveauCompte = self.AppendItem(self.root, nomSansCivilite, ct_type=1)

            self.SetItemText(niveauCompte, UTILS_Dates.DateEngFr(str(date_debut)), 1)
            self.SetItemText(niveauCompte, UTILS_Dates.DateEngFr(str(date_fin)), 2)
            self.SetItemText(niveauCompte, texteRetard, 3)
            self.SetItemText(niveauCompte, solde, 4)

            ctrl_document = CTRL_document(self.GetMainWindow(), -1, branche=niveauCompte, IDcompte_payeur=IDcompte_payeur, nbreJoursRetard=nbreJoursRetard, infobulle=_("S�lectionnez un document"))
            self.SetItemWindow(niveauCompte, ctrl_document, 5)
            self.dictControles[IDcompte_payeur] = ctrl_document

            self.SetItemData(niveauCompte, {"type" : "compte", "valeur" : IDcompte_payeur, "IDcompte_payeur" : IDcompte_payeur, "IDfamille" : IDfamille, "nom" : nomSansCivilite, "ctrl_document" : ctrl_document})

            index += 1
        del dlgAttente

    def GetDictDocument(self, IDcompte_payeur=None):
        ctrl_document = self.dictControles[IDcompte_payeur]
        return ctrl_document.GetDictDocument()

    def SetCouleurLigne(self, branche, couleur):
        self.SetItemBackgroundColour(branche, couleur)
    
    def OnCompareItems(self, item1, item2):
        if self.GetItemData(item1) > self.GetItemData(item2) :
            return 1
        elif self.GetItemData(item1) < self.GetItemData(item2) :
            return -1
        else:
            return 0
                        
    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        item = self.GetSelection()
        dictItem = self.GetMainWindow().GetItemPyData(item)
        type = dictItem["type"]
        if type != "compte" : return
        nomIndividu = dictItem["nom"]
        
        # Cr�ation du menu contextuel
        menuPop = wx.Menu()

        # Item Ouvrir fiche famille
        item = wx.MenuItem(menuPop, 10, _("Afficher un aper�u PDF"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.AfficherApercu, id=10)

        # Finalisation du menu
        self.PopupMenu(menuPop)
        menuPop.Destroy()
            
    def AfficherApercu(self, event=None):
        item = self.GetSelection()
        dictItem = self.GetMainWindow().GetItemPyData(item)
        if dictItem == None :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucune lettre dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        type = dictItem["type"]
        if type != "compte" : 
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucune lettre dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDfamille = dictItem["IDfamille"]
        IDcompte_payeur = dictItem["IDfamille"]
        dictDocument = dictItem["ctrl_document"].GetDictDocument()
        # V�rifie qu'un texte a �t� attribu�
        if dictDocument["IDtexte"] == 0 :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement attribuer un texte � cette lettre !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        
        # R�cup�ration des donn�es
        dictCompte = self.dictComptes[IDcompte_payeur]
        
        dictCompte["titre"] = dictDocument["titre"] 
        dictCompte["IDtexte"] = dictDocument["IDtexte"] 
        
        # Fusion des mots-cl�s
        facturation = UTILS_Rappels.Facturation()
        dictCompte["texte"] = facturation.Fusion(dictDocument["IDtexte"] , dictCompte)

        # R�cup�ration des param�tres d'affichage
        dlg = DLG_Apercu_rappel.Dialog(self, provisoire=True)
        if dlg.ShowModal() == wx.ID_OK:
            dictOptions = dlg.GetParametres()
            dlg.Destroy()
        else :
            dlg.Destroy()
            return False
                   
        # Fabrication du PDF
        dlgAttente = PBI.PyBusyInfo(_("Cr�ation de l'aper�u au format PDF..."), parent=None, title=_("Veuillez patienter..."), icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
        wx.Yield() 
        try :
            UTILS_Impression_rappel.Impression({IDcompte_payeur : dictCompte}, dictOptions, IDmodele=dictOptions["IDmodele"])
            del dlgAttente
        except Exception as err:
            del dlgAttente
            traceback.print_exc(file=sys.stdout)
            dlg = wx.MessageDialog(self, _("D�sol�, le probl�me suivant a �t� rencontr� dans la cr�ation de l'aper�u de la lettre de rappel : \n\n%s") % err, _("Erreur"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        


# -------------------------------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        
        # Donn�es pour les tests        
        self.myOlv = CTRL(panel)
        dictParametres = {
            "date_reference" : datetime.date.today(),
            "IDlot" : None,
            "date_edition" : datetime.date.today(),
            "prestations" : ["consommation", "cotisation", "autre"],
            "IDcompte_payeur" : None,
            "listeActivites" : [1, 2, 3],
            "listeExceptionsComptes" : [],
            "listeIDfamilles" : [3386]
            }
        self.myOlv.SetParametres(dictParametres)
        
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.myOlv, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.SetSize((900, 500))
        self.Layout()
        self.CenterOnScreen()
        

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "OL TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()

#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-15 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
from Utils import UTILS_Interface
from Utils import UTILS_Json
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils
import os
import shutil
from Dlg import DLG_Messagebox
from wx.lib import langlistctrl
from Utils import UTILS_Fichiers


class Track(object):
    def __init__(self, donnees):
        self.nom = donnees["nom"]
        self.code = donnees["code"]
        self.initial = donnees["initial"]
        self.perso = donnees["perso"]
    
    
class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        # Initialisation du listCtrl
        self.nom_fichier_liste = __file__
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        
    def OnItemActivated(self,event):
        self.Modifier(None)
                
    def InitModel(self):
        self.donnees = self.GetTracks()

    def GetTracks(self):
        """ R�cup�ration des donn�es """
        # Langues existantes
        dictLangues = {}
        for rep in (Chemins.GetStaticPath("Lang"), UTILS_Fichiers.GetRepLang()) :
            for nomFichier in os.listdir(rep) :
                if nomFichier.endswith("lang") :
                    code, extension = nomFichier.split(".")
                    data = UTILS_Json.Lire(os.path.join(rep, nomFichier), conversion_auto=True)
                    dictInfos = data["###INFOS###"]
                    nom = dictInfos["nom_langue"]
                    code = dictInfos["code_langue"]
                    nbreTextes = len(data) - 1

                    if (code in dictLangues) == False :
                        dictLangues[code] = {"nom" : nom, "initial" : 0, "perso" : 0}

                    if extension == "lang" :
                        dictLangues[code]["initial"] = nbreTextes
                    else :
                        dictLangues[code]["perso"] = nbreTextes

        # Remplissage
        listeListeView = []
        for code, valeurs in dictLangues.items() :
            dictDonnees = {"code" : code, "initial" : valeurs["initial"], "perso" : valeurs["perso"], "nom" : valeurs["nom"]}
            listeListeView.append(Track(dictDonnees))
        
        return listeListeView
            
    def InitObjectListView(self):            
        # Couleur en alternance des lignes
        self.oddRowsBackColor = UTILS_Interface.GetValeur("couleur_tres_claire", wx.Colour(240, 251, 237))
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True

        liste_Colonnes = [
            ColumnDefn("ID", "left", 0, "", typeDonnee="entier"),
            ColumnDefn(_("Nom"), 'left', 140, "nom", typeDonnee="texte", isSpaceFilling=True),
            ColumnDefn(_("Code"), "center", 60, "code", typeDonnee="texte"),
            ColumnDefn(_("Trad. officielles"), "center", 100, "initial", typeDonnee="entier"),
            ColumnDefn(_("Trad. perso."), "center", 100, "perso", typeDonnee="entier"),
            ]
        
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_("Aucune langue"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, False, "Tekton"))
        self.SetSortColumn(self.columns[1])
        self.SetObjects(self.donnees)
       
    def MAJ(self):
        self.InitModel()
        self.InitObjectListView()
        self._ResizeSpaceFillingColumns() 

    def Selection(self):
        return self.GetSelectedObjects()

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        if len(self.Selection()) == 0:
            noSelection = True
        else:
            noSelection = False
                
        # Cr�ation du menu contextuel
        menuPop = UTILS_Adaptations.Menu()

        # Item Modifier
        item = wx.MenuItem(menuPop, 10, _("Ajouter"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Ajouter, id=10)

        menuPop.AppendSeparator()

        # Item Modifier
        item = wx.MenuItem(menuPop, 20, _("Modifier"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Modifier, id=20)
        if noSelection == True : item.Enable(False)
        
        # Item Supprimer
        item = wx.MenuItem(menuPop, 30, _("Supprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Supprimer, id=30)
        if noSelection == True : item.Enable(False)
                
        menuPop.AppendSeparator()

        # Item Importer
        item = wx.MenuItem(menuPop, 80, _("Importer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Document_import.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Importer, id=80)

        # Item Exporter
        item = wx.MenuItem(menuPop, 90, _("Exporter"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Document_export.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Exporter, id=90)
        if noSelection == True : item.Enable(False)

        menuPop.AppendSeparator()
    
        # Item Apercu avant impression
        item = wx.MenuItem(menuPop, 40, _("Aper�u avant impression"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=40)
        
        # Item Imprimer
        item = wx.MenuItem(menuPop, 50, _("Imprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=50)
        
        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Apercu(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des langues"), format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des langues"), format="A", orientation=wx.PORTRAIT)
        prt.Print()


    def Ajouter(self, event):
        dlg = Saisie(self)
        code = None
        if dlg.ShowModal() == wx.ID_OK:
            code = dlg.GetCode()
            nom = dlg.GetNom()
        dlg.Destroy()
        if code == None : 
            return
        
        from Dlg import DLG_Saisie_traduction
        dlg = DLG_Saisie_traduction.Dialog(self, code=code, nom=nom)
        if dlg.ShowModal() == wx.ID_OK:
            self.MAJ()
        dlg.Destroy()
        
    def Modifier(self, event):
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucune langue � modifier dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]
        from Dlg import DLG_Saisie_traduction
        dlg = DLG_Saisie_traduction.Dialog(self, code=track.code, nom=track.nom)
        if dlg.ShowModal() == wx.ID_OK:
            self.MAJ()
        dlg.Destroy()

    def Supprimer(self, event):
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucun fichier de traduction � supprimer dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]

        if track.perso == 0 :
            dlg = wx.MessageDialog(self, _("Il n'y a aucune traduction personnalis�e � supprimer !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer ce fichier de traduction personnalis� (%d traductions) ?\n\nAttention, toute suppression est irr�versible.") % track.perso, _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
        if dlg.ShowModal() == wx.ID_YES :
            nomFichier = UTILS_Fichiers.GetRepLang(u"%s.xlang" % track.code)
            os.remove(nomFichier)
            self.MAJ() 
        dlg.Destroy()
    
    def Importer(self, event):
        """ Importer un fichier de langue """
        # Ouverture de la fen�tre de dialogue
        wildcard = "Fichiers de langue (*.lang, *.xlang)|*.lang;*.xlang|Tous les fichiers (*.*)|*.*"
        sp = wx.StandardPaths.Get()
        dlg = wx.FileDialog(
            self, message=_("Choisissez un fichier de langue � importer"),
            defaultDir=sp.GetDocumentsDir(), 
            defaultFile="",
            wildcard=wildcard,
            style=wx.FD_OPEN
            )
        if dlg.ShowModal() == wx.ID_OK:
            nomFichierCourt = dlg.GetFilename()
            nomFichierLong = dlg.GetPath()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
        
        # V�rifie si un fichier existe d�j�
        if os.path.isfile(UTILS_Fichiers.GetRepLang(nomFichierCourt)) == False :
            shutil.copyfile(nomFichierLong, UTILS_Fichiers.GetRepLang(nomFichierCourt))
            self.MAJ()
        else :
            dlg = DLG_Messagebox.Dialog(self, titre=_("Importer"), introduction=_("Ce fichier est d�j� pr�sent !"), detail=None, conclusion=_("Souhaitez-vous le remplacer ou les fusionner ?"), icone=wx.ICON_EXCLAMATION, boutons=[_("Fusionner"), _("Remplacer"), _("Annuler")])
            reponse = dlg.ShowModal()
            dlg.Destroy()
            
            if reponse == 0 : 
                # Fusionner
                dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment fusionner les deux fichiers ?"), _("Confirmation"), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
                reponse = dlg.ShowModal()
                dlg.Destroy()
                if reponse == wx.ID_NO :
                    return
                
                # Lecture des 2 fichiers
                dictDonnees = {}
                for nomFichier in [UTILS_Fichiers.GetRepLang(nomFichierCourt), nomFichierLong] :
                    data = UTILS_Json.Lire(nomFichier, conversion_auto=True)
                    for key, valeur in data.items() :
                        dictDonnees[key] = valeur

                # Ecriture du fichier final
                nomFichier = UTILS_Fichiers.GetRepLang(nomFichierCourt)
                UTILS_Json.Ecrire(nomFichier, data=dictDonnees)
                self.MAJ()

                dlg = wx.MessageDialog(self, _("Le fichier a �t� import� avec succ�s !"), _("Confirmation"), wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()

            if reponse == 1 :
                # Remplacer
                dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment remplacer le fichier ?"), _("Confirmation"), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
                reponse = dlg.ShowModal()
                dlg.Destroy()
                if reponse == wx.ID_NO :
                    return
                
                # Copie du fichier vers le r�pertoire Lang
                os.remove(UTILS_Fichiers.GetRepLang(nomFichierCourt))
                shutil.copyfile(nomFichierLong, UTILS_Fichiers.GetRepLang(nomFichierCourt))
                self.MAJ()
 
                dlg = wx.MessageDialog(self, _("Le fichier a �t� import� avec succ�s !"), _("Confirmation"), wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
               
            if reponse == 2 :
                return False
        
    def Exporter(self, event):
        """ Exporter le mod�le s�lectionn� """
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucune langue dans la liste !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]
        
        if track.perso == 0 :
            dlg = wx.MessageDialog(self, _("Il n'y a aucune traduction personnalis�e � exporter !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        nomFichier = track.code + ".xlang"
        
        # Demande le chemin pour la sauvegarde du fichier
        standardPath = wx.StandardPaths.Get()
        dlg = wx.FileDialog(self, message=_("Envoyer le fichier de traduction personnalis� vers..."),
                            defaultDir = standardPath.GetDocumentsDir(), defaultFile=nomFichier,
                            wildcard="Fichier de traduction (*.xlang)|*.xlang", style=wx.FD_SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        else :
            path = None
        dlg.Destroy()
        if path == None :
            return

        # Le fichier de destination existe d�j� :
        if os.path.isfile(path) == True :
            dlg = wx.MessageDialog(None, _("Un fichier portant ce nom existe d�j�. \n\nVoulez-vous le remplacer ?"), "Attention !", wx.YES_NO | wx.NO_DEFAULT | wx.ICON_EXCLAMATION)
            if dlg.ShowModal() == wx.ID_NO :
                return False
                dlg.Destroy()
            else:
                dlg.Destroy()

        # Exportation
        shutil.copyfile(UTILS_Fichiers.GetRepLang(nomFichier), path)

        # Confirmation
        dlg = wx.MessageDialog(self, _("Le fichier de traduction a �t� export� avec succ�s !"), _("Exportation"), wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
        



# -------------------------------------------------------------------------------------------------------------------------------------------




class Saisie(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.SetTitle(_("Saisie d'une nouvelle traduction"))
        self.SetMinSize((400, 400)) 
        
        self.label_langue = wx.StaticText(self, -1, _("S�lectionnez une langue :"))
        self.ctrl_langue = langlistctrl.LanguageListCtrl(self, -1, filter=langlistctrl.LC_ALL)
        self.dictLangues = langlistctrl.BuildLanguageCountryMapping() 
        
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ok"), cheminImage="Images/32x32/Valider.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Annuler"), cheminImage="Images/32x32/Annuler.png")

        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.label_langue, 0, wx.TOP|wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        grid_sizer_base.Add(self.ctrl_langue, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(1)
        self.Layout()
        self.CenterOnScreen()
        
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        
    def OnBoutonOk(self, event):
        index = self.ctrl_langue.GetLanguage()
        if index == None :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement s�lectionner une langue dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        
        self.EndModal(wx.ID_OK)

    def GetCode(self):
        index = self.ctrl_langue.GetLanguage()
        return self.dictLangues[index]
    
    def GetNom(self):
        index = self.ctrl_langue.GetFirstSelected() 
        return self.ctrl_langue.GetItemText(index)
    

# -------------------------------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.myOlv = ListView(panel, id=-1, name="OL_test", style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        self.myOlv.MAJ() 
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.myOlv, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "OL TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()

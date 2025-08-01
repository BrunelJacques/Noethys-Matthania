#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys branche Matthania
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS, JB
# Copyright:       (c) 2010-18 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import Chemins
import wx
import datetime
import copy
import os
import decimal
from Ctrl import CTRL_Footer
import Olv.ObjectListView as OLV
from Olv.ObjectListView import AbstractVirtualObjectListView as Abstract
import Olv.Filter as Filter
import Olv.OLVEvent as OLVEvent

def Nz(valeur):
    if not valeur:
        valeur = 0
    return valeur

class Track():
    def __init__(self, dictTotaux):
        for nomColonne, total in dictTotaux.items() :
            setattr(self, nomColonne, total)


class ObjectListView(OLV.ObjectListView):
    def __init__(self, *args, **kwargs):
        # Variables sp�ciales
        self.listeColonnes = []
        self.listeFiltresColonnes = []
        self.nomListe = None
        self.ctrl_footer = None
        self.barreRecherche = None
        self.titre = ""
        self.impression_intro = ""
        self.impression_total = ""
        self.orientation = wx.PORTRAIT
        self.filtrerAndNotOr = True

        OLV.ObjectListView.__init__(self, *args, **kwargs)
        self.Bind(wx.EVT_LIST_COL_DRAGGING, self._HandleColumnDragging)
        self.GetMainWindow().Bind(wx.EVT_SCROLLWIN, self.OnScroll)

    def Activation(self, etat=True):
        """ Active ou desactive l'etat du controle """
        if etat == True :
            self.Enable(True)
            self.stEmptyListMsg.SetBackgroundColour(self.GetBackgroundColour())
        else :
            self.Enable(False)
            couleur = wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK)# self.stEmptyListMsg.GetBackgroundColour()
            self.stEmptyListMsg.SetBackgroundColour(couleur)
        self.stEmptyListMsg.Refresh()

    def SetColumns(self, columns, repopulate=True):
        self.listeColonnes = columns
        sortCol = self.GetSortColumn()
        wx.ListCtrl.ClearAll(self)
        self.checkStateColumn = None
        self.columns = []
        for x in columns:
            if hasattr(x, "visible") == False or x.visible == True :
                if isinstance(x, ColumnDefn) or isinstance(x, OLV.ColumnDefn):
                    self.AddColumnDefn(x)
                else:
                    self.AddColumnDefn(ColumnDefn(*x))
        # Try to preserve the column column
        if sortCol:
            self.SetSortColumn(sortCol)
        if repopulate:
            self.RepopulateList()

    def AddColumnDefn(self, defn):
        # Enl�ve l'espace gauche sur tous les headers du listctrl sous Phoenix en ajoutant une image transparente
        # if 'phoenix' in wx.PlatformInfo:
        #     if defn.headerImage == -1 :
        #         smallImage = wx.Bitmap(16, 16)
        #         mask = wx.Mask(smallImage, wx.BLACK)
        #         smallImage.SetMask(mask)
        #         self.smallImageList.AddNamedImage("vide", smallImage)
        #         normalImage = wx.Bitmap(32, 32)
        #         mask = wx.Mask(normalImage, wx.BLACK)
        #         normalImage.SetMask(mask)
        #         self.normalImageList.AddNamedImage("vide", normalImage)
        #         defn.headerImage = "vide"

        super(ObjectListView, self).AddColumnDefn(defn)

    def AddObjects(self, modelObjects):
        super(ObjectListView, self).AddObjects(modelObjects)

        # MAJ Footer
        if self.ctrl_footer :
            self.MAJ_footer()

    def RepopulateList(self):
        super(ObjectListView, self).RepopulateList()

        # MAJ Footer
        if self.ctrl_footer :
            self.MAJ_footer()

    def RefreshObject(self, modelObject):
        super(ObjectListView, self).RefreshObject(modelObject)

        # MAJ Footer
        if self.ctrl_footer :
            self.MAJ_footer()

    def _HandleColumnClick(self, evt):
        super(ObjectListView, self)._HandleColumnClick(evt)

        if hasattr(self, "OnClickColonne") :
            self.OnClickColonne(indexColonne=evt.GetColumn(), ascendant=self.sortAscending)
        self.RepopulateList()

    def _HandleColumnDragging(self, evt):
        self.MAJ_footer()
        evt.Skip()

    def _HandleLeftDownOnImage(self, rowIndex, subItemIndex):
        column = self.columns[subItemIndex]
        if not column.HasCheckState():
            return

        self._PossibleFinishCellEdit()
        modelObject = self.GetObjectAt(rowIndex)
        if modelObject is not None:
            column.SetCheckState(modelObject, not column.GetCheckState(modelObject))
            self.RefreshIndex(rowIndex, modelObject)
            self.OnCheck(modelObject)
    
    def OnCheck(self, modelObject=None):
        """ Fonction perso a surcharger """
        pass

    def OnScroll(self, event):
        if event.GetOrientation() == wx.HORIZONTAL :
            self.MAJ_footer()
        event.Skip()


    def _HandleSize(self, evt):
        self._PossibleFinishCellEdit()
        evt.Skip()
        self._ResizeSpaceFillingColumns()
        # Make sure our empty msg is reasonably positioned
        sz = self.GetClientSize()
        if self.HasFlag(wx.LC_NO_HEADER) :
            proportion = 3
        else :
            proportion = 2
        try :
            self.stEmptyListMsg.SetSize(0, int(sz.GetHeight()/proportion), sz.GetWidth(), sz.GetHeight()) # J'ai mis 2 a la place de 3
        except :
            self.stEmptyListMsg.SetDimensions(0, sz.GetHeight() / proportion, sz.GetWidth(), sz.GetHeight())  # J'ai mis 2 a la place de 3

        # Masque le texte "Aucun" si version phoenix (� cause des colonnes bleues)
        self.stEmptyListMsg.Hide()

        # Pour un centrage du texte
        # self.stEmptyListMsg.SetPosition((sz.GetWidth() / 2 - self.stEmptyListMsg.GetSize()[0]/2, sz.GetHeight() / proportion))

    def _SortObjects(
            self,
            modelObjects=None,
            sortColumn=None,
            secondarySortColumn=None):
        """
        Sort the given modelObjects in place.

        This does not change the information shown in the control itself.
        """
        if modelObjects is None:
            modelObjects = self.modelObjects
        if sortColumn is None:
            sortColumn = self.GetSortColumn()
        if secondarySortColumn == sortColumn:
            secondarySortColumn = None

        # If we don't have a sort column, we can't sort -- duhh
        if sortColumn is None:
            return

        # Let the world have a chance to sort the model objects
        evt = OLVEvent.SortEvent(
            self,
            self.sortColumnIndex,
            self.sortAscending,
            True)
        self.GetEventHandler().ProcessEvent(evt)
        if evt.IsVetoed() or evt.wasHandled:
            return

        # When sorting large groups, this is called a lot. Make it efficent.
        # It is more efficient (by about 30%) to try to call lower() and catch the
        # exception than it is to test for the class
        def _getSortValue(x):
            primary = sortColumn.GetValue(x)
            # pour des tris num�riques on garde le type d'origine de primary
            isNum = isinstance(primary,(float,decimal.Decimal,int,bool))
            if hasattr(sortColumn,'typeDonnee'):
                if sortColumn.typeDonnee in ("texte",):
                    isNum = False
                elif sortColumn.typeDonnee in ("montant", "entier","bool" ):
                    isNum = True
            if isNum:
                if not isinstance(primary,(float,int,decimal.Decimal)):
                    primary = 0.0
            else:
                # Ramener a des comparaisons texte, pour cas g�n�ral
                if primary == None:
                    primary = ""
                primary = str(primary)
            try:
                primary = primary.lower()
            except AttributeError:
                pass

            if secondarySortColumn:
                secondary = secondarySortColumn.GetValue(x)
                try:
                    secondary = secondary.lower()
                except AttributeError:
                    pass

                return (primary, secondary)
            else:
                return primary
        modelObjects.sort(key=_getSortValue, reverse=(not self.sortAscending))

        # Sorting invalidates our object map
        self.objectToIndexMap = None

    def SetColumns2(self, colonnes=[], nomListe=None):
        """ Pour une liste avec possibilit�s de configuration """
        self.nomListe = nomListe
        if self.listeColonnes == [] :
            from Dlg import DLG_Configuration_listes
            self.listeColonnesDefaut = copy.deepcopy(colonnes)
            self.listeCodesDefaut = [col.valueGetter for col in self.listeColonnesDefaut if hasattr(col, "visible") and col.visible == True]
            self.listeColonnes = DLG_Configuration_listes.RestaurationConfiguration(nomListe=nomListe, listeColonnesDefaut=colonnes)
        self.SetColumns(self.listeColonnes)

    def AjouterCommandesMenuContext(self, menu=None):
        # S�paration
        menu.AppendSeparator()
        
        # Item Configurer la liste
        item = wx.MenuItem(menu, 8601, "Configurer la liste")
        item.SetBitmap(wx.Bitmap(
            Chemins.GetStaticPath("Images/16x16/Mecanisme.png"), wx.BITMAP_TYPE_PNG))
        menu.Append(item)
        self.Bind(wx.EVT_MENU, self.MenuConfigurerListe, id=8601)

        # S�paration
        menu.AppendSeparator()
        
        # Statistiques de la liste
        nbreLignes = len(self.innerList)
        if nbreLignes == 0 :
            label = "Liste vide"
        elif nbreLignes == 1 :
            label = "1 ligne"
        else :
            label = "%d lignes" % nbreLignes
        label += " et %d colonnes" % len(self.columns)
        item = wx.MenuItem(menu, 8602, label)
        menu.Append(item)
        item.Enable(False)
    
    def MenuConfigurerListe(self, event=None):
        # Recherche les colonnes disponibles
        colonnes_dispo = []
        for col in self.listeColonnesDefaut:
            if hasattr(col, "visible"):
                # M�morise colonne disponible
                nom = col.title
                if nom == "":
                    nom = col.valueGetter
                colonnes_dispo.append({"nom" : nom, "code" : col.valueGetter, "col" : col})

        # M�morise s�lection actuelle
        colonnes_selection = []
        for col in self.listeColonnes :
            if hasattr(col, "visible"):
                if col.visible == True :
                    colonnes_selection.append(col.valueGetter)

        # Recherche les colonnes par d�faut
        colonnes_defaut = copy.copy(self.listeCodesDefaut)

        # DLG de la configuration de listes
        from Dlg import DLG_Configuration_listes
        dlg = DLG_Configuration_listes.Dialog(self, colonnes_dispo=colonnes_dispo, colonnes_defaut=colonnes_defaut, colonnes_selection=colonnes_selection)
        if dlg.ShowModal() == wx.ID_OK:
            listeColonnesSelection = dlg.GetSelections(mode="dict")
            dlg.Destroy()
        else :
            dlg.Destroy()
            return

        # Analyse des r�sultats
        self.listeColonnes = []
        for dictColonne in listeColonnesSelection :
            col = dictColonne["col"]
            col.visible = True
            self.listeColonnes.append(col)

        # Sauvegarde
        self.SauvegardeConfiguration()

        # Annule le regroupement �ventuel
        if hasattr(self, "SetShowGroups"):
            self.SetShowGroups(False)
        self.useExpansionColumn = False

        # Mise � jour de la liste
        attente = wx.BusyInfo(u"Configuration de la liste en cours...", self)
        self.OnConfigurationListe()
        self.InitModel()
        self.InitObjectListView()
        del attente

    def OnConfigurationListe(self):
        """ A surcharger """
        pass

    def SauvegardeConfiguration(self, event=None):
        """ Sauvegarde de la configuration """
        if self.nomListe != None :
            from Dlg import DLG_Configuration_listes
            DLG_Configuration_listes.SauvegardeConfiguration(nomListe=self.nomListe, listeColonnes=self.listeColonnes)
    
        
    def AjouteLigneTotal(self, listeNomsColonnes=[]):
        return
        for (iCol, col) in enumerate(self.columns):
            colWidth = self.GetColumnWidth(iCol)
            boundedWidth = col.CalcBoundedWidth(colWidth)


        # R�cup�ration des totaux des colonnes souhait�es
        dictTotaux = {}
        nbreLignes = 0
        for track in self.modelObjects :
            for nomColonne in listeNomsColonnes :
                valeur = getattr(track, nomColonne)
                if (nomColonne in dictTotaux) == False :
                    dictTotaux[nomColonne] = 0
                else :
                    dictTotaux[nomColonne] += valeur
            nbreLignes += 1
        
        track = Track(dictTotaux)
##        self.modelObjects.append(track)
        self.AddObject(track)
    
    def SetFooter(self, ctrl=None, dictColonnes={}):
        self.ctrl_footer = ctrl
        self.ctrl_footer.listview = self
        self.ctrl_footer.dictColonnes = dictColonnes
    
    def MAJ_footer(self):
        if self.ctrl_footer != None :
            self.ctrl_footer.MAJ()
    
    def GetListview(self):
        return self

    def DefilePremier(self):
        largeur, hauteur = self.GetSize()
        if largeur > 0 and hauteur > 0:
            if self.GetFilter() != None:
                listeObjets = self.GetFilteredObjects()
            else:
                listeObjets = self.GetObjects()
            if len(listeObjets) > 0:
                premierTrack = listeObjets[0]
                index = self.GetIndexOf(premierTrack)
                self.EnsureCellVisible(index, 0)

    def DefileDernier(self):
        """ Defile jusqu'au dernier item de la liste """
        largeur, hauteur = self.GetSize()
        if largeur > 0 and hauteur > 0 :
            if self.GetFilter() != None :
                listeObjets = self.GetFilteredObjects()
            else :
                listeObjets = self.GetObjects()
            if len(listeObjets) > 0 :
                dernierTrack = listeObjets[-1]
                index = self.GetIndexOf(dernierTrack)
                self.EnsureCellVisible(index, 0)
            
    def Filtrer(self, texteRecherche=None):
        listeFiltres = []
        
        # Filtre barre de recherche
        if texteRecherche != None and len(texteRecherche) > 0:
            filtre = Filter.TextSearch(self, self.columns[0:self.GetColumnCount()])
            filtre.SetText(texteRecherche)
            listeFiltres.append(filtre)
        
        # Filtres de colonnes
        # for texteFiltre in self.formatageFiltres(self.listeFiltresColonnes) :
        #     filtre = Filter.Predicate(lambda track: eval(texteFiltre))
        #     listeFiltres.append(filtre)

        filtres_colonnes = self.formatageFiltres(self.listeFiltresColonnes)
        if len(filtres_colonnes) > 0:
            if self.filtrerAndNotOr:
                andor = " and "
            else: andor = " or "
            texteFiltre = andor.join(filtres_colonnes)
            # Pour d�bug voir les param�trages => def formatageFiltres(
            filtre = Filter.Predicate(lambda track: eval(texteFiltre))
            listeFiltres.append(filtre)
        self.SetFilter(Filter.Chain(self.filtrerAndNotOr,*listeFiltres))
        self.RepopulateList()
        self.Refresh() 
        self.OnCheck(None) 
    
    def SetFiltresColonnes(self, listeFiltresColonnes=[]):
        self.listeFiltresColonnes = listeFiltresColonnes
        if self.barreRecherche != None :
            self.barreRecherche.Cancel()
        self.Filtrer() 
    
    def formatageFiltres(self, listeFiltres=[]):
        # Formatage du filtre
        listeFiltresFinale = []
        filtre = None
        for dictFiltre in listeFiltres :
            code = dictFiltre["code"]
            choix = dictFiltre["choix"]
            criteres = dictFiltre["criteres"]
            typeDonnee = dictFiltre["typeDonnee"]

            # Filtre librement compos� comme une condition de if
            if typeDonnee == "libre" :
                filtre = criteres

            # Texte
            if typeDonnee == "texte" :
                if choix == "EGAL" :
                    filtre = "track.%s != None and track.%s.lower() == '%s'.lower()" % (code, code, criteres)
                if choix == "DIFFERENT" :
                    filtre = "track.%s != None and track.%s.lower() != '%s'.lower()" % (code, code, criteres)
                if choix == "CONTIENT" :
                    filtre = "track.%s != None and '%s'.lower() in track.%s.lower()" % (code, criteres, code)
                if choix == "COMMENCE":
                    lg = len(criteres)
                    filtre = "track.%s != None and u'%s'.lower()[:%d] == track.%s.lower()[:%d]" % (code, criteres, lg, code, lg)
                if choix == "CONTIENTPAS" :
                    filtre = "track.%s != None and '%s'.lower() not in track.%s.lower()" % (code, criteres, code)
                if choix == "VIDE" :
                    filtre = "(track.%s == '' or track.%s == None)" % (code, code)
                if choix == "PASVIDE" :
                    filtre = "track.%s != '' and track.%s != None" % (code, code)
                if choix == "DANS" :
                    lst = criteres.split(";")
                    serie = "["
                    for x in lst:
                        serie += "'%s'"%x.lower().strip() + ","
                    serie += "]"
                    filtre = "track.%s != None and track.%s.lower() in %s" % (code, code, serie)
                if choix == "NONDANS" :
                    lst = criteres.split(";")
                    serie = "["
                    for x in lst:
                        serie += "'%s'"%x.lower().strip() + ","
                    serie += "]"
                    filtre = "((track.%s == None) or not(track.%s.lower() in %s))" % (code, code, serie)
            # Bool
            if typeDonnee == "bool" :
                if choix == "TRUE" :
                    filtre = "track.%s in (True, 'True', 1, '1')" % code
                if choix == "FALSE" :
                    filtre = "track.%s in (False, 'False', 0, '0', None, '')" % code

            # Entier, montant
            if typeDonnee in ("entier", "montant") :
                
                if choix == "COMPRIS" :
                    min = str(criteres.split(";")[0])
                    max = str(criteres.split(";")[1])
                else :
                    criteres = str(criteres)

                filtre = 'track.%s != None and '%code

                if choix == "EGAL" :
                    filtre += "track.%s == %s" % (code, criteres)
                if choix == "DIFFERENT" :
                    filtre += "track.%s != %s" % (code, criteres)
                if choix == "SUP" :
                    filtre += "track.%s > %s" % (code, criteres)
                if choix == "SUPEGAL" :
                    filtre += "track.%s >= %s" % (code, criteres)
                if choix == "INF" :
                    filtre += "track.%s < %s" % (code, criteres)
                if choix == "INFEGAL" :
                    filtre += "track.%s <= %s" % (code, criteres)
                if choix == "COMPRIS" :
                    filtre += "(track.%s >= %s and track.%s <= %s)" % (code, min, code, max)

                if choix == "VIDE" :
                    filtre = "(track.%s == None)" % (code)
                if choix == "PASVIDE" :
                    filtre = "track.%s != None" % (code)


            # Date
            if typeDonnee in ("date", "dateheure") :
                if choix == "EGAL" :
                    if criteres == None:
                        filtre = "(track.%s == None or track.%s == '')" % (
                        code, code)
                    else:
                        filtre = "track.%s != None and str(track.%s) == '%s'" % (
                        code, code, criteres)
                if choix == "DIFFERENT":
                    if criteres == None:
                        filtre = "track.%s != None" % (code)
                    else:
                        filtre = "track.%s != None and str(track.%s) != '%s'" % (
                        code, code, criteres)
                if choix == "SUP":
                    if criteres == None:
                        filtre = "track.%s != None" % (code)
                    else:
                        filtre = "track.%s != None and str(track.%s) > '%s'" % (
                        code, code, criteres)
                if choix == "SUPEGAL":
                    filtre = "track.%s != None and str(track.%s) >= '%s'" % (
                    code, code, criteres)
                if choix == "INF":
                    filtre = "track.%s != None and str(track.%s) < '%s'" % (
                    code, code, criteres)
                if choix == "INFEGAL":
                    if criteres == None:
                        filtre = "(track.%s == None or track.%s <= '')" % (
                        code, code)
                    else:
                        filtre = "track.%s != None and str(track.%s) <= '%s'" % (
                        code, code, criteres)
                if choix == "COMPRIS":
                    if criteres.split(";")[0] == 'None':
                        max = criteres.split(";")[1]
                        filtre = "(track.%s == None or str(track.%s) <= '%s')" % (
                        code, code, max)
                    else:
                        min = criteres.split(";")[0]
                        max = criteres.split(";")[1]
                        filtre = "track.%s != None and str(track.%s) >= '%s' and str(track.%s) <= '%s'" % (
                        code, code, min, code, max)
                if choix == "VIDE" :
                    filtre = "(track.%s == '' or track.%s == None)" % (code, code)
                if choix == "PASVIDE" :
                    filtre = "track.%s != '' and track.%s != None" % (code, code)

            # Inscrits
            if typeDonnee == "inscrits" :
                if choix == "INSCRITS" :
                    filtre = "track.ID%s in %s" % (code, self.GetInscrits(mode=code, choix=choix, criteres=criteres))
                if choix == "PRESENTS" :
                    filtre = "track.ID%s in %s" % (code, self.GetInscrits(mode=code, choix=choix, criteres=criteres))
                    
            # M�morisation
            if filtre:
                listeFiltresFinale.append(filtre)
        
        return listeFiltresFinale

    def GetInscrits(self, mode="individu", choix="", criteres={}):
        """ R�cup�ration de la liste des individus inscrits et pr�sents """
        listeActivites = criteres["listeActivites"]
        listeGroupes = criteres["listeGroupes"]
        if choix == "PRESENTS":
            periode = (criteres["date_debut"], criteres["date_fin"])
        else :
            periode = None

        # Conditions Activites
        if listeActivites == None or listeActivites == [] :
            conditionActivites = ""
        else:
            if len(listeActivites) == 1 :
                conditionActivites = " AND inscriptions.IDactivite=%d" % listeActivites[0]
            else:
                conditionActivites = " AND inscriptions.IDactivite IN %s" % str(tuple(listeActivites))

        # Conditions Groupes
        if listeGroupes == None or listeGroupes == [] :
            conditionGroupes = ""
        else:
            if len(listeGroupes) == 1 :
                conditionGroupes = " AND inscriptions.IDgroupe=%d" % listeGroupes[0]
            else:
                conditionGroupes = " AND inscriptions.IDgroupe IN %s" % str(tuple(listeGroupes))
            if periode != None :
                conditionGroupes = conditionGroupes.replace("inscriptions", "consommations")
                
        # Conditions Pr�sents
        conditionPresents = ""
        jointurePresents = ""
        if periode != None :
            conditionPresents = " AND (consommations.date>='%s' AND consommations.date<='%s' AND consommations.etat IN ('reservation', 'present'))" % (str(periode[0]), str(periode[1]))
            jointurePresents = "LEFT JOIN consommations ON consommations.IDindividu = inscriptions.IDindividu"

        # Condition Date inscription
        conditionDateInscription = ""
        if "date_debut_inscription" in criteres:
            conditionDateInscription = " AND (inscriptions.date_inscription>='%s' AND inscriptions.date_inscription<='%s')" % (str(criteres["date_debut_inscription"]), str(criteres["date_fin_inscription"]))

        # Condition Date naissance
        conditionDateNaissance = ""
        if "date_debut_naissance" in criteres:
            conditionDateNaissance = " AND (individus.date_naiss>='%s' AND individus.date_naiss<='%s')" % (str(criteres["date_debut_naissance"]), str(criteres["date_fin_naissance"]))

        # Choix de la key
        if mode == "individu" :
            key = "inscriptions.IDindividu"
        if mode == "famille" :
            key = "inscriptions.IDfamille"
        
        import GestionDB
        DB = GestionDB.DB()
        req = """SELECT %s
        FROM inscriptions 
        LEFT JOIN individus ON individus.IDindividu = inscriptions.IDindividu
        %s
        WHERE (NOT inscriptions.statut LIKE 'ko%%') AND (inscriptions.date_desinscription IS NULL OR inscriptions.date_desinscription>='%s')  %s %s %s %s %s
        GROUP BY %s
        ;""" % (key, jointurePresents, datetime.date.today(), conditionActivites, conditionGroupes, conditionPresents, conditionDateInscription, conditionDateNaissance, key)
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close() 
        
        listeID = []
        for donnees in listeDonnees :
            listeID.append(donnees[0])
        return listeID

    def SetBarreRecherche(self, ctrl=None):
        self.barreRecherche = ctrl

    def CocheListeTout(self, event=None):
        for track in self.modelObjects :
            self.Check(track)
        self.RepopulateList()
        self.OnCheck(None)
        
    def CocheListeRien(self, event=None):
        for track in self.modelObjects :
            self.Uncheck(track)
        self.RepopulateList()
        self.OnCheck(None)

    def CocheJusqua(self, event=None):
        listeObjects = self.innerList # listview.GetFilteredObjects()
        selection = self.GetSelectedObject()
        for track in listeObjects :
            coche = self.GetCheckState(track)
            inverse = not coche
            self.SetCheckState(track,inverse)
            self.RefreshObject(track)
            if selection != None:
                if selection == track:
                    break
        self.OnCheck(None)

    def CocheTout(self, event=None):
        self.CocheListeTout()

    def CocheRien(self, event=None):
        self.CocheListeRien()

    def GetNomModule(self):
        if hasattr(self, "nom_fichier_liste") :
            nom_module = os.path.basename(self.nom_fichier_liste)
            for extension in (".pyc", ".py"):
                nom_module = nom_module.replace(extension, "")
            return nom_module
        return None

    def GenerationContextMenu(self, menu=None, intro="", total="", titre=None, orientation=wx.PORTRAIT, dictParametres=None):
        if dictParametres != None :
            if "titre" in dictParametres : titre = dictParametres["titre"]
            if "intro" in dictParametres: intro = dictParametres["intro"]
            if "total" in dictParametres: total = dictParametres["total"]
            if "orientation" in dictParametres: orientation = dictParametres["orientation"]

        # Met � jour le titre de la liste si besoin
        if titre != None :
            self.titre = titre

        # Intro et total
        self.impression_intro = intro
        self.impression_total = total
        self.orientation = orientation

        if self.checkStateColumn != None:

            # Item Tout cocher
            id = wx.Window.NewControlId()
            item = wx.MenuItem(menu, id, "Tout cocher")
            item.SetBitmap(wx.Bitmap(
                Chemins.GetStaticPath("Images/16x16/Cocher.png"), wx.BITMAP_TYPE_PNG))
            menu.Append(item)
            self.Bind(wx.EVT_MENU, self.CocheListeTout, id=id)

            # Item Tout d�cocher
            id = wx.Window.NewControlId()
            item = wx.MenuItem(menu, id, "Tout d�cocher")
            item.SetBitmap(wx.Bitmap(
                Chemins.GetStaticPath("Images/16x16/Decocher.png"), wx.BITMAP_TYPE_PNG))
            menu.Append(item)
            self.Bind(wx.EVT_MENU, self.CocheListeRien, id=id)

            menu.AppendSeparator()

        # Apercu avant impression
        id = wx.Window.NewControlId()
        item = wx.MenuItem(menu, id, "Aper�u avant impression")
        item.SetBitmap(wx.Bitmap(
            Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG))
        menu.Append(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=id)

        # Item Imprimer
        id = wx.Window.NewControlId()
        item = wx.MenuItem(menu, id, "Imprimer")
        item.SetBitmap(wx.Bitmap(
            Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_PNG))
        menu.Append(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=id)

        menu.AppendSeparator()

        # Item Export Texte
        id = wx.Window.NewControlId()
        item = wx.MenuItem(menu, id, "Exporter au format Texte")
        item.SetBitmap(wx.Bitmap(
            Chemins.GetStaticPath("Images/16x16/Texte2.png"), wx.BITMAP_TYPE_PNG))
        menu.Append(item)
        self.Bind(wx.EVT_MENU, self.ExportTexte, id=id)

        # Item Export Excel
        id = wx.Window.NewControlId()
        item = wx.MenuItem(menu, id, "Exporter au format Excel")
        item.SetBitmap(wx.Bitmap(
            Chemins.GetStaticPath("Images/16x16/Excel.png"), wx.BITMAP_TYPE_PNG))
        menu.Append(item)
        self.Bind(wx.EVT_MENU, self.ExportExcel, id=id)

        # Recherche s'il y a un IDfamille ou un IDindividu
        if len(self.GetObjects()) > 0 :
            track = self.GetObjects()[0]
            famille = hasattr(track, "IDfamille")
            individu = hasattr(track, "IDindividu")
            if famille == True or individu == True :

                menu.AppendSeparator()

                # Envoyer des emails
                id = wx.Window.NewControlId()
                item = wx.MenuItem(menu, id, "Envoyer un Email")
                item.SetBitmap(wx.Bitmap(
                    Chemins.GetStaticPath("Images/16x16/Editeur_email.png"), wx.BITMAP_TYPE_PNG))
                menu.Append(item)
                self.Bind(wx.EVT_MENU, self.EnvoyerMail, id=id)

    def Apercu(self, event=None):
        if hasattr(self, "GetParametresImpression") :
            dictParametres = self.GetParametresImpression()
            if "titre" in dictParametres: self.titre = dictParametres["titre"]
            if "intro" in dictParametres: self.impression_intro = dictParametres["intro"]
            if "total" in dictParametres: self.impression_total = dictParametres["total"]
            if "orientation" in dictParametres: self.orientation = dictParametres["orientation"]

        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=self.titre, intro=self.impression_intro, total=self.impression_total, format="A", orientation=self.orientation)
        prt.Preview()

    def Imprimer(self, event=None):
        if hasattr(self, "GetParametresImpression") :
            dictParametres = self.GetParametresImpression()
            if "titre" in dictParametres: self.titre = dictParametres["titre"]
            if "intro" in dictParametres: self.impression_intro = dictParametres["intro"]
            if "total" in dictParametres: self.impression_total = dictParametres["total"]
            if "orientation" in dictParametres: self.orientation = dictParametres["orientation"]

        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=self.titre, intro=self.impression_intro, total=self.impression_total, format="A", orientation=self.orientation)
        prt.Print()

    def ExportTexte(self, event=None):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(self, titre=self.titre)

    def ExportExcel(self, event=None):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=self.titre)

    def EnvoyerMail(self, event=None):
        from Dlg import DLG_Liste_envoi_email
        dlg = DLG_Liste_envoi_email.Dialog(self, listview=self)
        dlg.ShowModal()
        dlg.Destroy()

class ColumnDefn(OLV.ColumnDefn):
    def __init__(self, *args, **kwargs):
        self.visible = kwargs.pop("visible", True)
        self.typeDonnee = kwargs.pop("typeDonnee", None)
        OLV.ColumnDefn.__init__(self, *args, **kwargs)

# -----------------------------------------------------------------------------------------------
        
class AbstractVirtualObjectListView(Abstract, ObjectListView):
    def __init__(self, *args, **kwargs):
        self.lastGetObjectIndex = -1
        self.lastGetObject = None
        self.objectGetter = None
        self.listItemAttr = None
        #self.cacheHit = 0
        #self.cacheMiss = 0

        self.SetObjectGetter(kwargs.pop("getter", None))

        # We have to set the item count after the list has been created
        if "count" in kwargs:
            wx.CallAfter(self.SetItemCount, kwargs.pop("count"))

        # Virtual lists have to be in report format
        kwargs["style"] = kwargs.get("style", 0) | wx.LC_REPORT | wx.LC_VIRTUAL

        ObjectListView.__init__(self, *args, **kwargs)

    def SetItemCount(self, count):
        """
        Change the number of items visible in the list
        """
        wx.ListCtrl.SetItemCount(self, count)
        if 'phoenix' not in wx.PlatformInfo:
            self.stEmptyListMsg.Show(count == 0)
        self.lastGetObjectIndex = -1

class FastObjectListView(OLV.FastObjectListView, AbstractVirtualObjectListView):
    def __init__(self, *args, **kwargs):
        AbstractVirtualObjectListView.__init__(self, *args, **kwargs)
        self.SetObjectGetter(lambda index: self.innerList[index])

    def AddObjects(self, modelObjects):
        super(FastObjectListView, self).AddObjects(modelObjects)

        # MAJ Footer
        if self.ctrl_footer :
            self.MAJ_footer()


    def RepopulateList(self):
        super(FastObjectListView, self).RepopulateList()
        
        # MAJ Footer
        if self.ctrl_footer :
            self.MAJ_footer()

    def RefreshObjects(self, aList=None):
        super(FastObjectListView, self).RefreshObjects(aList)

        # MAJ Footer
        if self.ctrl_footer :
            self.MAJ_footer()

class GroupListView(OLV.GroupListView, FastObjectListView):
    def __init__(self, *args, **kwargs):
        self.groups = list()
        self.showGroups = True
        self.putBlankLineBetweenGroups = True
        self.alwaysGroupByColumnIndex = -1
        self.useExpansionColumn = kwargs.pop("useExpansionColumn", True)
        self.showItemCounts = kwargs.pop("showItemCounts", True)
        FastObjectListView.__init__(self, *args, **kwargs)

        # Setup default group characteristics
        font = self.GetFont()
        self.groupFont = wx.FFont(
            font.GetPointSize(),
            font.GetFamily(),
            wx.FONTFLAG_BOLD,
            font.GetFaceName())
        self.groupTextColour = wx.Colour(33, 33, 33, 255)
        self.groupBackgroundColour = wx.Colour(159, 185, 250, 249)

        self._InitializeImages()

    def SetColumns(self, columns, repopulate=True):
        newColumns = columns[:]
        # Insert the column used for expansion and contraction (if one isn't already there)
        if self.showGroups and self.useExpansionColumn and len(newColumns) > 0:
            if not isinstance(newColumns[0], ColumnDefn) or not newColumns[0].isInternal:
                newColumns.insert(0, ColumnDefn("", fixedWidth=24, isEditable=False))
                newColumns[0].isInternal = True
        FastObjectListView.SetColumns(self, newColumns, repopulate)

    def SortGroups(self, groups=None, ascending=None):
        """
        Sort the given collection of groups in the given direction (defaults to ascending).

        The model objects within each group will be sorted as well
        """
        if groups is None:
            groups = self.groups
        if ascending is None:
            ascending = self.sortAscending

        # If the groups are locked, we sort by the sort column, otherwise by the grouping column.
        # The primary column is always used as a secondary sort key.
        if self.GetAlwaysGroupByColumn():
            sortCol = self.GetSortColumn()
        else:
            sortCol = self.GetGroupByColumn()

        # Let the world have a change to sort the items
        evt = OLVEvent.SortGroupsEvent(self, groups, sortCol, ascending)
        self.GetEventHandler().ProcessEvent(evt)
        if evt.wasHandled:
            return

        # Sorting event wasn't handled, so we do the default sorting
        def _getLowerCaseKey(group):
            key = group.key
            if type(key) == datetime.date :
                key = str(key)
            try:
                return key.lower()
            except:
                return key

        groups = sorted(groups, key=_getLowerCaseKey,
                        reverse=(not ascending))
        # update self.groups which is used e.g. in _SetGroups
        self.groups = groups

        # Sort the model objects within each group.
        for x in groups:
            self._SortObjects(x.modelObjects, sortCol, self.GetPrimaryColumn())

# -----------------------------------------------------------------------------------------------

class PanelAvecFooter(wx.Panel):
    def __init__(self, parent, listview=None, kwargs={}, dictColonnes={}, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL):
        wx.Panel.__init__(self, parent, id=-1, style=style)
        
        # Contr�les
        kwargs["parent"] = self
##        if kwargs.has_key("parent") == False : kwargs["parent"] = self # BUG ICI
        if ("id" in kwargs) == False : kwargs["id"] = -1
        if ("style" in kwargs) == False : kwargs["style"] = wx.LC_REPORT|wx.NO_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES
        
        self.ctrl_listview = listview(**kwargs)
        self.ctrl_listview.SetMinSize((10, 10)) 
        self.ctrl_footer = CTRL_Footer.Footer(self)
        self.ctrl_listview.SetFooter(ctrl=self.ctrl_footer, dictColonnes=dictColonnes)
        
        # Layout
        sizerbase = wx.BoxSizer(wx.VERTICAL)
        sizerbase.Add(self.ctrl_listview, 1, wx.ALL|wx.EXPAND, 0)
        sizerbase.Add(self.ctrl_footer, 0, wx.ALL|wx.EXPAND, 0)
        self.SetSizer(sizerbase)
        self.Layout()
        
    def GetListview(self):
        return self.ctrl_listview

class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent, listview, texteDefaut=u"Rechercher..."):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1),
                               style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.listview = listview
        self.oldTxt = ''

        # Assigne cette barre de recherche au listview
        self.listview.SetBarreRecherche(self)

        self.SetDescriptiveText(texteDefaut)
        self.ShowSearchButton(True)

        self.SetCancelBitmap(wx.Bitmap(
            Chemins.GetStaticPath("Images/16x16/Interdit.png"),
            wx.BITMAP_TYPE_PNG))
        self.SetSearchBitmap(wx.Bitmap(
            Chemins.GetStaticPath("Images/16x16/Loupe.png"),
            wx.BITMAP_TYPE_PNG))

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.Recherche, self.timer)

        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnDoSearch)
        self.Bind(wx.EVT_TEXT, self.OnDoSearch)

    def OnSearch(self, evt):
        self.Recherche()

    def OnCancel(self, evt):
        self.SetValue("")
        self.Recherche()

    def OnDoSearch(self, evt):
        if self.timer.IsRunning():
            self.timer.Stop()
        if len(self.listview.GetObjects()) < 500:
            duree = 10
        elif len(self.listview.GetObjects()) < 1000:
            duree = 200
        elif len(self.listview.GetObjects()) < 5000:
            duree = 500
        else:
            duree = 1000
        self.timer.Start(duree)

    def Cancel(self):
        self.OnCancel(None)

    def Recherche(self, event=None):
        if self.timer.IsRunning():
            self.timer.Stop()
        txtSearch = self.GetValue()
        if txtSearch != self.oldTxt:
            self.ShowCancelButton(len(txtSearch))
            self.listview.Filtrer(txtSearch)
            self.oldTxt = txtSearch

class CTRL_Regroupement(wx.Choice):
    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1)
        self.parent = parent
        self.listview = None
        self.listeLabels = []
        self.dictDonnees = {}

    def MAJ(self, listview=None):
        if self.listview == None:
            self.listview = listview
            self.Bind(wx.EVT_CHOICE, self.OnChoix, self)
            self.listview = listview

        if self.listeLabels == []:
            self.dictDonnees = {}
            self.listeLabels = ["Aucun", ]
            indexColonne = 0
            indexLigne = 1
            for titre in self.GetTitresColonnes(listview):
                if titre not in ("ID", ""):
                    self.listeLabels.append(titre)
                    self.dictDonnees[indexLigne] = indexColonne
                    indexLigne += 1
                indexColonne += 1
            self.SetItems(self.listeLabels)
            self.Select(0)

    def GetTitresColonnes(self, listview=None):
        listeColonnes = []
        for index in range(0, listview.GetColumnCount()):
            listeColonnes.append(listview.columns[index].title)
        return listeColonnes

    def GetRegroupement(self):
        index = self.GetSelection()
        if index == -1 or index == 0: return None
        indexColonne = self.dictDonnees[index]
        return indexColonne

    def OnChoix(self, event=None):
        self.listview.regroupement = self.GetRegroupement()
        self.listview.MAJ()

class CTRL_Outils(wx.Panel):
    def __init__(self, parent, listview=None, texteDefaut=u"Rechercher...",
                 afficherCocher=False, afficherRegroupement=False,
                 style=wx.NO_BORDER | wx.TAB_TRAVERSAL):
        wx.Panel.__init__(self, parent, id=-1, style=style)
        self.listview = listview
        self.afficherRegroupement = afficherRegroupement

        # Contr�les
        self.barreRecherche = BarreRecherche(self, listview=listview,
                                             texteDefaut=texteDefaut)
        ##        self.bouton_filtrage = wx.Button(self, -1, "Filtrage avanc�", size=(-1, 20))
        ##        self.bouton_filtrage = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/BoutonsImages/Filtrer_liste_2.png"), wx.BITMAP_TYPE_ANY))

        import wx.lib.platebtn as platebtn

        # Bouton Filtrer
        self.bouton_filtrer = platebtn.PlateButton(self, -1, " Filtrer",
                                                   wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Filtre.png"), wx.BITMAP_TYPE_ANY))

        self.bouton_filtrer.SetToolTip(
            wx.ToolTip("Cliquez ici pour filtrer cette liste"))

        menu = wx.Menu()
        item = wx.MenuItem(menu, 10,
                           "Ajouter, modifier ou supprimer des filtres",
                           "Cliquez ici pour acc�der � la gestion des filtres de listes")
        item.SetBitmap(wx.Bitmap(
            Chemins.GetStaticPath("Images/16x16/Filtre.png"),
            wx.BITMAP_TYPE_ANY))
        menu.Append(item)
        menu.AppendSeparator()
        item = wx.MenuItem(menu, 11, "Supprimer tous les filtres",
                           "Cliquez ici pour supprimer tous les filtres")
        item.SetBitmap(wx.Bitmap(
            Chemins.GetStaticPath("Images/16x16/Filtre_supprimer.png"),
            wx.BITMAP_TYPE_ANY))
        menu.Append(item)
        self.bouton_filtrer.SetMenu(menu)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonFiltrer, self.bouton_filtrer)

        # Bouton Cocher
        if afficherCocher == True:
            self.bouton_cocher = platebtn.PlateButton(self, -1, " Cocher",
                                                      wx.Bitmap(
                                                          Chemins.GetStaticPath("Images/16x16/Cocher.png"),
                                                          wx.BITMAP_TYPE_ANY))
            self.bouton_cocher.SetToolTip(wx.ToolTip(
                "Cliquez ici pour cocher ou d�cocher rapidement tous les �l�ments de cette liste"))

            menu = wx.Menu()
            item = wx.MenuItem(menu, 20, "Tout cocher",
                               "Cliquez ici pour cocher tous les �l�ments de la liste")
            item.SetBitmap(wx.Bitmap(
                Chemins.GetStaticPath("Images/16x16/Cocher.png"),
                wx.BITMAP_TYPE_ANY))
            menu.Append(item)
            item = wx.MenuItem(menu, 21, "Tout d�cocher",
                               "Cliquez ici pour d�cocher tous les �l�ments de la liste")
            item.SetBitmap(wx.Bitmap(
                Chemins.GetStaticPath("Images/16x16/Decocher.png"),
                wx.BITMAP_TYPE_ANY))
            menu.Append(item)

            item = wx.MenuItem(menu, 22, "Inverser jusqu'� Selection",
                               "Cliquez ici pour inverser les coches jusqu'� la selection")
            item.SetBitmap(wx.Bitmap(
                Chemins.GetStaticPath("Images/16x16/Decocher.png"),
                wx.BITMAP_TYPE_ANY))
            menu.Append(item)

            self.bouton_cocher.SetMenu(menu)
            self.Bind(wx.EVT_BUTTON, self.OnBoutonCocher, self.bouton_cocher)

        self.Bind(wx.EVT_MENU, self.OnMenu)
        self.Bind(wx.EVT_SIZE, self.OnSize)

        # Regroupement
        if self.afficherRegroupement == True:
            self.label_regroupement = wx.StaticText(self, -1,
                                                    "Regroupement :")
            self.ctrl_regroupement = CTRL_Regroupement(self)
            listview.ctrl_regroupement = self.ctrl_regroupement

        # Layout
        sizerbase = wx.BoxSizer(wx.HORIZONTAL)
        sizerbase.Add(self.barreRecherche, 1, wx.ALL | wx.EXPAND, 0)
        sizerbase.Add(self.bouton_filtrer, 0, wx.LEFT | wx.EXPAND, 5)
        if afficherCocher == True:
            sizerbase.Add(self.bouton_cocher, 0, wx.LEFT | wx.EXPAND, 5)
        if self.afficherRegroupement == True:
            sizerbase.Add((20, 5), 0, wx.EXPAND)
            sizerbase.Add(self.label_regroupement, 0,
                          wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
            sizerbase.Add(self.ctrl_regroupement, 0, wx.LEFT | wx.EXPAND, 5)
        self.SetSizer(sizerbase)
        self.Layout()

    def OnSize(self, event):
        self.Refresh()
        event.Skip()

    def MAJ_ctrl_filtrer(self):
        """ Met � jour l'image du bouton Filtrage """
        nbreFiltres = len(self.listview.listeFiltresColonnes)

        # Modifie l'image selon le nbre de filtres activ�s
        if nbreFiltres == 0:
            nomImage = "Filtre"
        elif nbreFiltres < 10:
            nomImage = "Filtre_%d" % nbreFiltres
        else:
            nomImage = "Filtre_10"
        self.bouton_filtrer.SetBitmap(wx.Bitmap(
            Chemins.GetStaticPath("Images/16x16/%s.png" % nomImage),
            wx.BITMAP_TYPE_ANY))
        self.bouton_filtrer.Refresh()

        # Modifie le tip en fonction des filtres activ�s
        if nbreFiltres == 0:
            texte = "Cliquez ici pour filtrer cette liste"
        else:
            if nbreFiltres == 1:
                texte = "Cliquez ici pour filtrer cette liste\n> 1 filtre activ�"
            else:
                texte = "Cliquez ici pour filtrer cette liste\n> %d filtres activ�s" % nbreFiltres
        self.bouton_filtrer.SetToolTip(wx.ToolTip(texte))

    def OnBoutonFiltrer(self, event):
        from Dlg import DLG_Filtres_listes
        dlg = DLG_Filtres_listes.Dialog(self, ctrl_listview=self.listview)
        if dlg.ShowModal() == wx.ID_OK:
            listeFiltres = dlg.GetDonnees()
            self.listview.SetFiltresColonnes(listeFiltres)
            self.listview.Filtrer()
            self.MAJ_ctrl_filtrer()
        dlg.Destroy()

    def SetFiltres(self, listeFiltres=[]):
        self.listview.SetFiltresColonnes(listeFiltres)
        self.listview.Filtrer()
        self.MAJ_ctrl_filtrer()

    def OnBoutonCocher(self, event):
        self.bouton_cocher.ShowMenu()

    def OnMenu(self, event):
        ID = event.GetId()
        # Acc�der � la gestion des filtres
        if ID == 10:
            self.OnBoutonFiltrer(None)
        # Supprimer tous les filtres
        if ID == 11:
            self.listview.SetFiltresColonnes([])
            self.listview.Filtrer()
            self.MAJ_ctrl_filtrer()
            # Tout cocher
        if ID == 20:
            self.listview.CocheListeTout()
        # Tout d�cocher
        if ID == 21:
            self.listview.CocheListeRien()
        # Tout inversion coches
        if ID == 22:
            self.listview.CocheJusqua()



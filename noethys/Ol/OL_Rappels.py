#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys branche Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-13 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import Chemins
import wx
import GestionDB
import wx.lib.agw.pybusyinfo as PBI
import FonctionsPerso
import copy
from Utils import UTILS_Dates
from Utils import UTILS_Utilisateurs
from Utils import UTILS_Titulaires
from Utils import UTILS_Config
from Utils import UTILS_Rappels

SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils, PanelAvecFooter


class Track(object):
    def __init__(self, dict):
        self.__dict__ = copy.deepcopy(dict)
        if not "IDrappel" in dict:
            self.IDrappel = 0
        if "email_factures" in dict:
            if dict["email_factures"] != None:
                self.email = True
        self.email = False

class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        # Initialisation du listCtrl
        self.IDcompte_payeur = kwds.pop("IDcompte_payeur", None)
        self.checkColonne = kwds.pop("checkColonne", False)
        self.codesColonnes = kwds.pop("codesColonnes", [])
        self.codesColonnes = ["IDfamille", "IDtitulaire","nomPrenom", "ville", "solde", "retard", "activite", "rappel", "numero"]
        self.triColonne = kwds.pop("triColonne", 1)
        self.filtres = None
        self.selectionID = None
        self.lstIDfamilles = []
        self.selectionTrack = None
        self.onlyRappels = False
        FastObjectListView.__init__(self,  *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        
    def OnActivated(self,event):
        self.Modifier(None)

    def InitModel(self):
        self.donnees = self.GetTracks()

    def SetFiltres(self, filtres=None):
        self.filtres = filtres

    def GetListeRappels(self):
        # Récupération des impayés et recherche liste des payeurs à relancer
        DB = GestionDB.DB()

        if self.lstIDfamilles != []:
            where = "WHERE (prestations.IDcompte_payeur IN (%s)) AND "%str(self.lstIDfamilles)[1:-1]
        else: where = "WHERE "
        listeIDfamilles = []
        dictComptes = {}
        # Prestations partiellement réglées, puis sans ventilation
        for ventil in (True,False):
            if ventil :
                champ = ", Sum(ventilation.montant) AS mtt_ventil "
                condition = where +" (ventilation.IDventilation Is Not Null)"
                having = "HAVING (((prestations.montant) > mtt_ventil))"
            else:
                champ = ", 0.0 "
                condition = where + "(ventilation.IDventilation Is Null)"
                having = ""
            req = """
            SELECT prestations.IDcompte_payeur, prestations.IDprestation, prestations.Date, prestations.montant %s 
            FROM prestations 
            LEFT JOIN ventilation ON prestations.IDprestation = ventilation.IDprestation
            %s
            GROUP BY prestations.IDcompte_payeur, prestations.IDprestation, prestations.Date, prestations.montant
            %s
            ;""" %(champ,condition,having)
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            listeDus = DB.ResultatReq()
            for IDfamille, IDprestation, minDatePrest , mttPrestations, ventPrestations in listeDus:
                if mttPrestations != 0 :
                    if not IDfamille in listeIDfamilles:
                        listeIDfamilles.append(IDfamille)
                    if IDfamille not in dictComptes:
                        dictComptes[IDfamille]={}
                        dictComptes[IDfamille]["IDfamille"]= IDfamille
                        dictComptes[IDfamille]["solde"] = 0.0
                        dictComptes[IDfamille]["minDatePrest"]= "2199-12-01"
                        dictComptes[IDfamille]["lastRappel"]= None
                        dictComptes[IDfamille]["numero"]= None
                        dictComptes[IDfamille]["IDrappel"]= None
                        dictComptes[IDfamille]["lastInscri"]= None
                    dictComptes[IDfamille]["solde"] += (float(-mttPrestations) + float(ventPrestations))
                    if minDatePrest < dictComptes[IDfamille]["minDatePrest"]:
                        dictComptes[IDfamille]["minDatePrest"]= minDatePrest

        # Recherche dernier rappel
        req = """
            SELECT rappels.IDcompte_payeur, Max(rappels.date_edition), Count(rappels.numero), 
                    Max(rappels.numero),Max(rappels.IDrappel)
            FROM rappels
            WHERE IDcompte_payeur IN ( %s )
            GROUP BY rappels.IDcompte_payeur;
            """ % (str(listeIDfamilles)[1:-1])
        DB.ExecuterReq(req,MsgBox= "OL_Rappels.rappels")
        listeLastRappel = DB.ResultatReq()
        for IDfamille, date,nbRappels,numero,IDrappel in listeLastRappel :
            dictComptes[IDfamille]["lastRappel"]= UTILS_Dates.DateEngEnDateDD(date)
            dictComptes[IDfamille]["nbRappels"]= nbRappels
            dictComptes[IDfamille]["numero"]= numero
            dictComptes[IDfamille]["IDrappel"]= IDrappel

        # purge éventuelle des sans rappel, si lancé par DLG_Rappels_impression
        if self.onlyRappels:
            lstIDtemp = [ x for x in listeIDfamilles]
            for IDfamille in listeIDfamilles:
                if dictComptes[IDfamille]["IDrappel"] == None:
                    del dictComptes[IDfamille]
                    lstIDtemp.remove(IDfamille)
            listeIDfamilles = lstIDtemp

        # Recherche identité des titulaires des familles
        req = """SELECT lst.IDfamille, individus.IDindividu, individus.nom, individus.prenom, individus.ville_resid, individus_1.ville_resid
                FROM (
                    SELECT familles.IDfamille, Max(rattachements.IDindividu) AS lstIndivi
                    FROM familles INNER JOIN rattachements ON familles.IDfamille = rattachements.IDfamille
                    WHERE (((rattachements.titulaire)=1) AND ((familles.IDfamille) In ( %s )))
                    GROUP BY familles.IDfamille
                    ) as lst
                INNER JOIN individus ON lst.lstIndivi = individus.IDindividu
                LEFT JOIN individus AS individus_1 ON individus.adresse_auto = individus_1.IDindividu
                ;"""  % str(listeIDfamilles)[1:-1]
        ok = DB.ExecuterReq(req,MsgBox = "OL_Rappels.titulaires")
        listeTitulaires = DB.ResultatReq()
        listeIDtitulaires = []
        for IDfamille, IDindividu, nom, prenom, ville, villeAuto in listeTitulaires:
            listeIDtitulaires.append(IDindividu)
            dictComptes[IDfamille]["IDtitulaire"]= IDindividu
            dictComptes[IDfamille]["nomPrenom"]= nom + " " + prenom
            if  ville != None :
                dictComptes[IDfamille]["ville"]= ville
            else:
                dictComptes[IDfamille]["ville"]= villeAuto

        # Recherche dernière activité inscrite
        req = """SELECT inscriptions.IDfamille, Max(activites.abrege)
                FROM inscriptions
                INNER JOIN activites ON inscriptions.IDactivite = activites.IDactivite
                INNER JOIN prestations ON activites.IDactivite = prestations.IDactivite
                WHERE inscriptions.IDfamille IN ( %s ) AND NOT (prestations.IDfacture IS NULL)
                GROUP BY inscriptions.IDfamille;
                """ % str(listeIDfamilles)[1:-1]
        ok= DB.ExecuterReq(req,MsgBox="OL_Rappels.activite")
        listeLastInscri = DB.ResultatReq()
        for IDfamille, abrege in listeLastInscri :
            dictComptes[IDfamille]["lastInscri"]= abrege

        DB.Close()
        # actualisation de la liste dans parent.dicParametres
        self.lstIDfamilles = listeIDfamilles
        return dictComptes

    def GetTracks(self):
        # Récupération des données
        dictComptes = self.GetListeRappels()
        listeListeView = []
        listeDus = list(dictComptes.keys())
        for IDfamille in listeDus :
            track = Track(dictComptes[IDfamille])
            listeListeView.append(track)
            if self.selectionID == IDfamille :
                self.selectionTrack = track
        return listeListeView

    def InitObjectListView(self):
        # ImageList
        self.imgEmail = self.AddNamedImages("email", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Emails_exp.png"), wx.BITMAP_TYPE_PNG))

        def GetImageEmail(track):
            if track.email == True :
                return self.imgEmail
        
        def FormateNumero(numero):
            return "%06d" % numero

        def FormateDate(dateDD):
            if dateDD == None : return ""
            return UTILS_Dates.DateEngFr(str(dateDD))

        def FormateMontant(montant):
            if montant == None or montant == "" : return ""
            return "%.2f %s" % (montant, SYMBOLE)
                   
        def rowFormatter(listItem, track):
            if track.valide == False :
                listItem.SetTextColour(wx.Colour(150, 150, 150))
                
        # Couleur en alternance des lignes
        self.oddRowsBackColor = wx.Colour(255, 255, 255) #"#EEF4FB" # Bleu
        self.evenRowsBackColor = "#F0FBED" # Vert

        # Paramètres ListView
        self.useExpansionColumn = True

        dictColonnes = {
            "IDfamille" : ColumnDefn("", "left", 0, "IDfamille", typeDonnee="entier"),
            "IDtitulaire" : ColumnDefn("Ind.", "left", 50, "IDtitulaire", typeDonnee="entier"),
            "nomPrenom" : ColumnDefn(_("Titulaire"), "left", 180, "nomPrenom", typeDonnee="texte"),
            "ville" : ColumnDefn(_("Ville"), "left", 100, "ville", typeDonnee="texte"),
            "solde" : ColumnDefn(_("Solde"), "right", 80, "solde", typeDonnee="montant", stringConverter=FormateMontant),
            "retard" : ColumnDefn(_("Retard"), "centre", 80, "minDatePrest", typeDonnee="date", stringConverter=FormateDate),
            "activite" : ColumnDefn(_("Activité"), "centre", 80, "lastInscri", typeDonnee="texte"),
            "rappel" : ColumnDefn(_("Rappelé"), "centre", 80, "lastRappel", typeDonnee="date", stringConverter=FormateDate),
            "numero" : ColumnDefn("No", "left", 60, "numero", typeDonnee="entier"),
            }

        listeColonnes = []
        tri = None
        index = 0
        for codeColonne in self.codesColonnes :
            listeColonnes.append(dictColonnes[codeColonne])
            # Checkbox 
            if codeColonne == self.triColonne :
                tri = index
            index += 1
        
        self.SetColumns(listeColonnes)
        if self.checkColonne == True :
            self.CreateCheckStateColumn(0)
        if tri != None :
            if self.checkColonne == True : tri += 1
            self.SetSortColumn(self.columns[tri])

        self.SetEmptyListMsg(_("Aucune lettre de rappel"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, faceName="Tekton"))
        self.SetObjects(self.donnees)
            
    def MAJ(self, ID=None):
        if ID != None :
            self.selectionID = ID
            self.selectionTrack = None
        else:
            self.selectionID = None
            self.selectionTrack = None

        self.InitModel()
        self.InitObjectListView()
        # Sélection d'un item
        if self.selectionTrack != None :
            self.SelectObject(self.selectionTrack, deselectOthers=True, ensureVisible=True)
        self.selectionID = None
        self.selectionTrack = None
        # MAJ du total du panel
        try :
            if self.GetParent().GetName() == "panel_prestations" :
                self.GetParent().MAJtotal()
        except :
            pass
    
    def Selection(self):
        return self.GetSelectedObjects()
    
    def DefilePremier(self):
        if len(self.GetObjects()) > 0 :
            self.EnsureCellVisible(0, 0)

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        #if len(self.Selection()) > 0 :
        #    ID = self.Selection()[0].IDrappel
        
        # Création du menu contextuel
        menuPop = wx.Menu()


        # Item Rééditer la lettre
        item = wx.MenuItem(menuPop, 60, _("Aperçu PDF de la lettre de rappel"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Reedition, id=60)

        # Item Envoyer la lettre par Email
        item = wx.MenuItem(menuPop, 90, _("Envoyer la lettre de rappel par Email"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Emails_exp.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.EnvoyerEmail, id=90)
        
        menuPop.AppendSeparator()


        # Item Supprimer
        item = wx.MenuItem(menuPop, 30, _("Supprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Supprimer, id=30)
        if len(self.Selection()) == 0 and len(self.GetTracksCoches()) == 0 : item.Enable(False)

        menuPop.AppendSeparator()


        # Appel de la famille
        item = wx.MenuItem(menuPop, 35, _("Accéder à la famille"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Famille.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.OuvrirFicheFamille, id=35)

        menuPop.AppendSeparator()

        if self.checkColonne == True :
            
            # Item Tout cocher
            item = wx.MenuItem(menuPop, 70, _("Tout cocher"))
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.CocheTout, id=70)

            # Item Tout décocher
            item = wx.MenuItem(menuPop, 80, _("Tout décocher"))
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.CocheRien, id=80)

            menuPop.AppendSeparator()

        # Item Apercu avant impression
        item = wx.MenuItem(menuPop, 40, _("Aperçu avant impression"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=40)
        
        # Item Imprimer
        item = wx.MenuItem(menuPop, 50, _("Imprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=50)
        
        menuPop.AppendSeparator()
    
        # Item Export Texte
        item = wx.MenuItem(menuPop, 600, _("Exporter au format Texte"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Texte2.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.ExportTexte, id=600)
        
        # Item Export Excel
        item = wx.MenuItem(menuPop, 700, _("Exporter au format Excel"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Excel.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.ExportExcel, id=700)

        self.PopupMenu(menuPop)
        menuPop.Destroy()
    
    def Reedition(self, event):
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune lettre à imprimer !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDfamille = self.Selection()[0].IDfamille
        facturation = UTILS_Rappels.Facturation(lstIDfamille=[IDfamille,])
        facturation.Impression()
    
    def EnvoyerEmail(self, event):
        """ Envoyer la lettre par Email """
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune lettre de rappel à envoyer par Email !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]
        # Envoi du mail
        from Utils import UTILS_Envoi_email
        from Utils import UTILS_Fichiers
        nomDoc = UTILS_Fichiers.GetRepTemp("RAPPEL%s.pdf" % FonctionsPerso.GenerationIDdoc())
        UTILS_Envoi_email.EnvoiEmailFamille(parent=self, IDfamille=track.IDfamille, nomDoc=nomDoc, categorie="rappel")
    
    def CreationPDF(self, nomDoc="", afficherDoc=True):        
        """ Création du PDF pour Email """
        IDfamille = self.Selection()[0].IDfamille
        facturation = UTILS_Rappels.Facturation(lstIDfamille=[IDfamille,])
        resultat = facturation.Impression(nomDoc=nomDoc, afficherDoc=False)
        if resultat == False : 
            return False
        dictChampsFusion, dictPieces = resultat
        return dictChampsFusion[IDfamille]

    def GetTextesImpression(self):
        total = _("%d factures. ") % len(self.donnees)
        if self.filtres != None :
            from Dlg.DLG_Filtres_rappels import GetTexteFiltres 
            intro = total + _("Filtres de sélection : %s") % GetTexteFiltres(self.filtres)
        else :
            intro = None
        return intro, total

    def Apercu(self, event=None):
        from Utils import UTILS_Printer
        txtIntro, txtTotal = self.GetTextesImpression()
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des lettres de rappel"), intro=txtIntro, total=txtTotal, format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event=None):
        from Utils import UTILS_Printer
        txtIntro, txtTotal = self.GetTextesImpression()
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des lettres de rappel"), intro=txtIntro, total=txtTotal, format="A", orientation=wx.PORTRAIT)
        prt.Print()

    def ExportTexte(self, event=None):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(self, titre=_("Liste des lettres de rappel"))
        
    def ExportExcel(self, event=None):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=_("Liste des lettres de rappel"))

    def CocheTout(self, event=None):
        if self.GetFilter() != None :
            listeObjets = self.GetFilteredObjects()
        else :
            listeObjets = self.GetObjects()
        for track in listeObjets :
            self.Check(track)
            self.RefreshObject(track)
        
    def CocheRien(self, event=None):
        for track in self.donnees :
            self.Uncheck(track)
            self.RefreshObject(track)

    def GetTracksCoches(self):
        return self.GetCheckedObjects()
    
    def GetTracksTous(self):
        return self.donnees
        
    def Supprimer(self, event):
        if self.IDcompte_payeur == None and UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("facturation_rappels", "supprimer") == False : return
        
        if len(self.Selection()) == 0 and len(self.GetTracksCoches()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune lettre de rappel à supprimer dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        
        if len(self.GetTracksCoches()) > 0 :
            # Suppression multiple
            listeSelections = self.GetTracksCoches()
            dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer les %d lettres de rappel cochées ?") % len(listeSelections), _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
            reponse = dlg.ShowModal() 
            dlg.Destroy()
            if reponse != wx.ID_YES :
                return
        
        else :
            # Suppression unique
            listeSelections = self.Selection()        
            dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer la lettre de rappel n°%d ?") % listeSelections[0].numero, _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
            reponse = dlg.ShowModal() 
            dlg.Destroy()
            if reponse != wx.ID_YES :
                return
        
        # Suppression des lettres de rappel
        listeIDrappels = []
        for track in listeSelections :
            listeIDrappels.append(track.IDrappel)

        dlgAttente = PBI.PyBusyInfo(_("Suppression des lettres de rappel en cours..."), parent=None, title=_("Veuillez patienter..."), icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
        wx.Yield() 
        DB = GestionDB.DB()
        for IDrappel in listeIDrappels :
            DB.ReqDEL("rappels", "IDrappel", IDrappel)
        DB.Close() 
        del dlgAttente
        
        # MAJ du listeView
        self.MAJ() 
        
        # Confirmation de suppression
        dlg = wx.MessageDialog(self, _("%d lettres(s) de rappel supprimée(s) avec succès.") % len(listeSelections), _("Suppression"), wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def OuvrirFicheFamille(self,event):
        # Ouverture de la fiche famille
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune fiche famille à ouvrir !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDfamille = self.Selection()[0].IDfamille
        from Dlg import DLG_Famille
        dlg = DLG_Famille.Dialog(self, IDfamille)
        if dlg.ShowModal() == wx.ID_OK:
            self.MAJ()
        dlg.Destroy()

# -------------------------------------------------------------------------------------------------------------------------------------------
class ListviewAvecFooter(PanelAvecFooter):
    def __init__(self, parent, kwargs={}):
        dictColonnes = {
            "nomPrenom" : {"mode" : "nombre", "singulier" : "ligne", "pluriel" : "lignes", "alignement" : wx.ALIGN_CENTER},
            "solde" : {"mode" : "total"},
            }
        PanelAvecFooter.__init__(self, parent, ListView, kwargs, dictColonnes)

# ----------------- FRAME DE TEST ----------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)

        IDcompte_payeur = None
        checkColonne = True
        triColonne = "numero"

        self.myOlv = ListView(panel, -1, IDcompte_payeur=IDcompte_payeur,  checkColonne=checkColonne, triColonne=triColonne, style=wx.LC_HRULES|wx.LC_VRULES|wx.LC_REPORT|wx.SUNKEN_BORDER)
        self.myOlv.MAJ() 
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.myOlv, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.SetSize((800, 400))
        self.Layout()


if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "FastObjectListView")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()

#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys branche Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import Chemins
from Utils.UTILS_Traduction import _
import wx
import datetime
import GestionDB
from Utils import UTILS_Historique
from Utils import UTILS_Dates
from Utils import UTILS_Interface
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter
from Dlg.DLG_Inscription import STATUTS

from Utils import UTILS_Utilisateurs

class Track(object):
    def __init__(self, parent, donnees):
        self.IDinscription = donnees[0]
        self.IDindividu = donnees[1]
        self.IDfamille = donnees[2]
        self.IDactivite = donnees[3]
        self.IDgroupe = donnees[4]
        self.IDcategorie_tarif = donnees[5]
        self.date_inscription = donnees[6]
        self.nom_activite = donnees[7]
        self.nom_groupe = donnees[8]
        self.nom_categorie = donnees[9]
        self.date_desinscription = UTILS_Dates.DateEngEnDateDD(donnees[10])
        self.date_debut = UTILS_Dates.DateEngEnDateDD(donnees[11])
        self.date_fin = UTILS_Dates.DateEngEnDateDD(donnees[12])
        self.statut = donnees[13]

        # Nom des titulaires de famille
        self.nomTitulaires = _("IDfamille n°%d") % self.IDfamille
        if parent.dictFamillesRattachees != None :
            if self.IDfamille in parent.dictFamillesRattachees : 
                self.nomTitulaires = parent.dictFamillesRattachees[self.IDfamille]["nomsTitulaires"]

        # Validité de la pièce
        if (datetime.date.today() <= self.date_fin and (self.date_desinscription is None or self.date_desinscription >= datetime.date.today())):
            self.valide = True
        else:
            self.valide = False

class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        # Récupération des paramètres perso
        self.IDindividu = kwds.pop("IDindividu", None)
        self.dictFamillesRattachees = kwds.pop("dictFamillesRattachees", {} )
        self.activeDoubleclick = kwds.pop("activeDoubleclick", True)
        self.nbreFamilles = 0
        self.selectionID = None
        self.selectionTrack = None
        self.criteres = ""
        self.itemSelected = False
        self.popupIndex = -1
        self.listeFiltres = []
##        self.GetLogoOrganisateur()
        # Initialisation du listCtrl
        self.nom_fichier_liste = __file__
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

    def OnItemActivated(self,event):
        if self.activeDoubleclick :
            self.Modifier(None)
                
    def InitModel(self):
        self.donnees = self.GetTracks()

    def GetTracks(self):
        """ Récupération des données """
        listeID = None
        DB = GestionDB.DB()
        req = """
            SELECT IDinscription, IDindividu, IDfamille, 
                inscriptions.IDactivite, inscriptions.IDgroupe, 
                inscriptions.IDcategorie_tarif, date_inscription, 
                activites.nom, groupes.nom, categories_tarifs.nom,
                inscriptions.date_desinscription, activites.date_debut, activites.date_fin,
                inscriptions.statut
            FROM inscriptions 
            LEFT JOIN activites ON inscriptions.IDactivite=activites.IDactivite
            LEFT JOIN groupes ON inscriptions.IDgroupe=groupes.IDgroupe
            LEFT JOIN categories_tarifs ON inscriptions.IDcategorie_tarif=categories_tarifs.IDcategorie_tarif
            WHERE IDindividu=%d
            ORDER BY activites.nom; """ % self.IDindividu
        DB.ExecuterReq(req,MsgBox="OL_Inscriptions")
        listeDonnees = DB.ResultatReq()
        DB.Close()

        listeListeView = []
        listeIDfamilles = []
        for item in listeDonnees :
            IDfamille = item[2]
            if IDfamille not in listeIDfamilles :
                listeIDfamilles.append(IDfamille)
            valide = True
            if listeID != None :
                if item[0] not in listeID :
                    valide = False
            if valide == True :
                track = Track(self, item)
                listeListeView.append(track)
                if self.selectionID == item[0] :
                    self.selectionTrack = track

        self.nbreFamilles = len(listeIDfamilles)
        return listeListeView
      
    def InitObjectListView(self):            
        # Couleur en alternance des lignes
        self.oddRowsBackColor = UTILS_Interface.GetValeur("couleur_tres_claire", wx.Colour(240, 251, 237))
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True

        # Ajoute les images des statuts
        for dictStatut in STATUTS :
            self.AddNamedImages(dictStatut["code"], wx.Bitmap(Chemins.GetStaticPath("Images/16x16/%s" % dictStatut["image"]), wx.BITMAP_TYPE_PNG))


        # Création du imageList avec une taille personnalisée
##        dictImages = {}
##        imageList = wx.ImageList(TAILLE_IMAGE[0], TAILLE_IMAGE[1])
##        for track in self.donnees :
##            indexImg = imageList.Add(track.bmp)
##            dictImages[track.IDactivite] = indexImg
##        self.SetImageLists(imageList, imageList)

##        def GetLogo(track):
##            if dictImages.has_key(track.IDactivite) :
##                return dictImages[track.IDactivite]
##            else :
##                return None

        def DateEngFr(textDate):
            if textDate != None :
                text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
            else:
                text = ""
            return text

        def FormateStatut(statut):
            for dictStatut in STATUTS :
                if dictStatut["code"] == statut :
                    return dictStatut["label_court"]
            return ""

        def GetImageStatut(track):
            if track.statut == "ok" :
                return "ok"
            elif track.statut == "attente" :
                return "attente"
            elif track.statut == "refus" :
                return "refus"
            else :
                return None

        def rowFormatter(listItem, track):
            if track.valide == False :
                listItem.SetTextColour((180, 180, 180))

        if self.nbreFamilles > 1 :
            liste_Colonnes = [
                ColumnDefn(_("ID"), "left", 0, "IDinscription", typeDonnee="entier"),
                # ColumnDefn(u"", 'left', TAILLE_IMAGE[0]+1, "", imageGetter=GetLogo),
                ColumnDefn(_("Date"), 'center', 70, "date_inscription", typeDonnee="date", stringConverter=DateEngFr),
                ColumnDefn(_("Statut"), 'left', 70, "statut", typeDonnee="texte", stringConverter=FormateStatut, imageGetter=GetImageStatut),
                ColumnDefn(_("Nom de l'activité"), 'left', 110, "nom_activite", typeDonnee="texte", isSpaceFilling=True),
                ColumnDefn(_("Groupe"), 'left', 80, "nom_groupe", typeDonnee="texte"),
                ColumnDefn(_("Catégorie de tarifs"), 'left', 110, "nom_categorie", typeDonnee="texte"),
                ColumnDefn(_("Famille"), 'left', 110, "nomTitulaires", typeDonnee="texte"),
                ]
        else:
            liste_Colonnes = [
                ColumnDefn(_("ID"), "left", 0, "IDinscription", typeDonnee="entier"),
                # ColumnDefn(u"", 'left', TAILLE_IMAGE[0]+1, "", imageGetter=GetLogo),
                ColumnDefn(_("Date"), 'center', 70, "date_inscription", typeDonnee="date", stringConverter=DateEngFr),
                ColumnDefn(_("Statut"), 'left', 70, "statut", typeDonnee="texte", stringConverter=FormateStatut, imageGetter=GetImageStatut),
                ColumnDefn(_("Nom de l'activité"), 'left', 160, "nom_activite", typeDonnee="texte", isSpaceFilling=True),
                ColumnDefn(_("Groupe"), 'left', 100, "nom_groupe", typeDonnee="texte"),
                ColumnDefn(_("Catégorie de tarifs"), 'left', 140, "nom_categorie", typeDonnee="texte"),
                ]

        self.rowFormatter = rowFormatter
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_("Aucune activité"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, faceName="Tekton"))
        self.SetSortColumn(self.columns[1])
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
        self._ResizeSpaceFillingColumns() 
    
    def Selection(self):
        return self.GetSelectedObjects()

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        if len(self.Selection()) == 0:
            noSelection = True
        else:
            noSelection = False
            ID = self.Selection()[0].IDinscription
                
        # Création du menu contextuel
        menuPop = wx.Menu()

        # Item Modifier
        item = wx.MenuItem(menuPop, 10, _("Ajouter"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Ajouter, id=10)

        # Item Ajouter
        item = wx.MenuItem(menuPop, 20, _("Modifier"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Modifier, id=20)
        if noSelection == True : item.Enable(False)
        
        # Item Supprimer
        item = wx.MenuItem(menuPop, 30, _("Supprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Supprimer, id=30)
        if noSelection == True : item.Enable(False)
                
        menuPop.AppendSeparator()

        # Item Imprimer
        item = wx.MenuItem(menuPop, 60,
                           _("Editer une confirmation d'inscription (PDF)"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.EditerConfirmation, id=60)
        if noSelection == True : item.Enable(False)

        menuPop.AppendSeparator()

        # Item Envoyer par Email
        item = wx.MenuItem(menuPop, 40, _("Aperçu avant impression"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Emails_exp.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=40)

        # Item Imprimer
        item = wx.MenuItem(menuPop, 50, _("Imprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("ImagesImages/16x16/Imprimante.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=50)
        
        menuPop.AppendSeparator()

        # Génération automatique des fonctions standards
        self.GenerationContextMenu(menuPop, titre=_("Liste des inscriptions"))

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Ajouter(self, event):
        # Recherche si l'individu est rattaché à d'autres familles
        listeNoms = []
        listeFamille = []
        # Vérifie que l'individu est rattaché comme REPRESENTANT ou ENFANT à une famille
        if self.dictFamillesRattachees != None :
            valide = False
            for IDfamille, dictFamille in self.dictFamillesRattachees.items() :
                if dictFamille["IDcategorie"] in (1, 2) :
                    valide = True
            if valide == False :
                dlg = wx.MessageDialog(self, _("Pour être inscrit à une activité, un individu doit obligatoirement être\nrattaché comme représentant ou enfant à une fiche famille !"), _("Inscription impossible"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return
        
        if len(self.dictFamillesRattachees) == 1 :
            IDfamille = list(self.dictFamillesRattachees.keys())[0]
            listeFamille.append(IDfamille)
            listeNoms.append(self.dictFamillesRattachees[IDfamille]["nomsTitulaires"])
        else:
            # Si rattachée à plusieurs familles
            for IDfamille, dictFamille in self.dictFamillesRattachees.items() :
                IDcategorie = dictFamille["IDcategorie"]
                if IDcategorie in (1, 2) :
                    listeFamille.append(IDfamille)
                    listeNoms.append(dictFamille["nomsTitulaires"])
                
            if len(listeFamille) == 1 :
                IDfamille = listeFamille[0]
            else:
                # On demande à quelle famille rattacher cette inscription
                dlg = wx.SingleChoiceDialog(self, _("Cet individu est rattaché à %d familles.\nA quelle famille souhaitez-vous rattacher cette inscription ?") % len(listeNoms), _("Rattachements multiples"), listeNoms, wx.CHOICEDLG_STYLE)
                if dlg.ShowModal() == wx.ID_OK:
                    indexSelection = dlg.GetSelection()
                    IDfamille = listeFamille[indexSelection]
                    dlg.Destroy()
                else:
                    dlg.Destroy()
                    return
        
        # Recherche de la ville de l'individu pour sélection auto de la catégorie de tarif
        cp, ville = None, None
        try :
            dictAdresse = self.GetGrandParent().GetPageAvecCode("coords").GetAdresseIndividu()
            cp = dictAdresse["cp"]
            ville = dictAdresse["ville"]
        except :
            pass

        # Ouverture de la fenêtre d'inscription
        from Dlg import DLG_Inscription
        dlg = DLG_Inscription.Dialog(self)
        dlg.SetFamille(listeNoms, listeFamille, IDfamille, False)
        if dlg.ShowModal() == wx.ID_OK:
            IDfamille = dlg.GetIDfamille()
            IDactivite = dlg.GetIDactivite()
            IDgroupe = dlg.GetIDgroupe()
            IDcategorie_tarif = dlg.GetIDcategorie()
            nomActivite = dlg.GetNomActivite()
            nomGroupe = dlg.GetNomGroupe()
            nomCategorie = dlg.GetNomCategorie()
            IDcompte_payeur = self.GetCompteFamille(IDfamille)
            parti = dlg.GetParti()

            # Verrouillage utilisateurs
            if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_inscriptions", "creer", IDactivite=IDactivite) == False :
                return

            # Vérifie que l'individu n'est pas déjà inscrit à cette activite
            for inscription in self.donnees :
                if inscription.IDactivite == IDactivite and inscription.IDfamille == IDfamille :
                    dlg2 = wx.MessageDialog(self, _("Individu déjà inscrit à l'activité '%s' !") % inscription.nom_activite, _("Erreur de saisie"), wx.OK | wx.ICON_ERROR)
                    dlg2.ShowModal()
                    dlg2.Destroy()
                    dlg.Destroy()
                    return

            # Sauvegarde
            DB = GestionDB.DB()
            listeDonnees = [
                ("IDindividu", self.IDindividu ),
                ("IDfamille", IDfamille ),
                ("IDactivite", IDactivite ),
                ("IDgroupe", IDgroupe),
                ("IDcategorie_tarif", IDcategorie_tarif),
                ("IDcompte_payeur", IDcompte_payeur),
                ("date_inscription", str(datetime.date.today()) ),
                ("parti", parti),
                ]
            IDinscription = DB.ReqInsert("inscriptions", listeDonnees)
            DB.Close()

            # Mémorise l'action dans l'historique
            UTILS_Historique.InsertActions([{
                "IDindividu" : self.IDindividu,
                "IDfamille" : IDfamille,
                "IDcategorie" : 18,
                "action" : _("Inscription à l'activité '%s' sur le groupe '%s' avec la tarification '%s'") % (nomActivite, nomGroupe, nomCategorie)
                },])

            # Actualise l'affichage
            self.MAJ(IDinscription)

            # Saisie de forfaits auto
            from Dlg import DLG_Appliquer_forfait
            f = DLG_Appliquer_forfait.Forfaits(IDfamille=IDfamille, listeActivites=[IDactivite,], listeIndividus=[self.IDindividu,], saisieManuelle=False, saisieAuto=True)
            f.Applique_forfait(selectionIDcategorie_tarif=IDcategorie_tarif, inscription=True, selectionIDactivite=IDactivite)

        dlg.Destroy()

    def Modifier(self, event):
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune inscription à modifier dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        # Recherche si l'individu est rattaché à d'autres familles
        listeNoms = []
        listeFamille = []
        for IDfamille, dictFamille in self.dictFamillesRattachees.items() :
            listeFamille.append(IDfamille)
            listeNoms.append(dictFamille["nomsTitulaires"])

        from Dlg import DLG_Inscription
        IDinscription = self.Selection()[0].IDinscription
        IDfamille = self.Selection()[0].IDfamille
        dlg = DLG_Inscription.Dialog(self)
        dlg.SetFamille(listeNoms, listeFamille, self.Selection()[0].IDfamille, True)
        dlg.SetIDactivite(self.Selection()[0].IDactivite)
        dlg.ctrl_activites.Enable(False)
        dlg.SetIDgroupe(self.Selection()[0].IDgroupe)
        dlg.SetIDcategorie(self.Selection()[0].IDcategorie_tarif)
        dlg.SetParti(self.Selection()[0].parti)
        if dlg.ShowModal() == wx.ID_OK:
            IDactivite = dlg.GetIDactivite()
            IDgroupe = dlg.GetIDgroupe()
            IDcategorie_tarif = dlg.GetIDcategorie()
            nomActivite = dlg.GetNomActivite()
            nomGroupe = dlg.GetNomGroupe()
            nomCategorie = dlg.GetNomCategorie()
            parti = dlg.GetParti()

            # Verrouillage utilisateurs
            if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_inscriptions", "modifier", IDactivite=IDactivite) == False :
                return

            # Sauvegarde
            DB = GestionDB.DB()
            listeDonnees = [
                ("IDindividu", self.IDindividu ),
                ("IDactivite", IDactivite ),
                ("IDgroupe", IDgroupe),
                ("IDcategorie_tarif", IDcategorie_tarif),
                ("parti", parti),
                ]
            DB.ReqMAJ("inscriptions", listeDonnees, "IDinscription", IDinscription)
            DB.Close()

            # Mémorise l'action dans l'historique
            UTILS_Historique.InsertActions([{
                "IDindividu" : self.IDindividu,
                "IDfamille" : IDfamille,
                "IDcategorie" : 20,
                "action" : _("Modification de l'inscription à l'activité '%s' sur le groupe '%s' avec la tarification '%s'") % (nomActivite, nomGroupe, nomCategorie)
                },])

            # Actualise l'affichage
            self.MAJ(IDinscription)
        dlg.Destroy()

    def Supprimer(self, event):
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune inscription à supprimer dans la liste"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        
        IDinscription = self.Selection()[0].IDinscription
        IDfamille = self.Selection()[0].IDfamille
        IDindividu = self.Selection()[0].IDindividu
        nomActivite = self.Selection()[0].nom_activite
        IDactivite = self.Selection()[0].IDactivite

        # Verrouillage utilisateurs
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_inscriptions", "supprimer", IDactivite=IDactivite) == False : 
            return

        DB = GestionDB.DB()
        
        # Recherche si des consommations existent
        req = """SELECT IDconso, forfait
        FROM consommations
        WHERE IDinscription=%d AND (forfait IS NULL OR forfait=1);""" % IDinscription
        DB.ExecuterReq(req)
        listeConso = DB.ResultatReq()
        if len(listeConso) > 0 :
            dlg = wx.MessageDialog(self, _("Il existe déjà %d consommations enregistrées sur cette inscription. \n\nIl est donc impossible de la supprimer !") % len(listeConso), _("Annulation impossible"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            DB.Close() 
            return
        
        # Recherche si des prestations existent
        req = """SELECT IDprestation, prestations.forfait
        FROM prestations
        WHERE IDactivite=%d AND IDindividu=%d
        ;""" % (IDactivite, IDindividu)
        DB.ExecuterReq(req)
        listePrestations = DB.ResultatReq()
        listePrestationsForfait = []
        listePrestationsNormales = []
        for IDprestation, forfait in listePrestations :
            if forfait == 2 : 
                if IDprestation not in listePrestationsForfait : 
                    listePrestationsForfait.append(IDprestation)
            else:
                if IDprestation not in listePrestationsNormales : 
                    listePrestationsNormales.append(IDprestation)
        if len(listePrestations) - len(listePrestationsForfait) > 0 :
            dlg = wx.MessageDialog(self, _("Il existe déjà %d prestations enregistrées sur cette inscription. \n\nIl est donc impossible de la supprimer !") % len(listePrestations), _("Annulation impossible"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            DB.Close() 
            return
        
        DB.Close() 

        # Demande de confirmation
        if len(listePrestationsForfait) == 0 : texteForfait = ""
        elif len(listePrestationsForfait) == 1 : texteForfait = _("\n\n(La prestation associée sera également supprimée)")
        else : texteForfait = _("\n\n(Les %d prestations associées seront également supprimées)") % len(listePrestationsForfait)
        dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer cette inscription ?%s") % texteForfait, _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
        if dlg.ShowModal() == wx.ID_YES :
            IDinscription = self.Selection()[0].IDinscription
            DB = GestionDB.DB()
            DB.ReqDEL("inscriptions", "IDinscription", IDinscription)
            # Suppression des forfaits associés déjà saisis
            for IDprestation in listePrestationsForfait :
                DB.ReqDEL("prestations", "IDprestation", IDprestation)
                DB.ReqDEL("consommations", "IDprestation", IDprestation)
                DB.ReqDEL("deductions", "IDprestation", IDprestation)
                DB.ReqDEL("ventilation", "IDprestation", IDprestation)
            DB.Close() 
            
            # Mémorise l'action dans l'historique
            UTILS_Historique.InsertActions([{
                "IDindividu" : self.IDindividu,
                "IDfamille" : IDfamille,
                "IDcategorie" : 19, 
                "action" : _("Suppression de l'inscription à l'activité '%s'") % nomActivite
                },])
                
            # Actualise l'affichage
            self.MAJ()
        dlg.Destroy()

    def GetCompteFamille(self, IDfamille=None):
        """ Récupère le compte_payeur par défaut de la famille """
        DB = GestionDB.DB()
        req = """SELECT IDfamille, IDcompte_payeur
        FROM familles
        WHERE IDfamille=%d;""" % IDfamille
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if len(listeDonnees) == 0 : return None
        IDcompte_payeur = listeDonnees[0][1]
        return IDcompte_payeur

    def GetListeActivites(self):
        """ Retourne la liste des activités sur lesquelles l'individu est inscrit """
        """ Sert pour le ctrl DLG_Individu_inscriptions (saisir d'un forfait daté) """
        listeActivites = []
        for track in self.donnees :
            listeActivites.append(track.IDactivite)
        listeActivites.sort()
        return listeActivites

    def EditerConfirmation(self, event):
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune inscription dans la liste !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDinscription = self.Selection()[0].IDinscription
        from Dlg import DLG_Impression_inscription
        dlg = DLG_Impression_inscription.Dialog(self, IDinscription=IDinscription) 
        dlg.ShowModal()
        dlg.Destroy()



# -------------------------------------------------------------------------------------------------------------------------------------


class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False
        
        self.SetDescriptiveText(_("Rechercher une inscription..."))
        self.ShowSearchButton(True)
        
        self.listView = self.parent.ctrl_listview
        nbreColonnes = self.listView.GetColumnCount()
        self.listView.SetFilter(Filter.TextSearch(self.listView, self.listView.columns[0:nbreColonnes]))
        
        self.SetCancelBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Interdit.png"), wx.BITMAP_TYPE_PNG))
        self.SetSearchBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Loupe.png"), wx.BITMAP_TYPE_PNG))
        
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
        self.Recherche()
        
    def Recherche(self):
        txtSearch = self.GetValue().replace("'","\\'")
        self.ShowCancelButton(len(txtSearch))
        self.listView.GetFilter().SetText(txtSearch)
        self.listView.RepopulateList()
        self.Refresh() 



# -------------------------------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.myOlv = ListView(panel, id=-1, IDindividu=3, name="OL_test", style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
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

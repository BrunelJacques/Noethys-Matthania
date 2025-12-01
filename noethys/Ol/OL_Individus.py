#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB, Jacques BRUNEL
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import Chemins
from Utils.UTILS_Traduction import _
import wx
import datetime
import GestionDB
from Data import DATA_Civilites as Civilites
from Utils import UTILS_Titulaires
from Utils import UTILS_Dates
from Utils import UTILS_Utilisateurs
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, PanelAvecFooter


class Track(object):
    def __init__(self, donnees, dictIndividus):
        self.IDfamille = donnees["rattachements.IDfamille"]
        self.IDindividu = donnees["individus.IDindividu"]
        self.IDcivilite = donnees["IDcivilite"]
        self.nom = donnees["individus.nom"]
        self.prenom = donnees["prenom"]
        self.nom_naiss = donnees["nom_jfille"]
        self.date_naiss = donnees["date_naiss"]
        self.age = donnees["age"]
        self.adresse_auto = donnees["adresse_auto"]
        
        # Adresse auto ou manuelle
        if self.adresse_auto != None and self.adresse_auto in dictIndividus :
            self.rue_resid = dictIndividus[self.adresse_auto]["rue_resid"]
            self.cp_resid = dictIndividus[self.adresse_auto]["cp_resid"]
            self.ville_resid = dictIndividus[self.adresse_auto]["ville_resid"]
        else:
            self.rue_resid = donnees["rue_resid"]
            self.cp_resid = donnees["cp_resid"]
            self.ville_resid = donnees["ville_resid"]

        self.tel_domicile = donnees["tel_domicile"]
        self.tel_mobile = donnees["tel_mobile"]
        self.mail = donnees["mail"]
        self.genre = donnees["genre"]
        self.categorieCivilite = donnees["categorieCivilite"]
        self.civiliteLong = donnees["civiliteLong"]
        self.civiliteAbrege = donnees["civiliteAbrege"]
        self.nomImage = donnees["nomImage"]
        
        # Champ pour filtre de recherche
        nom = self.nom
        if nom == None : nom = ""
        prenom = self.prenom
        if prenom == None : prenom = ""
        self.champ_recherche = "%s %s %s" % (nom, prenom, nom)

    def GetRattachements(self):
        # Récupération des rattachements dans la base
        DB = GestionDB.DB()
        req = """
        SELECT rattachements.IDcategorie, rattachements.IDfamille, 
               rattachements.titulaire, familles.IDfamille
        FROM rattachements 
        LEFT JOIN familles ON rattachements.IDfamille = familles.IDfamille
        WHERE IDindividu=%d
        GROUP BY rattachements.IDcategorie, rattachements.IDfamille, rattachements.titulaire, familles.IDfamille;
        ;""" % self.IDindividu
        DB.ExecuterReq(req)
        listeRattachements = DB.ResultatReq()

        # Recherche des rattachements
        dictTitulaires = {}
        lstRattachOrphelins = []
        rattachements = None
        dictTitulaires = {}
        txtTitulaires = _("Rattaché à aucune famille")
        if len(listeRattachements) == 1 :
            rattachement = listeRattachements[0]
            (IDcategorie, IDfamille, titulaire, familles_id) = rattachement
            if familles_id:
                rattachements = [(IDcategorie, IDfamille, titulaire)]
                dictTitulaires[IDfamille] = self.GetNomsTitulaires(IDfamille)
                txtTitulaires = dictTitulaires[IDfamille]
            else:
                lstRattachOrphelins.append(IDfamille)
        elif len(listeRattachements) > 1:
            rattachements = []
            txtTitulaires = ""
            for IDcategorie, IDfamille, titulaire, familles_id in listeRattachements :
                if familles_id:
                    rattachements.append((IDcategorie, IDfamille, titulaire))
                    nomsTitulaires =  self.GetNomsTitulaires(IDfamille)
                    dictTitulaires[IDfamille] = nomsTitulaires
                    txtTitulaires += nomsTitulaires + " | "
                else:
                    lstRattachOrphelins.append(IDfamille)
            if len(txtTitulaires) > 0 :
                txtTitulaires = txtTitulaires[:-2]
            else:
                txtTitulaires = None
        if len(lstRattachOrphelins) > 0:
            # correction de l'anomalie de non présence dans familles de l'id famille
            for IDfamille in lstRattachOrphelins:
                req = """
                DELETE FROM rattachements 
                WHERE IDindividu = %d
                    AND IDfamille = %d  
                ;""" % (self.IDindividu, IDfamille)
                DB.ExecuterReq(req,MsgBox = "OL_Individu.GetRattachements DEL orphelins")
        DB.Close()

        return rattachements, dictTitulaires, txtTitulaires

    def GetNomsTitulaires(self, IDfamille=None):
        dictTitulaires = UTILS_Titulaires.GetTitulaires(listeIDfamille=[IDfamille,])
        noms = dictTitulaires[IDfamille]["titulairesSansCivilite"]
        return noms

class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        self.categorie = kwds.pop("categorie", None)
        # Récupération des paramètres perso
        self.texteRecherche = ""
        self.itemSelected = False
        self.popupIndex = -1
        self.listeFiltres = []
        self.historique = []
        self.dictTracks = {}
        self.dictIndividus = {}
        self.donnees = []
        self.dictParametres = {
            "groupes_activites": [],
            "activites": [],
            "archives": False,
            "effaces": False,
        }
        self.listeActivites = []
        self.listeGroupesActivites = []
        self.forceActualisation = False
        self.inPayeurs = None
        # Initialisation du listCtrl
        FastObjectListView.__init__(self, *args, **kwds)
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, faceName="Tekton"))
        self.SetEmptyListMsg(_("Aucun individu"))
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

    def SetParametres(self, parametres=""):
        if parametres == None :
            parametres = ""

        dictParametres = {}
        listeParametres = parametres.split("###")
        for parametre in listeParametres :
            if "===" in parametre:
                nom, valeur = parametre.split("===")
                dictParametres[nom] = valeur

        # Groupes d'activités
        self.dictParametres["groupes_activites"] = []
        if "liste_groupes_activites" in dictParametres:
            listeID = [int(ID) for ID in dictParametres["liste_groupes_activites"].split(";")]
            self.dictParametres["groupes_activites"] = listeID

        # Activités
        self.dictParametres["activites"] = []
        if "liste_activites" in dictParametres:
            listeID = [int(ID) for ID in dictParametres["liste_activites"].split(";")]
            self.dictParametres["activites"] = listeID

        # Options
        if "archives" in dictParametres:
            self.dictParametres["archives"] = True
        else :
            self.dictParametres["archives"] = False

        if "effaces" in dictParametres:
            self.dictParametres["effaces"] = True
        else :
            self.dictParametres["effaces"] = False

    def OnItemActivated(self,event):
        self.Modifier(None)

    def GetTracks(self,inPayeurs):
        # Récupération des données dans la base
        listeChamps = (
            "individus.IDindividu", "rattachements.IDfamille", "IDcivilite", "individus.nom", "prenom",
            "nom_jfille","date_naiss", "adresse_auto", "rue_resid", "cp_resid", "ville_resid",
            "tel_domicile", "tel_mobile","mail"
            )
        condition = "1"
        db = GestionDB.DB()
        if self.texteRecherche and len(self.texteRecherche) > 0 :
            #on teste une saisie numérique
            try :
                ID = int(self.texteRecherche)
            except :
                ID = 0
            if ID >0 :
                # on a saisi un nombre code client ou famille
                condition = "individus.IDindividu = %d OR rattachements.IDfamille =%d" % (ID,ID)
            elif inPayeurs :
                # recherche dans les noms de payeurs
                condition = "((payeurs.nom LIKE '%%%s%%') AND (rattachements.IDcategorie=1))"% (self.texteRecherche)
            else:
                # SAISIE alpha et recherche élargie au noms jeune fille
                if db.isNetwork == True :
                    # Version MySQL
                    concat = "CONCAT(individus.nom, ' ', IFNULL(individus.prenom,' '), ' ',individus.nom, IFNULL(nom_jfille,' '))"
                    condition = """(
                            %s LIKE '%%%s%%' 
                            )"""% (concat,self.texteRecherche)
                else:
                    condition = """individus.nom LIKE '%%%s%%' 
                                OR individus.prenom LIKE '%%%s%%'
                                OR individus.nom_jfille LIKE '%%%s%%'
                                """ % (self.texteRecherche, self.texteRecherche,self.texteRecherche)

        # LEFT JOIN a nécessité un index IDindividu sur rattachements
        if inPayeurs and len(self.texteRecherche) > 0 and ID <= 0:
            req = """
                    SELECT %s
                    FROM (individus 
                            INNER JOIN rattachements ON individus.IDindividu = rattachements.IDindividu) 
                            INNER JOIN payeurs ON rattachements.IDfamille = payeurs.IDpayeur                       
                    WHERE %s
                    GROUP BY %s;"""% (",".join(listeChamps),condition,",".join(listeChamps))
        else:
            req = """
                    SELECT %s
                    FROM individus
                    LEFT JOIN rattachements
                    ON rattachements.IDindividu = individus.IDindividu
                    WHERE %s ; """ % (",".join(listeChamps),condition)

        retour = db.ExecuterReq(req, MsgBox="OL_Individus.ListView.GetTracks")
        listeDonnees = db.ResultatReq()
        db.Close()

        # Récupération du dictionnaire des civilités
        dictCivilites = Civilites.GetDictCivilites()

        # Création du dictionnaire des données
        dictIndividus = {}
        for valeurs in listeDonnees :
            IDindividu = valeurs[0]
            dictTemp = {}
            # Infos de la table Individus
            for index in range(0, len(listeChamps)) :
                nomChamp = listeChamps[index]
                dictTemp[nomChamp] = valeurs[index]
            # Infos sur la civilité
            if dictTemp["IDcivilite"] != None and dictTemp["IDcivilite"] != "" :
                dictTemp["genre"] = dictCivilites[dictTemp["IDcivilite"]]["sexe"]
                dictTemp["categorieCivilite"] = dictCivilites[dictTemp["IDcivilite"]]["categorie"]
                dictTemp["civiliteLong"] = dictCivilites[dictTemp["IDcivilite"]]["civiliteLong"]
                dictTemp["civiliteAbrege"] = dictCivilites[dictTemp["IDcivilite"]]["civiliteAbrege"] 
                dictTemp["nomImage"] = dictCivilites[dictTemp["IDcivilite"]]["nomImage"] 
            else:
                dictTemp["genre"] = ""
                dictTemp["categorieCivilite"] = ""
                dictTemp["civiliteLong"] = ""
                dictTemp["civiliteAbrege"] = ""
                dictTemp["nomImage"] = None
            
            if dictTemp["date_naiss"] == None :
                dictTemp["age"] = None
            else:
                try : 
                    datenaissDD = UTILS_Dates.DateEngEnDateDD(dictTemp["date_naiss"])
                    datedujour = datetime.date.today()
                    age = (datedujour.year - datenaissDD.year) - int((datedujour.month, datedujour.day) < (datenaissDD.month, datenaissDD.day))
                    dictTemp["age"] = age
                    dictTemp["date_naiss"] = datenaissDD
                except :
                    dictTemp["age"] = None

            dictIndividus[IDindividu] = dictTemp
        
        # Vérifie si le dictIndividus est différent du précédent pour empêcher l'actualisation de la liste
        if dictIndividus == self.dictIndividus and len(self.listeActivites) == 0 and len(self.listeGroupesActivites) == 0 and self.forceActualisation == False :
            return None
        else :
            self.dictIndividus = dictIndividus
        
        filtre = None

        # Si filtre activités
        if len(self.listeActivites) > 0 :
            if len(self.listeActivites) == 0 : conditionActivites = "()"
            elif len(self.listeActivites) == 1 : conditionActivites = "(%d)" % self.listeActivites[0]
            else : conditionActivites = str(tuple(self.listeActivites))
            db = GestionDB.DB()
            req = """SELECT individus.IDindividu, nom
            FROM individus
            LEFT JOIN inscriptions ON inscriptions.IDindividu = individus.IDindividu
            WHERE inscriptions.IDactivite IN %s
            ;""" % conditionActivites
            db.ExecuterReq(req)
            listeDonnees = db.ResultatReq()
            db.Close()
            filtre = []
            for ID, nom in listeDonnees :
                filtre.append(ID)

        # Si filtre Groupes d'activités
        if len(self.listeGroupesActivites) > 0 :
            if len(self.listeGroupesActivites) == 0 : conditionGroupesActivites = "()"
            elif len(self.listeGroupesActivites) == 1 : conditionGroupesActivites = "(%d)" % self.listeGroupesActivites[0]
            else : conditionGroupesActivites = str(tuple(self.listeGroupesActivites))
            db = GestionDB.DB()
            req = """SELECT individus.IDindividu, nom
            FROM individus
            LEFT JOIN inscriptions ON inscriptions.IDindividu = individus.IDindividu
            LEFT JOIN groupes_activites ON groupes_activites.IDactivite = inscriptions.IDactivite
            WHERE groupes_activites.IDtype_groupe_activite IN %s
            ;""" % conditionGroupesActivites
            db.ExecuterReq(req,MsgBox="OL_Individus")
            listeDonnees = db.ResultatReq()
            db.Close()
            filtre = []
            for ID, nom in listeDonnees :
                filtre.append(ID)

        # Création des Tracks
        listeListeView = []
        self.dictTracks = {}
        for IDindividu, dictTemp in dictIndividus.items() :
            if filtre == None or IDindividu in filtre :
                track = Track(dictTemp, dictIndividus)
                listeListeView.append(track)
                self.dictTracks[IDindividu] = track
        
        return listeListeView
      
    def InitObjectListView(self):
        # Création du imageList
        for categorie, civilites in Civilites.LISTE_CIVILITES :
            for IDcivilite, CiviliteLong, CiviliteAbrege, nomImage, genre in civilites :
                indexImg = self.AddNamedImages(nomImage, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/%s"% nomImage), wx.BITMAP_TYPE_PNG))
        imgSansRattachement = self.AddNamedImages("sansRattachement", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Attention.png"), wx.BITMAP_TYPE_PNG))

        def GetImageCivilite(track):
            return track.nomImage

        def FormateDate(date):
            return UTILS_Dates.DateDDEnFr(date)
        
        def FormateAge(age):
            if age == None : return ""
            return _("%d ans") % age
        
        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED"
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
                
        liste_Colonnes = [
            ColumnDefn("Ind.", "left", 60, "IDindividu", typeDonnee="entier", imageGetter=GetImageCivilite),
            ColumnDefn("Fam.", "left", 40, "IDfamille", typeDonnee="entier"),
            ColumnDefn(_("Nom"), 'left', 100, "nom", typeDonnee="texte"),
            ColumnDefn(_("Prénom"), "left", 80, "prenom", typeDonnee="texte"),
            ColumnDefn(_("Nom naiss."), "left", 80, "nom_naiss", typeDonnee="texte"),
            ColumnDefn(_("Date naiss."), "left", 72, "date_naiss", typeDonnee="date", stringConverter=FormateDate),
            ColumnDefn(_("Age"), "left", 50, "age", typeDonnee="entier", stringConverter=FormateAge),
            ColumnDefn(_("Rue"), "left", 150, "rue_resid", typeDonnee="texte"),
            ColumnDefn(_("C.P."), "left", 50, "cp_resid", typeDonnee="texte"),
            ColumnDefn(_("Ville"), "left", 100, "ville_resid", typeDonnee="texte"),
            ColumnDefn(_("Tél. domicile"), "left", 100, "tel_domicile", typeDonnee="texte"),
            ColumnDefn(_("Tél. mobile"), "left", 100, "tel_mobile", typeDonnee="texte"),
            ColumnDefn(_("Email"), "left", 150, "mail", typeDonnee="texte"),
            ColumnDefn(_("Recherche"), "left", 0, "champ_recherche", typeDonnee="texte"),
            ]
        
        self.SetColumns(liste_Colonnes)
        #self.SetSortColumn(self.columns[2])
        self.SetObjects(self.donnees)
       
    def MAJ(self, IDindividu=None, forceActualisation=False, inPayeurs=None):
        if inPayeurs == None:
            # reprend par défaut l'ancienne valeur
            inPayeurs = self.inPayeurs
        else:
            self.inPayeurs = inPayeurs
        # Mémorise l'individu sélectionné avant la MAJ
        if IDindividu == None :
            selectionTrack = self.Selection()
            if len(selectionTrack) > 0 :        
                IDindividu = selectionTrack[0].IDindividu
        
        # MAJ
        self.forceActualisation = forceActualisation
        donnees = self.GetTracks(inPayeurs)
        self.forceActualisation = False
        if donnees != None :
            self.donnees = donnees
            self.GetParent().Freeze() 
            self.InitObjectListView()
            self.GetParent().Thaw() 
        self.Reselection(IDindividu)
    
    def Reselection(self, IDindividu=None):
        """ Re-sélection après MAJ de la liste """
        if IDindividu in self.dictTracks :
            track = self.dictTracks[IDindividu]
            self.SelectObject(track, deselectOthers=True, ensureVisible=True)
        
    def Selection(self):
        return self.GetSelectedObjects()

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        # Si on est dans le DLG Rattachement
        if self.GetParent().GetName() == "DLG_Rattachement" :
            return
        
        # Si on est dans le panel Recherche d'individus
        if len(self.Selection()) == 0:
            noSelection = True
        else:
            noSelection = False
            ID = self.Selection()[0].IDindividu
                
        # Création du menu contextuel
        menuPop = wx.Menu()

        # Item Modifier
        item = wx.MenuItem(menuPop, 10, _("Ajouter une fiche famille"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Famille_ajouter.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Ajouter, id=10)
        
        # Item Modifier
        item = wx.MenuItem(menuPop, 20, _("Modifier la fiche famille"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Famille_modifier.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Modifier, id=20)
        if noSelection == True : item.Enable(False)
        
        # Item Supprimer
        item = wx.MenuItem(menuPop, 30, _("Supprimer la fiche famille"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Famille_supprimer.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Supprimer, id=30)
        if noSelection == True : item.Enable(False)
                
        menuPop.AppendSeparator()

        # Item Ajouter
        item = wx.MenuItem(menuPop, 60, _("Ouvrir la grille des consommations"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Calendrier.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Modifier, id=60)
        if noSelection == True : item.Enable(False)
        
        # Item Supprimer
        item = wx.MenuItem(menuPop, 70, _("Ouvrir la fiche individuelle"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Personnes.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Modifier, id=70)
        if noSelection == True : item.Enable(False)
        
        menuPop.AppendSeparator()

        # Génération automatique des fonctions standards
        self.GenerationContextMenu(menuPop, titre=_("Liste des individus"), orientation=wx.LANDSCAPE)
        
        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Ajouter(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_fiche", "creer") == False : return
        # lance le rattachement par anticipation
        from Dlg import DLG_Rattachement
        dlgRattach = DLG_Rattachement.Dialog(None, IDfamille=None)
        dataRattach = None
        IDfamille = None
        if dlgRattach.ShowModal() == wx.ID_OK:
            dataRattach = dlgRattach.GetData()
            IDfamille = dlgRattach.GetIDfamille()
            # l'individu créé était déjà dans une famille
            if IDfamille:
                dataRattach = None
        dlgRattach.Destroy()
        from Dlg import DLG_Famille
        dlg = DLG_Famille.Dialog(self, IDfamille=IDfamille, dataRattach=dataRattach)
        ret = dlg.ShowModal()
        if ret == wx.ID_OK:
            pass
        else:
            pass

        try :
            if self.GetGrandParent().GetName() == "general" :
                self.GetGrandParent().MAJ() 
##                self.GetGrandParent().ctrl_remplissage.MAJ() 
            else:
                self.MAJ() 
        except : pass

    def Modifier(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_fiche", "consulter") == False : return
        # Si on est dans le DLG Rattachement
        if self.GetParent().GetName() == "DLG_Rattachement" :
            self.GetParent().OnBoutonOk(None)
            return
        # Si on est dans le panel de recherche d'individus
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucun individu dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        # Ouvrir la fiche famille de l'individu
        track = self.Selection()[0]
        
        ouvrirGrille=False
        ouvrirFicheInd = False
        if event != None :
            # Ouverture grille de l'individu si touche CTRL enfoncée
            if wx.GetKeyState(wx.WXK_CONTROL) == True or event.GetId() == 60 :
                ouvrirGrille=True
            
            # Ouverture fiche de l'individu si touche SHIFT enfoncée
            if wx.GetKeyState(wx.WXK_SHIFT) == True or event.GetId() == 70 :
                ouvrirFicheInd = True
        
        # Ouverture de la fiche famille
        self.OuvrirFicheFamille(track, ouvrirGrille, ouvrirFicheInd)
    
    def OuvrirFicheFamille(self, track=None, ouvrirGrille=False, ouvrirFicheInd=False, IDfamille=None):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_fiche", "consulter") == False : return

        IDindividu = track.IDindividu

        rattachements, dictTitulaires, txtTitulaires = track.GetRattachements()
        if rattachements != None :
            rattachements.sort()

        # Rattaché à aucune famille
        if rattachements == None :
            dlg = wx.MessageDialog(self, _("Cet individu n'est rattaché à aucune famille.\n\nSouhaitez-vous ouvrir sa fiche individuelle ?"), _("Confirmation"), wx.YES_NO|wx.YES_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse !=  wx.ID_YES :
                return False
            else:
                # Ouverture de la fiche individuelle
                from Dlg import DLG_Individu
                dlg = DLG_Individu.Dialog(None, IDindividu=IDindividu)
                if dlg.ShowModal() == wx.ID_OK:
                    pass
                dlg.Destroy()
                self.MAJ()
                return

        # Rattachée à une seule famille
        elif len(rattachements) == 1 :
            IDcategorie, IDfamille, titulaire = rattachements[0]
        # Rattachée à plusieurs familles
        else:
            listeNoms = []
            for IDcategorie, IDfamille, titulaire in rattachements :
                nomTitulaires = dictTitulaires[IDfamille]
                if IDcategorie == 1 :
                    nomCategorie = _("représentant")
                    if titulaire == 1 :
                        nomCategorie += _(" titulaire")
                if IDcategorie == 2 : nomCategorie = _("enfant")
                if IDcategorie == 3 : nomCategorie = _("contact")
                listeNoms.append(_("%d: %s (en tant que %s)") % (IDfamille, nomTitulaires, nomCategorie))
            dlg = wx.SingleChoiceDialog(self, _("Cet individu est rattaché à %d familles.\nLa fiche de quelle famille souhaitez-vous ouvrir ?") % len(listeNoms), _("Rattachements multiples"), listeNoms, wx.CHOICEDLG_STYLE)
            IDfamilleSelection = None
            if dlg.ShowModal() == wx.ID_OK:
                indexSelection = dlg.GetSelection()
                IDcategorie, IDfamille, titulaire = rattachements[indexSelection]
                dlg.Destroy()
            else:
                dlg.Destroy()
                return
            
        # Ouverture de la fiche famille
        if IDfamille != None and IDfamille != -1 :
            from Dlg import DLG_Famille
            dlg = DLG_Famille.Dialog(self, IDfamille)
            # Ouverture grille de l'individ
            if ouvrirGrille == True :
                dlg.OuvrirGrilleIndividu(IDindividu)
            # Ouverture fiche de l'individu
            if ouvrirFicheInd == True :
                dlg.OuvrirFicheIndividu(IDindividu)
            ret = dlg.ShowModal()
            if ret== wx.ID_OK:
                self.MAJ(IDindividu)
            dlg.Destroy()
            # MAJ du remplissage
            try :
                if self.GetGrandParent().GetName() == "general" :
                    self.GetGrandParent().MAJ() 
                else:
                    self.MAJ() 
            except : pass
            # Mémorisation pour l'historique de la barre de recherche rapide
            if IDindividu not in self.historique :
                self.historique.append(IDindividu)
                if len(self.historique) > 30 :
                    self.historique.pop(0)

    def Supprimer(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_fiche", "consulter") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucun individu dans la liste"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDindividu = self.Selection()[0].IDindividu
        
        DB = GestionDB.DB()
        
        # Vérifie si cet individu n'est pas rattaché à une famille
        req = """
        SELECT IDrattachement, IDfamille
        FROM rattachements
        WHERE IDindividu=%d
        """ % IDindividu
        DB.ExecuterReq(req,MsgBox="OL_Individus2")
        listeDonnees = DB.ResultatReq()
        if len(listeDonnees) > 0 :
            dlg = wx.MessageDialog(self, _("Vous ne pouvez pas supprimer cette fiche car elle est rattachée à au moins une famille.\n\nSi vous souhaitez vraiment la supprimer, veuillez effectuer cette action à partir de la fiche famille !"), _("Suppression impossible"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            DB.Close()
            return False

        # Vérifie si cet individu n'est pas rattaché à une inscription
        req = """
        SELECT IDinscription, IDfamille
        FROM inscriptions
        WHERE IDindividu=%d
        """ % IDindividu
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        if len(listeDonnees) > 0:
            IDfamille = listeDonnees[0][1]
            dlg = wx.MessageDialog(self, _(
                "Vous ne pouvez pas supprimer cette fiche car elle est rattachée à au moins une inscription.\n\nSi vous souhaitez vraiment la supprimer, veuillez effectuer cette action à partir de la fiche famille %d, après avoir recréé le rattachement!"%IDfamille),
                                   _("Suppression impossible"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            DB.Close()
            return False

        # Demande de confirmation
        dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer cet individu ?"), _("Confirmation de suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
        if dlg.ShowModal() != wx.ID_YES :
            DB.Close()
            dlg.Destroy()
            return False
        dlg.Destroy()
        
        # Suppression : liens
        req = "DELETE FROM liens WHERE IDindividu_sujet=%d;" % IDindividu
        DB.ExecuterReq(req,MsgBox="OL_Individus3")
        req = "DELETE FROM liens WHERE IDindividu_objet=%d;" % IDindividu
        DB.ExecuterReq(req,MsgBox="OL_Individus4")
        
        # Suppression : vaccins
        req = "DELETE FROM vaccins WHERE IDindividu=%d;" % IDindividu
        DB.ExecuterReq(req,MsgBox="OL_Individus5")
        
        # Suppression : problemes_sante
        req = "DELETE FROM problemes_sante WHERE IDindividu=%d;" % IDindividu
        DB.ExecuterReq(req,MsgBox="OL_Individus6")
        
        # Suppression : abonnements
        req = "DELETE FROM abonnements WHERE IDindividu=%d;" % IDindividu
        DB.ExecuterReq(req,MsgBox="OL_Individus7")
        
        # Suppression : individu
        req = "DELETE FROM individus WHERE IDindividu=%d;" % IDindividu
        DB.ExecuterReq(req,MsgBox="OL_Individus8")
        
        DB.Commit() 
        DB.Close()
                
        dlg = wx.MessageDialog(self, _("La fiche individuelle a été supprimée avec succès."), _("Suppression"), wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

        self.MAJ()

        # MAJ du listView
        # MAJ du remplissage
        try :
            if self.GetGrandParent().GetName() == "general" :
                self.GetGrandParent().MAJ() 
            else:
                self.MAJ() 

        except : pass

# Gestion de la barreRecherche ---------------------------------------------------------------------------------
class CTRL_Outils(wx.Panel):
    def __init__(self, parent, listview=None, texteDefaut="Recherche...", afficherCocher=False, historique=False, style=wx.NO_BORDER | wx.TAB_TRAVERSAL):
        wx.Panel.__init__(self, parent, id=-1, style=style)
        self.listview = listview

        # Contrôles
        self.barreRecherche = BarreRecherche(self, listview=listview, texteDefaut=texteDefaut, historique=historique)
        import wx.lib.platebtn as platebtn

        # Bouton Filtrer
        self.bouton_filtrer = platebtn.PlateButton(self, -1, " Filtrer",
                                                   wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Filtre.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_filtrer.SetToolTip("Cliquez ici pour filtrer cette liste")

        menu = wx.Menu()
        item = wx.MenuItem(menu, 10, "Ajouter, modifier ou supprimer des filtres", "Cliquez ici pour accéder à la gestion des filtres de listes")
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Filtre.png"), wx.BITMAP_TYPE_ANY))
        menu.Append(item)
        menu.AppendSeparator()
        item = wx.MenuItem(menu, 11, "Supprimer tous les filtres", "Cliquez ici pour supprimer tous les filtres")
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Filtre_supprimer.png"), wx.BITMAP_TYPE_ANY))
        menu.Append(item)
        self.bouton_filtrer.SetMenu(menu)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonFiltrer, self.bouton_filtrer)

        # Bouton Cocher
        if afficherCocher == True :
            self.bouton_cocher = platebtn.PlateButton(self, -1, " Cocher", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Cocher.png"), wx.BITMAP_TYPE_ANY))
            self.bouton_cocher.SetToolTip("Cliquez ici pour cocher ou décocher rapidement tous les éléments de cette liste")

            menu = wx.Menu()
            item = wx.MenuItem(menu, 20, "Tout cocher", "Cliquez ici pour cocher tous les éléments de la liste")
            item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Cocher.png"), wx.BITMAP_TYPE_ANY))
            menu.Append(item)
            item = wx.MenuItem(menu, 21, "Tout décocher", "Cliquez ici pour décocher tous les éléments de la liste")
            item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Decocher.png"), wx.BITMAP_TYPE_ANY))
            menu.Append(item)
            self.bouton_cocher.SetMenu(menu)
            self.Bind(wx.EVT_BUTTON, self.OnBoutonCocher, self.bouton_cocher)

        self.Bind(wx.EVT_MENU, self.OnMenu)
        self.Bind(wx.EVT_SIZE, self.OnSize)

        # Layout
        sizerbase = wx.BoxSizer(wx.HORIZONTAL)
        sizerbase.Add(self.barreRecherche, 1, wx.ALL|wx.EXPAND, 0)
        sizerbase.Add(self.bouton_filtrer, 0, wx.LEFT|wx.EXPAND, 5)
        if afficherCocher == True :
            sizerbase.Add(self.bouton_cocher, 0, wx.LEFT|wx.EXPAND, 5)
        self.SetSizer(sizerbase)
        self.Layout()

    def OnSize(self, event):
        self.Refresh()
        event.Skip()

    def MAJ_ctrl_filtrer(self):
        """ Met à jour l'image du bouton Filtrage """
        nbreFiltres = len(self.listview.listeFiltresColonnes)

        # Modifie l'image selon le nbre de filtres activés
        if nbreFiltres == 0 :
            nomImage = "Filtre"
        elif nbreFiltres < 10 :
            nomImage = "Filtre_%d" % nbreFiltres
        else :
            nomImage = "Filtre_10"
        self.bouton_filtrer.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/%s.png")% nomImage, wx.BITMAP_TYPE_ANY))
        self.bouton_filtrer.Refresh()

        # Modifie le tip en fonction des filtres activés
        if nbreFiltres == 0 :
            texte = "Cliquez ici pour filtrer cette liste"
        else :
            if nbreFiltres == 1 :
                texte = "Cliquez ici pour filtrer cette liste\n> 1 filtre activé"
            else :
                texte = "Cliquez ici pour filtrer cette liste\n> %d filtres activés" % nbreFiltres
        self.bouton_filtrer.SetToolTip(texte)

    def OnBoutonFiltrer(self, event):
        listeFiltres = []
        from Dlg import DLG_Filtres_listes
        dlg = DLG_Filtres_listes.Dialog(self, ctrl_listview=self.listview)
        if dlg.ShowModal() == wx.ID_OK :
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
        # Accéder à la gestion des filtres
        if ID == 10 :
            self.OnBoutonFiltrer(None)
        # Supprimer tous les filtres
        if ID == 11 :
            self.listview.SetFiltresColonnes([])
            self.listview.Filtrer()
            self.MAJ_ctrl_filtrer()
        # Tout cocher
        if ID == 20 :
            self.listview.CocheListeTout()
        # Tout décocher
        if ID == 21 :
            self.listview.CocheListeRien()

class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent, listview, texteDefaut="Rechercher individu ou famille...", historique=False):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.historique = historique
        self.listview = listview
        self.rechercheEnCours = False
        self.IDindividu = None
        self.texteCherche = None

        # Assigne cette barre de recherche au listview
        self.listview.SetBarreRecherche(self)

        self.SetDescriptiveText(texteDefaut)
        self.ShowSearchButton(True)

        self.SetCancelBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Interdit.png"), wx.BITMAP_TYPE_PNG))
        self.SetSearchBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Loupe.png"), wx.BITMAP_TYPE_PNG))

        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnEnter)
        self.Bind(wx.EVT_TEXT, self.OnText)

    def Recherche(self,txtSearch):
        self.ShowCancelButton(len(txtSearch))
        self.listview.texteRecherche = txtSearch
        self.listview.MAJ()

    def OnKeyDown(self, event):
        """ Efface tout si touche ECHAP """
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_ESCAPE :
            self.OnCancel(None)
        event.Skip()

    def OnEnter(self, evt):
        txtSearch = self.GetValue().replace("'","\\'")
        self.Recherche(txtSearch)

    def OnSearch(self, evt):
        if self.historique == True :
            self.SetMenu(self.MakeMenu())
        self.Recherche(self.GetValue())

    def Cancel(self):
        self.OnCancel(None)

    def OnCancel(self, evt):
        self.SetValue("")
        self.Recherche(self.GetValue())

    def OnText(self, evt):
        #à chaque frappe du clavier on ne fait rien qu'un petit test
        txtSearch = self.GetValue().replace("'","\\'")
        try :
            ID = int(txtSearch)
        except :
            ID = 0

    def MakeMenu(self):
        menu = wx.Menu()
        if len(self.listview.historique) == 0 :
            label = _(u"L'historique des fiches ouvertes est vide")
        else:
            label = _(u"----- Historique des fiches ouvertes -----")
        item = menu.Append(-1, label)
        item.Enable(False)
        index = 0
        for IDindividu in self.listview.historique :
            if IDindividu in self.listview.dictTracks :
                track = self.listview.dictTracks[IDindividu]
                label = u"%s %s" % (track.nom, track.prenom)
                menu.Append(index, label)
                index += 1
        self.Bind(wx.EVT_MENU_RANGE, self.OnItemMenu, id=0, id2=len(self.listview.historique))
        return menu

    def OnItemMenu(self, event):
        index = event.GetId()
        IDindividu = self.listview.historique[index]
        track = self.listview.dictTracks[IDindividu]
        self.listview.SelectObject(track)
        self.listview.OuvrirFicheFamille(track)



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
    frame_1 = MyFrame(None, -1, "OL")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()


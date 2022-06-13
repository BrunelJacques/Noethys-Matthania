#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania condition d'age sur groupes
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB, Jacques Brunel
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import wx
import Chemins
from Ctrl import CTRL_Bouton_image
import datetime
from Ctrl import CTRL_Bandeau

import GestionDB
from Gest import GestionArticle


STATUTS = [
    {"code": "ok", "label_long": _("Inscription validée"), "label_court": _("Valide"), "image" : "Ok4.png"},
    {"code": "attente", "label_long": _("Inscription en attente"), "label_court": _("Attente"), "image" : "Attente.png"},
    {"code": "refus", "label_long": _("Inscription refusée"), "label_court": _("Refus"), "image" : "Interdit.png"},
]

class Choix_famille(wx.Choice):
    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1) 
        self.parent = parent
        self.listeNoms = []
        self.listeDonnees = []
    
    def SetListeDonnees(self, listeDonnees=[]):
        self.listeNoms = []
        self.listeDonnees = listeDonnees
        for dictTemp in listeDonnees :
            IDfamille = dictTemp["IDfamille"]
            nom = _("Famille de %s") % dictTemp["nom"]
            self.listeNoms.append(nom)
        self.SetItems(self.listeNoms)
    
    def SetID(self, ID=None):
        index = 0
        for dictTemp in self.listeDonnees :
            IDfamille = dictTemp["IDfamille"]
            if IDfamille == ID :
                 self.SetSelection(index)
            index += 1

    def GetID(self):
        index = self.GetSelection()
        if index == -1 : return None
        return self.listeDonnees[index]["IDfamille"]

# ------------------------------------------------------------------------------------------------------------------------------------------

class ListBox(wx.ListBox):
    def __init__(self, parent, type="activites", IDindividu=None, IDcondition=None):
        wx.ListBox.__init__(self, parent, id=-1, choices=[])
        self.parent = parent
        self.IDindividu = IDindividu
        self.listeDonnees = []
        self.campeur = None
        self.type = type
        self.IDcondition = IDcondition
        self.Bind(wx.EVT_LISTBOX, self.OnSelection,)

    
    def MAJ(self, IDcondition=None):
        if IDcondition != None : 
            self.IDcondition = IDcondition
        self.listeDonnees = []
        if self.type == "activites" : self.Importation_activites() 
        if self.type == "groupes" :
            DB = GestionDB.DB()
            self.age = GestionArticle.AgeIndividu(DB,self.IDindividu,self.parent.IDactivite,mute=True)
            DB.Close()
            if self.age>110:
                self.GetParent().ctrl_groupes_valides.SetValue(False)
                self.GetParent().SetAgeInconnu(True)
            elif self.age > 0:
                self.GetParent().SetAgeInconnu(False)
                self.GetParent().ageConnu = True
            self.Importation_groupes()
        if self.type == "categories" : self.Importation_categories()
        listeItems = []
        if len(self.listeDonnees) > 0 :
            for dictValeurs in self.listeDonnees :
                label = dictValeurs["nom"]
                if label == None :
                    label = "Inconnu (ID%d)" % dictValeurs["ID"]
                listeItems.append(label)
        self.Set(listeItems)
        # Si un seul item dans la liste, le sélectionne...
        if self.type != "activites" and len(self.listeDonnees) == 1 :
            self.Select(0)
            self.OnSelection(None)

    def OnSelection(self, event):
        if self.type == "activites" : 
            IDactivite = self.GetID()
            self.parent.IDactivite=IDactivite
            self.parent.ctrl_groupes.MAJ(IDactivite)
            self.parent.ctrl_categories.MAJ((IDactivite,
                                             self.parent.ctrl_groupes.campeur))
            #self.parent.ctrl_categories.SelectCategorieSelonVille()
        elif self.type == "groupes" :
            IDactivite = self.parent.IDactivite
            selection = self.GetSelection()
            self.parent.ctrl_groupes.campeur = self.listeDonnees[selection]["campeur"]
            self.parent.ctrl_categories.MAJ((IDactivite,self.listeDonnees[selection]["campeur"]))
        return

    def Importation_activites(self):
        if self.GetParent().ctrl_activites_valides.GetValue() == True :
            dateDuJour = str(datetime.date.today())
            conditionDate = "WHERE date_fin >= '%s' " % dateDuJour
        else:
            conditionDate = ""
        db = GestionDB.DB()
        req = """SELECT activites.IDactivite, nom, nbre_inscrits_max, COUNT(inscriptions.IDinscription),activites.date_debut,activites.date_fin
        FROM activites
        LEFT JOIN inscriptions ON inscriptions.IDactivite = activites.IDactivite
        %s
        GROUP BY activites.IDactivite, nom, nbre_inscrits_max, activites.date_debut,activites.date_fin
        ORDER BY nom; """ % conditionDate
        db.ExecuterReq(req,MsgBox="Appel des activités")
        listeDonnees = db.ResultatReq()
        db.Close()
        for IDactivite, nom, nbre_inscrits_max, nbre_inscrits,dateDeb,dateFin in listeDonnees :
            valeurs = { "ID" : IDactivite, "nom" : nom, "nbre_inscrits_max" : nbre_inscrits_max, "nbre_inscrits" : nbre_inscrits,
                        "dateDeb" : dateDeb,"dateFin" : dateFin}
            self.listeDonnees.append(valeurs)

    def Importation_groupes(self):
        if self.IDcondition == None : return
        if self.GetParent().ctrl_groupes_valides.GetValue() == True :
            self.filtreAge = True
        else:
            self.filtreAge = False
        db = GestionDB.DB()
        req = """SELECT groupes.IDgroupe, groupes.nom, groupes.ageMini, groupes.ageMaxi, groupes.campeur
                FROM groupes
                INNER JOIN ouvertures ON groupes.IDgroupe = ouvertures.IDgroupe
                WHERE groupes.IDactivite=%d
                GROUP BY groupes.IDgroupe, groupes.nom, groupes.ageMini, groupes.ageMaxi
                ORDER BY ordre; """ % self.IDcondition
        db.ExecuterReq(req,MsgBox="Recherche Groupes")
        listeDonnees = db.ResultatReq()
        db.Close()
        for IDgroupe, nom, ageMini, ageMaxi,campeur in listeDonnees :
            visible = True
            try:
                flAgeMini = float(ageMini)
            except:
                flAgeMini = 0.0
            try:
                flAgeMaxi = float(ageMaxi)
            except:
                flAgeMaxi = 0.0
            if flAgeMaxi == 0: flAgeMaxi = 99
            if self.filtreAge:
                if self.age < flAgeMini:
                    visible = False
                if self.age > flAgeMaxi:
                    visible = False
            if visible:
                conditionAge = (flAgeMaxi + flAgeMini > 0 )
                valeurs = { "ID" : IDgroupe, "nom" : nom ,"campeur":campeur,"conditionAge": conditionAge}
                self.listeDonnees.append(valeurs)

    def Importation_categories(self):
        if self.IDcondition == None : return
        DB = GestionDB.DB()

        IDactivite, campeur = self.IDcondition  # ID condition doit être un tuple d'IDs
        if campeur == None:
            conditionCampeur = "true"
        elif campeur == 1:
            conditionCampeur = "campeur in (0,1)"
        elif campeur in (0,1,2) :
            conditionCampeur = "campeur=%d"%campeur
        else:
            conditionCampeur = "true"

        # Recherche des catégories
        req = """SELECT IDcategorie_tarif, nom, campeur
        FROM categories_tarifs 
        WHERE IDactivite=%d AND %s
        ORDER BY nom; """ % (IDactivite, conditionCampeur)
        DB.ExecuterReq(req,MsgBox="DLG_Inscription")
        listeCategories = DB.ResultatReq()

        for IDcategorie_tarif, nom, campeur in listeCategories :
            valeurs = { "ID" : IDcategorie_tarif, "nom" : nom, "campeur":campeur}
            self.listeDonnees.append(valeurs)
        DB.Close()
            
    def SetID(self, ID=None):
        index = 0
        for dictValeurs in self.listeDonnees :
            if ID == dictValeurs["ID"] :
                self.SetSelection(index)
                return
            index += 1
        
    def GetID(self):
        index = self.GetSelection()
        if index == -1 : return None
        ID = self.listeDonnees[index]["ID"]
        return ID
    
    def GetInfosSelection(self):
        index = self.GetSelection()
        if index == -1 : return None
        return self.listeDonnees[index]
    
    def SelectCategorieSelonVille(self):
        # pour un chhoix de tarif selon la ville
        return False

# -----------------------------------------------------------------------------------------------------------------------------------------------

class Dialog(wx.Dialog):
    def __init__(self, parent, mode="saisie", IDindividu=None, IDinscription=None, IDfamille=None, cp=None, ville=None, intro=None):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.IDindividu = IDindividu
        self.IDinscription = IDinscription
        self.IDfamille = IDfamille
        self.cp = cp
        self.ville = ville
        self.mode = mode
        intro = _("Sélectionner activité, groupe et catégorie de tarifs.")
        titre = _("Inscription à une activité")
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=20, nomImage="Images/22x22/Smiley_nul.png")
        
        self.ctrl_famille = Choix_famille(self)
        
        self.staticbox_activite_staticbox = wx.StaticBox(self, -1, _("1. Sélectionnez une activité"))
        self.ctrl_activites = ListBox(self, type="activites")
        self.ctrl_activites.SetMinSize((-1, 80))

        self.ctrl_ageInconnu = wx.StaticText(self,label="Date naissance inconnue")
        self.SetAgeInconnu(False)
        self.ageConnu = False

        self.ctrl_activites_valides = wx.CheckBox(self, -1, _("Afficher uniquement les activités ouvertes"))
        self.ctrl_activites_valides.SetFont(wx.Font(7, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL))
        self.ctrl_activites_valides.SetValue(True)
        self.IDactivite = self.ctrl_activites.GetID()

        self.staticbox_groupe_staticbox = wx.StaticBox(self, -1, _("2. Sélectionnez un groupe"))
        self.ctrl_groupes = ListBox(self, type="groupes", IDindividu = self.IDindividu)
        self.ctrl_groupes.SetMinSize((-1, 80))
        
        self.ctrl_groupes_valides = wx.CheckBox(self, -1, _("Filtrer les groupes selon l'âge de l'individu"))
        self.ctrl_groupes_valides.SetFont(wx.Font(7, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL))
        self.ctrl_groupes_valides.SetValue(True) 
        
        
        self.staticbox_categorie_staticbox = wx.StaticBox(self, -1, _("3. Catégorie de tarif et type d'effectif"))
        self.ctrl_categories = ListBox(self, type="categories")
        self.ctrl_categories.SetMinSize((-1, 50))
        
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png"))
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ok"), cheminImage=Chemins.GetStaticPath("Images/32x32/Valider.png"))
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Annuler"), cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png"))

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_CHECKBOX, self.OnCocheActivitesValides, self.ctrl_activites_valides)
        self.Bind(wx.EVT_CHECKBOX, self.OnCocheGroupesValides, self.ctrl_groupes_valides)

        # Init contrôles
        self.ctrl_activites.MAJ()

    def __set_properties(self):
        self.ctrl_ageInconnu.SetToolTip("Les conditions d'âge sur les groupes ne pouvent être calculées")
        self.SetTitle(_("DLG_Inscription"))
        self.ctrl_famille.SetToolTip(_("Sélectionnez une famille"))
        self.ctrl_activites.SetToolTip(_("Sélectionnez une activité"))
        self.ctrl_activites_valides.SetToolTip(_("Cochez cette case pour afficher uniquement les activités encore ouvertes à ce jour"))
        self.ctrl_groupes.SetToolTip(_("Sélectionnez un groupe"))
        self.ctrl_groupes_valides.SetToolTip(_("Cochez cette case pour afficher uniquement les groupes respectant les conditions d'âge"))
        self.ctrl_categories.SetToolTip(_("Sélectionnez une catégorie de tarif"))
        self.bouton_aide.SetToolTip(_("Cliquez ici pour obtenir de l'aide"))
        self.bouton_ok.SetToolTip(_("Cliquez ici pour valider"))
        self.bouton_annuler.SetToolTip(_("Cliquez ici pour annuler"))
        self.SetMinSize((480, 690))

        
    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=6, cols=1, vgap=5, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)
        
        # Famille
        grid_sizer_base.Add(self.ctrl_famille, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        # Activités
        staticbox_activite = wx.StaticBoxSizer(self.staticbox_activite_staticbox, wx.VERTICAL)
        grid_sizer_activite = wx.FlexGridSizer(rows=2, cols=1, vgap=2, hgap=2)
        grid_sizer_activite.Add(self.ctrl_activites, 1, wx.EXPAND, 0)
        grid_sizer_activite.Add(self.ctrl_activites_valides, 1,wx.ALIGN_RIGHT, 0)
        grid_sizer_activite.AddGrowableRow(0)
        grid_sizer_activite.AddGrowableCol(0)
        staticbox_activite.Add(grid_sizer_activite, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_base.Add(staticbox_activite, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        # Groupes
        staticbox_groupe = wx.StaticBoxSizer(self.staticbox_groupe_staticbox, wx.VERTICAL)
        grid_sizer_groupe = wx.FlexGridSizer(rows=2, cols=1, vgap=2, hgap=2)
        grid_sizer_groupe.Add(self.ctrl_groupes, 1, wx.EXPAND, 0)
        grid_sizer_actComplements = wx.FlexGridSizer(rows=1, cols=3, vgap=2, hgap=2)
        grid_sizer_actComplements.Add(self.ctrl_ageInconnu,0,wx.ALIGN_LEFT,0)
        grid_sizer_actComplements.Add((10,10),1,wx.EXPAND,0)
        grid_sizer_actComplements.Add(self.ctrl_groupes_valides, 0, wx.ALIGN_RIGHT, 0)
        grid_sizer_actComplements.AddGrowableCol(1)
        grid_sizer_groupe.Add(grid_sizer_actComplements, 1, wx.EXPAND, 0)
        grid_sizer_groupe.AddGrowableRow(0)
        grid_sizer_groupe.AddGrowableCol(0)
        staticbox_groupe.Add(grid_sizer_groupe, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_base.Add(staticbox_groupe, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        # Catégories de tarifs
        staticbox_categorie = wx.StaticBoxSizer(self.staticbox_categorie_staticbox, wx.VERTICAL)
        staticbox_categorie.Add(self.ctrl_categories, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_base.Add(staticbox_categorie, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=5, hgap=5)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(2)
##        grid_sizer_base.AddGrowableRow(3)
##        grid_sizer_base.AddGrowableRow(4)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen() 
    
    def SetAgeInconnu(self,activation):
        if activation:
            print("Rouge")
            self.ctrl_ageInconnu.SetForegroundColour((250,0,0)) # set text color
            self.ctrl_ageInconnu.SetBackgroundColour((230,230,230)) # set text back color
            self.ageConnu = False
        else:
            self.ctrl_ageInconnu.SetForegroundColour((230,230,230)) # set text color
            self.ctrl_ageInconnu.SetBackgroundColour((230,230,230)) # set text back color
            self.ageConnu = True
        self.Refresh()

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Activits1")

    def OnBoutonOk(self, event):
        # Vérification des données saisies
        IDactivite = self.ctrl_activites.GetID()
        if  IDactivite == None :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement sélectionner une activité !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDgroupe = self.ctrl_groupes.GetID()
        if  IDgroupe == None :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement sélectionner un groupe !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        infoGroupe = self.ctrl_groupes.GetInfosSelection()

        if self.ctrl_categories.GetID() == None and len(self.ctrl_categories.listeDonnees) > 0 :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement sélectionner une catégorie de tarifs !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        infoCategories = self.ctrl_categories.GetInfosSelection()
        if infoCategories["campeur"] == 1 and self.ageConnu == False and infoGroupe["conditionAge"]:
            mess = "Risque sur la condition d'âge\n\n"
            mess += "Vous avez choisi un tarif campeur, pour un groupe ayant des conditions sur l'âge,\n"
            mess += "et le campeur n'a pas de date de naissance connue. "
            wx.MessageBox(mess,"Info Non bloquante",style=wx.ICON_WARNING)

        #vérification de la présence de jours d'ouverture de l'activité
        infosActivite = self.ctrl_activites.GetInfosSelection()
        conditionDate = " AND (ouvertures.date >= '%s') AND (ouvertures.date <= '%s') " %(infosActivite["dateDeb"],infosActivite["dateFin"])

        db = GestionDB.DB()
        req = """SELECT Count(ouvertures.IDouverture)
                FROM ouvertures
                WHERE ouvertures.IDactivite = %d AND ouvertures.IDgroupe = %d %s;
                 """ % (IDactivite, IDgroupe, conditionDate)
        db.ExecuterReq(req,MsgBox="Recherche Ouvertures")
        recordset = db.ResultatReq()
        db.Close()
        if recordset[0][0] == 0 :
            dlg = wx.MessageDialog(self, _("Il n'y a aucune date d'ouverture dans cette activité pour ce groupe!"), _("Inscription impossible"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        # Vérification du nombre d'inscrits max du groupe
        db = GestionDB.DB()
        req = """
            SELECT groupes.nbre_inscrits_max, Count(matPieces.pieIDnumPiece)
            FROM (groupes 
                INNER JOIN matPieces ON groupes.IDgroupe = matPieces.pieIDgroupe) 
                INNER JOIN categories_tarifs ON matPieces.pieIDcategorie_tarif = categories_tarifs.IDcategorie_tarif
            WHERE ((matPieces.pieNature In ("RES","COM","FAC")) 
                    AND (groupes.IDgroupe = %d) 
                    AND (categories_tarifs.campeur = 1))
            GROUP BY groupes.nbre_inscrits_max ;
            """ % (IDgroupe)
        db.ExecuterReq(req,MsgBox="Recherche Nombre maxi du groupe")
        recordset = db.ResultatReq()
        db.Close()
        if len(recordset) > 0:
            nbre_inscrits_max, nbre_inscrits = recordset[0]
            if not nbre_inscrits_max: nbre_inscrits_max = 0
            if nbre_inscrits > 0 and nbre_inscrits_max >0:
                nbrePlacesRestantes = nbre_inscrits_max - nbre_inscrits
                if nbrePlacesRestantes <= 0 :
                    mess = "Nbre d'inscrit maximal atteint\n\n"
                    mess += "Le nombre maximal d'inscrits autorisé pour ce groupe, a été atteint !\n"
                    mess += "Vous êtes invité à mettre à jour les maximums prévus dans la gestion des activités\n\n"
                    mess += "Souhaitez-vous tout de même inscrire cet individu ?"
                    dlg = wx.MessageDialog(None,mess, _("Avertissement NON bloquant"),
                                           wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
                    reponse = dlg.ShowModal()
                    dlg.Destroy()
                    if reponse != wx.ID_YES :
                        return

        # Vérification du nombre d'inscrits max de l'activité
        nbre_inscrits_max = infosActivite["nbre_inscrits_max"]
        nbre_inscrits = infosActivite["nbre_inscrits"]
        if nbre_inscrits_max != None and nbre_inscrits != None :
            nbrePlacesRestantes = nbre_inscrits_max - nbre_inscrits
            if nbrePlacesRestantes <= 0 :
                dlg = wx.MessageDialog(None, _("Le nombre maximal d'inscrits autorisé pour cette activité a été atteint !\n\nSouhaitez-vous tout de même inscrire cet individu ?"), _("Nbre d'inscrit maximal atteint"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_EXCLAMATION)
                reponse = dlg.ShowModal()
                dlg.Destroy()
                if reponse != wx.ID_YES :
                    return

        # Fermeture de la fenêtre
        self.EndModal(wx.ID_OK)
    
    def OnCocheActivitesValides(self, event):
        self.ctrl_activites.MAJ()
        self.ctrl_groupes.Clear()
        self.ctrl_categories.Clear()
        
    def OnCocheGroupesValides(self, event):
        self.ctrl_groupes.MAJ()
        self.ctrl_categories.MAJ()

    def SetFamille(self, listeNoms=[], listeIDfamille=[], IDfamille=None, verrouillage=False) :
        listeDonnees = []
        for index in range(0, len(listeNoms)) :
            dictTemp = {"IDfamille" : listeIDfamille[index], "nom" : listeNoms[index] }
            listeDonnees.append(dictTemp)
        self.ctrl_famille.SetListeDonnees(listeDonnees)
        self.ctrl_famille.SetID(IDfamille)
        if len(listeIDfamille) < 2 or verrouillage == True :
            self.ctrl_famille.Enable(False)
            
    def GetIDfamille(self):
        return self.ctrl_famille.GetID() 

    def GetIDactivite(self):
        IDactivite = self.ctrl_activites.GetID()
        return IDactivite
    
    def GetNomActivite(self):
        return self.ctrl_activites.GetStringSelection() 
    
    def GetIDgroupe(self):
        IDgroupe = self.ctrl_groupes.GetID()
        return IDgroupe

    def GetNomGroupe(self):
        return self.ctrl_groupes.GetStringSelection() 

    def GetIDcategorie(self):
        IDcategorie = self.ctrl_categories.GetID()
        return IDcategorie

    def GetNomCategorie(self):
        return self.ctrl_categories.GetStringSelection() 
    
    def SetIDactivite(self, IDactivite=None):
        if IDactivite != None :
            self.ctrl_activites_valides.SetValue(False)
            self.ctrl_activites_valides.Enable(False)
            self.ctrl_activites.MAJ() 
            self.ctrl_activites.SetID(IDactivite)
            self.ctrl_groupes.MAJ(IDactivite)
            self.ctrl_categories.MAJ((IDactivite,self.parent.ctrl_groupes.campeur))
            
    def SetIDgroupe(self, IDgroupe=None):
        self.ctrl_groupes.SetID(IDgroupe)

    def SetIDcategorie(self, IDcategorie=None):
        self.ctrl_categories.SetID(IDcategorie)
    
if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = Dialog(None,IDindividu=12315)
    app.SetTopWindow(frame_1)
    frame_1.ShowModal()
    app.MainLoop()

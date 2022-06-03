#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys branche Matthania, modifs pour gestion des présences absence en forfaits datés
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB, Jacques Brunel
# Copyright:       (c) 2010-13 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#-----------------------------------------------------------


from Utils.UTILS_Traduction import _
import Chemins
import wx
from Ctrl import CTRL_Bouton_image
import wx.grid as gridlib
import datetime
import copy
import time
import textwrap
import operator

import GestionDB
from Data import DATA_Touches as Touches
from Ctrl import CTRL_Grille_renderers
from Ctrl import CTRL_Grille
from Utils import UTILS_Dates
from Utils import UTILS_Identification
from Utils import UTILS_Divers
from Utils import UTILS_Utilisateurs

from Ctrl.CTRL_Saisie_transport import DICT_CATEGORIES as DICT_CATEGORIES_TRANSPORTS


class CTRL_Couleur(wx.Choice):
    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1)
        self.parent = parent
        self.couleurs = [
            {"code": None, "label": _("Noir (par défaut)")},
            {"code": "red", "label": _("Rouge")},
            {"code": "blue", "label": _("Bleu")},
            {"code": "green", "label": _("Vert")},
            {"code": "purple", "label": _("Violet")},
            {"code": "yellow", "label": _("Jaune")},
            {"code": "pink", "label": _("Rose")},
            {"code": "gray", "label": _("Gris")},
            {"code": "orange", "label": _("Orange")},
            {"code": "brown", "label": _("Marron")},
        ]
        self.MAJ()
        self.Select(0)

    def MAJ(self):
        listeItems = []
        self.dictDonnees = {}
        index = 0
        for dictCouleur in self.couleurs:
            self.dictDonnees[index] = {"code": dictCouleur["code"], "label": dictCouleur["label"]}
            listeItems.append(dictCouleur["label"])
            index += 1
        self.SetItems(listeItems)

    def SetCode(self, code=None):
        for index, values in self.dictDonnees.items():
            if values["code"] == code:
                self.SetSelection(index)

    def GetCode(self):
        index = self.GetSelection()
        if index == -1 : return None
        return self.dictDonnees[index]["code"]


class DLG_Saisie_memo(wx.Dialog):
    def __init__(self, parent, texte="", couleur=None):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE)
        self.parent = parent

        self.label_texte = wx.StaticText(self, wx.ID_ANY, _("Texte :"))
        self.ctrl_texte = wx.TextCtrl(self, wx.ID_ANY, "", style=wx.TE_PROCESS_ENTER)
        self.ctrl_texte.SetMinSize((300, -1))

        self.label_couleur = wx.StaticText(self, wx.ID_ANY, _("Couleur :"))
        self.ctrl_couleur = CTRL_Couleur(self)

        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ok"), cheminImage="Images/32x32/Valider.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Annuler"), cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)
        self.ctrl_texte.Bind(wx.EVT_KEY_DOWN, self.OnKey)

        # Init contrôles
        if texte:
            self.SetTitle(_("Modification d'un mémo journalier"))
            self.ctrl_texte.SetValue(texte)
            self.ctrl_couleur.SetCode(couleur)
        else:
            self.SetTitle(_("Saisie d'un mémo journalier"))
        self.ctrl_texte.SetFocus()

    def __set_properties(self):
        self.ctrl_texte.SetToolTip(wx.ToolTip(_("Saisissez le texte du mémo")))
        self.ctrl_couleur.SetToolTip(wx.ToolTip(_("Sélectionnez une couleur (Noir par défaut). Cette couleur sera utilisée dans l'édition de la liste des consommations au format PDF).")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_("Cliquez ici pour valider")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Cliquez ici pour annuler")))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(2, 1, 10, 10)
        grid_sizer_haut = wx.FlexGridSizer(3, 2, 10, 10)

        grid_sizer_haut.Add(self.label_texte, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_haut.Add(self.ctrl_texte, 0, wx.EXPAND, 0)

        grid_sizer_haut.Add(self.label_couleur, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_haut.Add(self.ctrl_couleur, 0, 0, 0)

        grid_sizer_haut.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_haut, 1, wx.ALL | wx.EXPAND, 10)

        grid_sizer_boutons = wx.FlexGridSizer(1, 3, 10, 10)
        grid_sizer_boutons.Add((20, 20), 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()

    def OnKey(self, event):
        if event.GetKeyCode() in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
            self.OnBoutonOk()
        event.Skip()

    def OnBoutonAnnuler(self, event):
        self.EndModal(wx.ID_CANCEL)

    def OnBoutonOk(self, event=None):
        self.texte = self.ctrl_texte.GetValue()
        self.couleur = self.ctrl_couleur.GetCode()
        self.EndModal(wx.ID_OK)


class CaseSeparationDate():
    def __init__(self, ligne, grid, numLigne=None, numColonne=None, couleurFond=(255, 255, 255)):
        self.typeCase = "date"
        grid.SetReadOnly(numLigne, numColonne, True)
        grid.SetCellBackgroundColour(numLigne, numColonne, couleurFond)

    def GetTypeUnite(self):
        return "separationDate"

    def OnClick(self):
        pass
    
    def OnContextMenu(self):
        pass
    
    def GetTexteInfobulle(self):
        return None

    def GetStatutTexte(self, x, y):
        return None

class CaseSeparationActivite():
    def __init__(self, ligne, grid, numLigne=None, numColonne=None, IDactivite=None, estMemo=False):
        self.typeCase = "activite"
        self.IDactivite = IDactivite
        self.couleurFond = CTRL_Grille.COULEUR_COLONNE_ACTIVITE
        
        # Dessin de la case
        self.renderer = CTRL_Grille_renderers.CaseActivite(self)
        if self.IDactivite != None :
            if grid.dictActivites != None :
                if IDactivite in grid.dictActivites :
                    labelActivite = grid.dictActivites[IDactivite]["nom"]
                else :
                    labelActivite = _("Activité inconnue")
            else:
                labelActivite = _("Activité ID%d") % IDactivite
        if estMemo == True :
            labelActivite = _("Informations")
        grid.SetCellValue(numLigne, numColonne, labelActivite)
        grid.SetCellAlignment(numLigne, numColonne, wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)
        grid.SetCellRenderer(numLigne, numColonne, self.renderer)
        grid.SetReadOnly(numLigne, numColonne, True)

    def GetTypeUnite(self):
        return "separationActivite"

    def OnClick(self):
        pass
    
    def OnContextMenu(self):
        pass

    def GetTexteInfobulle(self):
        return None

    def GetStatutTexte(self, x, y):
        return None

class CaseMemo():
    def __init__(self, ligne, grid, numLigne=None, numColonne=None, IDindividu=None, date=None, texte="", IDmemo=None, couleur=None):
        self.typeCase = "memo"
        self.grid = grid
        self.ligne = ligne
        self.numLigne = numLigne
        self.numColonne = numColonne
        self.IDindividu = IDindividu
        self.date = date
        self.texte = texte
        self.IDmemo = IDmemo
        self.statut = None
        self.couleur = couleur

        # Dessin de la case
        self.renderer = CTRL_Grille_renderers.CaseMemo(self)
##        self.renderer = gridlib.GridCellAutoWrapStringRenderer()
        self.editor = gridlib.GridCellTextEditor()
        self.grid.SetCellValue(self.numLigne, self.numColonne, self.texte)
        self.grid.SetCellRenderer(self.numLigne, self.numColonne, self.renderer)
        self.grid.SetCellAlignment(self.numLigne, self.numColonne, wx.ALIGN_LEFT, wx.ALIGN_CENTRE)
        self.grid.SetCellEditor(self.numLigne, self.numColonne, self.editor)

    def GetTypeUnite(self):
        return "memo"

    def GetTexte(self):
        return self.grid.GetCellValue(self.numLigne, self.numColonne)
    
    def MemoriseValeurs(self):
        texte = self.grid.GetCellValue(self.numLigne, self.numColonne)
        # Création
        if texte != "" and self.IDmemo == None : self.statut = "ajout"
        # Modification
        if texte != "" and self.IDmemo != None : self.statut = "modification"
        # Suppression
        if texte == "" and self.IDmemo == None : self.statut = None
        if texte == "" and self.IDmemo != None : self.statut = "suppression"
        self.texte = texte
        if (self.IDindividu, self.date) in self.grid.dictMemos :
            self.grid.dictMemos[(self.IDindividu, self.date)]["texte"] = self.texte
            self.grid.dictMemos[(self.IDindividu, self.date)]["statut"] = self.statut
            self.grid.dictMemos[(self.IDindividu, self.date)]["couleur"] = self.couleur
        else:
            self.grid.dictMemos[(self.IDindividu, self.date)] = {"texte" : self.texte, "IDmemo" : None, "statut" : self.statut, "couleur": self.couleur}

    def OnClick(self):
        pass
    
    def OnContextMenu(self):
        pass

    def GetTexteInfobulle(self):
        dictDonnees = {}
        
        # Formatage du texte
        if self.texte != "" :
            listeLignes = textwrap.wrap(self.texte, 45)
            texte = '\n'.join(listeLignes) + "\n\n"
        else :
            texte = _("Aucun mémo\n\n")
            
        dictDonnees["titre"] = _("Mémo journalier")
        dictDonnees["texte"] = texte
        dictDonnees["pied"] = _("Double-cliquez sur la case pour modifier")
        dictDonnees["bmp"] = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_ANY)
        return dictDonnees
    
    def OnDoubleClick(self):
        # Récupération du mémo
        texte = self.grid.GetCellValue(self.numLigne, self.numColonne)
        
        # Boîte de dialogue pour modification du mémo
        dlg = DLG_Saisie_memo(None, texte=texte, couleur=self.couleur)
        if dlg.ShowModal() == wx.ID_OK:
            self.texte = dlg.texte
            self.couleur = dlg.couleur
            dlg.Destroy()
        else:
            dlg.Destroy()

        # Mémorisation du mémo
        self.grid.SetCellValue(self.numLigne, self.numColonne, self.texte)
        self.MemoriseValeurs()
        
    def GetStatutTexte(self, x, y):
        return _("Double-cliquez sur la case 'Mémo' pour ajouter, modifier ou supprimer un mémo")
    
    def SetTexte(self, texte=""):
        """ Modification manuelle du mémo """
        self.grid.SetCellValue(self.numLigne, self.numColonne, texte)
        self.MemoriseValeurs()
        
        

class CaseTransports():
    def __init__(self, ligne, grid, numLigne=None, numColonne=None, IDindividu=None, date=None):
        self.typeCase = "transports"
        self.grid = grid
        self.ligne = ligne
        self.numLigne = numLigne
        self.numColonne = numColonne
        self.IDindividu = IDindividu
        self.date = date
        self.statut = None
        
        self.couleurFond = (230, 230, 255)
        
        # Dessin de la case
        self.renderer = CTRL_Grille_renderers.CaseTransports(self)
        self.grid.SetCellValue(self.numLigne, self.numColonne, "")
        self.grid.SetCellAlignment(self.numLigne, self.numColonne, wx.ALIGN_LEFT, wx.ALIGN_CENTRE)
        self.grid.SetCellRenderer(self.numLigne, self.numColonne, self.renderer)
        self.grid.SetReadOnly(self.numLigne, self.numColonne, True)
        
        self.MAJ() 

    def GetTypeUnite(self):
        return "transports"

    def MAJ(self):
        self.dictTransports = self.grid.RechercheTransports(IDindividu=self.IDindividu, date=self.date)
        self.grid.Refresh()
    
    def OnClick(self):
        # Récupère la liste des IDtransport actuels
        listeIDinitiale = list(self.dictTransports.keys())
        
        # Label de la ligne
        if self.ligne.modeLabel == "date" :
            label = "du %s" % self.ligne.labelLigne
        else :
            label = _("de %s") % self.ligne.labelLigne
        
        # Dialog
        from Dlg import DLG_Transports_grille
        dlg = DLG_Transports_grille.Dialog(None, grid=self.grid, label=label, IDindividu=self.IDindividu, date=self.date, dictTransports=copy.deepcopy(self.dictTransports))  
        if dlg.ShowModal() == wx.ID_OK:
            dictTransports = dlg.GetDictTransports()
            # Actualise la liste des transports de la grille
            listeNewID = []
            for IDtransport, dictTemp in dictTransports.items() :
                listeNewID.append(IDtransport)
                if (self.IDindividu in self.grid.dict_transports) == False :
                    self.grid.dict_transports[self.IDindividu] = {}
                self.grid.dict_transports[self.IDindividu][IDtransport] = dictTemp
            self.dictTransports = dictTransports
            
            # Supprime les suppressions
            for IDtransport in listeIDinitiale :
                if IDtransport not in listeNewID :
                    del self.grid.dict_transports[self.IDindividu][IDtransport]
            
            # MAJ case
            self.MAJ() 
        
        dlg.Destroy() 
    
    def OnContextMenu(self):
        pass

    def GetTexteInfobulle(self):
        """ Texte pour info-bulle """
        dictDonnees = {}
        dictDonnees["titre"] = _("Transports")
        dictDonnees["bmp"] = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Transport.png"), wx.BITMAP_TYPE_ANY)
        dictDonnees["pied"] = _("Cliquez sur la case pour modifier")
        dictDonnees["couleur"] = self.couleurFond
        
        dictTransports = {}
        for IDtransport in CTRL_Grille_renderers.TriTransports(self.dictTransports) :
            dictTemp = self.dictTransports[IDtransport]
            categorie = dictTemp["categorie"]
            labelCategorie = DICT_CATEGORIES_TRANSPORTS[categorie]["label"]
                
            # Analyse du départ
            depart_nom = ""
            if dictTemp["depart_IDarret"] != None and dictTemp["depart_IDarret"] in CTRL_Grille.DICT_ARRETS :
                depart_nom = CTRL_Grille.DICT_ARRETS[dictTemp["depart_IDarret"]]
            if dictTemp["depart_IDlieu"] != None and dictTemp["depart_IDlieu"] in CTRL_Grille.DICT_LIEUX :
                depart_nom = CTRL_Grille.DICT_LIEUX[dictTemp["depart_IDlieu"]]
            if dictTemp["depart_localisation"] != None :
                depart_nom = self.AnalyseLocalisation(dictTemp["depart_localisation"])
            
            depart_heure = ""
            if dictTemp["depart_heure"] != None :
                depart_heure = dictTemp["depart_heure"].replace(":", "h")

            # Analyse de l'arrivée
            arrivee_nom = ""
            if dictTemp["arrivee_IDarret"] != None and dictTemp["arrivee_IDarret"] in CTRL_Grille.DICT_ARRETS :
                arrivee_nom = CTRL_Grille.DICT_ARRETS[dictTemp["arrivee_IDarret"]]
            if dictTemp["arrivee_IDlieu"] != None and dictTemp["arrivee_IDlieu"] in CTRL_Grille.DICT_LIEUX :
                arrivee_nom = CTRL_Grille.DICT_LIEUX[dictTemp["arrivee_IDlieu"]]
            if dictTemp["arrivee_localisation"] != None :
                arrivee_nom = self.AnalyseLocalisation(dictTemp["arrivee_localisation"])
            
            arrivee_heure = ""
            if dictTemp["arrivee_heure"] != None :
                arrivee_heure = dictTemp["arrivee_heure"].replace(":", "h")
                
            # Création du label du schedule
            label = "%s %s > %s %s" % (depart_heure, depart_nom, arrivee_heure, arrivee_nom)
            
            if (labelCategorie in dictTransports) == False :
                dictTransports[labelCategorie] = []
            dictTransports[labelCategorie].append(label)
        
        # Regroupement par moyen de transport
        texte = ""
        for labelCategorie, listeTextes in dictTransports.items() :
            texte += "</b>%s\n" % labelCategorie
            for texteLigne in listeTextes :
                texte += "%s\n" % texteLigne
            texte += "\n"
        
        dictDonnees["texte"] = texte

        if len(dictTransports) == 0 :
            dictDonnees["texte"] = _("Aucun transport\n\n")

        return dictDonnees

    def AnalyseLocalisation(self, texte=""):
        code = texte.split(";")[0]
        if code == "DOMI" :
            return _("Domicile")
        if code == "ECOL" :
            IDecole = int(texte.split(";")[1])
            if IDecole in CTRL_Grille.DICT_ECOLES:
                return CTRL_Grille.DICT_ECOLES[IDecole]
        if code == "ACTI" :
            IDactivite = int(texte.split(";")[1])
            if IDactivite in CTRL_Grille.DICT_ACTIVITES:
                return CTRL_Grille.DICT_ACTIVITES[IDactivite]
        if code == "AUTR" :
            code, nom, rue, cp, ville = texte.split(";")
            return "%s %s %s %s" % (nom, rue, cp, ville)
        return ""

    def GetStatutTexte(self, x, y):
        return _("Double-cliquez sur la case 'Transports' pour ajouter, modifier ou supprimer un transport")





class Case():
    def __init__(self, ligne, grid, numLigne=None, numColonne=None, IDindividu=None, IDfamille=None, date=None, IDunite=None, IDactivite=None, verrouillage=0):
        self.typeCase = "consommation"
        self.grid = grid
        self.ligne = ligne
        self.numLigne = numLigne
        self.numColonne = numColonne
        self.IDindividu = IDindividu
        self.IDfamille = IDfamille
        self.date = date
        self.IDunite = IDunite
        self.IDactivite = IDactivite
        self.IDinscription = None
        self.IDgroupe = None
        self.badgeage_debut = None
        self.badgeage_fin = None

        # Récupération du groupe en mode INDIVIDU
        if self.IDindividu in grid.dictInfosInscriptions :
            if self.IDactivite in grid.dictInfosInscriptions[self.IDindividu] :
                if self.grid.mode == "individu" :
                    self.IDgroupe = grid.GetGrandParent().panel_activites.ctrl_activites.GetIDgroupe(self.IDactivite, self.IDindividu)
                if self.IDgroupe == None :
                    self.IDgroupe = grid.dictInfosInscriptions[self.IDindividu][self.IDactivite]["IDgroupe"]

        # Recherche si l'activité est ouverte
        self.ouvert = self.EstOuvert()

        # Récupération des infos sur l'inscription
        self.dictInfosInscriptions = self.GetInscription() 
        if self.dictInfosInscriptions != None :
            self.IDcategorie_tarif = self.dictInfosInscriptions["IDcategorie_tarif"]

            
    def GetTypeUnite(self):
        return self.grid.dictUnites[self.IDunite]["type"]

    def EstOuvert(self):
        """ Recherche si l'unité est ouverte à cette date """
        ouvert = False
        if self.date in self.grid.dictOuvertures:
            if self.IDgroupe in self.grid.dictOuvertures[self.date]:
                if self.IDunite in self.grid.dictOuvertures[self.date][self.IDgroupe]:
                    ouvert = True
        return ouvert

    def GetInscription(self):
        """ Recherche s'il y a une conso pour cette case """
        try :
            dictInfosInscriptions = self.grid.dictInfosInscriptions[self.IDindividu][self.IDactivite]
        except : 
            dictInfosInscriptions = None
        return dictInfosInscriptions

    def MAJ_facturation(self, modeSilencieux=False, evenement=None, action="saisie"):
        # Vérifie la période de gestion
        if self.grid.gestion.Verification("consommations", self.date) == False : return False

        listeEtiquettes = []
        for conso in self.GetListeConso() :
            IDprestation = conso.IDprestation
            listeEtiquettes.extend(conso.etiquettes)
            if IDprestation in self.grid.dictPrestations :
                if self.grid.dictPrestations[IDprestation]["IDfacture"] != None :
                    nomUnite = self.grid.dictUnites[self.IDunite]["nom"]
                    dateComplete = UTILS_Dates.DateComplete(self.date)
                    if self.IDindividu in self.grid.dictInfosIndividus :
                        nom = self.grid.dictInfosIndividus[self.IDindividu]["nom"]
                        prenom = self.grid.dictInfosIndividus[self.IDindividu]["prenom"]
                        if prenom == None :
                            prenom = ""
                    else :
                        nom = "?"
                        prenom = "?"
                    nomCase = _("%s du %s pour %s %s") % (nomUnite, dateComplete, nom, prenom)
                    if modeSilencieux == False :
                        dlg = wx.MessageDialog(self.grid, _("La prestation correspondant à cette consommation apparaît déjà sur une facture.\n\nIl est donc impossible de la modifier ou de la supprimer."), nomCase, wx.OK | wx.ICON_ERROR)
                        dlg.ShowModal()
                        dlg.Destroy()
                    return False

        self.grid.Facturation(self.IDactivite, self.IDindividu, self.IDfamille, self.date, self.IDcategorie_tarif, IDgroupe=self.IDgroupe, case=self, etiquettes=listeEtiquettes, modeSilencieux=modeSilencieux, action=action)
        self.grid.ProgrammeTransports(self.IDindividu, self.date, self.ligne)

    def GetTexteInfobulleConso(self, conso=None, evenement=None):
        """ Renvoie le texte pour l'infobulle de la case """
        dictDonnees = {}
        
        # Titre
        nomUnite = self.grid.dictUnites[self.IDunite]["nom"]
        dateComplete = UTILS_Dates.DateComplete(self.date)
        dictDonnees["titre"] = "%s du %s\n\n" % (nomUnite, dateComplete)
        
        # Image
        dictDonnees["bmp"] = None
        
        texte = ""

        if evenement != None:
            texte += "===== %s =====\n\n" % evenement.GetStatutTexte()
        
        if conso != None :
            
            # Etiquettes
            nbreEtiquettes = len(conso.etiquettes)
            if nbreEtiquettes > 0 :
                if nbreEtiquettes == 1 :
                    texte += _("1 étiquette : \n")
                else :
                    texte += _("%d étiquettes : \n" % nbreEtiquettes)
                for IDetiquette in conso.etiquettes :
                    if IDetiquette in self.grid.dictEtiquettes :
                        dictEtiquette = self.grid.dictEtiquettes[IDetiquette]
                        texte += "   - %s \n" % dictEtiquette["label"]
                texte += "\n"
                
            # Heures de la consommation
            if conso.etat in ("reservation", "attente", "present") :
                if conso.heure_debut == None or conso.heure_fin == None :
                    texte += _("Horaire de la consommation non spécifié\n")
                else:
                    texte += _("De %s à %s\n") % (conso.heure_debut.replace(":","h"), conso.heure_fin.replace(":","h"))
                if conso.IDgroupe in self.grid.dictGroupes :
                    texte += _("Sur le groupe %s \n") % self.grid.dictGroupes[conso.IDgroupe]["nom"]
                else:
                    texte += _("Groupe non spécifié\n")
            
            # Quantité
            if conso.quantite != None :
                texte += _("Quantité : %d\n") % conso.quantite
        
        texte += "\n" 
        
        # Si unité fermée
        if self.ouvert == False :
            return None

        # Nbre de places
        dictInfosPlaces = self.GetInfosPlaces()
        if dictInfosPlaces != None :
            listeUnitesRemplissage = []
            hasHoraires = False
            for IDunite_remplissage in self.grid.dictUnitesRemplissage[self.IDunite] :
                nom = self.grid.dictRemplissage[IDunite_remplissage]["nom"]
                heure_min = UTILS_Dates.HeureStrEnTime(self.grid.dictRemplissage[IDunite_remplissage]["heure_min"])
                heure_max = UTILS_Dates.HeureStrEnTime(self.grid.dictRemplissage[IDunite_remplissage]["heure_max"])
                if str(heure_min) not in ("None", "00:00:00") or str(heure_max) not in ("None", "00:00:00") :
                    hasHoraires = True
                listeUnitesRemplissage.append((IDunite_remplissage, nom, heure_min, heure_max))


                if hasHoraires == True :
                    # Version pour unités de remplissage AVEC horaires :
                    nbrePlacesRestantes = None
                    for IDunite_remplissage, nom, heure_min, heure_max in listeUnitesRemplissage :

                        nbrePlacesInitial = dictInfosPlaces[IDunite_remplissage]["nbrePlacesInitial"]
                        nbrePlacesPrises = dictInfosPlaces[IDunite_remplissage]["nbrePlacesPrises"]
                        nbrePlacesRestantes = dictInfosPlaces[IDunite_remplissage]["nbrePlacesRestantes"]
                        nbreAttente = dictInfosPlaces[IDunite_remplissage]["nbreAttente"]
                        seuil_alerte = dictInfosPlaces[IDunite_remplissage]["seuil_alerte"]

                        if str(heure_min) not in ("None", "00:00:00") and str(heure_max) not in ("None", "00:00:00") :
                            texte += _("%s (de %s à %s) : \n") % (nom, UTILS_Dates.DatetimeTimeEnStr(heure_min), UTILS_Dates.DatetimeTimeEnStr(heure_max))
                        else :
                            texte += "%s : \n" % nom
                        if nbrePlacesInitial not in (None, 0) :
                            texte += _("   - Nbre maximal de places  : %d \n") % nbrePlacesInitial
                        else:
                            texte += _("   - Aucune limitation du nbre de places\n")
                        texte += _("   - Nbre de places prises : %d \n") % nbrePlacesPrises
                        if nbrePlacesRestantes != None and nbrePlacesInitial not in (None, 0) :
                            texte += _("   - Nbre de places disponibles : %d \n") % nbrePlacesRestantes
                        # texte += _("   - Seuil d'alerte : %d \n") % seuil_alerte
                        texte += _("   - Nbre d'individus sur liste d'attente : %d \n") % nbreAttente

                if hasHoraires == False :
                    # Version pour unités de remplissage SANS horaires :
                    nbrePlacesRestantes = None
                    for IDunite_remplissage, nom, heure_min, heure_max in listeUnitesRemplissage :
                        if nbrePlacesRestantes == None or dictInfosPlaces[IDunite_remplissage]["nbrePlacesRestantes"] < nbrePlacesRestantes :
                            nbrePlacesInitial = dictInfosPlaces[IDunite_remplissage]["nbrePlacesInitial"]
                            nbrePlacesPrises = dictInfosPlaces[IDunite_remplissage]["nbrePlacesPrises"]
                            nbrePlacesRestantes = dictInfosPlaces[IDunite_remplissage]["nbrePlacesRestantes"]
                            nbreAttente = dictInfosPlaces[IDunite_remplissage]["nbreAttente"]
                            seuil_alerte = dictInfosPlaces[IDunite_remplissage]["seuil_alerte"]

                    if nbrePlacesInitial not in (None, 0) :
                        texte += _("Nbre maximal de places  : %d \n") % nbrePlacesInitial
                    else:
                        texte += _("Aucune limitation du nbre de places\n")
                    texte += _("Nbre de places prises : %d \n") % nbrePlacesPrises
                    if nbrePlacesRestantes != None and nbrePlacesInitial not in (None, 0) :
                        texte += _("Nbre de places disponibles : %d \n") % nbrePlacesRestantes
                    # texte += _("Seuil d'alerte : %d \n") % seuil_alerte
                    texte += _("Nbre d'individus sur liste d'attente : %d \n") % nbreAttente

            else:
                texte += _("Aucune limitation du nombre de places\n")

            
        # Etat de la case
        texte += "\n"
        if conso != None and conso.etat in ("reservation", "attente", "refus", "present") :
            date_saisie_FR = UTILS_Dates.DateComplete(conso.date_saisie)
            if conso.etat == "reservation" or conso.etat == "present" : texte += _("Consommation réservée le %s\n") % date_saisie_FR
            if conso.etat == "attente" : texte += _("Consommation mise en attente le %s\n") % date_saisie_FR
            if conso.etat == "refus" : texte += _("Consommation refusée le %s\n") % date_saisie_FR
            if conso.IDutilisateur != None :
                dictUtilisateur = UTILS_Identification.GetAutreDictUtilisateur(conso.IDutilisateur)
                if dictUtilisateur != None :
                    texte += _("Par %s %s\n") % (dictUtilisateur["prenom"], dictUtilisateur["nom"])
                else:
                    texte += _("Par l'utilisateur ID%d\n") % conso.IDutilisateur
            texte += "\n"
        # Infos Individu
        if self.IDindividu in self.grid.dictInfosIndividus :
            nom = self.grid.dictInfosIndividus[self.IDindividu]["nom"]
            prenom = self.grid.dictInfosIndividus[self.IDindividu]["prenom"]
        else :
            nom = "?"
            prenom = "?"
        texte += _("Informations sur %s %s : \n") % (prenom, nom)
        date_naiss = self.grid.dictInfosIndividus[self.IDindividu]["date_naiss"]
        if date_naiss != None :
            ageActuel = UTILS_Dates.CalculeAge(datetime.date.today(), date_naiss)
            texte += _("   - Age actuel : %d ans \n") % ageActuel
            if conso != None and conso.etat != None :
                ageConso = UTILS_Dates.CalculeAge(self.date, date_naiss)
                texte += _("   - Age lors de la consommation : %d ans \n") % ageConso
        else:
            texte += _("   - Date de naissance inconnue ! \n")
        # Infos inscription :
        nom_categorie_tarif = self.dictInfosInscriptions["nom_categorie_tarif"]
        if conso != None and conso.etat in ("reservation", "absenti", "absentj", "present") :
            texte += "\n"
            texte += _("Catégorie de tarif : '%s'\n") % nom_categorie_tarif
        # Déductions
        if conso != None :
            if conso.IDprestation in self.grid.dictDeductions :
                listeDeductions = self.grid.dictDeductions[conso.IDprestation]
                if len(listeDeductions) == 1 :
                    texte += _("1 déduction sur la prestation :\n")
                else:
                    texte += _("%d déductions sur la prestation :\n") % len(listeDeductions)
                for dictDeduction in listeDeductions :
                    texte += "   > %.2f € (%s)\n" % (dictDeduction["montant"], dictDeduction["label"])
        
        if texte.endswith("\n") : 
            texte = texte[:-1]
        dictDonnees["texte"] = texte
        
        # Pied
        dictDonnees["pied"] = _("Cliquez sur le bouton droit de la souris pour plus d'infos")
        
        # Couleur
        if conso == None and self.CategorieCase == "multihoraires" :
            dictDonnees["couleur"] = wx.Colour(255, 255, 255)
        else :
            dictDonnees["couleur"] = self.renderer.GetCouleur(conso)
            
        return dictDonnees

    def ContextMenu(self, conso=None):
        if self.ouvert == False :
            return
        
        # Création du menu contextuel
        menuPop = wx.Menu()

        # Item IDENTIFICATION DE LA CASE
        nomUnite = self.grid.dictUnites[self.IDunite]["nom"]
        dateComplete = UTILS_Dates.DateComplete(self.date)
        texteItem = "- %s du %s -" % (nomUnite, dateComplete)
        item = wx.MenuItem(menuPop, 10, texteItem)
        menuPop.Append(item)
        item.Enable(False)

        # Commandes spécifiques
        if self.grid.tarifsForfaitsCreditsPresents == True :
            menuPop.AppendSeparator()

            item = wx.MenuItem(menuPop, 200, _("Appliquer un forfait crédit"))
            item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Forfait.png"), wx.BITMAP_TYPE_PNG))
            menuPop.Append(item)
            self.grid.Bind(wx.EVT_MENU, self.AppliquerForfaitCredit, id=200)            

        # Etiquettes
        if conso != None and conso.etat != None :
            menuPop.AppendSeparator()
            
            item = wx.MenuItem(menuPop, 300, _("Sélectionner des étiquettes"))
            item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Etiquette.png"), wx.BITMAP_TYPE_PNG))
            menuPop.Append(item)
            self.grid.Bind(wx.EVT_MENU, self.SelectionnerEtiquettes, id=300)            
        
        if conso == None or conso.etat == None :
            menuPop.AppendSeparator()

            item = wx.MenuItem(menuPop, 210, _("Ajouter"))
            item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_PNG))
            menuPop.Append(item)
            self.grid.Bind(wx.EVT_MENU, self.Ajouter, id=210)            

        if conso != None and conso.etat != None :
            menuPop.AppendSeparator()
            
            if self.grid.dictUnites[conso.case.IDunite]["type"] != "Unitaire" :
                item = wx.MenuItem(menuPop, 220, _("Modifier"))
                item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_PNG))
                menuPop.Append(item)
                self.grid.Bind(wx.EVT_MENU, self.Modifier, id=220)            

            item = wx.MenuItem(menuPop, 230, _("Supprimer"))
            item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_PNG))
            menuPop.Append(item)
            self.grid.Bind(wx.EVT_MENU, self.Supprimer, id=230)            
        
        # Etat de la consommation
        if conso != None and conso.etat in ("reservation", "present", "absenti", "absentj") :
            menuPop.AppendSeparator()
            
            item = wx.MenuItem(menuPop, 60, _("Pointage en attente"), kind=wx.ITEM_RADIO)
            menuPop.Append(item)
            if conso.etat == "reservation" : item.Check(True)
            self.grid.Bind(wx.EVT_MENU, self.SetEtat, id=60)
            
            item = wx.MenuItem(menuPop, 70, _("Présent"), kind=wx.ITEM_RADIO)
            menuPop.Append(item)
            if conso.etat == "present" : item.Check(True)
            self.grid.Bind(wx.EVT_MENU, self.SetEtat, id=70)
            
            item = wx.MenuItem(menuPop, 80, _("Absence justifiée"), kind=wx.ITEM_RADIO)
            menuPop.Append(item)
            if conso.etat == "absentj" : item.Check(True)
            self.grid.Bind(wx.EVT_MENU, self.SetEtat, id=80)
            
            item = wx.MenuItem(menuPop, 90, _("Absence injustifée"), kind=wx.ITEM_RADIO)
            menuPop.Append(item)
            if conso.etat == "absenti" : item.Check(True)
            self.grid.Bind(wx.EVT_MENU, self.SetEtat, id=90)
        
        if conso != None and conso.etat in ("reservation", "attente", "refus") and conso.forfait == None :
            menuPop.AppendSeparator()
            item = wx.MenuItem(menuPop, 30, _("Réservation"), kind=wx.ITEM_RADIO)
            menuPop.Append(item)
            if conso.etat == "reservation" : item.Check(True)
            self.grid.Bind(wx.EVT_MENU, self.SetEtat, id=30)
            item = wx.MenuItem(menuPop, 40, _("Attente"), kind=wx.ITEM_RADIO)
            menuPop.Append(item)
            if conso.etat == "attente" : item.Check(True)
            self.grid.Bind(wx.EVT_MENU, self.SetEtat, id=40)
            item = wx.MenuItem(menuPop, 50, _("Refus"), kind=wx.ITEM_RADIO)
            menuPop.Append(item)
            if conso.etat == "refus" : item.Check(True)
            self.grid.Bind(wx.EVT_MENU, self.SetEtat, id=50)
        
        # Changement de Groupe
        listeGroupes = []
        for IDgroupe, dictGroupe in self.grid.dictGroupes.items():
            if dictGroupe["IDactivite"] == self.IDactivite :
                listeGroupes.append( (dictGroupe["ordre"], dictGroupe["nom"], IDgroupe) )
        listeGroupes.sort() 
        if conso != None and len(listeGroupes) > 0 and conso.etat in ("reservation", "attente", "refus") :
            menuPop.AppendSeparator()
            for ordreGroupe, nomGroupe, IDgroupe in listeGroupes :
                IDitem = 10000 + IDgroupe
                item = wx.MenuItem(menuPop, IDitem, nomGroupe, kind=wx.ITEM_RADIO)
                menuPop.Append(item)
                if conso.IDgroupe == IDgroupe : item.Check(True)
                self.grid.Bind(wx.EVT_MENU, self.SetGroupe, id=IDitem)
                
        # Détail de la consommation
        if conso != None and conso.etat in ("reservation", "present", "absenti", "absentj", "attente", "refus") :
            menuPop.AppendSeparator()
            
            item = wx.MenuItem(menuPop, 100, _("Recalculer la prestation"))
            bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Euro.png"), wx.BITMAP_TYPE_PNG)
            item.SetBitmap(bmp)
            menuPop.Append(item)
            self.grid.Bind(wx.EVT_MENU, self.MAJ_facturation_menu, id=100)            
            
            item = wx.MenuItem(menuPop, 20, _("Détail de la consommation"))
            bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Calendrier_zoom.png"), wx.BITMAP_TYPE_PNG)
            item.SetBitmap(bmp)
            menuPop.Append(item)
            self.grid.Bind(wx.EVT_MENU, self.DLG_detail, id=20)
                            
        self.grid.PopupMenu(menuPop)
        menuPop.Destroy()
    
    def MAJ_facturation_menu(self, event):
        self.MAJ_facturation() 
        
    def AppliquerForfaitCredit(self, event=None):
        try:
            self.grid.GetGrandParent().panel_forfaits.Ajouter(date_debut=self.date, IDfamille=self.IDfamille)
        except:
            self.grid.GetGrandParent().GetParent().panel_forfaits.Ajouter(date_debut=self.date, IDfamille=self.IDfamille)
        
    def GetInfosPlaces(self):
        if (self.IDunite in self.grid.dictUnitesRemplissage) == False :
            return None
        
        try :
            etiquettesCoches = self.grid.GetGrandParent().panel_etiquettes.GetCoches(self.IDactivite)
        except :
            etiquettesCoches = []
            
        # Recherche des nbre de places
        dictInfosPlaces = {}
        for IDunite_remplissage in self.grid.dictUnitesRemplissage[self.IDunite] :
            
            etiquettesRemplissage = self.grid.dictRemplissage[IDunite_remplissage]["etiquettes"]
            
            # Récupère le nombre de places restantes pour le groupe
            nbrePlacesInitial = 0
            try :
                nbrePlacesInitial = self.grid.dictRemplissage[IDunite_remplissage][self.date][self.IDgroupe]
            except :
                nbrePlacesInitial = 0
            
            # Filtre étiquettes
            if len(etiquettesRemplissage) > 0 :
                etiquettesCommunes = set(etiquettesRemplissage) & set(etiquettesCoches)
                if len(etiquettesCommunes) == 0 :
                    nbrePlacesInitial = 0
                
            nbrePlacesPrises = 0
            nbreAttente = 0
            try :
                d = self.grid.dictRemplissage2[IDunite_remplissage][self.date][self.IDgroupe]
                if "reservation" in d : nbrePlacesPrises += d["reservation"]
                if "present" in d : nbrePlacesPrises += d["present"]
                if "attente" in d : nbreAttente += d["attente"]
            except :
                nbrePlacesPrises = 0
                nbreAttente = 0
            
            if nbrePlacesInitial == None : nbrePlacesInitial = 0
            if nbrePlacesPrises == None : nbrePlacesPrises = 0
            nbrePlacesRestantes = nbrePlacesInitial - nbrePlacesPrises
            
            # Récupère le nombre de places restantes pour l'ensemble des groupes
            nbrePlacesInitialTousGroupes = 0
            try :
                nbrePlacesInitialTousGroupes = self.grid.dictRemplissage[IDunite_remplissage][self.date][None]
            except :
                nbrePlacesInitialTousGroupes = 0
            
            if nbrePlacesInitialTousGroupes > 0 :
                nbrePlacesPrisesTousGroupes = 0
                try :
                    for IDgroupe, d in self.grid.dictRemplissage2[IDunite_remplissage][self.date].items() :
                        if "reservation" in d : nbrePlacesPrisesTousGroupes += d["reservation"]
                        if "present" in d : nbrePlacesPrisesTousGroupes += d["present"]
                except :
                    nbrePlacesPrisesTousGroupes = 0
                
                nbrePlacesRestantesTousGroupes = nbrePlacesInitialTousGroupes - nbrePlacesPrisesTousGroupes
                if nbrePlacesRestantesTousGroupes < nbrePlacesRestantes or nbrePlacesInitial == 0 :
                    nbrePlacesInitial = nbrePlacesInitialTousGroupes
                    nbrePlacesPrises = nbrePlacesPrisesTousGroupes
                    nbrePlacesRestantes = nbrePlacesRestantesTousGroupes
                    
            # Récupère le seuil_alerte
            seuil_alerte = self.grid.dictRemplissage[IDunite_remplissage]["seuil_alerte"]
            if seuil_alerte == None :
                seuil_alerte = 0
                        
            # Création d'un dictionnaire de réponses
            dictInfosPlaces[IDunite_remplissage] = {
                "nbrePlacesInitial" : nbrePlacesInitial, 
                "nbrePlacesPrises" : nbrePlacesPrises, 
                "nbrePlacesRestantes" : nbrePlacesRestantes, 
                "seuil_alerte" : seuil_alerte,
                "nbreAttente" : nbreAttente,
                }
        
        return dictInfosPlaces

    def GetRect(self):
        return self.grid.CellToRect(self.numLigne, self.numColonne)

    def Refresh(self):
        rect = self.GetRect()
        x, y = self.grid.CalcScrolledPosition(rect.GetX(), rect.GetY())
        rect = wx.Rect(x, y, rect.GetWidth(), rect.GetHeight())
        self.grid.GetGridWindow().Refresh(False, rect)

    def MAJremplissage(self):
        # Recalcule tout le remplissage de la grille
        self.grid.CalcRemplissage() 
        # Modifie la couleur des autres cases de la ligne ou de toute la grille en fonction du remplissage + MAJ Totaux Gestionnaire de conso
        if self.grid.mode == "date" :
            self.grid.MAJcouleurCases(saufLigne=None)
            self.grid.GetGrandParent().MAJ_totaux_contenu()
        else:
            #self.ligne.MAJcouleurCases(saufCase=self) # Cette ligne ne mettait pas à jour si fraterie affichée

            # Met à jour l'affichage de toutes les lignes de la même date (pour prendre en charge les frateries)
            for numLigne, ligne in self.grid.dictLignes.items() :
                if ligne.estSeparation == False and ligne.date == self.date :
                    ligne.MAJcouleurCases()


    def VerifieCompatibilitesUnites(self):
        listeIncompatibilites = self.grid.dictUnites[self.IDunite]["unites_incompatibles"]
        for numCol, case in self.ligne.dictCases.items():
            if case.typeCase == "consommation" :
                IDunite = case.IDunite
                for conso in case.GetListeConso() :
                    if conso.etat in ["reservation", "present"] and IDunite in listeIncompatibilites :
                        return IDunite
        return None

    #JB gestion des conso indépendante des factures
    def ProtectionsModifSuppr(self, conso=None, modeSilencieux=False):
        """ Protections anti modif et suppression de conso """
        # Si la conso est dans une facture, on annule la suppression
        if conso.IDfacture != None :
            dlg = wx.MessageDialog(self.grid, _("Cette consommation apparaît sur une facture déjà éditée.\nIl est donc impossible de la supprimer !\n\n(Suppression forçée)"), _("Consommation verrouillée"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return True
        
        # Si la conso est dans un forfait non supprimable
        if conso.forfait == 2 :
            dlg = wx.MessageDialog(self.grid, _("Cette consommation fait partie d'un forfait!\n\n(Suppression forçée)"), _("Consommation verrouillée"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return True

        # Si la conso est verrouillée, on annule l'action
        if conso.verrouillage == 1 and modeSilencieux == False :
            dlg = wx.MessageDialog(self.grid, _("Consommation vérouillée, Suppression forçée !"), _("Consommation verrouillée"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return True
        
        # Si la conso est "present", on annule l'action
        if conso.etat == "present" and modeSilencieux == False :
            dlg = wx.MessageDialog(self.grid, _("Vous ne pouvez pas modifier une consommation pointée 'présent' !"), _("Consommation verrouillée"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        
        # Si la conso est "absent", on annule l'action
        if (conso.etat == "absenti" or conso.etat == "absentj") and modeSilencieux == False :
            dlg = wx.MessageDialog(self.grid, _("Vous ne pouvez pas supprimer une consommation pointée 'absent' !"), _("Consommation verrouillée"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        # Regarde si la prestation apparaît déjà sur une facture
        if conso.IDprestation in self.grid.dictPrestations :
            IDfacture = self.grid.dictPrestations[conso.IDprestation]["IDfacture"]
            if IDfacture != None :
                dlg = wx.MessageDialog(self.grid, _("La prestation correspondant à cette consommation apparaît déjà sur une facture.\n\nSuppression forçée"), _("Consommation verrouillée"), wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                return True

        # Regarde si la prestation correspondante est déja payée
        if conso.IDprestation in self.grid.dictPrestations and modeSilencieux == False :
            montantPrestation = self.grid.dictPrestations[conso.IDprestation]["montant"]
            montantVentilation = self.grid.dictPrestations[conso.IDprestation]["montantVentilation"]
            if montantVentilation > 0.0 :
                message = _("La prestation correspondant à cette consommation a déjà été ventilée sur un règlement. \n\n(Suppression forçée)")
                dlg = wx.MessageDialog(self.grid, message, _("Suppression"), wx.OK|wx.ICON_EXCLAMATION)
                reponse = dlg.ShowModal() 
                dlg.Destroy()
                return True
        return True
    
    def OnTouchesRaccourcisPerso(self):
        for code, IDunite in self.grid.listeTouchesRaccourcis :
            if IDunite != self.IDunite :
                if wx.GetKeyState(Touches.DICT_TOUCHES[code][1]) == True :
                    # Création d'une conso supp
                    for numColonne, case in self.ligne.dictCases.items() :
                        if case.typeCase == "consommation" :
                            if case.IDunite == IDunite :
                                if case.CategorieCase == "multihoraires" :
                                    case.SaisieBarre(case.heure_min, case.heure_max, TouchesRaccourciActives=False)
                                else :
                                    case.OnClick(TouchesRaccourciActives=False)

    def SupprimeForfaitDate(self, IDprestationForfait=None):
        """ Suppression de toutes les conso d'un forfait """
        listeCases = []
        for IDindividu, dictDates in self.grid.dictConsoIndividus.items() :
            for date, dictUnites in dictDates.items() :
                for IDunite, listeConso in dictUnites.items() :
                    for conso in listeConso :
                        case = conso.case
                        if case != None : 
                            if conso.IDprestation == IDprestationForfait :
                                # Suppression conso multihoraires
                                if case.CategorieCase == "multihoraires" :
                                    conso.etat = None
                                    conso.forfait = None
                                    if conso.IDconso != None : 
                                        conso.statut = "suppression"
                                        self.grid.listeConsoSupprimees.append(conso)
                                    if conso.IDconso == None : 
                                        conso.statut = "suppression"
                                    case.MAJ_facturation()
                                    case.listeBarres.remove(conso.barre)
                                    self.grid.dictConsoIndividus[case.IDindividu][case.date][case.IDunite].remove(conso)
                                    self.Refresh() 
                                else :
                                    # Suppression conso standard
                                    if conso.etat != None :
                                        case.etat = None
                                        case.forfait = None
                                        if case.IDconso != None : case.statut = "suppression"
                                        if case.IDconso == None : case.statut = None
                                        case.MemoriseValeurs()
                                        case.Refresh()
                                        case.grid.listeHistorique.append((IDindividu, date, IDunite, _("Suppression d'une conso forfait")))
                                        if case not in listeCases :
                                            listeCases.append(case)
        
        for case in listeCases :
            case.MAJ_facturation()
                                            
        self.MAJremplissage()

                        




class CaseStandard(Case):
    def __init__(self, ligne, grid, numLigne=None, numColonne=None, IDindividu=None, IDfamille=None, date=None, IDunite=None, IDactivite=None, verrouillage=0):
        Case.__init__(self, ligne, grid, numLigne, numColonne, IDindividu, IDfamille, date, IDunite, IDactivite, verrouillage)
        self.CategorieCase = "standard"
        self.ligne = ligne

        self.statut = None # statuts possibles = None, ajout, modification, suppression
        self.IDconso = None
        self.heure_debut = None
        self.heure_fin = None
        self.etat = None
        self.verrouillage = verrouillage
        self.date_saisie = None
        self.IDutilisateur = None
        self.IDcategorie_tarif = None
        self.IDcompte_payeur = None
        self.IDprestation = None
        self.forfait = None
        self.IDfacture = None
        self.quantite = None
        self.etiquettes = []
        self.badgeage_debut = None
        self.badgeage_fin = None

        # Recherche s'il y a des conso pour cette case
        self.conso = self.GetConso() 

        # Importation des données de la conso
        if self.conso != None :
            self.IDconso = self.conso.IDconso
            self.heure_debut = self.conso.heure_debut
            self.heure_fin = self.conso.heure_fin
            self.etat = self.conso.etat
            self.date_saisie = self.conso.date_saisie
            self.IDutilisateur = self.conso.IDutilisateur
            self.IDcategorie_tarif = self.conso.IDcategorie_tarif
            self.IDcompte_payeur = self.conso.IDcompte_payeur
            self.IDprestation = self.conso.IDprestation
            self.forfait = self.conso.forfait
            #self.IDfamille = self.conso.IDfamille
            self.statut = self.conso.statut
            self.quantite = self.conso.quantite
            self.IDgroupe = self.conso.IDgroupe
            self.IDinscription = self.conso.IDinscription
            self.etiquettes = self.conso.etiquettes

            if self.IDprestation != None and self.IDprestation in self.grid.dictPrestations :
                self.IDfacture = self.grid.dictPrestations[self.IDprestation]["IDfacture"]
            
            self.grid.dictConsoIndividus[self.IDindividu][self.date][self.IDunite][0].case = self
        
        else :
            self.conso = CTRL_Grille.Conso()
                    
        # Dessin de la case
        self.renderer = CTRL_Grille_renderers.CaseStandard(self)
        self.grid.SetCellValue(self.numLigne, self.numColonne, "")
        self.grid.SetCellAlignment(self.numLigne, self.numColonne, wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)
        self.grid.SetCellRenderer(self.numLigne, self.numColonne, self.renderer)
        self.grid.SetReadOnly(self.numLigne, self.numColonne, True)
    
            
    def GetConso(self):
        """ Recherche s'il y a une conso pour cette case """
        try :
            conso = self.grid.dictConsoIndividus[self.IDindividu][self.date][self.IDunite][0]
        except : 
            conso = None
        return conso
    
    def GetListeConso(self):
        return [self.conso,]
                        
    def OnClick(self, TouchesRaccourciActives=True, saisieHeureDebut=None, saisieHeureFin=None, saisieQuantite=None, modeSilencieux=False, ForcerSuppr=False, etiquettes=None):
        """ Lors d'un clic sur la case """
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("consommations_conso", "modifier", IDactivite=self.IDactivite) == False : return

        # Récupération du mode de saisie
        mode = self.grid.GetGrandParent().panel_grille.GetMode()
        
        # Récupération des étiquettes
        if etiquettes != None :
            self.etiquettes = etiquettes
        else :
            self.etiquettes = self.grid.GetGrandParent().panel_etiquettes.GetCoches(self.IDactivite)
        
        # Si l'unité est fermée
        if self.ouvert == False : 
            return
        
        # Quantité actuelle
        if self.quantite != None :
            quantiteTemp = self.quantite
        else:
            quantiteTemp = 1
        
        # Touches de commandes rapides
        if wx.GetKeyState(97) == True : # Touche "a" pour Pointage en attente...
            if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("consommations_conso", "modifier", IDactivite=self.IDactivite) == False : return
            if self.etat in ("present", "absenti", "absentj") :
                self.ModifieEtat(etat="reservation")
            return
        if wx.GetKeyState(112) == True : # Touche "p" pour Présent
            if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("consommations_conso", "modifier", IDactivite=self.IDactivite) == False : return
            if self.etat in ("reservation", "absenti", "absentj") :
                self.ModifieEtat(etat="present")
            return
        if wx.GetKeyState(105) == True : # Touche "i" pour Absence injustifée
            if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("consommations_conso", "modifier", IDactivite=self.IDactivite) == False : return
            if self.etat in ("reservation", "present", "absentj") :
                self.ModifieEtat(etat="absenti")
            return
        if wx.GetKeyState(106) == True : # Touche "j" pour Absence justifiée
            if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("consommations_conso", "modifier", IDactivite=self.IDactivite) == False : return
            if self.etat in ("reservation", "present", "absenti") :
                self.ModifieEtat(etat="absentj")
            return

        # Protections anti modification et suppression
        conso = self.GetConso()
        # JB
        #if conso != None and self.ProtectionsModifSuppr(conso, modeSilencieux) == True :
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("consommations_conso", "modifier", IDactivite=self.IDactivite) == False : return
        if self.etat in ("present",) :
            self.ModifieEtat(etat="suppression")
        else :
            self.ModifieEtat(etat="present")

        # Sauvegarde des données dans le dictConsoIndividus
        self.MemoriseValeurs()

        # Change l'apparence de la case
        self.Refresh()

        # MAJ Données remplissage
        self.MAJremplissage()

        # Autogénération
        self.grid.Autogeneration(ligne=self.ligne, IDactivite=self.IDactivite, IDunite=self.IDunite)
        
        
    def MemoriseValeurs(self):
        if self.IDconso != None and self.statut != "suppression" : 
            self.statut = "modification"
        if self.IDconso == None and self.statut != "suppression" :
            self.statut = "ajout"
            self.date_saisie = datetime.date.today()
            self.IDcategorie_tarif = self.dictInfosInscriptions["IDcategorie_tarif"]
            self.IDcompte_payeur = self.dictInfosInscriptions["IDcompte_payeur"]
            self.IDinscription = self.dictInfosInscriptions["IDinscription"]
            DB = GestionDB.DB()
            self.IDutilisateur = DB.IDutilisateurActuel()
            self.forfait = 2
            if self.IDactivite > 0 and self.IDindividu > 0 :
                req = """ SELECT IDprestation
                    FROM prestations
                    WHERE ( IDactivite = '%d' ) AND ( IDindividu = '%d' ) ;""" %(self.IDactivite, self.IDindividu)
                retour = DB.ExecuterReq(req,MsgBox="ExecuterReq")
                if retour != "ok" :
                    GestionDB.MessageBox(None,retour)
                retour = DB.ResultatReq()
                if len(retour)>0:
                    self.IDprestation = retour[0][0]
                else:
                    wx.MessageBox("Vous souhaitez gérer des consommations, mais il n'y a pas de prestation ouverte\n\n"+
                                    "seule une réservation ou une commande permettent de gérer des consommations!")
                    self.grid.Parent.Parent.EndModal(wx.ID_CANCEL)
            DB.Close

        if (self.IDindividu in self.grid.dictConsoIndividus) == False :
            self.grid.dictConsoIndividus[self.IDindividu] = {}
        if (self.date in self.grid.dictConsoIndividus[self.IDindividu]) == False :
            self.grid.dictConsoIndividus[self.IDindividu][self.date] = {}
        if (self.IDunite in self.grid.dictConsoIndividus[self.IDindividu][self.date]) == False :
            self.grid.dictConsoIndividus[self.IDindividu][self.date][self.IDunite] = []
        listeConso = self.grid.dictConsoIndividus[self.IDindividu][self.date][self.IDunite]
        
        index = None
        i = 0
        for conso in listeConso :
            if conso == self.conso :
                self.conso = conso
                index = i
            i += 1
        if index == None :
            self.conso = CTRL_Grille.Conso() 
                
        self.conso.IDconso = self.IDconso
        self.conso.IDactivite = self.IDactivite
        self.conso.IDinscription = self.IDinscription
        self.conso.IDgroupe = self.IDgroupe
        self.conso.heure_debut = self.heure_debut
        self.conso.heure_fin = self.heure_fin
        self.conso.etat = self.etat
        self.conso.verrouillage = self.verrouillage
        self.conso.IDfamille = self.IDfamille
        self.conso.IDcompte_payeur = self.IDcompte_payeur
        self.conso.date_saisie = self.date_saisie
        self.conso.IDutilisateur = self.IDutilisateur
        self.conso.IDcategorie_tarif = self.IDcategorie_tarif
        self.conso.IDprestation = self.IDprestation
        self.conso.forfait = self.forfait
        self.conso.quantite = self.quantite
        self.conso.statut = self.statut
        self.conso.case = self
        self.conso.IDindividu = self.IDindividu
        self.conso.IDfamille = self.IDfamille
        self.conso.date = self.date
        self.conso.IDunite = self.IDunite
        self.conso.IDactivite = self.IDactivite
        self.conso.etiquettes = self.etiquettes

        if index != None :
            self.grid.dictConsoIndividus[self.IDindividu][self.date][self.IDunite][index] = self.conso
        else :
            self.grid.dictConsoIndividus[self.IDindividu][self.date][self.IDunite].append(self.conso)
        
                        
    def GetTexteInfobulle(self):
        try :
            texte = self.GetTexteInfobulleConso(self.conso)
        except Exception as err :
            print(err)
            texte = ""
        return texte
    
    def OnContextMenu(self):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("consommations_conso", "modifier", IDactivite=self.IDactivite) == False : return
        return self.ContextMenu(self.conso)
        
    def SetGroupe(self, event):
        IDgroupe = event.GetId() - 10000
        self.IDgroupe = IDgroupe
        self.MemoriseValeurs()
        self.Refresh()
        self.MAJremplissage() 
                    
    def SetEtat(self, event):
        ID = event.GetId()
        if ID == 30 or ID == 60 : 
            self.ModifieEtat(etat="reservation")
        if ID == 40 : 
            self.ModifieEtat(etat="attente")
        if ID == 50 : 
            self.ModifieEtat(etat="refus")
        if ID == 70 : 
            self.ModifieEtat(etat="present")
        if ID == 80 : 
            self.ModifieEtat(etat="absentj")
        if ID == 90 : 
            self.ModifieEtat(etat="absenti")

    def ModifieEtat(self, conso=None, etat="reservation"):
        ancienEtat = self.etat

        # Vérifie si prestation correspondante déjà facturée
        if self.IDprestation in self.grid.dictPrestations :
            IDfacture = self.grid.dictPrestations[self.IDprestation]["IDfacture"]
            if IDfacture != None :
                changementPossible = True
                if etat in ("reservation", "present", "absenti") and ancienEtat in ("attente", "refus", "absentj") : 
                    changementPossible = False
                if etat in (None, "attente", "refus", "absentj") and ancienEtat in ("reservation", "present", "absenti") : 
                    changementPossible = False
                if changementPossible == False :
                    dlg = wx.MessageDialog(self.grid, _("La prestation correspondant à cette consommation apparaît déjà sur une facture.\n\nIl est donc impossible de la modifier ou de la supprimer."), _("Consommation verrouillée"), wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    return False
        
        # Modifier état
        self.etat = etat
        self.MemoriseValeurs()

        if self.forfait == 0 or self.forfait == None :
            self.MAJ_facturation(action="modification_etat")
        
        self.Refresh()
        self.MAJremplissage() 
        self.grid.listeHistorique.append((self.IDindividu, self.date, self.IDunite, _("Modification de l'état d'une consommation")))
        self.grid.Autogeneration(ligne=self.ligne, IDactivite=self.IDactivite, IDunite=self.IDunite)

    def Verrouillage(self, event):
        self.verrouillage = 1
        if self.statut == None : self.statut = "modification"
        self.MemoriseValeurs()
        self.Refresh()

    def Deverrouillage(self, event):
        self.verrouillage = 0
        if self.statut == None : self.statut = "modification"
        self.MemoriseValeurs()
        self.Refresh()
    
    def DLG_detail(self, event):
        from Dlg import DLG_Detail_conso
        dictConso = self.GetConso() 
        texteInfoBulle = self.GetTexteInfobulle()
        typeUnite = self.grid.dictUnites[dictConso.case.IDunite]["type"]
        dlg = DLG_Detail_conso.Dialog(self.grid, dictConso, texteInfoBulle)
        if typeUnite == "Horaire" :
            dlg.ctrl_heure_debut.Enable(False)
            dlg.ctrl_heure_fin.Enable(False)
        if dlg.ShowModal() == wx.ID_OK:
            self.IDgroupe = dlg.GetIDgroupe()
            self.heure_debut = dlg.GetHeureDebut()
            self.heure_fin = dlg.GetHeureFin()
            self.MemoriseValeurs()
            if self.IDconso != None : 
                self.statut = "modification"
            self.Refresh()
            self.MAJremplissage()
            self.grid.Autogeneration(ligne=self.ligne, IDactivite=self.IDactivite, IDunite=self.IDunite)

        dlg.Destroy()
    
    def Ajouter(self, event=None):
        self.OnClick()
        
    def Modifier(self, event=None):
        """ Modifier la consommation sélectionnée """
        self.OnClick()
    
    def Supprimer(self, event=None):
        """ Supprimer la consommation sélectionnée """
        for conso in self.GetListeConso() :
            if conso.etat != None :
                self.OnClick()

    def IsCaseDisponible(self, heure_debut=None, heure_fin=None):
        """ Regarde si conso existe déjà sur ce créneau """
        for conso in self.GetListeConso() :
            if conso.etat == None :
                return True
            else :
                return False

    def HasPlaceDisponible(self, heure_debut=None, heure_fin=None):
        """ Regarde si place disponible selon le remplissage """
        dictInfosPlaces = self.GetInfosPlaces()
        if dictInfosPlaces != None :
            nbrePlacesRestantes = None
            for IDunite_remplissage in self.grid.dictUnitesRemplissage[self.IDunite] :
                if (nbrePlacesRestantes == None or dictInfosPlaces[IDunite_remplissage]["nbrePlacesRestantes"] < nbrePlacesRestantes) and dictInfosPlaces[IDunite_remplissage]["nbrePlacesInitial"] not in (0, None) :
                    nbrePlacesRestantes = dictInfosPlaces[IDunite_remplissage]["nbrePlacesRestantes"]
            if nbrePlacesRestantes != None and nbrePlacesRestantes <= 0 :
                return False
        return True

    def GetStatutTexte(self, x, y):
        if self.IsCaseDisponible() == False :
            texte = _("Cliquez sur cette case pour modifier ou supprimer la consommation")
        else :
            texte = _("Cliquez sur cette case pour ajouter une consommation")
        return texte

    def SelectionnerEtiquettes(self, event):
        listeCoches = self.conso.etiquettes
        from Ctrl import CTRL_Etiquettes
        dlg = CTRL_Etiquettes.DialogSelection(self.grid, listeActivites=[self.IDactivite,])
        dlg.SetCoches(listeCoches)
        if dlg.ShowModal() == wx.ID_OK :
            listeCoches = dlg.GetCoches() 
            self.etiquettes = listeCoches
            self.MemoriseValeurs()
            self.MAJ_facturation(action="modification")
            self.Refresh()
            self.MAJremplissage() 
        dlg.Destroy()
        

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class Barre():
    def __init__(self, case=None, calque=0, conso=None):
        self.case = case
        self.calque = calque
        self.conso = conso
        self.conso.case = self.case
        self.conso.barre = self
        
        # Attributs
        self.readOnly = False
        self.rectBarre = None
    
    def SetHeures(self, heure_debut=None, heure_fin=None) :
        if heure_debut != None :
            self.conso.heure_debut = UTILS_Dates.DatetimeTimeEnStr(heure_debut, separateur=":")
        if heure_fin != None :
            self.conso.heure_fin = UTILS_Dates.DatetimeTimeEnStr(heure_fin, separateur=":")
        self.MemoriseValeurs() 
        self.case.grid.memoireHoraires[self.case.IDunite] = {"heure_debut":self.conso.heure_debut, "heure_fin":self.conso.heure_fin}


    def UpdateRect(self):
        rectCase = self.case.GetRect()
        # vérifie que les heures sont ok
        self.heure_debut = UTILS_Dates.HeureStrEnTime(self.conso.heure_debut)
        self.heure_fin = UTILS_Dates.HeureStrEnTime(self.conso.heure_fin)
        # Recherche des positions
        posG = self.case.HeureEnPos(self.heure_debut)
        posD = self.case.HeureEnPos(self.heure_fin)
        # Création du wx.rect
        x = CTRL_Grille_renderers.PADDING_MULTIHORAIRES["horizontal"] + posG
        largeur = posD - posG
        y = CTRL_Grille_renderers.PADDING_MULTIHORAIRES["vertical"]
        hauteur = rectCase.GetHeight() -  CTRL_Grille_renderers.PADDING_MULTIHORAIRES["vertical"] * 2
        self.rectBarre = wx.Rect(x, y, largeur, hauteur)

    def GetRect(self, mode="case"):
        """ Modes : 
        case = les coordonnées dans la case
        grid = les coordonnées dans la grid
        """
        if self.rectBarre == None :
            return None
        if mode == "case" :
            return self.rectBarre
        if mode == "grid" :
            return wx.Rect(self.rectBarre.x + self.case.GetRect().x, self.rectBarre.y + self.case.GetRect().y, self.rectBarre.GetWidth(), self.rectBarre.GetHeight())
    
    def Refresh(self):
        self.case.Refresh()
        
    def MemoriseValeurs(self):
        self.conso.case = self.case
        self.conso.barre = self

        ajout = False
        if (self.case.IDindividu in self.case.grid.dictConsoIndividus) == False :
            self.case.grid.dictConsoIndividus[self.case.IDindividu] = {}
        if (self.case.date in self.case.grid.dictConsoIndividus[self.case.IDindividu]) == False :
            self.case.grid.dictConsoIndividus[self.case.IDindividu][self.case.date] = {}
        if (self.case.IDunite in self.case.grid.dictConsoIndividus[self.case.IDindividu][self.case.date]) == False :
            self.case.grid.dictConsoIndividus[self.case.IDindividu][self.case.date][self.case.IDunite] = []
        
        listeConso = self.case.grid.dictConsoIndividus[self.case.IDindividu][self.case.date][self.case.IDunite]
        position = None
        index = 0
        for conso in listeConso :
            if self.conso == conso :
                position = index
            index += 1
        
        if position == None :
            self.case.grid.dictConsoIndividus[self.case.IDindividu][self.case.date][self.case.IDunite].append(self.conso)
        else :
            if self.conso.statut not in ("ajout", "suppression") : 
                self.conso.statut = "modification"
            self.case.grid.dictConsoIndividus[self.case.IDindividu][self.case.date][self.case.IDunite][position] = self.conso
        
    def MAJ_facturation(self,**kw):
        self.case.MAJ_facturation()
        
        

class CaseMultihoraires(Case):
    def __init__(self, ligne, grid, numLigne=None, numColonne=None, IDindividu=None, IDfamille=None, date=None, IDunite=None, IDactivite=None, verrouillage=0, heure_min=None, heure_max=None):
        Case.__init__(self, ligne, grid, numLigne, numColonne, IDindividu, IDfamille, date, IDunite, IDactivite, verrouillage)
        self.CategorieCase = "multihoraires"

        # Plage horaire
        self.heure_min = heure_min
        self.heure_max = heure_max
        
        # Dessin de la case
        self.renderer = CTRL_Grille_renderers.CaseMultihoraires(self)
        self.grid.SetCellValue(self.numLigne, self.numColonne, "")
        self.grid.SetCellAlignment(self.numLigne, self.numColonne, wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)
        self.grid.SetCellRenderer(self.numLigne, self.numColonne, self.renderer)
        self.grid.SetReadOnly(self.numLigne, self.numColonne, True)
        
        # Création des barres
        self.listeBarres = self.GetListeBarres()
        
    def GetListeConso(self):
        listeConso = []
        for barre in self.listeBarres :
            listeConso.append(barre.conso) 
        return listeConso

    def HeureEnPos(self, heure):
        tempsAffichable = UTILS_Dates.SoustractionHeures(self.heure_max, self.heure_min)
        return 1.0 * UTILS_Dates.SoustractionHeures(heure, self.heure_min).seconds / tempsAffichable.seconds * self.GetLargeurMax() 

    def PosEnHeure(self, x, arrondir=False):
        tempsAffichable = UTILS_Dates.SoustractionHeures(self.heure_max, self.heure_min)
        pos = x - self.GetRect().GetX() - CTRL_Grille_renderers.PADDING_MULTIHORAIRES["horizontal"]
        temp = datetime.timedelta(seconds=1.0 * pos / self.GetLargeurMax() * tempsAffichable.seconds)
        if arrondir == True :
            temp = UTILS_Dates.DeltaEnTime(temp)
            minutes = temp.strftime("%M")
            if int(minutes[1]) < 5 : minutes = "%s%d" % (minutes[0], 0)
            if int(minutes[1]) > 5 : minutes = "%s%d" % (minutes[0], 5)
            temp = datetime.time(int(temp.strftime("%H")), int(minutes))
        heure = UTILS_Dates.AdditionHeures(self.heure_min, temp)
        return UTILS_Dates.DeltaEnTime(heure)

    def GetLargeurMax(self):
        return self.GetRect().GetWidth() - CTRL_Grille_renderers.PADDING_MULTIHORAIRES["horizontal"] * 2
        
    def ContraintesCalque(self, barreCible, heure_debut, heure_fin):
        """ Vérifie si un calque ne se superpose sur un autre du même calque """
        numCalque = barreCible.calque 
        for barre in self.listeBarres :
            if barre.calque == numCalque and barre != barreCible :
                if heure_debut < barre.heure_fin and heure_fin > barre.heure_debut :
                    return True
        return False
    
    def GetListeBarres(self):
        listeBarres = []
        if self.IDindividu in self.grid.dictConsoIndividus :
            if self.date in self.grid.dictConsoIndividus[self.IDindividu] :
                if self.IDunite in self.grid.dictConsoIndividus[self.IDindividu][self.date] :
                    for conso in self.grid.dictConsoIndividus[self.IDindividu][self.date][self.IDunite] :
                        barre = Barre(case=self, calque=1, conso=conso)
                        listeBarres.append(barre)
        return listeBarres

    def GetTexteInfobulle(self):
        barre = self.RechercheBarreMousePosition() 
        if barre != None :
            conso = barre.conso
        else :
            conso = None
        return self.GetTexteInfobulleConso(conso)

    def OnContextMenu(self):
        barre = self.RechercheBarreMousePosition() 
        if barre != None :
            self.barreContextMenu = barre
            return self.ContextMenu(barre.conso)
        else :
            return self.ContextMenu()
    
    def RechercheBarreMousePosition(self):
        x, y = self.grid.CalcUnscrolledPosition(self.grid.ScreenToClient(wx.GetMousePosition()))
        x = x - self.grid.GetRowLabelSize()
        y = y - self.grid.GetColLabelSize()
        barre = self.RechercheBarre(x, y)
        if barre == None :
            return None
        else :
            barre, region, x, y, ecart = barre
            return barre
        
    def RechercheBarre(self, x, y, readOnlyInclus=True):
        for barre in self.listeBarres :
            if readOnlyInclus == True or (readOnlyInclus == False and barre.readOnly == False) :
                rectBarre = barre.GetRect("grid")
                if rectBarre != None and rectBarre.ContainsXY(x, y) :
                    # Région
                    if x < rectBarre.width / 4.0 + rectBarre.x :
                        region = "gauche"
                        ecart = x - rectBarre.x
                    elif x > rectBarre.width / 4.0 * 3 + rectBarre.x :
                        region = "droite"
                        ecart = rectBarre.width + rectBarre.x - x
                    else :
                        region = "milieu"
                        ecart = x - rectBarre.x
                    return barre, region, x, y, ecart
        return None

    def SetGroupe(self, event):
        barre = self.barreContextMenu
        barre.conso.IDgroupe = event.GetId() - 10000
        barre.MemoriseValeurs()
        if barre.conso.IDconso != None : 
            barre.conso.statut = "modification"
        barre.Refresh()
        self.MAJremplissage() 
    
    def SetEtat(self, event):
        barre = self.barreContextMenu
        ID = event.GetId()
        if ID == 30 or ID == 60 : 
            self.ModifieEtat(barre.conso, "reservation")
        if ID == 40 : 
            self.ModifieEtat(barre.conso, "attente")
        if ID == 50 : 
            self.ModifieEtat(barre.conso, "refus")
        if ID == 70 : 
            self.ModifieEtat(barre.conso, "present")
        if ID == 80 : 
            self.ModifieEtat(barre.conso, "absentj")
        if ID == 90 : 
            self.ModifieEtat(barre.conso, "absenti")

    def ModifieEtat(self, conso=None, etat="reservation"):
        ancienEtat = conso.etat

        # Vérifie si prestation correspondante déjà facturée
        if conso.IDprestation in self.grid.dictPrestations :
            IDfacture = self.grid.dictPrestations[conso.IDprestation]["IDfacture"]
            if IDfacture != None :
                changementPossible = True
                if etat in ("reservation", "present", "absenti") and ancienEtat in ("attente", "refus", "absentj") : 
                    changementPossible = False
                if etat in (None, "attente", "refus", "absentj") and ancienEtat in ("reservation", "present", "absenti") : 
                    changementPossible = False
                if changementPossible == False :
                    dlg = wx.MessageDialog(self.grid, _("La prestation correspondant à cette consommation apparaît déjà sur une facture.\n\nIl est donc impossible de la modifier ou de la supprimer."), _("Consommation verrouillée"), wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    return False

        barre = conso.barre
        barre.conso.etat = etat
        barre.MemoriseValeurs() 
        
        if barre.conso.forfait == 0 or barre.conso.forfait == None :
            if etat in ("reservation", "present", "absenti") and ancienEtat in ("attente", "refus", "absentj") : 
                self.MAJ_facturation()
            if etat in ("attente", "refus", "absentj") and ancienEtat in ("reservation", "present", "absenti") : 
                self.MAJ_facturation()
            
        barre.Refresh()
        self.MAJremplissage() 
        self.grid.listeHistorique.append((self.IDindividu, self.date, self.IDunite, _("Modification de l'état d'une consommation multihoraires")))
        
    def Verrouillage(self, event):
        pass
##        self.verrouillage = 1
##        if self.statut == None : self.statut = "modification"
##        self.MemoriseValeurs()
##        self.renderer.MAJ()

    def Deverrouillage(self, event):
        pass
##        self.verrouillage = 0
##        if self.statut == None : self.statut = "modification"
##        self.MemoriseValeurs()
##        self.renderer.MAJ()
    
    def DLG_detail(self, event):
        barre = self.barreContextMenu
        from Dlg import DLG_Detail_conso
        texteInfoBulle = self.GetTexteInfobulleConso(barre.conso)
        dlg = DLG_Detail_conso.Dialog(self.grid, barre.conso, texteInfoBulle)
        if dlg.ShowModal() == wx.ID_OK:
            barre.conso.IDgroupe = dlg.GetIDgroupe()
            barre.conso.heure_debut = dlg.GetHeureDebut()
            barre.conso.heure_fin = dlg.GetHeureFin()
            barre.MemoriseValeurs()
            if barre.conso.IDconso != None : 
                barre.conso.statut = "modification"
            barre.Refresh()
            self.MAJremplissage()
            self.grid.Autogeneration(ligne=self.ligne, IDactivite=self.IDactivite, IDunite=self.IDunite)
        dlg.Destroy()
    
    def SaisieBarre(self, heure_debut=None, heure_fin=None, modeSilencieux=False, TouchesRaccourciActives=True, etiquettes=None):
        """ Création d'une barre + conso """        
        # Vérifie d'abord qu'il n'y a aucune incompatibilités entre unités
        incompatibilite = self.VerifieCompatibilitesUnites()
        if incompatibilite != None :
            nomUniteCase = self.grid.dictUnites[self.IDunite]["nom"]
            nomUniteIncompatible = self.grid.dictUnites[incompatibilite]["nom"]
            dlg = wx.MessageDialog(self.grid, _("L'unité %s est incompatible avec l'unité %s déjà sélectionnée !") % (nomUniteCase, nomUniteIncompatible), _("Incompatibilités d'unités"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        # Vérifie que la case n'est pas déjà occupée
        if self.IsCaseDisponible(heure_debut, heure_fin) == False :
            if modeSilencieux == True : 
                return False
            dlg = wx.MessageDialog(None, _("Une consommation existe déjà sur ce créneau horaire !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        
        # Vérifie qu'il y a de la place
        if self.grid.blocageSiComplet == True and self.HasPlaceDisponible(heure_debut, heure_fin) == False :
            if modeSilencieux == True : 
                return False
            dlg = wx.MessageDialog(None, _("Il n'y a plus de places disponibles sur cette tranche horaire.\n\nSouhaitez-vous quand même saisir une consommation ?"), _("Complet !"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_EXCLAMATION)
            reponse = dlg.ShowModal() 
            dlg.Destroy()
            if reponse != wx.ID_YES : 
                return 

        # Touches de raccourci
        if TouchesRaccourciActives == True :
            self.OnTouchesRaccourcisPerso() 
        
        # Création d'une conso
        conso = CTRL_Grille.Conso() 
        conso.IDconso = None
        conso.IDactivite = self.IDactivite
        conso.IDinscription = self.dictInfosInscriptions["IDinscription"]
        conso.IDgroupe = self.IDgroupe
        conso.heure_debut = UTILS_Dates.DatetimeTimeEnStr(heure_debut, ":") # self.grid.dictUnites[self.IDunite]["heure_debut"]
        conso.heure_fin = UTILS_Dates.DatetimeTimeEnStr(heure_fin, ":") # self.grid.dictUnites[self.IDunite]["heure_fin"]

        # Mode de saisie
        conso.etat = self.grid.GetGrandParent().panel_grille.GetMode()

        # Récupération des étiquettes
        if etiquettes != None :
            conso.etiquettes = etiquettes
        else :
            conso.etiquettes = self.grid.GetGrandParent().panel_etiquettes.GetCoches(self.IDactivite)
        
        # Autres paramètres
        conso.verrouillage = 0
        conso.IDfamille = self.IDfamille
        conso.IDcompte_payeur = self.dictInfosInscriptions["IDcompte_payeur"]
        conso.date_saisie = datetime.date.today()
        conso.IDutilisateur = self.grid.IDutilisateur
        conso.IDcategorie_tarif = self.dictInfosInscriptions["IDcategorie_tarif"] 
        conso.IDprestation = None
        conso.forfait = None
        conso.quantite = None
        conso.statut = "ajout"
        conso.IDunite = self.IDunite

        if self.IDactivite in self.grid.dictInfosInscriptions[self.IDindividu] :
            if self.grid.mode == "individu" :
                conso.IDgroupe = self.grid.GetGrandParent().panel_activites.ctrl_activites.GetIDgroupe(self.IDactivite, self.IDindividu)
            if self.IDgroupe == None :
                conso.IDgroupe = self.grid.dictInfosInscriptions[self.IDindividu][self.IDactivite]["IDgroupe"]
        else:
            conso.IDgroupe = None
        
        self.grid.memoireHoraires[self.IDunite] = {"heure_debut":conso.heure_debut, "heure_fin":conso.heure_fin}
        
        barre = Barre(case=self, calque=1, conso=conso)
        barre.MemoriseValeurs() 
        self.listeBarres.append(barre)
        self.MAJremplissage()
        
        # Facturation
        self.MAJ_facturation()
        
        barre.Refresh()
        
        self.grid.listeHistorique.append((self.IDindividu, self.date, self.IDunite, _("Ajout d'une consommation multihoraires")))        
        
        # Si les heures saisies dépassent les heures min et max, on élargit la colonne Multihoraires
        if (heure_debut < self.heure_min) or (heure_fin > self.heure_max) : 
            self.grid.MAJ_affichage()

        # Autogénération
        self.grid.Autogeneration(ligne=self.ligne, IDactivite=self.IDactivite, IDunite=self.IDunite)

        return barre
        
    def AjouterBarre(self, position=None):
        """ Ajouter une barre """
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("consommations_conso", "creer", IDactivite=self.IDactivite) == False : return

        # Recherche des horaires à appliquer
        heure_cliquee = self.PosEnHeure(position[0], arrondir=True)
        
        # Recherche d'un emplacement disponible dans la case
        heure_debut = self.heure_min
        heure_fin = self.heure_max
        self.listeBarres.sort(key=operator.attrgetter("heure_debut"))
        for barre in self.listeBarres :
            if heure_cliquee > barre.heure_debut and heure_cliquee > barre.heure_fin :
                heure_debut = barre.heure_fin
            if heure_cliquee < barre.heure_debut and heure_cliquee < barre.heure_fin :
                heure_fin = barre.heure_debut

        # Copie de la conso précédemment saisie
        if wx.GetKeyState(99) == True : 
            if self.IDunite in self.grid.memoireHoraires :
                heure_debut = UTILS_Dates.HeureStrEnTime(self.grid.memoireHoraires[self.IDunite]["heure_debut"])
                heure_fin = UTILS_Dates.HeureStrEnTime(self.grid.memoireHoraires[self.IDunite]["heure_fin"])

        self.SaisieBarre(heure_debut, heure_fin)

    def Ajouter(self, event=None):
        """ Ajouter une barre avec dialog de saisie des heures """
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("consommations_conso", "creer", IDactivite=self.IDactivite) == False : return
        heure_debut = self.grid.dictUnites[self.IDunite]["heure_debut"]
        heure_fin = self.grid.dictUnites[self.IDunite]["heure_fin"]
        
        heure_debut_fixe = self.grid.dictUnites[self.IDunite]["heure_debut_fixe"]
        heure_fin_fixe = self.grid.dictUnites[self.IDunite]["heure_fin_fixe"]

        from Dlg import DLG_Saisie_conso_horaire
        dlg = DLG_Saisie_conso_horaire.Dialog(None, nouveau=True, heure_min=heure_debut, heure_max=heure_fin)
        dlg.SetHeureDebut(heure_debut, heure_debut_fixe)
        dlg.SetHeureFin(heure_fin, heure_fin_fixe)
        reponse = dlg.ShowModal()
        heure_debut = UTILS_Dates.HeureStrEnTime(dlg.GetHeureDebut())
        heure_fin = UTILS_Dates.HeureStrEnTime(dlg.GetHeureFin())
        dlg.Destroy()

        if reponse == wx.ID_OK:
            self.SaisieBarre(heure_debut, heure_fin)

    def Modifier(self, event=None):
        """ Modifier la consommation sélectionnée """
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("consommations_conso", "modifier", IDactivite=self.IDactivite) == False : return
        self.ModifierBarre(self.barreContextMenu)
    
    def Supprimer(self, event=None):
        """ Supprimer la consommation sélectionnée """
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("consommations_conso", "supprimer", IDactivite=self.IDactivite) == False : return
        self.SupprimerBarre(self.barreContextMenu)

    def ModifierBarre(self, barre=None, horaires=None, etiquettes=None):
        """ Horaires = None ou (heure_debut, heure_fin) """
        # Protections anti modification et suppression
        if self.ProtectionsModifSuppr(barre.conso) == False :
            return

        if horaires == None :
            heure_debut = UTILS_Dates.DatetimeTimeEnStr(barre.heure_debut, ":")
            heure_fin = UTILS_Dates.DatetimeTimeEnStr(barre.heure_fin, ":")
            heure_debut_fixe = self.grid.dictUnites[self.IDunite]["heure_debut_fixe"]
            heure_fin_fixe = self.grid.dictUnites[self.IDunite]["heure_fin_fixe"]

            from Dlg import DLG_Saisie_conso_horaire
            dlg = DLG_Saisie_conso_horaire.Dialog(None, nouveau=False)
            dlg.SetHeureDebut(heure_debut, heure_debut_fixe)
            dlg.SetHeureFin(heure_fin, heure_fin_fixe)
            reponse = dlg.ShowModal()
            heure_debut = dlg.GetHeureDebut()
            heure_fin = dlg.GetHeureFin()
            dlg.Destroy()
        else :
            heure_debut, heure_fin = horaires
            reponse = wx.ID_OK
            
        if reponse == wx.ID_OK:
            barre.conso.heure_debut = heure_debut
            barre.conso.heure_fin = heure_fin
            if etiquettes != None :
                barre.conso.etiquettes = etiquettes
            barre.MemoriseValeurs()
            if barre.conso.IDconso != None : 
                barre.conso.statut = "modification"
            self.MAJremplissage()
            self.MAJ_facturation()
            barre.Refresh()
            self.grid.listeHistorique.append((self.IDindividu, self.date, self.IDunite, _("Modification d'une consommation multihoraires")))

            # Si les heures saisies dépassent les heures min et max, on élargit la colonne Multihoraires
            if (heure_debut < str(self.heure_min)) or (heure_fin > str(self.heure_max)) : 
                self.grid.MAJ_affichage()

            # Autogénération
            self.grid.Autogeneration(ligne=self.ligne, IDactivite=self.IDactivite, IDunite=self.IDunite)

        elif reponse == 3 :
            # Suppression
            self.SupprimerBarre(barre)


            
    def SupprimerBarre(self, barre=None):
        # Protections anti modification et suppression
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("consommations_conso", "supprimer", IDactivite=self.IDactivite) == False : return

        if self.ProtectionsModifSuppr(barre.conso) == False :
            return

        # -Suppression d'un forfait supprimable
        if barre.conso.etat != None and barre.conso.forfait == 1 :
            # Demande la confirmation de la suppression du forfait
            dlg = wx.MessageDialog(self.grid, _("Cette consommation fait partie d'un forfait supprimable.\n\nSouhaitez-vous supprimer le forfait et toutes les consommations rattachées ?"), _("Suppression"), wx.YES_NO|wx.YES_DEFAULT|wx.CANCEL|wx.ICON_EXCLAMATION)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse == wx.ID_YES :
                self.SupprimeForfaitDate(barre.conso.IDprestation)
            return

        if barre.conso.etat != None and barre.conso.forfait == 2 :
            print("forfait 2")
            return

        # Suppression
        barre.conso.etat = None
        if barre.conso.IDconso != None : 
            barre.conso.statut = "suppression"
            self.grid.listeConsoSupprimees.append(barre.conso)
        if barre.conso.IDconso == None : 
            barre.conso.statut = "suppression"
        self.MAJ_facturation()
        self.listeBarres.remove(barre)
        self.grid.dictConsoIndividus[self.IDindividu][self.date][self.IDunite].remove(barre.conso)
        self.MAJremplissage()
        self.Refresh() 
        self.grid.listeHistorique.append((self.IDindividu, self.date, self.IDunite, _("Suppression d'une consommation multihoraires")))   

        # Autogénération
        self.grid.Autogeneration(ligne=self.ligne, IDactivite=self.IDactivite, IDunite=self.IDunite)

    def ToucheRaccourci(self, barre):
        """ Applique une touche raccourci à une barre """
        if wx.GetKeyState(97) == True : # Touche "a" pour Pointage en attente...
            if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("consommations_conso", "modifier", IDactivite=self.IDactivite) == False : return
            if barre.conso.etat in ("present", "absenti", "absentj") :
                self.ModifieEtat(barre.conso, "reservation")
                
        if wx.GetKeyState(112) == True : # Touche "p" pour Présent
            if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("consommations_conso", "modifier", IDactivite=self.IDactivite) == False : return
            if barre.conso.etat in ("reservation", "absenti", "absentj") :
                self.ModifieEtat(barre.conso, "present")
                
        if wx.GetKeyState(105) == True : # Touche "i" pour Absence injustifée
            if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("consommations_conso", "modifier", IDactivite=self.IDactivite) == False : return
            if barre.conso.etat in ("reservation", "present", "absentj") :
                self.ModifieEtat(barre.conso, "absenti")
                
        if wx.GetKeyState(106) == True : # Touche "j" pour Absence justifiée
            if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("consommations_conso", "modifier", IDactivite=self.IDactivite) == False : return
            if barre.conso.etat in ("reservation", "present", "absenti") :
                self.ModifieEtat(barre.conso, "absentj")

        if wx.GetKeyState(115) == True : # Suppression de la conso
            if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("consommations_conso", "supprimer", IDactivite=self.IDactivite) == False : return
            self.SupprimerBarre(barre)
            

    def IsCaseDisponible(self, heure_debut=None, heure_fin=None):
        """ Regarde si conso existe déjà sur ce créneau """
        self.listeBarres.sort(key=operator.attrgetter("conso.heure_debut"))
        if type(heure_debut) == datetime.time : heure_debut = UTILS_Dates.DatetimeTimeEnStr(heure_debut, ":")
        if type(heure_fin) == datetime.time : heure_fin = UTILS_Dates.DatetimeTimeEnStr(heure_fin, ":")
        for conso in self.GetListeConso() :
            if str(conso.heure_debut) < str(heure_fin) and str(conso.heure_fin) > str(heure_debut) :
                return False
        return True

    def HasPlaceDisponible(self, heure_debut=None, heure_fin=None):
        """ Regarde si place disponible selon le remplissage """
        dictInfosPlaces = self.GetInfosPlaces()
        if dictInfosPlaces != None :
            for IDunite_remplissage, valeurs in dictInfosPlaces.items() :
                heure_min_remplissage = self.grid.dictRemplissage[IDunite_remplissage]["heure_min"]
                heure_max_remplissage = self.grid.dictRemplissage[IDunite_remplissage]["heure_max"]
                nbrePlacesRestantes = valeurs["nbrePlacesRestantes"]
                if heure_min_remplissage < str(heure_fin) and heure_max_remplissage > str(heure_debut) and nbrePlacesRestantes <= 0 :
                    return False
        return True
        
    def GetStatutTexte(self, x=None, y=None):
        if self.grid.barreMoving != None :
            barre = self.grid.barreMoving["barre"]
        else :
            barre = self.RechercheBarre(x, y, readOnlyInclus=False)
            if barre != None :
                barre, region, xTemp, yTemp, ecart = barre
        if barre != None :
            heure_debut = UTILS_Dates.DatetimeTimeEnStr(barre.heure_debut)
            heure_fin = UTILS_Dates.DatetimeTimeEnStr(barre.heure_fin)
            texte = _("Consommation horaire : %s > %s") % (heure_debut, heure_fin)
        else :
            texte = _("Double-cliquez pour ajouter une nouvelle consommation horaire")
        return texte

    def SelectionnerEtiquettes(self, event):
        barre = self.barreContextMenu
        listeCoches = barre.conso.etiquettes
        from Ctrl import CTRL_Etiquettes
        dlg = CTRL_Etiquettes.DialogSelection(self.grid, listeActivites=[self.IDactivite,])
        dlg.SetCoches(listeCoches)
        if dlg.ShowModal() == wx.ID_OK :
            listeCoches = dlg.GetCoches() 
            barre.conso.etiquettes = listeCoches
            barre.MemoriseValeurs()
            if barre.conso.IDconso != None : 
                barre.conso.statut = "modification"
            self.MAJ_facturation()
            barre.Refresh()
            self.MAJremplissage() 
        dlg.Destroy()


if __name__ == '__main__':
    app = wx.App(0)
    from Dlg import DLG_Grille
    frame_1 = DLG_Grille.Dialog(None, IDfamille=2632, selectionIndividus=[12675,])
    app.SetTopWindow(frame_1)
    frame_1.ShowModal()
    app.MainLoop()

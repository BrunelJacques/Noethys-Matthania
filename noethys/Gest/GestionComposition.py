#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#----------------------------------------------------------
# Application :    Matthania-Noethys
# Auteur:          Jacques BRUNEL
# Licence:         Licence GNU GPL
# Regroupe toutes la gestion des compositions familles
# et rattachement  des individus
#-----------------------------------------------------------

import wx
import GestionDB
import FonctionsPerso as fp

from Utils import UTILS_Historique
from Utils import UTILS_SaisieAdresse
from Utils import UTILS_Utilisateurs
from Dlg import DLG_Individu

def MAJ(self):
    if hasattr(self, 'MAJ'):
        self.MAJ()
    if hasattr(self, 'MAJnotebook'):
        self.MAJnotebook()

class GestCompo():
    def __init__(self, parent, IDfamille=None):
        self.parent = parent
        self.IDfamille = IDfamille
        self.IDindividu = None
        self.dIndividus = {}
        self.dictRattach = {}

    def Changer_categorie(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_fiche",
                                                                  "modifier") == False: return
        IDcategorie = event.GetId() - 600
        IDrattachement = self.dictCadres[self.IDindividu_menu]["IDrattachement"]
        if self.dictCadres[self.IDindividu_menu]["categorie"] == 1:
            # risque d'incohérences avec titulaires et correspondants
            if self.dictCadres[self.IDindividu_menu]["titulaire"] == 1 or \
                    self.dictCadres[self.IDindividu_menu]["correspondant"]:
                mess = "Avant de changer la catégorie d'un titulaire ou d'un correspondant il faut désactiver ces fonctions"
                wx.MessageBox(mess, "Blocage")
                return
        if IDcategorie != self.dictCadres[self.IDindividu_menu]["categorie"]:
            dlg = wx.MessageDialog(None,
                                   "Souhaitez-vous vraiment modifier la catégorie de rattachement de cet individu ?",
                                   "Changement de catégorie",
                                   wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_QUESTION)
            if dlg.ShowModal() == wx.ID_YES:
                DB = GestionDB.DB()
                DB.ReqMAJ("rattachements", [("IDcategorie", IDcategorie), ],
                          "IDrattachement", IDrattachement)
                DB.Close()
                MAJ(self)
            dlg.Destroy()

    def On_SetTitulaire(self, event):
        if self.dictCadres[self.IDindividu_menu]["titulaire"] == 1:
            # Recherche s'il restera au moins un titulaire dans cette famille
            nbreTitulaires = 0
            for IDindividu, dictCadre in self.dictCadres.items():
                if dictCadre["titulaire"] == 1:
                    nbreTitulaires += 1
            if nbreTitulaires == 1:
                dlg = wx.MessageDialog(self,
                                       "Vous devez avoir au moins un titulaire de dossier dans une famille !",
                                       "Erreur de saisie", wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return
            etat = 0
            self.dictCadres[self.IDindividu_menu]["titulaire"] = 0
        else:
            etat = 1
            self.dictCadres[self.IDindividu_menu]["titulaire"] = 1
        DB = GestionDB.DB()
        req = "UPDATE rattachements SET titulaire=%d WHERE IDindividu=%d AND IDfamille=%d;" % (
        etat, self.IDindividu_menu, self.IDfamille)
        DB.ExecuterReq(req, MsgBox="ExecuterReq")
        DB.Commit()
        DB.Close()
        MAJ(self)

    def On_SetCorrespondant(self, event):
        if self.dictCadres[self.IDindividu_menu]["correspondant"]:
            # déjà le correspondant de cette famille
            dlg = wx.MessageDialog(self,
                                   "Déjà le correspondant de cette famille !\npour changer choisissez un autre titulaire",
                                   "Erreur de saisie", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        # Récup de l'ancdien correspondant
        exCorresp = None
        for IDindividu, dict in self.dictCadres.items():
            if dict["correspondant"]:
                exCorresp = IDindividu

        # Changement de correspondant de la famille
        designation = UTILS_SaisieAdresse.DesignationFamille(self.IDfamille,
                                                             partant=exCorresp)
        wx.MessageBox(
            "La nouvelle désignation pour la famille est '%s'\nVous pouvez la gérer dans les coordonnées d'un individu..." % designation)
        DB = GestionDB.DB()
        DB.ReqMAJ("familles", [('adresse_intitule', designation),
                               ('adresse_individu', self.IDindividu_menu)],
                  'IDfamille', self.IDfamille,
                  MsgBox="CTRL_Composition.On_SetCorrespondant")

        # Récup d'une adresse en propre à partir de son adresse auto
        if self.dictCadres[self.IDindividu_menu]["adresse_auto"]:
            exAdress = self.dictCadres[self.IDindividu_menu]["adresse_auto"]
            self.dictCadres[self.IDindividu_menu]["adresse_auto"] = None
            lstDonnees = [("adresse_auto", None), ]
            for item in ("rue_resid", "cp_resid", "ville_resid"):
                lstDonnees.append(
                    (item, self.getVal.dictInfosIndividus[exAdress][item]))
                self.dictCadres[self.IDindividu_menu][item] = \
                self.getVal.dictInfosIndividus[exAdress][item]
            DB.ReqMAJ("individus", lstDonnees, 'IDindividu', self.IDindividu_menu,
                      MsgBox="CTRL_Composition.On_SetCorrespondant2")

        # S'approprie les adresses auto de la famille pointant l'ancien correspondant
        if exCorresp:
            for IDindividu, dictInfo in self.getVal.dictInfosIndividus.items():
                if dictInfo[
                    "adresse_auto"] == exCorresp and IDindividu != self.IDindividu_menu:
                    DB.ReqMAJ("individus", [("adresse_auto", self.IDindividu_menu), ],
                              'IDindividu', IDindividu,
                              MsgBox="CTRL_Composition.On_SetCorrespondant3 ID %d" % IDindividu)
                for item in ("rue_resid", "cp_resid", "ville_resid"):
                    self.dictCadres[self.IDindividu_menu][item] = \
                    self.getVal.dictInfosIndividus[self.IDindividu_menu][item]
        DB.Close()
        MAJ(self)

    def Ajouter(self, event=None):
        """ Rattacher un nouvel individu """
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_fiche",
                                                                  "creer") == False: return
        ok = True
        if not self.dictRattach:
            # Cas du lancement par ajouter à partir de composition
            from Dlg import DLG_Rattachement
            dlg = DLG_Rattachement.Dialog(None, IDfamille=self.IDfamille)
            if dlg.ShowModal() == wx.ID_OK:
                ok = True
                self.dictRattach = dlg.GetData()
            else:
                ok = False
            dlg.Destroy()
        if ok:
            mode, IDcategorie, titulaire, IDindividu, nom, prenom = self.dictRattach
            self.dictRattach = None
            nom = fp.NoPunctuation(nom)
            prenom = fp.NoPunctuation(prenom)
            if mode == "creation":
                # Création d'un nouvel individu rattaché
                dictInfosNouveau = {
                    "IDfamille": self.IDfamille,
                    "IDcategorie": IDcategorie,
                    "titulaire": titulaire,
                    "nom": nom.upper(),
                    "prenom": prenom.capitalize(),
                }
                dlg = DLG_Individu.Dialog(None, IDindividu=None,
                                          dictInfosNouveau=dictInfosNouveau)
                if dlg.ShowModal() == wx.ID_OK:
                    IDindividu = dlg.IDindividu  # print "Nouvelle fiche creee et deja rattachee."
                else:
                    self.SupprimerFamille()
                dlg.Destroy()
            else:
                # Rattachement d'un individu existant
                self.RattacherIndividu(IDindividu, IDcategorie, titulaire)

            # MAJ de l'affichage
            MAJ(self)
            return IDindividu
        else:
            self.SupprimerFamille()
            return None

    def Ajouter_individu(self, dictRattach=None):
        # Rattacher un nouvel individu, dont l'identité est issue de DLG_Rattachement
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_fiche",
                                                                  "creer") == False: return
        ok = True
        self.dictRattach = dictRattach
        if not dictRattach:
            # Cas du lancement par ajouter à partir de composition
            from Dlg import DLG_Rattachement
            dlg = DLG_Rattachement.Dialog(None, IDfamille=self.IDfamille)
            if dlg.ShowModal() == wx.ID_OK:
                ok = True
                self.dictRattach = dlg.GetDictData()
            else:
                ok = False
            dlg.Destroy()
        if ok:
            IDindividu = dictRattach['IDindividu']
            if self.dictRattach['mode'] == "creation":
                # Création d'un nouvel individu rattaché
                dlg = DLG_Individu.Dialog(None, IDindividu=None,
                                          dictInfosNouveau=self.dictRattach)
                if dlg.ShowModal() == wx.ID_OK:
                    IDindividu = dlg.IDindividu  # print "Nouvelle fiche creee et deja rattachee."
                else:
                    self.SupprimerFamille()
                dlg.Destroy()
            else:
                # Rattachement d'un individu existant
                args = [self.dictRattach[x] for x in ('IDindividu','IDcategorie','titulaire')]
                self.RattacherIndividu(*args)

            # MAJ de l'affichage
            MAJ(self)
            return IDindividu
        else:
            self.SupprimerFamille()
            return None

    def SupprimerFamille(self):
        # Supprime la fiche famille lorsqu'on annule le rattachement du premier titulaire
        DB = GestionDB.DB()
        req = """SELECT IDrattachement, IDfamille FROM rattachements 
        WHERE IDfamille=%d""" % self.IDfamille
        DB.ExecuterReq(req, MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if len(listeDonnees) == 0:
            self.GetParent().SupprimerFicheFamille()

    def RattacherIndividu(self, IDindividu=None, IDcategorie=None, titulaire=0):
        if not IDindividu or not self.IDfamille:
            return False
        # Saisie dans la base d'un rattachement
        DB = GestionDB.DB()
        listeDonnees = [
            ("IDindividu", IDindividu),
            ("IDfamille", self.IDfamille),
            ("IDcategorie", IDcategorie),
            ("titulaire", titulaire),
        ]
        IDrattachement = DB.ReqInsert("rattachements", listeDonnees)
        DB.Close()
        return True

    def Modifier_selection(self, event=None):
        """ Modifier une fiche à partir du bouton Modifier """
        IDindividu = self.selectionCadre
        self.selectionCadre = None
        if IDindividu == None:
            dlg = wx.MessageDialog(self,
                                   "Vous devez d'abord sélectionner un individu dans le cadre Composition !",
                                   "Erreur de saisie", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        else:
            self.Modifier(IDindividu)

    def Supprimer_selection(self, event=None):
        """ Supprimer ou detacher """
        IDindividu = self.selectionCadre
        self.selectionCadre = None
        if IDindividu == None:
            dlg = wx.MessageDialog(self,
                                   "Vous devez d'abord sélectionner un individu dans le cadre Composition !",
                                   "Erreur de saisie", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        else:
            self.Supprimer(IDindividu)

    def Modifier(self, IDindividu=None, maj=True):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_fiche",
                                                                  "modifier") == False: return
        dlg = DLG_Individu.Dialog(None, IDindividu=IDindividu, IDfamille=self.IDfamille)
        ret = dlg.ShowModal()
        if ret != wx.ID_OK:
            return
        # dlg.Destroy()
        MAJ(self)

    def Supprimer(self, IDindividu=None):
        """ Supprimer un individu """
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_fiche",
                                                                  "supprimer") == False: return
        from Dlg import DLG_Supprimer_fiche
        dlg = DLG_Supprimer_fiche.Dialog(self, IDindividu=IDindividu,
                                         IDfamille=self.IDfamille)
        reponse = dlg.ShowModal()
        dlg.Destroy()

        # MAJ de la fiche famille
        if reponse:
            # MAJ de l'affichage
            MAJ(self)


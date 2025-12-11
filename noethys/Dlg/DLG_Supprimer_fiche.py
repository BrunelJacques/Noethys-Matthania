#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB; Jacques Brunel
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import datetime
import GestionDB
from Utils import UTILS_Historique
from Utils import UTILS_Titulaires

ID_BOUTON_DETACHER = 1
ID_BOUTON_SUPPRIMER = 2
ID_SUPPRIMER_FAMILLE = 3

class Dialog(wx.Dialog):
    def __init__(self, parent, IDindividu=None, IDfamille=None):
        wx.Dialog.__init__(self, parent, -1, name="DLG_Supprimer_fiche", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        if hasattr(self.Parent,"dlgFamille"):
            self.dlgFamille = self.Parent.dlgFamille
        elif hasattr(self.GrandParent,"dlgFamille"):
            self.dlgFamille = self.GrandParent.dlgFamille
        self.IDindividu = IDindividu
        self.IDfamille = IDfamille
        self.staticbox_staticbox = wx.StaticBox(self, -1, "")
        self.label_intro = wx.StaticText(self, -1, _("Souhaitez-vous détacher ou supprimer cette fiche ?"))
        
        self.bouton_detacher = wx.BitmapButton(self, ID_BOUTON_DETACHER, wx.Bitmap(Chemins.GetStaticPath("Images/BoutonsImages/Detacher_fiche.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_supprimer = wx.BitmapButton(self, ID_BOUTON_SUPPRIMER, wx.Bitmap(Chemins.GetStaticPath("Images/BoutonsImages/Supprimer_fiche.png"), wx.BITMAP_TYPE_ANY))
        
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Annuler"), cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonDetacher, self.bouton_detacher)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSupprimer, self.bouton_supprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        
        self.bouton_annuler.SetFocus()
        self.familleDeleted = False
        
    def __set_properties(self):
        self.SetTitle(_("Supprimer une fiche"))
        self.bouton_detacher.SetToolTip(wx.ToolTip(_("Cliquez ici pour détacher la fiche")))
        self.bouton_supprimer.SetToolTip(wx.ToolTip(_("Cliquez ici pour supprimer la fiche")))
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici pour obtenir de l'aide")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Cliquez ici pour annuler")))
        self.SetMinSize((400, 240))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=3, vgap=10, hgap=10)
        staticbox = wx.StaticBoxSizer(self.staticbox_staticbox, wx.VERTICAL)
        grid_sizer_contenu = wx.FlexGridSizer(rows=2, cols=1, vgap=10, hgap=10)
        grid_sizer_commandes = wx.FlexGridSizer(rows=1, cols=2, vgap=10, hgap=10)
        grid_sizer_contenu.Add(self.label_intro, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
        grid_sizer_commandes.Add(self.bouton_detacher, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_commandes.Add(self.bouton_supprimer, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_commandes.AddGrowableRow(0)
        grid_sizer_commandes.AddGrowableCol(0)
        grid_sizer_commandes.AddGrowableCol(1)
        grid_sizer_contenu.Add(grid_sizer_commandes, 1, wx.EXPAND, 0)
        grid_sizer_contenu.AddGrowableRow(1)
        grid_sizer_contenu.AddGrowableCol(0)
        staticbox.Add(grid_sizer_contenu, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(staticbox, 1, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(0)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen() 

    def OnBoutonDetacher(self, event): 
        resultat = self.Detacher()
        if resultat == True : self.EndModal(ID_BOUTON_DETACHER)
        if resultat == False : self.EndModal(wx.ID_CANCEL)
        if resultat == "famille" : self.EndModal(ID_SUPPRIMER_FAMILLE)
    
    def Detacher(self):
        """ Processus de détachement d'une fiche individuelle """
        DB = GestionDB.DB()

        # Vérifie si son adresse n'est pas utilisée comme correspondant de la famille
        req = """   SELECT familles.IDfamille, Count(rattachements.IDrattachement)
                    FROM familles  
                    INNER JOIN rattachements ON familles.IDfamille = rattachements.IDfamille
                    WHERE (familles.IDfamille=%d AND (adresse_individu=%d))
                    GROUP BY familles.IDfamille;
                    """% (self.IDfamille, self.IDindividu)
        ret = DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        if len(listeDonnees) > 0 :
            (IDfamille, nbreRattachements) = listeDonnees[0]
            if nbreRattachements > 1:
                dlg = wx.MessageDialog(self, "L'adresse du détaché sert pour la correspondance de la famille,"+
                                             "\n\nchoisissez un autre correspondant !",
                                       _("Détachement impossible"), wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                DB.Close()
                return False


        # Vérifie si son adresse n'est pas utilisée dans la famille
        req = """   SELECT individus.IDindividu,individus.nom, individus.prenom
                    FROM individus INNER JOIN rattachements ON individus.IDindividu = rattachements.IDindividu
                    WHERE ((rattachements.IDfamille = %d) AND (individus.adresse_auto = %d));
                    """% (self.IDfamille, self.IDindividu)
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        if len(listeDonnees) > 0 :
            strNoms = ""
            for ID,nom,prenom in listeDonnees:
                strNoms +=  "\n" + prenom + " " + nom
            dlg = wx.MessageDialog(self, "L'adresse du détaché sert à d'autres membres, corrigez : %s"%(strNoms), _("Détachement impossible"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            DB.Close()
            return False

        # Recherche si cet individu n'est pas rattaché à une autre famille
        req = """
        SELECT IDfamille
        FROM rattachements
        WHERE IDindividu=%d and IDfamille<>%d
        """ % (self.IDindividu, self.IDfamille)
        DB.ExecuterReq(req,MsgBox="DLG_Supprimer_fiche")
        listeDonnees = DB.ResultatReq()
        existRattach = False
        newFamille = None
        if len(listeDonnees) > 0 :
            existRattach = True
            newFamille = listeDonnees[0][0]


        # Compte le nbre d'individus présents dans la fiche
        req = """
        SELECT IDrattachement, IDindividu
        FROM rattachements
        WHERE IDindividu<>%d AND IDfamille=%d
        """ % (self.IDindividu, self.IDfamille)
        DB.ExecuterReq(req,MsgBox="DLG_Supprimer_fiche")
        listeDonnees = DB.ResultatReq()
        nbreAutresIndividus = len(listeDonnees)
        
        # Vérifie qu'il ne s'agit pas du dernier titulaire
        req = """
        SELECT IDrattachement, IDindividu
        FROM rattachements
        WHERE IDcategorie=1 AND titulaire=1 AND IDindividu<>%d AND IDfamille=%d
        """ % (self.IDindividu, self.IDfamille)
        DB.ExecuterReq(req,MsgBox="DLG_Supprimer_fiche")
        listeDonnees = DB.ResultatReq()
        if len(listeDonnees) == 0 :
            dernierTitulaire = True
        else:
            dernierTitulaire = False

        if dernierTitulaire == True :
            if nbreAutresIndividus > 0 :
                # S'il s'agit du dernier titulaire mais qu'il y a d'autres membres dans la fiche famille
                dlg = wx.MessageDialog(self, _("Il s'agit du dernier titulaire du dossier, vous ne pouvez donc pas le détacher !\n\n(Si vous souhaitez supprimer la fiche famille, commencez pas détacher ou supprimer tous les autres membres de cette fiche)"), _("Détachement impossible"), wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                DB.Close()
                return False
            else:
                # S'il s'agit du dernier membre de la famille
                dlg = wx.MessageDialog(self, _("Il s'agit du dernier membre de cette famille.\n\nSouhaitez-vous détacher la fiche individuelle et supprimer la fiche famille ?"),
                                       _("Confirmation"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_EXCLAMATION)
                reponse = dlg.ShowModal()
                dlg.Destroy()
                if reponse !=  wx.ID_YES :
                    dlg = wx.MessageDialog(self, _("Vous ne pouvez pas détacher le dernier membre d'une famille sans supprimer la fiche famille !"), _("Détachement impossible"), wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    DB.Close()
                    return False
                
                # Vérifie qu'il est possible de supprimer la fiche famille

                req = """SELECT IDcotisation, IDfamille FROM cotisations WHERE IDfamille=%d""" % self.IDfamille
                DB.ExecuterReq(req)
                listeDonnees = DB.ResultatReq()
                if len(listeDonnees) >0 :
                    dlg = wx.MessageDialog(self, _("Vous ne pouvez pas supprimer la fiche famille car il y a déjà %d cotisation(s) enregistrée(s) dans cette fiche.") % len(listeDonnees), _("Détachement impossible"), wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    DB.Close()
                    return False
                
                req = """SELECT IDreglement, date FROM reglements 
                LEFT JOIN comptes_payeurs ON comptes_payeurs.IDcompte_payeur = reglements.IDcompte_payeur
                WHERE IDfamille=%d""" % self.IDfamille
                DB.ExecuterReq(req,MsgBox="DLG_Supprimer_fiche")
                listeDonnees = DB.ResultatReq()
                if len(listeDonnees) >0 :
                    dlg = wx.MessageDialog(self, _("Vous ne pouvez pas supprimer la fiche famille car il y a déjà %d règlement(s) enregistré(s) dans cette fiche.") % len(listeDonnees), _("Détachement impossible"), wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    DB.Close()
                    return False

                # Suppression de la fiche famille
                self.dlgFamille.SupprimerFicheFamille(IDfamille=self.IDfamille)
                self.familleDeleted = True

        # confirmation du détachement
        if existRattach:
            # détachement sans création
            mess = "Cet individu va être détaché de la famille %d, Il restera rattaché à la famille %d! confirmez!..."%(self.IDfamille,newFamille)
            mess += "\n\nVérifiez ensuite si l'adresse actuelle convient toujours!"
            dlg = wx.MessageDialog(self, _(mess),
                                   _("Confirmation"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_QUESTION)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse !=  wx.ID_YES :
                DB.Close()
                return False
        else:
            # détachement avant proposition création d'une nouvelle famille plus loin
            dlg = wx.MessageDialog(self, _("Cet individu va être détaché de cette famille\n\nConfirmez!"), _("Confirmation"),
                                   wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_QUESTION)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse !=  wx.ID_YES :
                DB.Close()
                return False


        # Détachement de la fiche individu
        req = "DELETE FROM rattachements WHERE IDfamille=%d AND IDindividu=%d;" % (self.IDfamille, self.IDindividu)
        DB.ExecuterReq(req)
        DB.Commit()

        self.AjouteMemo(DB)

       # Vérifie si son adresse était de type auto pour la dupliquer
        req = """   
                SELECT individus_1.rue_resid, individus_1.cp_resid, individus_1.ville_resid, 
                individus.IDindividu, individus.nom, individus.prenom,individus.cp_resid
                FROM individus 
                LEFT JOIN individus AS individus_1 ON individus.adresse_auto = individus_1.IDindividu
                WHERE (individus.IDindividu = %d );
                    """% (self.IDindividu)
        DB.ExecuterReq(req)
        lstDonnees = DB.ResultatReq()
        dictIndividus = {}
        for rue_1, cp_1,ville_1,IDindividu,nom,prenom,cp in lstDonnees:
            dictIndividus[IDindividu] = f"{IDindividu}-{prenom} {nom}"
            if cp_1 and not cp:
                # l'adresse était auto et pas de perso, on la duplique en perso
                lstDonnees = [('rue_resid', rue_1),
                              ('cp_resid', cp_1),
                              ('ville_resid',ville_1),
                              ('adresse_auto',None)]
                DB.ReqMAJ("individus",lstDonnees,"IDindividu",self.IDindividu)

        if not existRattach:
            # création et rattachement à une nouvelle famille après proposition
            dlg = wx.MessageDialog(self, _("Voulez-vous créer une nouvelle famille pour ce détaché ?"), _("Confirmation"),
                                   wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_QUESTION)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse ==  wx.ID_YES :
                # crétion d'une nouvelle famille
                if dictIndividus and self.IDindividu in dictIndividus:
                    lblIndividu = dictIndividus[self.IDindividu]
                else: # ne devrait pas se produire vérifier dans table 'historique'
                    lblIndividu = "Inconnu encore!"
                self.dlgFamille.CreateIDfamille(DB,lblIndividu)
                IDfamilleNew = self.dlgFamille.IDfamille
                # composition désignation de la famille
                dicIndividu = UTILS_Titulaires.GetIndividus([self.IDindividu,])[self.IDindividu]
                designation = "%s %s"%(dicIndividu["civiliteAbrege"],dicIndividu["nom_complet"])
                correspondant = self.IDindividu
                lstDonnees = [('adresse_individu',correspondant), ('adresse_intitule',designation)]
                ret = DB.ReqMAJ("familles", lstDonnees, "IDfamille", IDfamilleNew,MsgBox = "DLG_Supprimer_fiche.Detacher newfamille")
                if ret == 'ok':
                    self.NewRattachement(DB,IDfamilleNew,self.IDindividu)

        DB.Close()
        # Fermeture de la fiche famille
        return True

    def NewRattachement(self,DB,IDfamille, IDindividu):
        """ Rattacher un individu suite à un détachement il devient titulaire"""
        listeDonnees = [
            ("IDindividu", IDindividu),
            ("IDfamille", IDfamille),
            ("IDcategorie", 1),
            ("titulaire", 1),
            ]
        ret = DB.ReqInsert("rattachements", listeDonnees,retourID=None,
                            MsgBox = "DLG_Supprimer_fiche.Detacher newRattachement")
        if ret == 'ok':
            action = f"Ratachement individu {IDindividu} à la famille {IDfamille}"
        else:
            action = f"Echec ratachement individu {IDindividu} famille {IDfamille}, {ret}"
        UTILS_Historique.InsertActions([{
            "IDfamille": self.IDfamille,
            "IDindividu": self.IDindividu,
            "IDcategorie": 13,
            "action": action,
        }, ])

    def AjouteMemo(self,DB):
        # ajoute dans le memo de la fiche client
        action = _("Détaché de la famille ID %d le %s" ) % (self.IDfamille,str(datetime.date.today()))
        req = """
        SELECT nom, prenom, memo
        FROM individus
        WHERE IDindividu=%d
        """ % (self.IDindividu)
        DB.ExecuterReq(req,MsgBox="DLG_Supprimer_fiche MAJ")
        recordset = DB.ResultatReq()
        memo = ""
        sortant = ""
        for (nom, prenom, texte) in recordset:
            if texte == None: texte = ""
            if len(texte) >0:
                memo += texte + "\n"
            if nom == None : nom = ""
            if prenom == None : prenom = ""
            sortant += prenom + " " + nom
        memo += action
        DB.ReqMAJ("individus",[("memo",memo),("deces", 1),("annee_deces",datetime.date.today().year)],"IDindividu",self.IDindividu,MsgBox="DLG_Supprimer_fiche MAJ")

        # message dans la famille quittée
        if not self.familleDeleted:
            message = sortant + " est sorti le %s " % datetime.date.today()
            from Dlg import DLG_Saisie_message
            dlg = DLG_Saisie_message.Dialog(self, IDmessage=None, IDfamille=self.IDfamille, mode="famille")
            dlg.MessageDirect(mess = message)
            dlg.Destroy()

        # Mémorise l'action dans l'historique.
        if self.familleDeleted:
            action = _("Détachement individu ID%d et suppression famille ID%d") % (self.IDindividu, self.IDfamille)
        else:
            action = _("Détachement de la fiche individuelle ID%d de la famille ID %d") % (self.IDindividu, self.IDfamille)
        UTILS_Historique.InsertActions([{
                "IDfamille" : self.IDfamille,
                "IDindividu" : self.IDindividu,
                "IDcategorie" : 14,
                "action" : action,
                },])
        return True

    def OnBoutonSupprimer(self, event): 
        resultat = self.Supprimer()
        if resultat == True : self.EndModal(ID_BOUTON_SUPPRIMER)
        if resultat == False : self.EndModal(wx.ID_CANCEL)
        if resultat == "famille" : self.EndModal()

    def Supprimer(self):
        """ Processus de suppression d'une fiche individuelle """
        DB = GestionDB.DB()

        # Vérifie si cet individu n'est pas correspondant de la famille
        req = """   SELECT familles.IDfamille, count(rattachements.IDindividu)
                    FROM familles
                    LEFT JOIN rattachements ON familles.IDfamille = rattachements.IDfamille 
                    WHERE ((familles.IDfamille=%d) AND (familles.adresse_individu=%d))
                    GROUP BY familles.IDfamille;
                    """% (self.IDfamille, self.IDindividu)
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        if len(listeDonnees) > 0 and listeDonnees[0][1] > 1:
            dlg = wx.MessageDialog(self, _("Vous ne pouvez pas supprimer cette fiche car l'adresse sert pour la correspondance"+
                                           " avec la famille.\n\nChoisissez un autre correspondant"),
                                   _("Suppression impossible"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            DB.Close()
            return False

        # Vérifie si cet individu n'est pas rattaché à une autre famille
        req = """
        SELECT IDrattachement, IDfamille
        FROM rattachements
        WHERE IDindividu=%d and IDfamille<>%d
        """ % (self.IDindividu, self.IDfamille)
        DB.ExecuterReq(req,MsgBox="DLG_Supprimer_fiche")
        listeDonnees = DB.ResultatReq()
        if len(listeDonnees) > 0 :
            dlg = wx.MessageDialog(self, _("Vous ne pouvez pas supprimer cette fiche car elle est également rattachée à %d autre(s) famille(s).\n\nSi vous souhaitez vraiment la supprimer, veuillez la détacher de l'autre famille !") % len(listeDonnees), _("Suppression impossible"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            DB.Close()
            return False
        
        # Vérifie si des pièces n'existent pas
        req = """
        SELECT IDpiece, IDtype_piece
        FROM pieces
        WHERE IDindividu=%d and IDfamille=%d
        """ % (self.IDindividu, self.IDfamille)
        DB.ExecuterReq(req,MsgBox="DLG_Supprimer_fiche")
        listeDonnees = DB.ResultatReq()
        if len(listeDonnees) > 0 :
            dlg = wx.MessageDialog(self, _("Vous ne pouvez pas supprimer cette fiche car %d pièce(s) existent déjà pour cet individu sur cette fiche famille !") % len(listeDonnees), _("Suppression impossible"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            DB.Close()
            return False

        # Vérifie si des inscriptions n'existent pas
        req = """
        SELECT IDinscription, IDactivite
        FROM inscriptions
        WHERE IDindividu=%d and IDfamille=%d
        """ % (self.IDindividu, self.IDfamille)
        DB.ExecuterReq(req,MsgBox="DLG_Supprimer_fiche")
        listeDonnees = DB.ResultatReq()
        if len(listeDonnees) > 0 :
            dlg = wx.MessageDialog(self, _("Vous ne pouvez pas supprimer cette fiche car cet individu est déjà inscrit à %d activité(s) sur cette fiche famille !") % len(listeDonnees), _("Suppression impossible"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            DB.Close()
            return False
        
        # Vérifie si des consommations n'existent pas
        req = """
        SELECT IDconso, IDactivite
        FROM consommations
        LEFT JOIN comptes_payeurs ON comptes_payeurs.IDcompte_payeur = consommations.IDcompte_payeur
        WHERE consommations.IDindividu=%d and IDfamille=%d
        """ % (self.IDindividu, self.IDfamille)
        DB.ExecuterReq(req,MsgBox="DLG_Supprimer_fiche")
        listeDonnees = DB.ResultatReq()
        if len(listeDonnees) > 0 :
            dlg = wx.MessageDialog(self, _("Vous ne pouvez pas supprimer cette fiche car %d consommation(s) ont déjà été enregistrée(s) pour cet individu sur cette fiche famille !") % len(listeDonnees), _("Suppression impossible"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            DB.Close()
            return False

        # Vérifie si des prestations n'existent pas
        req = """
        SELECT IDprestation, label
        FROM prestations
        WHERE IDindividu=%d and IDfamille=%d
        """ % (self.IDindividu, self.IDfamille)
        DB.ExecuterReq(req,MsgBox="DLG_Supprimer_fiche")
        listeDonnees = DB.ResultatReq()
        if len(listeDonnees) > 0 :
            dlg = wx.MessageDialog(self, _("Vous ne pouvez pas supprimer cette fiche car %d prestations(s) ont déjà été enregistrée(s) pour cet individu sur cette fiche famille !") % len(listeDonnees), _("Suppression impossible"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            DB.Close()
            return False

        # Vérifie si des messages n'existent pas
        req = """
        SELECT IDmessage, type
        FROM messages
        WHERE IDindividu=%d and IDfamille=%d
        """ % (self.IDindividu, self.IDfamille)
        DB.ExecuterReq(req,MsgBox="DLG_Supprimer_fiche")
        listeDonnees = DB.ResultatReq()
        if len(listeDonnees) > 0 :
            dlg = wx.MessageDialog(self, _("Vous ne pouvez pas supprimer cette fiche car %d message(s) ont déjà été enregistré(s) pour cet individu sur cette fiche famille !") % len(listeDonnees), _("Suppression impossible"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            DB.Close()
            return False
        
        # Compte le nbre d'individus présents dans la fiche
        req = """
        SELECT IDrattachement, IDindividu
        FROM rattachements
        WHERE IDindividu<>%d AND IDfamille=%d
        """ % (self.IDindividu, self.IDfamille)
        DB.ExecuterReq(req,MsgBox="DLG_Supprimer_fiche")
        listeDonnees = DB.ResultatReq()
        nbreAutresIndividus = len(listeDonnees)
        
        # Vérifie qu'il ne s'agit pas du dernier titulaire
        req = """
        SELECT IDrattachement, IDindividu
        FROM rattachements
        WHERE IDcategorie=1 AND titulaire=1 AND IDindividu<>%d AND IDfamille=%d
        """ % (self.IDindividu, self.IDfamille)
        DB.ExecuterReq(req,MsgBox="DLG_Supprimer_fiche")
        listeDonnees = DB.ResultatReq()
        if len(listeDonnees) == 0 :
            dernierTitulaire = True
        else:
            dernierTitulaire = False
        if dernierTitulaire == True :
            if nbreAutresIndividus > 0 :
                # S'il s'agit du dernier titulaire mais qu'il y a d'autres membres dans la fiche famille
                dlg = wx.MessageDialog(self, _("Il s'agit du dernier titulaire du dossier, vous ne pouvez donc pas le supprimer !\n\n(Si vous souhaitez supprimer la fiche famille, commencez pas détacher ou supprimer tous les autres membres de cette fiche)"), _("Suppression impossible"), wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                DB.Close()
                return False
            else:
                # S'il s'agit du dernier membre de la famille
                dlg = wx.MessageDialog(self, _("Il s'agit du dernier membre de cette famille.\n\nSouhaitez-vous supprimer la fiche individuelle et la fiche famille ?"), _("Confirmation"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_EXCLAMATION)
                reponse = dlg.ShowModal()
                dlg.Destroy()
                if reponse !=  wx.ID_YES :
                    dlg = wx.MessageDialog(self, _("Vous ne pouvez pas supprimer le dernier membre d'une famille sans supprimer la fiche famille !"), _("Suppression impossible"), wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    DB.Close()
                    return False
                
                # Vérifie qu'il est possible de supprimer la fiche famille
                req = """SELECT IDaide, nom FROM aides WHERE IDfamille=%d""" % self.IDfamille
                DB.ExecuterReq(req,MsgBox="DLG_Supprimer_fiche")
                listeDonnees = DB.ResultatReq()
                if len(listeDonnees) >0 :
                    dlg = wx.MessageDialog(self, _("Vous ne pouvez pas supprimer la fiche famille car il y a déjà %d aide(s) journalière(s) enregistrée(s) dans cette fiche.") % len(listeDonnees), _("Suppression impossible"), wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    DB.Close()
                    return False
                
                req = """SELECT IDcotisation, IDfamille FROM cotisations WHERE IDfamille=%d""" % self.IDfamille
                DB.ExecuterReq(req,MsgBox="DLG_Supprimer_fiche")
                listeDonnees = DB.ResultatReq()
                if len(listeDonnees) >0 :
                    dlg = wx.MessageDialog(self, _("Vous ne pouvez pas supprimer la fiche famille car il y a déjà %d cotisation(s) enregistrée(s) dans cette fiche.") % len(listeDonnees), _("Suppression impossible"), wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    DB.Close()
                    return False
                
                req = """SELECT IDreglement, date FROM reglements 
                LEFT JOIN comptes_payeurs ON comptes_payeurs.IDcompte_payeur = reglements.IDcompte_payeur
                WHERE IDfamille=%d""" % self.IDfamille
                DB.ExecuterReq(req,MsgBox="DLG_Supprimer_fiche")
                listeDonnees = DB.ResultatReq()
                if len(listeDonnees) >0 :
                    dlg = wx.MessageDialog(self, _("Vous ne pouvez pas supprimer la fiche famille car il y a déjà %d règlement(s) enregistré(s) dans cette fiche.") % len(listeDonnees), _("Suppression impossible"), wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    DB.Close()
                    return False
                
                DB.Close()
                
                # Suppression de la fiche individu
                self.SupprimerIndividu()

                # Suppression de la fiche famille
                self.dlgFamille.SupprimerFicheFamille(IDfamille=self.IDfamille)
                self.familleDeleted = True

                return "famille"
        else :
            # Suppression de la fiche individuelle
            dlg = wx.MessageDialog(self, _("Etes-vous sûr de vouloir supprimer cette fiche ?"), _("Confirmation"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse !=  wx.ID_YES :
                DB.Close()
                return False

            DB.Close()
            self.SupprimerIndividu() 
            return True
    
    def SupprimerIndividu(self):
        # Suppression de l'individu
        DB = GestionDB.DB()
        req = """
            SELECT prenom,nom FROM individus 
            WHERE IDindividu=%d""" % self.IDindividu
        DB.ExecuterReq(req, MsgBox="DLG_Supprimer_fiche.SupprimerIndividu")
        listeDonnees = DB.ResultatReq()
        if len(listeDonnees) > 0:
            name =  str(self.IDindividu) + "-" + " ".join(listeDonnees[0])

        req = "DELETE FROM rattachements WHERE IDfamille=%d AND IDindividu=%d;" % (self.IDfamille, self.IDindividu)
        DB.ExecuterReq(req,MsgBox="DLG_Supprimer_fiche")
        req = "DELETE FROM liens WHERE IDfamille=%d AND IDindividu_sujet=%d;" % (self.IDfamille, self.IDindividu)
        DB.ExecuterReq(req,MsgBox="DLG_Supprimer_fiche")
        req = "DELETE FROM liens WHERE IDfamille=%d AND IDindividu_objet=%d;" % (self.IDfamille, self.IDindividu)
        DB.ExecuterReq(req,MsgBox="DLG_Supprimer_fiche")
        DB.ReqDEL("vaccins", "IDindividu", self.IDindividu)
        DB.ReqDEL("problemes_sante", "IDindividu", self.IDindividu)
        DB.ReqDEL("abonnements", "IDindividu", self.IDindividu)
        DB.ReqDEL("individus", "IDindividu", self.IDindividu)
        DB.ReqDEL("questionnaire_reponses", "IDindividu", self.IDindividu)
        DB.ReqDEL("inscriptions", "IDindividu", self.IDindividu)
        DB.ReqDEL("scolarite", "IDindividu", self.IDindividu)
        DB.ReqDEL("transports", "IDindividu", self.IDindividu)
        DB.ReqDEL("messages", "IDindividu", self.IDindividu)
        DB.Commit() 
        DB.Close()
        # Suppression de la photo 
        DB = GestionDB.DB(suffixe="PHOTOS")
        DB.ReqDEL("photos", "IDindividu", self.IDindividu)
        DB.Close()
        action = f"Suppression de l'individu {name} de la famille {self.IDfamille}"

        UTILS_Historique.InsertActions([{
            "IDfamille" : self.IDfamille,
            "IDindividu" : self.IDindividu,
            "IDcategorie" : 12,
            "action" : action,
        },])

    def OnBoutonAide(self, event): 
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Compositiondelafamille")

if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dialog_1 = Dialog(None, IDindividu=None)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()

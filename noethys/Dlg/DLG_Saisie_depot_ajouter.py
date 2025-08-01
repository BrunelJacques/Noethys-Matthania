#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import datetime

from Ol import OL_Reglements_depots
from Dlg import DLG_Messagebox
from Ctrl import CTRL_Saisie_date
from Ctrl.CTRL_ObjectListView import CTRL_Outils

import GestionDB


def DateEngFr(textDate):
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text



class CTRL_Compte(wx.Choice):
    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1) 
        self.parent = parent
        self.listeNoms = []
        self.listeID = []
        self.dictNumeros = {}
        self.SetListeDonnees() 
        self.SetID(None)
    
    def SetListeDonnees(self):
        self.listeNoms = [_("Tous les comptes")]
        self.listeID = [None,]
        DB = GestionDB.DB()
        req = """SELECT IDcompte, nom, numero
        FROM comptes_bancaires 
        ORDER BY nom;"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if len(listeDonnees) == 0 : return
        for IDcompte, nom, numero in listeDonnees :
            self.listeNoms.append(nom)
            self.listeID.append(IDcompte)
            self.dictNumeros[IDcompte] = numero
        self.SetItems(self.listeNoms)
    
    def SetID(self, ID=None):
        index = 0
        for IDcompte in self.listeID :
            if IDcompte == ID :
                 self.SetSelection(index)
            index += 1

    def GetID(self):
        index = self.GetSelection()
        if index == -1 : return None
        return self.listeID[index]
    
    def GetNumero(self):
        IDcompte = self.GetID() 
        if IDcompte != None :
            return self.dictNumeros[IDcompte]
        else:
            return None

# ------------------------------------------------------------------------------------------------------------------------------------------

class CTRL_Modes(wx.Choice):
    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1) 
        self.parent = parent
        self.listeNoms = []
        self.listeID = []
        self.SetListeDonnees() 
        self.SetID(None)
    
    def SetListeDonnees(self):
        self.listeNoms = [_("Tous les modes")]
        self.listeID = [None,]
        DB = GestionDB.DB()
        req = """SELECT IDmode, label
        FROM modes_reglements 
        ORDER BY label;"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if len(listeDonnees) == 0 : return
        for IDmode, nom in listeDonnees :
            self.listeNoms.append(nom)
            self.listeID.append(IDmode)
        self.SetItems(self.listeNoms)
    
    def SetID(self, ID=None):
        index = 0
        for IDcompte in self.listeID :
            if IDcompte == ID :
                 self.SetSelection(index)
            index += 1

    def GetID(self):
        index = self.GetSelection()
        if index == -1 : return None
        return self.listeID[index]
    
# ------------------------------------------------------------------------------------------------------------------------------------------


class Dialog(wx.Dialog):
    def __init__(self, parent, tracks=[], IDcompte=None, IDmode=None, date=None):
        wx.Dialog.__init__(self, parent, -1, name="DLG_Saisie_depot_ajouter", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.tracks= tracks
        self.IDcompte = IDcompte
        self.IDmode = IDmode
        self.date = date
        self.label_intro = wx.StaticText(self, -1, _("Double-cliquez sur un r�glement pour l'affecter ou non au d�p�t."), style=wx.ALIGN_CENTER)


        self.label_date = wx.StaticText(self, -1, _("Date limite :"))
        self.ctrl_date = CTRL_Saisie_date.Date2(self)
        if self.date:
            self.ctrl_date.SetDate(date)
        else:
            self.ctrl_date.SetDate(datetime.date.today())

        self.label_compte = wx.StaticText(self, -1, _("Compte :"))
        self.ctrl_compte = CTRL_Compte(self)
        self.ctrl_compte.SetMinSize((230, -1))
        self.ctrl_compte.SetID(self.IDcompte)

        self.label_mode = wx.StaticText(self, -1, _("Mode :"))
        self.ctrl_mode = CTRL_Modes(self)
        self.ctrl_mode.SetMinSize((160, -1))
        if self.IDmode:
            self.ctrl_mode.SetID(self.IDmode)

        self.label_tri = wx.StaticText(self, -1, _("Tri :"))
        self.ctrl_tri = wx.Choice(self, -1, choices = (_("Ordre de saisie"), _("Date"), _("Mode de r�glement"), _("Emetteur"), _("Num�ro de pi�ce"), _("Famille"), _("Nom de payeur"), _("Montant"),
                                                       _("Avis"), _("Compte"), _("Diff�r�"), _("Attente"), _("Quittancier"), _("Observations")))
        self.ctrl_tri.Select(1)

        self.label_ordre = wx.StaticText(self, -1, _("Ordre :"))
        self.ctrl_ordre = wx.Choice(self, -1, choices = (_("Descendant"), _("Ascendant")))
        self.ctrl_ordre.Select(1)
        
        # Reglements disponibles
        self.staticbox_reglements_disponibles_staticbox = wx.StaticBox(self, -1, _("R�glements disponibles"))
        kwd = {"inclus" : False,
               "sortable" : True,
               "style": wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_HRULES|wx.LC_VRULES|wx.LB_MULTIPLE}
        self.listviewAvecFooter1 = OL_Reglements_depots.ListviewAvecFooter(self, kwargs=kwd)
        self.ctrl_reglements_disponibles = self.listviewAvecFooter1.GetListview()
        self.ctrl_reglements_disponibles.Name = "ctrl_reglements_disponibles"
        self.ctrl_recherche = CTRL_Outils(self, listview=self.ctrl_reglements_disponibles)

        # Commandes
        self.bouton_bas_tout = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Fleche_double_bas.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_bas = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Fleche_bas.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_haut = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Fleche_haut_rouge.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_haut_tout = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Fleche_double_haut_rouge.png"), wx.BITMAP_TYPE_ANY))

        # Reglements du d�p�t
        self.staticbox_reglements_depot_staticbox = wx.StaticBox(self, -1, _("R�glements du d�p�t"))
        kwd = {"inclus" : True,
               "style": wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_HRULES|wx.LC_VRULES|wx.LB_MULTIPLE,
               "selectionPossible": True
               }
        self.listviewAvecFooter2 = OL_Reglements_depots.ListviewAvecFooter(self, kwargs=kwd)
        self.ctrl_reglements_depot = self.listviewAvecFooter2.GetListview()
        self.ctrl_reglements_depot.Name = "ctrl_reglements_depot"

        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ok"), cheminImage="Images/32x32/Valider.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Annuler"), cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()
        
        self.Bind(wx.EVT_BUTTON, self.OnBoutonBasTout, self.bouton_bas_tout)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonBas, self.bouton_bas)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonHaut, self.bouton_haut)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonHautTout, self.bouton_haut_tout)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_CHOICE, self.OnChoixCompte, self.ctrl_compte)
        self.Bind(wx.EVT_CHOICE, self.OnChoixMode, self.ctrl_mode)
        self.Bind(wx.EVT_CHOICE, self.OnChoixTri, self.ctrl_tri)
        self.Bind(wx.EVT_CHOICE, self.OnChoixOrdre, self.ctrl_ordre)

        # Initialisation des contr�les
        self.OnChoixTri(None)
        self.OnChoixOrdre(None)
        self.MAJListes(tracks=self.tracks) 

    def __set_properties(self):
        self.SetTitle(_("Ajouter ou retirer des r�glements"))
        self.ctrl_compte.SetToolTip(wx.ToolTip(_("S�lectionnez un filtre de compte")))
        self.ctrl_mode.SetToolTip(wx.ToolTip(_("S�lectionnez un filtre de mode de r�glement")))
        self.ctrl_tri.SetToolTip(wx.ToolTip(_("S�lectionnez le crit�re de tri")))
        self.ctrl_ordre.SetToolTip(wx.ToolTip(_("S�lectionnez l'ordre de tri")))
        self.bouton_bas_tout.SetToolTip(wx.ToolTip(_("Cliquez ici pour ajouter tous les r�glements dans le d�p�t")))
        self.bouton_bas.SetToolTip(wx.ToolTip(_("Cliquez ici pour ajouter le r�glement disponible selectionn� dans le d�p�t")))
        self.bouton_bas_tout.SetMinSize((80, -1))
        self.bouton_bas.SetMinSize((150, -1))
        self.bouton_haut.SetMinSize((150, -1))
        self.bouton_haut_tout.SetMinSize((80, -1))
        self.bouton_haut.SetToolTip(wx.ToolTip(_("Cliquez ici pour retirer le r�glement s�lectionn� du d�p�t")))
        self.bouton_haut_tout.SetToolTip(wx.ToolTip(_("Cliquez ici pour retirer tous les r�glements du d�p�t")))
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici pour obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_("Cliquez ici pour valider")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Cliquez ici pour annuler")))
        self.SetMinSize((1100, 850))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=5, cols=1, vgap=10, hgap=10)
        
        # Intro
        grid_sizer_intro = wx.FlexGridSizer(rows=1, cols=8, vgap=5, hgap=5)
        grid_sizer_intro.Add(self.label_intro, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER, 0)
        grid_sizer_intro.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_intro, 1, wx.ALL|wx.EXPAND, 10)
        
        # R�glements disponibles
        staticbox_reglements_disponibles = wx.StaticBoxSizer(self.staticbox_reglements_disponibles_staticbox, wx.VERTICAL)
        grid_sizer_dispo = wx.FlexGridSizer(rows=2, cols=1, vgap=10, hgap=10)
        
        grid_sizer_options = wx.FlexGridSizer(rows=1, cols=17, vgap=5, hgap=5)
        grid_sizer_options.Add( (5, 5), 0, wx.EXPAND, 0)
        grid_sizer_options.Add(self.label_date, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_options.Add(self.ctrl_date, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_options.Add((5, 5), 0, wx.EXPAND, 0)
        grid_sizer_options.Add(self.label_compte, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_options.Add(self.ctrl_compte, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_options.Add((5, 5), 0, wx.EXPAND, 0)
        grid_sizer_options.Add(self.label_mode, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_options.Add(self.ctrl_mode, 0, 0, 0)
        grid_sizer_options.Add( (5, 5), 0, wx.EXPAND, 0)
        grid_sizer_options.Add(self.label_tri, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_options.Add(self.ctrl_tri, 0, 0, 0)
        grid_sizer_options.Add( (5, 5), 0, wx.EXPAND, 0)
        grid_sizer_options.Add(self.label_ordre, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_options.Add(self.ctrl_ordre, 0, 0, 0)
        grid_sizer_options.Add((15, 5), 0, wx.EXPAND, 0)
        grid_sizer_options.AddGrowableCol(0)
        grid_sizer_dispo.Add(grid_sizer_options, 0, wx.EXPAND, 0)
        
        grid_sizer_dispo.Add(self.listviewAvecFooter1, 0, wx.EXPAND, 0)
        
        grid_sizer_dispo.AddGrowableRow(1)
        grid_sizer_dispo.AddGrowableCol(0)
        staticbox_reglements_disponibles.Add(grid_sizer_dispo, 1, wx.ALL|wx.EXPAND, 5)
        staticbox_reglements_disponibles.Add(self.ctrl_recherche, 0, wx.EXPAND, 0)
        grid_sizer_base.Add(staticbox_reglements_disponibles, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        # Commandes de transfert
        grid_sizer_commandes = wx.FlexGridSizer(rows=1, cols=6, vgap=10, hgap=10)
        grid_sizer_commandes.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_commandes.Add(self.bouton_bas_tout, 0, 0, 0)
        grid_sizer_commandes.Add(self.bouton_bas, 0, 0, 0)
        grid_sizer_commandes.Add(self.bouton_haut, 0, 0, 0)
        grid_sizer_commandes.Add(self.bouton_haut_tout, 0, 0, 0)
        grid_sizer_commandes.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_commandes.AddGrowableCol(0)
        grid_sizer_commandes.AddGrowableCol(5)
        grid_sizer_base.Add(grid_sizer_commandes, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        # R�glements d�pos�s
        staticbox_reglements_depot = wx.StaticBoxSizer(self.staticbox_reglements_depot_staticbox, wx.VERTICAL)
        staticbox_reglements_depot.Add(self.listviewAvecFooter2, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_base.Add(staticbox_reglements_depot, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        self.SetSizer(grid_sizer_base)
        
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableRow(3)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen() 
    
    def MAJListes(self, tracks=None, selectionTrack=None, nextTrack=None):
        if tracks != None :
            self.tracks = tracks
        # MAJ Liste r�glements disponibles
        date = self.ctrl_date.GetDate()
        IDcompte = self.ctrl_compte.GetID() 
        IDmode = self.ctrl_mode.GetID() 
        self.ctrl_reglements_disponibles.MAJ(self.tracks, selectionTrack=selectionTrack,
                                             nextTrack=nextTrack, IDcompte=IDcompte,
                                             IDmode=IDmode, date=date)
        self.staticbox_reglements_disponibles_staticbox.SetLabel(self.ctrl_reglements_disponibles.GetLabelListe(_("r�glements disponibles")))
        # MAJ Liste r�glements du d�p�t
        self.ctrl_reglements_depot.MAJ(self.tracks, selectionTrack=selectionTrack, nextTrack=nextTrack) 
        self.staticbox_reglements_depot_staticbox.SetLabel(self.ctrl_reglements_depot.GetLabelListe(_("r�glements dans ce d�p�t")))
    
    def DeplacerTout(self, inclus=True):
        listeTracks = []
        for track in self.tracks :
            if inclus :
                ctrl = self.ctrl_reglements_disponibles
            else :
                ctrl = self.ctrl_reglements_depot
            if track.IDreglement in ctrl.GetListeIDreglement():
                track.inclus = inclus
            listeTracks.append(track)
        self.MAJListes(listeTracks)
        
    def GetTracks(self):
        return self.tracks

    def OnChoixDate(self):
        self.MAJListes()

    def OnChoixCompte(self, event):
        self.MAJListes()
        
    def OnChoixMode(self, event):
        self.MAJListes()
        
    def OnChoixTri(self, event):
        selection = self.ctrl_tri.GetSelection() 
        self.ctrl_reglements_disponibles.numColonneTri = selection
        #self.ctrl_reglements_depot.numColonneTri = selection
        self.MAJListes()

    def OnChoixOrdre(self, event):
        selection = self.ctrl_ordre.GetSelection() 
        self.ctrl_reglements_disponibles.ordreAscendant = selection
        #self.ctrl_reglements_depot.ordreAscendant = selection
        self.MAJListes()

    def OnBoutonBas(self, event): 
        self.ctrl_reglements_disponibles.Deplacer()

    def OnBoutonHaut(self, event):
        self.ctrl_reglements_depot.Deplacer()

    def OnBoutonBasTout(self, event): 
        dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment ajouter tous les r�glements ?"), _("Confirmation"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_EXCLAMATION)
        reponse = dlg.ShowModal()
        dlg.Destroy()
        if reponse ==  wx.ID_YES :
            self.DeplacerTout(inclus=True)

    def OnBoutonHautTout(self, event):
        dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment retirer tous les r�glements ?"), _("Confirmation"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_EXCLAMATION)
        reponse = dlg.ShowModal()
        dlg.Destroy()
        if reponse ==  wx.ID_YES :
            self.DeplacerTout(inclus=False)

    def OnBoutonAide(self, event): 
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Gestiondesdpts")

    def OnBoutonOk(self, event): 
        # Validation des r�glements s�lectionn�s
        tracks_differes = []
        for track in self.tracks :
            if track.inclus == True :
                # Cr�ation d'un label pour ce r�glement en cas de message � afficher
                label = _("R�glement ID%d du %s pay� en %s par %s") % (track.IDreglement, DateEngFr(str(track.date)), track.nom_mode, track.nom_payeur)
                
                # V�rifie si pas de r�glement en attente
                if track.encaissement_attente == True :
                    dlg = wx.MessageDialog(self, _("Vous avez s�lectionn� le r�glement suivant alors qu'il a �t� saisi avec l'option 'Encaissement en attente' :\n\n> %s\n\nIl vous est donc impossible de l'inclure dans ce d�p�t !") % label, _("R�glement en attente"), wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    return False
                    
                # V�rifie si r�glement diff�r�
                if track.date_differe != None :
                    if track.date_differe > datetime.date.today() :
                        tracks_differes.append(track)

        # Regroupement des messages
        if len(tracks_differes) > 0 :
            detail = []
            for track in tracks_differes:
                detail.append(_("R�glement ID%d du %s pay� en %s par %s") % (track.IDreglement, DateEngFr(str(track.date)), track.nom_mode, track.nom_payeur))
            introduction = _("Vous avez s�lectionn� des r�glements alors qu'ils comportent une date d'encaissement diff�r� sup�rieure � la date du jour :")
            conclusion = _("Souhaitez-vous tout de m�me les inclure dans ce d�p�t ?")
            dlg = DLG_Messagebox.Dialog(self, titre=_("Avertissement"), introduction=introduction, detail=u"\n".join(detail), conclusion=conclusion, icone=wx.ICON_EXCLAMATION, boutons=[_("Oui"), _("Non"), _("Annuler")])
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse != 0 :
                return False

        # Fermeture
        self.EndModal(wx.ID_OK)


if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dialog_1 = Dialog(None)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()

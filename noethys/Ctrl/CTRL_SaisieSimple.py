#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys branche Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB, Jacques Brunel
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#-----------------------------------------------------------


import Chemins
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Saisie_date
from Dlg import DLG_calendrier_simple
import GestionDB
import datetime


class CTRL(wx.SearchCtrl):
    def __init__(self, parent, size=(-1, -1), modeDLG=False):
        wx.SearchCtrl.__init__(self, parent, size=size, style=wx.TE_PROCESS_ENTER)
        self.modeDLG = modeDLG

class CTRL_date(wx.Panel):
    def __init__(self, parent, **kwds):
        name = kwds.pop("name","")
        label = kwds.pop("label","")
        wx.Panel.__init__(self, parent, id=-1, name=name, style=wx.TAB_TRAVERSAL)
        self.parent = parent

        self.label_date = wx.StaticText(self, -1, label)
        self.ctrl_date = CTRL_Saisie_date.Date(self)
        self.bouton_date = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Calendrier.png"), wx.BITMAP_TYPE_ANY))

        #self.Bind(wx.EVT_KILL_FOCUS, self.OnCtrlDate, self.ctrl_date)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonDate, self.bouton_date)
        self.bouton_date.SetToolTip(_("Cliquez ici pour choisir une date à partir du calendrier"))
        self.ctrl_date.SetToolTip(_("Saisissez une date ou choisissez dans le calendrier"))
        self.label_date.SetToolTip(_("Saisissez une date ou choisissez dans le calendrier"))
        self.SetMinSize((130 + len(label)*5, -1))

        # Période
        grid_sizer_dates = wx.FlexGridSizer(rows=1, cols=3, vgap=5, hgap=5)
        grid_sizer_dates.Add(self.label_date, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_dates.Add(self.ctrl_date, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_dates.Add(self.bouton_date, 0, 0, 0)
        self.SetSizer(grid_sizer_dates)
        grid_sizer_dates.Fit(self)

    def OnChoixDate(self,event):
        self.parent.OnchoixDate(event)

    def SetFocus(self):
        self.ctrl_date.SetFocus()

    def OnBoutonDate(self, event):
        dlg = DLG_calendrier_simple.Dialog(self)
        if dlg.ShowModal() == wx.ID_OK :
            date = dlg.GetDate()
            self.ctrl_date.SetDate(date)
        dlg.Destroy()

    def SetDate(self,date):
        self.ctrl_date.SetDate(date)

    def GetDate(self):
        return self.ctrl_date.GetDate()

# --------------------------- DLG de saisie de mot de passe ------------------------------------------------------
class Dialog(wx.Dialog):
    def __init__(self, parent, id=-1, title=_("Saisie d'un paramètre"), nomParam="Mon paramètre"):
        wx.Dialog.__init__(self, parent, id, title, name="CTRL_SaisieSimple")
        self.nomParam = nomParam
        self.saisie = None

        if self.nomParam != None :
            self.SetTitle(title)
            
        self.staticbox = wx.StaticBox(self, -1, "")
        self.label = wx.StaticText(self, -1, _("Veuillez saisir le paramétre : %s")% self.nomParam)
        self.ctrl_param = CTRL(self, modeDLG=False)
        self.ctrl_param.SetDescriptiveText("Saisir "+nomParam)

        # Texte pour rappeller mot de passe du fichier Exemple
        self.label_exemple = wx.StaticText(self, -1, _("La saisie sera stockée par <Enregistrer>"))
        self.label_exemple.SetFont(wx.Font(7, wx.SWISS, wx.NORMAL, wx.NORMAL))
        self.label_exemple.SetForegroundColour((130, 130, 130))

        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Enregistrer"), cheminImage=Chemins.GetStaticPath("Images/32x32/Valider.png"))
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Annuler"), cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png"))

        # Binds
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, self.bouton_annuler)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)

        self.__set_properties()
        self.__do_layout()
        
        self.ctrl_param.SetFocus() 
        
    def __set_properties(self):
        self.bouton_annuler.SetToolTip(_("Cliquez ici pour annuler"))
        self.bouton_ok.SetToolTip(_("Cliquez ici pour enregistrer"))
        self.ctrl_param.SetMinSize((300, -1))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=0, hgap=0)
        
        # Intro
        grid_sizer_base.Add(self.label, 0, wx.ALL, 10)
        
        # Staticbox
        staticbox = wx.StaticBoxSizer(self.staticbox, wx.HORIZONTAL)
        grid_sizer_contenu = wx.FlexGridSizer(rows=2, cols=1, vgap=2, hgap=2)
        grid_sizer_contenu.Add(self.ctrl_param, 1, wx.EXPAND, 0)
        grid_sizer_contenu.Add(self.label_exemple, 1, wx.ALIGN_RIGHT, 0)
        grid_sizer_contenu.AddGrowableCol(0)
        staticbox.Add(grid_sizer_contenu, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(staticbox, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_boutons.Add((20, 20), 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.ALL|wx.EXPAND, 10)
        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.Fit(self)
        self.Layout()
        self.CentreOnScreen()

    def OnBoutonOk(self,event):
        self.saisie = self.ctrl_param.GetValue()
        self.EndModal(wx.ID_OK)

    def OnCancel(self, event):
        self.EndModal(wx.ID_CANCEL,)

# --------------------------- DLG de saisie d'une date  -----------------------------------------------------------
class DlgDate(wx.Dialog):
    def __init__(self, parent, nomParam="Votre date", title=_("Saisie d'une date")):
        wx.Dialog.__init__(self, parent, -1, title, name="CTRL_SaisieSimple")
        self.nomParam = nomParam
        self.dateSaisie = None

        if self.nomParam != None :
            self.SetTitle(title)

        self.staticbox = wx.StaticBox(self, -1, "")
        self.label = wx.StaticText(self, -1, _("%s")% self.nomParam)
        self.ctrl_param = CTRL_date(self)

        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Validez"), cheminImage=Chemins.GetStaticPath("Images/32x32/Valider.png"))
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Abandon"), cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png"))

        # Binds
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, self.bouton_annuler)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)

        self.__set_properties()
        self.__do_layout()

        self.ctrl_param.SetFocus()

    def __set_properties(self):
        self.bouton_annuler.SetToolTip(_("Cliquez ici pour annuler"))
        self.bouton_ok.SetToolTip(_("Cliquez ici pour enregistrer"))
        self.ctrl_param.SetMinSize((300, -1))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=0, hgap=0)

        # Intro
        grid_sizer_base.Add(self.label, 0, wx.ALL, 10)

        # Staticbox
        staticbox = wx.StaticBoxSizer(self.staticbox, wx.HORIZONTAL)
        grid_sizer_contenu = wx.FlexGridSizer(rows=1, cols=1, vgap=2, hgap=2)
        grid_sizer_contenu.Add(self.ctrl_param, 1, wx.EXPAND, 0)
        grid_sizer_contenu.AddGrowableCol(0)
        staticbox.Add(grid_sizer_contenu, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(staticbox, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_boutons.Add((20, 20), 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.ALL|wx.EXPAND, 10)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.Fit(self)
        self.Layout()
        self.CentreOnScreen()

    def OnBoutonOk(self,event):
        self.dateSaisie = self.ctrl_param.GetDate()
        self.EndModal(wx.ID_OK)

    def GetDate(self):
            return self.dateSaisie

    def OnCancel(self, event):
        self.EndModal(wx.ID_CANCEL,)

# --------------------------- DLG de gestions des dates d'activité en changement ---------------------------------
class DlgDatesActivite(wx.Dialog):
    def __init__(self, parent, **kwds):
        title = "CTRL_SaisieSimple"
        id = -1
        nom_activite = kwds.pop("nom_activite","mon activité")
        date_debut = kwds.pop("date_debut","2000-01-01")
        date_fin = kwds.pop("date_fin","2000-12-31")

        wx.Dialog.__init__(self, parent, id, title,size=(500,350),style=wx.RESIZE_BORDER)
        self.SetTitle(title)

        self.lblAnnonce = wx.StaticText(self, -1, "Changement de dates d'activité et d'ouvertures des groupes:")
        self.lblAnnonce.SetFont(wx.Font(10, wx.ROMAN, wx.NORMAL, wx.NORMAL))
        self.lblAnnonce.SetForegroundColour((0, 0, 120))
        self.lblActivite = wx.StaticText(self, -1, nom_activite)
        self.lblActivite.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.lblActivite.SetForegroundColour((0, 0, 120))

        self.staticbox = wx.StaticBox(self, -1, "")

        txt = "Le choix 'Ouvertures selon l'ancienne période' permet de\nreproduire les jours fermés du calendrier précédent"
        self.lblInfo = wx.StaticText(self, -1,txt,style=wx.ALIGN_CENTER)
        self.lblInfo.SetFont(wx.Font(8, wx.ROMAN, wx.NORMAL, wx.NORMAL))
        self.lblInfo.SetForegroundColour((130, 130, 130))

        self.lblRef = wx.StaticText(self,-1,"Ancienne période,",style=wx.ALIGN_RIGHT)
        self.ctrlDuRef = CTRL_date(self,label="du:")
        self.ctrlAuRef = CTRL_date(self,label="au:")
        self.ctrlDuRef.SetDate(date_debut)
        self.ctrlAuRef.SetDate(date_fin)

        self.lblAct = wx.StaticText(self,-1,"Période de l'activité,",style=wx.ALIGN_RIGHT)
        self.ctrlDuAct = CTRL_date(self,label="du:")
        self.ctrlAuAct = CTRL_date(self,label="au:")
        self.ctrlDuAct.SetDate(date_debut)
        self.ctrlAuAct.SetDate(date_fin)

        self.radioTranspose = wx.RadioButton(self, -1,  "Ouvertures à trous idem ancienne période", style=wx.RB_GROUP)
        self.radioToutes = wx.RadioButton(self, -1,     "Ouvertures tous les jours de la période")
        self.radioToutes.SetValue(True)

        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Enregistrer"), cheminImage=Chemins.GetStaticPath("Images/32x32/Valider.png"))
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Annuler"), cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png"))

        self.__set_properties()
        self.__do_layout()

        self.ctrlDuAct.SetFocus()

    def __set_properties(self):
        # Binds
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, self.bouton_annuler)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadio, self.radioToutes)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadio, self.radioTranspose)

        # TipString
        self.bouton_annuler.SetToolTip(_("Cliquez ici pour annuler"))
        self.bouton_ok.SetToolTip(_("Cliquez ici pour enregistrer"))
        self.lblRef.SetToolTip("l'ancienne période correspond à la période du modèle de l'activité dupliquée et sert de comparaison par les noms de groupes pour les ouvertures")
        self.lblAct.SetToolTip("La période d'activité va être appliquée aux différents onglets de l'écran précédent")
        self.lblInfo.SetMinSize((400, -1))
        self.lblRef.SetMinSize((130, -1))
        self.lblAct.SetMinSize((130, -1))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=0, hgap=0)

        # Intro
        grid_sizer_base.Add(self.lblAnnonce, 1, wx.TOP|wx.LEFT| wx.EXPAND, 10)
        grid_sizer_base.Add(self.lblActivite, 1, wx.TOP|wx.ALIGN_CENTER_HORIZONTAL, 5)
        # Staticbox
        staticbox = wx.StaticBoxSizer(self.staticbox, wx.HORIZONTAL)
        grid_contenu = wx.FlexGridSizer(rows=4, cols=1, vgap=5, hgap=2)

        grid_ref = wx.FlexGridSizer(rows=1, cols=3, vgap=10, hgap=10)
        grid_ref.Add(self.lblRef,1,wx.ALIGN_RIGHT|wx.EXPAND, 0)
        grid_ref.Add(self.ctrlDuRef, 0, wx.ALIGN_RIGHT, 0)
        grid_ref.Add(self.ctrlAuRef, 0, wx.ALIGN_RIGHT, 0)
        grid_ref.AddGrowableCol(0)
        grid_contenu.Add(grid_ref, 1, wx.ALIGN_CENTER, 0)

        grid_contenu.Add(self.lblInfo, 1, wx.LEFT|wx.ALIGN_CENTER, 130)

        grid_act = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_act.Add(self.lblAct,1,wx.ALIGN_RIGHT|wx.EXPAND, 0)
        grid_act.Add(self.ctrlDuAct, 0, wx.ALIGN_RIGHT, 0)
        grid_act.Add(self.ctrlAuAct, 0, wx.ALIGN_RIGHT, 0)
        grid_contenu.Add(grid_act, 1, wx.ALIGN_CENTER, 0)

        grid_radio = wx.FlexGridSizer(rows=2, cols=1, vgap=5, hgap=2)
        grid_radio.Add(self.radioTranspose,1,wx.ALIGN_CENTER, 0)
        grid_radio.Add(self.radioToutes,1,wx.ALIGN_CENTER, 0)
        grid_contenu.Add(grid_radio, 1, wx.TOP |wx.BOTTOM | wx.ALIGN_CENTER, 15)

        grid_contenu.AddGrowableCol(0)
        staticbox.Add(grid_contenu, 1, wx.ALL | wx.EXPAND, 10)
        grid_sizer_base.Add(staticbox, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_boutons.Add((20, 20), 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.ALL | wx.EXPAND, 10)

        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(2)
        self.SetSizer(grid_sizer_base)
        #grid_sizer_base.Fit(self)
        self.Layout()
        self.CentreOnScreen()

    def CtrlCoherence(self):
        mess = ""
        try:
            if self.radioTranspose.GetValue() and not (self.ctrlAuRef.GetDate() and self.ctrlDuRef.GetDate()):
                mess += "On ne peut pas transposer sans l'ancienne période\n"
            if not (self.ctrlDuAct.GetDate() and self.ctrlAuAct.GetDate()):
                mess += "Il faut obligatoirement saisir la période début et fin\n"
            if self.radioTranspose.GetValue() and self.ctrlAuRef.GetDate():
                if self.ctrlDuRef.GetDate() > self.ctrlAuRef.GetDate():
                    mess += "l'ancienne période débute après sa fin!\n"
            if self.ctrlDuAct.GetDate() > self.ctrlAuAct.GetDate():
                mess += "La période d'activité débute après sa fin!\n"

        except: pass
        if len(mess) >0:
            wx.MessageBox(mess)
            return False
        return True

    def CtrlDuree(self,debut,fin):
        return (fin - debut).days < 367

    def CtrlPresence(self):
        mess = ""
        if self.radioTranspose.GetValue():
            if not self.ctrlDuRef.GetDate():
                mess += "L'ancienne période n'a pas de date de début !\n"
            if not self.ctrlAuRef.GetDate():
                mess += "L'ancienne période n'a pas de date de fin !\n"
        if not self.ctrlDuAct.GetDate():
            mess += "La période d'activité n'a pas de date de début !\n"
        if not self.ctrlAuAct.GetDate():
            mess += "La période d'activité n'a pas de date de fin !\n"
        if len(mess) >0:
            wx.MessageBox(mess)
            return False
        # Vérification de la durée des périodes
        if self.radioTranspose.GetValue():
            if not self.CtrlDuree(self.ctrlDuRef.GetDate(),self.ctrlAuRef.GetDate()):
                mess += "L'ancienne période dure plus d'un an !\n"
        if not self.CtrlDuree(self.ctrlDuAct.GetDate(), self.ctrlAuAct.GetDate()):
            mess += "La période d'activité dure plus d'un an !\n"
        if len(mess) >0:
            wx.MessageBox(mess)
            return False
        if (self.ctrlDuAct.GetDate() == self.ctrlDuRef.GetDate()) and (self.ctrlAuAct.GetDate() == self.ctrlAuRef.GetDate()):
            mess += "Aucun changement n'est demandé !\n"
            wx.MessageBox(mess)
        return True

    def OnDate(self,event):
        self.CtrlCoherence()

    def OnRadio(self,event):
        refok = self.radioTranspose.GetValue()
        self.lblRef.Enable(refok)
        self.ctrlAuRef.Enable(refok)
        self.ctrlDuRef.Enable(refok)
        self.lblInfo.Enable(refok)

    def OnBoutonOk(self, event):
        if not self.CtrlCoherence():
            return
        if not self.CtrlPresence():
            return
        self.dictChoix = {
                    "transpose": self.radioTranspose.GetValue(),
                    "dateDebut_ref": self.ctrlDuRef.GetDate(),
                    "dateFin_ref": self.ctrlAuRef.GetDate(),
                    "dateDebut": self.ctrlDuAct.GetDate(),
                    "dateFin": self.ctrlAuAct.GetDate(),
                    }
        self.EndModal(wx.ID_OK)

    def OnCancel(self, event):
        self.EndModal(wx.ID_CANCEL, )

# ----------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    app = wx.App(0)
    #dlg = Dialog(None)
    #dlg = DlgDatesActivite(None)
    dlg = DlgDate(None,"Saisie de la date qu'il faut")
    app.SetTopWindow(dlg)
    ret = dlg.ShowModal()
    if ret == wx.ID_OK : print((dlg.GetDate()))
    app.MainLoop()

#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import Chemins
from Utils import UTILS_Adaptations
import wx
import wx.lib.masked as masked
import re
import sys
import datetime
import calendar
import six
from Utils import UTILS_Config
from dateutil.parser import parse, parserinfo
from dateutil import relativedelta
from Utils.UTILS_Traduction import _
from Utils import UTILS_Dates
from Ctrl import CTRL_Saisie_heure
from FonctionsPerso import Beep


ID_AIDE = 5
ID_AUJOURDHUI = 10
ID_HIER = 20
ID_DEMAIN = 30
ID_SEMAINE_ACTUELLE = 100
ID_SEMAINE_PRECEDENTE = 110
ID_SEMAINE_SUIVANTE = 120
ID_MOIS_ACTUEL = 200
ID_MOIS_PRECEDENT = 210
ID_MOIS_SUIVANT = 220
ID_ANNEE_ACTUELLE = 300
ID_ANNEE_PRECEDENTE = 310
ID_ANNEE_SUIVANTE = 320

# expression régulière pour une date (JJ/MM/AAAA)
datePattern = re.compile(
    r"(?P<jour>[\d]{1,2})/(?P<mois>[\d]{1,2})/(?P<annee>[\d]{4})")

class myparserinfo(parserinfo):
    JUMP = [" ", ".", ",", ";", "-", "/", "'",
            "at", "on", "and", "ad", "m", "t", "of",
            "st", "nd", "rd", "th"]

    WEEKDAYS = [(_("Lun"), _("Lundi")),
                (_("Mar"), _("Mardi")),
                (_("Mer"), _("Mercredi")),
                (_("Jeu"), _("Jeudi")),
                (_("Ven"), _("Vendredi")),
                (_("Sam"), _("Samedi")),
                (_("Dim"), _("Dimanche"))]
    MONTHS = [(_("Jan"), _("Janvier")),
              (_("Fév"), _("Février")),
              (_("Mar"), _("Mars")),
              (_("Avr"), _("Avril")),
              (_("Mai"), _("Mai")),
              (_("Juin"), _("Juin")),
              (_("Juil"), _("Juillet")),
              (_("Aoû"), _("Août")),
              (_("Sept"), _("Septembre")),
              (_("Oct"), _("Octobre")),
              (_("Nov"), _("Novembre")),
              (_("Déc"), _("Décembre")),]
    HMS = [("h", "hour", "hours"),
           ("m", "minute", "minutes"),
           ("s", "second", "seconds")]
    AMPM = [("am", "a"),
            ("pm", "p")]
    UTCZONE = ["UTC", "GMT", "Z"]
    PERTAIN = ["of"]
    TZOFFSET = {}

    def __init__(self) :
        parserinfo.__init__(self, dayfirst=True, yearfirst=False)

class Date(masked.TextCtrl):
    """ Contrôle Date simple """
    def __init__(self, parent, date_min="01/01/1900", date_max="01/01/2999", size=(-1, -1), pos=wx.DefaultPosition):
        self.mask_date = UTILS_Config.GetParametre("mask_date", "##/##/####")
        masked.TextCtrl.__init__(self, parent, -1, "", style=wx.TE_CENTRE |wx.TE_PROCESS_ENTER, size=size, pos=pos, mask=self.mask_date)
        self.parent = parent
        self.date_min = date_min
        self.date_max = date_max
        self.dateDD = None
        self.lienCtrlAge = False
        largeur = 95
        if "linux" in sys.platform :
            largeur = 110
        self.SetMinSize((largeur, -1))
        self.Bind(wx.EVT_TEXT_ENTER, self.OnKillFocus)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnContextMenu)
        if self.mask_date == "" :
            self.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)

    def OnDoubleClick(self, event):
        pass

    def SetDate(self, date):
        """ Importe une date string ou datetime """
        if (not date) or date == "" :
            return
        try :
            # Quelque soit le format, le change en datetime
            if type(date) == str or type(date) == six.text_type :
                if date[2] == "/" :
                    # Si c'est une date française
                    dateDD = datetime.date(year=int(date[6:10]), month=int(date[3:5]), day=int(date[:2]))
                else:
                    # Si c'est une date anglaise
                    dateDD = datetime.date(year=int(date[:4]), month=int(date[5:7]), day=int(date[8:10]))
            else:
                # Si c'est un datetime entre autre
                dateDD = date

            # Transformation en date française
            dateFR = self.DateEngFr(str(dateDD))
            self.SetValue(dateFR)
        except :
            pass
    
    def GetDate(self, FR=False):
        """ Récupère une date au format Datetime ou francaise"""
        dateFR = self.GetValue()
        if dateFR == "  /  /    " or dateFR == "" :
            return None
        validation = ValideDate(dateFR, self.date_min, self.date_max, avecMessages=False, mask=self.mask_date)
        if not validation :
            return None
        dateDD = datetime.date(year=int(dateFR[6:10]), month=int(dateFR[3:5]), day=int(dateFR[:2]))
        dateFR = self.DateEngFr(str(dateDD))
        if FR:
            return dateFR
        else:
            return dateDD
            
    def DateEngFr(self, textDate):
        text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
        return text

    def DateFrEng(self, textDate):
        text = str(textDate[6:10]) + "/" + str(textDate[3:5]) + "/" + str(textDate[:2])
        return text
        
    def OnKillFocus(self, event):
        self.MaJ_DateNaiss()
        # Vérification de la date
        self.FonctionValiderDate()
        # Envoi un signal de changement de date au panel parent
        self.parent.OnChoixDate()
        try :
            self.parent.OnChoixDate()
        except :
            pass
        event.Skip()
        
    def MaJ_DateNaiss(self):
        # Verifie la validite de la date
        if self.GetValue() == "  /  /    ":
            if self.lienCtrlAge == True :
                self.parent.ctrl_age.SetValue("")
            return

    def FonctionValiderDate(self):
        # Parser de la date en cas de format libre
        if self.GetValue() != "" and self.mask_date == "":
            try :
                date = parse(self.GetValue(), myparserinfo())
                self.SetDate(datetime.date(year=date.year, month=date.month, day=date.day))
            except :
                pass

        # Verifie la validite de la date
        validation = ValideDate(self.GetValue(), self.date_min, self.date_max, mask=self.mask_date)
        return validation
    
    def Validation(self):
        return self.FonctionValiderDate()
    
    def GetAge(self):
        # Calcul de l'age de la personne
        bday = self.GetDate()
        datedujour = datetime.date.today()
        age = (datedujour.year - bday.year) - int((datedujour.month, datedujour.day) < (bday.month, bday.day))
        return age
    
    def GetPanelParent(self):
        if self.parent.GetName() == "panel_date2" :
            return self.parent.parent
        else :
            return self.parent

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        menuPop = UTILS_Adaptations.Menu()
        
        item = wx.MenuItem(menuPop, ID_AUJOURDHUI, _("Aujourd'hui"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Date_actuelle.png"), wx.BITMAP_TYPE_PNG))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnActionMenu, id=ID_AUJOURDHUI)

        item = wx.MenuItem(menuPop, ID_HIER, _("Hier"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Date_precedente.png"), wx.BITMAP_TYPE_PNG))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnActionMenu, id=ID_HIER)

        item = wx.MenuItem(menuPop, ID_DEMAIN, _("Demain"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Date_suivante.png"), wx.BITMAP_TYPE_PNG))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnActionMenu, id=ID_DEMAIN)
        
        menuPop.AppendSeparator()
        
        listeFonctions = [
            (ID_SEMAINE_ACTUELLE, _("Semaine actuelle")),
            (ID_SEMAINE_PRECEDENTE, _("Semaine précédente")),
            (ID_SEMAINE_SUIVANTE, _("Semaine suivante")),
            (None, None),
            (ID_MOIS_ACTUEL, _("Mois actuel")),
            (ID_MOIS_PRECEDENT, _("Mois précédent")),
            (ID_MOIS_SUIVANT, _("Mois suivant")),
            (None, None),
            (ID_ANNEE_ACTUELLE, _("Année actuelle")),
            (ID_ANNEE_PRECEDENTE, _("Année précédente")),
            (ID_ANNEE_SUIVANTE, _("Année suivante")),
            ]
        for id, label in listeFonctions :
            if id == None :
                menuPop.AppendSeparator()
            else :
                sousMenu = UTILS_Adaptations.Menu()
                sousMenu.AppendItem(wx.MenuItem(menuPop, id+1, _("Date de début")))
                self.Bind(wx.EVT_MENU, self.OnActionMenu, id=id+1)
                sousMenu.AppendItem(wx.MenuItem(menuPop, id+2, _("Date de fin")))
                self.Bind(wx.EVT_MENU, self.OnActionMenu, id=id+2)
                item = menuPop.AppendMenu(id, label, sousMenu)
        
        menuPop.AppendSeparator()
        
        item = wx.MenuItem(menuPop, ID_AIDE, _("Aide"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Aide.png"), wx.BITMAP_TYPE_PNG))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnActionMenu, id=ID_AIDE)

        self.PopupMenu(menuPop)
        menuPop.Destroy()
    
    def OnActionMenu(self, event=None):
        id = event.GetId() 
        dateJour = datetime.date.today()
        
        if id == ID_AUJOURDHUI :
            self.SetDate(dateJour)
        
        if id == ID_HIER :
            self.SetDate(dateJour-datetime.timedelta(days=1))
        
        if id == ID_DEMAIN :
            self.SetDate(dateJour+datetime.timedelta(days=1))
        
        # Semaine
        if id == ID_SEMAINE_ACTUELLE + 1 :
            date = dateJour + relativedelta.relativedelta(weekday=relativedelta.MO(-1))
            self.SetDate(date)
        if id == ID_SEMAINE_ACTUELLE + 2 :
            date = dateJour + relativedelta.relativedelta(weekday=relativedelta.MO(-1))
            self.SetDate(date + datetime.timedelta(days=6))

        if id == ID_SEMAINE_PRECEDENTE + 1 :
            date = dateJour + relativedelta.relativedelta(weekday=relativedelta.SU(-1))
            self.SetDate(date - datetime.timedelta(days=6))
        if id == ID_SEMAINE_PRECEDENTE + 2 :
            date = dateJour + relativedelta.relativedelta(weekday=relativedelta.SU(-1))
            self.SetDate(date)

        if id == ID_SEMAINE_SUIVANTE + 1 :
            date = dateJour + relativedelta.relativedelta(weekday=relativedelta.MO(+1))
            self.SetDate(date)
        if id == ID_SEMAINE_SUIVANTE + 2 :
            date = dateJour + relativedelta.relativedelta(weekday=relativedelta.MO(+1))
            self.SetDate(date + datetime.timedelta(days=6))

        # Mois
        if id == ID_MOIS_ACTUEL + 1 :
            self.SetDate(datetime.date(dateJour.year, dateJour.month, 1))
        if id == ID_MOIS_ACTUEL + 2 :
            mois = calendar.monthrange(dateJour.year, dateJour.month)
            self.SetDate(datetime.date(dateJour.year, dateJour.month, mois[1]))

        if id == ID_MOIS_PRECEDENT + 1 :
            date = dateJour + relativedelta.relativedelta(months=-1)
            self.SetDate(datetime.date(date.year, date.month, 1))
        if id == ID_MOIS_PRECEDENT + 2 :
            date = dateJour + relativedelta.relativedelta(months=-1)
            mois = calendar.monthrange(date.year, date.month)
            self.SetDate(datetime.date(date.year, date.month, mois[1]))

        if id == ID_MOIS_SUIVANT + 1 :
            date = dateJour + relativedelta.relativedelta(months=+1)
            self.SetDate(datetime.date(date.year, date.month, 1))
        if id == ID_MOIS_SUIVANT + 2 :
            date = dateJour + relativedelta.relativedelta(months=+1)
            mois = calendar.monthrange(date.year, date.month)
            self.SetDate(datetime.date(date.year, date.month, mois[1]))

        # Année
        if id == ID_ANNEE_ACTUELLE + 1 :
            self.SetDate(datetime.date(dateJour.year, 1, 1))
        if id == ID_ANNEE_ACTUELLE + 2 :
            self.SetDate(datetime.date(dateJour.year, 12, 31))

        if id == ID_ANNEE_PRECEDENTE + 1 :
            date = dateJour + relativedelta.relativedelta(years=-1)
            self.SetDate(datetime.date(date.year, 1, 1))
        if id == ID_ANNEE_PRECEDENTE + 2 :
            date = dateJour + relativedelta.relativedelta(years=-1)
            self.SetDate(datetime.date(date.year, 12, 31))

        if id == ID_ANNEE_SUIVANTE + 1 :
            date = dateJour + relativedelta.relativedelta(years=+1)
            self.SetDate(datetime.date(date.year, 1, 1))
        if id == ID_ANNEE_SUIVANTE + 2 :
            date = dateJour + relativedelta.relativedelta(years=+1)
            self.SetDate(datetime.date(date.year, 12, 31))
        
        if id == ID_AIDE :
            from Utils import UTILS_Aide
            UTILS_Aide.Aide("Slectionnerunedate")

def ValideDate(texte, date_min="01/01/1900", date_max="01/01/2999", avecMessages=True, mask=""):
    """ Verificateur de validite de date """
    if texte == "  /  /    " or texte == "" :
        return True

    listeErreurs = []

    # Recherche depuis l'expression régulière
    date = datePattern.match(texte)
    if date:
        # On vérifie que les chiffres existent
        jour = int(date.group("jour"))
        if jour == 0 or jour > 31:
            listeErreurs.append(_("le jour"))
        mois = int(date.group("mois"))
        if mois == 0 or mois > 12:
            listeErreurs.append(_("le mois"))
        annee = int(date.group("annee"))
        if annee < 1900 or annee > 2999:
            listeErreurs.append(_("l'année"))

        # Affichage du message d'erreur
        if listeErreurs:
            # Message en cas de date incomplète
            if avecMessages == True :
                nbErreurs = len(listeErreurs)
                if nbErreurs == 1:
                    message = _("Une incohérence a été détectée dans ") + listeErreurs[0]
                else:
                    message = _("Des incohérences ont été détectées dans ") + listeErreurs[0]
                    if nbErreurs == 2:
                        message += " et " + listeErreurs[1]
                    elif nbErreurs == 3:
                        message += ", " + listeErreurs[1]  + " et " + listeErreurs[2]
                message += _(" de la date que vous venez de saisir. Veuillez la vérifier.")
                wx.MessageBox(message, "Erreur de date")
            return False
        else:
            # On vérifie que les dates sont comprises dans l'intervalle donné en paramètre
            date_min = int(str(date_min[6:10]) + str(date_min[3:5]) + str(date_min[:2]))
            date_max = int(str(date_max[6:10]) + str(date_max[3:5]) + str(date_max[:2]))
            date_sel = int(str(annee) + ('0' if mois < 10 else '') + str(mois) +
                                        ('0' if jour < 10 else '') + str(jour))

            if date_sel < date_min:
                if avecMessages == True :
                    message = _("La date que vous venez de saisir semble trop ancienne. Veuillez la vérifier.")
                    wx.MessageBox(message, "Erreur de date")
                return False
            if date_sel > date_max:
                if avecMessages == True :
                    message = _("La date que vous venez de saisir semble trop élevée. Veuillez la vérifier.")
                    wx.MessageBox(message, "Erreur de date")
                return False

            # On vérifie que la date peut être transformée en Datetime
            try:
                datetime.date(year=annee, month=mois, day=jour)
            except :
                pass
            else:
                return True

    if avecMessages == True :
        message = _("La date que vous venez de saisir ne semble pas valide !")
        wx.MessageBox(message, "Erreur de date")
    return False

class Date2(wx.Panel):
    """ Contrôle Date avec Bouton Calendrier inclus """
    def __init__(self, parent, date_min="01/01/1910", date_max="01/01/2030",
                 activeCallback=True, size=(-1, -1), heure=False, pos=wx.DefaultPosition):
        wx.Panel.__init__(self, parent, id=-1, name="panel_date2", size=size, pos=pos, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.activeCallback = activeCallback
        self.heure = heure
        
        self.ctrl_date = Date(self, date_min, date_max)
        self.bouton_calendrier = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Calendrier.png"), wx.BITMAP_TYPE_ANY))
        self.Bind(wx.EVT_BUTTON, self.OnBoutonCalendrier, self.bouton_calendrier)
        self.bouton_calendrier.SetToolTip(wx.ToolTip(_("Cliquez ici pour sélectionner la date dans le calendrier")))

        if heure == True :
            self.ctrl_heure = CTRL_Saisie_heure.Heure(self)

        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=3, vgap=5, hgap=5)
        grid_sizer_base.Add(self.ctrl_date, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 0)
        grid_sizer_base.Add(self.bouton_calendrier, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 0)
        if heure == True :
            grid_sizer_base.Add(self.ctrl_heure, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 0)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        self.Layout()
    
    def SetToolTipString(self, texte=""):
        self.ctrl_date.SetToolTip(wx.ToolTip(texte))

    def SetToolTip(self, tip=None):
        self.ctrl_date.SetToolTip(tip)

    def OnBoutonCalendrier(self, event): 
        from Dlg import DLG_calendrier_simple
        dlg = DLG_calendrier_simple.Dialog(self)
        if dlg.ShowModal() == wx.ID_OK :
            date = dlg.GetDate()
            self.ctrl_date.SetDate(date)
            self.OnChoixDate() 
        dlg.Destroy()

    def OnChoixDate(self):
        # Envoi un signal de changement de date au panel parent
        if self.activeCallback == True and hasattr(self.parent,"OnChoixDate"):
            self.parent.OnChoixDate()

    def SetDate(self, date):
        if type(date) == datetime.datetime or (type(date) in (str, six.text_type) and ":" in date):
            self.ctrl_date.SetDate(datetime.datetime.strftime(UTILS_Dates.DateEngEnDateDDT(date), "%Y-%m-%d"))
            if self.heure == True :
                self.ctrl_heure.SetHeure(datetime.datetime.strftime(UTILS_Dates.DateEngEnDateDDT(date), "%H:%M"))
        else :
            self.ctrl_date.SetDate(date)
    
    def GetDate(self, FR=False):
        if self.heure == False :
            return self.ctrl_date.GetDate(FR=FR)
        else :
            date = self.ctrl_date.GetDate()
            heure = self.ctrl_heure.GetHeure()
            if date == None or heure == None or heure == "  :  ":
                return None
            date_heure = datetime.datetime(year=date.year, month=date.month, day=date.day, hour=int(heure[:2]), minute=int(heure[3:]))
            return date_heure

    def FonctionValiderDate(self):
        return self.Validation()
    
    def Validation(self):
        if self.heure == False:
            return self.ctrl_date.FonctionValiderDate()
        else :
            date_valide = self.ctrl_date.FonctionValiderDate()
            if date_valide == False :
                return False

            heure = self.ctrl_heure.GetHeure()
            if heure == None or self.ctrl_heure.Validation() == False :
                dlg = wx.MessageDialog(self, _("Vous devez obligatoirement saisir une heure valide !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                self.ctrl_heure.SetFocus()
                return False

            return True
        
    def GetAge(self):
        return self.ctrl_date.GetAge() 
    
    def SetInsertionPoint(self, position=0):
        self.ctrl_date.SetInsertionPoint(position)
    
    def SetFocus(self):
        self.ctrl_date.SetFocus()

class Periode(wx.Panel):
    """ Saisie d'une période avec Bouton Calendrier inclus """
    def __init__(self, parent, size=(-1, -1),pos=wx.DefaultPosition):
        wx.Panel.__init__(self, parent, id=-1, name="periode",size=size,pos=pos)
        self.parent = parent
        self.periode = (datetime.date.today(),datetime.date.today())
        # Période
        self.label_du = wx.StaticText(self, wx.ID_ANY, _("Du"))
        self.ctrl_date_debut = Date2(self)
        self.label_au = wx.StaticText(self, wx.ID_ANY, _("au"))
        self.ctrl_date_fin = Date2(self)

        # Properties
        self.ctrl_date_debut.SetToolTip(wx.ToolTip("Saisir le début de la période"))
        self.ctrl_date_fin.SetToolTip(wx.ToolTip("Saisir la fin de la période"))

        self.__do_layout()
        self.SetPeriode()

    def __do_layout(self):
        sizer_base = wx.BoxSizer(wx.HORIZONTAL)

        grid_sizer_periode = wx.FlexGridSizer(2, 2, 5, 5)
        grid_sizer_periode.Add(self.label_du, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_periode.Add(self.ctrl_date_debut, 0, wx.EXPAND, 0)
        grid_sizer_periode.Add(self.label_au, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_periode.Add(self.ctrl_date_fin, 0, wx.EXPAND, 0)
        sizer_base.Add(grid_sizer_periode, 1, wx.EXPAND | wx.ALL, 10)

        self.SetSizer(sizer_base)
        self.Layout()

    def SetPeriode(self,periode=(datetime.date.today(),datetime.date.today())):
        self.periode = periode
        self.ctrl_date_debut.SetDate(self.periode[0])
        self.ctrl_date_fin.SetDate(self.periode[1])

    def GetPeriode(self):
        return self.periode

    def OnChoixDate(self):
        debut,fin = self.GetDateDebut(),self.GetDateFin()
        # incohérences dates saisies
        if fin < debut:
            Beep(duration=500)
            if self.periode[0] == debut:
                # début inchangé, on l'aligne sur la fin
                self.periode = (fin,fin)
            else:
                # on aligne la fin sur le début
                self.periode = (debut,debut)
            self.SetPeriode(self.periode)
        else:
            self.periode = (debut, fin)
        self.SetPeriode(self.periode)
        if hasattr(self.parent,'OnChoixDate'):
            self.parent.OnChoixDate()

    def GetDateDebut(self):
        return self.ctrl_date_debut.GetDate()

    def GetDateFin(self):
        return self.ctrl_date_fin.GetDate()

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="panel_test")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.ctrl1 = Date2(panel, heure=True)
        self.ctrl2 = Date2(panel)
        self.bouton1 = wx.Button(panel, -1, "Tester la validité du ctrl 1")
        self.periode = Periode(panel)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl1, 1, wx.ALL|wx.EXPAND, 4)
        sizer_2.Add(self.ctrl2, 0, wx.ALL|wx.EXPAND, 4)
        sizer_2.Add(self.bouton1, 0, wx.ALL | wx.EXPAND, 4)
        sizer_2.Add(self.periode, 1, wx.ALL | wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnBouton1, self.bouton1)

    def OnBouton1(self, event):
        print(self.ctrl1.Validation())

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "TEST", size=(800, 400))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()

#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, branche Matthania
# Module :  Pr�f�rences de base, avec choix adresse auteur
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------



from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Bandeau

import GestionDB
from Utils import UTILS_Config
from Utils import UTILS_Utilisateurs
from Utils import UTILS_Interface
from Utils import UTILS_Parametres

def Parametres(mode="get",nom="",valeur=""):
    return UTILS_Parametres.Parametres(mode=mode,categorie="preferences",
                                  nom=nom,valeur=valeur)

# -----------------------------------------------------------------------------

class Interface(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)

        self.staticbox_staticbox = wx.StaticBox(self, -1, _("Interface(1)"))

        # Th�me
        self.liste_labels_theme = []
        self.liste_codes_theme = []
        for code, label in UTILS_Interface.THEMES :
            self.liste_labels_theme.append(label)
            self.liste_codes_theme.append(code)

        self.label_theme = wx.StaticText(self, -1, _("Th�me :"))
        self.ctrl_theme = wx.Choice(self, -1, choices=self.liste_labels_theme)
        self.ctrl_theme.SetSelection(0)

        # Langue
        self.liste_labels_langue = [u"Fran�ais (par d�faut)",]
        self.liste_codes_langue = [None,]

        self.label_langue = wx.StaticText(self, -1, _("Langue :"))
        self.ctrl_langue = wx.Choice(self, -1, choices=self.liste_labels_langue)
        self.ctrl_langue.SetSelection(0)

        self.__set_properties()
        self.__do_layout()
        
        # Init
        self.Importation() 

    def __set_properties(self):
        self.ctrl_theme.SetToolTip(wx.ToolTip(_("S�lectionnez un th�me pour l'interface. Red�marrez le logiciel pour appliquer la modification.")))
        self.ctrl_langue.SetToolTip(wx.ToolTip(_("S�lectionnez la langue de l'interface parmi les langues disponibles dans la liste. Red�marrez le logiciel pour appliquer la modification.")))
        self.ctrl_langue.Enable(False)

    def __do_layout(self):
        staticbox = wx.StaticBoxSizer(self.staticbox_staticbox, wx.VERTICAL)
        grid_sizer_base = wx.FlexGridSizer(rows=2, cols=2, vgap=10, hgap=10)
        grid_sizer_base.Add(self.label_theme, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_base.Add(self.ctrl_theme, 1, wx.EXPAND, 0)
        grid_sizer_base.Add(self.label_langue, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_base.Add(self.ctrl_langue, 1, wx.EXPAND, 0)
        grid_sizer_base.AddGrowableCol(1)
        staticbox.Add(grid_sizer_base, 1, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(staticbox)
        staticbox.Fit(self)
    
    def Importation(self):
        # Th�me
        theme = UTILS_Interface.GetTheme()
        index = 0
        for code in self.liste_codes_theme :
            if code == theme :
                self.ctrl_theme.SetSelection(index)
            index += 1

        # Langue
        code = UTILS_Config.GetParametre("langue_interface", None)
        index = 0
        for codeTemp in self.liste_codes_langue :
            if codeTemp == code :
                self.ctrl_langue.SetSelection(index)
            index += 1
            
    def Validation(self):
        return True
    
    def Sauvegarde(self):
        # Th�me
        theme = self.liste_codes_theme[self.ctrl_theme.GetSelection()]
        UTILS_Interface.SetTheme(theme)

        # Langue
        code = self.liste_codes_langue[self.ctrl_langue.GetSelection()]
        UTILS_Config.SetParametre("langue_interface", code)

class Interface_mysql(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.listeLabels = [u"MySQLdb (par d�faut)", "mysql.connector"]
        self.listeCodes = ["mysqldb", "mysql.connector"]
        
        self.staticbox_staticbox = wx.StaticBox(self, -1, _("MySQL"))
        self.label_interface = wx.StaticText(self, -1, _("Interface :"))
        self.ctrl_interface = wx.Choice(self, -1, choices=self.listeLabels)
        self.label_pool_mysql = wx.StaticText(self, -1, _("Pool :"))
        self.ctrl_pool_mysql = wx.SpinCtrl(self, -1)
        self.ctrl_pool_mysql.SetRange(0, 20)

        self.__set_properties()
        self.__do_layout()
        
        self.ctrl_interface.SetSelection(0)
        self.Importation() 

    def __set_properties(self):
        self.ctrl_interface.SetToolTip(wx.ToolTip(_("S�lectionnez l'interface MySQL � utiliser pour les fichiers r�seau. 'Mysqldb' est conseill� mais il est possible que 'mysql.connector' soit parfois plus rapide pour certaines connexions distantes (par internet). Vous pouvez tester les deux pour choisir le plus rapide.")))
        self.ctrl_pool_mysql.SetToolTip(wx.ToolTip(_("S�lectionnez une valeur de pool pour l'interface mysql.connector (0 par d�faut)")))

    def __do_layout(self):
        staticbox = wx.StaticBoxSizer(self.staticbox_staticbox, wx.VERTICAL)
        grid_sizer_base = wx.FlexGridSizer(rows=2, cols=2, vgap=10, hgap=10)
        grid_sizer_base.Add(self.label_interface, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_base.Add(self.ctrl_interface, 1, wx.EXPAND, 0)
        grid_sizer_base.Add(self.label_pool_mysql, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_base.Add(self.ctrl_pool_mysql, 1, wx.EXPAND, 0)
        grid_sizer_base.AddGrowableCol(1)
        staticbox.Add(grid_sizer_base, 1, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(staticbox)
        staticbox.Fit(self)
    
    def Importation(self):
        code = UTILS_Config.GetParametre("interface_mysql", None)
        pool = UTILS_Config.GetParametre("pool_mysql", 5)
        index = 0
        for codeTemp in self.listeCodes :
            if codeTemp == code :
                self.ctrl_interface.SetSelection(index)
            index += 1
        self.ctrl_pool_mysql.SetValue(pool)
            
    def Validation(self):
        return True
    
    def Sauvegarde(self):
        interface_mysql = self.listeCodes[self.ctrl_interface.GetSelection()]
        UTILS_Config.SetParametre("interface_mysql", interface_mysql)
        pool_mysql = self.ctrl_pool_mysql.GetValue()
        UTILS_Config.SetParametre("pool_mysql", pool_mysql)

        try :
            topWindow = wx.GetApp().GetTopWindow()
            topWindow.userConfig["interface_mysql"] = interface_mysql
            topWindow.userConfig["pool_mysql"] = pool_mysql
            GestionDB.SetInterfaceMySQL(interface_mysql, pool_mysql)
        except Exception as err :
            print("Erreur dans changement de l'interface mySQL depuis les preferences :", err)

class Dates(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)

        self.staticbox_staticbox = wx.StaticBox(self, -1, _("Dates"))
        self.radio_france = wx.RadioButton(self, -1, _("Format fran�ais"), style=wx.RB_GROUP)
        self.radio_libre = wx.RadioButton(self, -1, _("Format libre"))

        self.__set_properties()
        self.__do_layout()

        self.Importation()

    def __set_properties(self):
        self.radio_france.SetToolTip(wx.ToolTip(_("Format fran�ais (JJ/MM/AAAA)")))
        self.radio_libre.SetToolTip(wx.ToolTip(_("Format libre")))

    def __do_layout(self):
        staticbox = wx.StaticBoxSizer(self.staticbox_staticbox, wx.VERTICAL)
        grid_sizer_base = wx.FlexGridSizer(rows=2, cols=5, vgap=10, hgap=10)
        grid_sizer_base.Add(self.radio_france, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_base.Add(self.radio_libre, 0, wx.EXPAND, 0)
        staticbox.Add(grid_sizer_base, 1, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(staticbox)
        staticbox.Fit(self)

    def Importation(self):
        mask = UTILS_Config.GetParametre("mask_date", "##/##/####")
        if mask == "":
            self.radio_libre.SetValue(True)
        else:
            self.radio_france.SetValue(True)

    def Validation(self):
        return True

    def Sauvegarde(self):
        if self.radio_france.GetValue() == True:
            mask = "##/##/####"
        else:
            mask = ""
        UTILS_Config.SetParametre("mask_date", mask)

class Telephones(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)

        self.staticbox_staticbox = wx.StaticBox(self, -1, _("Num�ros de t�l�phone"))
        self.radio_france = wx.RadioButton(self, -1, _("Format fran�ais"), style = wx.RB_GROUP)
        self.radio_libre = wx.RadioButton(self, -1, _("Format libre"))

        self.__set_properties()
        self.__do_layout()
        
        self.Importation() 

    def __set_properties(self):
        self.radio_france.SetToolTip(wx.ToolTip(_("Format fran�ais")))
        self.radio_libre.SetToolTip(wx.ToolTip(_("Format libre")))

    def __do_layout(self):
        staticbox = wx.StaticBoxSizer(self.staticbox_staticbox, wx.VERTICAL)
        grid_sizer_base = wx.FlexGridSizer(rows=2, cols=5, vgap=10, hgap=10)
        grid_sizer_base.Add(self.radio_france, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_base.Add(self.radio_libre, 0, wx.EXPAND, 0)
        staticbox.Add(grid_sizer_base, 1, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(staticbox)
        staticbox.Fit(self)
    
    def Importation(self):
        mask = UTILS_Config.GetParametre("mask_telephone", "##.##.##.##.##.")
        if mask == "" :
            self.radio_libre.SetValue(True)
        else:
            self.radio_france.SetValue(True)
    
    def Validation(self):
        return True
    
    def Sauvegarde(self):
        if self.radio_france.GetValue() == True :
            mask = "##.##.##.##.##."
        else:
            mask = ""
        UTILS_Config.SetParametre("mask_telephone", mask)

class Codes_postaux(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)

        self.staticbox_staticbox = wx.StaticBox(self, -1, _("Codes postaux"))
        self.radio_france = wx.RadioButton(self, -1, _("Format fran�ais"), style = wx.RB_GROUP)
        self.radio_libre = wx.RadioButton(self, -1, _("Format libre"))

        self.__set_properties()
        self.__do_layout()
        
        self.Importation() 

    def __set_properties(self):
        self.radio_france.SetToolTip(wx.ToolTip(_("Format fran�ais")))
        self.radio_libre.SetToolTip(wx.ToolTip(_("Format libre")))

    def __do_layout(self):
        staticbox = wx.StaticBoxSizer(self.staticbox_staticbox, wx.VERTICAL)
        grid_sizer_base = wx.FlexGridSizer(rows=2, cols=5, vgap=10, hgap=10)
        grid_sizer_base.Add(self.radio_france, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_base.Add(self.radio_libre, 0, wx.EXPAND, 0)
        staticbox.Add(grid_sizer_base, 1, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(staticbox)
        staticbox.Fit(self)
    
    def Importation(self):
        mask = UTILS_Config.GetParametre("mask_cp", "#####")
        if mask == "" :
            self.radio_libre.SetValue(True)
        else:
            self.radio_france.SetValue(True)
    
    def Validation(self):
        return True
    
    def Sauvegarde(self):
        if self.radio_france.GetValue() == True :
            mask = "#####"
        else:
            mask = ""
        UTILS_Config.SetParametre("mask_cp", mask)

class Adresses(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)

        self.staticbox_staticbox = wx.StaticBox(self, -1, _("Adresses"))
        self.check_autoComplete = wx.CheckBox(self, -1, _("Auto-compl�tion des villes et codes postaux"))

        self.__set_properties()
        self.__do_layout()
        
        self.Importation() 

    def __set_properties(self):
        self.check_autoComplete.SetToolTip(wx.ToolTip(_("Activation de l'auto-compl�tion")))

    def __do_layout(self):
        staticbox = wx.StaticBoxSizer(self.staticbox_staticbox, wx.VERTICAL)
        grid_sizer_base = wx.FlexGridSizer(rows=2, cols=5, vgap=10, hgap=10)
        grid_sizer_base.Add(self.check_autoComplete, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        staticbox.Add(grid_sizer_base, 1, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(staticbox)
        staticbox.Fit(self)
    
    def Importation(self):
        autoComplete = UTILS_Config.GetParametre("adresse_autocomplete", True)
        self.check_autoComplete.SetValue(autoComplete)
    
    def Validation(self):
        return True
    
    def Sauvegarde(self):
        UTILS_Config.SetParametre("adresse_autocomplete", self.check_autoComplete.GetValue())

class Autodeconnect(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)

        self.staticbox_staticbox = wx.StaticBox(self, -1,
                                                _("D�connexion automatique de l'utilisateur"))
        self.check_autodeconnect = wx.CheckBox(self, -1,
                                               _("D�connexion de l'utilisateur si inactivit� durant"))
        self.listeValeurs = [
            (15, "15 secondes"),
            (30, "30 secondes"),
            (60, "1 minute"),
            (120, "2 minutes"),
            (180, "3 minutes"),
            (240, "4 minutes"),
            (300, "5 minutes"),
            (360, "6 minutes"),
            (480, "8 minutes"),
            (600, "10 minutes"),
            (900, "15 minutes"),
            (1200, "20 minutes"),
            (1800, "30 minutes"),
            (3600, "1 heure"),
            (7200, "2 heures"),
        ]
        listeLabels = []
        for temps, label in self.listeValeurs:
            listeLabels.append(label)
        self.ctrl_temps = wx.Choice(self, -1, choices=listeLabels)
        self.ctrl_temps.SetSelection(0)

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_CHECKBOX, self.OnCheck, self.check_autodeconnect)

        self.Importation()

    def __set_properties(self):
        self.check_autodeconnect.SetToolTip(wx.ToolTip(
            _("Cochez cette case pour activer la d�connexion automatique de l'utilisateur au bout du temps d'inactivit� s�lectionn� dans la liste")))
        self.ctrl_temps.SetToolTip(
            wx.ToolTip(_("S�lectionnez un temps d'inactivit�")))

    def __do_layout(self):
        staticbox = wx.StaticBoxSizer(self.staticbox_staticbox, wx.VERTICAL)
        grid_sizer_base = wx.FlexGridSizer(rows=2, cols=5, vgap=0, hgap=0)
        grid_sizer_base.Add(self.check_autodeconnect, 0,
                            wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_base.Add(self.ctrl_temps, 0, wx.EXPAND, 0)
        grid_sizer_base.AddGrowableCol(1)
        staticbox.Add(grid_sizer_base, 1, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(staticbox)
        staticbox.Fit(self)

    def OnCheck(self, event=None):
        self.ctrl_temps.Enable(self.check_autodeconnect.GetValue())

    def GetValeur(self):
        if self.check_autodeconnect.GetValue() == True:
            index = self.ctrl_temps.GetSelection()
            temps = self.listeValeurs[index][0]
            return temps
        else:
            return None

    def SetValeur(self, valeur=None):
        if valeur == None:
            self.check_autodeconnect.SetValue(False)
        else:
            self.check_autodeconnect.SetValue(True)
            index = 0
            for temps, label in self.listeValeurs:
                if temps == valeur:
                    self.ctrl_temps.SetSelection(index)
                index += 1
        self.OnCheck(None)

    def Importation(self):
        valeur = UTILS_Config.GetParametre("autodeconnect", None)
        self.SetValeur(valeur)

    def Validation(self):
        return True

    def Sauvegarde(self):
        valeur = self.GetValeur()
        UTILS_Config.SetParametre("autodeconnect", valeur)
        try:
            topWindow = wx.GetApp().GetTopWindow()
            topWindow.userConfig["autodeconnect"] = valeur
            topWindow.Start_autodeconnect_timer()
        except:
            pass

class DerniersFichiers(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)

        self.staticbox_staticbox = wx.StaticBox(self, -1,
                                                _("Liste des derniers fichiers ouverts"))
        self.label_nbre = wx.StaticText(self, -1,
                                        _("Nombre de fichiers affich�s :"))
        self.ctrl_nbre = wx.SpinCtrl(self, -1)
        self.ctrl_nbre.SetRange(1, 20)
        self.bouton_purge = wx.Button(self, -1, _("Purger la liste"))

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonPurge, self.bouton_purge)

        self.Importation()

    def __set_properties(self):
        self.ctrl_nbre.SetToolTip(wx.ToolTip(
            _("Saisissez ici le nombre de fichiers � afficher dans la liste des fichiers ouverts")))
        self.bouton_purge.SetToolTip(wx.ToolTip(
            _("Cliquez ici pour purger la liste des derniers fichiers ouverts")))

    def __do_layout(self):
        staticbox = wx.StaticBoxSizer(self.staticbox_staticbox, wx.VERTICAL)
        grid_sizer_base = wx.FlexGridSizer(rows=2, cols=5, vgap=10, hgap=10)
        grid_sizer_base.Add(self.label_nbre, 0,
                            wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_base.Add(self.ctrl_nbre, 0, wx.EXPAND, 0)
        grid_sizer_base.Add(self.bouton_purge, 0, wx.EXPAND, 0)
        staticbox.Add(grid_sizer_base, 1, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(staticbox)
        staticbox.Fit(self)

    def Importation(self):
        nbre = UTILS_Config.GetParametre("nbre_derniers_fichiers", 10)
        self.ctrl_nbre.SetValue(nbre)

    def Validation(self):
        return True

    def Sauvegarde(self):
        nbre = self.ctrl_nbre.GetValue()
        UTILS_Config.SetParametre("nbre_derniers_fichiers", nbre)
        topWindow = wx.GetApp().GetTopWindow()
        try:
            topWindow.PurgeListeDerniersFichiers(nbre)
        except:
            pass

    def OnBoutonPurge(self, event):
        topWindow = wx.GetApp().GetTopWindow()
        topWindow.PurgeListeDerniersFichiers(1)

    # ---------------------------------------------------------------------------------------------------------------------------

class Email(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)

        self.staticbox_staticbox = wx.StaticBox(self, -1, _("Envoi d'emails"))
        self.check_timeout = wx.CheckBox(self, -1, _("Dur�e maximale de l'envoi personnalis�e :"))
        self.listeValeurs = [(5, "5 secondes"), (10, "10 secondes"), (20, "20 secondes"), (30, "30 secondes"),
            (40, "40 secondes"), (50, "50 secondes"), (60, "1 minute"), (120, "2 minutes"), (180, "3 minutes"),
            (240, "4 minutes"), (300, "5 minutes")]
        listeLabels = []
        for temps, label in self.listeValeurs:
            listeLabels.append(label)
        self.ctrl_temps = wx.Choice(self, -1, choices=listeLabels)
        self.ctrl_temps.SetSelection(0)

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_CHECKBOX, self.OnCheck, self.check_timeout)

        self.Importation()

    def __set_properties(self):
        self.check_timeout.SetToolTip(wx.ToolTip(_("Cochez cette case pour activer la dur�e maximale d'envoi personnalis�e")))
        self.ctrl_temps.SetToolTip(wx.ToolTip(_("S�lectionnez une dur�e")))

    def __do_layout(self):
        staticbox = wx.StaticBoxSizer(self.staticbox_staticbox, wx.VERTICAL)
        grid_sizer_base = wx.FlexGridSizer(rows=2, cols=5, vgap=0, hgap=0)
        grid_sizer_base.Add(self.check_timeout, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_base.Add(self.ctrl_temps, 0, wx.EXPAND, 0)
        grid_sizer_base.AddGrowableCol(1)
        staticbox.Add(grid_sizer_base, 1, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(staticbox)
        staticbox.Fit(self)

    def OnCheck(self, event=None):
        self.ctrl_temps.Enable(self.check_timeout.GetValue())

    def GetValeur(self):
        if self.check_timeout.GetValue() == True:
            index = self.ctrl_temps.GetSelection()
            temps = self.listeValeurs[index][0]
            return temps
        else:
            return None

    def SetValeur(self, valeur=None):
        if valeur == None:
            self.check_timeout.SetValue(False)
        else:
            self.check_timeout.SetValue(True)
            index = 0
            for temps, label in self.listeValeurs:
                if temps == valeur:
                    self.ctrl_temps.SetSelection(index)
                index += 1
        self.OnCheck(None)

    def Importation(self):
        valeur = UTILS_Parametres.Parametres(mode="get", categorie="email", nom="timeout", valeur=None)
        if valeur in ("","None"):
            valeur = None
        self.SetValeur(valeur)

    def Validation(self):
        return True

    def Sauvegarde(self):
        valeur = self.GetValeur()
        UTILS_Parametres.Parametres(mode="set", categorie="email", nom="timeout", valeur=valeur)

# -----------------------------------------------------------------------------

class Propose_maj(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.enable = parent.isAdmin
        self.enable = False
        self.staticbox_staticbox = wx.StaticBox(self, -1,
                                                _("Mises � jour internet(2)"))
        self.check = wx.CheckBox(self, -1,
                                 _("Propose le t�l�chargement des mises � jour � l'ouverture du logiciel"))

        self.__set_properties()
        self.__do_layout()

        self.Importation()

    def __set_properties(self):
        self.check.SetToolTip(wx.ToolTip(
            _("Propose le t�l�chargement des mises � jour � l'ouverture du logiciel")))
        self.check.Enable(self.enable)

    def __do_layout(self):
        staticbox = wx.StaticBoxSizer(self.staticbox_staticbox, wx.VERTICAL)
        grid_sizer_base = wx.FlexGridSizer(rows=2, cols=5, vgap=10, hgap=10)
        grid_sizer_base.Add(self.check, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        staticbox.Add(grid_sizer_base, 1, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(staticbox)
        staticbox.Fit(self)

    def Importation(self):
        valeur = Parametres("get","propose_maj", True)
        self.check.SetValue(valeur)

    def Validation(self):
        return True

    def Sauvegarde(self):
        Parametres("set","propose_maj", self.check.GetValue())

class Rapport_bugs(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.enable = parent.isAdmin

        self.staticbox_staticbox = wx.StaticBox(self, -1, _("Rapports de bugs(2)"))
        self.check = wx.CheckBox(self, -1, "Activation")
        self.label_mailAuteur = wx.StaticText(self, -1, "Mail du destinataire :")
        self.ctrl_mailAuteur = wx.TextCtrl(self, -1, "")

        self.__set_properties()
        self.__do_layout()
        
        self.Importation() 

    def __set_properties(self):
        self.check.SetToolTip(wx.ToolTip(_("Affichage du rapport de bugs lorsqu'une erreur est rencontr�e")))
        self.label_mailAuteur.SetToolTip(wx.ToolTip(_("Adresse du correspondant informatique qui traitera le probl�me")))
        self.ctrl_mailAuteur.SetToolTip(wx.ToolTip(_("Adresse du correspondant informatique qui traitera le probl�me")))
        self.Bind(wx.EVT_CHECKBOX,self.MAJ,self.check)
        self.check.Enable(self.enable)
        self.label_mailAuteur.Enable(self.enable)
        self.ctrl_mailAuteur.Enable(self.enable)

    def __do_layout(self):
        staticbox = wx.StaticBoxSizer(self.staticbox_staticbox, wx.VERTICAL)
        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=5, vgap=10, hgap=5)
        grid_sizer_base.Add(self.check, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
        grid_sizer_base.Add(self.label_mailAuteur, 0, wx.TOP|wx.ALIGN_CENTER_VERTICAL,2)
        grid_sizer_base.Add(self.ctrl_mailAuteur, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 0)
        grid_sizer_base.AddGrowableCol(2)
        staticbox.Add(grid_sizer_base, 1, wx.ALL|wx.EXPAND, 0)
        self.SetSizer(staticbox)
        staticbox.Fit(self)

    def Importation(self):
        self.check.SetValue(Parametres("get","rapports_bugs", True))
        self.ctrl_mailAuteur.SetValue(Parametres("get","rapports_mailAuteur", "xxxx@yyyy.com"))
        self.MAJ(None)

    def MAJ(self,evt):
        if self.check.GetValue():
            self.ctrl_mailAuteur.Enable(self.enable)
        else:
            self.ctrl_mailAuteur.Enable(False)

    def Validation(self):
        return True
    
    def Sauvegarde(self):
        Parametres("set","rapports_bugs", self.check.GetValue())
        Parametres("set","rapports_mailAuteur", self.ctrl_mailAuteur.GetValue())

class Monnaie(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.enable = parent.isAdmin
        self.staticbox_staticbox = wx.StaticBox(self, -1, _("Monnaie(1)(2)"))
        self.label_singulier = wx.StaticText(self, -1, _("Nom (singulier) :"))
        self.ctrl_singulier = wx.TextCtrl(self, -1, "")
        self.label_division = wx.StaticText(self, -1,
                                            _("Unit� divisionnaire :"))
        self.ctrl_division = wx.TextCtrl(self, -1, "")
        self.label_pluriel = wx.StaticText(self, -1, _("Nom (pluriel) :"))
        self.ctrl_pluriel = wx.TextCtrl(self, -1, "")
        self.label_symbole = wx.StaticText(self, -1, _("Symbole :"))
        self.ctrl_symbole = wx.TextCtrl(self, -1, "")

        self.ctrl_singulier.SetMinSize((70, -1))
        self.ctrl_division.SetMinSize((100, -1))
        self.ctrl_pluriel.SetMinSize((70, -1))

        self.__set_properties()
        self.__do_layout()

        self.Importation()

    def __set_properties(self):
        self.ctrl_singulier.SetToolTip(
            wx.ToolTip(_("'Euro' par d�faut (au singulier)")))
        self.ctrl_division.SetToolTip(
            wx.ToolTip(_("'Centime' par d�faut (au singulier)")))
        self.ctrl_pluriel.SetToolTip(
            wx.ToolTip(_("'Euros' par d�faut (au pluriel)")))
        self.ctrl_symbole.SetMinSize((60, -1))
        self.ctrl_symbole.SetToolTip(wx.ToolTip(_("'�' par d�faut")))

        self.ctrl_singulier.Enable(self.enable)
        self.ctrl_pluriel.Enable(self.enable)
        self.ctrl_division.Enable(self.enable)
        self.ctrl_symbole.Enable(self.enable)

        self.label_singulier.Enable(self.enable)
        self.label_pluriel.Enable(self.enable)
        self.label_division.Enable(self.enable)
        self.label_symbole.Enable(self.enable)

    def __do_layout(self):
        staticbox = wx.StaticBoxSizer(self.staticbox_staticbox, wx.VERTICAL)
        grid_sizer_base = wx.FlexGridSizer(rows=2, cols=5, vgap=5, hgap=5)
        grid_sizer_base.Add(self.label_singulier, 0,
                            wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_base.Add(self.ctrl_singulier, 0, wx.EXPAND, 0)
        grid_sizer_base.Add((0, 20), 0, 0, 0)
        grid_sizer_base.Add(self.label_division, 0,
                            wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_base.Add(self.ctrl_division, 0, 0, 0)
        grid_sizer_base.Add(self.label_pluriel, 0,
                            wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_base.Add(self.ctrl_pluriel, 0, wx.EXPAND, 0)
        grid_sizer_base.Add((0, 20), 0, 0, 0)
        grid_sizer_base.Add(self.label_symbole, 0,
                            wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_base.Add(self.ctrl_symbole, 0, 0, 0)
        grid_sizer_base.AddGrowableCol(1)
        staticbox.Add(grid_sizer_base, 1, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(staticbox)
        staticbox.Fit(self)

    def Importation(self):
        self.ctrl_singulier.SetValue(Parametres("get","monnaie_singulier", _("Euro")))
        self.ctrl_pluriel.SetValue(Parametres("get","monnaie_pluriel", _("Euros")))
        self.ctrl_division.SetValue(
            Parametres("get","monnaie_division", _("Centime")))
        self.ctrl_symbole.SetValue(
            Parametres("get","monnaie_symbole", "�"))

    def Validation(self):
        singulier = self.ctrl_singulier.GetValue()
        if len(singulier) == 0:
            dlg = wx.MessageDialog(self,
                                   _("Vous devez obligatoirement saisir une monnaie (singulier) !"),
                                   _("Erreur de saisie"),
                                   wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_singulier.SetFocus()
            return False

        pluriel = self.ctrl_pluriel.GetValue()
        if len(pluriel) == 0:
            dlg = wx.MessageDialog(self,
                                   _("Vous devez obligatoirement saisir une monnaie (pluriel) !"),
                                   _("Erreur de saisie"),
                                   wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_pluriel.SetFocus()
            return False

        division = self.ctrl_division.GetValue()
        if len(division) == 0:
            dlg = wx.MessageDialog(self,
                                   _("Vous devez obligatoirement saisir une monnaie (division) !"),
                                   _("Erreur de saisie"),
                                   wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_division.SetFocus()
            return False

        symbole = self.ctrl_symbole.GetValue()
        if len(symbole) == 0:
            dlg = wx.MessageDialog(self,
                                   _("Vous devez obligatoirement saisir un symbole pour la monnaie !"),
                                   _("Erreur de saisie"),
                                   wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_symbole.SetFocus()
            return False

        return True

    def Sauvegarde(self):
        singulier = self.ctrl_singulier.GetValue()
        pluriel = self.ctrl_pluriel.GetValue()
        division = self.ctrl_division.GetValue()
        symbole = self.ctrl_symbole.GetValue()

        Parametres("set","monnaie_singulier", singulier)
        Parametres("set","monnaie_pluriel", pluriel)
        Parametres("set","monnaie_division", division)
        Parametres("set","monnaie_symbole", symbole)

class Comptes_internet(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)

        self.enable = parent.isAdmin
        self.staticbox_staticbox = wx.StaticBox(self, -1, _("Comptes internet(2)"))
        self.label_taille = wx.StaticText(self, -1, _("Nombre de caract�res des mots de passe :"))
        self.ctrl_taille = wx.SpinCtrl(self, -1)
        self.ctrl_taille.SetRange(5, 20)

        self.__set_properties()
        self.__do_layout()

        self.Importation()

    def __set_properties(self):
        self.ctrl_taille.SetToolTip(wx.ToolTip(_("Saisissez ici la taille des mots de passe des comptes internet. Ce param�tre ne sera valable que pour les prochains comptes cr��s.")))
        self.ctrl_taille.Enable(self.enable)
        self.label_taille.Enable(self.enable)
        
    def __do_layout(self):
        staticbox = wx.StaticBoxSizer(self.staticbox_staticbox, wx.VERTICAL)
        grid_sizer_base = wx.FlexGridSizer(rows=2, cols=5, vgap=10, hgap=10)
        grid_sizer_base.Add(self.label_taille, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_base.Add(self.ctrl_taille, 0, wx.EXPAND, 0)
        staticbox.Add(grid_sizer_base, 1, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(staticbox)
        staticbox.Fit(self)

    def Importation(self):
        taille = UTILS_Parametres.Parametres(mode="get", categorie="comptes_internet", nom="taille_passwords", valeur=7)
        self.ctrl_taille.SetValue(taille)

    def Validation(self):
        return True

    def Sauvegarde(self):
        taille = self.ctrl_taille.GetValue()
        UTILS_Parametres.Parametres(mode="set", categorie="comptes_internet", nom="taille_passwords", valeur=taille)

# ------------------------------------------------------------------------------------------------------------------------

class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE)
        self.parent = parent
        self.isAdmin = UTILS_Utilisateurs.IsAdmin(False)
        intro = _("Vous pouvez modifier ici les param�tres de base du logiciel. Certains ne s'appliquent qu'� otre station<BR>(1) n�cessite un red�marrage du logiciel (2) s'applique � toute station et tout utilisateur.")
        titre = _("Pr�f�rences")
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/32x32/Configuration2.png")
        self.userConfig = {}
        # Contenu
        self.ctrl_interface = Interface(self)
        self.ctrl_monnaie = Monnaie(self)
        self.ctrl_dates = Dates(self)
        self.ctrl_adresses = Adresses(self)
        self.ctrl_rapport_bugs = Rapport_bugs(self)
        self.ctrl_propose_maj = Propose_maj(self)
        self.ctrl_derniers_fichiers = DerniersFichiers(self)
        self.ctrl_autodeconnect = Autodeconnect(self) 
        self.ctrl_interface_mysql = Interface_mysql(self) 
        self.ctrl_comptes_internet = Comptes_internet(self)
        self.ctrl_email = Email(self)

        # Red�marrage
        self.label_redemarrage = wx.StaticText(self, -1, _("(1) Le changement sera effectif au red�marrage du logiciel"))
        self.label_redemarrage.SetFont(wx.Font(7, wx.SWISS, wx.NORMAL, wx.NORMAL))
        self.label_admin = wx.StaticText(self, -1, _("(2) S'applique partout, la modification requiert des droits 'administrateur'"))
        self.label_admin.SetFont(wx.Font(7, wx.SWISS, wx.NORMAL, wx.NORMAL))

        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ok"), cheminImage="Images/32x32/Valider.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Annuler"), cheminImage="Images/32x32/Annuler.png")


        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        
    def __set_properties(self):
        self.SetTitle(_("Pr�f�rences"))
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici pour obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_("Cliquez ici pour valider la saisie")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Cliquez ici pour annuler et fermer")))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=5, cols=1, vgap=10, hgap=10)
        
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)
        
        grid_sizer_gauche = wx.FlexGridSizer(rows=8, cols=1, vgap=10, hgap=10)
        grid_sizer_gauche.Add(self.ctrl_interface, 1, wx.EXPAND, 0)
        grid_sizer_gauche.Add(self.ctrl_interface_mysql, 1, wx.EXPAND, 0)
        grid_sizer_gauche.Add(self.ctrl_derniers_fichiers, 1, wx.EXPAND, 0)
        grid_sizer_gauche.Add(self.ctrl_dates, 1, wx.EXPAND, 0)
        grid_sizer_gauche.Add(self.ctrl_adresses, 1, wx.EXPAND, 0)
        grid_sizer_gauche.Add(self.ctrl_autodeconnect, 1, wx.EXPAND, 0)
        grid_sizer_gauche.Add(self.ctrl_email, 1, wx.EXPAND, 0)

        grid_sizer_droit = wx.FlexGridSizer(rows=7, cols=1, vgap=10, hgap=10)
        grid_sizer_droit.Add(self.ctrl_propose_maj, 1, wx.EXPAND, 0)
        grid_sizer_droit.Add(self.ctrl_rapport_bugs, 1, wx.EXPAND, 0)
        grid_sizer_droit.Add(self.ctrl_monnaie, 1, wx.EXPAND, 0)
        grid_sizer_droit.Add(self.ctrl_comptes_internet, 1, wx.EXPAND, 0)
        grid_sizer_droit.Add((10,10), 1, wx.EXPAND, 0)
        grid_sizer_droit.Add(self.label_redemarrage, 1, wx.EXPAND, 0)
        grid_sizer_droit.Add(self.label_admin, 1, wx.EXPAND, 0)
        grid_sizer_droit.AddGrowableRow(4)

        grid_sizer_contenu = wx.FlexGridSizer(rows=10, cols=2, vgap=10, hgap=10)
        grid_sizer_contenu.Add(grid_sizer_gauche, 1, wx.EXPAND, 0)
        grid_sizer_contenu.Add(grid_sizer_droit, 1, wx.EXPAND, 0)
        
        grid_sizer_base.Add(grid_sizer_contenu, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        # Ligne vide pour agrandir la fen�tre
        grid_sizer_base.AddGrowableRow(2)
        grid_sizer_base.AddGrowableCol(0)

        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)

        self.Layout()
        self.CenterOnScreen()

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Prfrences")

    def OnBoutonOk(self, event):
        # Validation des donn�es
        if self.ctrl_interface.Validation() == False : return
        if self.ctrl_monnaie.Validation() == False : return
        if self.ctrl_dates.Validation() == False : return
        if self.ctrl_adresses.Validation() == False : return
        if self.ctrl_rapport_bugs.Validation() == False : return
        if self.ctrl_propose_maj.Validation() == False : return
        if self.ctrl_derniers_fichiers.Validation() == False : return
        if self.ctrl_autodeconnect.Validation() == False : return
        if self.ctrl_interface_mysql.Validation() == False : return
        if self.ctrl_comptes_internet.Validation() == False : return
        if self.ctrl_email.Validation() == False : return

        # Sauvegarde
        self.ctrl_interface.Sauvegarde()
        self.ctrl_monnaie.Sauvegarde()
        self.ctrl_dates.Sauvegarde()
        self.ctrl_adresses.Sauvegarde()
        self.ctrl_rapport_bugs.Sauvegarde()
        self.ctrl_propose_maj.Sauvegarde()
        self.ctrl_derniers_fichiers.Sauvegarde()
        self.ctrl_autodeconnect.Sauvegarde()
        self.ctrl_interface_mysql.Sauvegarde()
        self.ctrl_email.Sauvegarde()
        
        # Fermeture de la fen�tre
        self.EndModal(wx.ID_OK)
        
    
if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dialog_1 = Dialog(None)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()



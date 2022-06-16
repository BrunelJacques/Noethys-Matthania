#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys, Matthania adaptation saisie nombre
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB, Jacques Brunel
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#-----------------------------------------------------------


from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image


class CTRL(wx.TextCtrl):
    def __init__(self, parent, format= "0.00", font= None, size=(-1, -1), style=wx.TE_RIGHT, verif=True):
        wx.TextCtrl.__init__(self, parent, -1,format, size=size, style=style)
        self.parent = parent
        self.format = format
        self.SetToolTip(_("Saisissez un nombre"))
        if verif:
            self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
        if font != None :
            self.SetFont(font)
    
    def OnKillFocus(self, event):
        valide, messageErreur = self.Validation()
        if valide == False :
            wx.MessageBox(messageErreur, "Erreur de saisie")
        else:
            montant = int(self.GetValue())
            self.SetValue(str(montant))
        if event != None : event.Skip() 
    
    def Validation(self):
        # Vérifie si montant vide
        montantStr = self.GetValue()
        if montantStr == "":
            montantStr = "0"
        try :
            test = int(montantStr)
        except :
            message = _("Le nombre que vous avez saisi n'est pas valide.")
            return False, message
        return True, None
    
    def SetMontant(self, montant=0.0):
        if montant == None : montant = 0
        self.SetValue("%d" % montant)
    
    def GetMontant(self):
        validation, erreur = self.Validation()
        if validation == True :
            montant = float(self.GetValue()) 
            return montant
        else:
            return None
        
        
        


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.ctrl= CTRL(panel)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "TEST", size=(800, 400))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys branche Matthania,
# Module : Matthania possibilit� de nul et n�gatif, d�sactivation frais gestion
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB, Jacques Brunel
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import Chemins
import wx
from Ctrl import CTRL_Bouton_image
import os
import sys
import six
import datetime
import decimal
import wx.html as html
import wx.lib.agw.hyperlink as Hyperlink
import FonctionsPerso

from Utils import UTILS_Historique
from Utils import UTILS_Identification
from Utils import UTILS_Config
from Utils import UTILS_Titulaires
import GestionDB

SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "�")

from Ctrl import CTRL_Bandeau
from Ctrl import CTRL_Saisie_date
from Ctrl import CTRL_Saisie_euros
from Ctrl import CTRL_Ventilation as CTRL_Ventilation

ID_OPTION_BLOQUER_VENTILATION = wx.Window.NewControlId() 

# ----------------------------------------------------------------------------------------

def DateEngFr(textDate):
    if textDate == None: return ""
    textDate = str(textDate)
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text

def DateComplete(dateDD):
    """ Transforme une date DD en date compl�te : Ex : lundi 15 janvier 2008 """
    listeJours = (_("Lundi"), _("Mardi"), _("Mercredi"), _("Jeudi"), _("Vendredi"), _("Samedi"), _("Dimanche"))
    listeMois = (_("janvier"), _("f�vrier"), _("mars"), _("avril"), _("mai"), _("juin"), _("juillet"), _("ao�t"), _("septembre"), _("octobre"), _("novembre"), _("d�cembre"))
    dateComplete = listeJours[dateDD.weekday()] + " " + str(dateDD.day) + " " + listeMois[dateDD.month-1] + " " + str(dateDD.year)
    return dateComplete

def DateEngEnDateDD(dateEng):
    if dateEng and not isinstance(dateEng,str): dateEng = str(dateEng)
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

def DateFREnDateDD(dateFR):
    try:
        dateDD = datetime.date(int(dateFR[6:10]),int(dateFR[3:5]),int(dateFR[:2]), )
    except:
        dateDD = datetime.date.today()
    return dateDD

# ----------------------------------------------------------------------------------------

class CTRL_Image(wx.StaticBitmap):
    def __init__(self, parent, style=0):
        wx.StaticBitmap.__init__(self, parent, id=-1, style=style)
        self.parent = parent
        self.tailleImage = (132, 72)
        self.SetMinSize(self.tailleImage) 
        self.SetSize(self.tailleImage) 
        self.SetBackgroundColour(wx.Colour(0, 0, 0))
        
        self.SetPhotoMode()
        
    
    def SetPhotoMode(self, IDmode=None):
        bmp = self.GetPhoto("modes_reglements", "IDmode", IDmode, Chemins.GetStaticPath("Images/Special/Image_non_disponible.png"))
        self.SetBitmap(bmp)

    def SetPhotoEmetteur(self, IDemetteur=None):
        bmp = self.GetPhoto("emetteurs", "IDemetteur", IDemetteur, Chemins.GetStaticPath("Images/Special/Image_non_disponible.png"))
        self.SetBitmap(bmp)    

    def GetPhoto(self, table="", key="", IDkey=None, imageDefaut=None):
        """ R�cup�re une image """            
        # Recherche de l'image
        if IDkey != None : 
            DB = GestionDB.DB()
            req = "SELECT image FROM %s WHERE %s=%d;" % (table, key, IDkey)
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            listeDonnees = DB.ResultatReq()
            DB.Close()
            if len(listeDonnees) > 0 :
                # Si une image est trouv�e
                bmpBuffer = listeDonnees[0][0]
                if bmpBuffer != None :
                    io = six.BytesIO(bmpBuffer)
                    img = wx.Image(io, wx.BITMAP_TYPE_JPEG)
                    bmp = img.Rescale(width=self.tailleImage[0], height=self.tailleImage[1], quality=wx.IMAGE_QUALITY_HIGH) 
                    bmp = bmp.ConvertToBitmap()
                    return bmp
        
        # Si aucune image est trouv�e, on prend l'image par d�faut
        if imageDefaut != None :
            bmp = self.GetImageDefaut(imageDefaut) 
            return bmp
        
        return None
    
    def GetImageDefaut(self, imageDefaut):
        if os.path.isfile(imageDefaut):
            bmp = wx.Bitmap(imageDefaut, wx.BITMAP_TYPE_ANY) 
            bmp = bmp.ConvertToImage()
            bmp = bmp.Rescale(width=self.tailleImage[0], height=self.tailleImage[1], quality=wx.IMAGE_QUALITY_HIGH) 
            bmp = bmp.ConvertToBitmap()
            return bmp
        return None

class CTRL_Infos(html.HtmlWindow):
    def __init__(self, parent, texte="", hauteur=32,  couleurFond=(255, 255, 255), style=0):
        html.HtmlWindow.__init__(self, parent, -1, style=style)#, style=wx.html.HW_NO_SELECTION | wx.html.HW_SCROLLBAR_NEVER | wx.NO_FULL_REPAINT_ON_RESIZE)
        self.parent = parent
        if "gtk2" in wx.PlatformInfo:
            self.SetStandardFonts()
        self.SetBorders(5)
        self.SetMinSize((-1, hauteur))
        self.couleurFond = couleurFond
        font = self.parent.GetFont()
        self.SetFont(font)
        self.SetLabel(texte)
    
    def SetLabel(self, texte=""):
        self.SetPage("""<BODY TEXT='#B2B2B2' LINK='#B2B2B2' VLINK='#B2B2B2' ALINK='#B2B2B2'><FONT SIZE=1 COLOR='#777777'>%s</FONT></BODY>""" % texte)
        self.SetBackgroundColour(self.couleurFond)
    
    def OnLinkClicked(self, linkinfo):
        IDfamille = int(linkinfo.GetHref())

class CTRL_Mode(wx.Choice):
    # choix du mode de paiement
    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1) 
        self.parent = parent
        self.MAJ() 
    
    def MAJ(self):
        listeItems = self.GetListeDonnees()
        if len(listeItems) == 0 :
            self.Enable(False)
        self.SetItems(listeItems)

    def GetListeDonnees(self):
        db = GestionDB.DB()
        req = """
        SELECT IDmode, label, numero_piece, nbre_chiffres,  frais_gestion, frais_montant, 
        frais_pourcentage, frais_arrondi, frais_label, IDcompte
        FROM modes_reglements
        ORDER BY label;"""
        db.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = db.ResultatReq()
        db.Close()
        listeItems = []
        self.dictDonnees = {}
        index = 0
        for IDmode, label, numero_piece, nbre_chiffres, frais_gestion, frais_montant, \
            frais_pourcentage, frais_arrondi, frais_label, IDcompte in listeDonnees :
            self.dictDonnees[index] = { 
                "ID": IDmode, "label": label, "numero_piece": numero_piece, "nbre_chiffres": nbre_chiffres,
                "frais_gestion": frais_gestion, "frais_montant": frais_montant, "frais_pourcentage": frais_pourcentage, 
                "frais_arrondi": frais_arrondi, "frais_label": frais_label, "IDcompte": IDcompte
                }
            listeItems.append(label)
            index += 1
        return listeItems

    def SetID(self, ID=0):
        for index, values in self.dictDonnees.items():
            if values["ID"] == ID :
                 self.SetSelection(index)

    def GetID(self):
        index = self.GetSelection()
        if index == -1 : return None
        return self.dictDonnees[index]["ID"]
    
    def GetInfosMode(self):
        """ R�cup�re les infos sur le mode s�lectionn� """
        index = self.GetSelection()
        if index == -1 : return None
        return self.dictDonnees[index]

class CTRL_Emetteur(wx.Choice):
    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1) 
        self.parent = parent
        self.MAJ() 
        if len(self.dictDonnees) > 0 :
            self.SetSelection(0)
    
    def MAJ(self, IDmode=None):
        listeItems = self.GetListeDonnees(IDmode)
        if len(listeItems) == 0 :
            self.Enable(False)
        else:
            self.Enable(True)
        self.SetItems(listeItems)
    
    def GetListeDonnees(self, IDmode=None):
        self.dictDonnees = {}
        listeItems = []
        if IDmode == None :
            return listeItems
        db = GestionDB.DB()
        req = """SELECT IDemetteur, nom
        FROM emetteurs
        WHERE IDmode=%d
        ORDER BY nom;""" % IDmode
        db.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = db.ResultatReq()
        db.Close()
        index = 0
        for IDemetteur, nom in listeDonnees :
            self.dictDonnees[index] = { "ID" : IDemetteur }
            listeItems.append(nom)
            index += 1
        return listeItems

    def SetID(self, ID=0):
        for index, values in self.dictDonnees.items():
            if values["ID"] == ID :
                 self.SetSelection(index)

    def GetID(self):
        index = self.GetSelection()
        if index == -1 : return None
        return self.dictDonnees[index]["ID"]

class CTRL_Payeurs(wx.ListBox):
    def __init__(self, parent, IDcompte_payeur=None):
        wx.ListBox.__init__(self, parent, id=-1, choices=[])
        self.parent = parent
        self.IDcompte_payeur = IDcompte_payeur
        self.MAJ() 
    
    def MAJ(self, IDpayeur=None):
        self.listeDonnees = []
        self.Importation() 
        listeItems = []
        if len(self.listeDonnees) > 0 :
            for dictValeurs in self.listeDonnees :
                if dictValeurs["nom"] == None: dictValeurs["nom"] = " "
                label = dictValeurs["nom"]
                listeItems.append(label)
        self.Set(listeItems)
        if IDpayeur != None :
            self.SetID(IDpayeur)
        
    def Importation(self):
        db = GestionDB.DB()
        req = """SELECT IDpayeur, nom
        FROM payeurs 
        WHERE IDcompte_payeur=%d
        ORDER BY nom; """ % self.IDcompte_payeur
        db.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = db.ResultatReq()
        db.Close()
        for IDpayeur, nom in listeDonnees :
            valeurs = { "ID" : IDpayeur, "nom" : nom }
            self.listeDonnees.append(valeurs)
            
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

    def Ajouter(self):
        dlg = wx.TextEntryDialog(self, _("Saisissez le nom du nouveau payeur :"), _("Saisie d'un payeur"), "")
        if dlg.ShowModal() == wx.ID_OK:
            nom = dlg.GetValue()
            if nom == "":
                dlg = wx.MessageDialog(self, _("Le nom que vous avez saisi n'est pas valide !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return
            else:
                DB = GestionDB.DB()
                listeDonnees = [ ("IDcompte_payeur", self.IDcompte_payeur), ("nom", nom), ]
                IDpayeur = DB.ReqInsert("payeurs", listeDonnees)
                DB.Close()
                self.MAJ(IDpayeur)
        dlg.Destroy()

    def Modifier(self):
        IDpayeur = self.GetID()
        if IDpayeur == None :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucun payeur � modifier dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        nom = self.listeDonnees[self.GetSelection()]["nom"]
        dlg = wx.TextEntryDialog(self, _("Modifiez le nom du payeur :"), _("Modification d'un payeur"), nom)
        if dlg.ShowModal() == wx.ID_OK:
            nom = dlg.GetValue()
            if nom == "":
                dlg = wx.MessageDialog(self, _("Le nom que vous avez saisi n'est pas valide !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return
            else:
                DB = GestionDB.DB()
                listeDonnees = [ ("nom", nom ), ]
                DB.ReqMAJ("payeurs", listeDonnees, "IDpayeur", IDpayeur)
                DB.Close()
                self.MAJ(IDpayeur)
        dlg.Destroy()

    def Supprimer(self):
        IDpayeur = self.GetID()
        if IDpayeur == None :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucun payeur � supprimer dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
##        if self.Selection()[0].nbreTitulaires > 0 :
##            dlg = wx.MessageDialog(self, _("Il est impossible de supprimer une cat�gorie d�j� assign�e � un ou plusieurs individus !"), _("Suppression impossible"), wx.OK | wx.ICON_INFORMATION)
##            dlg.ShowModal()
##            dlg.Destroy()
##            return
        dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer ce payeur ?"), _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
        if dlg.ShowModal() == wx.ID_YES :
            DB = GestionDB.DB()
            DB.ReqDEL("payeurs", "IDpayeur", IDpayeur)
            DB.Close() 
            self.MAJ()
        dlg.Destroy()

class CTRL_Frais(Hyperlink.HyperLinkCtrl):
    def __init__(self, parent, id=-1, label="", infobulle="", URL="", size=(-1, -1), pos=(0, 0)):
        Hyperlink.HyperLinkCtrl.__init__(self, parent, id, label, URL=URL, size=size, pos=pos)
        self.parent = parent
        self.dictFrais = {}
        self.labelPrestation = ""
        self.montantPrestation = 0.0
        self.IDprestationFrais = None

        self.URL = URL
        self.AutoBrowse(False)
        self.SetColours("BLUE", "BLUE", "BLUE")
        self.SetUnderlines(False, False, True)
        self.SetBold(False)
        self.EnableRollover(True)
        self.SetToolTip(wx.ToolTip(infobulle))
        self.UpdateLink()
        self.DoPopup(False)
        self.Bind(Hyperlink.EVT_HYPERLINK_LEFT, self.OnLeftLink)
    
    def OnLeftLink(self, event):
        from Dlg import DLG_Saisie_frais_gestion
        dlg = DLG_Saisie_frais_gestion.Dialog(self, self.dictFrais)
        if dlg.ShowModal() == wx.ID_OK :
            self.dictFrais = dlg.GetDictFrais()
            self.MAJ() 
        dlg.Destroy()
        self.UpdateLink()

    def GetDictFrais(self):
        return self.dictFrais
    
    def SetPrestationFrais(self, IDprestationFrais=None, montant=None, labelPrestation=None):
        self.IDprestationFrais = IDprestationFrais
        self.dictFrais = {  
            "frais_gestion" : "FIXE",
            "frais_montant" : montant,
            "frais_pourcentage" : None,
            "frais_arrondi" : None,
            "frais_label" : labelPrestation,
            }
        self.MAJ()

    def SetDictFrais(self, dictFrais={}):
        self.dictFrais = dictFrais
        self.MAJ()
    
    def MAJ(self):
        if len(self.dictFrais) == 0 :
            self.SetLabel("Aucun frais")
            self.montantPrestation = 0.0
            self.labelPrestation = ""
            return       
         
        typeFrais = self.dictFrais["frais_gestion"]
        montant = self.dictFrais["frais_montant"]
        pourcentage = self.dictFrais["frais_pourcentage"]
        arrondi = self.dictFrais["frais_arrondi"]
        labelPrestation = self.dictFrais["frais_label"]
        
        # Calcul du montant
        montantReglement = self.parent.ctrl_montant.GetMontant()
        if montantReglement == None :
            montantReglement = 0.0
            
        # Aucun frais
        if typeFrais == None :
            self.montantPrestation = 0.0
            label = _("Aucun frais")

        # Montant libre
        if typeFrais == "LIBRE" :
            label = _("Aucun frais")

        # Montant fixe
        if typeFrais == "FIXE" :
            self.montantPrestation = montant
            label = "%.2f %s" % (self.montantPrestation, SYMBOLE)
        
        # Prorata
        if typeFrais == "PRORATA" :
            self.montantPrestation = 1.0 * montantReglement * pourcentage / 100.0
            x = decimal.Decimal(str(self.montantPrestation))
            if arrondi == "centimesup" : typeArrondi = decimal.ROUND_UP
            if arrondi == "centimeinf" : typeArrondi = decimal.ROUND_DOWN
            self.montantPrestation = float(x.quantize(decimal.Decimal('0.01'), typeArrondi))
            label = "%.2f %s (%s %%)" % (self.montantPrestation, SYMBOLE, pourcentage)
            
        # Recherche label prestation
        if labelPrestation != None :
            self.labelPrestation = labelPrestation
        else:
            self.labelPrestation = ""
        
        # Affiche label du hyperlien
        self.SetLabel(label)
    
    def GetDonnees(self):
        """ R�cup�re donn�es sur frais de gestion saisis """
        typeFrais = self.dictFrais["frais_gestion"]
        if typeFrais == None :
            # Aucun
            return (None, None, self.IDprestationFrais)
        else :
            # Autres types : Fixe et prorata
            return (self.montantPrestation, self.labelPrestation, self.IDprestationFrais)

class CTRL_Compte(wx.Choice):
    # Choix du Compte bancaire et des param�tres du d�p�t
    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1) 
        self.parent = parent
        self.IDdefaut = None
        self.MAJ()             
    
    def MAJ(self):
        listeItems = self.GetListeDonnees()
        if len(listeItems) == 0 :
            self.Enable(False)
        else:
            self.Enable(True)
        self.SetItems(listeItems)
        if self.IDdefaut != None :
            self.SetID(self.IDdefaut)
    
    def GetListeDonnees(self):
        self.dictDonnees = {}
        listeItems = []
        db = GestionDB.DB()
        req = """SELECT IDcompte, nom, numero, defaut
        FROM comptes_bancaires
        ORDER BY nom;"""
        db.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = db.ResultatReq()
        db.Close()
        index = 0
        for IDcompte, nom, numero, defaut in listeDonnees :
            self.dictDonnees[index] = { "ID" : IDcompte }
            listeItems.append(nom)
            if defaut == 1 :
                self.IDdefaut = IDcompte
            index += 1
        return listeItems

    def SetID(self, ID=0):
        for index, values in self.dictDonnees.items():
            if values["ID"] == ID :
                 self.SetSelection(index)

    def GetID(self):
        index = self.GetSelection()
        if index == -1 : return None
        return self.dictDonnees[index]["ID"]

# ----------------------------------------------------------------------------------------

class Dialog(wx.Dialog):
    def __init__(self, parent, IDcompte_payeur=None, IDreglement=None):
        wx.Dialog.__init__(self, parent, -1, name="DLG_Emetteurs", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.IDcompte_payeur = IDcompte_payeur
        self.IDreglement = IDreglement
        self.dernierRecu = None
        self.avis_depot = None
        self.lstModifs = []


        if "linux" in sys.platform :
            defaultFont = self.GetFont()
            defaultFont.SetPointSize(8)
            self.SetFont(defaultFont)

        if self.IDreglement != None :
            DB = GestionDB.DB()
            
            # Recherche du IDcompte_payeur si on vient pas de la fiche famille
            req = """SELECT IDcompte_payeur
            FROM reglements
            WHERE IDreglement=%d
            """ % self.IDreglement
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            listeDonnees = DB.ResultatReq()
            self.IDcompte_payeur = listeDonnees[0][0]
            
            # Recherche si re�u �dit�
            req = """SELECT numero, date_edition, IDutilisateur
            FROM recus
            WHERE IDreglement=%d
            ORDER BY date_edition""" % self.IDreglement
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            listeDonnees = DB.ResultatReq()
            if len(listeDonnees) > 0 :
                numero, date_edition, IDutilisateur = listeDonnees[-1]
                self.dernierRecu = {"numero" : numero, "date_edition" : date_edition, "IDutilisateur" : IDutilisateur}

            DB.Close()
        
        self.date_saisie = datetime.date.today()
        self.IDutilisateur = UTILS_Identification.GetIDutilisateur()
        self.IDdepot = None
        self.compta = None
        
        # Bandeau
        if self.IDreglement == None:
            regl = _("Ajout d'un r�glement")
        else:
            regl =  _("Saisie du r�glement ID : %s")%str(self.IDreglement)
        intro = _("Vous pouvez ici saisir un r�glement pour une famille. Commencez par saisir la date, s�lectionnez le mode de r�glement et si besoin l'�metteur associ�, saisissez le num�ro de pi�ce (si ch�que) puis le montant et s�lectionnez un nom de payeur. Enfin, vous devez obligatoirement ventiler le r�glement sur les diff�rentes prestations disponibles ci-dessous.")
        titre =regl
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/22x22/Smiley_nul.png")
        
        # Infos
        self.staticbox_infos_staticbox = wx.StaticBox(self, -1, _("Informations"))
##        self.panel_infos = wx.Panel(self, -1, style=wx.TAB_TRAVERSAL)
##        self.panel_infos.SetBackgroundColour("#F0FBED")
        self.ctrl_image = CTRL_Image(self, style=wx.SUNKEN_BORDER)
        self.ctrl_infos = CTRL_Infos(self, couleurFond="#FFFFFF", style=wx.SUNKEN_BORDER ) #F0FBED
        
        # G�n�ralit�s
        self.staticbox_generalites_staticbox = wx.StaticBox(self, -1, _("G�n�ralites"))
        self.label_date = wx.StaticText(self, -1, _("Date :"))
        self.ctrl_date = CTRL_Saisie_date.Date(self)
        self.ctrl_date.SetDate(datetime.date.today())
        self.label_mode = wx.StaticText(self, -1, _("Mode :"))
        self.ctrl_mode = CTRL_Mode(self)
        self.label_emetteur = wx.StaticText(self, -1, _("Emetteur :"))
        self.ctrl_emetteur = CTRL_Emetteur(self)
        self.label_numero = wx.StaticText(self, -1, _("N� Pi�ce :"))
        self.ctrl_numero = wx.TextCtrl(self, -1, "")
        self.label_montant = wx.StaticText(self, -1, _("Montant :"))
        font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.BOLD, 0, "")
        self.ctrl_montant = CTRL_Saisie_euros.CTRL(self, font)
        self.label_payeur = wx.StaticText(self, -1, _("Payeur :"))
        self.ctrl_payeur = CTRL_Payeurs(self, self.IDcompte_payeur)
        self.bouton_ajouter_payeur = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_modifier_payeur = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_supprimer_payeur = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_ANY))
        
        self.bouton_calendrier = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Calendrier.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_mode = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Mecanisme.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_emetteur = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Mecanisme.png"), wx.BITMAP_TYPE_ANY))

        # Options
        self.staticbox_options_staticbox = wx.StaticBox(self, -1, _("Options"))
        self.label_observations = wx.StaticText(self, -1, _("Observations :"))
        self.ctrl_observations = wx.TextCtrl(self, -1, "", style=wx.TE_MULTILINE)
        self.label_quittancier = wx.StaticText(self, -1, _("N� Quittancier :"))
        self.ctrl_quittancier = wx.TextCtrl(self, -1, "")
        self.label_recu = wx.StaticText(self, -1, _("Edition re�u :"))
        self.ctrl_recu = wx.CheckBox(self, -1, "")
        self.label_frais = wx.StaticText(self, -1, _("Frais de gestion :"))
        self.hyperlien_frais = CTRL_Frais(self, label=_("Aucun frais"), infobulle=_("Cliquez ici pour appliquer des frais de gestion"), URL="")
        
        # Encaissement
        self.staticbox_encaissement_staticbox = wx.StaticBox(self, -1, _("Encaissement"))
        self.label_compte = wx.StaticText(self, -1, _("Compte :"))
        self.ctrl_compte = CTRL_Compte(self)
        self.label_differe = wx.StaticText(self, -1, _("Diff�r� :"))
        self.ctrl_check_differe = wx.CheckBox(self, -1, "")
        self.label_differe_2 = wx.StaticText(self, -1, _("A partir du"))
        self.ctrl_differe = CTRL_Saisie_date.Date(self)
        self.label_attente = wx.StaticText(self, -1, _("Attente :"))
        self.ctrl_attente = wx.CheckBox(self, -1, "")
        
        self.bouton_calendrier_differe = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Calendrier.png"), wx.BITMAP_TYPE_ANY))

        # Ventilation
        self.staticbox_ventilation_staticbox = wx.StaticBox(self, -1, _("Ventilation"))
        self.ctrl_ventilation = CTRL_Ventilation.CTRL(self, IDcompte_payeur=self.IDcompte_payeur, IDreglement=self.IDreglement)
        
        # Commandes
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png"))
        self.bouton_options = CTRL_Bouton_image.CTRL(self, texte=_("Options"), cheminImage=Chemins.GetStaticPath("Images/32x32/Configuration2.png"))
        self.bouton_calculatrice = CTRL_Bouton_image.CTRL(self, texte=_("Calculatrice"), cheminImage=Chemins.GetStaticPath("Images/32x32/Calculatrice.png"))
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ok"), cheminImage=Chemins.GetStaticPath("Images/32x32/Valider.png"))
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Annuler"), cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png"))

        self.__set_properties()
        self.__do_layout()
        
        self.Bind(wx.EVT_CHOICE, self.OnChoixEmetteur, self.ctrl_emetteur)
        self.Bind(wx.EVT_CHOICE, self.OnChoixMode, self.ctrl_mode)
        self.Bind(wx.EVT_CHOICE, self.OnChoixCompte, self.ctrl_compte)
        self.ctrl_date.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocusDate)
        self.bouton_calendrier.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocusDate)

        self.ctrl_numero.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocusNumero)
        self.ctrl_montant.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocusMontant)
        self.ctrl_montant.Bind(wx.EVT_TEXT, self.OnTextMontant)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonCalendrier, self.bouton_calendrier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonMode, self.bouton_mode)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonEmetteur, self.bouton_emetteur)
        self.Bind(wx.EVT_BUTTON, self.OnAjouterPayeur, self.bouton_ajouter_payeur)
        self.Bind(wx.EVT_BUTTON, self.OnModifierPayeur, self.bouton_modifier_payeur)
        self.Bind(wx.EVT_BUTTON, self.OnSupprimerPayeur, self.bouton_supprimer_payeur)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckDiffere, self.ctrl_check_differe)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonCalendrierDiffere, self.bouton_calendrier_differe)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOptions, self.bouton_options)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonCalculatrice, self.bouton_calculatrice)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        
        # R�cup�ration du nom des titulaires
        try :
            dictTitulaires = UTILS_Titulaires.GetTitulaires(listeIDfamille=[self.IDcompte_payeur,])
            nomsTitulaires = dictTitulaires[self.IDcompte_payeur]["titulairesSansCivilite"]
        except :
            nomsTitulaires = None
        
        # Importation des donn�es
        if nomsTitulaires != None and nomsTitulaires != "" :
            titreFamille = _("pour la famille de %s") % nomsTitulaires
        else:
            titreFamille = ""
        if self.IDreglement != None :
            self.Importation() 
            self.SetTitle(_("DLG_Saisie_reglement : Saisie d'un r�glement de %s") % titreFamille)
        else:
            self.SetTitle(_("DLG_Saisie_reglement : Modification d'un r�glement de  %s") % titreFamille)
            
        # Initialisation des contr�les
        self.OnCheckDiffere(None)
        self.MAJinfos() 
        self.ctrl_ventilation.MAJ()
        
        if self.IDreglement == None :
            self.OnChoixMode(None)
            # Importe les derni�res valeurs
            self.ImportationDernierReglement() 

        # Verrouillage Depot
        self.VerrouillageDepot()
        
        # Param�tres
        self.ctrl_ventilation.ctrl_ventilation.bloquer_ventilation = UTILS_Config.GetParametre("ventilation_bloquer", True)
        
        # Focus
        self.ctrl_date.SetFocus() 
        wx.CallAfter(self.ctrl_date.SetInsertionPoint, 0)

    def __set_properties(self):
        self.ctrl_date.SetToolTip(_("Saisissez la date d'�mission du r�glement"))
        self.ctrl_mode.SetToolTip(_("S�lectionnez le mode de r�glement"))
        self.ctrl_emetteur.SetToolTip(_("S�lectionnez l'�metteur du r�glement (banque ou organisme)"))
        self.ctrl_numero.SetToolTip(_("Saisissez le num�ro de la pi�ce"))
        self.ctrl_montant.SetToolTip(_("Saisissez un montant en %s") % SYMBOLE)
        self.bouton_calendrier.SetToolTip(_("Cliquez ici pour s�lectionner la date dans un calendrier"))
        self.bouton_mode.SetToolTip(_("Cliquez ici pour ajouter, modifier ou supprimer un mode de r�glement"))
        self.bouton_emetteur.SetToolTip(_("Cliquez ici pour ajouter, modifier ou supprimer un �metteur de r�glement"))
        self.ctrl_attente.SetToolTip(_("Cochez cette case si vous souhaitez laisser l'encaissement en attente"))
        self.ctrl_compte.SetToolTip(_("S�lectionner le compte bancaire sur lequel encaisser ce r�glement"))
        self.ctrl_observations.SetToolTip(_("Saisissez ici les observations de votre choix"))
        self.ctrl_quittancier.SetToolTip(_("Saisissez ici le num�ro de quittancier si vous en utilisez un"))
        self.ctrl_recu.SetToolTip(_("Cochez cette case si vous souhaitez �diter un re�u pour ce r�glement juste apr�s la validation de celui-ci"))
        self.bouton_ajouter_payeur.SetToolTip(_("Cliquez ici pour ajouter un payeur"))
        self.bouton_modifier_payeur.SetToolTip(_("Cliquez ici pour modifier le payeur s�lectionn�"))
        self.bouton_supprimer_payeur.SetToolTip(_("Cliquez ici pour supprimer le payeur s�lectionn�"))
        self.ctrl_check_differe.SetToolTip(_("Cochez cette case pour pr�ciser une date d'encaissement ult�rieure"))
        self.bouton_calendrier_differe.SetToolTip(_("Cliquez ici pour s�lectionner une date d'encaissement diff�r� dans un calendrier"))
        self.bouton_options.SetToolTip(_("Cliquez ici pour acc�der aux options"))
        self.bouton_aide.SetToolTip(_("Cliquez ici pour obtenir de l'aide"))
        self.bouton_calculatrice.SetToolTip(_("Cliquez ici pour ouvrir la calculatrice install�e par d�faut sur votre ordinateur"))
        self.bouton_ok.SetToolTip(_("Cliquez ici pour valider"))
        self.bouton_annuler.SetToolTip(_("Cliquez ici pour annuler"))
        self.ctrl_differe.SetToolTip(_("Saisissez ici la date d'encaissement souhait�e"))
        self.ctrl_mode.SetMinSize((200, -1))
        self.ctrl_montant.SetMinSize((-1, 30))
        self.ctrl_compte.SetMinSize((200, 21))
        self.SetMinSize((850, 730))
        
    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=10, hgap=10)
        
        # Bandeau
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)
        
        grid_sizer_haut = wx.FlexGridSizer(rows=1, cols=3, vgap=10, hgap=10)
        grid_sizer_haut_droit = wx.FlexGridSizer(rows=2, cols=1, vgap=10, hgap=10)
        
        # Infos
        staticbox_infos = wx.StaticBoxSizer(self.staticbox_infos_staticbox, wx.VERTICAL)
        grid_sizer_infos = wx.FlexGridSizer(rows=2, cols=1, vgap=0, hgap=0)
        grid_sizer_infos.Add(self.ctrl_image, 0, wx.ALL, 5)
        grid_sizer_infos.Add(self.ctrl_infos, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.TOP|wx.EXPAND, 5)
##        self.panel_infos.SetSizer(grid_sizer_infos)
        grid_sizer_infos.AddGrowableRow(1)
        staticbox_infos.Add(grid_sizer_infos, 1, wx.ALL|wx.EXPAND, 0)
        grid_sizer_haut.Add(staticbox_infos, 1, wx.EXPAND, 0)
        
        # G�n�ralit�s
        staticbox_generalites = wx.StaticBoxSizer(self.staticbox_generalites_staticbox, wx.VERTICAL)
        grid_sizer_generalites = wx.FlexGridSizer(rows=6, cols=2, vgap=5, hgap=5)
        grid_sizer_generalites.Add(self.label_date, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        
        # Date
        grid_sizer_date = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_date.Add(self.ctrl_date, 0, wx.EXPAND, 0)
        grid_sizer_date.Add(self.bouton_calendrier, 0, 0, 0)
        grid_sizer_generalites.Add(grid_sizer_date, 1, wx.EXPAND, 0)
        grid_sizer_generalites.Add(self.label_mode, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        
        # Mode
        grid_sizer_mode = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_mode.Add(self.ctrl_mode, 0, wx.EXPAND, 0)
        grid_sizer_mode.Add(self.bouton_mode, 0, 0, 0)
        grid_sizer_mode.AddGrowableCol(0)
        grid_sizer_generalites.Add(grid_sizer_mode, 1, wx.EXPAND, 0)
        grid_sizer_generalites.Add(self.label_emetteur, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        
        # Emetteur
        grid_sizer_emetteur = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_emetteur.Add(self.ctrl_emetteur, 0, wx.EXPAND, 0)
        grid_sizer_emetteur.Add(self.bouton_emetteur, 0, 0, 0)
        grid_sizer_emetteur.AddGrowableCol(0)
        grid_sizer_generalites.Add(grid_sizer_emetteur, 1, wx.EXPAND, 0)
        
        # Num�ro
        grid_sizer_generalites.Add(self.label_numero, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_generalites.Add(self.ctrl_numero, 0, 0, 0)
        
        # Montant
        grid_sizer_generalites.Add(self.label_montant, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_generalites.Add(self.ctrl_montant, 0, 0, 0)
        grid_sizer_generalites.Add(self.label_payeur, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        
        # Payeurs
        grid_sizer_payeur = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_boutons_payeurs = wx.FlexGridSizer(rows=3, cols=1, vgap=5, hgap=5)
        grid_sizer_payeur.Add(self.ctrl_payeur, 0, wx.EXPAND, 0)
        grid_sizer_boutons_payeurs.Add(self.bouton_ajouter_payeur, 0, 0, 0)
        grid_sizer_boutons_payeurs.Add(self.bouton_modifier_payeur, 0, 0, 0)
        grid_sizer_boutons_payeurs.Add(self.bouton_supprimer_payeur, 0, 0, 0)
        grid_sizer_payeur.Add(grid_sizer_boutons_payeurs, 1, wx.EXPAND, 0)
        grid_sizer_payeur.AddGrowableCol(0)
        grid_sizer_generalites.Add(grid_sizer_payeur, 1, wx.EXPAND, 0)
        
        grid_sizer_generalites.AddGrowableCol(1)
        staticbox_generalites.Add(grid_sizer_generalites, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_haut.Add(staticbox_generalites, 1, wx.EXPAND, 0)
        
        # Options
        staticbox_options = wx.StaticBoxSizer(self.staticbox_options_staticbox, wx.VERTICAL)
        grid_sizer_options = wx.FlexGridSizer(rows=4, cols=2, vgap=5, hgap=5)
        grid_sizer_options.Add(self.label_observations, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_options.Add(self.ctrl_observations, 0, wx.EXPAND, 0)
        grid_sizer_options.Add(self.label_quittancier, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_options.Add(self.ctrl_quittancier, 0, wx.EXPAND, 0)
        grid_sizer_options.Add(self.label_recu, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_options.Add(self.ctrl_recu, 0, 0, 0)
        grid_sizer_options.Add(self.label_frais, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        
        # Frais
        grid_sizer_frais = wx.FlexGridSizer(rows=1, cols=3, vgap=5, hgap=5)
        grid_sizer_frais.Add(self.hyperlien_frais, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_options.Add(grid_sizer_frais, 1, wx.EXPAND, 0)
        grid_sizer_options.AddGrowableRow(0)
        grid_sizer_options.AddGrowableCol(1)
        staticbox_options.Add(grid_sizer_options, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_haut_droit.Add(staticbox_options, 1, wx.EXPAND, 0)
        
        # Encaissement
        staticbox_encaissement = wx.StaticBoxSizer(self.staticbox_encaissement_staticbox, wx.VERTICAL)
        grid_sizer_encaissement = wx.FlexGridSizer(rows=3, cols=2, vgap=5, hgap=5)
        grid_sizer_encaissement.Add(self.label_compte, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_encaissement.Add(self.ctrl_compte, 0, wx.EXPAND, 0)
        grid_sizer_encaissement.Add(self.label_differe, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        
        grid_sizer_differe = wx.FlexGridSizer(rows=1, cols=4, vgap=5, hgap=5)
        grid_sizer_differe.Add(self.ctrl_check_differe, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_differe.Add(self.label_differe_2, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_differe.Add(self.ctrl_differe, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_differe.Add(self.bouton_calendrier_differe, 0, 0, 0)
        grid_sizer_encaissement.Add(grid_sizer_differe, 0, 0, 0)
        
        grid_sizer_encaissement.Add(self.label_attente, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_encaissement.Add(self.ctrl_attente, 0, 0, 0)
        grid_sizer_encaissement.AddGrowableCol(1)
        staticbox_encaissement.Add(grid_sizer_encaissement, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_haut_droit.Add(staticbox_encaissement, 1, wx.EXPAND, 0)
        grid_sizer_haut_droit.AddGrowableRow(0)
        
        grid_sizer_haut.Add(grid_sizer_haut_droit, 1, wx.EXPAND, 0)
        grid_sizer_haut.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_haut, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        # Ventilation
        staticbox_ventilation = wx.StaticBoxSizer(self.staticbox_ventilation_staticbox, wx.VERTICAL)
        grid_sizer_ventilation = wx.FlexGridSizer(rows=2, cols=2, vgap=10, hgap=10)
        grid_sizer_ventilation.Add(self.ctrl_ventilation, 0, wx.EXPAND, 0)
        grid_sizer_ventilation.AddGrowableRow(0)
        grid_sizer_ventilation.AddGrowableCol(0)
        staticbox_ventilation.Add(grid_sizer_ventilation, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_base.Add(staticbox_ventilation, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=7, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_options, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_calculatrice, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(3)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(2)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        
        # D�termine la taille de la fen�tre
        taille_fenetre = UTILS_Config.GetParametre("taille_fenetre_reglement")
        if taille_fenetre == None or taille_fenetre[0] == None:
            self.SetSize((840, 700))
        elif taille_fenetre == (0, 0) :
            self.Maximize(True)
        else:
            self.SetSize(taille_fenetre)        
        self.CenterOnScreen() 
        
        wx.CallLater(0, self.Layout) # Contre pb d'affichage du wx.Choice
    
    def VerrouillageDepot(self):
        parent = self.GetParent().GetName()
        origineDepot = parent == "OL_Reglements_depots"
        if origineDepot and self.compta == None:
            return

        if self.IDdepot != None or self.compta != None :
            if self.compta != None:
                mess = "Ce r�glement est transf�r� en compta, les possibilit�s de modification sont limit�es"
            else:
                mess = "Ce r�glement ayant fait l'objet d'un d�p�t, vous devez le sortir du d�p�t pour une modification compl�te"

            dlg = wx.MessageDialog(self, mess , _("Modification limit�e"), wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_date.Enable(False)
            self.ctrl_mode.Enable(False)
            #self.ctrl_emetteur.Enable(False)
            #self.ctrl_numero.Enable(False)
            self.ctrl_montant.Enable(False)
            #self.ctrl_payeur.Enable(False)
            self.bouton_ajouter_payeur.Enable(False)
            self.bouton_modifier_payeur.Enable(False)
            self.bouton_supprimer_payeur.Enable(False)
            self.bouton_calendrier.Enable(False)
            self.bouton_mode.Enable(False)
            self.bouton_emetteur.Enable(False)
            #self.ctrl_compte.Enable(False)
            self.ctrl_check_differe.Enable(False)
            self.ctrl_differe.Enable(False)
            #self.ctrl_attente.Enable(False)
            self.bouton_calendrier_differe.Enable(False)

    def MAJinfos(self):
        texte = ""
        # IDr�glement
        if self.IDreglement != None :
            texte += _("R�glement n�%d<BR>") % self.IDreglement
        else:
            DB = GestionDB.DB()
            prochainID = DB.GetProchainID("reglements")
            DB.Close()
            if prochainID != None :
                texte += _("R�glement n�%d<BR>") % prochainID
        # Date saisie
        texte += _("Saisi le %s<BR>") % DateEngFr(str(self.date_saisie))
        # Nom Utilisateur
        if self.IDutilisateur != None :
            dictUtilisateur = UTILS_Identification.GetAutreDictUtilisateur(self.IDutilisateur)
            if dictUtilisateur != None :
                nomUtilisateur = "%s %s" % (dictUtilisateur["nom"], dictUtilisateur["prenom"])
            else:
                nomUtilisateur = "n�%d" % self.IDutilisateur
        else:
            nomUtilisateur = _("Utilisateur inconnu")
        texte += _("Par l'utilisateur %s<BR>") % nomUtilisateur
        # Compte payeur
        texte += _("Compte payeur n�%d<BR>") % self.IDcompte_payeur
        # D�p�t
        if self.IDdepot != None :
            texte += _("D�p�t n�%d<BR>") % self.IDdepot
        else :
            texte += _("Non d�pos�<BR>")
        # Dernier re�u
        if self.dernierRecu == None :
            texte += _("Aucun re�u �dit�<BR>")
        else :
            numero = self.dernierRecu["numero"]
            date_edition = DateEngFr(str(self.dernierRecu["date_edition"]))
            if self.IDutilisateur != None :
                dictUtilisateur = UTILS_Identification.GetAutreDictUtilisateur(self.dernierRecu["IDutilisateur"])
                if dictUtilisateur != None :
                    nomUtilisateur = "%s %s" % (dictUtilisateur["nom"], dictUtilisateur["prenom"])
                else:
                    nomUtilisateur = "n�%d" % self.IDutilisateur
            else:
                nomUtilisateur = _("Utilisateur inconnu")
            texte += _("Re�u n�%s �dit� le %s par %s<BR>") % (numero, date_edition, nomUtilisateur)
        # Avis de d�p�t
        if self.avis_depot != None :
            texte += _("Avis de d�p�t envoy� par Email le %s<BR>") % DateEngFr(str(self.avis_depot))
            
        self.ctrl_infos.SetLabel(texte)

    def StockeCompteDefault(self,dicInfo, IDcompte):
        mess = "Ce choix est-il habituel pour les '%s'?" % dicInfo["label"]
        mess += "\n\nSi cette banque est la destination normale pour ce mode de r�glement,"
        mess += "nous allons l'enregistrer pour le proposer la prochaine fois.\n"
        mess += "Il est toujours possible de revenir sur la valeur propos�e par la gestion des modes de r�glements."
        dlg = wx.MessageDialog(self,mess,"Choix du compte bancaire",style=wx.YES_NO|wx.ICON_EXCLAMATION)
        ret = dlg.ShowModal()
        if ret != wx.ID_YES:
            return
        DB = GestionDB.DB()
        listeDonnees = [("IDcompte", IDcompte),]
        mess = "DLG_Saisie_reglements.StockeCompteDefault"
        ret = DB.ReqMAJ("modes_reglements", listeDonnees, "IDmode", dicInfo["ID"],MsgBox=mess)
        if ret == "ok":
            dicInfo["IDcompte"] = IDcompte
        DB.Close()

    def OnChoixMode(self, event):
        IDmode = self.ctrl_mode.GetID()
        self.ctrl_emetteur.MAJ(IDmode)
        self.ctrl_image.SetPhotoMode(IDmode)
        self.FormateNumPiece() 
        self.SetFraisGestion()
        dicInfos = self.ctrl_mode.GetInfosMode()
        if dicInfos and "IDcompte" in dicInfos:
            IDcompte = self.ctrl_mode.GetInfosMode()["IDcompte"]
            if IDcompte:
                self.ctrl_compte.SetID(IDcompte)

    def OnChoixEmetteur(self, event): 
        IDemetteur = self.ctrl_emetteur.GetID()
        self.ctrl_image.SetPhotoEmetteur(IDemetteur)
        
    def OnBoutonCalendrier(self, event): 
        from Dlg import DLG_calendrier_simple
        dlg = DLG_calendrier_simple.Dialog(self)
        if dlg.ShowModal() == wx.ID_OK :
            date = dlg.GetDate()
            self.ctrl_date.SetDate(date)
        dlg.Destroy()

    def OnBoutonMode(self, event): 
        IDmode = self.ctrl_mode.GetID()
        from Dlg import DLG_Modes_reglements
        dlg = DLG_Modes_reglements.Dialog(self)
        dlg.ShowModal()
        dlg.Destroy()
        self.ctrl_mode.MAJ()
        self.ctrl_mode.SetID(IDmode)
        self.OnChoixMode(None)

    def OnChoixCompte(self,event):
        # Stocke l'ID compte bancaire dans le champ par d�faut du mode de r�glement
        dicInfo = self.ctrl_mode.GetInfosMode()
        IDcompte = self.ctrl_compte.GetID()
        if dicInfo["IDcompte"] != IDcompte:
            self.StockeCompteDefault(dicInfo,IDcompte)

    def OnBoutonEmetteur(self, event): 
        IDemetteur = self.ctrl_emetteur.GetID()
        IDmode = self.ctrl_mode.GetID()
        from Dlg import DLG_Emetteurs
        dlg = DLG_Emetteurs.Dialog(self)
        dlg.SelectMode(IDmode)
        dlg.ShowModal()
        dlg.Destroy()
        self.ctrl_emetteur.MAJ(IDmode)
        self.ctrl_emetteur.SetID(IDemetteur)
        self.OnChoixEmetteur(None)

    def OnKillFocusDate(self, event):
        # controle si saisie dans un exercice ouvert
        DB = GestionDB.DB()
        dateSaisie = DateFREnDateDD(self.ctrl_date.GetValue())
        exerciceDeb, exerciceFin = DB.GetExercice(dateSaisie,approche=False)
        if exerciceDeb != None and exerciceFin != None:
            #la date est dans un exercice
            pass
        else:
            if dateSaisie >= datetime.date.today():
                #on accepte les dates futures
                pass
            else:
                self.ctrl_date.SetDate(datetime.date.today())
                self.Refresh()
        DB.Close()

    def OnKillFocusNumero(self, event):
        self.FormateNumPiece() 
        event.Skip()

    def OnKillFocusMontant(self, event):
        montant = self.ctrl_montant.GetMontant()
        if montant == None :
            self.ctrl_montant.SetMontant(0.0)
        # MAJ des frais de gestion
        self.hyperlien_frais.MAJ() 
        # MAJ de la ventilation
        if montant != None :
            self.ctrl_ventilation.SetMontantReglement(montant)
        event.Skip()
    
    def OnTextMontant(self, event):
        montant = self.ctrl_montant.GetMontant()
        self.hyperlien_frais.MAJ() 
        self.ctrl_ventilation.SetMontantReglement(montant)
##        self.ctrl_ventilation.Show(montant >= 0.0)
        event.Skip()
        
    def FormateNumPiece(self):
        """ Formate le num�ro de pi�ce en fonction du param�trage du mode de r�glement """
        dictInfosMode = self.ctrl_mode.GetInfosMode()
        if dictInfosMode == None : return
        numero_piece = dictInfosMode["numero_piece"]
        nbre_chiffres = dictInfosMode["nbre_chiffres"]
        # Si aucun num�ro de pi�ce
        if numero_piece == None : 
            self.ctrl_numero.Enable(False)
        # Si alphanum�rique :
        if numero_piece == "ALPHA" :
            self.ctrl_numero.Enable(True)
        # Si num�rique
        if numero_piece == "NUM" :
            self.ctrl_numero.Enable(True)
            if nbre_chiffres != None:
                try :
                    numeroInt = int(self.ctrl_numero.GetValue())
                    fmt = "{:0%dd}"%nbre_chiffres
                    numeroStr = fmt.format(numeroInt)
                    self.ctrl_numero.SetValue(numeroStr)
                except :
                    pass

    def SetFraisGestion(self):
        # R�cup�ration des infos par d�faut du r�glement
        dictInfosMode = self.ctrl_mode.GetInfosMode()
        if dictInfosMode == None : return
        dictFrais = {  
            "frais_gestion" : dictInfosMode["frais_gestion"],
            "frais_montant" : dictInfosMode["frais_montant"],
            "frais_pourcentage" : dictInfosMode["frais_pourcentage"],
            "frais_arrondi" : dictInfosMode["frais_arrondi"],
            "frais_label" : dictInfosMode["frais_label"],
            }
        self.hyperlien_frais.SetDictFrais(dictFrais)

    def OnAjouterPayeur(self, event): 
        self.ctrl_payeur.Ajouter()

    def OnModifierPayeur(self, event): 
        self.ctrl_payeur.Modifier()

    def OnSupprimerPayeur(self, event): 
        self.ctrl_payeur.Supprimer()
        
    def OnCheckDiffere(self, event): 
        if self.ctrl_check_differe.GetValue() == True and self.IDdepot == None :
            etat = True
        else:
            etat = False
        self.label_differe_2.Enable(etat) 
        self.ctrl_differe.Enable(etat) 
        self.bouton_calendrier_differe.Enable(etat) 
        if etat == True :
            self.ctrl_differe.SetFocus()
            self.ctrl_differe.SetInsertionPoint(0)

    def OnBoutonCalendrierDiffere(self, event): 
        from Dlg import DLG_calendrier_simple
        dlg = DLG_calendrier_simple.Dialog(self)
        if dlg.ShowModal() == wx.ID_OK :
            date = dlg.GetDate()
            self.ctrl_differe.SetDate(date)
        dlg.Destroy()

    def OnBoutonAide(self, event): 
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Rglements1")

    def OnBoutonOptions(self, event):
        # Cr�ation du menu Options
        menuPop = wx.Menu()
    
        item = wx.MenuItem(menuPop, ID_OPTION_BLOQUER_VENTILATION, _("Bloquer la ventilation lorsque le cr�dit est �puis�"), _("Bloquer la ventilation lorsque le cr�dit est �puis�"), wx.ITEM_CHECK)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.On_option_bloquer_ventilation, id=ID_OPTION_BLOQUER_VENTILATION)
        if self.ctrl_ventilation.ctrl_ventilation.bloquer_ventilation == True : item.Check(True)
        
        self.PopupMenu(menuPop)
        menuPop.Destroy()
    
    def On_option_bloquer_ventilation(self, event):
        self.ctrl_ventilation.ctrl_ventilation.bloquer_ventilation = not self.ctrl_ventilation.ctrl_ventilation.bloquer_ventilation
        
    def OnBoutonCalculatrice(self, event):
        FonctionsPerso.OuvrirCalculatrice() 
        
    def OnBoutonOk(self, event): 
        # Sauvegarde des donn�es
        valide = self.Sauvegarde()
        if valide == False :
            return
        
        # Recherche si la famille est abonn�e � l'envoi du re�u par Email
        email_envoye = False
        DB = GestionDB.DB()
        req = """SELECT familles.IDfamille, email_recus 
        FROM familles 
        LEFT JOIN comptes_payeurs ON comptes_payeurs.IDfamille = familles.IDfamille
        WHERE comptes_payeurs.IDcompte_payeur=%d;""" % self.IDcompte_payeur
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        IDfamille, email_recus = listeDonnees[0]
        if email_recus != None and self.nouveauReglement == True :

            dlg = wx.MessageDialog(None, _("Cette famille est abonn�e au service d'envoi automatique des re�us de r�glements par Email. \n\nConfirmez-vous l'envoi direct du re�u maintenant ?\n\nOUI = Envoi direct \nNON = Acc�der aux param�tres d'envoi \nANNULER = Ne pas envoyer"), _("Envoi du re�u par Email"), wx.YES_NO|wx.YES_DEFAULT|wx.CANCEL|wx.ICON_EXCLAMATION)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse != wx.ID_CANCEL :
                
                # Recherche de l'adresse d'envoi
                DB = GestionDB.DB()
                req = """SELECT individus.IDindividu, mail, travail_mail
                FROM individus
                LEFT JOIN rattachements ON rattachements.IDindividu = individus.IDindividu
                WHERE rattachements.IDfamille=%d;""" % IDfamille
                DB.ExecuterReq(req,MsgBox="ExecuterReq")
                listeAdressesIndividus = DB.ResultatReq()
                DB.Close() 
                dictAdressesIndividus = {}
                for IDindividu, mail, travail_mail in listeAdressesIndividus :
                    dictAdressesIndividus[IDindividu] = {"perso" : mail, "travail" : travail_mail}
            
                IDindividu, categorie, adresse = email_recus.split(";")
                if IDindividu != "" :
                    try :
                        if int(IDindividu) in dictAdressesIndividus :
                            adresse = dictAdressesIndividus[int(IDindividu)][categorie]
                    except :
                        pass
                
                if adresse == None :
                    dlg = wx.MessageDialog(self, _("L'adresse Email enregistr�e ne semble pas valide. Renseignez une nouvelle adresse valide pour cette famille..."), _("Erreur d'adresse Email"), wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    return False
                
                else :
                    
                    # Ouverture du Mailer
                    from Dlg import DLG_Impression_recu
                    dlg1 = DLG_Impression_recu.Dialog(self, IDreglement=self.IDreglement) 
                    dlg1.listeAdresses = [adresse,]
                    
                    if reponse == wx.ID_NO :
                        # Acc�s aux param�tres
                        dlg1.ShowModal() 
                        dlg1.Destroy() 
                    
                    if reponse == wx.ID_YES :
                        # Envoi direct

                        nomDoc="RECU%s.pdf" % FonctionsPerso.GenerationIDdoc()
                        from Utils import UTILS_Fichiers
                        nomDoc = UTILS_Fichiers.GetRepTemp(nomDoc)
                        categorie="recu_reglement"
                        dictChamps = dlg1.CreationPDF(nomDoc=nomDoc, afficherDoc=False)
                        if dictChamps == False :
                            dlg1.Destroy()
                            return False
                        
                        listeDonnees = [{"adresse" : adresse, "pieces" : [nomDoc,], "champs" : dictChamps,}]
                        from Dlg import DLG_Mailer
                        dlg2 = DLG_Mailer.Dialog(self, categorie=categorie, afficher_confirmation_envoi=False)
                        dlg2.SetDonnees(listeDonnees, modificationAutorisee=False)
                        dlg2.ChargerModeleDefaut()
                        dlg2.OnBoutonEnvoyer(None) 
                        if len(dlg2.listeAnomalies) == 0 :
                            succes = True
                        else :
                            succes = False
                        dlg2.Destroy()
                        
                        try :
                            os.remove(nomDoc)     
                        except :
                            pass
                        
                        # M�morisation de l'�dition du re�u
                        if succes == True :
                            dlg1.Sauvegarder(demander=False)
                        dlg1.Destroy() 

        # M�morisation du param�tre de la taille d'�cran
        UTILS_Config.SetParametre("ventilation_bloquer", self.ctrl_ventilation.ctrl_ventilation.bloquer_ventilation)

        # Edition d'un re�u
        if self.ctrl_recu.GetValue() == True and email_envoye == False :
            from Dlg import DLG_Impression_recu
            dlg = DLG_Impression_recu.Dialog(self, IDreglement=self.IDreglement) 
            dlg.ShowModal()
            dlg.Destroy()
            
        # Fermeture
        self.EndModal(wx.ID_OK)

    def OnBoutonAnnuler(self, event): 
        self.EndModal(wx.ID_CANCEL)
    
    def Importation(self):
        DB = GestionDB.DB()
        req = """SELECT 
        IDcompte_payeur, date, IDmode, IDemetteur, numero_piece, montant, IDpayeur,
        observations, numero_quittancier, IDprestation_frais, IDcompte, date_differe, 
        encaissement_attente, IDdepot, date_saisie, IDutilisateur, avis_depot, compta
        FROM reglements
        WHERE IDreglement=%d;
        """ % self.IDreglement
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        if len(listeDonnees) == 0 : 
            DB.Close()
            return
        
        IDcompte_payeur, date, IDmode, IDemetteur, numero_piece, montant, IDpayeur, observations, numero_quittancier, IDprestation_frais, IDcompte, date_differe, encaissement_attente, IDdepot, date_saisie, IDutilisateur, avis_depot, compta = listeDonnees[0]
        
        # G�n�ralit�s
        self.ctrl_date.SetDate(date)
        self.ctrl_mode.SetID(IDmode)
        self.OnChoixMode(None)
        if self.ctrl_emetteur.IsEnabled() == True :
            self.ctrl_emetteur.SetID(IDemetteur)
            self.OnChoixEmetteur(None)
        if numero_piece != None :
            self.ctrl_numero.SetValue(numero_piece)
        self.ctrl_montant.SetMontant(montant)
        self.ctrl_ventilation.SetMontantReglement(montant)
        self.ctrl_payeur.SetID(IDpayeur)
        self.avis_depot = avis_depot
        
        # Options
        if observations != None :
            self.ctrl_observations.SetValue(observations)
        if numero_quittancier != None :
            self.ctrl_quittancier.SetValue(numero_quittancier)
        
        # JE N'AI PAS PROGRAMME LA RECUP DE LA PRESTATION FRAIS DE GESTION !!!!!
        
        # Encaissement
        self.ctrl_compte.SetID(IDcompte)
        if date_differe != None :
            self.ctrl_differe.SetDate(date_differe)
            self.ctrl_check_differe.SetValue(True)
        if encaissement_attente == 1 :
            self.ctrl_attente.SetValue(True)
        if IDdepot != None or compta != None :
            #self.ctrl_compte.Enable(False)
            self.ctrl_check_differe.Enable(False)
            #self.ctrl_attente.Enable(False)
        
        # Autres
        self.date_saisie = DateEngEnDateDD(date_saisie)
        self.IDutilisateur = IDutilisateur
        self.IDdepot = IDdepot
        self.compta = compta

        # Frais de gestion
        req = """SELECT IDprestation, montant_initial, label
        FROM prestations
        WHERE reglement_frais=%d;
        """ % self.IDreglement
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if len(listeDonnees) > 0 : 
            IDprestationFrais, montant, labelPrestation = listeDonnees[0]
            self.hyperlien_frais.SetPrestationFrais(IDprestationFrais, montant, labelPrestation)
        else :
            self.hyperlien_frais.SetDictFrais({  
                    "frais_gestion" : None,
                    "frais_montant" : None,
                    "frais_pourcentage" : None,
                    "frais_arrondi" : None,
                    "frais_label" : None,
                    })

    def GetIDreglement(self):
        return self.IDreglement
    
    def Sauvegarde(self):
        # Date
        date = self.ctrl_date.GetDate()
        if date == None :
            dlg = wx.MessageDialog(self, _("Vous devez saisir une date d'�mission du r�glement correcte !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_date.SetFocus()
            return False
        
        # Mode
        IDmode = self.ctrl_mode.GetID()
        if IDmode == None :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement s�lectionner un mode de r�glement !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_mode.SetFocus()
            return False
        
        # Emetteur
        IDemetteur = self.ctrl_emetteur.GetID()
        if self.ctrl_emetteur.IsEnabled() and IDemetteur == None :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement s�lectionner un �metteur !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_emetteur.SetFocus()
            return False
        
        # Num�ro de pi�ce
        numero_piece = self.ctrl_numero.GetValue()
        if self.ctrl_numero.IsEnabled() :
            if numero_piece == "" :
                dlg = wx.MessageDialog(self, _("Etes-vous s�r de ne pas saisir de num�ro de pi�ce ?"), _("Confirmation"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
                reponse = dlg.ShowModal()
                dlg.Destroy()
                if reponse !=  wx.ID_YES :
                    return False
        else:
            numero_piece = ""
        
        # Montant modifi� JB
        montant = self.ctrl_montant.GetMontant()
        if self.ctrl_montant.Validation() == False :
            dlg = wx.MessageDialog(self, _("Le montant que vous avez saisi n'est pas valide !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_montant.SetFocus()
            return False

        # Payeur
        IDpayeur = self.ctrl_payeur.GetID() 
        if IDpayeur == None :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement s�lectionner un payeur dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_payeur.SetFocus()
            return False
        
        # Observations
        observations = self.ctrl_observations.GetValue()
        numero_quittancier = self.ctrl_quittancier.GetValue()
        
        # Compte d'encaissement
        IDcompte = self.ctrl_compte.GetID()
        if IDcompte == None :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement s�lectionner un compte bancaire dans la liste ! S'il n'y en aucun, vous devez en param�trer un � partir du menu Param�trage de la fen�tre d'accueil..."), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_compte.SetFocus()
            return False
        
        # Encaissement diff�r�
        date_differe = None
        if self.ctrl_check_differe.GetValue() == True :
            date_differe = self.ctrl_differe.GetDate()
            if date_differe == None :
                dlg = wx.MessageDialog(self, _("La date d'encaissement diff�r� n'est pas valide !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                self.ctrl_differe.SetFocus()
                return False
        
        # Attente d'encaissement
        encaissement_attente = 0
        if self.ctrl_attente.GetValue() == True :
            encaissement_attente = 1
        
        # Ventilation
        if self.ctrl_ventilation.Validation() == False :
            return False
        
        # Date de saisie
        date_saisie = self.date_saisie
        
        # Utilisateur
        IDutilisateur = self.IDutilisateur
        
        # R�cup�re IDfamille
        DB = GestionDB.DB()
        req = """SELECT IDfamille
        FROM comptes_payeurs
        WHERE IDcompte_payeur=%d
        """ % self.IDcompte_payeur
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        IDfamille = DB.ResultatReq()[0][0]

        # R�cup�re des frais de gestion
        donneesFrais = self.hyperlien_frais.GetDonnees() 
        if donneesFrais[0] != None and donneesFrais[0] != 0.0 :
            dlg = wx.MessageDialog(self, _("Confirmez-vous pour ce r�glement la facturation de frais de gestion d'un montant de %.2f %s ?") % (donneesFrais[0], SYMBOLE), _("Avertissement"), wx.YES_NO|wx.YES_DEFAULT|wx.CANCEL|wx.ICON_QUESTION)
            reponse = dlg.ShowModal() 
            dlg.Destroy()
            if reponse != wx.ID_YES :
                DB.Close()
                return False

        # --- Sauvegarde du r�glement ---
        listeDonnees = [    
                ("IDcompte_payeur", self.IDcompte_payeur),
                ("date", date),
                ("IDmode", IDmode),
                ("IDemetteur", IDemetteur),
                ("numero_piece", numero_piece),
                ("montant", montant),
                ("IDpayeur", IDpayeur),
                ("observations", observations),
                ("numero_quittancier", numero_quittancier),
                ("IDcompte", IDcompte),
                ("date_differe", date_differe),
                ("encaissement_attente", encaissement_attente),
                ("date_saisie", date_saisie),
                ("IDutilisateur", IDutilisateur),
            ]
        if self.IDreglement == None :
            self.nouveauReglement = True
            self.IDreglement = DB.ReqInsert("reglements", listeDonnees)
        else:
            self.nouveauReglement = False
            DB.ReqMAJ("reglements", listeDonnees, "IDreglement", self.IDreglement)
        self.lstModifs = listeDonnees
        
        # --- Sauvegarde de la ventilation ---
        self.ctrl_ventilation.Sauvegarde(self.IDreglement)
        
        # --- Sauvegarde les frais de gestion ---
        montantFrais, labelFrais, IDprestationFrais = donneesFrais
        
        # Si ajout d'un frais
        if montantFrais != None and montantFrais != 0.0 :
            listeDonnees = [    
                    ("IDcompte_payeur", self.IDcompte_payeur),
                    ("date", date),
                    ("categorie", "autre"),
                    ("label", labelFrais),
                    ("montant_initial", montantFrais),
                    ("montant", montantFrais),
                    ("IDfamille", IDfamille),
                    ("reglement_frais", self.IDreglement),
                ]
            if IDprestationFrais == None :
                IDprestationFrais = DB.ReqInsert("prestations", listeDonnees)
            else:
                DB.ReqMAJ("prestations", listeDonnees, "IDprestation", IDprestationFrais)
                DB.ReqDEL("ventilation", "IDprestation", IDprestationFrais)
        
        # Si suppression d'un frais
        if montantFrais == None and IDprestationFrais != None :
            DB.ReqDEL("prestations", "IDprestation", IDprestationFrais)
            DB.ReqDEL("ventilation", "IDprestation", IDprestationFrais)
        
        DB.Close() 
        
        # --- M�morise l'action dans l'historique ---
        if self.nouveauReglement == True :
            IDcategorie = 6
            categorie = _("Saisie")
        else:
            IDcategorie = 7
            categorie = "Modification"
        texteMode = self.ctrl_mode.GetStringSelection() 
        if IDemetteur != None :
            texteEmetteur = self.ctrl_emetteur.GetStringSelection() 
        else:
            texteEmetteur = ""
        if self.ctrl_numero.GetValue() != "" :
            texteNumpiece = " n�%s" % self.ctrl_numero.GetValue()
        else:
            texteNumpiece = ""
        if texteEmetteur == "" and texteNumpiece == "" :
            texteDetail = ""
        else:
            texteDetail = "- %s%s - " % (texteEmetteur, texteNumpiece)
        montant = "%.2f %s" % (self.ctrl_montant.GetMontant(), SYMBOLE)
        textePayeur = self.ctrl_payeur.GetStringSelection()  
        UTILS_Historique.InsertActions([{
            "IDfamille" : IDfamille,
            "IDcategorie" : IDcategorie, 
            "action" : _("%s du r�glement ID%d : %s en %s %spay� par %s") % (categorie, self.IDreglement, montant, texteMode, texteDetail, textePayeur),
            },])
        
        return True
        
    def OnClose(self, event):
        self.MemoriseTailleFenetre() 
        event.Skip() 
        
    def MemoriseTailleFenetre(self):
        # M�morisation du param�tre de la taille d'�cran
        if self.IsMaximized() == True :
            taille_fenetre = (0, 0)
        else:
            taille_fenetre = tuple(self.GetSize())
        UTILS_Config.SetParametre("taille_fenetre_reglement", taille_fenetre)

    def ImportationDernierReglement(self):
        DB = GestionDB.DB()
        req = """SELECT IDmode, IDemetteur, IDpayeur
        FROM reglements
        WHERE IDcompte_payeur=%d
        ORDER BY IDreglement DESC
        LIMIT 1
        ;""" % self.IDcompte_payeur
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if len(listeDonnees) == 0 : return
        IDmode, IDemetteur, IDpayeur = listeDonnees[0]
        self.ctrl_mode.SetID(IDmode)
        self.OnChoixMode(None)
        if self.ctrl_emetteur.IsEnabled() == True :
            self.ctrl_emetteur.SetID(IDemetteur)
            self.OnChoixEmetteur(None)
        self.ctrl_payeur.SetID(IDpayeur)
    
    def SelectionneFacture(self, IDfacture=None):
        self.ctrl_ventilation.SelectionneFacture(IDfacture)
        montant = self.ctrl_ventilation.ctrl_ventilation.GetTotalVentile()
        self.ctrl_ventilation.SetMontantReglement(montant)
        self.ctrl_montant.SetMontant(montant)

if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    import time
    heure_debut = time.time()
    dialog_1 = Dialog(None, IDcompte_payeur=4542, IDreglement=31945)
    print("Temps de chargement Saisie d'un reglement =", time.time() - heure_debut)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()

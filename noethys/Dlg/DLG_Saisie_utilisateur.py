#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
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
import GestionDB
from Ctrl import CTRL_Droits
import wx.lib.agw.hyperlink as Hyperlink
from hashlib import sha256
from Utils import UTILS_Internet
from Utils import UTILS_Parametres
from Ctrl import CTRL_Compte_internet

LISTE_IMAGES = [

    [_("Hommes"), [
        (_("Homme 1"), "Homme1"),
        (_("Homme 2"), "Hommechic"),
        (_("Pilote"), "Hommepilote"),
        (_("Barbare"), "Barbare"),
        (_("Cowboy"), "Cowboy"),
        (_("Marié"), "Marie"),
        (_("Père Noël"), "Perenoel"),
        (_("Ouvrier"), "Ouvrier"),
        (_("Garçon"), "Garcon"),
        ]],
        
    [_("Femmes"), [
        (_("Femme 1"), "Femme1"),
        (_("Femme 2"), "Femme2"),
        (_("Femme 3"), "Femme3"),
        (_("Cowgirl"), "Cowgirl"),
        (_("Viking"), "Viking"),
        (_("Mariée"), "Mariee"),
        (_("Pilote"), "Femmepilote"),
        (_("Secrétaire"), "Femmesecretaire"),
        (_("Mère Noël"), "Merenoel"),
        (_("Ouvrière"), "Ouvriere"),
        (_("Fille"), "Fille"),
        ]],
        
    [_("Animaux"), [
        (_("Oiseau 1"), "Oiseau1"),
        (_("Oiseau 2"), "Oiseau2"),
        (_("Oiseau 3"), "Oiseau3"),
        (_("Poisson"), "Poisson1"),
        (_("Lion"), "Lion"),
        ]],

    [_("Sports"), [
        (_("Basket-ball"), "Basket"),
        (_("Rugby"), "Rugby"),
        (_("Tennis"), "Tennis"),
        (_("Foot-ball"), "Foot"),
        ]],

    [_("Abstrait"), [
        (_("Abstrait 1"), "Abstrait1"),
        (_("Abstrait 2"), "Abstrait2"),
        (_("Abstrait 3"), "Abstrait3"),
        (_("Abstrait 4"), "Abstrait4"),
        ]],

    [_("Divers"), [
        (_("Bonhomme de neige"), "Bonhommedeneige"),
        (_("Boussole"), "Boussole"),
        (_("Cadeau"), "Cadeau"),
        (_("Chine"), "Chine"),
        ]],

    ]
NBCARMDP = 6
NBDIGMDP = 1
NBUPPMDP = 1
NBLOWMDP = 1
EXIGEMDP = ( NBCARMDP, NBUPPMDP, NBLOWMDP, NBDIGMDP,)

class Hyperlien(Hyperlink.HyperLinkCtrl):
    def __init__(self, parent, id=-1, label="", infobulle="", URL=""):
        Hyperlink.HyperLinkCtrl.__init__(self, parent, id, label, URL=URL)
        self.parent = parent
        
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
        self.parent.ctrl_image.ContextMenu()
        self.UpdateLink()


class CTRL_Image(wx.StaticBitmap):
    def __init__(self, parent, nomImage="Automatique", style=wx.SUNKEN_BORDER):
        wx.StaticBitmap.__init__(self, parent, id=-1, style=style)
        self.parent = parent
        self.tailleImage = (128, 128)
        self.nomImage = nomImage
        self.SetMinSize(self.tailleImage) 
        self.SetSize(self.tailleImage) 
        self.SetBackgroundColour(wx.Colour(0, 0, 0))
        self.SetToolTip(wx.ToolTip(_("Cliquez sur le bouton droit de votre souris\npour sélectionner un avatar")))
        
        self.Bind(wx.EVT_LEFT_DOWN, self.ContextMenu)
        self.Bind(wx.EVT_RIGHT_DOWN, self.ContextMenu)
        
        self.MAJ() 

    def ContextMenu(self, event=None):
        # Création du menu contextuel
        menuPop = UTILS_Adaptations.Menu()
        
        # Automatique
        item = wx.MenuItem(menuPop, 999, _("Automatique (Défaut)"))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnItemMenu, id=999)
        
        menuPop.AppendSeparator()
                    
        # Item Modifier
        tailleImage = (60, 60)
        numCategorie = 1000
        for labelSousMenu, listeItems in LISTE_IMAGES :
            
            sousMenu = UTILS_Adaptations.Menu()
            numItem = 0
            for label, nomImage in listeItems :
                id = numCategorie + numItem
                item = wx.MenuItem(menuPop, id, label)
                bmp = wx.Bitmap(Chemins.GetStaticPath("Images/Avatars/128x128/%s.png" % nomImage), wx.BITMAP_TYPE_PNG)
                item.SetBitmap(self.ConvertTailleImage(bmp, tailleImage))
                sousMenu.AppendItem(item)
                self.Bind(wx.EVT_MENU, self.OnItemMenu, id=id)
                numItem += 1
        
            menuPop.AppendMenu(numCategorie, labelSousMenu, sousMenu)
            numCategorie += 1000

        self.PopupMenu(menuPop)
        menuPop.Destroy()
    
    def OnItemMenu(self, event):
        id = event.GetId() 
        if id == 999 :
            nomImage = "Automatique"
        else :
            numCategorie = int((str(id))[0]) - 1
            numItem = id - ((numCategorie+1)*1000)
            nomImage = LISTE_IMAGES[numCategorie][1][numItem][1]
        self.SetImage(nomImage)
    
    def MAJ(self):
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/Avatars/128x128/%s.png" % self.nomImage), wx.BITMAP_TYPE_PNG)
        self.SetBitmap(bmp)
        
    def ConvertTailleImage(self, bitmap=None, taille=None):
        """ Convertit la taille d'une image """
        # Réduction de l'image
        bitmap = bitmap.ConvertToImage()
        bitmap = bitmap.Rescale(width=taille[0], height=taille[1], quality=wx.IMAGE_QUALITY_HIGH) 
        bitmap = bitmap.ConvertToBitmap()
        
        # Insertion de l'image sur un fond noir
        img = wx.EmptyImage(taille[0], taille[1], True)
        img.SetRGB((0, 0, taille[0], taille[1]), 0, 0, 0)
        bmp = img.ConvertToBitmap()
        dc = wx.MemoryDC()
        dc.SelectObject(bmp)
        dc.DrawBitmap(bitmap, int(taille[0]/2.0-bitmap.GetSize()[0]/2.0), int(taille[1]/2.0-bitmap.GetSize()[1]/2.0))
        dc.SelectObject(wx.NullBitmap)
        return bmp

    def SetImage(self, nomImage="Automatique"):
        if nomImage == None :
            nomImage = "Automatique"
        self.nomImage = nomImage
        self.MAJ() 
        
    def GetImage(self):
        return self.nomImage

# ----------------------------------------------------------------------------------------
class CTRL_Modeles_droits(wx.Choice):
    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1) 
        self.parent = parent
        self.MAJ() 
    
    def MAJ(self):
        listeItems = self.GetListeDonnees()
        if len(listeItems) == 0 :
            self.Enable(False)
        else :
            self.SetItems(listeItems)
            self.Select(0)
                                        
    def GetListeDonnees(self):
        DB = GestionDB.DB()
        req = """SELECT IDmodele, nom, observations
        FROM modeles_droits ORDER BY nom; """ 
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        listeItems = []
        self.dictDonnees = {}
        index = 0
        for IDmodele, nom, observations in listeDonnees :
            listeItems.append(nom)
            self.dictDonnees[index] = IDmodele
            index += 1
        return listeItems

    def SetID(self, IDmodele=None):
        for index, IDmodeleTemp in self.dictDonnees.items() :
            if IDmodeleTemp == IDmodele :
                self.SetSelection(index)

    def GetID(self):
        index = self.GetSelection()
        if index == -1 :
            return None
        else :
            return self.dictDonnees[index]

# --------------------------- DLG de saisie du nouveau mot de passe ---------------------
class DLG_Saisie_mdp(wx.Dialog):
    def __init__(self, parent,IDutilisateur=None, titre=None, intro=None):
        if not titre: titre = "Modification du mot de passe"
        if not intro:
            intro = "Veuillez saisir un nouveau mot de passe :"
            intro += "\n\n (avec %d caractères, %d majuscule, %d minuscule, %d chiffre)"%EXIGEMDP

        wx.Dialog.__init__(self, parent, id=-1, name="DLG_nouveau_mdp_utilisateur",
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.parent = parent
        self.IDutilisateur = IDutilisateur
        self.SetTitle(titre)
        self.intro = intro
        self.testMdp = ""
        self.checkHideValue = True
        self.ctrl_mdp = wx.TextCtrl(self, -1, "",style= wx.TE_PASSWORD)
        self.ctrl_confirm = wx.TextCtrl(self, -1, "", style=wx.TE_PASSWORD)
        self.Init()

    def Init(self):
        self.staticbox = wx.StaticBox(self, -1, "")
        self.label = wx.StaticText(self, -1, self.intro)
        self.label_mdp = wx.StaticText(self, -1, _("Mot de passe :"))
        self.label_confirmation = wx.StaticText(self, -1, _("Confirmation :"))
        self.checkHideMdp = wx.CheckBox(self,-1,"Masquer la saisie ",)
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ok"), cheminImage="Images/32x32/Valider.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Annuler"), cheminImage="Images/32x32/Annuler.png")

        self.Set_properties()
        self.Do_layout()
        self.ctrl_mdp.SetFocus()

    def Set_properties(self):
        self.checkHideMdp.SetValue(self.checkHideValue)
        self.checkHideMdp.SetToolTip(wx.ToolTip("Pour voir votre saisie décochez"))
        self.ctrl_mdp.SetToolTip(wx.ToolTip(_("Saisissez un mot de passe, mini 6 car, dont 1 Maj, 1Min, 1Maj")))
        self.ctrl_confirm.SetToolTip(wx.ToolTip(_("Confirmez le mot de passe en le saisissant une nouvelle fois")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_("Cliquez ici pour valider")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Cliquez ici pour annuler")))
        self.ctrl_mdp.SetMinSize((100, -1))
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.ctrl_mdp.Bind(wx.EVT_KILL_FOCUS, self.OnEnterMdp)
        self.checkHideMdp.Bind(wx.EVT_CHECKBOX, self.OnCheckHideMdp)

    def Do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=0, hgap=0)
        grid_sizer_base.Add(self.label, 0, wx.ALL, 10)
        # Staticbox
        staticbox = wx.StaticBoxSizer(self.staticbox, wx.HORIZONTAL)
        grid_sizer_contenu = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)
        grid_sizer_contenu.Add(self.label_mdp, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_contenu.Add(self.ctrl_mdp, 0, wx.EXPAND, 0)
        grid_sizer_contenu.Add(self.label_confirmation, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_contenu.Add(self.ctrl_confirm, 0, wx.EXPAND, 0)
        grid_sizer_contenu.AddGrowableCol(1)
        staticbox.Add(grid_sizer_contenu, 1, wx.ALL | wx.EXPAND, 10)
        grid_sizer_base.Add(staticbox, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=5)
        grid_sizer_boutons.Add((1, 20), 0, 0, 0)
        grid_sizer_boutons.Add(self.checkHideMdp, 0, wx.ALIGN_BOTTOM, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.ALL | wx.EXPAND, 10)
        grid_sizer_base.AddGrowableCol(0)

        self.SetSizerAndFit(grid_sizer_base)
        self.Layout()
        self.CentreOnScreen()

    def GetMdpCrypt(self):
        return sha256(self.ctrl_mdp.GetValue().encode('utf-8')).hexdigest()

    def GetMdp(self):
        return self.ctrl_mdp.GetValue()

    def OnBoutonOk(self, event):
        """ Validation des données saisies """
        if (not self.UniciteMdp()) or  (not self.Security(self.ctrl_mdp.GetValue())):
            self.ctrl_mdp.SetFocus()
            return False

        if len(self.ctrl_confirm.GetValue()) == 0:
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement saisir la confirmation du mot de passe !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_confirm.SetFocus()
            return False

        if self.ctrl_mdp.GetValue() != self.ctrl_confirm.GetValue():
            dlg = wx.MessageDialog(self, _("La confirmation du mot de passe ne correspond pas au mot de passe saisi !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_confirm.SetFocus()
            return False

        # Fermeture
        self.EndModal(wx.ID_OK)

    def OnEnterMdp(self,event):
        mdp = self.GetMdp()
        if len(mdp) == 0:
            return
        self.ctrl_confirm.SetFocus()
        if len(mdp) > 0 and mdp != self.testMdp:
            self.UniciteMdp()
            self.Security(mdp)
        self.testMdp = mdp

    def OnCheckHideMdp(self,event):
        mdp = self.ctrl_mdp.GetValue()
        confirm = self.ctrl_confirm.GetValue()
        self.Sizer.Clear()
        if self.checkHideMdp.GetValue():
            self.checkHideValue = True
            self.ctrl_mdp = wx.TextCtrl(self, -1, "",style=wx.TE_PROCESS_ENTER|wx.TE_PASSWORD)
            self.ctrl_confirm = wx.TextCtrl(self, -1, "", style=wx.TE_PASSWORD)
        else:
            self.checkHideValue = False
            self.ctrl_mdp = wx.TextCtrl(self, -1, "",style=wx.TE_PROCESS_ENTER)
            self.ctrl_confirm = wx.TextCtrl(self, -1, "", style=0)
        self.ctrl_mdp.SetValue(mdp)
        self.ctrl_confirm.SetValue(confirm)
        self.Init()
        self.ctrl_mdp.SetFocus()

    def UniciteMdp(self):
        # Vérifie que le code d'accès n'est pas déjà utilisé
        IDutilisateur = self.IDutilisateur
        if not IDutilisateur: IDutilisateur = 0
        DB = GestionDB.DB()

        req = """SELECT IDutilisateur, sexe, nom, prenom, mdp, mdpcrypt, profil, actif
        FROM utilisateurs 
        WHERE (mdp LIKE '%s%%' OR mdpcrypt='%s') AND IDutilisateur<>%d
        ;""" % (self.GetMdp()[:NBCARMDP], self.GetMdpCrypt(), IDutilisateur)
        ret = DB.ExecuterReq(req, MsgBox="DLG_Saisie_utilisateur.UniciteMdp")
        listeDonnees = []
        if ret == 'ok':
            listeDonnees = DB.ResultatReq()
        DB.Close()
        if len(listeDonnees) >= NBCARMDP:
            mess = "Désolé, mot impossible\n\n"
            mess +="La racine '%s' a déja été utilisée, il faut en utiliser une autre"%self.GetMdp()[:NBCARMDP]
            dlg = wx.MessageDialog(self,mess,"Erreur de saisie", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        if ret =='ok':
            return True
        return False

    def Security(self,mdp, mute=False):
        # Test sur les exigences de complexité
        nbdigit, nbupper,nblower =0,0,0
        nbcar = len(mdp)
        for a in mdp:
            if a.isdigit(): nbdigit +=1
            if a.isupper(): nbupper +=1
            if a.islower(): nblower +=1

        condCase = nbdigit >= NBDIGMDP and nbupper >= NBUPPMDP and nblower >= NBLOWMDP
        if nbcar>=NBCARMDP and condCase:
            return True
        else:
            mess = "Mot de passe insatisfaisant\n\n"
            if nbcar < 6: mess += "n'a pas au moins 6 caractères\n"
            if nbdigit < NBDIGMDP: mess += "ne contient pas assez de chiffre\n"
            if nbupper < NBUPPMDP: mess += "ne contient pas assez de majuscule\n"
            if nblower < NBLOWMDP: mess += "ne contient pas assez de minuscule\n"
            if not mute:
                ret = wx.MessageBox(mess,"Resaisir", style=wx.CANCEL | wx.ICON_INFORMATION)
                if ret == wx.CANCEL:
                    self.ctrl_mdp.SetValue("")
                    self.ctrl_confirm.SetFocus()
                    return True
        return False

    def SaveModifPassword(self):
        IDutilisateur = self.IDutilisateur
        ret = "Le mot de passe ne satisfait pas les exigences"
        if not IDutilisateur:
            raise Exception("Pas d'IDutilisateur en 'SaveModifPassword'")
        if self.UniciteMdp() and self.Security(self.GetMdp(),mute=True):
            DB = GestionDB.DB()
            listeDonnees = [
                    ("mdp", self.GetMdp()),
                    ("mdpcrypt", self.GetMdpCrypt()),
            ]
            ret = DB.ReqMAJ("utilisateurs", listeDonnees, "IDutilisateur",
                            IDutilisateur)
            DB.Close()
        if ret == 'ok':
            mess = "Mot de passe enregistré !\n\nà utiliser lors de la prochaine connection"
            style = wx.ICON_INFORMATION
        else:
            mess = "Mot de passe inchangé!\n\n%s\nChangement redemandé à la prochaine connection"%ret
            style =wx.ICON_EXCLAMATION
        wx.MessageBox(mess,'Changement MDP',style=style)

# --------------------------- DLG de saisie d'un utilisateur  ----------------------------
class Dialog(wx.Dialog):
    def __init__(self, parent, IDutilisateur=None):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent      
        self.IDutilisateur = IDutilisateur
        self.mdp = None
        self.mdpcrypt = None

        if IDutilisateur == None :
            DB = GestionDB.DB()
            IDutilisateur = DB.GetProchainID("utilisateurs")
            DB.Close()

        # Identité
        self.staticbox_identite_staticbox = wx.StaticBox(self, -1, _("Identité"))
        self.label_sexe = wx.StaticText(self, -1, _("Sexe :"))
        self.ctrl_sexe = wx.Choice(self, -1, choices=[_("Homme"), _("Femme")])
        self.label_nom = wx.StaticText(self, -1, _("Nom :"))
        self.ctrl_nom = wx.TextCtrl(self, -1, "")
        self.label_prenom = wx.StaticText(self, -1, _("Prénom :"))
        self.ctrl_prenom = wx.TextCtrl(self, -1, "")
        
        # Image
        self.staticbox_image_staticbox = wx.StaticBox(self, -1, _("Avatar"))
        self.ctrl_image = CTRL_Image(self)
        self.hyper_image = Hyperlien(self, label=_("Choisir un avatar"), infobulle=_("Cliquez ici pour modifier l'avatar de l'utilisateur"), URL="")
        
        # Accès
        self.staticbox_acces_staticbox = wx.StaticBox(self, -1, _("Accès"))
        self.ctrl_actif = wx.CheckBox(self, -1, "Utilisateur actif")
        self.ctrl_actif.SetValue(True)
        self.bouton_modif_mdp = CTRL_Bouton_image.CTRL(self, texte="", cheminImage="Images/32x32/Cle.png")

        # Compte internet
        self.staticbox_internet_staticbox = wx.StaticBox(self, -1, _("Compte internet"))
        self.ctrl_compte_internet = CTRL_Compte_internet.CTRL(self, IDutilisateur=IDutilisateur, couleurFond=wx.WHITE)
        self.bouton_modifier = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Modifier.png"), wx.BITMAP_TYPE_ANY))
        #self.bouton_envoi_mail = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Emails_exp.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_envoi_pressepapiers = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Clipboard.png"), wx.BITMAP_TYPE_ANY))
        #self.bouton_historique = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Historique.png"), wx.BITMAP_TYPE_ANY))

        # Droits
        self.staticbox_droits_staticbox = wx.StaticBox(self, -1, _("Droits"))
        self.radio_droits_admin = wx.RadioButton(self, -1, _("Administrateur"), style=wx.RB_GROUP)
        self.radio_droits_modele = wx.RadioButton(self, -1, _("Le modèle de droits suivant :"))
        self.ctrl_modele_droits = CTRL_Modeles_droits(self)
        self.radio_droits_perso = wx.RadioButton(self, -1, _("Les droits personnalisés suivants :"))
        self.ctrl_droits = CTRL_Droits.CTRL(self, IDutilisateur=self.IDutilisateur)
        self.ctrl_droits.MAJ()
        
        # Commandes
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ok"), cheminImage="Images/32x32/Valider.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Annuler"), cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonModifMdp, self.bouton_modif_mdp)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioDroits, self.radio_droits_admin)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioDroits, self.radio_droits_modele)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioDroits, self.radio_droits_perso)
        self.Bind(wx.EVT_BUTTON, self.ctrl_compte_internet.Modifier, self.bouton_modifier)
        #self.Bind(wx.EVT_BUTTON, self.Envoyer_email, self.bouton_envoi_mail)
        self.Bind(wx.EVT_BUTTON, self.ctrl_compte_internet.Envoyer_pressepapiers, self.bouton_envoi_pressepapiers)
        #self.Bind(wx.EVT_BUTTON, self.Consulter_historique, self.bouton_historique)

        if self.IDutilisateur == None :
            self.SetTitle(_("Saisie d'un utilisateur"))

            # Création des codes internet
            internet_identifiant = UTILS_Internet.CreationIdentifiant(IDutilisateur=IDutilisateur)
            internet_mdp = UTILS_Internet.CreationMDP(nbreCaract=8)
            self.ctrl_compte_internet.SetDonnees({"internet_actif": 0, "internet_identifiant": internet_identifiant, "internet_mdp": internet_mdp})

        else:
            self.SetTitle(_("Modification d'un utilisateur"))
            self.Importation()
        
        self.OnRadioDroits(None)
        self.MAJboutonMdp()

    def __set_properties(self):
        self.bouton_modifier.SetToolTip(wx.ToolTip(_("Modifier les paramètres du compte internet")))
        #self.bouton_envoi_mail.SetToolTip(wx.ToolTip(_("Envoyer un couriel à la famille avec les codes d'accès au portail Internet")))
        self.bouton_envoi_pressepapiers.SetToolTip(wx.ToolTip(_("Copier les codes d'accès dans le presse-papiers afin de les coller ensuite dans un document ou un email par exemple")))
        #self.bouton_historique.SetToolTip(wx.ToolTip(_("Consulter et traiter les demandes de l'utilisateur")))
        self.ctrl_sexe.SetToolTip(wx.ToolTip(_("Sélectionnez le sexe de l'utilisateur")))
        self.ctrl_sexe.SetSelection(0)
        self.ctrl_nom.SetToolTip(wx.ToolTip(_("Saisissez ici le nom de famille de l'utilisateur")))
        self.ctrl_prenom.SetToolTip(wx.ToolTip(_("Saisissez ici le prénom de l'utilisateur")))
        self.radio_droits_admin.SetToolTip(wx.ToolTip(_("Sélectionnez l'option 'Administrateur' pour donner tous les droits à cet utilisateur")))
        self.radio_droits_modele.SetToolTip(wx.ToolTip(_("Sélectionnez cette option pour attribuer un modèle de droits à cet utilisateur")))
        self.radio_droits_perso.SetToolTip(wx.ToolTip(_("Sélectionnez cette option pour attribuer des droits personnalisés à cet utilisateur")))
        self.ctrl_actif.SetToolTip(wx.ToolTip(_("Décochez cette case pour désactiver l'utilisateur. L'utilisateur n'aura plus accès à ce fichier de données.")))
        self.bouton_modif_mdp.SetToolTip(wx.ToolTip(_("Cliquez ici pour saisir un nouveau mot de passe pour cet utilisateur")))
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici pour obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_("Cliquez ici pour valider")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Cliquez ici pour annuler")))
        self.SetMinSize((850, 750))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_haut = wx.FlexGridSizer(rows=1, cols=3, vgap=10, hgap=10)
        grid_sizer_haut_gauche = wx.FlexGridSizer(rows=2, cols=1, vgap=10, hgap=10)
        
        # Identité
        staticbox_identite = wx.StaticBoxSizer(self.staticbox_identite_staticbox, wx.VERTICAL)
        grid_sizer_identite = wx.FlexGridSizer(rows=3, cols=2, vgap=5, hgap=10)
        grid_sizer_identite.Add(self.label_sexe, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_identite.Add(self.ctrl_sexe, 0, 0, 0)
        grid_sizer_identite.Add(self.label_nom, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_identite.Add(self.ctrl_nom, 0, wx.EXPAND, 0)
        grid_sizer_identite.Add(self.label_prenom, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_identite.Add(self.ctrl_prenom, 0, wx.EXPAND, 0)
        
        grid_sizer_identite.AddGrowableCol(1)
        staticbox_identite.Add(grid_sizer_identite, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_haut_gauche.Add(staticbox_identite, 1, wx.EXPAND, 0)
        
        # Accès
        staticbox_acces = wx.StaticBoxSizer(self.staticbox_acces_staticbox, wx.VERTICAL)
        self.grid_sizer_acces = wx.FlexGridSizer(rows=1, cols=5, vgap=10, hgap=10)
        self.grid_sizer_acces.Add(self.ctrl_actif, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        self.grid_sizer_acces.Add( (5, 5), 0, wx.EXPAND, 0)
        self.grid_sizer_acces.Add(self.bouton_modif_mdp, 0, 0, 0)
        self.grid_sizer_acces.AddGrowableCol(1)

        staticbox_acces.Add(self.grid_sizer_acces, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_haut_gauche.Add(staticbox_acces, 1, wx.EXPAND, 0)
        grid_sizer_haut_gauche.AddGrowableCol(0)
        
        grid_sizer_haut.Add(grid_sizer_haut_gauche, 1, wx.EXPAND, 0)
        
        # Image
        staticbox_image = wx.StaticBoxSizer(self.staticbox_image_staticbox, wx.VERTICAL)
        staticbox_image.Add(self.ctrl_image, 0, wx.ALL|wx.EXPAND, 10)
        staticbox_image.Add(self.hyper_image, 0, wx.ALIGN_CENTER|wx.ALL, 0)
        grid_sizer_haut.Add(staticbox_image, 1, wx.EXPAND, 0)
        
        grid_sizer_haut.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_haut, 1, wx.ALL|wx.EXPAND, 10)

        # Compte internet
        staticbox_internet = wx.StaticBoxSizer(self.staticbox_internet_staticbox, wx.VERTICAL)
        grid_sizer_param = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_param.Add(self.ctrl_compte_internet, 0, wx.EXPAND, 0)

        grid_sizer_boutons = wx.FlexGridSizer(rows=6, cols=1, vgap=5, hgap=5)
        grid_sizer_boutons.Add(self.bouton_modifier, 0, 0, 0)
        grid_sizer_boutons.Add( (5, 5), 0, 0, 0)
        #grid_sizer_boutons.Add(self.bouton_envoi_mail, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_envoi_pressepapiers, 0, 0, 0)
        #grid_sizer_boutons.Add(self.bouton_historique, 0, 0, 0)
        grid_sizer_param.Add(grid_sizer_boutons, 0, 0, 0)
        grid_sizer_param.AddGrowableRow(0)
        grid_sizer_param.AddGrowableCol(0)

        staticbox_internet.Add(grid_sizer_param, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_haut.Add(staticbox_internet, 1, wx.ALL|wx.EXPAND, 0)

        # Droits
        staticbox_droits = wx.StaticBoxSizer(self.staticbox_droits_staticbox, wx.VERTICAL)
        grid_sizer_droits = wx.FlexGridSizer(rows=5, cols=1, vgap=10, hgap=10)

        grid_sizer_droits.Add(self.radio_droits_admin, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_droits.Add(self.radio_droits_modele, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_droits.Add(self.ctrl_modele_droits, 1, wx.LEFT|wx.EXPAND, 20)
        grid_sizer_droits.Add(self.radio_droits_perso, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_droits.Add(self.ctrl_droits, 1, wx.LEFT|wx.EXPAND, 20)
        
        grid_sizer_droits.AddGrowableCol(0)
        grid_sizer_droits.AddGrowableRow(4)
        staticbox_droits.Add(grid_sizer_droits, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(staticbox_droits, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

        # Commandes
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(1)
        self.Layout()
        self.CenterOnScreen()

    def MAJboutonMdp(self, event=None):
        if self.mdpcrypt == None :
            texte = _("Saisir le mot de passe")
        else :
            texte = _("Modifier le mot de passe")
        self.bouton_modif_mdp.SetTexte(texte)

    def OnBoutonAide(self, event): 
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Utilisateurs")

    def OnRadioDroits(self, event):
        self.ctrl_modele_droits.Enable(self.radio_droits_modele.GetValue())
        self.ctrl_droits.Enable(self.radio_droits_perso.GetValue())
        if self.radio_droits_perso.GetValue() == True :
            self.ctrl_droits.SetModeDisable(False)
        else :
            if self.ctrl_droits.modeDisable == False :
                self.ctrl_droits.SetModeDisable(True)

    def OnBoutonModifMdp(self, event):
        if self.mdpcrypt == None :
            titre = _("Saisie du mot de passe")
            intro = _("Veuillez saisir un mot de passe :")
        else :
            titre = None
            intro = None
        dlg = DLG_Saisie_mdp(self,titre=titre,intro=intro,IDutilisateur=self.IDutilisateur)
        if dlg.ShowModal() == wx.ID_OK:
            if dlg.UniciteMdp():
                self.mdp = dlg.GetMdp()
                self.mdpcrypt = dlg.GetMdpCrypt()
        dlg.Destroy()
        self.MAJboutonMdp()
        self.grid_sizer_acces.Layout()

    def OnBoutonOk(self, event): 
        # Vérification des données
        if len(self.ctrl_nom.GetValue()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement saisir un nom !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_nom.SetFocus()
            return

        if self.mdpcrypt == None :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement saisir un mot de passe !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        if self.IDutilisateur == None :
            IDutilisateurTmp = 0
        else:
            IDutilisateurTmp = self.IDutilisateur

        # Vérifie qu'il reste au moins un administrateur dans la base de données
        if self.radio_droits_admin.GetValue() == False :
            DB = GestionDB.DB()
            req = """SELECT IDutilisateur, profil
            FROM utilisateurs
            WHERE profil='administrateur' AND IDutilisateur!=%d;""" % IDutilisateurTmp
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            listeDonnees = DB.ResultatReq()
            DB.Close()
            if len(listeDonnees) == 0 :
                dlg = wx.MessageDialog(self, _("Il doit rester au moins un administrateur dans le fichier !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return

        # Vérifie qu'il reste au moins un administrateur ACTIF dans la base de données
        if self.ctrl_actif.GetValue() == False :
            DB = GestionDB.DB()
            req = """SELECT IDutilisateur, profil, actif
            FROM utilisateurs
            WHERE profil='administrateur' AND actif=1 AND IDutilisateur!=%d;""" % IDutilisateurTmp
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            listeDonnees = DB.ResultatReq()
            DB.Close()
            if len(listeDonnees) == 0 :
                dlg = wx.MessageDialog(self, _("Il doit rester au moins un administrateur ACTIF dans le fichier ! Cochez la case Actif."), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return

        # Droits
        if self.radio_droits_modele.GetValue() == True :
            if self.ctrl_modele_droits.GetID() == None :
                dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucun modèle de droits !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return

        # Vérifie que le compte n'est pas inactif alors que le compte internet est actif
        dictCompteInternet = self.ctrl_compte_internet.GetDonnees()
        if dictCompteInternet["internet_actif"] == 1 and self.ctrl_actif.GetValue() == False :
            dlg = wx.MessageDialog(self, _("Vous devez désactiver le compte internet si vous souhaitez désactiver cet utilisateur !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        # Sauvegarde
        self.Sauvegarde()
        
        # Fermeture de la fenêtre
        self.EndModal(wx.ID_OK)

    def GetIDutilisateur(self):
        return self.IDutilisateur

    def Importation(self):
        """ Importation des donnees de la base """
        DB = GestionDB.DB()
        req = """SELECT sexe, nom, prenom, mdp, mdpcrypt, profil, actif, image, internet_actif, internet_identifiant, internet_mdp
        FROM utilisateurs 
        WHERE IDutilisateur=%d;""" % self.IDutilisateur
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if len(listeDonnees) == 0 : return
        sexe, nom, prenom, mdp, mdpcrypt, profil, actif, image, internet_actif, internet_identifiant, internet_mdp = listeDonnees[0]
        # Identité
        if sexe == "M" :
            self.ctrl_sexe.Select(0)
        else:
            self.ctrl_sexe.Select(1)
        self.ctrl_nom.SetValue(nom)
        self.ctrl_prenom.SetValue(prenom)
        # Accès
        self.mdp = mdp
        self.mdpcrypt = mdpcrypt
        if actif == 1 :
            self.ctrl_actif.SetValue(True)
        else:
            self.ctrl_actif.SetValue(False)
        # Droits
        if profil != None :
            if profil.startswith("administrateur") :
                self.radio_droits_admin.SetValue(True) 
            if profil.startswith("modele") :
                self.radio_droits_modele.SetValue(True) 
                IDmodele = int(profil.split(":")[1])
                self.ctrl_modele_droits.SetID(IDmodele)
            if profil.startswith("perso") :
                self.radio_droits_perso.SetValue(True)
        # Avatar
        self.ctrl_image.SetImage(image)
        # Compte internet
        self.ctrl_compte_internet.SetDonnees({"internet_actif": internet_actif, "internet_identifiant": internet_identifiant, "internet_mdp": internet_mdp})

    def Sauvegarde(self):
        """ Sauvegarde """
        # Identité
        if self.ctrl_sexe.GetSelection() == 0 :
            sexe = "M"
        else:
            sexe = "F"
        nom = self.ctrl_nom.GetValue() 
        prenom = self.ctrl_prenom.GetValue() 
        
        # Accès
        if self.ctrl_actif.GetValue() == True :
            actif = 1
        else:
            actif = 0
            
        # Droits
        if self.radio_droits_admin.GetValue() == True : 
            profil = "administrateur"
        if self.radio_droits_modele.GetValue() == True : 
            profil = "modele:%d" % self.ctrl_modele_droits.GetID() 
        if self.radio_droits_perso.GetValue() == True : 
            profil = "perso"
        
        # Avatar
        nomImage = self.ctrl_image.GetImage()

        # Compte internet
        dictCompteInternet = self.ctrl_compte_internet.GetDonnees()
        
        # Sauvegarde
        DB = GestionDB.DB()
        listeDonnees = [    
                ("sexe", sexe),
                ("nom", nom),
                ("prenom", prenom),
                ("mdp", self.mdp),
                ("mdpcrypt", self.mdpcrypt),
                ("profil", profil),
                ("actif", actif),
                ("image", nomImage),
                ("internet_actif", dictCompteInternet["internet_actif"]),
                ("internet_identifiant", dictCompteInternet["internet_identifiant"]),
                ("internet_mdp", dictCompteInternet["internet_mdp"]),
        ]
        if self.IDutilisateur == None :
            self.IDutilisateur = DB.ReqInsert("utilisateurs", listeDonnees)
        else:
            DB.ReqMAJ("utilisateurs", listeDonnees, "IDutilisateur", self.IDutilisateur)
        DB.Close()
    
        # Droits
        self.ctrl_droits.Sauvegarde(IDutilisateur=self.IDutilisateur)

# ----------------------------------------------------------------------------------------

if __name__ == "__main__":
    app = wx.App(0)
    dialog_1 = Dialog(None, IDutilisateur=7)
    dialog_1.ShowModal()
    #dialog_2 = DLG_Saisie_mdp(None,)
    #dialog_2.ShowModal()
    #dialog_2.SaveModifPassword()
    app.MainLoop()

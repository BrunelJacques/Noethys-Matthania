#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:          Ivan LUCAS, JB, Jacques Brunel
# Licence:         Licence GNU GPL
# Gestion de la piece en modifiction
# Adapté à partir de DLG_InscriptionModif
#------------------------------------------------------------------------

from Utils.UTILS_Traduction import _
import wx
import datetime
from Dlg import DLG_Inscription
from Utils import UTILS_Utilisateurs
from Gest import GestionArticle
import GestionDB
from Gest import GestionInscription
from Dlg import DLG_PrixActivite
from Dlg import DLG_InscriptionComplements
from Dlg import DLG_PrixFamille
from Dlg import DLG_InscriptionModif

def Nz(valeur):
    if valeur == None:
        valeur = 0
    return valeur

def Decod(valeur):
    return GestionDB.Decod(valeur)

# -----------------------------------------------------------------------------------------------------------------
class DlgMenu(wx.Dialog):
    def __init__(self, parent, selection, mode, *args, **kwds):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE)
        self.DB = kwds.get("DB",GestionDB.DB())
        self.selection=selection
        self.module = "DLG_InscriptionMenu.DlgMenu"
        self.parent = parent
        self.IDindividu = kwds.pop("IDindividu", None)
        self.dictFamillesRattachees = kwds.pop("dictFamillesRattachees", {} )
        self.dictPiece={}
        self.dictPiece["origine"]="vide"
        self.dictPiece["nature"]=""
        self.listeNoms = []
        self.listeFamille = []
        self.inscriptionChoisie = False
        self.IDfamille = None
        for self.IDfamille, dictFamille in self.dictFamillesRattachees.items() :
            self.listeFamille.append(self.IDfamille)
            self.listeNoms.append(dictFamille["nomsTitulaires"])

        droitCreation = UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_inscriptions", "creer")
        if mode == "modifier":
            self.Modifier()

        if mode == "ajouter":
            if droitCreation: parent.selection = self.Ajouter()
            else: GestionDB.MessageBox(self, "Vous ne disposez pas de droits pour créer des individus_inscriptions")


        if mode == "supprimer":
            if droitCreation: self.Supprimer()
            else: GestionDB.MessageBox(self, "Vous ne disposez pas de droits pour créer des individus_inscriptions")

        if len(selection) >0:
            self.VerifTransports()
        self.DB.Close()

    def VerifTransports(self):
        # Checkpoint pour tracker des pertes d'info constatées, à des fins de débug
        IDinscription = self.selection[0].IDinscription
        req = """
            SELECT matPieces.pieIDtranspAller, matPieces.pieIDtranspRetour, 
                    matPieces.piePrixTranspAller, matPieces.piePrixTranspRetour, 
                    transports.IDtransport, trsp_1.IDtransport
            FROM (matPieces 
                LEFT JOIN transports ON matPieces.pieIDtranspAller = transports.IDtransport) 
                LEFT JOIN transports AS trsp_1 ON matPieces.pieIDtranspRetour = trsp_1.IDtransport
            WHERE (((matPieces.pieIDinscription)=%d));
            """ % IDinscription
        retour = self.DB.ExecuterReq(req, MsgBox="DLG_InscriptionMenu.VerifieTransports")
        if retour == "ok":
            recordset = self.DB.ResultatReq()
            mess = ""
            for IDpieAller,IDpieRetour,prixAller,prixRetour,IDtrspAller,IDtrspRetour in recordset:
                if Nz(IDpieAller) > 0 and Nz(IDtrspAller) == 0:
                    mess += "Un transport Aller a été envisagé pour %6.2f€, mais son détail a disparu!\n" % float(Nz(prixAller))
                if Nz(IDpieRetour) > 0 and Nz(IDtrspRetour) == 0:
                    mess += "Un transport Retour a été envisagé pour %6.2f€, mais son détail a disparu!\n" % float(Nz(prixAller))
            if len(mess) > 0:
                mess1 = "Perte d'info constatée\n\n" + mess
                mess1 += "\nMémorisez votre action et décrivez-là dans le rapport de bug que nous allons provoquer"
                ret = wx.MessageBox(mess1,"Erreur provoquée",style=wx.ICON_ERROR)
                raise Exception("IDinscription %d, IDtransport dans pièce non trouvé dans table transports" % IDinscription)

    def ChoixInscription(self):
        # Choix de la famille si multi (ajouté pour forcer un choix si plusieurs possibles)
        fGest = GestionInscription.Forfaits(self,DB=self.DB)
        if not fGest.GetFamille(self):
            self.Destroy()
        # Ouverture de la fenêtre d'inscription choix de l'activité, groupe, catTarif
        dlg = DLG_Inscription.Dialog(self,IDindividu=self.IDindividu)
        dlg.SetFamille(self.listeNoms, self.listeFamille, self.IDfamille, False)
        choixInscription = dlg.ShowModal()
        if choixInscription != wx.ID_OK:
            return wx.ID_ABORT
        self.IDactivite = dlg.GetIDactivite()
        # Vérifie que l'individu n'est pas déjà inscrit à cette activite
        for inscription in self.parent.listeListeView :
            if inscription.IDactivite == self.IDactivite and inscription.IDindividu == self.IDindividu :
                dlg2 = wx.MessageDialog(self, _("Cet individu est déjà inscrit à l'activité '%s' !") % inscription.nom_activite, _("Erreur de saisie"), wx.OK | wx.ICON_ERROR)
                dlg2.ShowModal()
                dlg2.Destroy()
                return
        IDgroupe =  dlg.GetIDgroupe()
        IDcategorie_tarif = dlg.GetIDcategorie()
        if IDgroupe == None or IDcategorie_tarif == None :
            GestionDB.MessageBox(self,"Pour une inscription il faut préciser une activité, un groupe et une catégorie de tarif!\nIl y a aussi la possibilité de facturer ici sans inscription")
            dlg.Destroy()
            return wx.ID_CANCEL
        self.memeAct = False
        if "IDactivite" in self.dictDonnees:
            if self.dictDonnees["IDactivite"] == self.IDactivite:
                self.memeAct = True
            else:
                self.dictDonnees["activite"] = self.IDactivite
        self.IDcompte_payeur = fGest.GetPayeurFamille(self,self.IDfamille)
        self.listeDonnees = [
            ("IDindividu", self.IDindividu ),
            ("IDfamille", self.IDfamille ),
            ("IDcompte_payeur", self.IDcompte_payeur),
            ("IDactivite", self.IDactivite),
            ("IDgroupe", IDgroupe),
            ("IDcategorie_tarif", IDcategorie_tarif),
            ("date_inscription", str(datetime.date.today())),
            ("parti", None),
            ]
        self.dictDonnees = fGest.GetDictDonnees(self,self.listeDonnees)
        self.nom_famille = self.listeNoms[dlg.ctrl_famille.GetSelection()]
        ajoutListe = [
            ("origine", "ajout" ),
            ("nom_activite", dlg.GetNomActivite()),
            ("nom_groupe", dlg.GetNomGroupe()),
            ("nom_categorie_tarif", dlg.GetNomCategorie()),
            ("IDparrain",None),
            ("parrainAbandon",False),
            ("commentaire", str(datetime.date.today()) + " Activité: " + dlg.GetNomActivite() + "Groupe: " + dlg.GetNomGroupe()+ "\nCampeur : " + self.dictDonnees["nom_individu"]+ " | Famille : " + self.dictDonnees["nom_famille"]),
            ]
        self.dictDonnees = fGest.ModifDictDonnees(self,ajoutListe)
        dlg.Destroy()
        self.inscriptionChoisie = True
        return wx.ID_OK
        #fin ChoixInscription

    def SetInscription(self):
        # Enregistre l'inscription façon noethys
        if not self.memeAct:
            retour = self.DB.ReqInsert("inscriptions", self.listeDonnees, retourID=False)
            if retour != "ok":
                GestionDB.MessageBox(self, retour)
                return wx.ID_ABORT
            self.IDinscription = self.DB.newID
        else:
            retour = self.DB.ReqMAJ("inscriptions", self.listeDonnees, "IDinscription", self.IDinscription,
                               MsgBox="Modif de l'inscription existante")
            if retour != "ok":
                GestionDB.MessageBox(self, retour)
                return wx.ID_ABORT
        return wx.ID_OK
        #fin SetInscription

    def AppliquerTarif(self):
        # Tarification MATTHANIA à la place de Saisie des forfaits_auto NOETHYS
        fTar = DLG_PrixActivite.DlgTarification(self,self.dictDonnees)
        tarification =fTar.ShowModal()

        # récupération des lignes de l'inscription génération de la piece
        self.naturePiece =fTar.codeNature
        listeLignesPiece = fTar.listeLignesPiece
        self.nbreJours = fTar.nbreJours

        #recherche des codes nature pour calcul de l'état
        listeCodesNature = []
        for item in GestionArticle.LISTEnaturesPieces :
            listeCodesNature.append(item[0])
        if (tarification == wx.ID_OK) and (self.naturePiece in listeCodesNature):
            etatPiece = "00000"
            i = listeCodesNature.index(self.naturePiece)
            # Mise à "1" du caractère en la position correspondant à la nature de la pièce (ex: FAC = 4eme)
            etatPiece = etatPiece[:i]+"1"+ etatPiece[i+1:]
            self.dictDonnees["nature"] = self.naturePiece
            self.dictDonnees["etat"] = etatPiece
            self.dictDonnees["lignes_piece"] = listeLignesPiece
            self.dictDonnees["nbreJours"] = self.nbreJours
            self.dictDonnees["IDprestation"] = None

            # Enregistre l'inscription nouvelle
            if self.inscriptionChoisie :
                self.SetInscription()
            self.dictDonnees["IDinscription"] = self.IDinscription

            # Actualise l'affichage et pointe la nouvelle inscription
            self.parent.MAJ(self.IDinscription)

            # Enregistre dans Pieces
            fGest = GestionInscription.Forfaits(self,DB=self.DB)
            IDnumPiece = fGest.AjoutPiece(self,self.dictDonnees)
            self.dictDonnees["IDnumPiece"] = IDnumPiece
            self.dictDonnees["noFacture"] = fGest.noFacture

            # Enregistre les consommations
            if self.naturePiece != "DEV":
                ajout = fGest.AjoutConsommations(self,self.dictDonnees)
                if not ajout :
                    self.dictDonnees["nature"] = "DEV"
                    fGest.ModifiePieceCree(self,self.dictDonnees)

            # Gestion du nombre de jours modifié
            if "nbreJours" in self.dictDonnees:
                fGest.ModifieNbreJours(self,self.dictDonnees)

            # Gestion des compléments transport cotisation et reduction famille
            fTransp = DLG_InscriptionComplements.DlgTransports(self.dictDonnees)
            transports =fTransp.ShowModal()
            self.dictDonnees = fTransp.GetDictDonnees(self.dictDonnees)
            if transports != wx.ID_OK:
                self.dictDonnees["prixTranspAller"] = None
                self.dictDonnees["prixTranspRetour"] = None
                self.dictDonnees["IDtranspAller"] = None
                self.dictDonnees["IDtranspRetour"] = None
            else:
                fGest.ModifiePieceCree(self,self.dictDonnees)
            fTransp.Destroy()

            # si seulement réservation on saute l'enregistrement de prestation
            if self.naturePiece in ("COM","FAC"):
                # Enregistre la prestation
                IDprestation = fGest.AjoutPrestation(self,self.dictDonnees)
                self.dictDonnees["IDprestation"] = IDprestation
                if IDprestation > 0 :
                    fGest.ModifiePieceCree(self,self.dictDonnees)
                    fGest.ModifieConsoCree(self,self.dictDonnees)
            fFam = DLG_PrixFamille.DlgTarification(self,self.dictDonnees,fromIndividu=True)
            fFam.ShowModal()
            fFam.Destroy()
            self.parent.MAJ(self.IDinscription)
        fTar.Destroy()
        return wx.ID_OK

    def Ajouter(self):
        # permet d'ajouter une inscription puis d'appliquer un prix
        self.dictDonnees = {}
        ret = self.ChoixInscription()
        if ret != wx.ID_OK:
            return ret
        #la clé 'coches' précise s'il faut tout décocher les articles ou pas
        self.dictDonnees['coches'] = True
        ret = self.AppliquerTarif()
        self.Historise("AjoutInscription")
        return ret
        #fin Ajouter

    def AjouterPiece(self, razConsos = False):
        # se distingue de Ajouter car on crée une nouvelle pièce alors qu'il en existe d'autres qui ont déjà été facturées et non modifiables,
        # on a ajouté des lignes à l'inscription mais c'est dans une nouvelle pièce.
        individu = self.dictDonnees["IDindividu"]
        activite = self.dictDonnees["IDactivite"]
        if "IDtranspAller" in self.dictDonnees:
            self.dictDonnees["IDtranspAller"] = None
            self.dictDonnees["IDtranspRetour"] = None
            self.dictDonnees["prixTranspAller"] = 0.0
            self.dictDonnees["prixTranspRetour"] = 0.0
        if razConsos :
            req = """DELETE FROM consommations
                   WHERE IDindividu = %d AND IDactivite =%d ;""" % (individu, activite)
            self.DB.ExecuterReq(req,commit=True,MsgBox = "AjouterPiece.razConsos")
        self.Historise("AjoutInscription")
        self.dictDonnees['coches'] = False
        self.AppliquerTarif()
        #fin AjouterPiece

    def Modifier(self):
        #tests préalables
        if len(self.selection) == 0 :
            GestionDB.MessageBox(self, "Vous n'avez sélectionné aucune inscription à modifier dans la liste")
            return
        select = self.selection[0]
        self.IDinscription = select.IDinscription
        fGest = GestionInscription.Forfaits(self,DB=self.DB)
        reqPiece = fGest.GetPieceModif(self,select.IDindividu,select.IDactivite)
        # GetPieceModif False pour abandon, None pour absence de piece, True pour self.dictPiece alimentée
        if reqPiece == None:
            GestionDB.MessageBox(self, _("Pas de pièce associée à cette inscription!\nLa modification est impossible"))
            fGest.NeutraliseReport(select.IDfamille, select.IDindividu, select.IDactivite)
            return
        if reqPiece == False:
            return

        # présence d'une pièce pointée dans fGest
        self.dictDonneesOrigine = fGest.dictPiece
        fGest = GestionInscription.Forfaits(self,DB=self.DB)
        if not fGest.GetFamille(self):
            self.Destroy()
        dlg = DLG_Inscription.Dialog(self,IDindividu=self.IDindividu)
        dlg.SetFamille(self.listeNoms, self.listeFamille, self.IDfamille, False)
        dlg.Destroy()
        if self.dictDonneesOrigine["IDfamille"] != self.IDfamille:
            GestionDB.MessageBox(self, "Cette inscription n'est pas dans cette famille actuelle, allez dans la famille %d"%self.dictDonneesOrigine["IDfamille"])
            return

        self.dictDonneesOrigine["origine"]= "modif"
        self.IDactivite = self.dictDonneesOrigine["IDactivite"]
        modifiable = fGest.PieceModifiable(self,self.dictDonneesOrigine)
        fMod = DLG_InscriptionModif.Dialog(self,self.dictDonneesOrigine,self.dictFamillesRattachees)
        if not modifiable:
            texte = "Pb cette facture n'en est pas vraiment une! etat : %s nature %s" %(self.dictDonneesOrigine["etat"],self.dictDonneesOrigine["nature"])
            if len(self.dictDonneesOrigine["etat"]) > 3:
                etatFacture = int(self.dictDonneesOrigine["etat"][3])
                if etatFacture > 2:
                    texte = "Elle est consultable et peut faire l'objet d'un avoir global"
                else:
                    texte = "Par 'Facturation' une rétrogradation en commande est possible"
            GestionDB.MessageBox(self, "Facturé : seules les notes sont modifiables!\n" + texte,titre="Information")
            self.dictDonneesOrigine["origine"]= "consult"
        #appel du dialogue de modification et récup de la saisie des données
        modif = fMod.ShowModal()

        # retour sur validation des modifs
        if modif == wx.ID_OK:
            self.dictDonnees = fMod.dictDonnees
            fMod.Destroy()
            self.Historise("ModificationInscription")
            # Vérifier pour confirmer les réductions liées aux inscriptions...
            fFam = DLG_PrixFamille.DlgTarification(self,self.dictDonnees,fromIndividu=True)
            ret = fFam.ShowModal()
            fFam.Destroy()
            if ret == wx.ID_OK:
                # Actualise l'affichage et pointe l'inscription
                self.parent.MAJ(self.IDinscription)
                return
            else:
                #fermeture du DLG_Individu
                try :
                    self.parent.parent.parent.parent.Destroy()
                except :
                    pass
        #retour sur nouvelle pièce

        elif modif == wx.ID_APPLY:
            # Cas d'un ajout de lignes complémentaires à la facture principale de l'activité
            self.dictDonnees = fMod.dictDonnees
            self.AjouterPiece(razConsos=True)

        elif modif == wx.ID_BOTTOM:
            # Cas de la génération d'un avoir global de la pièce
            self.dictDonnees = fMod.dictDonnees
            fMod.Destroy()
            self.Historise("AvoirInscription")
            # Vérifier pour confirmer les réductions liées aux inscriptions...
            fFam = DLG_PrixFamille.DlgTarification(self,self.dictDonnees,fromIndividu=True,fromAvoir=True)
            ret = fFam.ShowModal()
        #fin Modifier

    def Supprimer(self):
        if len(self.selection) == 0 :
            GestionDB.MessageBox(self, _("Vous n'avez sélectionné aucune inscription à supprimer dans la liste"))
            return
        for select in self.selection:
            # Gestion du type de suppression
            fGest = GestionInscription.Forfaits(self,DB=self.DB)
            reqPiece = fGest.GetPieceSupprime(self,select.IDinscription,select.IDindividu,select.IDactivite)
            #GetPieceSupprime retourne False pour abandon, None pour suppresion sans piece, True pour self.dictPiece alimentée
            if reqPiece == None:
                # pas de pièce
                fGest = GestionInscription.Forfaits(self,DB=self.DB)
                fGest.SuppressionInscription(select.IDinscription)
                self.parent.MAJ()
                return
            elif reqPiece == False:
                #abandon
                continue
            if reqPiece == True:
                self.dictDonnees = fGest.dictPiece
                suppressible = fGest.PieceModifiable(self,self.dictDonnees)
                if not suppressible :
                    GestionDB.MessageBox(self, "Facture bloquée, ne peut pas être supprimée!\nElle est consultable et peut faire l'objet d'un avoir")
                    continue
                if self.dictDonnees['nature'] in ['FAC','AVO'] :
                    GestionDB.MessageBox(self, "Une Facture doit d'abord être rétrogradée en commande pour être supprimée !\nElle est consultable et peut faire l'objet d'un avoir")
                    continue
                if len(list(self.dictDonnees.keys()))> 1:
                    dlg = wx.MessageDialog(self, _("Confirmez vous la suppression de %s  crée le %s par %s \n %s ")% (Decod(self.dictDonnees["nature"]),Decod(self.dictDonnees["dateCreation"]),Decod(self.dictDonnees["utilisateurCreateur"]),Decod(self.dictDonnees["commentaire"])), _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
                    if dlg.ShowModal() != wx.ID_YES:
                        continue
                    fGest.Suppression(self,self.dictDonnees)
                    self.Historise("SuppressionInscription")
                # Vérifier pour confirmer les réductions liées aux inscriptions...
                fFam = DLG_PrixFamille.DlgTarification(self,self.dictDonnees,fromIndividu=True)
                fFam.ShowModal()
                fFam.Destroy()
        # Actualise l'affichage
        self.parent.MAJ()
        #fin Supprimer

    def Historise(self,action):
        fGest = GestionInscription.Forfaits(self,DB=self.DB)
        # Mémorise l'action dans l'historique
        IDindividu = self.dictDonnees["IDindividu"]
        IDfamille = self.dictDonnees["IDfamille"]
        commentaire = Decod(self.dictDonnees["commentaire"])
        fGest.Historise(IDindividu,IDfamille,action, commentaire)

"""
class ProjetPnlActivite(wx.Panel):
    def __init__(self, parent, dictPiece,dictFamillesRattachees):
        wx.Panel.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE)
        self.dictDonneesOrigine = dictPiece
        self.dictFamillesRattachees = dictFamillesRattachees
        self.parent = parent
        parent.SetTitle("DLG_InscriptionMenu/PnlActivite")
        if dictPiece["origine"] in ("consult","lecture"):
            self.rw = False
        else :
            self.rw = True

        self.staticbox_CAMPgauche = wx.StaticBox(self, -1, _("Activite"))
        self.label_activite = wx.StaticText(self, -1, _("Activité (hors cotisation et transport):"))
        self.ctrl_nom_activite = wx.TextCtrl(self, -1, "",size=(50, 20))
        self.bouton_activite = wx.Button(self, -1, "...", size=(20, 20))
        self.label_groupe = wx.StaticText(self, -1,  _("Groupe :"))
        self.ctrl_nom_groupe = wx.TextCtrl(self, -1, "",size=(50, 20))
        self.label_tarif = wx.StaticText(self, -1, _("Catégorie Tarif:"))
        self.ctrl_nom_tarif = wx.TextCtrl(self, -1, "",size=(50, 20))

        self.staticbox_PRIX = wx.StaticBox(self, -1,_("Prix de l'activité"))
        self.label_prix1 = wx.StaticText(self, -1, _("Actuel :"))
        self.ctrl_prix1 = CTRL_Saisie_euros.CTRL(self)
        self.bouton_prix1 = wx.Button(self, -1, "...", size=(20, 20))
        self.label_prix2 = wx.StaticText(self, -1, _("Nouveau :"))
        self.ctrl_prix2 = CTRL_Saisie_euros.CTRL(self)
        self.bouton_prix2 = wx.Button(self, -1, "...", size=(20, 20))

        self.staticbox_PIECEgauche = wx.StaticBox(self, -1, _("Pièce"))
        self.label_nature = wx.StaticText(self, -1, _("Nature :"))
        self.ctrl_nom_nature = wx.TextCtrl(self, -1, "",size=(150, 20))
        self.bouton_piece = wx.Button(self, -1, "...", size=(20, 20))
        self.label_etat = wx.StaticText(self, -1,  _("Etat pièce :"))
        self.ctrl_nom_etat = wx.TextCtrl(self, -1, "",size=(150, 20))

        self.staticbox_CONTENU = wx.StaticBox(self, -1, _("Contenu"))
        self.label_commentaire = wx.StaticText(self, -1, _("Notes\nmodifiables :"))
        self.txt_commentaire = wx.TextCtrl(self, -1, "", style=wx.TE_MULTILINE,size = (150,60))
        self.label_infos = wx.StaticText(self, -1, _("Infos pièce :"))
        self.choice_infos = wx.Choice(self, -1, choices=[],size = (150,20))
        self.__set_data()
        self.__set_properties()
        self.__do_layout()

    def __set_data(self):
        self.modifPrestations = False
        self.modifConsommations = False
        self.modifInscriptions = False
        self.modifPieces = False
        self.dictDonnees = {}
        self.listeNoms = []
        self.listeFamille = []
        #self.dictFamillesRattachees = self.parent.dictFamillesRattachees

        #alimente Choice des listeInfo
        self.listeChamps = sorted(self.dictDonneesOrigine.keys())
        for champ in self.listeChamps:
            self.dictDonnees[champ] = self.dictDonneesOrigine[champ]
            tip = type(self.dictDonneesOrigine[champ])
            if tip in ( str, unicode):
                valeur = self.dictDonneesOrigine[champ]
            elif tip in (int, float):
                valeur = str(self.dictDonneesOrigine[champ])
            elif self.dictDonneesOrigine[champ] == None:
                valeur = "  -"
            elif tip == list:
                valeur = str(len(self.dictDonneesOrigine[champ])) +" lignes"
            else:
                valeur = str(tip)
            self.choice_infos.Append(((champ + " :"+ ("_"*25))[:30] + valeur))
        self.choice_infos.Select(16)

        # transposition de la nature et de l'état de la pièce
        self.liste_naturesPieces = copy.deepcopy(GestionArticle.LISTEnaturesPieces)
        self.liste_codesNaturePiece = []
        for a,b,c in self.liste_naturesPieces: self.liste_codesNaturePiece.append(a)
        self.liste_etatsPieces = copy.deepcopy(GestionArticle.LISTEetatsPieces)
        #ajout de l'avoir pour usage en lecture seule
        self.liste_naturesPieces.append(("AVO", "Facture&Avoir", "Facture annulée par un Avoir se génère par suppression d'une inscription facturée ou par saisie libre", ))
        nature,etat = self.GetNomsNatureEtat(self.dictDonneesOrigine)
        self.ctrl_nom_nature.SetValue(nature)
        self.ctrl_nom_etat.SetValue(etat)

        #Calcul du prix
        prix = 0.00
        listeLignes = self.dictDonneesOrigine["lignes_piece"]
        for dictLigne in listeLignes:
            prix += dictLigne["montant"]
        self.ctrl_prix1.SetValue(str("{:10.2f}".format((prix))))
        self.AffichePrix2()
        #Autre elements gérés, appel des données
        self.txt_commentaire.SetValue(Decod(self.dictDonneesOrigine["commentaire"]))
        self.ctrl_nom_individu.SetValue(self.dictDonneesOrigine["nom_individu"])
        self.ctrl_nom_famille.SetValue(self.dictDonneesOrigine["nom_famille"])
        self.ctrl_nom_payeur.SetValue(self.dictDonneesOrigine["nom_payeur"])
        self.ctrl_nom_activite.SetValue(self.dictDonneesOrigine["nom_activite"])
        self.ctrl_nom_groupe.SetValue(self.dictDonneesOrigine["nom_groupe"])
        self.ctrl_nom_tarif.SetValue(self.dictDonneesOrigine["nom_categorie_tarif"])
        # éléments pour modif
        self.IDindividu = self.dictDonneesOrigine["IDindividu"]
        self.IDfamille = self.dictDonneesOrigine["IDfamille"]
        self.IDpayeur = self.dictDonneesOrigine["IDcompte_payeur"]
        #fin SetData

    def __set_properties(self):
        self.SetMinSize((500, 600))
        self.bouton_activite.SetToolTip(_("Cliquez pour modifier les éléments acitivité"))
        self.bouton_prix1.SetToolTip(_("Cliquez pour consulter la composition du prix"))
        self.bouton_prix2.SetToolTip(_("Cliquez pour modifier la tarification actuelle"))
        self.bouton_piece.SetToolTip(_("Cliquez pour modifier la nature de la pièce, l'état en découle"))
        self.choice_infos.SetToolTip(_("Pour info seulement, contenu du fichier pièce"))
        self.txt_commentaire.SetToolTip(_("Ces infos sont générées automatiquement lors de la création mais vous pouvez les modifier"))
        self.ctrl_nom_groupe.SetToolTip(_("Cliquez sur le bouton pour modifier les éléments acitivité"))
        self.ctrl_nom_tarif.SetToolTip(_("Cliquez sur le bouton pour modifier les éléments acitivité"))
        self.ctrl_prix1.SetToolTip(_("Cliquez pour consulter la composition du prix"))
        self.ctrl_prix2.SetToolTip(_("Cliquez sur le bouton pour modifier la tarification actuelle"))
        self.ctrl_nom_nature.SetToolTip(_("Cliquez sur le bouton pour changer la nature de la pièce, l'état en découle"))
        self.ctrl_nom_activite.SetToolTip(_("Cliquez sur le bouton pour modifier les éléments acitivité"))

        self.Bind(wx.EVT_BUTTON, self.On_activite, self.bouton_activite)
        self.ctrl_nom_activite.Bind(wx.EVT_SET_FOCUS, self.On_ctrl_activite)
        self.ctrl_nom_groupe.Bind(wx.EVT_SET_FOCUS, self.On_ctrl_activite)
        self.ctrl_nom_tarif.Bind(wx.EVT_SET_FOCUS, self.On_ctrl_activite)
        self.Bind(wx.EVT_BUTTON, self.On_prix1, self.bouton_prix1)
        self.Bind(wx.EVT_BUTTON, self.On_prix2, self.bouton_prix2)
        self.ctrl_prix2.Bind(wx.EVT_SET_FOCUS, self.On_ctrl_prix2)
        self.Bind(wx.EVT_BUTTON, self.On_piece, self.bouton_piece)
        self.ctrl_nom_nature.Bind(wx.EVT_SET_FOCUS, self.On_ctrl_nom_nature)
        self.txt_commentaire.Bind(wx.EVT_KILL_FOCUS, self.On_commentaire)
        self.label_etat.Enable(False)
        self.ctrl_nom_etat.Enable(False)
        self.ctrl_prix1.Enable(False)
        self.bouton_prix2.Enable(self.rw)
        self.bouton_piece.Enable(self.rw)
        self.bouton_activite.Enable(self.rw)
        self.ctrl_nom_etat.Enable(self.rw)
        self.ctrl_prix2.Enable(self.rw)
        self.ctrl_nom_nature.Enable(self.rw)
        self.ctrl_nom_activite.Enable(self.rw)
        self.ctrl_nom_groupe.Enable(self.rw)
        self.ctrl_nom_tarif.Enable(self.rw)
        self.ctrl_nom_nature.Enable(self.rw)
        self.ctrl_nom_etat.Enable(self.rw)
        #fin _set_properties

    def __do_layout(self):
        gridsizer_BASE = wx.FlexGridSizer(rows=7, cols=1, vgap=0, hgap=0)
        gridsizer_BASE.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)

        staticsizer_TIERS = wx.StaticBoxSizer(self.staticbox_TIERS, wx.VERTICAL)
        gridsizer_TIERS = wx.FlexGridSizer(rows=2, cols=1, vgap=0, hgap=0)
        gridsizer_TIERShaut = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        gridsizer_TIERShaut.Add(self.label_individu, 1, wx.LEFT, 15)
        gridsizer_TIERShaut.Add(self.ctrl_nom_individu, 1, wx.LEFT|wx.EXPAND, 0)
        gridsizer_TIERShaut.AddGrowableCol(1)
        gridsizer_TIERS.Add(gridsizer_TIERShaut, 1, wx.BOTTOM|wx.EXPAND, 5)

        gridsizer_TIERSbas = wx.FlexGridSizer(rows=2, cols=3, vgap=5, hgap=5)
        gridsizer_TIERSbas.Add(self.label_famille, 1, wx.LEFT, 15)
        gridsizer_TIERSbas.Add(self.ctrl_nom_famille, 1, wx.LEFT|wx.EXPAND, 15)
        gridsizer_TIERSbas.Add(self.bouton_famille, 1, wx.LEFT, 10)
        gridsizer_TIERSbas.Add(self.label_payeur, 1, wx.LEFT, 15)
        gridsizer_TIERSbas.Add(self.ctrl_nom_payeur, 1, wx.LEFT|wx.EXPAND, 15)
        gridsizer_TIERSbas.AddGrowableCol(1)
        gridsizer_TIERS.Add(gridsizer_TIERSbas, 1,wx.BOTTOM|wx.EXPAND, 5)
        gridsizer_TIERS.AddGrowableCol(0)
        staticsizer_TIERS.Add(gridsizer_TIERS, 1, wx.RIGHT|wx.EXPAND,5)
        gridsizer_BASE.Add(staticsizer_TIERS, 1,wx.ALL|wx.EXPAND, 3)

        gridsizer_CAMP = wx.FlexGridSizer(rows=1, cols=2, vgap=0, hgap=0)
        staticsizer_CAMPgauche = wx.StaticBoxSizer(self.staticbox_CAMPgauche, wx.VERTICAL)
        gridsizer_CAMPgauche = wx.FlexGridSizer(rows=3, cols=2, vgap=5, hgap=5)
        gridsizer_CAMPgauche.Add(self.label_activite, 1, wx.LEFT,15)
        gridsizer_CAMPgauche.Add(self.ctrl_nom_activite, 1, wx.TOP|wx.EXPAND, 0)
        gridsizer_CAMPgauche.Add(self.label_groupe, 1, wx.LEFT, 15)
        gridsizer_CAMPgauche.Add(self.ctrl_nom_groupe, 1, wx.LEFT|wx.EXPAND, 0)
        gridsizer_CAMPgauche.Add(self.label_tarif, 1, wx.LEFT, 15)
        gridsizer_CAMPgauche.Add(self.ctrl_nom_tarif, 1, wx.LEFT|wx.EXPAND, 0)
        gridsizer_CAMPgauche.AddGrowableCol(1)
        staticsizer_CAMPgauche.Add(gridsizer_CAMPgauche, 1, wx.RIGHT|wx.EXPAND,10)
        gridsizer_CAMP.Add(staticsizer_CAMPgauche, 1, wx.BOTTOM|wx.EXPAND, 5)

        gridsizer_CAMPdroite = wx.FlexGridSizer(rows=1, cols=1, vgap=5, hgap=5)
        gridsizer_CAMPdroite.Add(self.bouton_activite, 1, wx.TOP, 30)
        gridsizer_CAMP.Add(gridsizer_CAMPdroite, 1, wx.ALL, 5)

        gridsizer_CAMP.AddGrowableCol(0)
        gridsizer_BASE.Add(gridsizer_CAMP, 1,wx.ALL|wx.EXPAND, 3)

        staticsizer_PRIX = wx.StaticBoxSizer(self.staticbox_PRIX, wx.VERTICAL)
        gridsizer_PRIX = wx.FlexGridSizer(rows=1, cols=6, vgap=5, hgap=5)
        gridsizer_PRIX.Add(self.label_prix1, 1, wx.LEFT, 10)
        gridsizer_PRIX.Add(self.ctrl_prix1, 1, wx.LEFT|wx.EXPAND, 0)
        gridsizer_PRIX.Add(self.bouton_prix1, 1, wx.LEFT, 0)
        gridsizer_PRIX.Add(self.label_prix2, 1, wx.LEFT, 10)
        gridsizer_PRIX.Add(self.ctrl_prix2, 1, wx.LEFT|wx.EXPAND, 0)
        gridsizer_PRIX.Add(self.bouton_prix2, 1, wx.LEFT, 0)
        staticsizer_PRIX.Add(gridsizer_PRIX, 1, wx.RIGHT|wx.EXPAND,0)
        gridsizer_PRIX.AddGrowableCol(1)
        gridsizer_PRIX.AddGrowableCol(4)
        gridsizer_BASE.Add(staticsizer_PRIX, 1,wx.ALL|wx.EXPAND, 3)

        gridsizer_PIECE = wx.FlexGridSizer(rows=1, cols=2, vgap=0, hgap=0)
        staticsizer_PIECEgauche = wx.StaticBoxSizer(self.staticbox_PIECEgauche, wx.VERTICAL)
        gridsizer_PIECEgauche = wx.FlexGridSizer(rows=3, cols=2, vgap=5, hgap=5)
        gridsizer_PIECEgauche.Add(self.label_nature, 1, wx.LEFT,15)
        gridsizer_PIECEgauche.Add(self.ctrl_nom_nature, 1, wx.TOP, 0)
        gridsizer_PIECEgauche.Add(self.label_etat, 1, wx.LEFT, 15)
        gridsizer_PIECEgauche.Add(self.ctrl_nom_etat, 1, wx.LEFT|wx.EXPAND, 0)
        gridsizer_PIECEgauche.AddGrowableCol(1)
        staticsizer_PIECEgauche.Add(gridsizer_PIECEgauche, 1, wx.RIGHT|wx.EXPAND,10)
        gridsizer_PIECE.Add(staticsizer_PIECEgauche, 1, wx.BOTTOM|wx.EXPAND, 5)
        gridsizer_PIECEdroite = wx.FlexGridSizer(rows=1, cols=1, vgap=5, hgap=5)
        gridsizer_PIECEdroite.Add(self.bouton_piece, 1, wx.TOP, 15)
        gridsizer_PIECE.Add(gridsizer_PIECEdroite, 1, wx.ALL, 5)
        gridsizer_PIECE.AddGrowableCol(0)
        gridsizer_BASE.Add(gridsizer_PIECE, 1,wx.ALL|wx.EXPAND, 3)

        staticsizer_CONTENU = wx.StaticBoxSizer(self.staticbox_CONTENU, wx.VERTICAL)
        gridsizer_CONTENU = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)
        gridsizer_CONTENU.Add(self.label_commentaire, 1, wx.LEFT, 10)
        gridsizer_CONTENU.Add(self.txt_commentaire, 1, wx.LEFT|wx.EXPAND, 0)
        gridsizer_CONTENU.Add(self.label_infos, 1, wx.LEFT, 10)
        gridsizer_CONTENU.Add(self.choice_infos, 1, wx.LEFT|wx.EXPAND, 0)
        gridsizer_CONTENU.AddGrowableCol(1)
        staticsizer_CONTENU.Add(gridsizer_CONTENU, 1, wx.RIGHT|wx.EXPAND,0)
        gridsizer_BASE.Add(staticsizer_CONTENU, 1,wx.ALL|wx.EXPAND, 3)

        gridsizer_BOUTONS = wx.FlexGridSizer(rows=1, cols=5, vgap=10, hgap=10)
        staticsizer_BOUTONS = wx.StaticBoxSizer(self.staticbox_BOUTONS, wx.VERTICAL)
        gridsizer_BOUTONS.Add(self.bouton_avoir, 0, 0, 0)
        gridsizer_BOUTONS.Add((15, 15), 0, 0, 0)
        gridsizer_BOUTONS.Add(self.bouton_ok, 0, 0, 0)
        gridsizer_BOUTONS.Add(self.bouton_annuler, 0, 0, 0)
        gridsizer_BOUTONS.AddGrowableCol(1)
        staticsizer_BOUTONS.Add(gridsizer_BOUTONS, 1, wx.RIGHT|wx.EXPAND, 10)
        gridsizer_BASE.Add(staticsizer_BOUTONS, 1, wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

        self.SetSizer(gridsizer_BASE)
        gridsizer_BASE.Fit(self)
        gridsizer_BASE.AddGrowableRow(5)
        gridsizer_BASE.AddGrowableCol(0)
        self.Layout()
        self.CentreOnScreen()
        #fin do_layout

    def GetNomsNatureEtat(self,dictDonnees):
        nature, etat = "",""
        IDnature,i = 0,0
        self.naturePiece = dictDonnees["nature"]
        for a,b,c in self.liste_naturesPieces:
            if a == self.naturePiece:
                nature = b
                IDnature=i
            i+=1
        codeEtat = dictDonnees["etat"][IDnature]
        for a,b,c in self.liste_etatsPieces:
            if a == codeEtat: etat = dictDonnees["etat"]+" "+b+" : "+ c
        return nature, etat
        #fin GetNomsNatureEtat

    def AffichePrix2(self):
        prix = 0.00
        listeLignes = self.dictDonnees["lignes_piece"]
        for dictLigne in listeLignes:
            prix += dictLigne["montant"]
        self.ctrl_prix2.SetValue(str("{:10.2f}".format((prix))))
        if self.dictDonnees["nature"] == "AVO":
            self.ctrl_prix2.SetValue("0")

    def On_ctrl_nom_nature(self, event):
            self.ctrl_nom_nature.Enable(False)
            msg = GestionDB.Messages()
            msg.Box(message = "Pour modifier l'état de la pièce il faut passer par le bouton plus à droite !")

    def On_ctrl_activite(self, event):
            self.ctrl_nom_activite.Enable(False)
            self.ctrl_nom_groupe.Enable(False)
            self.ctrl_nom_tarif.Enable(False)
            msg = GestionDB.Messages()
            msg.Box(message = "Pour modifier les éléments de l'activité il faut passer par le bouton plus à droite !")

    def On_ctrl_prix2(self, event):
            self.ctrl_prix2.Enable(False)
            msg = GestionDB.Messages()
            msg.Box(message = "Pour modifier les éléments de prix il faut passer par le bouton plus à droite !")

    def On_activite(self, event):
        self.ctrl_nom_activite.Enable(True)
        self.ctrl_nom_groupe.Enable(True)
        self.ctrl_nom_tarif.Enable(True)
        fGest = GestionInscription.Forfaits(self.parent)
        # Ouverture de la fenêtre d'inscription choix de l'activité, groupe, catTarif
        dlg = DLG_Inscription.Dialog(self,IDindividu=self.IDindividu)
        dlg.SetFamille(self.listeNoms, self.listeFamille, self.IDfamille, False)
        choixInscription = dlg.ShowModal()
        if choixInscription != wx.ID_OK:
            dlg.Destroy()
            return
        IDgroupe =  dlg.GetIDgroupe()
        IDcategorie_tarif = dlg.GetIDcategorie()
        if IDgroupe == None or IDcategorie_tarif == None :
            GestionDB.MessageBox(self,u"Pour une inscription il faut préciser une activité, un groupe et une catégorie de tarif!\nIl y a aussi la possibilité de facturer sans inscription")
            dlg.Destroy()
            return
        nom_activite = dlg.GetNomActivite()
        nom_groupe = dlg.GetNomGroupe()
        nom_categorie = dlg.GetNomCategorie()
        self.ctrl_nom_activite.SetValue(nom_activite)
        self.ctrl_nom_groupe.SetValue(nom_groupe)
        self.ctrl_nom_tarif.SetValue(nom_categorie)
        self.IDactivite = dlg.GetIDactivite()
        self.IDcompte_payeur = fGest.GetPayeurFamille(self,self.IDfamille)
        commentaire = Decod(self.dictDonnees["commentaire"])
        commentaire = str(datetime.date.today()) + " Modifié: " + nom_activite + "-" + nom_groupe + "\n" + commentaire
        self.listeDonnees = [
            ("IDactivite", self.IDactivite),
            ("IDgroupe", IDgroupe),
            ("IDcategorie_tarif", IDcategorie_tarif),
            ("commentaire", commentaire),
            ]
        self.txt_commentaire.SetValue(commentaire)
        self.dictDonnees = fGest.ModifDictDonnees(self,self.listeDonnees)
        self.modifPrestations = True
        self.modifConsommations = True
        self.modifInscriptions = True
        self.modifPieces = True

    def On_prix1(self, event):
        origine = self.dictDonneesOrigine["origine"]
        self.dictDonneesOrigine["origine"]= "lecture"
        fTar = DLG_PrixActivite.DlgTarification(self,self.dictDonneesOrigine)
        fTar.ShowModal()
        self.dictDonneesOrigine["origine"]= origine

    # récupération des lignes de l'inscription génération de la piece
    def On_prix2(self, event):
        self.dictDonnees["origine"]= "modif"
        fTar = DLG_PrixActivite.DlgTarification(self,self.dictDonnees)
        tarification = fTar.ShowModal()
        if not(tarification == wx.ID_OK): return
        etatPiece = self.dictDonneesOrigine["etat"]
        listeLignesPiece = fTar.listeLignesPiece
        self.nbreJours = fTar.nbreJours
        #la nature de pièce a changé
        if (self.naturePiece != fTar.codeNature) and (fTar.codeNature != None):
            self.naturePiece = fTar.codeNature
            self.dictDonnees["nature"] = self.naturePiece
            i = self.liste_codesNaturePiece.index(self.naturePiece)
            # Mise à "1" du caractère en la position correspondant à la nature de la pièce (ex: FAC = 4eme)
            etatPiece = etatPiece[:i]+"1"+ etatPiece[i+1:]
            self.dictDonnees["etat"] = etatPiece
            nature, etat = self.GetNomsNatureEtat(self.dictDonnees)
            self.ctrl_nom_nature.SetValue(nature)
            self.ctrl_nom_etat.SetValue(etat)
            commentaire = Decod(self.dictDonnees["commentaire"])
            commentaire = str(datetime.date.today()) + " Nature: " + nature + "\n" + commentaire
            self.dictDonnees["commentaire"] = commentaire
            self.txt_commentaire.SetValue(commentaire)
        #si le montant a changé
        if self.dictDonnees["lignes_piece"] != listeLignesPiece:
            self.dictDonnees["lignes_piece"] = listeLignesPiece
            self.dictDonnees["nbreJours"] = self.nbreJours
            self.AffichePrix2()
            commentaire = Decod(self.dictDonnees["commentaire"])
            commentaire = str(datetime.date.today()) + " Montant modifié "+ "\n" + commentaire
            self.dictDonnees["commentaire"] = commentaire
            self.txt_commentaire.SetValue(commentaire)
        # récup parrainage
        self.dictDonnees["IDparrain"] = fTar.IDparrain
        self.dictDonnees["parrainAbandon"] = fTar.parrainAbandon
        self.modifPrestations = True
        self.modifPieces = True

    def On_piece(self, event):
        fGest = GestionInscription.Forfaits(self.parent)
        self.ctrl_nom_nature.Enable(True)
        interroChoix = wx.ID_CANCEL
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_factures", "creer")  :
            dlg = DLG_ValidationPiece.Dialog(self,"modif")
            interroChoix = dlg.ShowModal()
            self.codeNature = dlg.codeNature
            #dlg.Destroy()
        if interroChoix != wx.ID_OK :
            return
        etatPiece = self.dictDonnees["etat"]
        i = self.liste_codesNaturePiece.index(self.codeNature)
        # Mise à "1" du caractère en la position correspondant à la nature de la pièce (ex: FAC = 4eme)
        etatPiece = etatPiece[:i]+"1"+ etatPiece[i+1:]
        self.dictDonnees["etat"] = etatPiece
        commentaire = Decod(self.dictDonnees["commentaire"])
        commentaire = str(datetime.date.today()) + " Nature: " + self.codeNature + "\n" + commentaire
        self.dictDonnees["commentaire"] = commentaire
        self.txt_commentaire.SetValue(commentaire)
        self.listeDonnees = [
            ("nature", self.codeNature),
            ("etat", etatPiece),
            ]
        self.dictDonnees = fGest.ModifDictDonnees(self,self.listeDonnees)
        nature,etat = self.GetNomsNatureEtat(self.dictDonnees)
        self.ctrl_nom_nature.SetValue(nature)
        self.ctrl_nom_etat.SetValue(etat)
        self.modifPrestations = True
        self.modifConsommations = True
        self.modifPieces = True
        #fin OnPiece

    def On_commentaire(self, event):
        fGest = GestionInscription.Forfaits(self.parent)
        self.listeDonnees = [
            ("commentaire", self.txt_commentaire.GetValue()),
            ]
        self.dictDonnees = fGest.ModifDictDonnees(self,self.listeDonnees)        
        self.modifPieces = True
"""

# -------------------------  pour tests ------------------------------
class Parent(wx.Dialog):
    def __init__(self, selection):
        wx.Dialog.__init__(self, None, -1, style=wx.DEFAULT_DIALOG_STYLE)
        self.selection = selection

if __name__ == "__main__":
    app = wx.App(0)
    listeDonnees = [
        ("IDinscription", None),
        ("IDindividu", 15004),
        ("IDfamille", 6546),
        ("origine", "lecture"),
        ("etat", "00000"),
        ("IDactivite", 479),
        ("IDgroupe", 1147),
        ("IDcategorie_tarif", 1109),
        ("IDcompte_payeur", 6546),
        ("date_inscription", "2018-01-01"),
        ("parti", False),
        ("nature", "COM"),
        ("nom_activite", "Sejour 41 Mon activite"),
        ("nom_groupe", "Groupe Pasto Plus"),
        ("nom_payeur", "celui qui paye"),
        ("nom_categorie_tarif", "Tarif Normal"),
        ("nom_individu", "nom de  l'individu"),
        ("commentaire", "differents commentaires"),
        ("nom_famille", "nom de la famille"),
        ("lignes_piece",[{'utilisateur': 'NoName', 'quantite': 1.0, 'montant': 800.0, 'codeArticle': 'SEJ_CORSE_S1', 'libelle': 'Sejour Jeunes Corse S1', 'IDnumPiece': 10, 'prixUnit': 500.0, 'date': '2016-07-27', 'IDnumLigne': 190}, {'utilisateur': 'NoName', 'quantite': 1.0, 'montant': 10.0, 'codeArticle': 'ZLUN', 'libelle': 'Option lunettes de soleil', 'IDnumPiece': 10, 'prixUnit': 10.0, 'date': '2016-07-27', 'IDnumLigne': 191}, {'utilisateur': 'NoName', 'quantite': 1.0, 'montant': 90.0, 'codeArticle': 'ART4', 'libelle': 'Quatrieme article', 'IDnumPiece': 10, 'prixUnit': 90.0, 'date': '2016-07-27', 'IDnumLigne': 192}]),
        ]
    dictFamillesRattachees ={6546: {'listeNomsTitulaires': ['BONI Julien', 'BONI DESCLAUX Christelle'], 'nomsTitulaires': 'BONI Julien et BONI DESCLAUX Christelle', 'IDcompte_payeur': 6546, 'nomCategorie': 'enfant', 'IDcategorie': 2}}
    parent = Parent(None)
    IDindividu = 15004
    dictDonnees = {}
    listeChamps = []
    listeValeurs = []
    for donnee in listeDonnees:
        champ = donnee[0]
        valeur = donnee[1]
        dictDonnees[champ] = valeur
        listeChamps.append(champ)
        listeValeurs.append(valeur)
    dlg = DlgMenu(parent,dictDonnees,'ajouter',IDindividu=IDindividu, dictFamillesRattachees=dictFamillesRattachees)
    app.SetTopWindow(dlg)
    dlg.ShowModal()
    app.MainLoop()
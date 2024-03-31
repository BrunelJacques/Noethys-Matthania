#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:          Ivan LUCAS, JB, Jacques Brunel
# Licence:         Licence GNU GPL
# Gestion de la piece en modifiction
# Adapt� � partir de DLG_InscriptionModif
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
            else: GestionDB.MessageBox(self, "Vous ne disposez pas de droits pour cr�er des individus_inscriptions")


        if mode == "supprimer":
            if droitCreation: self.Supprimer()
            else: GestionDB.MessageBox(self, "Vous ne disposez pas de droits pour cr�er des individus_inscriptions")

        if len(selection) >0:
            self.VerifTransports()
        self.DB.Close()

    def VerifTransports(self):
        # Checkpoint pour tracker des pertes d'info constat�es, � des fins de d�bug
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
                    mess += "Un transport Aller a �t� envisag� pour %6.2f�, mais son d�tail a disparu!\n" % float(Nz(prixAller))
                if Nz(IDpieRetour) > 0 and Nz(IDtrspRetour) == 0:
                    mess += "Un transport Retour a �t� envisag� pour %6.2f�, mais son d�tail a disparu!\n" % float(Nz(prixAller))
            if len(mess) > 0:
                mess1 = "Perte d'info constat�e\n\n" + mess
                mess1 += "\nM�morisez votre action et d�crivez-l� dans le rapport de bug que nous allons provoquer"
                ret = wx.MessageBox(mess1,"Erreur provoqu�e",style=wx.ICON_ERROR)
                raise Exception("IDinscription %d, IDtransport dans pi�ce non trouv� dans table transports" % IDinscription)

    def ChoixInscription(self):
        # Choix de la famille si multi (ajout� pour forcer un choix si plusieurs possibles)
        fGest = GestionInscription.Forfaits(self,DB=self.DB)
        if not fGest.GetFamille(self):
            self.Destroy()
        # Ouverture de la fen�tre d'inscription choix de l'activit�, groupe, catTarif
        dlg = DLG_Inscription.Dialog(self,IDindividu=self.IDindividu)
        dlg.SetFamille(self.listeNoms, self.listeFamille, self.IDfamille, False)
        choixInscription = dlg.ShowModal()
        if choixInscription != wx.ID_OK:
            return wx.ID_ABORT
        self.IDactivite = dlg.GetIDactivite()
        # V�rifie que l'individu n'est pas d�j� inscrit � cette activite
        for inscription in self.parent.listeListeView :
            if inscription.IDactivite == self.IDactivite and inscription.IDindividu == self.IDindividu :
                dlg2 = wx.MessageDialog(self, _("Cet individu est d�j� inscrit � l'activit� '%s' !") % inscription.nom_activite, _("Erreur de saisie"), wx.OK | wx.ICON_ERROR)
                dlg2.ShowModal()
                dlg2.Destroy()
                return
        IDgroupe =  dlg.GetIDgroupe()
        IDcategorie_tarif = dlg.GetIDcategorie()
        if IDgroupe == None or IDcategorie_tarif == None :
            GestionDB.MessageBox(self,"Pour une inscription il faut pr�ciser une activit�, un groupe et une cat�gorie de tarif!\nIl y a aussi la possibilit� de facturer ici sans inscription")
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
            ("commentaire", str(datetime.date.today()) + " Activit�: " + dlg.GetNomActivite() + "Groupe: " + dlg.GetNomGroupe()+ "\nCampeur : " + self.dictDonnees["nom_individu"]+ " | Famille : " + self.dictDonnees["nom_famille"]),
            ]
        self.dictDonnees = fGest.ModifDictDonnees(self,ajoutListe)
        dlg.Destroy()
        self.inscriptionChoisie = True
        return wx.ID_OK
        #fin ChoixInscription

    def SetInscription(self):
        # Enregistre l'inscription fa�on noethys
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
        # Tarification MATTHANIA � la place de Saisie des forfaits_auto NOETHYS
        fTar = DLG_PrixActivite.DlgTarification(self,self.dictDonnees)
        tarification =fTar.ShowModal()

        # r�cup�ration des lignes de l'inscription g�n�ration de la piece
        self.naturePiece =fTar.codeNature
        listeLignesPiece = fTar.listeLignesPiece
        self.nbreJours = fTar.nbreJours

        #recherche des codes nature pour calcul de l'�tat
        listeCodesNature = []
        for item in GestionArticle.LISTEnaturesPieces :
            listeCodesNature.append(item[0])
        if (tarification == wx.ID_OK) and (self.naturePiece in listeCodesNature):
            etatPiece = "00000"
            i = listeCodesNature.index(self.naturePiece)
            # Mise � "1" du caract�re en la position correspondant � la nature de la pi�ce (ex: FAC = 4eme)
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

            # Gestion des compl�ments transport cotisation et reduction famille
            fTransp = DLG_InscriptionComplements.DlgTransports(self.dictDonnees)
            transports =fTransp.ShowModal()
            self.dictDonnees = fTransp.CompleteDictDonnees(self.dictDonnees)
            if transports != wx.ID_OK:
                self.dictDonnees["prixTranspAller"] = None
                self.dictDonnees["prixTranspRetour"] = None
                self.dictDonnees["IDtranspAller"] = None
                self.dictDonnees["IDtranspRetour"] = None
            else:
                fGest.ModifiePieceCree(self,self.dictDonnees)
            fTransp.Destroy()

            # si seulement r�servation on saute l'enregistrement de prestation
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
        #la cl� 'coches' pr�cise s'il faut tout d�cocher les articles ou pas
        self.dictDonnees['coches'] = True
        ret = self.AppliquerTarif()
        self.Historise("AjoutInscription")
        return ret
        #fin Ajouter

    def AjouterPiece(self, razConsos = False):
        # se distingue de Ajouter car on cr�e une nouvelle pi�ce alors qu'il en existe d'autres qui ont d�j� �t� factur�es et non modifiables,
        # on a ajout� des lignes � l'inscription mais c'est dans une nouvelle pi�ce.
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
        #tests pr�alables
        if len(self.selection) == 0 :
            GestionDB.MessageBox(self, "Vous n'avez s�lectionn� aucune inscription � modifier dans la liste")
            return
        select = self.selection[0]
        self.IDinscription = select.IDinscription
        fGest = GestionInscription.Forfaits(self,self.DB)
        reqPiece = fGest.GetPieceModif(self,select.IDindividu,select.IDactivite,DB=self.DB)
        # GetPieceModif False pour abandon, None pour absence de piece, True pour self.dictPiece aliment�e
        if reqPiece == None:
            GestionDB.MessageBox(self, _("Pas de pi�ce associ�e � cette inscription!\nLa modification est impossible"))
            fGest.NeutraliseReport(select.IDfamille, select.IDindividu, select.IDactivite)

            return
        if reqPiece == False:
            return

        # pr�sence d'une pi�ce point�e dans fGest
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
                    texte = "Par 'Facturation' une r�trogradation en commande est possible"
            GestionDB.MessageBox(self, "Factur� : seules les notes sont modifiables!\n" + texte,titre="Information")
            self.dictDonneesOrigine["origine"]= "consult"
        #appel du dialogue de modification et r�cup de la saisie des donn�es
        modif = fMod.ShowModal()

        # retour sur validation des modifs
        if modif == wx.ID_OK:
            self.dictDonnees = fMod.dictDonnees
            fMod.Destroy()
            self.Historise("ModificationInscription")
            # V�rifier pour confirmer les r�ductions li�es aux inscriptions...
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
        #retour sur nouvelle pi�ce

        elif modif == wx.ID_APPLY:
            # Cas d'un ajout de lignes compl�mentaires � la facture principale de l'activit�
            self.dictDonnees = fMod.dictDonnees
            self.AjouterPiece(razConsos=True)

        elif modif == wx.ID_BOTTOM:
            # Cas de la g�n�ration d'un avoir global de la pi�ce
            self.dictDonnees = fMod.dictDonnees
            fMod.Destroy()
            self.Historise("AvoirG�n�r�")
            # V�rifier pour confirmer les r�ductions li�es aux inscriptions...
            fFam = DLG_PrixFamille.DlgTarification(self,self.dictDonnees,fromIndividu=True,fromAvoir=True)
            ret = fFam.ShowModal()
        #fin Modifier

    def Supprimer(self):
        if len(self.selection) == 0 :
            GestionDB.MessageBox(self, _("Vous n'avez s�lectionn� aucune inscription � supprimer dans la liste"))
            return
        for select in self.selection:
            # Gestion du type de suppression
            fGest = GestionInscription.Forfaits(self,DB=self.DB)
            reqPiece = fGest.GetPieceSupprime(self,select.IDinscription,select.IDindividu,select.IDactivite)
            #GetPieceSupprime retourne False pour abandon, None pour suppresion sans piece, True pour self.dictPiece aliment�e
            if reqPiece == None:
                # pas de pi�ce
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
                    GestionDB.MessageBox(self, "Facture bloqu�e, ne peut pas �tre supprim�e!\nElle est consultable et peut faire l'objet d'un avoir")
                    continue
                if self.dictDonnees['nature'] in ['FAC','AVO'] :
                    GestionDB.MessageBox(self, "Une Facture doit d'abord �tre r�trograd�e en commande pour �tre supprim�e !\nElle est consultable et peut faire l'objet d'un avoir")
                    continue
                if len(list(self.dictDonnees.keys()))> 1:
                    dlg = wx.MessageDialog(self, _("Confirmez vous la suppression de %s  cr�e le %s par %s \n %s ")% (Decod(self.dictDonnees["nature"]),Decod(self.dictDonnees["dateCreation"]),Decod(self.dictDonnees["utilisateurCreateur"]),Decod(self.dictDonnees["commentaire"])), _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
                    if dlg.ShowModal() != wx.ID_YES:
                        continue
                    fGest.SuppressionPiece(self, self.dictDonnees)
                    self.Historise("SuppressionInscription")
                # V�rifier pour confirmer les r�ductions li�es aux inscriptions...
                fFam = DLG_PrixFamille.DlgTarification(self,self.dictDonnees,fromIndividu=True)
                fFam.ShowModal()
                fFam.Destroy()
        # Actualise l'affichage
        self.parent.MAJ()
        #fin Supprimer

    def Historise(self,action):
        fGest = GestionInscription.Forfaits(self,DB=self.DB)
        # M�morise l'action dans l'historique
        IDindividu = self.dictDonnees["IDindividu"]
        IDfamille = self.dictDonnees["IDfamille"]
        commentaire = Decod(self.dictDonnees["commentaire"])
        fGest.Historise(IDindividu,IDfamille,action, commentaire)

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
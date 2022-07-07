#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, compl�t� Matthania
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import Chemins
import sys
import GestionDB
import datetime
import os
import codecs
from Utils import UTILS_Fichiers

# ---- Fonctions usuelles-------------------------------
def GetPathRoot():
    return Chemins.GetMainPath("..")

def NoPunctuation(txt = ''):
    if not txt: return ''
    if txt.strip()== '': return ''
    import re
    punctuation = "!\"#$%&()*+,./:;<=>?@[\\]^_`{|}~"
    regex = re.compile('[%s]' % re.escape(punctuation))
    regex = regex.sub(' ', txt)
    return regex.replace('  ',' ')

def ChiffresSeuls(txt = ""):
    permis = "0123456789+-.,"
    new = ""
    for a in txt:
        if a in permis:
            new += a
    return new

def Supprime_accent(texte):
    if not texte: return
    liste = [ ("�", "e"), ("�", "e"), ("�", "e"), ("�", "e"), ("�", "a"), ("�", "u"), ("�", "o"),
              ("�", "c"), ("�", "i"), ("�", "i"),("/", ""), ("\\", "")]
    txtLow = texte.lower()
    for a, b in liste :
        if not a in txtLow: continue
        texte = texte.replace(a, b)
        texte = texte.replace(a.upper(), b.upper())
    return texte

def ListeToStr(lst=[], separateur=", "):
    # Convertit une liste en texte
    chaine = separateur.join([str(x) for x in lst])
    if chaine == "": chaine = "*"
    return chaine

# ----- Fonctions affichage -----------------------------
def GetAttente(parent=None,mess="Travail en cours",titre="Veuillez patienter..."):
    # parent doit �tre une fen�tre graphique wx
    busy = wx.lib.agw.pybusyinfo.PyBusyInfo
    return busy(mess, title=titre,
                icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"),
                               wx.BITMAP_TYPE_ANY),
                parent = parent,
                )

def BoucleFrameOuverte(nom, WindowEnCours) :
    """ Est utilis�e dans FrameOuverte """
    for children in WindowEnCours.GetChildren():
        if children.GetName() == nom : return children
        if len(children.GetChildren()) > 0 :
            tmp = BoucleFrameOuverte(nom, children)
            if tmp != None : return tmp
    return None

def FrameOuverte(nom) :
    """ Permet de savoir si une frame est ouverte ou pas..."""
    topWindow = wx.GetApp().GetTopWindow() 
    # Analyse le TopWindow
    if topWindow.GetName() == nom : return True
    # Analyse les enfants de topWindow
    reponse = BoucleFrameOuverte(nom, topWindow)
    return reponse

# modifie le wx.StaticText pour g�rer le redimensionnement
class StaticWrapText(wx.StaticText):
    """A StaticText-like widget which implements word wrapping."""
    def __init__(self, *args, **kwargs):
        wx.StaticText.__init__(self, *args, **kwargs)

        # store the initial label
        self.__label = super(StaticWrapText, self).GetLabel()

        # listen for sizing events
        self.Bind(wx.EVT_SIZE, self.OnSize)
        
    def SetLabel(self, newLabel):
        """Store the new label and recalculate the wrapped version."""
        self.__label = newLabel
        self.__wrap()

    def GetLabel(self):
        """Returns the label (unwrapped)."""
        return self.__label
    
    def __wrap(self):
        """Wraps the words in label."""
        words = self.__label.split()
        lines = []

        # get the maximum width (that of our parent)
        max_width = self.GetParent().GetVirtualSizeTuple()[0]-20 # J'ai ajout� le -20 ici
        
        index = 0
        current = []

        for word in words:
            current.append(word)

            if self.GetTextExtent(" ".join(current))[0] > max_width:
                del current[-1]
                lines.append(" ".join(current))

                current = [word]

        # pick up the last line of text
        lines.append(" ".join(current))

        # set the actual label property to the wrapped version
        super(StaticWrapText, self).SetLabel("\n".join(lines))

        # refresh the widget
        self.Refresh()
        
    def OnSize(self, event):
        # dispatch to the wrap method which will 
        # determine if any changes are needed
        self.__wrap()
        self.GetParent().Layout()

# ------------------------------------------------------------------------

def Creation_liste_pb_personnes():
    """ Cr�ation de la liste des probl�mes des personnes """
    listeIDpersonne = Recherche_ContratsEnCoursOuAVenir()
    dictNomsPersonnes, dictProblemesPersonnes = Recherche_problemes_personnes(listeIDpersonnes = tuple(listeIDpersonne))
    return dictNomsPersonnes, dictProblemesPersonnes
                
def Recherche_problemes_personnes(listeIDpersonnes = (), infosPersonne=[]):
    """ Recherche les probl�mes dans les dossiers des personnes """
    
    dictProblemes = {}
    dictNoms = {}
    
    #
    # Analyse des fiches individuelles
    #
    
    if len(listeIDpersonnes) == 0 : listeIDpersonnesTmp = "(100000)"
    elif len(listeIDpersonnes) == 1 : listeIDpersonnesTmp = "(%d)" % listeIDpersonnes[0]
    else : listeIDpersonnesTmp = str(tuple(listeIDpersonnes))
    
    DB = GestionDB.DB()        
    req = """SELECT IDpersonne, civilite, nom, nom_jfille, prenom, date_naiss, cp_naiss, ville_naiss, pays_naiss, nationalite, num_secu, adresse_resid, cp_resid, ville_resid, IDsituation
    FROM personnes WHERE IDpersonne IN %s ORDER BY nom; """ % listeIDpersonnesTmp
    DB.executerReq(req)
    listePersonnes = DB.resultatReq()
    
    # R�cup�re ici les infos directement dans les contr�les de la fiche individuelle
    if len(infosPersonne) != 0 :
        listePersonnes = infosPersonne

    for personne in listePersonnes :
        IDpersonne = personne[0]
        civilite = personne[1]
        nom = personne[2]
        nom_jfille = personne[3]
        prenom = personne[4]
        date_naiss = personne[5]
        cp_naiss = personne[6]
        ville_naiss = personne[7]
        pays_naiss = personne[8]
        nationalite = personne[9]
        num_secu = personne[10]
        adresse_resid = personne[11]
        cp_resid = personne[12]
        ville_resid = personne[13]
        IDsituation = personne[14]
        
        dictNoms[IDpersonne] = nom + " " + prenom
        problemesFiche = []
        
        # Civilit�
        if civilite == "" or civilite == None : problemesFiche.append( ("Civilit�") )
        # Nom
        if nom == "" or nom == None : problemesFiche.append( ("Nom de famille") )
        # Nom de jeune fille
        if civilite == "Mme" :
            if nom_jfille == "" or nom_jfille == None : problemesFiche.append( ("Nom de jeune fille") )
        # Pr�nom
        if prenom == "" or prenom == None : problemesFiche.append( ("Pr�nom") )
        # Date de naissance
        if str(date_naiss).strip(" ") == "" or date_naiss == None : problemesFiche.append( ("Date de naissance") )
        # CP_naissance
        if str(cp_naiss).strip(" ") == "" or cp_naiss == None : problemesFiche.append( ("Code postal de la ville de naissance") )
        # Ville de naissance
        if ville_naiss == "" or ville_naiss == None : problemesFiche.append( ("Ville de naissance") )
        # Pays de naissance
        if pays_naiss == "" or pays_naiss == None or pays_naiss == 0 : problemesFiche.append( ("Pays de naissance") )
        # Nationalite
        if nationalite == "" or nationalite == None or nationalite == 0 : problemesFiche.append( ("Nationalit�") )
        # Num S�cu
        if str(num_secu).strip(" ") == "" or num_secu == None : problemesFiche.append( ("Num�ro de s�curit� sociale") )
        # Adresse r�sidence
        if adresse_resid == "" or adresse_resid == None : problemesFiche.append( ("Adresse de r�sidence") )
        # Code postal r�sidence
        if str(cp_resid).strip(" ") == "" or cp_resid == None : problemesFiche.append( ("Code postal de r�sidence") )
        # Ville r�sidence
        if ville_resid == "" or ville_resid == None : problemesFiche.append( ("Ville de r�sidence") )
        # Situation
        if IDsituation == "" or IDsituation == None or IDsituation == 0 : problemesFiche.append( ("Situation sociale") )

    
        # Analyse des coordonn�es
        req = """SELECT IDcoord
        FROM coordonnees
        WHERE IDpersonne=%d;
        """ % IDpersonne
        DB.executerReq(req)
        listeCoords = DB.resultatReq()
        
        if len(listeCoords) == 0 : 
            problemesFiche.append( ("Coordonn�es t�l�phoniques") )
        
        # Met les donn�es dans le dictionnaire
        if len(problemesFiche) != 0 : 
            if (IDpersonne in dictProblemes) == False : dictProblemes[IDpersonne] = {}
            if len(problemesFiche) == 1 : 
                categorie = "1 information manquante"
            else:
                categorie = str(len(problemesFiche))  + " informations manquantes"
            dictProblemes[IDpersonne][categorie] = problemesFiche
            
    
    #
    # Analyse des pi�ces � fournir
    #
    
    date_jour = datetime.date.today()
    
    # Initialisation de la base de donn�es
    DB = GestionDB.DB()
        
    for IDpersonne in listeIDpersonnes :
        piecesManquantes = []
        piecesPerimees = []
        DictPieces = {}
        
        # Recherche des pi�ces SPECIFIQUES que la personne doit fournir...
        req = """
        SELECT types_pieces.IDtype_piece, types_pieces.nom_piece
        FROM diplomes INNER JOIN diplomes_pieces ON diplomes.IDtype_diplome = diplomes_pieces.IDtype_diplome INNER JOIN types_pieces ON diplomes_pieces.IDtype_piece = types_pieces.IDtype_piece
        WHERE diplomes.IDpersonne=%d;
        """ % IDpersonne
        DB.executerReq(req)
        listePiecesAFournir = DB.resultatReq()
        
        if type(listePiecesAFournir) != list :
            listePiecesAFournir = list(listePiecesAFournir)
        
        # Recherche des pi�ces BASIQUES que la personne doit fournir...
        req = """
        SELECT diplomes_pieces.IDtype_piece, types_pieces.nom_piece
        FROM diplomes_pieces INNER JOIN types_pieces ON diplomes_pieces.IDtype_piece = types_pieces.IDtype_piece
        WHERE diplomes_pieces.IDtype_diplome=0;
        """ 
        DB.executerReq(req)
        listePiecesBasiquesAFournir = DB.resultatReq()
        
        listePiecesAFournir.extend(listePiecesBasiquesAFournir)
        
        # Recherche des pi�ces que la personne poss�de
        req = """
        SELECT types_pieces.IDtype_piece, pieces.date_debut, pieces.date_fin
        FROM types_pieces LEFT JOIN pieces ON types_pieces.IDtype_piece = pieces.IDtype_piece
        WHERE (pieces.IDpersonne=%d AND pieces.date_debut<='%s' AND pieces.date_fin>='%s')
        ORDER BY pieces.date_fin;
        """ % (IDpersonne, date_jour, date_jour)
        DB.executerReq(req)
        listePieces = DB.resultatReq()
        dictTmpPieces = {}
        for IDtype_piece, date_debut, date_fin in listePieces :
            dictTmpPieces[IDtype_piece] = (date_debut, date_fin)
        
        # Passe en revue toutes les pi�ces � fournir et regarde si la personne poss�de les pi�ces correspondantes
        for IDtype_piece, nom_piece in listePiecesAFournir :
            if (IDtype_piece in dictTmpPieces) == True :
                date_debut = dictTmpPieces[IDtype_piece][0]
                date_fin = dictTmpPieces[IDtype_piece][1]
                # Recherche la validit�
                date_fin = datetime.date(int(date_fin[:4]), int(date_fin[5:7]), int(date_fin[8:10]))
                reste = str(date_fin - date_jour)
                if reste != "0:00:00":
                    jours = int(reste[:reste.index("day")])
                    if jours < 15  and jours > 0:
                        etat = "Attention"
                    elif jours <= 0:
                        etat = "PasOk"
                    else:
                        etat = "Ok"
                else:
                    etat = "Attention"
            else:
                etat = "PasOk"
            DictPieces[IDtype_piece] = (etat, nom_piece)
        

        for IDtype_piece, donnees in DictPieces.items() :
            etat, nom_piece = donnees
            if etat == "Ok": continue
            if etat == "PasOk" :
                piecesManquantes.append(nom_piece)
            if etat == "Attention" :
                piecesPerimees.append(nom_piece)

    
        # Met les listes de probl�mes dans un dictionnaire
        if len(piecesManquantes) != 0 : 
            if (IDpersonne in dictProblemes) == False : dictProblemes[IDpersonne] = {}
            if len(piecesManquantes) == 1 : 
                categorie = "1 pi�ce manquante"
            else:
                categorie = str(len(piecesManquantes))  + " pi�ces manquantes"
            dictProblemes[IDpersonne][categorie] = piecesManquantes

        if len(piecesPerimees) != 0 : 
            if (IDpersonne in dictProblemes) == False : dictProblemes[IDpersonne] = {}
            if len(piecesPerimees) == 1 : 
                categorie = "1 pi�ce bient�t p�rim�e"
            else:
                categorie = str(len(piecesPerimees))  + " pi�ces bient�t p�rim�es"
            dictProblemes[IDpersonne][categorie] = piecesPerimees
        
        
        # Analyse des contrats
        problemesContrats = []
        DB = GestionDB.DB()        
        req = """SELECT IDpersonne, signature, due
        FROM contrats 
        WHERE IDpersonne = %d
        ORDER BY date_debut;""" % IDpersonne
        DB.executerReq(req)
        listeContrats = DB.resultatReq()
        
        for contrat in listeContrats :
            signature = contrat[1]
            due = contrat[2]
            # Signature
            if signature == "" or signature == "Non" : 
                txt = "Contrat non sign�"
                problemesContrats.append( (txt) )
            # DUE
            if due == "" or due == "Non" : 
                txt = "DUE � faire"
                problemesContrats.append( (txt) )
        
        # Met les donn�es dans le dictionnaire
        if len(problemesContrats) != 0 : 
            if (IDpersonne in dictProblemes) == False : dictProblemes[IDpersonne] = {}
            if len(problemesContrats) == 1 : 
                categorie = "1 contrat � voir"
            else:
                categorie = str(len(problemesContrats))  + " contrats � voir"
            dictProblemes[IDpersonne][categorie] = problemesContrats
    

    # Fin de la fonction    
    DB.close()
    
##    print dictProblemes

    return dictNoms, dictProblemes

def Recherche_ContratsEnCoursOuAVenir() :
    """ Renvoie la liste des personnes qui ont ou vont avoir un contrat """
    # Recherche des contrats
    dateDuJour = str(datetime.date.today())
    DB = GestionDB.DB()        
    req = """SELECT contrats.IDpersonne, contrats_class.nom, contrats.date_debut, contrats.date_fin, contrats.date_rupture, contrats_types.duree_indeterminee
    FROM contrats INNER JOIN contrats_class ON contrats.IDclassification = contrats_class.IDclassification INNER JOIN contrats_types ON contrats.IDtype = contrats_types.IDtype
    WHERE contrats.date_fin>='%s'
    ORDER BY contrats.date_debut;""" % dateDuJour
    DB.executerReq(req)
    listeContrats = DB.resultatReq()
    DB.close()
    # Retourne la liste des IDpersonne
    if len(listeContrats) == 0 :
        return []
    else:
        listeIDpersonne = []
        for contrat in listeContrats :
            listeIDpersonne.append(contrat[0])
        return listeIDpersonne

# ----------------------------------------------------------------------------------------------------------------------------------------------------------

def EnvoyerMail(adresses = [], sujet="", message=""):
    """ Envoyer un Email avec le client de messagerie par d�faut """
    if len(adresses) == 1 :
        commande = "mailto:%s" % adresses[0]
    else:
        commande = "mailto:%s" % adresses[0] + "?"
        if len(adresses) > 1 :
            commande+= "bcc=%s" % adresses[1]
        for adresse in adresses[2:] :
            commande+= "&bcc=%s" % adresse
    if sujet != "" : 
        if len(adresses) == 1 : 
            commande += "?"
        else :
            commande += "&"
        commande += "subject=%s" % sujet
    if message != "" : 
        if len(adresses) == 1 and sujet == "" : 
            commande += "?"
        else:
            commande += "&"
        commande += "body=%s" % message
    #print commande
    import webbrowser
    webbrowser.open(commande)

# -----------------------------------------  Affiche l'aide -----------------------------------------------------------------------------------

def Aide(numItem=None):
    """ Appel du module d'aide de Windows """
    
##    # Demande le nom du fichier
##    import Aide
##    frm = Aide.Aide(None)
##    frm.ShowModal()
##    return
    
##    # ------- TEMPORAIRE : ---------------
##    txtMessage = _("Le syst�me d'aide n'est pas encore fonctionnel (actuellement en cours de r�daction).\n\nVous pouvez tout de m�me trouver actuellement de l'aide sur le forum de TeamWorks � l'adresse suivante : \nhttp://teamworks.forumactif.com (ou cliquez dans la barre de menu sur 'Aide' puis 'Acc�der au Forum').")
##    dlg = wx.MessageDialog(None, txtMessage, _("Aide"), wx.OK | wx.ICON_INFORMATION)
##    dlg.ShowModal()
##    dlg.Destroy()
##    return

    
    # -----------------------------------------------    
    nomPage = ""
    nomAncre = ""
    
    dictAide = {
        1 : ("Leplanning", "", "planning"),
        2 : ("ImprimeruneDUE", "", "Edition DUE"),
        3 : ("Envoyerunmailgroup", "", "Envoi mail group�"),
        4 : ("Creerunnouveaufichier", "", "Cr�er un nouveau fichier"),
        5 : ("Imprimerunelistedeprsences", "", "Impression d'une liste de pr�sences"),
        6 : ("Lescontrats", "", "Impression d'un contrat ou d'une DUE"),
        7 : ("Laprotectionparmotdepasse", "", "Saisie du mot de passe d'ouverture"),
        8 : ("Lescatgoriesdeprsences", "", "Config Cat�gories de pr�sences"),
        9 : ("Lespriodesdevacances", "", "Saisie d'une p�riode de vacances"),
        10 : ("Lestypesdecontrats", "", "Config types de contrats"),
        11 : ("Lescatgoriesdeprsences", "", "Saisie d'une cat de pr�sences"),
        12 : ("Personnes", "", "Panneau Personnes"),
        13 : ("Lesvaleursdepoints", "", "Saisie val point"),
        14 : ("Appliquerunmodledeprsences", "creer_modele", "Saisie d'un mod�le"),
        15 : ("Lespaysetnationalits", "", "Config pays"),
        16 : ("Lestypesdepices", "", "Config types pi�ces"),
        17 : ("Lasauvegardeautomatique", "", "Panel sauvegarde automatique"),
        18 : ("Creerunesauvegarde", "", "Cr�er une sauvegarde occasionnelle"),
        19 : ("Restaurerunesauvegarde", "", "Restaurer une sauvegarde"),
        20 : ("Leschampsdecontrats", "", "Saisie champs contrats"),
        21 : ("Ladresse", "", "Gestion des villes"),
        22 : ("Imprimerunefichedefrais", "", "Impression frais"),
        23 : ("Lespaysetnationalits", "", "Saisir un pays"),
        24 : ("Lestypesdesituations", "", "Config situations"),
        25 : ("Gestiondesfraisdedplacements", "", "Gestion des frais"),
        26 : ("Laprotectionparmotdepasse", "", "Config Password"),
        27 : ("Lesvaleursdepoints", "", "Config val_point"),
        28 : ("Rechercherdesmisesjour", "", "Updater"),
        29 : ("Crerunepice", "", "Saisie pi�ces"),
        30 : ("Imprimerdesphotosdepersonnes", "", "Impression_photo"),
        31 : ("Lesmodlesdecontrats", "", "wiz cr�ation modele contrat"),
        32 : ("Laprotectionparmotdepasse", "", "Saisie pwd"),
        33 : ("Saisirunetcheunique", "", "Saisie d'une pr�sence"),
        34 : ("Lesjoursfris", "", "Config jours f�ri�s"),
        35 : ("Leschampsdecontrats", "", "Config champs contrats"),
        36 : ("Enregistrerunremboursement", "", "Saisie remboursement"),
        37 : ("Imprimeruncontrat", "", "wiz �dition contrat"),
        38 : ("Lesclassifications", "", "Config classifications"),
        39 : ("Lesjoursfris", "", "Saisie jour f�ri�"),
        40 : ("Appliquerunmodledeprsences", "", "Application mod�le de pr�sences"),
        41 : ("Lestypesdecontrats", "", "Saisie types contrats"),
        42 : ("Attribuerunephoto", "", "Editeur photo"),
        43 : ("Lespriodesdevacances", "", "Config p�riodes vacances"),
        44 : ("Enregistrerundplacement", "", "Saisie d�placement"),
        45 : ("Lesgadgets", "", "Config gadgets"),
        46 : ("ExporterlespersonnesdansMSOutl", "", "Export Outlook"),
        47 : ("Ouvrirunfichier", "", "Ouvrir un fichier"),
        48 : ("Lestypesdequalifications", "", "Config types diplomes"),
        49 : ("Assistantdemarrage", "", "Assistant d�marrage"),
        50 : ("Lestypesdepices", "", "Saisie types pi�ces"),
        51 : ("Lecalendrier", "", "Le calendrier"),
        52 : ("Lesmodlesdecontrats", "", "Config modeles contrats"),
        53 : ("Lalistedespersonnes", "Options", "Config liste personnes"),
        54 : ("Creruncontrat", "", "wiz creation contrats"),
        55 : ("Lalistedespersonnes", "export_liste", "export liste personnes"),
        56 : ("Lalistedespersonnes", "Imprimer_liste", "Imprimer liste Personnes"),
        57 : ("Laficheindividuelle", "", "Fiche individuelle"),
        58 : ("Lagestiondesscnarios", "", "Les sc�narios"),
        59 : ("Lesstatistiques", "", "Les statistiques"),
        60 : ("Lagestiondesutilisateurs", "", "La gestion des utilisateurs r�seau"),
        } # NumItem : nomPage, nomAncre, Description
    
    if numItem != None :
        nomPage, nomAncre, description = dictAide[numItem]
    
    if "linux" in sys.platform :
        
        # Aide LINUX : sur internet
        
        # Pr�paration du fichier chm
        nomFichier = "http://www.clsh-lannilis.com/teamworks/aide/tw.htm"
        # Pr�paration de la page HTML
        if nomPage != "" :
            page = "?" + nomPage + ".html"
        else:
            page = ""
        # Pr�paration de l'ancre
        if nomAncre != "" :
            ancre = "#" + nomAncre
        else:
            ancre = ""
        # Ouverture de la page internet
        LanceFichierExterne(nomFichier + page + ancre)
            
    else:
        # Aide WINDOWS avec le CHM
        
        # Pr�paration du fichier chm
        nomFichier = "Aide/teamworks.chm"
        # Pr�paration de la page HTML
        if nomPage != "" :
            page = "::/" + nomPage + ".html"
        else:
            page = ""
        # Pr�paration de l'ancre
        if nomAncre != "" :
            ancre = "#" + nomAncre
        else:
            ancre = ""
        # Ouverture du module d'aide
        commande = 'hh.exe "'+ nomFichier  + page + ancre + '"'
        from subprocess import Popen
        Popen(commande)

def RecupNomCadrePersonne(IDpersonne):
    """ R�cup�re le nom du cadre de d�coration pour une personne donn�e """
    DB = GestionDB.DB()        
    req = "SELECT cadre_photo FROM personnes WHERE IDpersonne=%d;" % IDpersonne
    DB.executerReq(req)
    donnees = DB.resultatReq()
    DB.close()
    if len(donnees) == 0 : return None
    cadre_photo = donnees[0][0]
    if cadre_photo == "" : return None
    return cadre_photo

def VideRepertoireTemp():
    """ Supprimer tous les fichiers du r�pertoire TEMP """
    for rep in ("Temp/", UTILS_Fichiers.GetRepTemp()) :
        if os.path.isdir(rep) :
            for nomFichier in os.listdir(rep) :
                nomComplet = os.path.join(rep, nomFichier)
                try :
                    if os.path.isdir(nomComplet) :
                        import shutil
                        shutil.rmtree(nomComplet)
                    else :
                        os.remove(nomComplet)
                except Exception as err :
                    print(err)

def VideRepertoireUpdates(forcer=False):
    """ Supprimer les fichiers temporaires du r�pertoire Updates """
    try :
        listeReps = UTILS_Fichiers.GetRepUpdates()
        numVersionActuelle = GetVersionLogiciel()
        for nomRep in os.listdir(listeReps) :
            resultat = CompareVersions(versionApp=numVersionActuelle, versionMaj=nomRep)
            if resultat == False or forcer == True :
                # Le rep est pour une version �gale ou plus ancienne
                if numVersionActuelle != nomRep or forcer == True :
                    # Si la version est ancienne, suppression du r�pertoire
                    import shutil
                    shutil.rmtree(UTILS_Fichiers.GetRepUpdates(nomRep))
                else:
                    # La version est �gale : on la laisse pour l'instant
                    pass
    except Exception as err:
        print(err)
        pass

def AfficheStatsProgramme():
    """ Affiche des stats du programme """
    listeResultats = []
    nbreDialogs = 0
    nbreFrames = 0
    nbreImpressionsOL = 0
    nbreImpressionsPDF = 0
    nbreLignesTotal = 0
    nbreBoitesDialogue = 0
    nbreFonctions = 0
    
    # Recherche les fichiers python
    print("Lancement de l'analyse...")

    listeFichiers = {}
    for rep in ("Dlg", "Ctrl", "Ol", "Utils"):
        if rep not in listeFichiers:
            listeFichiers[rep] = []
        listeFichiers[rep] = os.listdir(os.getcwd() + "/" + rep)

    for rep, liste in listeFichiers.items() :
        for nomFichier in liste:
            if nomFichier.endswith(".py") :
                fichier = open(rep + "/" + nomFichier, 'r')
                nbreLignes = 0
                for line in fichier :
                    # Compte le nombre de lignes
                    nbreLignes += 1
                    # Recherche d'un wx.Dialog
                    if "wx.Dialog.__init__" in line : nbreDialogs += 1
                    # Recherche une impression ObjectListview
                    if "prt.Print()" in line : nbreImpressionsOL += 1
                    # Recherche une impression PDF avec reportlab
                    if "doc.build(story)" in line : nbreImpressionsPDF += 1
                    # Recherche des bo�tes de dialogue
                    if "wx.MessageDialog(" in line : nbreBoitesDialogue += 1
                    # Recherche le nbre de fonctions
                    if " def " in line : nbreFonctions += 1

                fichier.close()
                # M�morise les r�sultats
                listeResultats.append((nomFichier, nbreLignes))
                nbreLignesTotal += nbreLignes
    
    # Nbre tables
    from Data.DATA_Tables import DB_DATA
    nbreTables = len(list(DB_DATA.keys())) + 2
    
    # Affiche les r�sultats
    for nomFichier, nbreLignes in listeResultats :
        print("%s ---> %d lignes" % (nomFichier, nbreLignes))
    print("----------------------------------------")
    print("Nbre total de lignes = %d lignes" % nbreLignesTotal)
    print("Nbre total de modules = %s modules" % len(listeResultats))
    print("Nbre total de fonctions = %d" % nbreFonctions) 
    print("----------------------------------------")
    print("Nbre total de wx.Dialog = %d" % nbreDialogs)
    print("Nbre total d'impressions ObjectlistView = %d" % nbreImpressionsOL) 
    print("Nbre total d'impressions PDF = %d" % nbreImpressionsPDF) 
    print("Nbre total de boites de dialogue = %d" % nbreBoitesDialogue) 
    print("----------------------------------------")
    print("Nbre tables de donn�es = %d" % nbreTables)

def GetRepertoireProjet(fichier=""):
    frozen = getattr(sys, 'frozen', '')
    if not frozen:
        chemin = os.path.dirname(os.path.abspath(__file__))
    else :
        chemin = os.path.dirname(sys.executable)
    return os.path.join(chemin, fichier)

def GetTopWindow(onlyGeneral=False):
    topWindow = wx.GetApp().GetTopWindow()
    if onlyGeneral:
        if topWindow.GetName() == "general":
             return topWindow
        else: return None
    return topWindow

def GetVersionLogiciel(datee=False):
    """ Recherche du texte version du logiciel dans fichier versions """
    fichierVersion = codecs.open(
        GetRepertoireProjet("Versions.txt"),
        encoding='utf-8',
        mode='r')
    txtVersion = fichierVersion.readlines()[0]
    fichierVersion.close()
    pos_debut_numVersion = txtVersion.find("n")
    if datee:
        pos_fin_numVersion = txtVersion.find(")") + 1
    else:
        pos_fin_numVersion = txtVersion.find("(")
    numVersion = txtVersion[pos_debut_numVersion+1:pos_fin_numVersion].strip()
    return numVersion

def ConvertVersionTuple(txtVersion=""):
    """ Convertit un num�ro de version texte en tuple """
    if "(" in txtVersion:
        # si la version est avec ('date'), il faut s'en tenir au num�ro version
        txtVersion = txtVersion.split("(")[0]
    texteVersion = ChiffresSeuls(txtVersion)
    tupleTemp = []
    for num in texteVersion.split(".") :
        tupleTemp.append(int(num))
    return tuple(tupleTemp)

def CompareVersions(versionApp="", versionMaj=""):
    """ Compare 2 versions """
    """ Return True si la version MAJ est plus r�cente """
    a,b = [[int(n) for n in version.split(".")] for version in [versionMaj, versionApp]]
    return a>b

def LanceFichierExterne(nomFichier) :
    """ Ouvre un fichier externe sous windows ou linux """
    nomSysteme = sys.platform
    if nomSysteme.startswith("win") : 
        nomFichier = nomFichier.replace("/", "\\")
        os.startfile(nomFichier)
    if "linux" in nomSysteme : 
        os.system("xdg-open " + nomFichier)

def OuvrirCalculatrice():
    if sys.platform.startswith("win") : LanceFichierExterne("calc.exe")
    if "linux" in sys.platform : os.system("gcalctool")

def Formate_taille_octets(size):
    """
    fonction qui prend en argument un nombre d'octets
    et renvoie la taille la plus adapt�
    """
    seuil_Kio = 1024
    seuil_Mio = 1024 * 1024
    seuil_Gio = 1024 * 1024 * 1024

    if size > seuil_Gio:
        return "%.2f Go" % (size/float(seuil_Gio))
    elif size > seuil_Mio:
        return "%.2f Mo" % (size/float(seuil_Mio))
    elif size > seuil_Kio:
        return "%.2f Ko" % (size/float(seuil_Kio))
    else:
        return "%i o" % size

def GetIDfichier():
    try :
        DB = GestionDB.DB()
        req = """SELECT IDparametre, nom, parametre 
        FROM parametres WHERE nom='IDfichier';"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeTemp = DB.ResultatReq()
        DB.Close()
        IDfichier = listeTemp[0][2]
    except :
        IDfichier = ""
    return IDfichier

def GenerationIDdoc():
    """ G�n�ration d'un ID unique � base de la date, de l'heure de l'IDfichier et d'un num�ro al�atoire """
    IDfichier = GetIDfichier()[14:17]
    import random
    numAleatoire = random.randint(100, 999)
    horodatage = datetime.datetime.now().strftime("%Y%m%d%H%M%S") 
    IDdoc = "%s%s%d" % (horodatage, IDfichier, numAleatoire)
    return IDdoc

def GenerationNomDoc(prefixe="", extension="pdf"):
    """ G�n�ration d'un nom de document dans le r�pertoire Temp"""
    nomDoc = "%s%s.%s" % (prefixe, GenerationIDdoc() , extension)
    return UTILS_Fichiers.GetRepTemp(nomDoc)

def InsertThemeDansOL():
    """ Pour ins�rer la prise en charge des th�mes dans les OL """
    # Get fichiers
    listeFichiers = os.listdir(os.getcwd())
    indexFichier = 0
    for nomFichier in listeFichiers :
        if nomFichier.endswith("py") and nomFichier.startswith("DATA_") == False :
            #print "%d/%d :  %s..." % (indexFichier, len(listeFichiers), nomFichier)

            # Ouverture des fichiers
            fichier = open(nomFichier, "r")
            dirty = False

            listeLignes = []
            for ligne in fichier :

                # Insertion de l'import
                if "from ObjectListView" in ligne :
                    listeLignes.append("\n")
                    listeLignes.append("import UTILS_Interface\n")
                    dirty = True

                # Insertion de l'import
                if "self.oddRowsBackColor =" in ligne :
                    ligne = """        self.oddRowsBackColor = UTILS_Interface.GetValeur("couleur_tres_claire", wx.Colour(240, 251, 237))\n"""
                    dirty = True

                listeLignes.append(ligne)

            # Cl�ture des fichiers
            fichier.close()

            # Ecriture du nouveau fichier
            if dirty == True :
                nouveauFichier = open("New/%s" % nomFichier, "w")
                for ligne in listeLignes :
                    nouveauFichier.write(ligne)
                nouveauFichier.close()

        indexFichier += 1

    print("Fini !!!!!!!!!!!!!!!!!")

if __name__ == "__main__":

    app = wx.App(0)

    import wx.lib.dialogs as dialogs
    image = wx.Bitmap("Static/Images/32x32/Activite.png", wx.BITMAP_TYPE_ANY)
    message2 = "Ceci est un message super m�ga long qui doit prendre pas mal de place !\n" * 50
    dlg = dialogs.MultiMessageDialog(None, "Ceci est le message 1", caption = "Message Box", msg2=message2, style = wx.ICON_EXCLAMATION | wx.OK | wx.CANCEL, icon=None, btnLabels={wx.ID_OK : "Ok", wx.ID_CANCEL : "Annuler"})
    attente = GetAttente(dlg)
    dlg.ShowModal()
    attente = GetAttente(dlg,"Suite")
    del attente
    dlg.Destroy()
    app.MainLoop()
    
    # Recherche de modules
##    listeModules = RechercheModules("OL_Liste_comptes.py")
##    for x in listeModules :
##        print x
##    print "-------------------- Modules trouves : %d --------------------" % len(listeModules) 
    
    # Cr�er des donn�es virtuelles dans DB
    #InsertThemeDansOL()

    # G�n�ration d'un nom de document
    #print GenerationNomDoc("document", "pdf")
    
    #VideRepertoireUpdates(forcer=True)

    #InsertCodeToolTip()
    #CreerDonneesVirtuellesLocations(1000)

    #InsertCode()

    pass

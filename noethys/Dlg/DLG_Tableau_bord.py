#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:          Jacques BRUNEL
# Licence:         Licence GNU GPL
# Lanceur d'outils de synthèse pour tableaux de bord via export excel
#------------------------------------------------------------------------

import wx, datetime
import Chemins
import GestionDB
import wx.lib.agw.pybusyinfo as PBI
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Bandeau
from Ctrl import CTRL_SelectionActivites
from Ctrl import CTRL_Saisie_date
from Utils import UTILS_Config
from Utils import UTILS_Dates
from FonctionsPerso import Supprime_accent
from Utils.UTILS_Export   import ExportExcel

# paramètrage des colonnes selon les applications
def GetColumnsRplActivites():
    return [
        ('Code', 'left', 50, 'cle'),
        ('Activité', 'left', 250, 'nom'),
    ]

def GetColumnsRplEffectifs():
    return [
        ('Cle', 'left', 250, 'cleGrp'),
        ('Groupe', 'left', 250, 'nomGroupe'),
        ('EffectifMaxi', 'right', 60, 'nbre_inscrits_max'),
        ]

def GetColumnsRplDonnees():
    """
    A générer:
    Camp,Nom_camp,Début,Fin,An,CleGroupe,Nom_groupe,Filles,Garçons,Animatrices,Animateurs,Ncampeurs,NAnims,Ninscrits,
    N1inscritsEq,N1inscritsFin,N1campeursEq,N1au,N2inscritsEq,N2inscritsFin,N2campeursEq,N2au,SsAcompte,
    N1campeursFin,N2campeursFin

    champs effectifs = ['cptActivite','nomActivite','dteDeb', 'dteFin','annee','cleGrp','nomGroupe'
    champs N ='filles','gars','animsF','animsG','Ncampeurs','Nanims','Ninscrits','ssAcompte','Nautres'
    champs anterieur = N1inscritsEq,N1campeursFin, N1au ... N2
    """
    return [
        ('Activité', 'left', 50, 'cptActivite'),# le dernier champ n'est pas utilisé, mais 4 items nécessaires
        ('NomActivité', 'left', 250, 'nomActivite'),
        ('Début', 'left', 80, 'dteDeb'),
        ('Fin', 'left', 80, 'dteFin'),
        ('An', 'left', 50, 'annee'),
        ('CleGroupe', 'left', 250, 'cleGrp'),
        ('NomGroupe', 'left', 250, 'nomGroupe'),
        ('Filles', 'right', 50, 'filles'),
        ('Garçons', 'right', 50, 'garcons'),
        ('Animatrices', 'right', 50, 'animsF'),
        ('Animateurs', 'right', 50, 'animsG'),
        ('Ncampeurs', 'right', 50, 'Ncampeurs'),
        ('Nanims', 'right', 50, 'Nanims'),
        ('Ninscrits', 'right', 50, 'Ninscrits'),
        ('N1inscritsEq', 'left', 50, 'N1inscritsEq'),
        ('N1inscritsFin', 'left', 50, 'N1inscritsFin'),
        ('N1campeursEq', 'left', 50, 'N1campeursEq'),
        ('N1au', 'left', 80, 'dteN1au'),
        ('N2inscritsEq', 'left', 50, 'N2inscritsEq'),
        ('N2inscritsFin', 'left', 50, 'N2inscritsFin'),
        ('N2campeursEq', 'left', 50, 'N2campeursEq'),
        ('N2au', 'left', 80, 'dteN2au'),
        ('ssAcompte', 'right', 50, 'ssAcompte'),
        ('N1campeursFin', 'left', 50, 'N1campeursFin'),
        ('N2campeursFin', 'left', 50, 'N2campeursFin'),
        ('Nautres', 'right', 50, 'Nautres'),
        ('NbreMaxi', 'right', 50, 'nbre_inscrits_max'),
        ]

class Track(object):
    def __init__(self, dictDonnees):
        for cle, valeur in dictDonnees.items():
            setattr(self,"%s"%cle,valeur)

class Remplissage(object):
    def __init__(self,parent):
        self.parent = parent
        self.dDates = None
        self.lstIDactivites = None

    def MajDates(self,DB,dteEquiv):
        dp, mp, yp = dteEquiv.day, dteEquiv.month, dteEquiv.year
        if mp==2 and dp==29:
            dp=28
        equivN1 = datetime.date(yp-1,mp,dp)
        equivN2 = datetime.date(yp-2,mp,dp)
        debExN,finExN = DB.GetExercice(dteEquiv,alertes=False,approche=True)
        debExN1,finExN1 = DB.GetExercice(equivN1,alertes=False,approche=True)
        debExN2,finExN2 = DB.GetExercice(equivN2,alertes=False,approche=True)
        self.dDates = {
            'equivN': dteEquiv,
            'equivN1': equivN1,
            'equivN2': equivN2,
            'debExN': debExN,
            'debExN1': debExN1,
            'debExN2': debExN2,
            'finExN': finExN,
            'finExN1': finExN1,
            'finExN2': finExN2,
            }
        return self.dDates

    def MajParams(self,DB,**kwd):
        # met à jour les paramètre de la classe
        lstIDactivites = kwd.get('lstIDactivites',None)
        dteEquiv = kwd.get('dteEquiv',None)
        if not dteEquiv:
            dteEquiv = datetime.date.today()
        # met à jour en self les activités retenues
        self.lstIDactivites = lstIDactivites
        # met à jour en self du dictionnaire contenenant toutes les dates
        self.MajDates(DB,dteEquiv)

    def NomSansPrefixeNum(self,nom):
        # enlève les préfixes numériques
        ix = 0
        for car in nom:
            if car in ('0123456789'):
                ix += 1
            else: break
        nom = nom[ix:].strip()
        if nom[0] in '-+:#>/':
            nom = nom[1:]
        return nom

    def FusionNoms(self,nom,new):
        if not isinstance(nom,str):
            nom = str(nom)
        # Fusion de noms en ne gardant que les radicaux communs
        if (not new) or (nom == new): return nom
        if not isinstance(new,str):
            new = str(new)
        lstMotsNom = nom.split(' ')
        lstMotsNew = new.split(' ')
        lstCommuns = []
        # repère les mots communs aux deux noms
        for mot in lstMotsNew:
            if mot == '': continue
            if mot in lstMotsNom:
                lstCommuns.append(lstMotsNom.index(mot))
        # minimum deux mots communs
        if len(lstCommuns) > 1:
            nom = ''
            for ix in lstCommuns:
                if lstMotsNom[ix] == '': continue
                nom += lstMotsNom[ix] + ' '
        else:
            nom = '%s/%s'%(nom,new)
        return nom.strip()

    def FusionDates(self,dateOld,dateNew,borne='fin'):
        # élargissement d'un période entre date début et fin
        if not dateOld and not dateNew:
            return None
        if not dateOld and dateNew:
            return dateNew
        if dateOld and not dateNew:
            return dateOld
        if dateOld <= dateNew:
            if borne == 'fin':
                return dateNew
            else: return dateOld
        else:
            if borne == 'fin':
                return dateOld
            else: return dateNew

    def GetCleGrp(self,codeAct,nomAct,nomGrp,ordre):
        if not codeAct: # activité sans code on prend son nom comme code
            codeAct = Supprime_accent(nomAct)
        nomSimple = self.NomSansPrefixeNum(nomGrp)
        if ordre == None: ordre = 5
        ordreGrp = '  %s'%str(ordre)
        cleGrp = '%s%s %s'%(codeAct,ordreGrp[-2:],Supprime_accent(nomSimple))
        return cleGrp

    def RechercheAcomptes(self,DB,donnees,dddGroupesFamillesInscriptions):
        # calcule le champ ssAcomptes dans donnees à partir du détail dddGroupesFamillesInscriptions
        lstIDfamilles = [] # lstIDfamilles servira de filtre de recherche du sql
        lstIDinscriptions = [] # pour recherche des ventilations
        minDateCreation = '9999' # servira de borne à minima pour alleger les requêtes
        dictDatesInscriptions = {}
        # génération des listes et dictionnaires
        for IDgroupe,ddFamillesInscriptions in dddGroupesFamillesInscriptions.items():            
            for IDfamille,dInscriptions in ddFamillesInscriptions.items():
                if not IDfamille in lstIDfamilles:
                    lstIDfamilles.append(IDfamille)
                for IDinscription, dInscr in dInscriptions.items():
                    if not IDinscription in lstIDinscriptions:
                        lstIDinscriptions.append(IDinscription)
                    dteInscription = dInscr['dteInscription']
                    if dteInscription <= minDateCreation:
                        minDateCreation = dteInscription
                    if not IDfamille in dictDatesInscriptions:
                        dictDatesInscriptions[IDfamille] = dInscr['dteInscription']
                    else:
                        dictDatesInscriptions[IDfamille] = self.FusionDates(dictDatesInscriptions[IDfamille],
                                                                            dInscr['dteInscription'],'debut')
        # recherche des acomptes inscriptions par la ventilation de règlements
        req = """
            SELECT matPieces.pieIDgroupe, matPieces.pieIDfamille, matPieces.pieIDinscription, 
                Sum(ventilation.montant), groupes.ordre, groupes.nom, activites.code_comptable,activites.nom
            FROM ((matPieces 
                    LEFT JOIN ventilation ON matPieces.pieIDprestation = ventilation.IDprestation) 
                    LEFT JOIN groupes ON matPieces.pieIDgroupe = groupes.IDgroupe) 
                    LEFT JOIN activites ON matPieces.pieIDactivite = activites.IDactivite
            WHERE matPieces.pieIDinscription in ( %s )
            GROUP BY matPieces.pieIDgroupe, matPieces.pieIDfamille, matPieces.pieIDinscription, groupes.ordre, 
                    groupes.nom, activites.code_comptable, activites.nom;    
            ;"""%(str(lstIDinscriptions)[1:-1])
        ret = DB.ExecuterReq(req,MsgBox='DLG_Tableau_bord.Ponderation1')
        recordset = DB.ResultatReq()
        for IDgroupe,IDfamille,IDinscription,mttVentile,ordre,nomGrp,codeAct,nomAct in recordset:
            # maj des inscriptions pour acomptes
            if mttVentile and mttVentile > 50:
                cleGrp = self.GetCleGrp(codeAct,nomAct,nomGrp,ordre)
                dddGroupesFamillesInscriptions[cleGrp][IDfamille][IDinscription]['acompte']=1

        def ImputationAcompte(ID):
            # Toutes les inscriptions de la famille sont acomptéees
            for IDgroupe,ddFamillesInscriptions in dddGroupesFamillesInscriptions.items():
                if ID not in ddFamillesInscriptions:
                    continue
                dInscriptions = ddFamillesInscriptions[ID]
                for IDinscription,dInscr in dInscriptions.items():
                    dInscr['acompte'] = 1
            
        # MAJ en cas de solde positif de la famille
        condFamille = 'IDcompte_payeur IN ( %s )'%(str(lstIDfamilles)[1:-1])
        req = """
            SELECT clientRegle.IDcompte_payeur, SUM(clientRegle.reglements), SUM(clientDu.prestations)
            FROM (
                    SELECT reglements.IDcompte_payeur, Sum(reglements.montant) AS reglements
                    FROM reglements
                    WHERE %s
                    GROUP BY reglements.IDcompte_payeur    
                 ) AS clientRegle 
                LEFT JOIN 
                    (   
                        SELECT prestations.IDcompte_payeur, Sum(prestations.montant) AS prestations
                        FROM prestations
                        WHERE %s
                        GROUP BY prestations.IDcompte_payeur
                    ) AS clientDu 
                ON clientRegle.IDcompte_payeur = clientDu.IDcompte_payeur
            GROUP BY clientRegle.IDcompte_payeur
            ;"""%(condFamille,condFamille)
        ret = DB.ExecuterReq(req,MsgBox='DLG_Tableau_bord.Ponderation2')
        recordset = DB.ResultatReq()
        for IDfamille,mttReglements,mttPrestations in recordset:
            if not mttReglements: mttReglements = 0.0
            if not mttPrestations: mttPrestations = 0.0
            solde = (mttReglements - mttPrestations)
            if solde > 50:
                ImputationAcompte(IDfamille)

        # MAJ si présence de règlementsLibres (non ventilés)
        condFamille = 'reglements.IDcompte_payeur IN ( %s )'%(str(lstIDfamilles)[1:-1])
        req = """
            SELECT reglements.IDcompte_payeur, reglements.date_saisie, 
                    Sum(reglements.montant)-Sum(ventilation.montant) AS mttLibre
            FROM reglements 
                LEFT JOIN ventilation ON reglements.IDreglement = ventilation.IDreglement
            WHERE   ((%s) 
                    AND (reglements.date_saisie >= '%s' ))
            GROUP BY reglements.IDcompte_payeur, reglements.date_saisie
            HAVING  Sum(reglements.montant)-Sum(ventilation.montant) > 0.01 
            ;"""%(condFamille,minDateCreation)
        ret = DB.ExecuterReq(req,MsgBox='DLG_Tableau_bord.Ponderation3')
        recordset = DB.ResultatReq()
        dictReglements = {}
        for IDfamille, dteSaisie,mttLibre in recordset:
            if not IDfamille in dictReglements:
                dictReglements[IDfamille] = {'mttLibre':0,'reglements':{}}
            dictReglements[IDfamille]['mttLibre'] += round(mttLibre,2)
            dictReglements[IDfamille]['reglements'] = {dteSaisie:round(mttLibre,2)}
        # reprise pour imputer des acomptes sur les inscriptions
        for IDgroupe,ddFamillesInscriptions in dddGroupesFamillesInscriptions.items():
            for IDfamille, dInscriptions in ddFamillesInscriptions.items():
                if not IDfamille in dictReglements:
                    continue
                mttLibre = dictReglements[IDfamille]['mttLibre']
                if mttLibre < 50:
                    continue
                for IDinscription, dInscr in dInscriptions.items():
                    if dInscr['acompte'] == 1:
                        continue
                    ventil = 0
                    for dteReglement, montant in dictReglements[IDfamille]['reglements'].items():
                        if dteReglement < dInscr['dteInscription']:
                            continue
                        ventil += min(montant,50)
                        dictReglements[IDfamille]['reglements'][dteReglement] -= ventil                        
                        if ventil < 50:
                            continue
                        dInscr['acompte'] = 1
                        mttLibre -= 50
                        dictReglements[IDfamille]['mttLibre'] -= 50
                    if mttLibre < 50:
                        break

        # Traitement de modification de chaque groupe dans données, déroule tous les groupes
        for key, dictDonnees in donnees.items():
            # recherche des acomptes ventilés
            nbInscrits = 0
            nbCampeurs = 0
            nbAcomptes = 0
            for IDfamille, ddFamillesInscriptions in dddGroupesFamillesInscriptions[key].items():
                for IDinscription, dInscr in ddFamillesInscriptions.items():
                    nbInscrits += 1
                    if dInscr['campeur'] == 1:
                        nbAcomptes += dInscr['acompte']
                        nbCampeurs += 1
            if nbCampeurs + nbInscrits != dictDonnees['Ninscrits'] + dictDonnees['Ncampeurs']:
                print((dictDonnees['nomActivite'],dictDonnees['nomGroupe'],
                      dictDonnees['Ninscrits'],nbInscrits,"Groupe: ",key))
                raise Exception('pb de logique')
            dictDonnees['ssAcompte'] = nbCampeurs - nbAcomptes

    def GetEffectifs(self,DB):
        # appel de tous les codes analytiques activités-groupes et leur paramètre effectif maxi
        lstChamps = ['cptActivite', 'nomActivite', 'dteDeb', 'dteFin', 'abregeGrp', 'nomGroupe','ordre', 'nbre_inscrits_max']

        dictEffectifs = {}
        dictActivites = {}
        condAnnee = "activites.date_debut BETWEEN '%s' AND '%s'"%(self.dDates['debExN'],self.dDates['finExN'])
        condActivite = 'activites.IDactivite IN (%s)'%str(self.lstIDactivites)[1:-1]
        req = """
            SELECT detail.code_comptable, detail.nomAct, detail.date_debut, detail.date_fin, 
					detail.abrege, detail.nomGrp, detail.ordre, detail.nbre_inscrits_max
            FROM 
            (	SELECT activites.code_comptable,activites.nom AS nomAct, activites.date_debut, activites.date_fin, 
                    groupes.abrege, groupes.nom AS nomGrp, groupes.ordre, groupes.nbre_inscrits_max
                FROM activites
				INNER JOIN groupes ON activites.IDactivite = groupes.IDactivite

                WHERE ((%s) AND (%s))
                GROUP BY activites.code_comptable, activites.nom, activites.date_debut, activites.date_fin, 
                    groupes.abrege, groupes.nom, groupes.ordre, groupes.nbre_inscrits_max
            ) AS detail
			GROUP BY detail.code_comptable, detail.nomAct, detail.date_debut, detail.date_fin, 
					detail.abrege, detail.nomGrp, detail.ordre, detail.nbre_inscrits_max
            ;"""%(condActivite,condAnnee)
        ret = DB.ExecuterReq(req,MsgBox='DLG_Tableau_bord.GetEffectifs')
        recordset = DB.ResultatReq()
        # constitution du squelette du dictionnaire des groupes concernés
        for record in recordset:
            codeAct = record[0]
            ixAct = lstChamps.index('nomActivite')
            nomAct = record[ixAct]
            ixNomGroupe = lstChamps.index('nomGroupe')
            nomGrp = record[ixNomGroupe]
            ixOrdre = lstChamps.index('ordre')
            ordre = record[ixOrdre]
            cleGrp = self.GetCleGrp(codeAct,nomAct,nomGrp,ordre)
            # alimente les activités
            nomActivite = str(codeAct) + ' ' + self.NomSansPrefixeNum(record[lstChamps.index('nomActivite')])
            if not codeAct in dictActivites:
                dictActivites[codeAct] = nomActivite
            else:
                dictActivites[codeAct] = self.FusionNoms(dictActivites[codeAct], nomActivite)

            # alimente les effectifs par groupe
            if not cleGrp in dictEffectifs:
                # clé créée
                dictEffectifs[cleGrp] = {}
                for ix in range(len(lstChamps)):
                    dictEffectifs[cleGrp][lstChamps[ix]] = record[ix]
            else:
                # cas d'un doublon
                for ix in range(len(lstChamps)):
                    # cumul des effectifs qui sont numériques, concaténation des str différent
                    if isinstance(record[ix],(int,float)):
                        if not dictEffectifs[cleGrp][lstChamps[ix]]:
                            dictEffectifs[cleGrp][lstChamps[ix]] = 0
                        dictEffectifs[cleGrp][lstChamps[ix]] += record[ix]
                    elif (not record[ix]) or dictEffectifs[cleGrp][lstChamps[ix]] == record[ix]:
                        continue
                    elif lstChamps[ix][:3] in ('dte','dat'):
                        # le cumul des dates consiste en un élargissement de période
                        if 'fin' in lstChamps[ix].lower():
                            borne = 'fin'
                        else: borne = 'debut'
                        dateOld = dictEffectifs[cleGrp][lstChamps[ix]]
                        dictEffectifs[cleGrp][lstChamps[ix]] = self.FusionDates(dateOld,record[ix],borne)
                    else:
                        old = Supprime_accent(dictEffectifs[cleGrp][lstChamps[ix]])
                        new = Supprime_accent(record[ix])
                        commun = self.FusionNoms(old,new)
                        dictEffectifs[cleGrp][lstChamps[ix]] = commun
            nomSimple = self.NomSansPrefixeNum(nomGrp)
            dictEffectifs[cleGrp]['nomGroupe'] = nomSimple
            dictEffectifs[cleGrp]['cleGrp'] = cleGrp
            dictEffectifs[cleGrp]['annee'] = dictEffectifs[cleGrp]['dteFin'][:4]

        return dictEffectifs, dictActivites

    def GetDonneesNN(self,DB, dteDebut,dteFin,dteLimite):
        # Recherche de données simplifiée pour années antérieures
        dictDonnees = {}
        # appel de toutes les inscriptions de l'exercice jusqu'à la date equiv, groupées par activité
        lstChamps = ['cptActivite','campeur','inscrits','dateMax']
        condAnnee = "activites.date_debut BETWEEN '%s' AND '%s'"%(dteDebut,dteFin)
        condAnnee += "AND matPieces.pieDateCreation <='%s'"%(dteLimite)

        req = """
            SELECT detail.code_comptable, detail.campeur, COUNT(detail.pieIDinscription), MAX(detail.dateMax)
            FROM 
            (	SELECT activites.code_comptable, categories_tarifs.campeur, matPieces.pieIDinscription, 
                        MAX(matPieces.pieDateCreation) AS dateMax
                FROM (activites 
                INNER JOIN matPieces ON activites.IDactivite = matPieces.pieIDactivite) 
                INNER JOIN categories_tarifs ON matPieces.pieIDcategorie_tarif = categories_tarifs.IDcategorie_tarif
            
                WHERE ((matPieces.pieNature NOT IN ('DEV','AVO')) 
                            AND (%s))
                GROUP BY activites.code_comptable, categories_tarifs.campeur, matPieces.pieIDinscription
            ) AS detail
            GROUP BY detail.code_comptable, detail.campeur
            ;"""%(condAnnee)
        ret = DB.ExecuterReq(req,MsgBox='DLG_Tableau_bord.GetDonneesNN')
        recordset = DB.ResultatReq()
        for codeAct, campeur, inscrits, dateMax in recordset:
            if not inscrits: inscrits = 0
            # alimente les activités
            if not codeAct in dictDonnees:
                dictDonnees[codeAct] = {'inscrits':0,'campeurs':0,'au':None}
            dictDonnees[codeAct]['inscrits'] += inscrits
            dictDonnees[codeAct]['au'] = self.FusionDates(dictDonnees[codeAct]['au'],dateMax)
            if campeur == 1:
                dictDonnees[codeAct]['campeurs'] += inscrits
        return dictDonnees

    def GetDonnees(self,DB):
        # trame de départ commune aux effectifs par groupe
        dictEffectif, dictActivites = self.GetEffectifs(DB)
        # appel des dictionnaires années antérieures
        exDeb = self.dDates['debExN1']
        exFin = self.dDates['finExN1']
        dDon_equivN1 = self.GetDonneesNN(DB,exDeb,exFin,self.dDates['equivN1'])
        dDon_exerciceN1 = self.GetDonneesNN(DB,exDeb,exFin,self.dDates['finExN1'],)
        exDeb = self.dDates['debExN2']
        exFin = self.dDates['finExN2']
        dDon_equivN2 = self.GetDonneesNN(DB,exDeb,exFin,self.dDates['equivN2'])
        dDon_exerciceN2 = self.GetDonneesNN(DB,exDeb,exFin,self.dDates['finExN2'])
        
        dictDonnees = {}
        dddGroupesFamillesInscriptions = {}
        
        # appel de toutes les inscriptions de l'exercice jusqu'à la date equiv        
        lstChamps = ['cptActivite','nomActivite','nomGroupe', 'IDcivilite',
                     'campeur','nomTarif','ordre','IDgroupe',
                     'IDfamille','IDinscription','dteInscription']
        #cptActivite,nomActivite,nomGrp, IDcivilite,campeur,nomTarif,ordre,IDgroupe,IDfamille,IDinscripion,dteInscription
        condActivite = "activites.IDactivite IN (%s)"%str(self.lstIDactivites)[1:-1]
        condAnnee = "activites.date_debut BETWEEN '%s' AND '%s' "%(self.dDates['debExN'],self.dDates['finExN'])
        condAnnee += "AND matPieces.pieDateCreation <='%s'"%(self.dDates['equivN'])
        req = """
			SELECT activites.code_comptable, activites.nom, groupes.nom, individus.IDcivilite, 
			        categories_tarifs.campeur, categories_tarifs.nom, groupes.ordre, groupes.IDgroupe, 
			        matPieces.pieIDfamille, matPieces.pieIDinscription, MIN(matPieces.pieDateCreation)
			FROM 
				activites 
				INNER JOIN 
				(	((matPieces 
					INNER JOIN groupes ON matPieces.pieIDgroupe = groupes.IDgroupe) 
					INNER JOIN individus ON matPieces.pieIDindividu = individus.IDindividu) 
					INNER JOIN categories_tarifs 
					    ON matPieces.pieIDcategorie_tarif = categories_tarifs.IDcategorie_tarif
				) ON activites.IDactivite = matPieces.pieIDactivite
			WHERE (( %s )
			        AND (%s) 
			        )
			GROUP BY activites.code_comptable, activites.nom, groupes.nom, 
					individus.IDcivilite, categories_tarifs.campeur, 
					categories_tarifs.nom, groupes.ordre, groupes.IDgroupe, 
			        matPieces.pieIDfamille, matPieces.pieIDinscription
			;"""%(condAnnee, condActivite)
        ret = DB.ExecuterReq(req,MsgBox='DLG_Tableau_bord.GetDonnees')
        recordset = DB.ResultatReq()
        # complétion du squelette constitué par les effectifs et génération de dddGroupesFamillesInscriptions
        for record in recordset:
            codeAct = record[0]
            ixAct = lstChamps.index('nomActivite')
            nomAct = record[ixAct]
            ixNomGroupe = lstChamps.index('nomGroupe')
            nomGrp = record[ixNomGroupe]
            ixOrdre = lstChamps.index('ordre')
            ordre = record[ixOrdre]
            cleGrp = self.GetCleGrp(codeAct,nomAct,nomGrp,ordre)

            # autant de passage que de categories_tarifs ou types_civilités détaillés par le sql
            if not cleGrp in dictDonnees:
                # premier item sur cette clé
                if not cleGrp in dictEffectif:
                    # clé normalement crée via les effectifs
                    raise Exception('Cf itineraire, cle normalement creee par les effectifs')
    
                # reprend le dic des données du groupe déjà dans les effectifs
                dictDonnees[cleGrp] = dictEffectif[cleGrp]

                # reprend les champs des années antérieures
                lstCles = []
                for dDon,periode,an in ((dDon_equivN1,'Eq','N1'),(dDon_exerciceN1,'Fin','N1'),
                                        (dDon_equivN2,'Eq','N2'),(dDon_exerciceN2,'Fin','N2')):
                    champInscrits = '%sinscrits%s'%(an,periode) #N1inscritsEq,N1campeursFin, N1au
                    champCampeurs = '%scampeurs%s'%(an,periode) #N2inscritsEq,N2campeursFin, N2au
                    if codeAct in dDon:
                        dictDonnees[cleGrp][champInscrits] = int(dDon[codeAct]['inscrits'])
                        dictDonnees[cleGrp][champCampeurs] = int(dDon[codeAct]['campeurs'])
                        # champ de la date 'dteN1au' 'dteN2au pour le cas de date équivalente
                        if periode == 'Eq':
                            dictDonnees[cleGrp]['dte%sau'%an] = dDon[codeAct]['au']
    
                # préparation d'un dictionnaire qui va updater l'existant dans dictDonnees venant d'effectifs et antérieur
                dictTemp = {'filles': 0,'gars': 0,
                            'animsF': 0,'animsG': 0,
                            'Ncampeurs': 0,'Nanims': 0,'Nautres': 0,'Ninscrits': 0,
                            }
                dictDonnees[cleGrp].update((dictTemp))
            dictDon = dictDonnees[cleGrp]
 
            # calculs clé unique 'IDinscription'
            cptActivite,nomActivite,nomGrp, IDcivilite,campeur,nomTarif,ordre,IDgroupe,IDfamille,IDinscription,dteInscription = record

            # génération dddGroupesFamillesInscriptions
            if not cleGrp in dddGroupesFamillesInscriptions:
                dddGroupesFamillesInscriptions[cleGrp] = {}
            ddFamillesInscriptions = dddGroupesFamillesInscriptions[cleGrp]
            if not IDfamille in ddFamillesInscriptions:
                ddFamillesInscriptions[IDfamille] = {}
            dInscriptions = ddFamillesInscriptions[IDfamille]
            
            dInscriptions[IDinscription] = {'acompte':0,'dteInscription':dteInscription, 'campeur':0}

            # complétion de dictDonnees
            dictDon['IDgroupe'] = IDgroupe
            dictDon['Ninscrits'] += 1

            if campeur == 1:
                # tous les tarifs inclus dans l'effectif sont des campeurs
                dictDon['Ncampeurs'] += 1
                dInscriptions[IDinscription]['campeur'] = 1
                if IDcivilite in (3,5):
                    dictDon['filles'] += 1
                else: dictDon['gars'] += 1

            elif ('enfant' in nomGrp) or ('enfant' in nomTarif):
                # les enfants du personnel ne sont ni anims ni campeurs
                dictDon['Nautres'] += 1

            else:
                # éauipiers, bénévoles anims etc, tous ce qui n'entre pas dans les effectifs sans être enfant
                dictDon['Nanims'] += 1
                if IDcivilite in (3,5):
                    dictDon['animsF'] += 1
                else: dictDon['animsG'] += 1
            # fin d'actualisation de dictDonnees[cleGrp)
        return dictDonnees, dddGroupesFamillesInscriptions

    def TbrActivites(self,DB,lstIDactivites=None,dteEquiv=None):
        dlgAttente = PBI.PyBusyInfo('Recherche des données...', parent=None, title='Veuillez patienter...',
                                    icon=wx.Bitmap(Chemins.GetStaticPath('Images/16x16/Logo.png'), wx.BITMAP_TYPE_ANY))
        wx.Yield()        # export (code noms) des activites
        self.MajParams(DB,lstIDactivites=lstIDactivites)
        effectifs, activites = self.GetEffectifs(DB)

        # Appel des données: reprise des seuls champs souhaités pour l'export
        llActivites = []
        for cle in sorted(activites.keys()):
            llActivites.append([cle,activites[cle]])
        lstColonnes = ['Clé']
        del dlgAttente
        # Export des données formatées selon les colonnes
        ExportExcel(listview=None,listeColonnes=GetColumnsRplActivites(),listeValeurs=llActivites)
        return

    def TbrDonnees(self,DB,lstIDactivites=None,dteEquiv=None):
        # Export des données de remplisage détaillées
        dlgAttente = PBI.PyBusyInfo('Recherche des données...',
                            parent=None, title='Veuillez patienter...',
                            icon=wx.Bitmap(Chemins.GetStaticPath('Images/16x16/Logo.png'),
                                           wx.BITMAP_TYPE_ANY))
        wx.Yield()        # export (code noms) des activites

        self.MajParams(DB,lstIDactivites=lstIDactivites,dteEquiv=dteEquiv)
        donnees,dddGroupesFamillesInscriptions = self.GetDonnees(DB)
        if len(list(dddGroupesFamillesInscriptions.keys())) >0:
            self.RechercheAcomptes(DB,donnees,dddGroupesFamillesInscriptions)

        # Appel des données: reprise des seuls champs souhaités pour l'export
        llDonnees = []
        lstChamps = ['cptActivite','nomActivite','dteDeb', 'dteFin','annee','cleGrp','nomGroupe',
                    'filles','gars','animsF','animsG','Ncampeurs','Nanims','Ninscrits',
                     'N1inscritsEq','N1inscritsFin','N1campeursEq','dteN1au',
                     'N2inscritsEq','N2inscritsFin','N2campeursEq','dteN2au',
                     'ssAcompte','N1campeursFin','N2campeursFin','Nautres','nbre_inscrits_max',
                     ]
        for cleGrp in sorted(donnees.keys()):
            lLigne = []
            for champ in lstChamps:
                if champ in donnees[cleGrp]:
                    if champ[:3] == 'dte':
                        # transforme les dates Ansi en date française
                        donnees[cleGrp][champ] = UTILS_Dates.DateEngFr(donnees[cleGrp][champ])
                    lLigne.append(donnees[cleGrp][champ])
                else: lLigne.append(None)
            llDonnees.append(lLigne)

        del dlgAttente
        # Export des données formatées selon les colonnes
        ExportExcel(listview=None,listeColonnes=GetColumnsRplDonnees(),listeValeurs=llDonnees)
        return

class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1,
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.today = datetime.date.today()
        self.DB = GestionDB.DB()
        if self.DB.echec == 1:
            raise Exception('Interrompu par absence de base de donnees')


        intro = ("Ici une sélection d'exports standards vers la bureautique.")
        titre = ('Exports pour tableaux de bord')
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro,  hauteurHtml=15,
                                                 nomImage=Chemins.GetStaticPath('Images/22x22/Smiley_nul.png'))

        # Sélection des Activités
        self.staticBoxSelection = wx.StaticBox(self, wx.ID_ANY, 'Paramètres')
        self.ctrl_activites = CTRL_SelectionActivites.CTRL(self)
        self.label_dateEquiv = wx.StaticText(self, -1, "Date d'analyse: ")
        self.ctrl_dateEquiv = CTRL_Saisie_date.Date2(self)

        self.staticBoxRemplissage = wx.StaticBox(self, -1, 'Suivi du remplissage de camps')
        messTbrDonnees = 'Données : détail des inscriptions'
        self.btn_tbrDonnees = CTRL_Bouton_image.CTRL(self, id=-1, texte= messTbrDonnees,
                                                     cheminImage=Chemins.GetStaticPath("Images/32x32/Calendrier.png"))
        #messTbrEffectifs = u'EffectifsMax : effectifs par groupes'
        #self.btn_tbrEffectifs = CTRL_Bouton_image.CTRL(self, id=-1, texte= messTbrEffectifs,
        #                                             cheminImage=Chemins.GetStaticPath("Images/32x32/Activite.png"))
        messTbrActivites = 'Activites : activites présentes'
        self.btn_tbrActivites = CTRL_Bouton_image.CTRL(self, id=-1, texte= messTbrActivites,
                                                       cheminImage=Chemins.GetStaticPath("Images/32x32/Activite.png"))

        self.bouton_fermer = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte= ('Fermer'),
                                                    cheminImage=Chemins.GetStaticPath("Images/32x32/Fermer.png"))

        self.__set_properties()
        self.__do_layout()
        self.Importation()

    def __set_properties(self):
        self.ctrl_dateEquiv.SetDate(self.today)

        self.SetTitle('DLG_Tableau_bord')
        self.bouton_fermer.SetToolTip('Cliquez ici pour fermer')
        self.SetMinSize((400, 500))
        self.Bind(wx.EVT_BUTTON, self.OnFermer, self.bouton_fermer)
        self.Bind(wx.EVT_BUTTON, self.OnTbrDonnees, self.btn_tbrDonnees)
        #self.Bind(wx.EVT_BUTTON, self.OnTbrEffectifs, self.btn_tbrEffectifs)
        self.Bind(wx.EVT_BUTTON, self.OnTbrActivites, self.btn_tbrActivites)

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=2, vgap=10, hgap=10)
        grid_sizer_contenu = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)

        sizer_selection = wx.StaticBoxSizer(self.staticBoxSelection, wx.VERTICAL)
        grid_sizer_selection = wx.FlexGridSizer(rows=2, cols=1, vgap=5, hgap=5)
        grid_sizer_selection.Add(self.ctrl_activites,0, wx.ALL|wx.EXPAND, 0)

        grid_sizer_date = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_date.Add(self.label_dateEquiv,0, wx.LEFT|wx.EXPAND, 15)
        grid_sizer_date.Add(self.ctrl_dateEquiv,0, wx.ALL|wx.EXPAND, 0)
        grid_sizer_selection.Add(grid_sizer_date,0, wx.ALL|wx.EXPAND, 0)

        sizer_selection.Add(grid_sizer_selection, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_selection.AddGrowableRow(0)
        grid_sizer_selection.AddGrowableCol(0)

        sizer_remplissage = wx.StaticBoxSizer(self.staticBoxRemplissage, wx.VERTICAL)
        grid_sizer_remplissage = wx.FlexGridSizer(rows=6, cols=1, vgap=5, hgap=5)

        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)

        grid_sizer_remplissage.Add(self.btn_tbrDonnees,0, wx.ALL|wx.EXPAND, 0)
        #grid_sizer_remplissage.Add(self.btn_tbrEffectifs,0, wx.ALL|wx.EXPAND, 0)
        grid_sizer_remplissage.Add(self.btn_tbrActivites,0, wx.ALL|wx.EXPAND, 0)
        grid_sizer_remplissage.Add((10,10),0, wx.ALL|wx.EXPAND, 0)
        grid_sizer_remplissage.Add((10,10),0, wx.ALL|wx.EXPAND, 0)
        grid_sizer_remplissage.Add((10,10),1, wx.ALL|wx.EXPAND, 5)
        sizer_remplissage.Add(grid_sizer_remplissage, 1, wx.ALL, 5)
        grid_sizer_remplissage.AddGrowableRow(5)

        grid_sizer_contenu.Add(sizer_selection, 1, wx.EXPAND, 0)
        grid_sizer_contenu.Add(sizer_remplissage, 1, wx.EXPAND, 0)
        grid_sizer_contenu.AddGrowableRow(0)
        grid_sizer_contenu.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_contenu, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_fermer, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()

    def GetParams(self):
        return self.ctrl_activites.GetActivites()

    def Validation(self):
        if self.ctrl_activites.Validation() == False :
            return False
        self.lstIDactivites = self.ctrl_activites.GetActivites()
        self.dateEquiv = self.ctrl_dateEquiv.GetDate()

        # Mémorisation des activités
        lstIDactivitetemp = self.ctrl_activites.GetActivites()
        lstIDactivite = []
        for ID in lstIDactivitetemp :
            lstIDactivite.append(str(ID))
        parametre = '%s' % ';'.join(lstIDactivite)
        UTILS_Config.SetParametre('tableau_bord_activites', parametre)
        return True

    def OnTbrDonnees(self,evt):
        if self.Validation():
            rpl = Remplissage(self)
            rpl.TbrDonnees(self.DB,self.lstIDactivites,self.dateEquiv)
            del rpl

    def OnTbrActivites(self,evt):
        if self.Validation():
            rpl = Remplissage(self)
            rpl.TbrActivites(self.DB,self.lstIDactivites,self.dateEquiv)
            del rpl

    def Importation(self):
        # Activités et dates
        activites = UTILS_Config.GetParametre('tableau_bord_activites', defaut=None)
        if activites != None and activites != '':
            lstIDactivite = []
            for ID in activites.split(';') :
                if not int(ID) in lstIDactivite:
                    lstIDactivite.append(int(ID))
            self.ctrl_activites.SetDates( lstIDactivites=lstIDactivite)
            self.ctrl_activites.SetValeurs(lstIDactivite)
            self.ctrl_activites.ctrl_activites.CocheIDliste(lstIDactivite)
            self.ctrl_activites.ctrl_activites.Modified()

    def OnFermer(self,evt):
        self.DB.Close()
        self.EndModal(wx.ID_OK)

#====Pour tests =====================================================================

if __name__ == '__main__':
    app = wx.App(0)

    dialog_1 = Dialog(None)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()

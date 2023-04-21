#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-19 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import wx,os
import Chemins
import Data.DATA_Tables
import GestionDB
import FonctionsPerso as fp
from Data import DATA_Tables
from Utils import UTILS_Fichiers
from Utils import UTILS_Utilisateurs

class DB(GestionDB.DB):
    def __init__(self, *args, **kwds):
        GestionDB.DB.__init__(self, *args, **kwds)
        self.nb = 0

    def TransposeChamp(self,typeChamp):
        # Adaptation à Sqlite
        if self.typeDB == 'sqlite' and typeChamp == "LONGBLOB": typeChamp = "BLOB"
        # Adaptation à MySQL :
        if self.isNetwork == True and typeChamp == "INTEGER PRIMARY KEY AUTOINCREMENT":
            typeChamp = "INTEGER PRIMARY KEY AUTO_INCREMENT"
        if self.isNetwork == True and typeChamp == "FLOAT": typeChamp = "REAL"
        if self.isNetwork == True and typeChamp == "DATE": typeChamp = "VARCHAR(10)"
        if self.isNetwork == True and typeChamp.startswith("VARCHAR"):
            nbreCaract = int(
                typeChamp[typeChamp.find("(") + 1:typeChamp.find(")")])
            if nbreCaract > 255:
                typeChamp = "TEXT"
            if nbreCaract > 65000:
                typeChamp = "MEDIUMTEXT"
        return typeChamp

    def SupprChamp(self, nomTable="", nomChamp = ""):
        """ Suppression d'une colonne dans une table """
        if self.isNetwork == False :
            # Version Sqlite

            # Recherche des noms de champs de la table
    ##        req = """
    ##        SELECT sql FROM sqlite_master
    ##        WHERE name='%s'
    ##        """ % nomTable
    ##        self.ExecuterReq(req,MsgBox="ExecuterReq")
    ##        reqCreate = self.ResultatReq()[0][0]
    ##        posDebut = reqCreate.index("(")+1
    ##        champs = reqCreate[posDebut:-1]
    ##        listeChamps = champs.split(", ")

            listeChamps = self.GetListeChamps2(nomTable)

            index = 0
            varChamps = ""
            varNomsChamps = ""
            for nomTmp, typeTmp in listeChamps :
                if nomTmp == nomChamp :
                    listeChamps.pop(index)
                    break
                else:
                    varChamps += "%s %s, " % (nomTmp, typeTmp)
                    varNomsChamps += nomTmp + ", "
                index += 1
            varChamps = varChamps[:-2]
            varNomsChamps = varNomsChamps[:-2]

            # Procédure de mise à jour de la table
            req = ""
            req += "BEGIN TRANSACTION;"
            req += "CREATE TEMPORARY TABLE %s_backup(%s);" % (nomTable, varChamps)
            req += "INSERT INTO %s_backup SELECT %s FROM %s;" % (nomTable, varNomsChamps, nomTable)
            req += "DROP TABLE %s;" % nomTable
            req += "CREATE TABLE %s(%s);" % (nomTable, varChamps)
            req += "INSERT INTO %s SELECT %s FROM %s_backup;" % (nomTable, varNomsChamps, nomTable)
            req += "DROP TABLE %s_backup;" % nomTable
            req += "COMMIT;"
            self.cursor.executescript(req)

        else:
            # Version MySQL
            req = "ALTER TABLE %s DROP %s;" % (nomTable, nomChamp)
            self.ExecuterReq(req,MsgBox="ExecuterReq")
            self.Commit()

    def AjoutChamp(self, nomTable = "", nomChamp = "", typeChamp = "",
                   valDefault = None, after = None):
        options = ""
        typeChamp = self.TransposeChamp(typeChamp)
        if isinstance(valDefault,(int,float)):
            options = "DEFAULT %d "% valDefault
        elif isinstance(valDefault,str):
            options = "DEFAULT %s "% valDefault
        if after:
            options += " AFTER %s "% after
        req = "ALTER TABLE %s ADD %s %s %s;" % (nomTable, nomChamp, typeChamp, options)
        ret = self.ExecuterReq(req,MsgBox="AjoutChamp")
        print(req , "----- ", ret)
        self.Commit()
        return ret

    def ModifNomChamp(self, nomTable="", nomChampOld="", nomChampNew=""):
        """ Pour renommer un champ - Ne fonctionne qu'avec MySQL """

        ret = "Champ %s non trouvé dans table %s"%(nomChampOld,nomTable)
        typeChamp = None
        for champ,tip in self.GetListeChamps2(nomTable):
            if champ == nomChampOld:
                typeChamp = tip

        if self.isNetwork == True and typeChamp:
            req = "ALTER TABLE %s CHANGE %s %s %s;" % (nomTable, nomChampOld, nomChampNew, typeChamp)
            ret = self.ExecuterReq(req,MsgBox="ExecuterReq")
        return ret

    def ModifTypeChamp(self, nomTable="", nomChamp="", typeChamp=""):
        """ Ne fonctionne qu'avec MySQL """
        if self.isNetwork == True :
            req = "ALTER TABLE %s CHANGE %s %s %s;" % (nomTable, nomChamp, nomChamp, typeChamp)
            ret = self.ExecuterReq(req,MsgBox="ExecuterReq")
            return ret

    def ReparationTable(self, nomTable="", dicoDB=DATA_Tables.DB_DATA):
        """ Réparation d'une table (re-création de la table) """
        if self.isNetwork == False:
            # Récupération des noms et types de champs
            listeChamps = []
            listeNomsChamps = []
            for descr in dicoDB[nomTable]:
                nomChamp = descr[0]
                typeChamp = descr[1]
                if self.isNetwork == False and typeChamp == "LONGBLOB": typeChamp = "BLOB"
                if self.isNetwork == False and typeChamp == "BIGINT": typeChamp = "INTEGER"
                listeChamps.append("%s %s" % (nomChamp, typeChamp))
                listeNomsChamps.append(nomChamp)
            varChamps = ", ".join(listeChamps)
            ##            varNomsChamps = ", ".join(listeNomsChamps)

            # Procédure de mise à jour de la table
            ##            req = "BEGIN TRANSACTION;"
            ##            req += "CREATE TEMPORARY TABLE %s_backup(%s);" % (nomTable, varChamps)
            ##            req += "INSERT INTO %s_backup SELECT %s FROM %s;" % (nomTable, ", ".join(listeNomsChamps[1:]), nomTable)
            ##            req += "DROP TABLE %s;" % nomTable
            ##            req += "CREATE TABLE %s(%s);" % (nomTable, varChamps)
            ##            req += "INSERT INTO %s SELECT %s FROM %s_backup;" % (nomTable, ", ".join(listeNomsChamps[1:]), nomTable)
            ##            req += "DROP TABLE %s_backup;" % nomTable
            ##            req += "COMMIT;"

            # Création de la table temporaire
            req = "BEGIN TRANSACTION;"
            req += "CREATE TEMPORARY TABLE %s_backup(%s);" % (
            nomTable, varChamps.replace(" PRIMARY KEY AUTOINCREMENT", ""))
            req += "INSERT INTO %s_backup SELECT %s FROM %s;" % (
            nomTable, ", ".join(listeNomsChamps), nomTable)
            req += "DROP TABLE %s;" % nomTable
            req += "CREATE TABLE %s(%s);" % (nomTable, varChamps)
            req += "COMMIT;"
            self.cursor.executescript(req)

            # Copie des données dans la table temporaire
            req = "SELECT %s FROM %s_backup;" % (
            ", ".join(listeNomsChamps[1:]), nomTable)
            self.cursor.execute(req)
            listeDonnees = self.cursor.fetchall()

            for ligne in listeDonnees:
                temp = []
                for x in range(0, len(ligne)):
                    temp.append("?")
                req = "INSERT INTO %s (%s) VALUES (%s)" % (
                nomTable, ", ".join(listeNomsChamps[1:]), ", ".join(temp))
                self.cursor.execute(req, ligne)
                self.Commit()

                # Suppression de la table temporaire
            self.cursor.execute("DROP TABLE %s_backup;" % nomTable)
            self.Commit()

            print("Reparation de la table '%s' terminee." % nomTable)

    def DropUneTable(self,nomTable=None):
        if nomTable == None : return "Absence de nom de table!!!"
        req = "DROP TABLE %s " % nomTable
        retour = self.ExecuterReq(req,MsgBox="ExecuterReq")
        if retour == "ok":
                self.Commit()
        print(retour)
        return retour
        #fin DropUneTable

    def TestTables(self, parent,dicTables, tables):
        if not tables:
            tables = dicTables.keys()
        retour = 'ok'
        for nomTable in tables:
            if self.IsTableExists(nomTable):
                continue
            retour = 'KO'
            mess = "Manque table %s, " %(nomTable)
            print(mess)
        if self and retour == 'KO':
            mess = "Des tables manquent dans cette base de donnée\n\n"
            mess += "Identifiez-vous en tant qu'admin pour pouvoir les créer, ou changez de base"
            wx.MessageBox(mess,"Création de tables nécessaires")

    def CreationUneTable(self, dicTables={},nomTable=None):
        if nomTable == None : return "Absence de nom de table!!!"
        if not dicTables or dicTables=={}:
            dicTables =DATA_Tables.DB_DATA
        req = "CREATE TABLE IF NOT EXISTS %s (" % nomTable
        for nomChamp, typeChamp, comment in dicTables[nomTable]:
            typeChamp = self.TransposeChamp(typeChamp)
            req = req + "%s %s, " % (nomChamp, typeChamp)
        req = req[:-2] + ")"
        self.cursor.execute(req)

    def CreationTables(self,dicTables, tables=None, fenetreParente=None):
        parent = fenetreParente
        if not tables:
            tables = dicTables.keys()
        nb = 0
        for nomTable in tables:
            if self.IsTableExists(nomTable):
                continue
            ret = self.CreationUneTable(dicTables=dicTables,nomTable=nomTable)
            mess = "Création de la table de données %s: %s" %(nomTable,ret)
            print(mess)
            if ret == 'ok': nb +=1
            # Affichage dans la StatusBar
            if parent:
                parent.mess += "%s %s, "%(nomTable,ret)
                parent.SetStatusText(parent.mess[-200:])
        if parent:
            parent.mess += "- Creation %d tables Terminé, "%nb
            parent.SetStatusText(parent.mess[-200:])

    def CreationIndex(self,nomIndex=None,dicIndex=None):
        try:
            """ Création d'un index """
            nomTable = dicIndex[nomIndex]["table"]
            nomChamp = dicIndex[nomIndex]["champ"]
        except Exception as err:
            return "Création index: %s"%str(err)

        retour = "Absence de table: %s"%nomTable
        if self.IsTableExists(nomTable) :
            #print "Creation de l'index : %s" % nomIndex
            if nomIndex[:7] == "PRIMARY":
                if self.typeDB == 'sqlite':
                    req = "CREATE UNIQUE INDEX %s ON %s (%s);" % (nomIndex, nomTable, nomChamp)
                else:
                    req = "ALTER TABLE %s ADD PRIMARY KEY (%s);" % (nomTable, nomChamp)
            elif nomIndex[:2] == "PK":
                req = "CREATE UNIQUE INDEX %s ON %s (%s);" % (nomIndex, nomTable, nomChamp)
            else :
                req = "CREATE INDEX %s ON %s (%s);" % (nomIndex, nomTable, nomChamp)
            retour = self.ExecuterReq(req,MsgBox="ExecuterReq")
            if retour == "ok":
                    self.Commit()
        return retour

    def CreationTousIndex(self,parent,dicIndex,tables=None,tip=None):
        """ Création de tous les index """
        if not dicIndex or dicIndex=={}:
            dicIndex =DATA_Tables.DB_INDEX
        if not tables:
            tables = DATA_Tables.DB_DATA
        self.nb = 0
        if parent and hasattr(parent, "mess"):
            rapport = True
        else: rapport = False
        for nomIndex, dict in dicIndex.items() :
            if not 'table' in dict:
                raise Exception("Structure incorrecte: shema Index '%s' - absence cle 'table'"%nomIndex)
            if not dict['table'] in tables: continue

            if nomIndex[:7] == "PRIMARY" and self.typeDB != 'sqlite':
                nomIndex = "PRIMARY"
                # test de présence car non détecté par la liste des index
                req = """
                    SELECT constraint_name
                    FROM information_schema.table_constraints
                    WHERE   table_name = '%s'
                            AND  constraint_name = 'PRIMARY';"""%(dict['table'])
                retour = self.ExecuterReq(req,MsgBox="ExecuterReq")
                if retour == 'ok':
                    recordset = self.ResultatReq()
                    if len(recordset)>0:
                        # primary exists on passe
                        continue
            idx = self.IsIndexExists(nomIndex)
            if not idx:
                ret = self.CreationIndex(nomIndex,dicIndex)
                if ret == "ok":
                    self.nb += 1
                # Affichage dans la StatusBar
                if rapport:
                    parent.mess += "%s %s, " % (nomIndex, ret)
                    parent.SetStatusText(parent.mess[-200:])
                else:
                    print("Création de l'index %s: %s" % (nomIndex, ret))

        if rapport:
            if tip == "IX":
                parent.mess += "- %d Index alt Créés"%self.nb
            elif tip == "PK":
                parent.mess += "- %d Index PK Terminés"%self.nb
            parent.SetStatusText(parent.mess[-200:])


    def Importation_table(self, nomTable="",
                          nomFichierdefault=Chemins.GetStaticPath(
                              "Databases/Defaut.dat")):
        """ Importe toutes les données d'une table donnée """
        # Ouverture de la base par défaut

        if not self.isNetwork:
            import sqlite3
            if os.path.isfile(nomFichierdefault) == False:
                print("Le fichier n'existe pas.")
                return (False, "Le fichier n'existe pas")

            try:
                connexionDefaut = sqlite3.connect(
                    nomFichierdefault.encode('utf-8'))
            except Exception as err:
                print("Echec Importation table. Erreur detectee :%s" % err)
                return (False, "Echec Importation table. Erreur detectee :%s" % err)
            else:
                cursor = connexionDefaut.cursor()

        else:
            try:
                connexionDefaut, nomFichier = GestionDB.GetConnexionReseau(
                                                            nomFichierdefault)
                cursor = connexionDefaut.cursor()

                # Ouverture Database
                cursor.execute("USE %s;" % nomFichier)

            except Exception as err:
                print(
                    "La connexion avec la base de donnees MYSQL a importer a echouee : \nErreur detectee :%s" % err)
                return (False,
                        "La connexion avec la base de donnees MYSQL a importer a echouee : \nErreur detectee :%s" % err)

        if not self.IsTableExists(nomTable):
            return (False, None)
        # Recherche des noms de champs de la table
        req = "SELECT * FROM %s" % nomTable
        cursor.execute(req)
        listeDonneesTmp = cursor.fetchall()
        listeNomsChamps = []
        for fieldDesc in cursor.description:
            listeNomsChamps.append(fieldDesc[0])

        # Préparation des noms de champs pour le transfert
        listeChamps = []
        listeMarks = []
        dictTypesChamps = GetChamps_DATA_Tables(nomTable)
        for nomChamp in listeNomsChamps[0:]:
            if nomChamp in dictTypesChamps:
                listeChamps.append(nomChamp)
                if self.isNetwork == True:
                    # Version MySQL
                    listeMarks.append("%s")
                else:
                    # Version Sqlite
                    listeMarks.append("?")

        # Récupération des données
        req = "SELECT %s FROM %s" % (", ".join(listeChamps), nomTable)
        cursor.execute(req)
        listeDonnees = cursor.fetchall()

        # Importation des données vers la nouvelle table
        req = "INSERT INTO %s (%s) VALUES (%s)" % (
        nomTable, ", ".join(listeChamps), ", ".join(listeMarks))
        try:
            # self.cursor est la base sqlite, cursor mysql
            self.cursor.executemany(req, listeDonnees)
        except Exception as err:
            print("Erreur dans l'importation de la table %s :" % nomTable)
            print(err)
            return (False, "Erreur dans l'importation de la table %s : %s" % (
            nomTable, err))
        self.connexion.commit()
        return (True, None)

    def Importation_table_reseau(self, nomTable="",nomFichier="",**kwd):
        """ Importe toutes les données de réseau à local """
        # Ouverture de la base réseau 'nomFichier'
        try:
            connexionDefaut, nomFichier = GestionDB.GetConnexionReseau(nomFichier)
            cursor = connexionDefaut.cursor()

            # Ouverture Database
            cursor.execute("USE %s;" % nomFichier)

        except Exception as err:
            print(
                "La connexion avec la base de donnees MYSQL a importer a echouee : \nErreur detectee :%s" % err)
            return (False,
                    "La connexion avec la base de donnees MYSQL a importer a echouee : \nErreur detectee :%s" % err)

        # Lecture des champs dans la table origine
        listeChamps = []
        req = "SHOW COLUMNS FROM %s;" % nomTable
        cursor.execute(req)
        listeTmpChamps = cursor.fetchall()
        # champs dans le modèle
        lstChampsDATA = GetChamps_DATA_Tables(nomTable)
        for valeurs in listeTmpChamps:
            if not valeurs[0] in lstChampsDATA:
                continue
            listeChamps.append((valeurs[0], valeurs[1]))

        # Préparation des noms de champs pour le transfert
        txtChamps = "(" + ", ".join(
            [nomChamp for nomChamp, typeChamp in listeChamps]) + ")"
        txtQMarks = "(" + ", ".join(
            ["?" for nomChamp, typeChamp in listeChamps]) + ")"

        # Récupération des données déclarées dans DATA_Tables
        req = "SELECT %s FROM %s" %(txtChamps[1:-1], nomTable)
        cursor.execute(req)
        listeDonneesTmp = cursor.fetchall()

        listeDonnees = []
        import sqlite3
        for donnees in listeDonneesTmp:
            # Analyse des données pour trouver les champs BLOB
            numColonne = 0
            listeValeurs = []
            for donnee in donnees[0:]:
                nomChamp, typeChamp = listeChamps[numColonne]
                if "BLOB" in typeChamp.upper():
                    if donnee != None:
                        donnee = sqlite3.Binary(donnee)
                listeValeurs.append(donnee)
                numColonne += 1
            listeDonnees.append(tuple(listeValeurs))

        # Importation des données vers la nouvelle table
        req = "INSERT OR IGNORE INTO %s %s VALUES %s" % (nomTable, txtChamps, txtQMarks)
        self.cursor.executemany(req, listeDonnees)
        self.connexion.commit()
        connexionDefaut.close()
        return (True, None)

    def Importation_valeurs_defaut(self, listeDonnees=[]):
        # Récupération du dictionnaire des tables Optionnelles pour l'importation
        lstTables = DATA_Tables.GetLstTablesOptions(lstOptions=listeDonnees)
        # importation des tables et valeurs par défaut
        for nomTable in lstTables:
            if self.IsTableExists(nomTable):
                self.Importation_table(nomTable)
        return True

    def CtrlTables(self, parent, dicTables, tables):
        # création de table ou ajout|modif des champs selon description fournie
        if not tables or tables == []:
            tables = dicTables.keys()
        messFix = ""
        nomTable = "aucune"
        if parent:
            messFix = parent.mess
            parent.SetStatusText(messFix)
        for nomTable in tables:
            # les possibles vues sont préfixées v_ donc ignorées
            ret = ""
            if nomTable[:2] == "v_":
                continue
            print(nomTable,end=": ")
            if not self.IsTableExists(nomTable):
                ret = self.CreationUneTable(dicTables=dicTables,nomTable=nomTable)
                mess = "Création table '%s': %s" %(nomTable,ret)
                messFix += mess
                
            # controle des champs à modifier
            else:
                tableModel = dicTables[nomTable]
                lstChampsBD = self.GetListeChamps(nomTable)
                lstNomsChampsBD = [ x[0].lower() for x in lstChampsBD]
                lstTypesChampsBD = [ x[1] for x in lstChampsBD]
                mess = "\tChamps: "
                for (nomChampModel, typeChampModel, info) in tableModel:
                    ret = None
                    # ajout du champ manquant
                    if not nomChampModel.lower() in lstNomsChampsBD:
                        ret = self.AjoutChamp(nomTable,nomChampModel,typeChampModel)
                        if ret == "ok":
                            ret = "ajouté"
                    else:
                        # modif du type de champ
                        typeChampBD = lstTypesChampsBD[lstNomsChampsBD.index(nomChampModel.lower())]
                        futurType = self.TransposeChamp(typeChampModel)
                        if self.isNetwork == True and futurType.lower() == "real":
                            futurType = "DOUBLE"
                        if futurType[:3].lower() != typeChampBD[:3].lower():
                            ret  = self.ModifTypeChamp(nomTable,nomChampModel,futurType)
                    if ret:
                        mess += "; %s.%s: %s"%(nomTable,nomChampModel,ret)
                        if ret != "ok":
                            messFix += mess
            if mess and mess != "\tChamps: ":
                print("\n" + mess)
            # Affichage dans la StatusBar
            if parent and mess:
                parent.SetStatusText(messFix + " %s %s, "%(nomTable,ret))
            if ret != None:
                print(nomTable + " fin: ",ret)
        fin = True
        if len(tables) == 0:
            messFix += "Table fournie: %s"%nomTable
            fin =  False
        elif nomTable != tables[-1]:
            # traitement inachevé
            messFix += "Traitement seulement jusqu'à table : %s"%nomTable
            fin =  False
        if parent:
            messFix += "- Fin CtrlTables = %s"%str(fin)
            parent.mess = messFix
            parent.SetStatusText(parent.mess[-200:])

        else: print(messFix)
        return fin

    def UpdateDB(self,parent, versionData=(0, 0, 0, 0) ) :
        """ Adapte un fichier obsolète à la version actuelle du logiciel """

        # exemples passé ==================================================
        """
                versionFiltre = (1, 1, 2, 3)
        if False and versionData < versionFiltre:
            try:
                self.AjoutChamp("unites", "coeff", "VARCHAR(50)")
                # ------------
                from Utils import UTILS_Procedures
                UTILS_Procedures.A8260()
                # ------------
                if self.isNetwork == True:
                    self.ExecuterReq(
                        "ALTER TABLE parametres MODIFY COLUMN parametre TEXT;")
                    self.Commit()
                # ------------
            except Exception as err:
                return " filtre de conversion %s | " % ".".join(
                    [str(x) for x in versionFiltre]) + str(err)

        versionFiltre = (1, 2, 4, 70)
        if versionData < versionFiltre:
            try:
                self.AjoutChamp("reglements", "compta", "INTEGER")
                self.AjoutChamp("matPieces", "pieComptaFac", "INTEGER")
                self.AjoutChamp("matPieces", "pieComptaAvo", "INTEGER")
                self.AjoutChamp("prestations", "compta", "INTEGER")
                self.AjoutChamp("inscriptions", "jours", "INTEGER")
                self.AjoutChamp("types_groupes_activites", "anaTransports",
                                "VARCHAR(8)")
                print("Mise a niveau base %s\t\t\t\t>>>>>>> OK" % ".".join(
                    [str(x) for x in versionFiltre]))
            except Exception as err:
                return " filtre de conversion %s | " % ".".join(
                    [str(x) for x in versionFiltre]) + str(err)

        versionFiltre = (1, 2, 5, 90)
        if versionData < versionFiltre:
            from Utils import UTILS_SaisieAdresse
            try:
                UTILS_SaisieAdresse.RemonteSecteurs()
                self.ModifClePrimaire("matParrainages",
                                      "parIDinscription,parIDligneParr")
                print("Mise a niveau base %s\t\t\t\t>>>>>>> OK" % ".".join(
                    [str(x) for x in versionFiltre]))
            except Exception as err:
                return " filtre de conversion %s | " % ".".join(
                    [str(x) for x in versionFiltre]) + str(err)

        versionFiltre = (1, 2, 5, 91)
        if versionData < versionFiltre:
            try:
                Ajout_IndexMat()
                self.AjoutChamp("individus", "adresse_normee", "INTEGER NULL"),
                self.AjoutChamp("individus", "refus_pub", "INTEGER NULL"),
                self.AjoutChamp("individus", "refus_mel", "INTEGER NULL"),
                self.AjoutChamp("familles", "refus_pub", "INTEGER NULL"),
                self.AjoutChamp("familles", "refus_mel", "INTEGER NULL"),
                self.AjoutChamp("familles", "adresse_intitule",
                                "VARCHAR(100) NULL"),
                self.AjoutChamp("familles", "adresse_individu",
                                "INTEGER NULL"),
                self.AjoutChamp("corrections_villes", "pays",
                                "VARCHAR(48) NULL"),
                self.AjoutChamp("listes_diffusion", "abrege",
                                "VARCHAR(8) NULL"),
                print("Mise a niveau base %s\t\t\t\t>>>>>>> OK" % ".".join(
                    [str(x) for x in versionFiltre]))
            except Exception as err:
                return " filtre de conversion %s | " % ".".join(
                    [str(x) for x in versionFiltre]) + str(err)

        versionFiltre = (1, 3, 1, 13)
        if versionData <= versionFiltre:
            try:
                Init_tables(parent=parent, mode='creation', tables=["releases"],
                            db_tables=Data.DATA_Tables.DB_DOCUMENTS,
                            suffixe="DOCUMENTS")
                print("Mise a niveau base %s\t\t\t\t>>>>>>> OK" % ".".join(
                    [str(x) for x in versionFiltre]))
            except Exception as err:
                return " filtre de conversion %s | " % ".".join(
                    [str(x) for x in versionFiltre]) + str(err)
        """
        versionFiltre = (1, 3, 2, 40)
        if versionData < versionFiltre:
            try:
                Ajout_IndexMat(parent=parent)
                print("Mise a niveau base %s\t\t\t\t>>>>>>> OK" % ".".join(
                    [str(x) for x in versionFiltre]))
            except Exception as err:
                return " filtre de conversion %s | " % ".".join(
                    [str(x) for x in versionFiltre]) + str(err)
        return True

def ConversionLocalReseau(nomFichier="", nouveauFichier="", fenetreParente=None):
    """ Convertit une DB locale en version RESEAU MySQL """
    print("Lancement de la procedure de conversion local->reseau :")

    for suffixe, dictTables in ( ("DATA", DATA_Tables.DB_DATA),
                                 ("PHOTOS", DATA_Tables.DB_PHOTOS),
                                 ("DOCUMENTS", DATA_Tables.DB_DOCUMENTS) ) :

        nomFichierActif = UTILS_Fichiers.GetRepData(u"%s_%s.dat" % (nomFichier, suffixe))
        nouveauNom = nouveauFichier[nouveauFichier.index("[RESEAU]"):].replace("[RESEAU]", "")

        dictResultats = GestionDB.TestConnexionMySQL(typeTest="fichier", nomFichier=u"%s_%s" % (nouveauNom, suffixe) )
        # Vérifie la connexion au réseau
        if dictResultats["connexion"][0] == False :
            erreur = dictResultats["connexion"][1]
            print("connexion reseau MySQL impossible.")
            return (False, "La connexion au réseau MySQL est impossible")

        # Vérifie que le fichier n'est pas déjà utilisé
        if dictResultats["fichier"][0] == True :
            print("le nom existe deja.")
            return (False, "Le fichier existe déjà")

        # Création de la base de données
        if fenetreParente != None : fenetreParente.SetStatusText(u"Conversion du fichier en cours... Création du fichier réseau...")
        db = DB(suffixe=suffixe, nomFichier=nouveauFichier, modeCreation=True)
        if db.echec == 1 :
            message = "Erreur dans la création du fichier.\n\nErreur : %s" % db.erreur
            return (False, message)
        print("  > Nouveau fichier reseau %s cree..." % suffixe)

        # Création des tables
        if fenetreParente != None : fenetreParente.SetStatusText(u"Conversion du fichier en cours... Création des tables de données %s..." % suffixe)
        db.CreationTables(dictTables)
        print("  > Nouvelles tables %s creees..." % suffixe)

        # Importation des valeurs
        listeTables = list(dictTables.keys())
        index = 1
        for nomTable in listeTables :
            print("  > Importation de la table '%s' (%d/%d)" % (nomTable, index, len(listeTables)))
            if fenetreParente != None : fenetreParente.SetStatusText(u"Conversion du fichier en cours... Importation de la table %d sur %s..." % (index, len(listeTables)))
            resultat = db.Importation_table(nomTable, nomFichierActif)
            if resultat[0] == False :
                db.Close()
                return resultat
            else :
                print("     -> ok")
            index += 1

        db.Close()

    print("  > Conversion terminee avec succes.")
    return (True, None)

def ConversionReseauLocal(nomFichier="", nouveauFichier="", fenetreParente=None):
    """ Convertit une DB RESEAU MySQL en version LOCALE SQLITE """
    print("Lancement de la procedure de conversion reseau->local :")

    # Vérifie que le fichier n'est pas déjà utilisé
    nouveauNom = UTILS_Fichiers.GetRepData(
        u"%s_%s.dat" % (nouveauFichier, "DATA"))
    if os.path.isfile(nouveauNom) == True:
        mess = "Le fichier '%s' existe déjà\n\n" % nouveauNom
        mess += "Complète-t-on le fichier existant?"
        ret = wx.MessageBox(mess, "Confirmez...",
                            wx.YES_NO | wx.CANCEL | wx.ICON_INFORMATION,
                            fenetreParente)
        if ret != wx.YES:
            return (False, "Abandon de l'opération")

    # déroule les trois types de base de donnée
    attente = fp.GetAttente(None,"Conversion des données, suivi en bas de l'écran")
    for suffixe, dictTables in ( ("DATA", DATA_Tables.DB_DATA), ("PHOTOS", DATA_Tables.DB_PHOTOS), ("DOCUMENTS", DATA_Tables.DB_DOCUMENTS) ) :
        nouveauNom = UTILS_Fichiers.GetRepData(u"%s_%s.dat" % (nouveauFichier, suffixe))

        # Création de la base de données
        if fenetreParente != None : fenetreParente.SetStatusText("Création du fichier local...")
        db = DB(suffixe=suffixe, nomFichier=nouveauFichier, modeCreation=True)
        if db.echec == 1 :
            erreur = db.erreur
            dlg = wx.MessageDialog(None, "Erreur dans la création du fichier.\n\nErreur : %s" % erreur, "Erreur de création de fichier", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return (False, "Abandon de l'opération")
        print("  > Nouveau fichier local %s cree..." % suffixe)

        # Création des tables
        if fenetreParente != None : fenetreParente.SetStatusText("Conversion du fichier en cours... Création des tables de données %s..." % suffixe)
        db.CreationTables(dictTables)
        print("  > Nouvelles tables %s creees..." % suffixe)

        # Importation des valeurs sur les seules tables présentes
        dbOrigine = DB(suffixe=suffixe,nomFichier=nomFichier)
        lstTablesOrigine = dbOrigine.GetListeTables()
        dbOrigine.Close()
        listeTables = list(dictTables.keys())
        index = 1
        for nomTable in listeTables :
            if not nomTable.lower() in lstTablesOrigine:
                continue
            print("  > Importation de la table '%s' (%d/%d)" % (nomTable, index, len(listeTables)))
            if fenetreParente != None : fenetreParente.SetStatusText(u"Conversion du fichier en cours... Importation de la table %d sur %s..." % (index, len(listeTables)))
            resultat = db.Importation_table_reseau(nomTable, "%s_%s" % (nomFichier, suffixe))
            if resultat[0] == False :
                db.Close()
                return resultat
            else :
                print("     -> ok")
            index += 1
        db.Close()
    del attente
    print("  > Conversion reseau->local terminee avec succes.")
    return (True, "  > Conversion reseau->local terminee avec succes.")

def Decod(valeur):
    return GestionDB.Decod(valeur)
# ----------- Outils d'adaptation des bases ------------------------------

def GetChamps_DATA_Tables(nomTable=""):
        for dictTables in (
        DATA_Tables.DB_DATA, DATA_Tables.DB_PHOTOS, DATA_Tables.DB_DOCUMENTS):
            if nomTable in dictTables:
                listeChamps = []
                for nom, typeTable, info in dictTables[nomTable]:
                    listeChamps.append(nom)
                return listeChamps
        return []

class Ajout_IndexMat(wx.Frame):
    # lançé à la mano ou dans les releases cf exemple anciennes releases
    def __init__(self,parent=None):
        """Constructor"""
        wx.Frame.__init__(self, parent=parent, size=(550, 400))
        self.mess = ""
        nb = 0
        if parent:
            parent.mess = ""
            frame = parent
        else:
            frame = self
        DB1 = DB(suffixe="DATA", modeCreation=False)
        DB1.CreationTousIndex(frame,DATA_Tables.DB_PK,tip="PK")
        if DB1.retourReq != "ok" :
            dlg = wx.MessageDialog(self, "Erreur base de données.\n\nErreur : %s" % DB1.retourReq,
                                   "Erreur de création d'index PK", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
        nb += DB1.nb
        DB1.CreationTousIndex(frame,DATA_Tables.DB_INDEX,tip="IX")
        if DB1.retourReq != "ok" :
            dlg = wx.MessageDialog(self, "Erreur base de données.\n\nErreur : %s" % DB1.retourReq,
                                   "Erreur de création d'index IX", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
        nb += DB1.nb
        DB1.Close()
        if parent:
            parent.SetStatusText(parent.mess[-200:])
            self.mess = "Ctrl des Index\n\n" + parent.mess
        if nb >0:
            wx.MessageBox(self.mess,"Fin travail")

def Init_tables(parent=None, mode='creation',tables=[],
                db_tables=None,db_ix=None,db_pk=None,suffixe="DATA"):
    # actualise ou vérifie la structure des tables : test, creation, ctrl
    db = DB(suffixe=suffixe)
    if db.echec: return False

    if hasattr(db,'cursor'):
        del db.cursor

    db.cursor = db.connexion.cursor()
    ret = None
    if parent:
        parent.mess += " >> "
        parent.SetStatusText(parent.mess[-200:])

    # ne fait que la création de nouvelles tables et les indexe
    if mode == "creation":
        ret = db.CreationTables(db_tables,tables,fenetreParente=parent)

        # réinit complet de db pour prendre en compte les nouvelles tables
        del db.cursor
        db.Close()
        db = DB()
        db.cursor = db.connexion.cursor()

        db.CreationTousIndex(parent,db_ix, tables,tip="IX")
        if not db_pk or db_pk=={}:
            db_pk = DATA_Tables.DB_PK
        db.CreationTousIndex(parent,db_pk, tables,tip="PK")

    # Crée les tables et ajoute les champs manquants dans les présentes
    elif mode == "ctrl":
        ret = db.CtrlTables(parent,db_tables,tables)

    db.Close() # fermeture pour prise en compte de la création
    return ret

def MAJ_TablesEtChamps(parent=None, mode='ctrl',lstTables=[]):
    if not UTILS_Utilisateurs.IsAdmin(afficheMessage=True):
        return
    # Complète une bd spécifique pour fonctionner avec cette version Noethys
    from Data.DATA_Tables import DB_DATA,DB_INDEX,DB_DOCUMENTS,DB_PHOTOS
    tblOptionnelles = []
    allTables = False
    if not lstTables: lstTables = []
    if len(lstTables) == 0 :
        allTables = True
        tblOptionnelles = Data.DATA_Tables.GetLstTablesOptions()
    tables = []
    db_tables = {}
    db_ix = {}
    for nomTable, dicTable in DB_DATA.items():
        if nomTable in tblOptionnelles:
            continue
        if (not allTables) and not (nomTable in lstTables):
            continue
        tables.append(nomTable)
        db_tables[nomTable] = dicTable
    for nomIndex, dicIndex in DB_INDEX.items():
        if dicIndex["table"] in tables:
            db_ix[nomIndex] = dicIndex
    if len(db_ix.keys()) == 0:
        db_ix = None
    libModes = {'creation': "Création",
                "test": "Vérification sans modif",
                "ctrl": "Création ou correction"}
    if not lstTables or lstTables == []:
        if mode in ('creation', 'test'):
            txt = "de toutes les tables manquantes à l'appli mère"
        else: txt = "de toutes les tables et de leurs champs"

        infoVersions = "lancement direct sur base de donnée par défaut"
        if parent:
            infoVersions = "%s"%parent.infoVersions
        md = wx.MessageDialog(
                parent,
                "%s %s:\n\n'%s...'\n\nConfirmez qu'il s'agit d'un upgrade normal de Noethys!"%(libModes[mode],
                                                  txt,
                                                  infoVersions,),
                "Confirmation nécessaire",
                style=wx.YES_NO|wx.ICON_EXCLAMATION)
        if md.ShowModal() != wx.ID_YES:
            return False
    mess = "Traitement Ctrl des tables de données "
    mess += "\n\n Suivi en bas de l'écran et fenêtre DOS"
    attente = fp.GetAttente(parent,mess)

    if parent:
        parent.mess = "Upgrade _DATA -"
    # traitement de la base _data
    ret = Init_tables(parent,mode=mode,tables=tables,db_tables=db_tables,db_ix=db_ix)

    # traitement des deux autres bases
    for suffixe, base in (("DOCUMENTS", DB_DOCUMENTS),("PHOTOS",DB_PHOTOS)):
        if parent:
            parent.mess += " - %s -"%suffixe
        tables = []
        db_tables = {}
        for nomTable, dicTable in base.items():
            if (not allTables) and not (nomTable in lstTables):
                continue
            tables.append(nomTable)
            db_tables[nomTable] = dicTable
            ret = Init_tables(parent, mode=mode, tables=tables,
                          db_tables=db_tables, suffixe=suffixe)
    del attente

    wx.MessageBox("Fin du contrôle tables et champs"," ",style=wx.OK)
    return True

if __name__ == "__main__":
    app = wx.App()
    #f = Ajout_TablesMat()
    #f = Ajout_IndexMat()
    #DB1 = DB()
    #retour = DB1.ConversionDB((1,2,5,89))
    #retour = DB1.UtilisateurActuel()
    #DB1.Close()

    #MessageBox(None,retour,titre="Résultat Test")
    #db = DB()
    #ret = db.DropTable('v_clients')

    #gdb = GestionBase()#nomFichier=u'3306;192.168.1.43;root;motdepasse[RESEAU]information_schema',suffixe=None
    #print(gdb.GetOccupations())

    # Update de la base de données : def ConversionDB(self, versionData=(0, 0, 0, 0) )
    MAJ_TablesEtChamps(None,mode='ctrl',lstTables=["documents"])

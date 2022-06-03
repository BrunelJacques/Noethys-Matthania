#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Module : Génération du pdf à partir du DictValeurs venant d'UTILS_Facturation
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
# Adaptation sur les tri des blocs, sur les noms au lieu des textes
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import wx
import Chemins
import os
import datetime
import decimal
import FonctionsPerso
from Utils.UTILS_Decimal import FloatToDecimal as FloatToDecimal
from Utils import UTILS_Fichiers
from Dlg import DLG_Noedoc

from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")

from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate, NextPageTemplate
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus.flowables import Image
from reportlab.platypus.frames import Frame
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.barcode import code39, qr
from reportlab.platypus.flowables import DocAssign, Flowable

TAILLE_PAGE = A4
LARGEUR_PAGE = TAILLE_PAGE[0]
HAUTEUR_PAGE = TAILLE_PAGE[1]
CADRE_CONTENU = (5*cm, 5*cm, 14*cm, 17*cm)
    
DICT_VALEURS = {}
DICT_OPTIONS = {} 

def DateEngFr(textDate):
    if textDate == None: return ""
    textDate = str(textDate)
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text

def PeriodeComplete(mois, annee):
    listeMois = (_("Janvier"), _("Février"), _("Mars"), _("Avril"), _("Mai"), _("Juin"), _("Juillet"), _("Août"), _("Septembre"), _("Octobre"), _("Novembre"), _("Décembre"))
    periodeComplete = "%02d/%d" % (mois, annee)
    return periodeComplete

def ConvertCouleurWXpourPDF(couleurwx=(0, 0, 0)):
    return (couleurwx[0]/255.0, couleurwx[1]/255.0, couleurwx[2]/255.0)

def ConvertCouleurPDFpourWX(couleurpdf=(0, 0, 0)):
    return (couleurpdf[0]*255.0, couleurpdf[1]*255.0, couleurpdf[2]*255.0)

def Template(canvas, doc):
    """ Première page de l'attestation """
    doc.modeleDoc.DessineFond(canvas) 
    doc.modeleDoc.DessineFormes(canvas)

class MyPageTemplate(PageTemplate):
    def __init__(self, id=-1, pageSize=TAILLE_PAGE, doc=None):
        self.pageWidth = pageSize[0]
        self.pageHeight = pageSize[1]
        
        # Récupère les coordonnées du cadre principal
        cadre_principal = doc.modeleDoc.FindObjet("cadre_principal")
        x, y, l, h = doc.modeleDoc.GetCoordsObjet(cadre_principal)
        global CADRE_CONTENU
        CADRE_CONTENU = (x, y, l, h)
        
        frame1 = Frame(x, y, l, h, id='F1', leftPadding=0, topPadding=0, rightPadding=0, bottomPadding=0)
        PageTemplate.__init__(self, id, [frame1], Template) 

    def afterDrawPage(self, canvas, doc):
        IDcompte = doc._nameSpace["IDcompte"]
        dictValeur = DICT_VALEURS[IDcompte]
        
        # Dessin du coupon-réponse vertical
        coupon_vertical = doc.modeleDoc.FindObjet("coupon_vertical")
        if "afficher_coupon_reponse" in DICT_OPTIONS and DICT_OPTIONS["afficher_coupon_reponse"] == True and coupon_vertical != None :
            x, y, largeur, hauteur = doc.modeleDoc.GetCoordsObjet(coupon_vertical)
            canvas.saveState() 
            # Ciseaux
            canvas.drawImage(Chemins.GetStaticPath("Images/Special/Ciseaux.png"), x+1*mm, y+hauteur-5*mm, 0.5*cm, 1*cm, preserveAspectRatio=True)
            # Rectangle
            canvas.setDash(3, 3)
            canvas.setLineWidth(0.25)
            canvas.setStrokeColorRGB(0, 0, 0)
            canvas.rect(x, y, largeur, hauteur, fill=0)
            # Textes
            soldeCR = dictValeur["montant"] - dictValeur["ventilation"]
            if DICT_OPTIONS["integrer_impayes"] == True :
                soldeCR += dictValeur["total_reports"]
            numero = dictValeur["numero"]
            nom = dictValeur["nomSansCivilite"]
            canvas.rotate(90)
            canvas.setFont("Helvetica", 8)
            canvas.drawString(y+2*mm, -x-4*mm, _("Merci de joindre ce coupon à votre règlement "))
            canvas.setFont("Helvetica", 7)
            canvas.drawString(y+2*mm, -x-7*mm, "%s - %.02f %s" % ("Montant : ", soldeCR, SYMBOLE))
            canvas.drawString(y+2*mm, -x-10*mm, "%s / %d " % (numero,dictValeur["IDfamille"] ))
            canvas.drawString(y+2*mm, -x-13*mm, "%s" % nom)
            # Code-barres
            if DICT_OPTIONS["afficher_codes_barres"] == True and "{CODEBARRES_NUM_FACTURE}" in dictValeur :
                barcode = code39.Extended39(dictValeur["{CODEBARRES_NUM_FACTURE}"], humanReadable=False)
                barcode.drawOn(canvas, y+46*mm, -x-13*mm)
            canvas.restoreState()

        # Dessin du coupon-réponse horizontal
        coupon_horizontal = doc.modeleDoc.FindObjet("coupon_horizontal")
        if "afficher_coupon_reponse" in DICT_OPTIONS and DICT_OPTIONS["afficher_coupon_reponse"] == True and coupon_horizontal != None :
            x, y, largeur, hauteur = doc.modeleDoc.GetCoordsObjet(coupon_horizontal)
            canvas.saveState() 
            # Rectangle
            canvas.setDash(3, 3)
            canvas.setLineWidth(0.25)
            canvas.setStrokeColorRGB(0, 0, 0)
            canvas.rect(x, y, largeur, hauteur, fill=0)
            # Textes
            canvas.setFont("Helvetica", 8)
            canvas.drawString(x+2*mm, y+hauteur-4*mm, _("Merci de joindre ce coupon à votre règlement"))
            canvas.setFont("Helvetica", 7)
            soldeCR = dictValeur["montant"] - dictValeur["ventilation"]
            if DICT_OPTIONS["integrer_impayes"] == True :
                soldeCR += dictValeur["total_reports"]
            numero = dictValeur["numero"]
            nom = dictValeur["nomSansCivilite"]
            canvas.drawString(x+2*mm, y+hauteur-9*mm, "%s - %.02f %s" % (numero, soldeCR, SYMBOLE))
            canvas.drawString(x+2*mm, y+hauteur-12*mm, "%s" % nom)
            # Code-barres
            if DICT_OPTIONS["afficher_codes_barres"] == True :
                barcode = code39.Extended39(dictValeur["{CODEBARRES_NUM_FACTURE}"], humanReadable=False)
                barcode.drawOn(canvas, x+36*mm, y+hauteur-13*mm)
            # Ciseaux
            canvas.rotate(-90)
            canvas.drawImage(Chemins.GetStaticPath("Images/Special/Ciseaux.png"), -y-hauteur+1*mm, x+largeur-5*mm, 0.5*cm, 1*cm, preserveAspectRatio=True)
            canvas.restoreState()

        canvas.saveState() 
        
        # Insertion du code39
        if "afficher_codes_barres" in DICT_OPTIONS and DICT_OPTIONS["afficher_codes_barres"] == True :
            doc.modeleDoc.DessineCodesBarres(canvas, dictChamps=dictValeur)
        
        # Insertion des lignes de textes
        doc.modeleDoc.DessineImages(canvas, dictChamps=dictValeur)
        doc.modeleDoc.DessineTextes(canvas, dictChamps=dictValeur)
        
        canvas.restoreState()

def Template_PagesSuivantes(canvas, doc):
    """ Première page de l'attestation """
    canvas.saveState()

    canvas.setFont('Times-Roman', 12)
    pageNumber = canvas.getPageNumber()
    canvas.drawCentredString(10*cm, cm, str(pageNumber))

    canvas.restoreState()

class Bookmark(Flowable):
    """ Utility class to display PDF bookmark. """
    def __init__(self, title, key):
        self.title = title
        self.key = key
        Flowable.__init__(self)

    def wrap(self, availWidth, availHeight):
        """ Doesn't take up any space. """
        return (0, 0)

    def draw(self):
        # set the bookmark outline to show when the file's opened
        self.canv.showOutline()
        # step 1: put a bookmark on the 
        self.canv.bookmarkPage(self.key)
        # step 2: put an entry in the bookmark outline
        self.canv.addOutlineEntry(self.title, self.key, 0, 0)

class Impression():
    def __init__(self, dictValeurs={}, dictOptions={}, IDmodele=None, mode="_", ouverture=True, nomFichier=None, titre=None):
        """ Impression """
        global DICT_VALEURS, DICT_OPTIONS
        DICT_VALEURS = dictValeurs
        DICT_OPTIONS = dictOptions
        
        detail = 0
        if dictOptions["affichage_prestations"] != None :
            detail = dictOptions["affichage_prestations"]

        # Initialisation des largeurs de tableau
        largeurColonneDate = dictOptions["largeur_colonne_date"]
        largeurColonneMontantHT = dictOptions["largeur_colonne_montant_ht"]
        largeurColonneTVA = dictOptions["largeur_colonne_montant_tva"]
        largeurColonneMontantTTC = dictOptions["largeur_colonne_montant_ttc"]
        largeurColonneBaseTTC = largeurColonneMontantTTC

        # Initialisation du document
        if nomFichier == None :
            nomFichier = _("%ss_%s.pdf") % (mode, FonctionsPerso.GenerationIDdoc())
        nomDoc = nomFichier
        if not "\\" in nomFichier:
            nomDoc = UTILS_Fichiers.GetRepTemp(nomFichier)

        doc = BaseDocTemplate(nomDoc, pagesize=TAILLE_PAGE, showBoundary=False)
        
        # Mémorise le ID du modèle
        modeleDoc = DLG_Noedoc.ModeleDoc(IDmodele=IDmodele)
        doc.modeleDoc = modeleDoc

        # Vérifie qu'un cadre principal existe bien dans le document
        if doc.modeleDoc.FindObjet("cadre_principal") == None :
            raise Exception("Votre modèle de document doit obligatoirement comporter un cadre principal. Retournez dans l'éditeur de document et utilisez pour votre modèle la commande 'Insérer un objet spécial > Insérer le cadre principal'.")
        
        # Importe le template de la première page
        doc.addPageTemplates(MyPageTemplate(pageSize=TAILLE_PAGE, doc=doc))
        
        story = []
        styleSheet = getSampleStyleSheet()
        h3 = styleSheet['Heading3']
        styleTexte = styleSheet['BodyText'] 
        styleTexte.fontName = "Helvetica"
        styleTexte.fontSize = 9
        styleTexte.borderPadding = 9
        styleTexte.leading = 12

        # ----------- Insertion du contenu des frames --------------
        listeNomsSansCivilite = []
        for IDcompte, dictValeur in dictValeurs.items() :
            listeNomsSansCivilite.append((dictValeur["nomSansCivilite"], IDcompte))
        listeNomsSansCivilite.sort()

        for nomSansCivilite, IDcompte in listeNomsSansCivilite :
            dictValeur = dictValeurs[IDcompte]
            if not "montant" in dictValeur:
                dictValeur["montant"] = dictValeur["total"]
            if dictValeur["select"] == True :
                
                story.append(DocAssign("IDcompte", IDcompte))
                nomSansCivilite = dictValeur["nomSansCivilite"]
                story.append(Bookmark(nomSansCivilite, str(IDcompte)))
                
                # ------------------- TITRE -----------------
                if dictOptions["afficher_titre"] == True :
                    if "{NATURE}" in dictValeur :
                        titre = dictValeur["{NATURE}"]
                    else : titre = ""
                    dataTableau = []
                    largeursColonnes = [ CADRE_CONTENU[2], ]
                    dataTableau.append((titre,))
                    texteDateDebut = DateEngFr(str(dictValeur["date_debut"]))
                    texteDateFin = DateEngFr(str(dictValeur["date_fin"]))
                    if dictOptions["afficher_periode"] == True :
                        dataTableau.append((_("Période du %s au %s") % (texteDateDebut, texteDateFin),))
                    styles = [
                            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), 
                            ('FONT',(0,0),(0,0), "Helvetica-Bold", dictOptions["taille_texte_titre"]), 
                            ('LINEBELOW', (0,0), (0,0), 0.25, colors.black), 
                            ('ALIGN', (0,0), (-1,-1), 'LEFT'), 
                            ]
                    
                    if dictOptions["afficher_periode"] == True :
                        styles.append(('FONT',(0,1),(0,1), "Helvetica", dictOptions["taille_texte_periode"]))
                    tableau = Table(dataTableau, largeursColonnes)
                    tableau.setStyle(TableStyle(styles))
                    story.append(tableau)
                    story.append(Spacer(0,20))
                
                # TEXTE D'INTRODUCTION pour Attestation
                #  if mode == "attestation" and dictValeur["intro"] != None :

                if dictOptions["texte_introduction"] != "" :
                    paraStyle = ParagraphStyle(name="introduction",
                                          fontName="Helvetica",
                                          fontSize=dictOptions["taille_texte_introduction"],
                                          leading=14,
                                          spaceBefore=0,
                                          spaceafter=0,
                                          leftIndent=5,
                                          rightIndent=5,
                                          alignment=dictOptions["alignement_texte_introduction"],
                                          backColor=ConvertCouleurWXpourPDF(dictOptions["couleur_fond_introduction"]),
                                          borderColor=ConvertCouleurWXpourPDF(dictOptions["couleur_bord_introduction"]),
                                          borderWidth=0.5,
                                          borderPadding=5,
                                        )
                    texte = dictValeur["texte_introduction"].replace("\\n", "<br/>")
                    if dictOptions["style_texte_introduction"] == 0 : texte = "<para>%s</para>" % texte
                    if dictOptions["style_texte_introduction"] == 1 : texte = "<para><i>%s</i></para>" % texte
                    if dictOptions["style_texte_introduction"] == 2 : texte = "<para><b>%s</b></para>" % texte
                    if dictOptions["style_texte_introduction"] == 3 : texte = "<para><i><b>%s</b></i></para>" % texte
                    story.append(Paragraph(texte, paraStyle))
                    story.append(Spacer(0,20))

                couleurFond = ConvertCouleurWXpourPDF(dictOptions["couleur_fond_1"]) # (0.8, 0.8, 1)
                couleurFondActivite = ConvertCouleurWXpourPDF(dictOptions["couleur_fond_2"]) # (0.92, 0.92, 1)

                # ------------------- TABLEAU CONTENU -----------------
                montantPeriode = FloatToDecimal(0.0)
                montantVentilation = FloatToDecimal(0.0)

                # Recherche si TVA utilisée
                activeTVA = False
                for IDindividu, dictIndividus in dictValeur["individus"].items() :
                    for IDactivite, dictActivites in dictIndividus["activites"].items() :
                        for date, dictDates in dictActivites["presences"].items() :
                            for dictLigne in dictDates["unites"] :
                                if dictLigne["tva"] != None and dictLigne["tva"] != 0.0 :
                                    activeTVA = True

                # Remplissage
                listeIndividusTemp = []
                for IDindividu, dictIndividus in dictValeur["individus"].items() :
                    if not "montant" in dictIndividus:
                        dictIndividus["montant"] = dictIndividus["total"]
                    listeIndividusTemp.append((dictIndividus["nom"], IDindividu, dictIndividus))
                listeIndividusTemp.sort()

                for texteTemp, IDindividu, dictIndividus in listeIndividusTemp :
                    listeIndexActivites = []
                    montantPeriode += dictIndividus["montant"]
                    montantVentilation += dictIndividus["ventilation"]

                    if activeTVA == True and detail == 0 :
                        largeurColonneIntitule = CADRE_CONTENU[2] - largeurColonneDate - largeurColonneMontantHT - largeurColonneTVA - largeurColonneMontantTTC
                        largeursColonnes = [ largeurColonneDate, largeurColonneIntitule, largeurColonneMontantHT, largeurColonneTVA, largeurColonneMontantTTC]
                    else :
                        if detail != 0 :
                            largeurColonneIntitule = CADRE_CONTENU[2] - largeurColonneDate - largeurColonneBaseTTC - largeurColonneMontantTTC
                            largeursColonnes = [ largeurColonneDate, largeurColonneIntitule, largeurColonneBaseTTC, largeurColonneMontantTTC]
                        else :
                            largeurColonneIntitule = CADRE_CONTENU[2] - largeurColonneDate - largeurColonneMontantTTC
                            largeursColonnes = [ largeurColonneDate, largeurColonneIntitule, largeurColonneMontantTTC]

                    # Insertion du nom de l'individu
                    paraStyle = ParagraphStyle(name="individu",
                                          fontName="Helvetica",
                                          fontSize=dictOptions["taille_texte_individu"],
                                          leading=dictOptions["taille_texte_individu"],
                                          spaceBefore=0,
                                          spaceafter=0,
                                        )
                    texteIndividu = Paragraph(dictIndividus["texte"], paraStyle)
                    dataTableau = []
                    dataTableau.append([texteIndividu,])
                    tableau = Table(dataTableau, [CADRE_CONTENU[2],])
                    listeStyles = [
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('FONT', (0, 0), (-1, -1), "Helvetica", dictOptions["taille_texte_individu"]),
                            ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
                            ('BACKGROUND', (0, 0), (-1, 0), couleurFond),
                            ]
                    tableau.setStyle(TableStyle(listeStyles))
                    story.append(tableau)

                    # Insertion du nom de l'activité
                    listeIDactivite = []
                    for IDactivite, dictActivites in dictIndividus["activites"].items() :
                        listeIDactivite.append((dictActivites["texte"], IDactivite, dictActivites))
                    listeIDactivite.sort()

                    for texteActivite, IDactivite, dictActivites in listeIDactivite :

                        texteActivite = dictActivites["texte"]
                        if texteActivite != None :
                            dataTableau = []
                            dataTableau.append([texteActivite,])
                            tableau = Table(dataTableau, [CADRE_CONTENU[2],])
                            listeStyles = [
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                ('FONT', (0, 0), (-1, -1), "Helvetica", dictOptions["taille_texte_activite"]),
                                ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
                                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                ('BACKGROUND', (0, 0), (-1, 0), couleurFondActivite),
                                ]
                            tableau.setStyle(TableStyle(listeStyles))
                            story.append(tableau)

                        # Style de paragraphe normal
                        paraStyle = ParagraphStyle(name="prestation",
                                      fontName="Helvetica",
                                      fontSize=dictOptions["taille_texte_prestation"],
                                      leading=dictOptions["taille_texte_prestation"],
                                      spaceBefore=0,
                                      spaceAfter=0,
                                      )

                        paraLabelsColonnes = ParagraphStyle(name="paraLabelsColonnes",
                                      fontName="Helvetica",
                                      fontSize=dictOptions["taille_texte_noms_colonnes"],
                                      leading=dictOptions["taille_texte_noms_colonnes"],
                                      spaceBefore=0,
                                      spaceAfter=0,
                                      )

                        # Insertion de la date -- MODE DETAILLE ---------------------------------------------------
                        listeDates = []
                        for date, dictDates in dictActivites["presences"].items() :
                            listeDates.append(date)
                        listeDates.sort()

                        paraStyle = ParagraphStyle(name="prestation",
                                      fontName="Helvetica",
                                      fontSize=dictOptions["taille_texte_prestation"],
                                      leading=dictOptions["taille_texte_prestation"],
                                      spaceBefore=0,
                                      spaceAfter=0,
                                      )

                        dataTableau = []

                        if activeTVA == True :
                            dataTableau.append([
                                Paragraph(_("<para align='center'>Date</para>"), paraLabelsColonnes),
                                Paragraph(_("<para align='center'>Prestation</para>"), paraLabelsColonnes),
                                Paragraph(_("<para align='center'>Montant HT</para>"), paraLabelsColonnes),
                                Paragraph(_("<para align='center'>Taux TVA</para>"), paraLabelsColonnes),
                                Paragraph(_("<para align='center'>Montant TTC</para>"), paraLabelsColonnes),
                                ])

                        for date in listeDates :
                            dictDates = dictActivites["presences"][date]

                            lignes = dictDates["unites"]

                            # Insertion des unités de présence
                            listeIntitules = []
                            listeMontantsHT = []
                            listeTVA = []
                            listeMontantsTTC = []
                            texteIntitules = ""
                            texteMontantsHT = ""
                            texteTVA = ""
                            texteMontantsTTC = ""

                            # Tri par ordre alpha des lignes
                            listeDictLignes = []
                            for dictLigne in lignes :
                                listeDictLignes.append((dictLigne["label"], dictLigne))
                            #listeDictLignes.sort()

                            for labelTemp, dictLigne in listeDictLignes :
                                label = dictLigne["label"]
                                montant = dictLigne["montant"]
                                deductions = dictLigne["deductions"]
                                tva = dictLigne["tva"]

                                # Date
                                #texteDate = Paragraph("<para align='center'>%s</para>" % date, paraStyle)
                                texteDate = " "

                                # recherche d'un commentaire
                                if "dictCommentaires" in dictOptions :
                                    key = (label, IDactivite)
                                    if key in dictOptions["dictCommentaires"] :
                                        commentaire = dictOptions["dictCommentaires"][key]
                                        label = "%s <i><font color='#939393'>%s</font></i>" % (label, commentaire)

                                # Affiche le Label de la prestation
                                if label == None:
                                    label = "Pour l'ensemble de la famille"
                                listeIntitules.append(Paragraph(label, paraStyle))

                                # TVA
                                if activeTVA == True :
                                    if tva == None : tva = 0.0
                                    montantHT = (100.0 * float(montant)) / (100 + float(tva)) #montant - montant * 1.0 * float(tva) / 100
                                    listeMontantsHT.append(Paragraph("<para align='center'>%.02f %s</para>" % (montantHT, SYMBOLE), paraStyle))
                                    listeTVA.append(Paragraph("<para align='center'>%.02f %%</para>" % tva, paraStyle))
                                else :
                                    listeMontantsHT.append("")
                                    listeTVA.append("")

                                # Affiche total
                                if montant == 0.00:
                                    listeMontantsTTC.append(Spacer(10,dictOptions["taille_texte_prestation"]))
                                else:
                                    param = "<para align='right'>%.02f %s</para>" % (montant, SYMBOLE)
                                    listeMontantsTTC.append(Paragraph(param, paraStyle))

                                # Déductions
                                if len(deductions) > 0 :
                                    for dictDeduction in deductions :
                                        listeIntitules.append(Paragraph("<para align='left'><font size=5 color='#939393'>- %.02f %s : %s</font></para>" % (dictDeduction["montant"], SYMBOLE, dictDeduction["label"]), paraStyle))
                                        #listeIntitules.append(Paragraph(u"<para align='left'><font size=5 color='#939393'>%s</font></para>" % dictDeduction["label"], paraStyle))
                                        listeMontantsHT.append(Paragraph("&nbsp;", paraStyle))
                                        listeTVA.append(Paragraph("&nbsp;", paraStyle))
                                        listeMontantsTTC.append(Paragraph("&nbsp;", paraStyle))
                                        #listeMontantsTTC.append(Paragraph(u"<para align='center'><font size=5 color='#939393'>- %.02f %s</font></para>" % (dictDeduction["montant"], SYMBOLE), paraStyle))

                            if len(listeIntitules) == 1 :
                                texteIntitules = listeIntitules[0]
                                texteMontantsHT = listeMontantsHT[0]
                                texteTVA = listeTVA[0]
                                texteMontantsTTC = listeMontantsTTC[0]
                            if len(listeIntitules) > 1 :
                                texteIntitules = listeIntitules
                                texteMontantsHT = listeMontantsHT
                                texteTVA = listeTVA
                                texteMontantsTTC = listeMontantsTTC

                            if activeTVA == True :
                                dataTableau.append([texteDate, texteIntitules, texteMontantsHT, texteTVA, texteMontantsTTC])
                            else :
                                dataTableau.append([texteDate, texteIntitules, texteMontantsTTC])

                        # Style du tableau des lignes
                        tableau = Table(dataTableau, largeursColonnes)
                        listeStyles = [
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('FONT', (0, 0), (-1, -1), "Helvetica", dictOptions["taille_texte_prestation"]),
                            ('GRID', (0, 0), (-1,-1), 0.25, colors.black),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTRE'),
                            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                            ('TOPPADDING', (0, 0), (-1, -1), 1),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                            ]
                        tableau.setStyle(TableStyle(listeStyles))
                        story.append(tableau)

                    # Insertion des totaux
                    dataTableau = []
                    if activeTVA == True and detail == 0 :
                        dataTableau.append(["", "", "", "", Paragraph("<para align='center'>%.02f %s</para>" % (dictIndividus["montant"], SYMBOLE) , paraStyle)])
                    else :
                        if detail != 0 :
                            dataTableau.append(["", "", "", Paragraph("<para align='center'>%.02f %s</para>" % (dictIndividus["montant"], SYMBOLE) , paraStyle)])
                        else :
                            dataTableau.append(["", "", Paragraph("<para align='center'>%.02f %s</para>" % (dictIndividus["montant"], SYMBOLE) , paraStyle)])

                    listeStyles = [
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('FONT', (0, 0), (-1, -1), "Helvetica", dictOptions["taille_texte_prestation"]),
                            ('GRID', (-1, -1), (-1,-1), 0.25, colors.black),
                            ('ALIGN', (-1, -1), (-1, -1), 'CENTRE'),
                            ('BACKGROUND', (-1, -1), (-1, -1), couleurFond),
                            ('TOPPADDING', (0, 0), (-1, -1), 1),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                            ]

                    # Création du tableau
                    tableau = Table(dataTableau, largeursColonnes)
                    tableau.setStyle(TableStyle(listeStyles))
                    story.append(tableau)
                    story.append(Spacer(0, 10))
                
                # Intégration des messages, des reports et des qf
                listeMessages = []
                paraStyle = ParagraphStyle(name="message",
                                          fontName="Helvetica",
                                          fontSize=dictOptions["taille_texte_messages"],
                                          leading=dictOptions["taille_texte_messages"],
                                          #spaceBefore=0,
                                          spaceAfter=1,
                                        )
                
                # Date d'échéance
##                if dictOptions["echeance"] != None :
##                    listeMessages.append(Paragraph(dictOptions["echeance"], paraStyle))

               # QF aux dates de facture
                if dictOptions["afficher_qf_dates"] == True :
                    dictQfdates = dictValeur["qfdates"]
                    listeDates = list(dictQfdates.keys()) 
                    listeDates.sort() 
                    if len(listeDates) > 0 :
                        for dates in listeDates :
                            qf = dictQfdates[dates]
##                            texteQf = _("--- Votre QF %s : <b>%s</b> ---") % (dates, qf)
                            texteQf = _("<b>Votre quotient familial : </b>Votre QF est de %s sur la période %s.") % (qf, dates)
                            listeMessages.append(Paragraph(texteQf, paraStyle))

                # Reports
                if dictOptions["afficher_impayes"] == True :
                    dictReports = dictValeur["reports"]
                    listePeriodes = list(dictReports.keys()) 
                    listePeriodes.sort()
                    if len(listePeriodes) > 0 :
                        texteTitre = ""
                        texteReport = ""
                        texteAffecter = ""
                        if dictOptions["integrer_impayes"] == True :
                            texteTitre = _("<b>Détail %s : </b>") %dictValeur["{LIB_REPORTS}"]
                        else :
                            if dictValeur["solde_du"] > 0:
                                texteTitre = _("<b>Impayés : </b>Merci de régler également le solde des autres prestations : ")
                            else :
                                texteTitre = _("<b>Crédits : </b>Valant règlement pour autres prestations : ")
                        for periode in listePeriodes :
                            txt = ""
                            if isinstance(periode,tuple):
                                annee, mois = periode
                                if annee and mois:
                                    nomPeriode = PeriodeComplete(mois, annee)
                            else: nomPeriode = str(periode)
                            txt += "%s:(" % (nomPeriode)
                            for type in dictReports[periode]:
                                montant_impaye = dictReports[periode][type]
                                txt += "%s %.02f %s," % (type, montant_impaye, SYMBOLE)
                            txt = txt[:-2]+ "); "
                            if isinstance(periode,tuple):
                                texteReport += txt
                            else:
                                texteAffecter += txt
                        listeMessages.append(Paragraph(texteTitre, paraStyle))
                        for txt in (texteReport, texteAffecter):
                            if txt != "":
                                txt = txt[:-2]+ "."
                                listeMessages.append(Paragraph(txt, paraStyle))
                # Règlements
                if dictOptions["afficher_reglements"] == True :
                    dictReglements = dictValeur["reglements"]
                    if len(dictReglements) > 0 :
                        listeTextesReglements = []
                        for IDreglement, dictTemp in dictReglements.items() :
                            if dictTemp["emetteur"] not in ("", None) :
                                emetteur = " (%s) " % dictTemp["emetteur"]
                            else :
                                emetteur = ""
                            if dictTemp["numero"] not in ("", None) :
                                numero = " n°%s " % dictTemp["numero"]
                            else :
                                numero = ""
                                
                            montantReglement = "%.02f%s" % (dictTemp["montant"], SYMBOLE)
                            montantVentilation = "%.02f%s" % (dictTemp["ventilation"], SYMBOLE)
                            if dictTemp["ventilation"] != dictTemp["montant"] :
                                texteMontant = "%s sur %s" % (montantVentilation, montantReglement)
                            else :
                                texteMontant = montantReglement
                            if "dateReglement" in list(dictTemp.keys()):
                                dat = str(dictTemp["dateReglement"])
                            else: dat = "          "
                            an = dat[:4]
                            mois = dat[5:7]
                            texte = "%s/%s %s%s de %s (%s)" % (mois,an,dictTemp["mode"][:3],  emetteur,
                                                                  dictTemp["payeur"], texteMontant)
                            listeTextesReglements.append(texte)
                        listeTextesReglements.sort()

                        if dictValeur["solde"] > FloatToDecimal(0.0) :
                            intro = "Partiellement réglé"
                        else :
                            intro = "Réglé en intégralité"
                            
                        texteReglements = _("<b>Règlements : </b> %s") % (intro)
                        listeMessages.append(Paragraph(texteReglements, paraStyle))
                        for ligne in listeTextesReglements:
                            listeMessages.append(Paragraph(ligne, paraStyle))

                # Messages
                if dictOptions["afficher_messages"] == True :
                    for message in dictOptions["messages"] :
                        listeMessages.append(Paragraph(message, paraStyle))

                    for message_familial in dictValeur["messages_familiaux"] :
                        texte = message_familial["texte"]
                        if len(texte) > 0 and texte[-1] not in ".!?" :
                            texte = texte + "."
                        texte = _("<b>Message : </b>%s") % texte
                        listeMessages.append(Paragraph(texte, paraStyle))

                if len(listeMessages) > 0 :
                    listeMessages.insert(0, Paragraph(_("<u>Informations :</u>"), paraStyle))
                
                # ------------------ CADRE TOTAUX ------------------------
                dataTableau = []
                largeurColonneLabel = 90
                largeursColonnes = [ CADRE_CONTENU[2] - largeurColonneMontantTTC - largeurColonneLabel, largeurColonneLabel, largeurColonneMontantTTC]

                if not "{LIB_MONTANT}" in dictValeur:
                    dictValeur["{LIB_MONTANT}"] = "Total activité :"
                libTotal = dictValeur["{LIB_MONTANT}"]
                if not "{LIB_SOLDE}" in dictValeur:
                    dictValeur["{LIB_SOLDE}"] = "Reste à régler :"
                dataTableau.append((listeMessages, libTotal, "%.02f %s" % (dictValeur["montant"], SYMBOLE)))
                if dictValeur["ventilation"] != 0 :
                    dataTableau.append(("", _("Règlements affectés :"), "%.02f %s" % (dictValeur["ventilation"], SYMBOLE)))
                    dataTableau.append(("", dictValeur["{LIB_SOLDE}"], "%.02f %s" % (dictValeur["solde"], SYMBOLE)))
                #gestion reports
                if ("total_reports" in dictValeur) and  dictValeur["total_reports"] != 0 \
                        and dictValeur["nature"] in ["COM","FAC","AVO"] \
                        and DICT_OPTIONS["integrer_impayes"] == True :
                    dataTableau.append(("", dictValeur["{LIB_REPORTS}"],
                                        "%.02f %s" % (abs(dictValeur["total_reports"]), SYMBOLE) ))
                    #gestion du reste en cas de report
                    dataTableau.append(("", _("%s :")%(dictValeur["{LIB_SOLDE_DU}"]),
                                        "%.02f %s" % (dictValeur["solde_du"], SYMBOLE) ))
                style = [
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), 
##                        ('FONT', (1, 0), (1, -1), "Helvetica", 7),#dictOptions["taille_texte_labels_totaux"]), 
##                        ('FONT', (2, 0), (2, -1), "Helvetica-Bold", 7),#dictOptions["taille_texte_montants_totaux"]), 
                        
                        # Lignes Période, avoir, impayés
                        ('FONT', (1, 0), (1, -2), "Helvetica", 8),#dictOptions["taille_texte_labels_totaux"]), 
                        ('FONT', (2, 0), (2, -2), "Helvetica-Bold", 8),#dictOptions["taille_texte_montants_totaux"]), 
                        
                        # Ligne Reste à régler
                        ('FONT', (1, -1), (1, -1), "Helvetica-Bold", dictOptions["taille_texte_labels_totaux"]), 
                        ('FONT', (2, -1), (2, -1), "Helvetica-Bold", dictOptions["taille_texte_montants_totaux"]), 
                        
                        ('GRID', (2, 0), (2, -1), 0.25, colors.black),
                        
                        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                        ('ALIGN', (2, 0), (2, -1), 'CENTRE'), 
                        ('BACKGROUND', (2, -1), (2, -1), couleurFond),
                        
                        ('SPAN', (0, 0), (0, -1)), 
                        ]
                
                if len(listeMessages) > 0 :
                    #style.append( ('BACKGROUND', (0, 0), (0, 0), couleurFondActivite) )
                    style.append( ('FONT', (0, 0), (0, -1), "Helvetica", 8)  )
                    style.append( ('VALIGN', (0, 0), (0, -1), 'TOP') )
                    
                tableau = Table(dataTableau, largeursColonnes)#, rowHeights=rowHeights)
                tableau.setStyle(TableStyle(style))
                story.append(tableau)
                
                # ------------------------- PRELEVEMENTS --------------------
                if "afficher_avis_prelevements" in dictOptions and "prelevement" in dictValeur :
                    if dictValeur["prelevement"] != None and dictOptions["afficher_avis_prelevements"] == True :
                        paraStyle = ParagraphStyle(name="intro",
                              fontName="Helvetica",
                              fontSize=8,
                              leading=11,
                              spaceBefore=2,
                              spaceafter=2,
                              alignment=1,
                              backColor=couleurFondActivite,
                            )
                        story.append(Spacer(0,20))
                        story.append(Paragraph("<para align='center'><i>%s</i></para>" % dictValeur["prelevement"], paraStyle))
                
                # Texte conclusion
                if dictOptions["texte_conclusion"] != "" :
                    story.append(Spacer(0,20))
                    paraStyle = ParagraphStyle(name="conclusion",
                                          fontName="Helvetica",
                                          fontSize=dictOptions["taille_texte_conclusion"],
                                          leading=14,
                                          spaceBefore=0,
                                          spaceafter=0,
                                          leftIndent=5,
                                          rightIndent=5,
                                          alignment=dictOptions["alignement_texte_conclusion"],
                                          backColor=ConvertCouleurWXpourPDF(dictOptions["couleur_fond_conclusion"]),
                                          borderColor=ConvertCouleurWXpourPDF(dictOptions["couleur_bord_conclusion"]),
                                          borderWidth=0.5,
                                          borderPadding=5,
                                        )
            
                    texte = dictValeur["texte_conclusion"].replace("\\n", "<br/>")
                    if dictOptions["style_texte_conclusion"] == 0 : texte = "<para>%s</para>" % texte
                    if dictOptions["style_texte_conclusion"] == 1 : texte = "<para><i>%s</i></para>" % texte
                    if dictOptions["style_texte_conclusion"] == 2 : texte = "<para><b>%s</b></para>" % texte
                    if dictOptions["style_texte_conclusion"] == 3 : texte = "<para><i><b>%s</b></i></para>" % texte
                    story.append(Paragraph(texte, paraStyle))
                    
                # Image signature
                if dictOptions["image_signature"] != "" :
                    cheminImage = dictOptions["image_signature"]
                    if os.path.isfile(cheminImage) :
                        img = Image(cheminImage)
                        largeur, hauteur = int(img.drawWidth * 1.0 * dictOptions["taille_image_signature"] / 100.0), int(img.drawHeight * 1.0 * dictOptions["taille_image_signature"] / 100.0)
                        if largeur > CADRE_CONTENU[2] or hauteur > CADRE_CONTENU[3] :
                            raise Exception(_("L'image de signature est trop grande. Veuillez diminuer sa taille avec le parametre Taille."))
                        img.drawWidth, img.drawHeight = largeur, hauteur
                        if dictOptions["alignement_image_signature"] == 0 : img.hAlign = "LEFT"
                        if dictOptions["alignement_image_signature"] == 1 : img.hAlign = "CENTER"
                        if dictOptions["alignement_image_signature"] == 2 : img.hAlign = "RIGHT"
                        story.append(Spacer(0,20))
                        story.append(img)
                        


                # Saut de page
                story.append(PageBreak())

        # Finalisation du PDF
        doc.build(story)
        # Ouverture du PDF
        if ouverture == True :
            FonctionsPerso.LanceFichierExterne(nomDoc)

def Decimal(texte):
    montant= decimal.Decimal(texte)
    return montant

if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()

    dictDonnees = {}

    dictOptions = {'texte_conclusion': '', 'image_signature': '', 'taille_texte_messages': 7, 'afficher_qf_dates': True,
                   'affichage_prestations': 0, 'taille_image_signature': 100, 'alignement_image_signature': 0,
                   'couleur_fond_conclusion': wx.Colour(255, 255, 255, 255), 'alignement_texte_introduction': 0,
                   'afficher_reglements': True, 'integrer_impayes': False, 'taille_texte_activite': 6,
                   'afficher_periode': True, 'couleur_fond_introduction': wx.Colour(255, 255, 255, 255),
                   'taille_texte_titre': 19, 'taille_texte_periode': 8, 'IDmodele': 5, 'couleur_fond_2': wx.Colour(234, 234, 255, 255),
                   'couleur_fond_1': wx.Colour(204, 204, 255, 255), 'afficher_impayes': True, 'afficher_messages': True,
                   'couleur_bord_conclusion': wx.Colour(255, 255, 255, 255), 'taille_texte_montants_totaux': 10,
                   'alignement_texte_conclusion': 0, 'largeur_colonne_montant_tva': 50, 'largeur_colonne_date': 50,
                   'taille_texte_prestation': 7, 'afficher_avis_prelevements': True,
                   'taille_texte_conclusion': 9, 'affichage_solde': 0, 'afficher_coupon_reponse': True,
                   'taille_texte_introduction': 9, 'intitules': 0, 'taille_texte_noms_colonnes': 5,
                   'texte_introduction': '', 'taille_texte_individu': 9, 'taille_texte_labels_totaux': 9,
                   'couleur_bord_introduction': wx.Colour(255, 255, 255, 255), 'afficher_codes_barres': True,
                   'afficher_titre': True, 'largeur_colonne_montant_ht': 50, 'messages': [], 'memoriser_parametres': True,
                   'largeur_colonne_montant_ttc': 70, 'style_texte_introduction': 0, 'style_texte_conclusion': 0,
                   'repertoire_copie': ''}
    Impression(dictDonnees, dictOptions,IDmodele=dictOptions["IDmodele"])
    # mettre un point d'arrêt pour voir le pdf
    print("Fin")
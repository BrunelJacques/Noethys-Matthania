#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------


DICT_TYPES_LIENS = {
    1 : { "M" : "p�re", "F" : "m�re", "public" : "A", "lien" : 2, "type" : "parent", "texte" : { "M" : "est son p�re", "F" : "est sa m�re"} },
    2 : { "M" : "fils", "F" : "fille", "public" : "AE", "lien" : 1, "type" : "enfant", "texte" : { "M" : "est son fils", "F" : "est sa fille"} },
    
    3 : { "M" : "fr�re", "F" : "soeur", "public" : "AE", "lien" : 3, "type" : None, "texte" : { "M" : "est son fr�re", "F" : "est sa soeur"} },
    
    4 : { "M" : "grand-p�re", "F" : "grand-m�re", "public" : "A", "lien" : 5, "type" : None, "texte" : { "M" : "est son grand-p�re", "F" : "est sa grand-m�re"} },
    5 : { "M" : "petit-fils", "F" : "petite-fille", "public" : "AE", "lien" : 4, "type" : None, "texte" : { "M" : "est son petit-fils", "F" : "est sa petite-fille"} },
    
    6 : { "M" : "oncle", "F" : "tante", "public" : "A", "lien" : 7, "type" : None, "texte" : { "M" : "est son oncle", "F" : "est sa tante"} },
    7 : { "M" : "neveu", "F" : "ni�ce", "public" : "AE", "lien" : 6, "type" : None, "texte" : { "M" : "est son neveu", "F" : "est sa ni�ce"} },
    
##    8 : { "M" : "parrain", "F" : "marraine", "public" : "AE", "lien" : 9 },
##    9 : { "M" : "filleul", "F" : "filleule", "public" : "AE", "lien" : 8 },
    
    10 : { "M" : "mari", "F" : "femme", "public" : "A", "lien" : 10, "type" : "couple", "texte" : { "M" : "est son mari", "F" : "est sa femme"} },
    
    11 : { "M" : "concubin", "F" : "concubine", "public" : "A", "lien" : 11, "type" : "couple", "texte" : { "M" : "est son concubin", "F" : "est sa concubine"} },
    
    12 : { "M" : "veuf", "F" : "veuve", "public" : "A", "lien" : 12, "type" : "couple", "texte" : { "M" : "est son veuf", "F" : "est sa veuve"}},

    13 : { "M" : "beau-p�re", "F" : "belle-m�re", "public" : "A", "lien" : 14, "type" : None, "texte" : { "M" : "est son beau-p�re", "F" : "est sa belle-m�re"} },
    14 : { "M" : "beau-fils", "F" : "belle-fille", "public" : "AE", "lien" : 13, "type" : None, "texte" : { "M" : "est son beau-fils", "F" : "est sa belle-fille"} },
    
    15 : { "M" : "pacs�", "F" : "pacs�e", "public" : "A", "lien" : 15, "type" : "couple", "texte" : { "M" : "est son pacs�", "F" : "est sa pacs�e"} },
    
    16 : { "M" : "ex-mari", "F" : "ex-femme", "public" : "A", "lien" : 16, "type" : "ex-couple", "texte" : { "M" : "est son ex-mari", "F" : "est son ex-femme"} },
    
    17 : { "M" : "ex-concubin", "F" : "ex-concubine", "public" : "A", "lien" : 17, "type" : "ex-couple", "texte" : { "M" : "est son ex-concubin", "F" : "est son ex-concubine"} },
    
    18 : { "M" : "tuteur", "F" : "tutrice", "public" : "AE", "lien" : 19, "type" : None, "texte" : { "M" : "est son tuteur", "F" : "est sa tutrice"} },
    19 : { "M" : "sous sa tutelle", "F" : "sous sa tutelle", "public" : "AE", "lien" : 18, "type" : None, "texte" : { "M" : "est sous sa tutelle", "F" : "est sous sa tutelle"} },

    20: {"M": "assistant maternel", "F": "assistante maternelle", "public": "A", "lien": 21, "type": None, "texte": {"M": "est son assistant maternel", "F": "est son assistante maternelle"}},
    21: {"M": "sous sa garde", "F": "sous sa garde", "public": "E", "lien": 20, "type": None, "texte": {"M": "est sous sa garde", "F": "est sous sa garde"}},

    22: {"M": "ami", "F": "amie", "public": "AE", "lien": 22, "type": None, "texte": {"M": "est son ami", "F": "est son amie"}},

    23: {"M": "voisin", "F": "voisine", "public": "AE", "lien": 23, "type": None, "texte": {"M": "est son voisin", "F": "est sa voisine"}},

}


DICT_AUTORISATIONS = {
    1 : { "M" : "Responsable l�gal", "F" : "Responsable l�gale", "img" : "Responsable_legal.png"},
    2 : { "M" : "Contacter en cas d'urgence", "F" : "Contacter en cas d'urgence", "img" : "Telephone.png"},
    3 : { "M" : "Raccompagnement autoris�", "F" : "Raccompagnement autoris�", "img" : "Sortir.png"},
    4 : { "M" : "Raccompagnement interdit", "F" : "Raccompagnement interdit", "img" : "Interdit2.png"},
    }


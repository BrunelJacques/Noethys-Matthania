# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         Filter.py
# Author:       Phillip Piper
# Created:      26 August 2008
# Copyright:    (c) 2008 Phillip Piper
# License:      wxWindows license
#----------------------------------------------------------------------------
# Change log:
# 2008/08/26  JPP   First version
#----------------------------------------------------------------------------
# To do:
#

"""
Filters provide a structured mechanism to display only some of the model objects
given to an Olv. Only those model objects which are 'chosen' by
an installed filter will be presented to the user.

Filters are simple callable objects which accept a single parameter, which
is the list of model objects to be filtered, and returns a collection of
those objects which will be presented to the user.

This module provides some standard filters.

Filters almost always impose a performance penalty on the Olv.
The penalty is normally O(n) since the filter normally examines each model
object to see if it should be included. Head() and Tail() are exceptions
to this observation.
"""


def Predicate(predicate):
    """
    Display only those objects that match the given predicate

    Example::
        self.olv.SetFilter(Filter.Predicate(lambda x: x.IsOverdue()))
    """
    return lambda modelObjects: [x for x in modelObjects if predicate(x)]


def Head(num):
    """
    Display at most the first N of the model objects

    Example::
        self.olv.SetFilter(Filter.Head(1000))
    """
    return lambda modelObjects: modelObjects[:num]


def Tail(num):
    """
    Display at most the last N of the model objects

    Example::
        self.olv.SetFilter(Filter.Tail(1000))
    """
    return lambda modelObjects: modelObjects[-num:]


class TextSearch(object):

    """
    Return only model objects that match a given string. If columns is not empty,
    only those columns will be considered when searching for the string. Otherwise,
    all columns will be searched.

    Example::
        self.olv.SetFilter(Filter.TextSearch(self.olv, text="findthis"))
        self.olv.RepopulateList()
    """

    def __init__(self, objectListView, columns=(), text=""):
        """
        Create a filter that includes on modelObject that have 'self.text' somewhere in the given columns.
        """
        self.objectListView = objectListView
        self.columns = columns
        self.text = text

    def __call__(self, modelObjects):
        """
        Return the model objects that contain our text in one of the columns to consider
        """
        if not self.text:
            return modelObjects

        # In non-report views, we can only search the primary column
        if self.objectListView.InReportView():
            cols = self.columns or self.objectListView.columns
        else:
            cols = [self.objectListView.columns[0]]

        textToFind = self.EnleveAccents(self.text).lower()

        def _containsText(modelObject):
            for col in cols:
                valeur = col.GetStringValue(modelObject)
                if valeur == None : valeur = ""
                textInListe = self.EnleveAccents(valeur).lower()
                # Recherche de la chaine
                if textToFind in textInListe :
                    return True
            return False

        return [x for x in modelObjects if _containsText(x)]

    def EnleveAccents(self, texte):
        try :
            return texte.decode("iso-8859-15")
        except : return texte


    def SetText(self, text):
        """
        Set the text that this filter will match. Set this to None or "" to disable the filter.
        """
        self.text = text


class Chain(object):

    def __init__(self,filterAndNotOr, *filters):
        """
        Create a filter that performs all the given filters.

        The order of the filters is important.
        """
        self.filters = filters
        self.filterAndNotOr = filterAndNotOr

    def __call__(self, modelObjects):
        if self.filterAndNotOr:
            #Return the model objects that match all of our filters
            for filter in self.filters:
                modelObjects = filter(modelObjects)
            return modelObjects
        else:
            #Return la fusion des sous ensembles filtrés
            modelcumul = []
            for filter in self.filters:
                model = filter(modelObjects)
                for ligne in model:
                    if not ligne in modelcumul:
                        modelcumul.append(ligne)
            return modelcumul

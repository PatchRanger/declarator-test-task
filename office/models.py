#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.db import models
from django.utils.encoding import smart_unicode
from mptt.models import MPTTModel, TreeForeignKey

# @link https://github.com/tyarkoni/transitions
from transitions import Machine

__author__ = "Dmitry Danilson"
__copyright__ = "Copyright 2016"
__credits__ = ["Dmitry Danilson"]
__license__ = "GPL"
__version__ = "1.0.1"
__maintainer__ = "Dmitry Danilson"
__status__ = "Test task"

class Office(MPTTModel):
    DECLARATION_STATE_UNKNOWN='unknown'
    DECLARATION_STATE_NO_DOCUMENT='no_document'
    DECLARATION_STATE_NONE='none'
    DECLARATION_STATE_SOME='some'
    DECLARATION_STATE_FULL='full'

    # For compatibility with DeclarationRecursiveSM
    DECLARATION_STATE_CHILDREN_MISSING = 'no_document'

    @property
    def DECLARATION_STATES(self):
        return [
            self.DECLARATION_STATE_UNKNOWN,
            self.DECLARATION_STATE_NO_DOCUMENT,
            self.DECLARATION_STATE_NONE,
            self.DECLARATION_STATE_SOME,
            self.DECLARATION_STATE_FULL,
        ]

    # @todo Replace with dynamic expression
    YEARS = range(2015, 2008, -1)

    parent = TreeForeignKey('self', blank=True, null=True)
    name = models.TextField(verbose_name=u'полное название')
    sort_order = models.IntegerField(default=0, verbose_name=u'Порядок сортировки')

    @property
    def stats_by_year(self):
        result = {}
        years = self.YEARS
        for year in self.YEARS:
            result[year] = self.get_declaration_state_by_year(year=year)
        return result

    def __unicode__(self):
        return str(self.id) + "<" + smart_unicode(self.name) + ">"

    def __str__(self):
        return str(self.id) + "<" + smart_unicode(self.name) + ">"

    # @todo Refactor for chaining query
    def get_documents(self):
        return Document.objects.filter(office=self).all()

    def get_documents_by_year(self, year):
        return Document.objects.filter(office=self, income_year=year).all()

    # For compatibility with DeclarationRecursiveSM
    def get_declaration_state_children(self):
        return self.declaration_state_children

    def get_declaration_state_by_year(self, year):
        self.declaration_state_children = self.get_documents_by_year(year=year)
        dsrsm = DeclarationStateRecursiveSM(instance=self)
        return dsrsm.get_declaration_state()

class Document(models.Model):
    DECLARATION_STATE_UNKNOWN='unknown'
    DECLARATION_STATE_NO_FILE='no_file'
    DECLARATION_STATE_NONE='none'
    DECLARATION_STATE_SOME='some'
    DECLARATION_STATE_FULL='full'

    # For compatibility with DeclarationRecursiveSM
    DECLARATION_STATE_CHILDREN_MISSING = 'no_file'

    @property
    def DECLARATION_STATES(self):
        return [
            self.DECLARATION_STATE_UNKNOWN,
            self.DECLARATION_STATE_NO_FILE,
            self.DECLARATION_STATE_NONE,
            self.DECLARATION_STATE_SOME,
            self.DECLARATION_STATE_FULL,
        ]

    office = TreeForeignKey('Office', verbose_name=u"орган власти")
    income_year = models.IntegerField(verbose_name=u"год за который указан доход")

    def get_document_files(self):
        return DocumentFile.objects.filter(document=self).all()

    # For compatibility with DeclarationRecursiveSM
    def get_declaration_state_children(self):
        return self.get_document_files()

    def get_declaration_state(self):
        dsrsm = DeclarationStateRecursiveSM(instance=self)
        return dsrsm.get_declaration_state()

    def __unicode__(self):
        return str(self.id) + "<" + smart_unicode(self.office) + ";" + str(self.income_year) + ">"

    def __str__(self):
        return str(self.id) + "<" + smart_unicode(self.office) + ";" + str(self.income_year) + ">"

class DocumentFile(models.Model):
    DECLARATION_STATE_NONE='none'
    DECLARATION_STATE_FULL='full'

    @property
    def DECLARATION_STATES(self):
        return [
            self.DECLARATION_STATE_NONE,
            self.DECLARATION_STATE_FULL,
        ]

    document = models.ForeignKey('Document', verbose_name=u"декларация")
    file = models.FileField(blank=True, max_length=255, null=True,
                                                    upload_to='uploads/%Y/%m/%d/', verbose_name=u"файл")

    def get_declaration_state(self):
        return self.DECLARATION_STATE_FULL if (hasattr(self, 'file') and bool(self.file)) else self.DECLARATION_STATE_NONE

    def __unicode__(self):
        return str(self.id) + "<" + smart_unicode(self.document) + ";" + smart_unicode(self.file) + ">"

    def __str__(self):
        return str(self.id) + "<" + smart_unicode(self.document) + ";" + smart_unicode(self.file) + ">"

# SM is for "State Machine"
class PrematureSMExitException(Exception):
    pass

class DeclarationStateRecursiveSM(object):
    def __init__(self, instance):
        self.instance = instance
        self.states = self.instance.DECLARATION_STATES

        # Initialize the state machine
        self.machine = Machine(model=self, states=self.states, initial=self.instance.DECLARATION_STATE_UNKNOWN)

        # Add some transitions. We could also define these using a static list of
        # dictionaries, as we did with states above, and then pass the list to
        # the Machine initializer as the transitions= argument.

        # Haven't found any children instances.
        self.machine.add_transition('children_missing', self.instance.DECLARATION_STATE_UNKNOWN, self.instance.DECLARATION_STATE_CHILDREN_MISSING, after='premature_finish')

        # The first one is promising: found.
        self.machine.add_transition('first_found', self.instance.DECLARATION_STATE_UNKNOWN, self.instance.DECLARATION_STATE_FULL)

        # The first one is disappointing: missing.
        self.machine.add_transition('first_missing', self.instance.DECLARATION_STATE_UNKNOWN, self.instance.DECLARATION_STATE_NONE)

        # Mixed results: after finds missing one or after finds missing one.
        # Exiting as we are already sure that there are some.
        self.machine.add_transition('some', '*', self.instance.DECLARATION_STATE_SOME, after='premature_finish')

    def premature_finish(self):
        raise PrematureSMExitException()

    def get_declaration_state(self):
        try:
            children = self.instance.get_declaration_state_children()
            if not children:
                self.children_missing()
            for child in children:
                # @todo Refactor even more in "state-machine-style" using "conditions"
                child_state = child.get_declaration_state()
                if (hasattr(child, 'DECLARATION_STATE_SOME') and (child_state == child.DECLARATION_STATE_SOME)):
                    self.some()
                elif (child_state == child.DECLARATION_STATE_FULL):
                    if (self.state == self.instance.DECLARATION_STATE_UNKNOWN):
                        self.first_found()
                    elif (self.state == self.instance.DECLARATION_STATE_NONE):
                        self.some()
                elif (
                    (child_state == child.DECLARATION_STATE_NONE)
                    or
                    (hasattr(child, 'DECLARATION_STATE_CHILDREN_MISSING') and (child_state == child.DECLARATION_STATE_CHILDREN_MISSING))
                ):
                    if (self.state == self.instance.DECLARATION_STATE_UNKNOWN):
                        self.first_missing()
                    elif (self.state == self.instance.DECLARATION_STATE_FULL):
                        self.some()
        except PrematureSMExitException:
            pass
        finally:
            return self.state
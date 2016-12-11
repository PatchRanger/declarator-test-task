#!/usr/bin/env python
from django.shortcuts import get_object_or_404,render
from django.template.response import TemplateResponse
from django.views.generic import DetailView
from django.views.generic import ListView

from office.models import Office

__author__ = "Dmitry Danilson"
__copyright__ = "Copyright 2016"
__credits__ = ["Dmitry Danilson"]
__license__ = "GPL"
__version__ = "1.0.1"
__maintainer__ = "Dmitry Danilson"
__status__ = "Test task"

def detail(request, id):
    # @todo Protect from injections.
    office = get_object_or_404(Office, pk=id)
    suboffices = Office.objects.filter(parent=office)
    context = {
        'office': office,
        'suboffices': suboffices,
    }
    return render(request, 'office/detail/index.html', context)

# @todo Find a way to re-use generic views
#class OfficeList(ListView):
#    model = Office
#
#class OfficeDetail(DetailView):
#    model = Office
#    pk_url_kwarg = 'id'
#    template_name = 'office/detail/index.html'
#
#    def get_context_data(self, **kwargs):
#        context = super(OfficeDetail, self).get_context_data(**kwargs)
#        # Suboffices
#        suboffices = Office.objects.filter(parent=object)
#        context['suboffices'] = suboffices
#        return context
#
#class SubofficeList(ListView):
#    model = Office
#    template_name = 'office/detail/structure/index.html'
#
#    def get_queryset(self):
#        self.office = get_object_or_404(Office, id=self.kwargs['id'])
#        return Office.objects.filter(parent=self.office)
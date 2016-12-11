#!/usr/bin/env python
from django.conf.urls import url

#from office.views import OfficeDetail, OfficeList
from . import views

__author__ = "Dmitry Danilson"
__copyright__ = "Copyright 2016"
__credits__ = ["Dmitry Danilson"]
__license__ = "GPL"
__version__ = "1.0.1"
__maintainer__ = "Dmitry Danilson"
__status__ = "Test task"

urlpatterns = [
    #url(r'^offices$', OfficeList.as_view(), name='list'),
    # ex: /office/5
    #url(r'^(?P<id>[0-9]+)$', OfficeDetail.as_view(), name='detail'),
    url(r'^(?P<id>[0-9]+)$', views.detail, name='detail'),
]
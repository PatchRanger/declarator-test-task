#!/usr/bin/env python
from django.contrib import admin

from .models import Office, Document, DocumentFile

admin.site.register(Office)
admin.site.register(Document)
admin.site.register(DocumentFile)
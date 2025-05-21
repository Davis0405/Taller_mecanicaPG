# usuarios/admin.py
from django.contrib import admin
from .models import Rol, Perfil

admin.site.register(Rol)
admin.site.register(Perfil)
from django.db.models.signals import post_save
from django.dispatch import receiver
from Iot_platform_app.models import Gauge_table,toggle_switch,Label,electric_switch
from django.db import models
from .models import create_dynamic_model_gauge,create_dynamic_model_toggle,create_dynamic_model_Label,create_dynamic_model_electric
from .models import dynamic_table_names_of_gauge,dynamic_table_names_toggle,dynamic_table_names_label,dynamic_table_names_switch
from django.db import connection
from django.core.management import call_command
from django.apps import apps
from django.contrib import admin

@receiver(post_save, sender=Gauge_table)
def create_new_table(sender, instance, created, **kwargs):
    if created:
        table_name = f"{instance.gauge_id}"
        
        dynamic_model = create_dynamic_model_gauge(table_name)
        
        dynamic_model.objects.create(common_field_2=0)

        dynamic_table_names_of_gauge.objects.create(model_name=table_name)
        admin.site.register(dynamic_model)
        if dynamic_model in admin.site._registry:
            print("successfully registered")
       
        
        call_command('makemigrations', 'Iot_platform_app')
        call_command('migrate', 'Iot_platform_app')
        
        
@receiver(post_save, sender=toggle_switch)
def create_new_table(sender, instance, created, **kwargs):
    if created:
        table_name = f"{instance.toggle_switch_id}"
        
        dynamic_model = create_dynamic_model_toggle(table_name)
        
        dynamic_model.objects.create(common_field_2=0)
        
        dynamic_table_names_toggle.objects.create(model_name=table_name)
        admin.site.register(dynamic_model)
        if dynamic_model in admin.site._registry:
            print("successfully registered")
       
        
        call_command('makemigrations', 'Iot_platform_app')
        call_command('migrate', 'Iot_platform_app')
        
@receiver(post_save, sender=Label)
def create_new_table(sender, instance, created, **kwargs):
    if created:
        table_name = f"{instance.label_id}"
        
        dynamic_model = create_dynamic_model_Label(table_name)
        
        dynamic_model.objects.create(common_field_2='')

        
        
        dynamic_table_names_label.objects.create(model_name=table_name)
        admin.site.register(dynamic_model)
        if dynamic_model in admin.site._registry:
            print("successfully registered")
       
        
        call_command('makemigrations', 'Iot_platform_app')
        call_command('migrate', 'Iot_platform_app')


@receiver(post_save, sender=electric_switch)
def create_new_table(sender, instance, created, **kwargs):
    if created:
        table_name = f"{instance.electric_switch_id}"
        
        dynamic_model = create_dynamic_model_electric(table_name)
        
        dynamic_model.objects.create(common_field_2=0)

        
        
        dynamic_table_names_switch.objects.create(model_name=table_name)
        admin.site.register(dynamic_model)
        if dynamic_model in admin.site._registry:
            print("successfully registered")
       
        
        call_command('makemigrations', 'Iot_platform_app')
        call_command('migrate', 'Iot_platform_app')
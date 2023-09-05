from django.apps import AppConfig,apps


class IotPlatformAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Iot_platform_app'
    
    def ready(self):
        from Iot_platform_app import signals
        
        from .models import create_dynamic_model_gauge, create_dynamic_model_toggle, create_dynamic_model_Label,create_dynamic_model_electric,dynamic_table_names_of_gauge,dynamic_table_names_label,dynamic_table_names_toggle,dynamic_table_names_switch
        from django.contrib import admin
        gauge=list(dynamic_table_names_of_gauge.objects.all().values_list('model_name'))
        toggle=list(dynamic_table_names_toggle.objects.all().values_list('model_name'))
        label=list(dynamic_table_names_label.objects.all().values_list('model_name'))
        electric=list(dynamic_table_names_switch.objects.all().values_list('model_name'))

        print(gauge)
        for gauge_name in gauge:
            print("gauge",''.join(gauge_name))
            dynamic_model_gauge = create_dynamic_model_gauge(''.join(gauge_name))
            admin.site.register(dynamic_model_gauge)

        for toggle_name in toggle:
            dynamic_model_toggle = create_dynamic_model_toggle(''.join(toggle_name))
            admin.site.register(dynamic_model_toggle)

        for label_name in label:
            dynamic_model_label = create_dynamic_model_Label(''.join(label_name))
            admin.site.register(dynamic_model_label)
        for switch_name in electric:
            dynamic_model_switch = create_dynamic_model_electric(''.join(switch_name))
            admin.site.register(dynamic_model_switch)
        

        
            
        
       

        
        
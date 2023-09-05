from django.db import models
import uuid
from datetime import datetime
# Create your models here.
from django.apps.registry import apps

class user_register_details(models.Model):
   

    user_id = models.UUIDField( default = uuid.uuid4,auto_created=True,primary_key=True,serialize=False,verbose_name='ID')
    names = models.CharField(max_length=100)
    last_name=models.CharField(max_length=100,default="")
    dob=models.DateField()
    emailId=models.CharField(max_length=400)
    password = models.CharField(max_length=100)
    contact_number = models.IntegerField()
    country = models.CharField(max_length=100)
    Register_date = models.DateField(auto_now=True)
    street_name=models.CharField(max_length=400,default="")
    city=models.CharField(max_length=100,default="")
    state=models.CharField(max_length=100,default="")
    pincode=models.CharField(max_length=100,default="")
    Institute_name=models.CharField(max_length=100,default="")
    department=models.CharField(max_length=100,default="")
    

class admin_details(models.Model):
    admin_id = models.UUIDField( default = uuid.uuid4,auto_created=True,primary_key=True,serialize=False,verbose_name='ID')
    admin_name = models.CharField(max_length=100)
    admin_emailId=models.CharField(max_length=400,unique=True)
    admin_password = models.CharField(max_length=100)
    admin_contact_number = models.IntegerField(unique=True)
    Register_date = models.DateField(auto_now=True)

class device_table(models.Model):
    device_id = models.UUIDField( default = uuid.uuid4,auto_created=True,primary_key=True,serialize=False,verbose_name='ID')
    device_name = models.TextField(max_length=100)
    user_id = models.ForeignKey(user_register_details,models.DO_NOTHING,db_column='user_id')
    
class Gauge_table(models.Model):
    device_id = models.ForeignKey(device_table,models.DO_NOTHING,db_column='device_id')
    gauge_id = models.UUIDField(default = uuid.uuid4,auto_created=True,primary_key=True,serialize=False,verbose_name='ID')
    Title = models.CharField(max_length=50)
    
    min_val = models.IntegerField()
    max_val = models.IntegerField()
    mqtt_topic = models.TextField()

class toggle_switch(models.Model):
    device_id = models.ForeignKey(device_table,models.DO_NOTHING,db_column='device_id')
    toggle_switch_id = models.UUIDField(default = uuid.uuid4,auto_created=True,primary_key=True,serialize=False,verbose_name='ID')
    Title = models.CharField(max_length=50)
    
    on_val = models.IntegerField()
    off_val = models.IntegerField()
    mqtt_topic = models.TextField()

class electric_switch(models.Model):
    device_id = models.ForeignKey(device_table,models.DO_NOTHING,db_column='device_id')
    electric_switch_id = models.UUIDField(default = uuid.uuid4,auto_created=True,primary_key=True,serialize=False,verbose_name='ID')
    Title = models.CharField(max_length=50)
   
    on_val = models.IntegerField()
    off_val = models.IntegerField()
    mqtt_topic = models.TextField()



class Label(models.Model):
    device_id = models.ForeignKey(device_table,models.DO_NOTHING,db_column='device_id')
    label_id = models.UUIDField(default = uuid.uuid4,auto_created=True,primary_key=True,serialize=False,verbose_name='ID')
    Title = models.CharField(max_length=50)
    mqtt_topic = models.TextField()

class dynamic_table_names_gauge(models.Model):
    model_name = models.CharField(max_length=100, unique=True)
class dynamic_table_names_of_gauge(models.Model):
    model_name = models.CharField(max_length=100, unique=True)
class dynamic_table_names_toggle(models.Model):
    model_name = models.CharField(max_length=100, unique=True)
class dynamic_table_names_label(models.Model):
    model_name = models.CharField(max_length=100, unique=True)
class dynamic_table_names_switch(models.Model):
    model_name = models.CharField(max_length=100, unique=True)
    
class BaseTable_gauge(models.Model):
    
    common_field_1 = models.DateTimeField(default=datetime.now)
    common_field_2 = models.IntegerField()
    
    class Meta:
        abstract = True
        
    
        
    
def create_dynamic_model_gauge(table_name):
    fields = {
        'common_field_1': models.DateTimeField(default=datetime.now),
        'common_field_2': models.IntegerField(),
    }

    Meta = type('Meta', (object,), {'db_table': table_name})

    attrs = {'__module__':__name__, 'Meta': Meta, **fields }

    model = type(str(table_name), (BaseTable_gauge,), attrs)

    

    return model

class BaseTable_toggle(models.Model):
    common_field_1 = models.DateTimeField(default=datetime.now)
    common_field_2 = models.IntegerField()

    class Meta:
        abstract = True
        
        


def create_dynamic_model_toggle(table_name):
    fields = {
        'common_field_1': models.DateTimeField(default=datetime.now),
        'common_field_2': models.IntegerField(),
    }

    Meta = type('Meta', (object,), {'db_table': table_name})

    attrs = {'__module__': __name__, 'Meta': Meta, **fields}

    model = type(str(table_name), (BaseTable_toggle,), attrs)
    

    return model

class BaseTable_Label(models.Model):
    common_field_1 = models.DateTimeField(default=datetime.now)
    common_field_2 = models.TextField()

    class Meta:
        abstract = True
    
        


def create_dynamic_model_Label(table_name):
    fields = {
        'common_field_1': models.DateTimeField(default=datetime.now),
        'common_field_2': models.TextField(),
    }

    Meta = type('Meta', (object,), {'db_table': table_name})

    attrs = {'__module__': __name__, 'Meta': Meta, **fields}

    model = type(str(table_name), (BaseTable_Label,), attrs)
    
    
    return model

    
class BaseTable_electric_switch(models.Model):
    common_field_1 = models.DateTimeField(default=datetime.now)
    common_field_2 = models.IntegerField()

    class Meta:
        abstract = True
        
        


def create_dynamic_model_electric(table_name):
    fields = {
        'common_field_1': models.DateTimeField(default=datetime.now),
        'common_field_2': models.IntegerField(),
    }

    Meta = type('Meta', (object,), {'db_table': table_name})

    attrs = {'__module__': __name__, 'Meta': Meta, **fields}

    model = type(str(table_name), (BaseTable_electric_switch,), attrs)
    

    return model
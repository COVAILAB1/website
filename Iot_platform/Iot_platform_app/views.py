from django.shortcuts import render,redirect
from django.db.models.fields import IntegerField
from django.db.models import Sum,F
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse,JsonResponse
import re
from django.core import serializers
import pymongo
from django.db import DatabaseError, IntegrityError
import uuid
from django.template.defaultfilters import date
import paho.mqtt.client as mqtt
from functools import partial
from django.apps.registry import apps
from .models import *
from .signals import *
from datetime import datetime,timedelta
from django.db import models
from django.core import files
from django.conf import settings
from django.db import connections
from datetime import datetime,timedelta
from django.db.models import Q
import json
from django.contrib import messages
from django.template.loader import render_to_string
on_off_state={}
recieved_messages={}
mqtt_clients = {}


def login(request):
    return render(request,'Iot_platform_app/login.html')
def login_details(request):
    
    if request.method == 'POST':
        username = request.POST['usermail']
        password = request.POST['pass']
       
        datas = list(user_register_details.objects.filter(emailId=username).values())
        if len(datas) > 0:
        

            if datas[0]['password'] == password:
                request.session['user_id'] = username

                
                id =   datas[0]['user_id']
                device_names = device_table.objects.filter(user_id=id).values()
                
                print(device_names)
                messages.success(request,"Successfully Logged in !!! ")
                return redirect('dashboard')
            else:
                messages.error(request,"Incorrect Password")
                return render(request,'Iot_platform_app/login.html')
        else:
            messages.error(request,"Invalid mailId ")
            return render(request,'Iot_platform_app/login.html')
       

def signup(request):

    return render(request,'Iot_platform_app/register.html')

def register_data(request):
    data_name = list(user_register_details.objects.values_list('names',flat=True))
    print(data_name)
    data_email = list(user_register_details.objects.values_list('emailId', flat=True))
    data_number = list(user_register_details.objects.values_list('contact_number', flat=True))
    
    print(data_number)

    if request.method == 'POST':
        if request.POST['name'] not in data_name:
            if request.POST['usermail'] not in data_email:
                if int(request.POST['mobile']) not in data_number:
                    if request.POST['pass'] == request.POST['cpass']:
                        if re.findall("[a-z]",request.POST['pass']):
                            if re.findall("[A-Z]",request.POST['pass']):
                                if re.findall("[0-9]",request.POST['pass']):
                                    if re.findall("[@]",request.POST['pass']) or re.findall("[$]",request.POST['pass']) or re.findall("[&]",request.POST['pass']) or re.findall("[.]",request.POST['pass']):
                                        data = user_register_details()
                                        data.names = request.POST['name']
                                        data.password = request.POST['pass']
                                        data.contact_number = request.POST['mobile']
                                        data.emailId = request.POST['usermail']
                                        data.save()
                                        messages.success(request,"Successfully registered!!!")
                                        
                                        return render(request,'Iot_platform_app/login.html')
                                    else:
                                        messages.error(request,"Password should contain special character(@,$,&,.)")
                                       
                                else:
                                    messages.error(request,"Password should contain numeric character (1-9)")
                                    
                            else:
                                messages.error(request,"Password should contain capital letter(A-Z)")
                                
                        else:
                            messages.error(request,"Password should contain capital letter(a-z)")
                            
                    else:
                        messages.error(request,"Confirm password and password is not equal ")
                       
                   
                else:
                    messages.error(request," Mobile number already exists ")
                   
            else:
                messages.error(request,"EmailId already exists")
               
        else:
            messages.error(request,"Username already exists")
            
    return render(request,'Iot_platform_app/register.html')


def dashboard_home(request):
    # client = pymongo.MongoClient(settings.DATABASES['default']['HOST'], settings.DATABASES['default']['PORT'])
    # db = client[settings.DATABASES['default']['NAME']]
    # collection_name=apps.get_model(app_label='Iot_platform_app', model_name=str('3ea6892-6626-4ad7-8479-4befb27d67ab'))
    # result = db.command('collstats', collection_name)
    # size_in_bytes = result['size']
    # print(size_in_bytes)



    datas = list(user_register_details.objects.filter(emailId=request.session['user_id']).values())
        
    id =   datas[0]['user_id']
    device_names = device_table.objects.filter(user_id=id).values()
    
    print(device_names)

    return render(request,'Iot_platform_app/Home.html',{'devices' : device_names,'count' : len(device_names)})
   
def add_device(request):
    device_data = device_table()
    user_data = user_register_details()
    datas =  user_register_details.objects.get(emailId=request.session['user_id'])
    if request.method == 'POST':
        if device_table.objects.filter(user_id=user_register_details.objects.get(emailId=request.session['user_id'])).count() < 4:
            device_data.device_name = request.POST['device_name']
            
            
            device_data.user_id= datas
            print(datas)
            device_data.save()
        else:
            messages.error(request,"Limit exceed")
       
       
        
        return redirect('dashboard')
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker")
    else:
        print("Connection failed with error code", rc)
def on_publish(client, userdata, mid):
      print(userdata+"user_data")
      
def publish_values(user_id, topic, payload):
    print("Publishing data:", payload)
    if user_id in mqtt_clients:
        client = mqtt_clients[user_id]
        if client.is_connected():
            client.publish(topic, payload)
            print("Data published using existing client")
        else:
            print("Existing client is not connected")
    else:
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_publish = on_publish
        mqtt_clients[user_id] = client
        client.connect("broker.hivemq.com", 1883)
        client.loop_start()  
        client.publish(topic, payload)
        client.loop_stop()
  

    
@csrf_exempt
def publish_data(request,device_name):
    if request.method == 'POST':

        user_id_ = list(user_register_details.objects.filter(emailId=request.session['user_id']).values())[0]['user_id']
        
        if request.POST.get('type_switch') =='toggle':
            toggle = list(toggle_switch.objects.filter(toggle_switch_id=request.POST.get('id_val')).values())[0]
            
            on_off = ""
            topic = toggle['mqtt_topic']
            if request.POST.get('id_val') in on_off_state:
                if on_off_state[request.POST.get('id_val')]:
                    on_off_state[request.POST.get('id_val')] = not on_off_state[request.POST.get('id_val')]
                    on_off = "off"
                else:
                    on_off_state[request.POST.get('id_val')] = not on_off_state[request.POST.get('id_val')]
                    on_off = "on"
            else:
                on_off_state[request.POST.get('id_val')] = True
                on_off = "on"

            if on_off == "on":
                on_val = toggle['on_val']
                publish_values(user_id_,topic,on_val)
                table_name = f"{request.POST.get('id_val')}"
                
                dynamic_model = apps.get_model(app_label='Iot_platform_app', model_name=table_name)
                if dynamic_model is not None:
        
                    new_data = {
                        
                        'common_field_2':on_val,
                    }
                    obj = dynamic_model(**new_data)
                    obj.save()
                
            else:
                off_val = toggle['off_val']
                publish_values(user_id_,topic,off_val)
                table_name = f"{request.POST.get('id_val')}"
                
                dynamic_model = apps.get_model(app_label='Iot_platform_app', model_name=table_name)
                if dynamic_model is not None:
        
                    new_data = {
                        
                        'common_field_2':off_val,
                    }
                    obj = dynamic_model(**new_data)
                    obj.save()
        elif request.POST.get('type_switch') =='switch':
            toggle = list(electric_switch.objects.filter(electric_switch_id=request.POST.get('id_val')).values())[0]
            on_off = ""
            topic = toggle['mqtt_topic']
            if request.POST.get('id_val') in on_off_state:
                if on_off_state[request.POST.get('id_val')]:
                    on_off_state[request.POST.get('id_val')] = not on_off_state[request.POST.get('id_val')]
                    on_off = "off"
                else:
                    on_off_state[request.POST.get('id_val')] = not on_off_state[request.POST.get('id_val')]
                    on_off = "on"
            else:
                on_off_state[request.POST.get('id_val')] = True
                on_off = "on"

            if on_off == "on":
                on_val = toggle['on_val']
                publish_values(user_id_,topic,on_val)
                table_name = f"{request.POST.get('id_val')}"
                
                dynamic_model = apps.get_model(app_label='Iot_platform_app', model_name=table_name)
                if dynamic_model is not None:
        
                    new_data = {
                        
                        'common_field_2':on_val,
                    }
                    obj = dynamic_model(**new_data)
                    obj.save()
                
            else:
                off_val = toggle['off_val']
                publish_values(user_id_,topic,off_val)
                table_name = f"{request.POST.get('id_val')}"
                
                dynamic_model = apps.get_model(app_label='Iot_platform_app', model_name=table_name)
                if dynamic_model is not None:
        
                    new_data = {
                        
                        'common_field_2':off_val,
                    }
                    obj = dynamic_model(**new_data)
                    obj.save()    
        
    return HttpResponse(status=200)
def create_mqtt_client(user_id):
    
    client = mqtt.Client()
   
    mqtt_clients[user_id] = client

def subscribe_topics(user_id, topics):
    if user_id in mqtt_clients:
        client = mqtt_clients[user_id]
        print(topics)
        client.connect("broker.hivemq.com", 1883,60)
       
        for topic in topics:
            client.subscribe(topic)

   
def on_message(client, userdata, msg):
    
    user_id = userdata
    topic = msg.topic
    payload = msg.payload.decode()
    recieved_messages[topic] = payload
    
    
   
    
     
def setup_message_handling(user_id):
    if user_id in mqtt_clients:
        client = mqtt_clients[user_id]
       
        client.on_message = on_message
       
        client.user_data_set(user_id)

def start_mqtt_loops():
    for client in mqtt_clients.values():
        # Start the MQTT client loop in a separate thread
        client.loop_start()
@csrf_exempt
def mqtt_view_subscribe(request,device_name):
       
        
        user_id_ = list(user_register_details.objects.filter(emailId=request.session['user_id']).values())[0]['user_id']
        devices = list(device_table.objects.filter(user_id=user_id_).values())   
        device_id_ = 0
        
        topics_lis= []
        topic_id=[]
        for x in devices:
            if x['device_name'] == device_name:
                device_id_= x['device_id']
        gauge_topics = list(Gauge_table.objects.filter(device_id=device_id_).values())
        lab_topics = list(Label.objects.filter(device_id=device_id_).values())
        for y in gauge_topics:
        
            topics_lis.append(y['mqtt_topic'])
            topic_id.append(y['gauge_id'])
        for lab in lab_topics:
       
            topics_lis.append(lab['mqtt_topic'])
            topic_id.append(lab['label_id'])
        setup_message_handling(user_id_)  
        
        start_mqtt_loops()
        
        print(recieved_messages)
        
        if len(topics_lis)==4:
             
            table_name = f"{topic_id[0]}"
            
            dynamic_model = apps.get_model(app_label='Iot_platform_app', model_name=table_name)
            if dynamic_model is not None:
    
                new_data = {
                    
                    'common_field_2': recieved_messages[topics_lis[0]],
                }
                obj = dynamic_model(**new_data)
                obj.save()

            table_name1 = f"{topic_id[1]}"
            
            dynamic_model1 = apps.get_model(app_label='Iot_platform_app', model_name=table_name1)
            if dynamic_model1 is not None:
    
                new_data1 = {
                    
                    'common_field_2': recieved_messages[topics_lis[1]],
                }
                obj1 = dynamic_model1(**new_data1)
                obj1.save()
            table_name2 = f"{topic_id[2]}"
            
            dynamic_model2 = apps.get_model(app_label='Iot_platform_app', model_name=table_name2)
            if dynamic_model2 is not None:
    
                new_data2 = {
                    
                    'common_field_2': recieved_messages[topics_lis[2]],
                }
                obj2 = dynamic_model2(**new_data2)
                obj2.save()
            table_name3 = f"{topic_id[3]}"
            
            dynamic_model3 = apps.get_model(app_label='Iot_platform_app', model_name=table_name3)
            if dynamic_model3 is not None:
    
                new_data3 = {
                    
                    'common_field_2': recieved_messages[topics_lis[3]],
                }
                obj3 = dynamic_model3(**new_data3)
                obj3.save()

            return JsonResponse({'change_variable0':recieved_messages[topics_lis[0]],'change_variable1':recieved_messages[topics_lis[1]],'change_variable2':recieved_messages[topics_lis[2]],'change_variable3':recieved_messages[topics_lis[3]]})
           
            
        elif len(topics_lis)==3:
           
            table_name = f"{topic_id[0]}"
            
            dynamic_model = apps.get_model(app_label='Iot_platform_app', model_name=table_name)
            if dynamic_model is not None:
    
                new_data = {
                    
                    'common_field_2': recieved_messages[topics_lis[0]],
                }
                obj = dynamic_model(**new_data)
                obj.save()

            table_name1 = f"{topic_id[1]}"
            
            dynamic_model1 = apps.get_model(app_label='Iot_platform_app', model_name=table_name1)
            if dynamic_model1 is not None:
    
                new_data1 = {
                    
                    'common_field_2': recieved_messages[topics_lis[1]],
                }
                obj1 = dynamic_model1(**new_data1)
                obj1.save()
            table_name2 = f"{topic_id[2]}"
            
            dynamic_model2 = apps.get_model(app_label='Iot_platform_app', model_name=table_name2)
            if dynamic_model2 is not None:
    
                new_data2 = {
                    
                    'common_field_2': recieved_messages[topics_lis[2]],
                }
                obj2 = dynamic_model2(**new_data2)
                obj2.save()
            return JsonResponse({'change_variable0':recieved_messages[topics_lis[0]],'change_variable1':recieved_messages[topics_lis[1]],'change_variable2':recieved_messages[topics_lis[2]]})
           

        elif len(topics_lis)==2:
            
            table_name = f"{topic_id[0]}"
            
            dynamic_model = apps.get_model(app_label='Iot_platform_app', model_name=table_name)
            if dynamic_model is not None:
    
                new_data = {
                    
                    'common_field_2': recieved_messages[topics_lis[0]],
                }
                obj = dynamic_model(**new_data)
                obj.save()

            table_name1 = f"{topic_id[1]}"
            
            dynamic_model1 = apps.get_model(app_label='Iot_platform_app', model_name=table_name1)
            if dynamic_model1 is not None:
    
                new_data1 = {
                    
                    'common_field_2': recieved_messages[topics_lis[1]],
                }
                obj1 = dynamic_model1(**new_data1)
                obj1.save()
            return JsonResponse({'change_variable0':recieved_messages[topics_lis[0]],'change_variable1':recieved_messages[topics_lis[1]]})
            
        elif len(topics_lis)==1:
            
            table_name = f"{topic_id[0]}"
            
            dynamic_model = apps.get_model(app_label='Iot_platform_app', model_name=table_name)
            if dynamic_model is not None:
    
                new_data = {
                    
                    'common_field_2': recieved_messages[topics_lis[0]],
                }
                obj = dynamic_model(**new_data)
                obj.save()
        
            return JsonResponse({'change_variable0':recieved_messages[topics_lis[0]]})
           
        else:
            return JsonResponse({'change_variable0':1})
        
    

    
def device_page(request,devicename):
   
    user_id_ = list(user_register_details.objects.filter(emailId=request.session['user_id']).values())[0]['user_id']
    devices = list(device_table.objects.filter(user_id=user_id_).values())

    device_id_ = 0
    topics_lis= []
    
    for x in devices:
        if x['device_name'] == devicename:
            device_id_= x['device_id']
    gauge_topics = list(Gauge_table.objects.filter(device_id=device_id_).values())
    lab_topics = list(Label.objects.filter(device_id=device_id_).values())
    for y in gauge_topics:
       
        topics_lis.append(y['mqtt_topic'])
    for lab in lab_topics:
       
        topics_lis.append(lab['mqtt_topic'])
    print(topics_lis)
    if device_id_ not in mqtt_clients:
       
        create_mqtt_client(user_id_)
        subscribe_topics(user_id_, topics_lis)  
       
    
    device_gauge = Gauge_table.objects.filter(device_id=device_id_).values()
    
    device_Toggle = toggle_switch.objects.filter(device_id = device_id_).values()
    device_Label = Label.objects.filter(device_id = device_id_).values()
    device_switch = electric_switch.objects.filter(device_id = device_id_).values()
    print(device_switch)
    
    return render(request,'Iot_platform_app/device_page.html',{'device_gauge':device_gauge,'device_Toggle':device_Toggle,'device_Label':device_Label,'device_switch':device_switch ,'device_name':devicename})

def profile_page(request):

    datas = list(user_register_details.objects.filter(emailId=request.session['user_id']).values())[0]
    print(datas['dob'])
    device_list = device_table.objects.filter(user_id=datas['user_id']).values()
    print(device_list)



   

    

    return render(request,'Iot_platform_app/profile.html',{'datas':datas,'device_list':device_list})

def edit_profile(request):
    if request.method == 'POST':
        
        datas = user_register_details.objects.get(emailId=request.session['user_id'])
        
        datas.names = request.POST['NAME']
        datas.last_name=request.POST['l_name']
        datas.dob=request.POST['birthdate']
        datas.street_name=request.POST['streetname']
        datas.city=request.POST['city']
        datas.state=request.POST['state']
        datas.pincode=request.POST['Pincode']
        datas.contact_number = request.POST['mobile']
        datas.emailId = request.POST['email']
        datas.country = request.POST['country']
        datas.Institute_name=request.POST['Institutename']
        datas.department=request.POST['dept']

        datas.save()
       
        
        data = list(user_register_details.objects.filter(emailId=request.session['user_id']).values())[0]
        user_id =data['user_id']
        print(user_id)
        device_lists = list(device_table.objects.filter(user_id=user_id).values())
        print(len(device_lists))

        device_topics = {}
        for x in device_lists:
            print(x["device_id"] in list(Gauge_table.objects.filter(device_id=x["device_id"]).values()))
            
            
        
        
    messages.success(request,"Profile updated successfully!!!")  
    return redirect('profile_page')

def edit_device(request,device_name):
        print(device_name)
        print("redirected")
        user_id_ = list(user_register_details.objects.filter(emailId=request.session['user_id']).values())[0]['user_id']
        print(user_id_)
        devices = list(device_table.objects.filter(user_id=user_id_).values())
        print(devices)
        device_id_ = 0
        

        for x in devices:
            if x['device_name'] == device_name:
            
                device_id_= x['device_id']
        print(device_id_)
        device_gauge = Gauge_table.objects.filter(device_id=device_id_).values()
        gauge_lis = list(device_gauge)
        device_Toggle = toggle_switch.objects.filter(device_id = device_id_).values()
        toggle_lis = list(device_Toggle)
        device_label = Label.objects.filter(device_id = device_id_).values()
        label_lis = list(device_label)
        device_switch = electric_switch.objects.filter(device_id = device_id_).values()
        switch_lis = list(device_switch)
        device_list_cout=len(gauge_lis)+len(toggle_lis)+len(label_lis)+len(switch_lis)
        print(len(device_gauge))
        return render(request,'Iot_platform_app/device1.html',{'device_gauge':device_gauge,'device_Toggle':device_Toggle,'device_label':device_label,'device_name':device_name,'device_switch':device_switch, 'device_list_cout':device_list_cout})
    






def insert_dashboard(request):
    
    
    if request.method == 'POST':
        
        user_id_ = list(user_register_details.objects.filter(emailId=request.session['user_id']).values())[0]['user_id']
        devices = list(device_table.objects.filter(user_id=user_id_).values())
        print(devices)
        user_name = list(user_register_details.objects.filter(emailId=request.session['user_id']).values())[0]['names']
        device_id_ = 0
        

        for x in devices:
            if x['device_name'] == request.POST.get('device_name'):
            
                device_id_= x['device_id']
        if request.POST.get('type') == "gauge":
            print(request.POST.get('id_val'))
            if request.POST.get('id_val') == 'None':
                load_gauge = Gauge_table()
                
                load_gauge.device_id= device_table.objects.get(device_id=device_id_)
            
                load_gauge.min_val= request.POST['min_val']
                load_gauge.max_val= request.POST['max_val']
                load_gauge.Title = request.POST['title']
               
                load_gauge.mqtt_topic = "kt/{0}/{1}/{2}".format(user_name,request.POST.get('device_name'),request.POST['title'])
                load_gauge.save()
               
                
            else:
                print(request.POST.get('type'))
                load_gauge= Gauge_table.objects.get(gauge_id=request.POST.get('id_val'))
                load_gauge.min_val= request.POST['min_val']
                load_gauge.max_val= request.POST['max_val']
                load_gauge.Title = request.POST['title']
                
                load_gauge.mqtt_topic = "kt/{0}/{1}/{2}".format(user_name,request.POST.get('device_name'),request.POST['title'])
                load_gauge.save()
            

            
            
                
        elif request.POST.get('type') == "toggle":
             
            if request.POST.get('id_val') == 'None':
                print(request.POST.get('type'))
                load_toggle = toggle_switch()
                
                load_toggle.device_id= device_table.objects.get(device_id=device_id_)
            
                load_toggle.on_val= request.POST['on_val']
                load_toggle.off_val= request.POST['off_val']
                load_toggle.Title = request.POST['title']
                
                load_toggle.mqtt_topic = "kt/{0}/{1}/{2}".format(user_name,request.POST.get('device_name'),request.POST['title'])
                load_toggle.save()
                
                
            else: 
                load_toggle = toggle_switch.objects.get(toggle_switch_id=request.POST.get('id_val'))
                load_toggle.on_val= request.POST['on_val']
                load_toggle.off_val= request.POST['off_val']
                load_toggle.Title = request.POST['title']
                
                load_toggle.mqtt_topic = "kt/{0}/{1}/{2}".format(user_name,request.POST.get('device_name'),request.POST['title'])
                load_toggle.save()
        elif request.POST.get('type') == "switch":
             
            if request.POST.get('id_val') == 'None':
                print(request.POST.get('type'))
                load_switch = electric_switch()
                
                load_switch.device_id= device_table.objects.get(device_id=device_id_)

                load_switch.on_val= request.POST['on_val']
                load_switch.off_val= request.POST['off_val']
                load_switch.Title = request.POST['title']
                load_switch.mqtt_topic = "kt/{0}/{1}/{2}".format(user_name,request.POST.get('device_name'),request.POST['title'])
                load_switch.save()
                
                
            else: 
                load_switch = electric_switch.objects.get(electric_switch_id=request.POST.get('id_val'))
                load_switch.on_val= request.POST['on_val']
                load_switch.off_val= request.POST['off_val']
                load_switch.Title = request.POST['title']
                
                load_switch.mqtt_topic = "kt/{0}/{1}/{2}".format(user_name,request.POST.get('device_name'),request.POST['title'])
                load_switch.save()
        elif request.POST.get('type') == "Label":
            print(request.POST.get('type'))
            if request.POST.get('id_val') == 'None':
                print(request.POST.get('type'))
                load_label = Label()
                load_label.device_id= device_table.objects.get(device_id=device_id_)

                load_label.Title = request.POST['title']
               
                load_label.mqtt_topic = "kt/{0}/{1}/{2}".format(user_name,request.POST.get('device_name'),request.POST['title'])
                load_label.save()
                
                
            else: 
                load_label = Label.objects.get(toggle_switch_id=request.POST.get('id_val'))
                
                load_label.Title = request.POST['title']
                
                load_label.mqtt_topic = "kt/{0}/{1}/{2}".format(user_name,request.POST.get('device_name'),request.POST['title'])
                load_label.save()
        
        devices = list(device_table.objects.filter(user_id=user_id_).values())
        device_id_ = 0
        
        for x in devices:
            if x['device_name'] == request.POST.get('device_name'):
                device_id_= x['device_id']
       
        device_gauge = Gauge_table.objects.filter(device_id=device_id_).values()
        gauge_lis = list(device_gauge)
        device_Toggle = toggle_switch.objects.filter(device_id = device_id_).values()
        toggle_lis = list(device_Toggle)
        device_Label = Label.objects.filter(device_id = device_id_).values()
        label_lis = list(device_Label)
        device_list_cout=len(gauge_lis)+len(toggle_lis)+len(label_lis)
        return render(request,'Iot_platform_app/device1.html',{'device_gauge':device_gauge,'device_Toggle':device_Toggle,'device_label':device_Label,'device_name':request.POST.get('device_name'),'device_list_cout':device_list_cout})   

def delete_data_dashboard(request):
    if request.method == 'POST':
        print("delete",request.POST.get('id_val'))
        if request.POST.get('type') == "gauge":
            Gauge_table.objects.filter(gauge_id=request.POST.get('id_val')).delete()
            dynamic_table_names_of_gauge.objects.filter(model_name=request.POST.get('id_val')).delete()
        elif request.POST.get('type') == "toggle":
            toggle_switch.objects.filter(toggle_switch_id=request.POST.get('id_val')).delete()
            dynamic_table_names_toggle.objects.filter(model_name=request.POST.get('id_val')).delete()
        elif request.POST.get('type') == "label":
            Label.objects.filter(label_id=request.POST.get('id_val')).delete()
            dynamic_table_names_label.objects.filter(model_name=request.POST.get('id_val')).delete()
        elif request.POST.get('type') == "switch":
            electric_switch.objects.filter(electric_switch_id=request.POST.get('id_val')).delete()
            dynamic_table_names_switch.objects.filter(model_name=request.POST.get('id_val')).delete()
        
            
        user_id_ = list(user_register_details.objects.filter(emailId=request.session['user_id']).values())[0]['user_id']
        devices = list(device_table.objects.filter(user_id=user_id_).values())
        device_id_ = 0
        

        for x in devices:
            if x['device_name'] == request.POST.get('device_name'):
            
                device_id_= x['device_id']
       
        device_gauge = Gauge_table.objects.filter(device_id=device_id_).values()
        gauge_lis = list(device_gauge)
        device_Toggle = toggle_switch.objects.filter(device_id = device_id_).values()
        toggle_lis = list(device_Toggle)
        device_label = Label.objects.filter(device_id = device_id_).values()
        label_lis = list(device_label)
        device_list_cout=len(gauge_lis)+len(toggle_lis)+len(label_lis)
        print(len(device_gauge))

        return render(request,'Iot_platform_app/device1.html',{'device_gauge':device_gauge,'device_Toggle':device_Toggle,'device_label':device_label,'device_name':request.POST.get('device_name'),'device_list_cout':device_list_cout})
def analytics(request):
    user_id_ = list(user_register_details.objects.filter(emailId=request.session['user_id']).values())[0]['user_id']
    devices = list(device_table.objects.filter(user_id=user_id_).values())
    print(devices)
    return render(request,'Iot_platform_app/analytics.html',{'device_names':devices})
@csrf_exempt     
def graph(request):
    if request.method=='POST':
            
    
        return render(request,'Iot_platform_app/graph.html')
@csrf_exempt 
def load_graph_template(request):
    if request.method=='POST':
        dict_count = []
        template_name = "Iot_platform_app/"+str(request.POST.get('template_name'))
        datas = list(user_register_details.objects.filter(emailId=request.session['user_id']).values())
        user_id = datas[0]["user_id"]
        device_datas = list(device_table.objects.filter(user_id=user_id).values())
        device_id = 0
        print("datas",device_datas,request.POST.get('device_name'))
        for x in device_datas:
            if x["device_name"] == request.POST.get('device_name'):
                print(x["device_id"])
                device_id = x["device_id"]
        
        device_list = []
        device_id_list =[]
        gauge_datas = list(Gauge_table.objects.filter(device_id=device_id).values())
        lab_datas = list(Label.objects.filter(device_id=device_id).values())
        toggle_datas = list(toggle_switch.objects.filter(device_id=device_id).values())
        electric_switch_datas = list(electric_switch.objects.filter(device_id=device_id).values())
        print(len(lab_datas))
        for gauge in gauge_datas:
            device_list.append(gauge["Title"])
            device_id_list.append(gauge["gauge_id"])
        for lab in lab_datas:
            device_list.append(lab["Title"])
            device_id_list.append(lab["label_id"])
        for toggle in toggle_datas:
            device_list.append(toggle["Title"])
            device_id_list.append(toggle["toggle_switch_id"])
        for electric in electric_switch_datas:
            device_list.append(electric["Title"])
            device_id_list.append(electric["electric_switch_id"])

        print(request.POST.get('duration'))

        
        for d in range(0,len(device_list)):



          
            datas = apps.get_model(app_label='Iot_platform_app', model_name=str( device_id_list[d]))
                
            current_datetime = datetime.now()


            start_datetime = current_datetime - timedelta(hours=1)
            end_datetime = current_datetime


            data = datas.objects.filter(common_field_1__gte=start_datetime, common_field_1__lt=end_datetime)


            data_per_interval = []


            interval = 10  
            num_intervals = 7
            for i in range(num_intervals):
                        interval_start = start_datetime + timedelta(minutes=interval * i)
                        interval_end = interval_start + timedelta(minutes=interval)
                        data_for_interval = data.filter(common_field_1__gte=interval_start, common_field_1__lt=interval_end)
                        count = data_for_interval.count()
                        data_per_interval.append({
                            'y': interval_start.strftime('%Y-%m-%d %H:%M:%S'),
                        
                            'a': count,
                        })
            print(data_per_interval)
                
            dict_count.append(json.dumps(data_per_interval))
            
            
            if len(dict_count)==0:
                dict_count0 = ''
                dict_count1 = ''
                dict_count2 = ''
                dict_count3 = ''
            elif len(dict_count)==1:
                dict_count0 = dict_count[0]
                dict_count1 = ''
                dict_count2 = ''
                dict_count3 = ''
            elif len(dict_count)==2:
                dict_count0 = dict_count[0]
                dict_count1 = dict_count[1]
                dict_count2 = ''
                dict_count3 = ''
            elif len(dict_count)==3:
                dict_count0 = dict_count[0]
                dict_count1 = dict_count[1]
                dict_count2 = dict_count[2]
                dict_count3 = ''
            elif len(dict_count)==4:
                dict_count0 = dict_count[0]
                dict_count1 = dict_count[1]
                dict_count2 = dict_count[2]
                dict_count3 = dict_count[3]


            print(device_list)
        context={"device_name":request.POST.get('device_name'),"dict_count0":dict_count0,"dict_count1":dict_count1,"dict_count2":dict_count2,"dict_count3":dict_count3,"device_list":device_list,"device_name":request.POST.get('device_name'),"index":"onehr"}
        html = render(request, template_name,context).content.decode('utf-8')
        return JsonResponse({'html': html})
# def storage_size(device_id):
#     print("in storage")
#     device_id_list =[]
#     storage_total =[]
#     gauge_datas = list(Gauge_table.objects.filter(device_id=device_id).values())
#     lab_datas = list(Label.objects.filter(device_id=device_id).values())
#     toggle_datas = list(toggle_switch.objects.filter(device_id=device_id).values())
#     print(len(lab_datas))
#     for gauge in gauge_datas:
       
#         device_id_list.append(gauge["gauge_id"])
#     for lab in lab_datas:
       
#         device_id_list.append(lab["label_id"])
#     for toggle in toggle_datas:
       
#         device_id_list.append(toggle["toggle_switch_id"])
    
#     for id_ in device_id_list:
#         model = apps.get_model(app_label='Iot_platform_app', model_name=str(id_))
#         total_size = model.objects.aggregate(total_size=Sum(F('common_field_1') + F('common_field_2'),output_field=IntegerField()))['total_size']
#         print(total_size)


@csrf_exempt
def calculate_data(request):
    
    if request.method == 'POST':
        template_name = "Iot_platform_app/graph.html"
        datas = list(user_register_details.objects.filter(emailId=request.session['user_id']).values())
        user_id = datas[0]["user_id"]
        device_datas = list(device_table.objects.filter(user_id=user_id).values())
        device_id = 0
        print("datas",device_datas,request.POST.get('device_name'))
        for x in device_datas:
            if x["device_name"] == request.POST.get('device_name'):
                print(x["device_id"])
                device_id = x["device_id"]
        
        device_list = []
        device_id_list =[]
        dict_count=[]
        gauge_datas = list(Gauge_table.objects.filter(device_id=device_id).values())
        lab_datas = list(Label.objects.filter(device_id=device_id).values())
        toggle_datas = list(toggle_switch.objects.filter(device_id=device_id).values())
        electric_switch_datas = list(electric_switch.objects.filter(device_id=device_id).values())
        print(len(lab_datas))
        for gauge in gauge_datas:
            device_list.append(gauge["Title"])
            device_id_list.append(gauge["gauge_id"])
        for lab in lab_datas:
            device_list.append(lab["Title"])
            device_id_list.append(lab["label_id"])
        for toggle in toggle_datas:
            device_list.append(toggle["Title"])
            device_id_list.append(toggle["toggle_switch_id"])
        for electric in electric_switch_datas:
            device_list.append(electric["Title"])
            device_id_list.append(electric["electric_switch_id"])
        print("device_list",device_list)
        print(device_id_list)

        print(request.POST.get('duration'))
    

        dict_count=[]
        dict_count0 = ''
        dict_count1 = ''
        dict_count2 = ''
        dict_count3 = ''
        index=''

        if request.POST.get("duration") == "oneweek":
            for d in range(0,len(device_list)):
                dict_val = []
                print(device_id_list[d])

                datas = apps.get_model(app_label='Iot_platform_app', model_name=str(device_id_list[d]))
                print(datas)
                current_date = datetime.now()

                
                one_week_ago = current_date - timedelta(days=7)


                data_per_day = {}
                current_day = one_week_ago
                one_week_ago = current_date - timedelta(days=7)


                data = datas.objects.filter(common_field_1__gte=one_week_ago, common_field_1__lt=current_date)
                print(data)
                data_per_day = {}
                date_iterator = one_week_ago
                
                for _ in range(7):
                    next_date = date_iterator + timedelta(days=1)
                    data_for_day = data.filter(common_field_1__gte=date_iterator, common_field_1__lt=next_date)
                    print(data_for_day)
                    data_per_day[next_date] = data_for_day.count() 
                    date_iterator = next_date
                
                for day, count in data_per_day.items():
                    day = day.strftime("%Y-%m-%d")
                
                    dict_val.append({"y" :day,"a":count})
                dict_count.append(json.dumps(dict_val))
                index="oneweek"
                
        elif request.POST.get("duration") == "oneday":
            index="oneday"
            for d in range(0,len(device_list)):    
                datas = apps.get_model(app_label='Iot_platform_app', model_name=str(device_id_list[d]))
                
                current_datetime = datetime.now()

                
                start_datetime = current_datetime - timedelta(days=1)
                end_datetime = current_datetime
                data = datas.objects.filter(common_field_1__gte=start_datetime, common_field_1__lt=end_datetime)

                data_per_hour = []

                for i in range(25):
                    
                    hour_start = start_datetime + timedelta(hours=i)
                    hour_end = hour_start + timedelta(hours=1)
                    data_for_hour = data.filter(common_field_1__gte=hour_start, common_field_1__lt=hour_end)
                
                    count = data_for_hour.count()
                    print(hour_start)
                    data_per_hour.append({
                                'y': hour_start.strftime("%Y-%m-%d %H:%M:%S"),
                                'a': count,
                            })

            
                dict_count.append(json.dumps(data_per_hour))
                print(dict_count)
                print(request.POST.get("duration"))
        elif request.POST.get("duration") == "onehr":
            index="onehr"
            print(device_id_list)
            for d in range(0,len(device_list)): 
                datas = apps.get_model(app_label='Iot_platform_app', model_name=str(device_id_list[d]))
                
                current_datetime = datetime.now()


                start_datetime = current_datetime- timedelta(hours=1)
                end_datetime = current_datetime


                data = datas.objects.filter(common_field_1__gte=start_datetime, common_field_1__lt=end_datetime)

                interval = 10  
                num_intervals = 6
                data_per_interval = []
                for i in range(num_intervals+1):
                        
                        interval_start = start_datetime + timedelta(minutes=interval * i)
                        interval_end = interval_start + timedelta(minutes=interval)
                        data_for_interval = data.filter(common_field_1__gte=interval_start, common_field_1__lt=interval_end)
                        count = data_for_interval.count()
                        data_per_interval.append({
                            'y': interval_start.strftime('%Y-%m-%d %H:%M:%S'),
                        
                            'a': count,
                        })
                        print(data_per_interval)
                
                dict_count.append(json.dumps(data_per_interval))

        elif request.POST.get("duration") == "onemonth":
            index="onemonth"
            for d in range(0,len(device_list)):
                print(device_id_list[d]) 
                datas = apps.get_model(app_label='Iot_platform_app', model_name=str(device_id_list[d]))
                
                current_datetime = datetime.now()


                start_datetime = current_datetime - timedelta(days=30)
                end_datetime = current_datetime
                print(start_datetime,end_datetime)
                data = datas.objects.filter(common_field_1__gte=start_datetime, common_field_1__lt=end_datetime)


                data_per_day = []
                date_iterator = start_datetime.date()
                for _ in range(31):
                    next_date = date_iterator + timedelta(days=1)
                    data_for_day = data.filter(common_field_1__gte=date_iterator, common_field_1__lt=next_date)
                    count = data_for_day.count()
                    data_per_day.append({
                        'y': date_iterator.strftime('%Y-%m-%d'),
                        'a': count
                    })   
                    date_iterator = next_date
                print(dict_count)
                dict_count.append(json.dumps(data_per_day))
        if len(dict_count)==0:
                dict_count0 = ''
                dict_count1 = ''
                dict_count2 = ''
                dict_count3 = ''
                print(dict_count)
                context={"device_name":request.POST.get('device_name'),"dict_count0":dict_count0,"dict_count1":dict_count1,"dict_count2":dict_count2,"dict_count3":dict_count3,"device_list":device_list,"device_name":request.POST.get('device_name'),"index":index}
                html = render(request, template_name,context).content.decode('utf-8')
                return JsonResponse({'html': html})
        elif len(dict_count)==1:
            dict_count0 = dict_count[0]
            dict_count1 = ''
            dict_count2 = ''
            dict_count3 = ''
            print(dict_count)
            context={"device_name":request.POST.get('device_name'),"dict_count0":dict_count0,"dict_count1":dict_count1,"dict_count2":dict_count2,"dict_count3":dict_count3,"device_list":device_list,"device_name":request.POST.get('device_name'),"index":index}
            html = render(request, template_name,context).content.decode('utf-8')
            return JsonResponse({'html': html})
        elif len(dict_count)==2:
            dict_count0 = dict_count[0]
            dict_count1 = dict_count[1]
            dict_count2 = ''
            dict_count3 = ''
            print(dict_count)
            context={"device_name":request.POST.get('device_name'),"dict_count0":dict_count0,"dict_count1":dict_count1,"dict_count2":dict_count2,"dict_count3":dict_count3,"device_list":device_list,"device_name":request.POST.get('device_name'),"index":index}
            html = render(request, template_name,context).content.decode('utf-8')
            return JsonResponse({'html': html})
        elif len(dict_count)==3:
            dict_count0 = dict_count[0]
            dict_count1 = dict_count[1]
            dict_count2 = dict_count[2]
            dict_count3 = ''
            print(dict_count)
            context={"device_name":request.POST.get('device_name'),"dict_count0":dict_count0,"dict_count1":dict_count1,"dict_count2":dict_count2,"dict_count3":dict_count3,"device_list":device_list,"device_name":request.POST.get('device_name'),"index":index}
            html = render(request, template_name,context).content.decode('utf-8')
            return JsonResponse({'html': html})
        elif len(dict_count)==4:
            dict_count0 = dict_count[0]
            dict_count1 = dict_count[1]
            dict_count2 = dict_count[2]
            dict_count3 = dict_count[3]
            print(dict_count)
            context={"device_name":request.POST.get('device_name'),"dict_count0":dict_count0,"dict_count1":dict_count1,"dict_count2":dict_count2,"dict_count3":dict_count3,"device_list":device_list,"device_name":request.POST.get('device_name'),"index":index}
            html = render(request, template_name,context).content.decode('utf-8')
            return JsonResponse({'html': html})
def logout(request):
    del request.session['user_id']
    messages.success(request,"Sucessfully Logged out!!!")
    return render(request,'Iot_platform_app/login.html')

def delete_device(request):
    print("delete_location")
    if request.method == 'POST':
        device_name = request.POST.get("device_name")
        user_id_ = list(user_register_details.objects.filter(emailId=request.session['user_id']).values())[0]['user_id']
        devices = list(device_table.objects.filter(user_id=user_id_).values())   
        device_id_ = 0
        for x in devices:
            if x['device_name'] == device_name:
                device_id_= x['device_id']

        device_table.objects.filter(device_id=device_id_).delete()
        Gauge_table.objects.filter(device_id=device_id_).delete()
        #dynamic_table_names_of_gauge.objects.filter(model_name=request.POST.get('id_val')).delete()
    
        toggle_switch.objects.filter(device_id=device_id_).delete()
        #dynamic_table_names_toggle.objects.filter(model_name=request.POST.get('id_val')).delete()
    
        Label.objects.filter(device_id=device_id_).delete()
        #dynamic_table_names_label.objects.filter(model_name=request.POST.get('id_val')).delete()
    return redirect('dashboard')

def admin_login_data(request):
    if request.method == 'POST':
        
        admin_data = admin_details()
        admin_data.admin_name = request.POST['admin_name']
        admin_data.admin_contact_number=request.POST['mobile_no']
        admin_data.admin_emailId=request.POST['admin_email_id']
        if request.POST['password'] == request.POST['confirm_pass']:

            admin_data.admin_password=request.POST['password']
            try:
                admin_data.save()
                
            except DatabaseError as e:
                messages.error(request,"Email ID or Mobile number already exists")
               
            
        else:
            messages.error(request,"Confirm password is not same as password")

        return redirect('create_admin')

def create_admin(request):

    return render(request,'Iot_platform_app/create_admin.html')

def admin_login_page(request):
    return render(request,'Iot_platform_app/admin_login.html')
def admin_signin(request):

    if request.method=='POST':
        try:
            print("HI")
            mailId = request.POST['adminmail']
            password = request.POST['pass']
            print(request.POST['adminmail'])
            datas = list(admin_details.objects.filter(admin_emailId=mailId).values())[0]
            print(datas)
            if len(datas) >0:
                if password == datas['admin_password']:
                    request.session['user_id'] = mailId
                    return redirect('create_admin')
                else:
                    messages.warning(request,"Incorrect password")
                    return redirect('admin_login_page')
            else:
                messages.warning(request,"Invalid EmailID")
                return redirect('admin_login_page')
        except:
            messages.warning(request,"Invalid EmailID")
            return redirect('admin_login_page')
            

   
def user_data(request):
    values = user_register_details.objects.all()

    return render(request,'Iot_platform_app/data.html',{"values":values})
def views_data(request,id):
    user_data = user_register_details.objects.filter(user_id=id).values()[0]
    name=user_data['names']
    device_names=device_table.objects.filter(user_id=id).values()
    
    return render(request,'Iot_platform_app/view_data.html',{'Name':name,'device_names':device_names})
@csrf_exempt    
def user_devices(request):
    if request.method == 'POST':
        print(request.POST.get('id_val'))
        gauge_values = list(Gauge_table.objects.filter(device_id=request.POST.get('id_val')).values_list('Title','gauge_id'))
        toggle_values = list(toggle_switch.objects.filter(device_id=request.POST.get('id_val')).values_list('Title','toggle_switch_id'))
        label_values = list(Label.objects.filter(device_id=request.POST.get('id_val')).values_list('Title','label_id'))
        electric_values = list(electric_switch.objects.filter(device_id=request.POST.get('id_val')).values_list('Title','electric_switch_id'))
        device_names=[]
        device_id=[]

        for gauge in gauge_values:
            device_names.append(gauge[0])
            device_id.append(gauge[1])
        for toggle in toggle_values:
            device_names.append(toggle[0])
            device_id.append(toggle[1])
        for label in label_values:
            device_names.append(label[0])
            device_id.append(label[1])
        for electric in electric_values:
            device_names.append(electric[0])
            device_id.append(electric[1])

        print(device_names,device_id)

        count_datas=[]
        for _id_  in device_id:
            model = apps.get_model('Iot_platform_app',str(_id_))
            datas=model.objects.all()
            count_datas.append(datas.count()-1)
        print(count_datas)
        return JsonResponse({'device_names':device_names,'data_counts':count_datas})

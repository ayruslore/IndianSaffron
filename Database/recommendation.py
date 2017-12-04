from gevent import monkey; monkey.patch_all()
from bottle import route, run, response
import pandas as pd
import bottle
import commands
import operator
import json
import razorpay
import googlemaps
from datetime import datetime
import random
import requests

import redis_functions as rd
from redis_functions import *
global dishes_db

i1 = open('dishes15.txt','r').read()
df = pd.read_json(json.loads(i1),orient='index')
dishes_db = df

app = bottle.app()

@app.route('/recommend')
def reco():
	global dishes_db
	result = dishes_db[dishes_db['stock']=='In']
	result = {"reco": result['name'].tolist()[:5],"links":result['link'].tolist()[:5],"prices":result['price'].tolist()[:5]}
	yield json.dumps(result)

@app.route('/recommend/<v_n>/<base_ing>/<category>')
def reco_filter1(v_n,base_ing,category):
	global dishes_db
	result = dishes_db[dishes_db['stock']=='In']
	if v_n in ["veg","nonveg"]:
		result = result[result["v_n"]==v_n]
	if base_ing in ["chicken","mutton","dal","egg","aloo","soya","curd","rice","paneer"]:
		result = result[result["base_ing"]==base_ing]
	if category in ["kathi_roll","rice","roti_parantha","dahi","curry","shorba","kebab","dessert"]:
		result = result[result["category"]==category]
	result = {"reco": result['name'].tolist()[:5],"links":result['link'].tolist()[:5],"prices":result['price'].tolist()[:5]}
	yield json.dumps(result)

def reco_filter(v_n,base_ing,category):
	global dishes_db
	result = dishes_db[dishes_db['stock']=='In']
	if v_n in ["veg","nonveg"]:
		result = result[result["v_n"]==v_n]
	if base_ing in ["chicken","mutton","dal","egg","aloo","soya","curd","rice","paneer"]:
		result = result[result["base_ing"]==base_ing]
	if category in ["kathi_roll","rice","roti_parantha","dahi","curry","shorba","kebab","dessert"]:
		result = result[result["category"]==category]
	result = {"reco": result['name'].tolist()[:5],"links":result['link'].tolist()[:5],"prices":result['price'].tolist()[:5]}
	return result

@app.route('/specials')
def special():
	global dishes_db
	specials = ['makai_ke_kebab','noorani_tangri_kebab','mirch_ka_salan','chicken_wings_masala']
	print specials
	#result = dishes_db[dishes_db['stock']=='In']
	#print result
	result = {"reco":[],"links":[],"prices":[]}
	for dish in specials:
		print dish
		res = dishes_db[dishes_db["name"] == dish]
		print res
		result["reco"].append(res["name"].tolist()[0])
		result["prices"].append(res["price"].tolist()[0])
		result["links"].append(res["link"].tolist()[0])
	print result
	yield json.dumps(result)

@app.route('/<identity>/get_history_reco')
def get_recommend_dishes2(identity):
	global dishes_db
	print dishes_db
	if(key_exists("user:"+str(identity)+":ordered_items") == False):
		dik = reco_filter('k','k','k')
		print dik
		yield json.dumps(dik)
	else:
		di = dishes_db[dishes_db['stock']=='In']
		dishes_list = get_history_reco3(di,identity)
		recommendation = {"reco": [],"links":[],"prices":[]}
		for dish in dishes_list:
			result = dishes_db[dishes_db["name"] == dish]
			recommendation["reco"].append(result["name"].tolist()[0])
			recommendation["prices"].append(result["price"].tolist()[0])
			recommendation["links"].append(result["link"].tolist()[0])
		print recommendation
		yield json.dumps(recommendation)

def get_recommend_dishes(identity):
	global dishes_db
	if(key_exists("user:"+str(identity)+":ordered_items") == False):
		return json.dumps(reco_filter('k','k','k'))
	else:
		dishes_list = get_history_reco(identity)
		recommendation = {"reco": [],"links":[],"prices":[]}
		for dish in dishes_list:
			#dishes_db[dishes_db[dishes_db['stock']=='In']['name']==dish]
			result = dishes_db[dishes_db["name"] == dish]
			recommendation["reco"].append(result["name"].tolist()[0])
			recommendation["prices"].append(result["price"].tolist()[0])
			recommendation["links"].append(result["link"].tolist()[0])
		return recommendation


def get_usual(identity):
	key = "user:"+str(identity)+":ordered_items"
	total = get_total_sorted(key)
	count = int(ss_count(key))
	count = min(5,count) #print count
	d={}
	if (count >=1):
		'''
		top_item, top_quantity = get_top_item(key)
		d[top_item]= float(top_quantity) / total * 1.0
		i=2'''
		for i in range(1,count +1):
			item, quant = get_nth_item(key, i)
			d[item]= float(quant) / total * 1.0
	return d

@app.route('/set_new_user_details/<identity>/<name>')
def set_new_details(identity,name):
	key = "user:" + str(identity) + ":details"
	set_hash_field(key,"name",name.replace(" ","_"))
	yield json.dumps({"first_name":name})

def get_price(items):
	global dishes_db
	result = {}
	count = 1
	for dish in items:
		print dish
		print dishes_db[dishes_db["name"] == dish[0]]["price"].tolist()
		result[str(count)] = [dish[0].replace("_"," "),dishes_db[dishes_db["name"] == dish[0]]["price"].tolist()[0],dish[1],dishes_db[dishes_db["name"] == dish[0]]["link"].tolist()[0]]
		count = count + 1
	return result

@app.route('/get_user_details/<identity>')
def user_details(identity):
	key = "user:" + str(identity) + ":details"
	result ={}
	if(key_exists(key) == False):
		result["name"] = "No name"
		result["usual"] = "Nothing"
		yield json.dumps(result)
	else:
		result["name"] = get_hash_field(key,"name").replace("_"," ")
		if(key_exists("user:"+str(identity)+":ordered_items") == True):
			s1 = get_key("user:"+str(identity)+":tic")
			result["day_diff"] = "None"
			result["time_diff"] = "None"
			if s1 !=  "":
			        s1 = s1.split("X")
				print dishes_db
				d1 = float(s1[0])
		        	t1 = float(s1[1])
				s2 = get_time_stamp()
	       		 	s2 = s2.split("X")
	        		d2 = float(s2[0])
	        		t2 = float(s2[1])
				result["day_diff"] = int(d2 - d1)
				result["time_diff"] = int(t2 - t1)
			result["usual"] = get_price(sorted(get_usual(identity).items(),key = lambda x:x[1],reverse = True))
		else:
			result["usual"] = "Nothing"
		yield json.dumps(result)
#Courses Category
#Shorba   shorba
#Kebab    kebab
#Kathi Rolls  kathi_roll
#Curries curry
#Dal  dal
#Rice  rice
#Roti Parantha  parantha
#Dahi dahi
#Dessert  dessert
def store_the_dishes():
	temp =  {"Courses":{"Shorba":{"Tamatar Dhaniya Ka Shorba":
["195","Veg","tomato"],"Murg Pudina Shorba":
["215","Non Veg","chicken"]},"Kebab":{"Dahi Ke Kebab":
["245","Veg","curd"],"Makai Ke Kebab":
["255","Veg","corn"],"Achari Paneer Tikka":
["255","Veg","paneer"],"Bharwan Tandoori Aloo":
["255","Veg","aloo"],"Soya Chaap":
["245","Veg","soya"],"Noorani Tangri Kebab":
["315","Non Veg","chicken"],"Mutton Gilafi Seekh Kebab":
["315","Non Veg","mutton"],"Mutton Burrah":
["315","Non Veg","mutton"],"Murg Tikka":
["295","Non Veg","chicken"],"Murg Malai Tikka":
["295","Non Veg","chicken"]},"Kathi Rolls":{"Paneer Roll":
["230","Veg","paneer"],"Aloo Masala Roll":
["215","Veg","aloo"],"Soya Chaap Roll":
["215","Veg","soya"],"Murg Tikka Roll":
["245","Non Veg","chicken"],"Murg Malai Roll":
["245","Non Veg","chicken"],"Mutton Seekh Roll":
["265","Non Veg","mutton"]},"Curries":{"Veg Nizami Handi":
["355", "Veg","U"],"Methi Chaman":
["355","Veg","paneer"],"Paneer Mirch Masala":
["355","Veg","paneer"],"Paneer Makhani":
["385", "Veg","paneer"],"Aloo Gobi Masala":
["325", "Veg","aloo"],"Malai Kofta":
["325","Veg","aloo"],"Jeera Aloo":
["325","Veg","aloo"],"Mirch Ka Salan":
["385","Veg","peanut"],"Murg Makhani half":
["375","Non Veg","chicken"],"Murg Makhani Boneless half":
["425","Non Veg","chicken"],"Murg Makhani":
["625","Non Veg","chicken"],"Murg Makhani Boneless":
["685","Non Veg","chicken"],"Kadhai Murg":
["425","Non Veg","chicken"],"Chicken Wings Masala":
["455","Non Veg","chicken"],"Mutton Rogan Josh":
["455","Non Veg","mutton"],"Mutton Bhuna Gosht":
["445","Non Veg","mutton"],"Egg Curry":
["325","Non Veg","egg"],"Chicken Curry South Indian Style":
["425","Non Veg","chicken"],"Laal Maas":
["465","Non Veg","mutton"]},"Dal":{"Dal Makhani":
["295","Veg","dal"],"Dal Tadka":
["275","Veg","dal"]},"Rice":{"Khichdi":
["255", "Veg","rice"],"Jeera Rice":
["155", "Veg","rice"],"Veg Pulao":
["255","Veg","rice"],"Chicken Biryani":
["315", "Veg","rice"],"Mutton Biryani":
["355","Veg","rice"]},"Roti Parantha":{"Taandoori Roti":
["30", "Veg","U"],"Lachha Parantha":
["65", "Veg","U"], "Butter Naan":
["55", "Veg","U"], "Plain Naan":
["45", "Veg","U"],"Stuffed Kulcha":
["65","Veg","U"],"Roomali Roti":
["45","Veg","U"],"Kashmiri Kandhari Naan":
["75","Veg","U"],"Pudina Parantha":
["55","Veg","U"],"Garlic Naan":
["65","Veg","U"],"Chur Chur Parantha":
["65","Veg","U"],"Laal Mirch Parantha":
["65","Veg","U"]},"Dahi":{"Mixed Veg Raita":
["105","Veg","curd"],"Boondi Raita":
["95","Veg","curd"]},"Dessert":{"Gulab Jamun":
["95","Veg","U"],"Phirni":
["110","Veg","U"],"Rasmalai":
["125","Veg","U"],"Kheer":
["125","Veg","U"]}}}
	global dishes_db , dishes_dicti
	dishes_db_new = {"name":[],"v_n":[],"base_ing":[],"course":[],"category":[],"count":[],"price":[],"link":[],"stock":[]}
	for course in temp["Courses"]:
		for dish in temp["Courses"][course]:
			dishes_db_new["course"].append(course)
			if(course == "Shorba"):
				dishes_db_new["category"].append("shorba")
			elif(course == "Kebab"):
				dishes_db_new["category"].append("kebab")
			elif(course == "Kathi Rolls"):
				dishes_db_new["category"].append("kathi_roll")
			elif(course == "Curries"):
				dishes_db_new["category"].append("curry")
			elif(course == "Dal"):
				dishes_db_new["category"].append("dal")
			elif(course == "Rice"):
				dishes_db_new["category"].append("rice")
			elif(course == "Roti Parantha"):
				dishes_db_new["category"].append("roti_parantha")
			elif(course == "Dahi"):
				dishes_db_new["category"].append("dahi")
			elif(course == "Dessert"):
				dishes_db_new["category"].append("dessert")
			else:
				dishes_db_new["category"].append("HERO")

			dishes_db_new["name"].append(dish.replace(" ","_").lower().replace("(","").replace(")",""))
			dishes_db_new["stock"].append("In")
			s = 'http://ec2-13-126-89-61.ap-south-1.compute.amazonaws.com/img/db/'
			dishes_db_new["link"].append(s + dish.replace(" ","-").replace("(","").replace(")","").upper() + ".jpg")

			if dish in dishes_dicti:
				dishes_db_new["count"].append(dishes_dicti[dish.replace(" ","_").lower().replace("(","").replace(")","")])
			else:
				dishes_db_new["count"].append(0)

			count = 1
			for data in temp["Courses"][course][dish]:
				if (count == 1):
					dishes_db_new["price"].append(data)
				if(count == 2):
					data = data.replace(" ","").lower()
					dishes_db_new["v_n"].append(data)
				if(count == 3):
					data = data.replace(" ","_").lower()
					dishes_db_new["base_ing"].append(data)
				count = count + 1

	dishes_db = pd.DataFrame.from_dict(dishes_db_new, orient='index')
	a_db = dishes_db.transpose()
	dishes_db = a_db
	#print(type(dishes_db))
	xyz = a_db.to_json(orient='index')
	#pprint(xyz)
	with open('dishes15.txt','w') as outfile:
		json.dump(xyz, outfile)

@app.route('/get_logged_msg')
def get_messages():
	fil = open('msg_nt_ndrstd.txt','r')
	fil = fil.readlines()
	return json.dumps(fil)

@app.route('/log_message/<message>')
def logger(message):
	fil = open("msg_nt_ndrstd.txt",'a')
	fil.write(message + "\n")
	return "Success"

@app.route('/addingdish/<d>')
def add_dish(d):
	global dishes_db
	df = pd.read_json(d, orient = 'records')
	for row in df.itertuples():
		row.link.replace("_","/")
	#print(dishes_db)
	dishes_db = dishes_db.append(df,ignore_index=True)
	return json.dumps('Success')

@app.route('/deletingdish/<name>')
def delete_dish(name):
	global dishes_db
	name = json.loads(name)
	for nam in name:
		dishes_db = dishes_db[dishes_db.name != str(nam)]
	return json.dumps('Success')

@app.route('/outofstock/<dname>')
def outstocking(dname):
	global dishes_db
	dname = dname.lower().replace(" ","_")
	if(dishes_db[dishes_db['name']==dname]['stock'].tolist()[0]== 'In'):
		dishes_db.loc[dishes_db['name']==dname,'stock'] = 'Out'
	elif(dishes_db[dishes_db['name']==dname]['stock'].tolist()[0]== 'Out'):
		dishes_db.loc[dishes_db['name']==dname,'stock'] = 'In'
	print dname
	print dishes_db
	return json.dumps('Success')

@app.route('/refreshing')
def refresh_stock():
	global dishes_db
	dishes_db = dishes_db.replace("Out","In")
	print dishes_db
	return json.dumps('Success')



store_the_dishes()
app.install(EnableCors())

app.run(host='0.0.0.0', port=7000, debug=True, server='gevent')

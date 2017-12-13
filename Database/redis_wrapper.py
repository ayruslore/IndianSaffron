from gevent import monkey; monkey.patch_all()
#import pdb; pdb.set_trace()

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
from pprint import pprint
#import logger

import redis_functions as rd
from redis_functions import *
app = bottle.app()



global daily_confirmed_carts
global daily_converted_value
global daily_delivered_carts

global y_converted_carts
global y_converted_value
global r_converted_carts
global r_converted_value
global o_converted_carts
global o_converted_value





daily_converted_value = "daily_converted_value"
daily_confirmed_carts = "daily_confirmed_carts"
daily_delivered_carts = "daily_delivered_carts"
y_converted_value = "y_converted_value"
y_converted_carts = "y_converted_carts"
o_converted_carts = "o_converted_carts"
o_converted_value = "o_converted_value"
r_converted_value = "r_converted_value"
r_converted_carts ="r_converted_carts"

global orders
orders = {}
global orders_branch_R
orders_branch_R={}
global orders_branch_O
orders_branch_O={}
global orders_branch_Y
orders_branch_Y={}
global busy

busy = False
@app.route('/write_order/<d>')
def write_order(d):
	print("writing")
	global orders
	global busy
	print("wriing")
	#d = json.loads(d)
	while busy==True:
		pass
	busy = True
	orders.append(d)
	busy = False
	yield "success"

@app.route('/is_carts/<identity>')
def is_carts(identity):
	key = get_cart_id(identity)
	cart = get_hash(key)
	if(key_exists(key)):
		if(cart!={}):
			yield "True"
		else:
			yield "False"
	else:
		yield "False"

@app.route('/<identity>/set_payment_key/<pass_key>')
def set_payment_key(identity,pass_key):
	key = 'user:'+ str(identity) +':payment_key'
	set_key(key,str(pass_key))

@app.route('/<identity>/get_payment_status')
def get_payment_status(identity):
	key = 'user:'+str(identity)+':payment_key'
	pay_key = get_key(key)
	result = payment(pay_key)
	yield result["status"]

@app.route('/get_cart_price/<id>')
def get_cart_price(id):
	global dishes_db
	key = get_cart_id(id)
	cart = get_hash(key)
	prices = {"oos":[]}
	total = 0
	for item in cart:
		if(dishes_db[dishes_db["name"]==item]["stock"].tolist()[0]=="In"):
			if(int(cart[item])>0):
				#print item
				val =  dishes_db[dishes_db["name"] == item]["price"].tolist()[0]
				prices[item] = (int(val) ,int(cart[item]))
				a,b = prices[item]
				total += a*b
		else:
			delete_hash_field(key,item)
			prices["oos"].append(item)
	prices["total"] = total
	expire_key_in(key,3600)
	key = "user:"+str(id)+":details"
	if(key_exists(key) and hash_field_exists(key,"address") and hash_field_exists(key,"number")):
		prices["flag"] = True
	else:
		prices["flag"] = False
	key = "rest_discount"
	prices["discount"]=prices["total"]*int(get_key(key))/100
	return prices

@app.route('/cart/<identity>/add/<d>')
def change_cart(identity, d):
	print "Enter add"
	d = d.lower()
	data = {"incart":[],"oos":[]}
	d = json.loads(d)
	key = "user:"+ identity +":cart:"+str(int(set_count("user:"+identity+":confirmed_carts"))+1)
	for item in d:
		if(dishes_db[dishes_db["name"]==item]["stock"].tolist()[0]=="In"):
			incr_hash_field_by(key,item,d[item])
			data["incart"].append(item)
		else:
			data["oos"].append(item)
	expire_key_in(key,3600)
	return data

@app.route('/cart/<identity>/cancel')
def cancel(identity):
	key = "user:"+ str(identity) +":cart:"+str(int(set_count("user:"+identity+":confirmed_carts"))+1)
	expire_key_in(key,1)

from geopy import distance , Point
global Hotel_locations
Hotel_locations = {"Vasant_kunj":Point("28.527335 77.151545")}
#Hotel_locations = {"Residency_Road":Point("12.9655 77.5989"),"Old_Airport_Road":Point("12.9603 77.6459"),"Yelahanka":Point("13.1047 77.5844")}

@app.route('/add_new_hotel/<name>/<lat>/<longi>')
def add_new_hotel(name,lat,longi):
    global Hotel_locations
    Hotel_locations[name] = Point(lat+" "+longi)

@app.route('/get_nearest_hotel/<lat>/<longi>')
def get_nearest_hotel(lat,longi):
	result = []
	for locations in Hotel_locations:
			p1 = Point(lat+" "+longi)
			dist = distance.distance(Hotel_locations[locations],p1).kilometers
			result.append((locations,dist))
	for a,b in result:
		if(b<=10):
			return a
	return None

@app.route('/cart/<identity>/show')
def show(identity):
	res = {"oos":[]}
	key = "user:"+ str(identity) +":cart:"+str(int(set_count("user:"+identity+":confirmed_carts"))+1)
	if key_exists(key) == False:
		yield res
	result = get_hash(key)
	for item in result:
		if(int(result[item])<=0):
			delete_hash_field(key,item)
		else:
			if(dishes_db[dishes_db["name"]==item]["stock"].tolist()[0] == "In"):
				res[item] = [dishes_db[dishes_db["name"] == item]["price"].tolist()[0],result[item]]
			else:
				delete_hash_field(key,item)
				res["oos"].append(item)
	expire_key_in(key,3600)
	yield json.dumps(res)

@app.route('/cart/<identity>/replace/<d>')
def replace(identity,d):
	print "Enter"
	key = "user:"+ str(identity) +":cart:"+str(int(set_count("user:"+identity+":confirmed_carts"))+1)
	delete_key(key)
	d=json.loads(d)
	data = {"incart":[],"oos":[]}
	for item in d:
		if(dishes_db[dishes_db["name"]==item]["stock"].tolist()[0]=="In"):
			set_hash_field(key,item,d[item])
			data["incart"].append(item)
		else:
			data["oos"].append(item)
	print "expiring"
	expire_key_in(key,3600)
	print "exit"
	yield json.dumps(data)

def get_details(identity):
	data = {}
	lat_long = get_key("user:"+str(identity)+":cur_address")
	lat_long = lat_long.split(",")
	key = "user:" + str(identity) + ":details"
	data['address'] = get_hash_field(key,"address").replace("_"," ")
	data['number'] = str(get_hash_field(key,"number")) #get_geocode(lat_long[0],lat_long[1])
	total = get_cart_price1(identity)
	data['total'] = total['total']
	data['discount'] = total["discount"]
	data['name'] = get_hash_field(key,"name").replace("_"," ")
	return data


@app.route('/discount/<num>')
def disc(num):
	key = "rest_discount"
	set_key(key,str(num))
	return "Success"

@app.route('/cart/<identity>/confirm')
def confirm10(identity):
	global orders_branch_Y
	global orders_branch_O
	global orders_branch_R
	k="user:"+str(identity)+":assigned_rest"
	closest = get_key(k)

	key = "user:" + identity + ":confirmed_carts"
	member = "user:"+identity+":cart:"+str(int(set_count("user:"+identity+":confirmed_carts"))+1)
	persist_key(member)

	set_add(key,member)
	key = "user:"+str(identity)+":last_cart"
	set_key(key,member)
	order = get_hash(member)

	key = "user:"+str(identity)+":ordered_items"
	for item in order:
		ss_member_increment_by(key,item,"1")
	key = "user:"+str(identity)+":cart_status"
	set_key(key,"pending")

	for item in order:
		ss_member_increment_by(key,item,"1")
	key = "user:"+str(identity)+":history:category"
	for item in order:
		val =  dishes_db[dishes_db["name"] == item]["category"].tolist()[0]
		ss_member_increment_by(key,val,"1")
	key = "user:"+str(identity)+":history:base_ing"
	for item in order:
		val =  dishes_db[dishes_db["name"] == item]["base_ing"].tolist()[0]
		ss_member_increment_by(key,val,"1")
	key = "user:"+str(identity)+":history:v_n"
	for item in order:
		val =  dishes_db[dishes_db["name"] == item]["v_n"].tolist()[0]
		ss_member_increment_by(key,val,"1")
	key = "user:"+str(identity)+":cart_status"
	set_key(key,"pending")
	key = "user:" + str(identity) + ":tic"
	set_key(key,get_time_stamp())

	data = {"id":str(identity),"cart":order,"data":get_details(identity),"status":"pending"}
	print (data)

	if closest in "Residency_Road":
		orders_branch_R[str(identity)] = data

	elif closest in "Yelahanka":
		orders_branch_Y[str(identity)] = data

	elif closest in "Old_Airport_Road":
		orders_branch_O[str(identity)] = data

	global orders

	orders[str(identity)] = data
	#write_order(data)
	print(data)

'''
0 pending
1 accept/reject
2 in_kitchen
3 out_for_delivery
4 delivered
'''

@app.route('/cart/<identity>/accept')
def confirm4(identity):
	key = "user:"+str(identity)+":cart_status"
	set_key(key,"order_accepted")
	if str(identity) in orders_branch_O:
		orders_branch_O[str(identity)]['status'] = 'order_accepted'
	elif str(identity) in orders_branch_Y:
		orders_branch_Y[str(identity)]['status'] = 'order_accepted'
	elif str(identity) in orders_branch_R:
		orders_branch_R[str(identity)]['status'] = 'order_accepted'
	orders[str(identity)]['status'] = 'order_accepted'

@app.route('/cart/<identity>/reject')
def confirm5(identity):
	key = "user:"+str(identity)+":cart_status"
	set_key(key,"rejected")
	if str(identity) in orders_branch_O:
		orders_branch_O[str(identity)]['status'] = 'rejected'
	elif str(identity) in orders_branch_Y:
		orders_branch_Y[str(identity)]['status'] = 'rejected'
	elif str(identity) in orders_branch_R:
		orders_branch_R[str(identity)]['status'] = 'rejected'
	orders[str(identity)]['status'] = 'rejected'
	orders.pop(str(identity),None)
	orders_branch_O.pop(str(identity),None)
	orders_branch_Y.pop(str(identity),None)
	orders_branch_R.pop(str(identity),None)


@app.route('/cart/<identity>/in_kitchen')
def confirm6(identity):
	key = "user:"+str(identity)+":cart_status"
	set_key(key,"in_kitchen")
	if str(identity) in orders_branch_O:
		orders_branch_O[str(identity)]['status'] = 'in_kitchen'
	elif str(identity) in orders_branch_Y:
		orders_branch_Y[str(identity)]['status'] = 'in_kitchen'
	elif str(identity) in orders_branch_R:
		orders_branch_R[str(identity)]['status'] = 'in_kitchen'
	orders[str(identity)]['status'] = 'in_kitchen'


@app.route('/cart/<identity>/out_for_delivery/<contact>')
def confirm7(identity, contact):
	key = "user:"+str(identity)+":cart_status"
	set_key(key,"out_for_delivery")
	key = "user:"+str(identity)+":dboy"
	set_key(key,str(contact))
	key = "delivery_boy:" + str(contact) + ":deliveries"
	set_add(key,str(identity))
	if str(identity) in orders_branch_O:
		orders_branch_O[str(identity)]['status'] = 'out_for_delivery'
	elif str(identity) in orders_branch_Y:
		orders_branch_Y[str(identity)]['status'] = 'out_for_delivery'
	elif str(identity) in orders_branch_R:
		orders_branch_R[str(identity)]['status'] = 'out_for_delivery'
	orders[str(identity)]['status'] = 'out_for_delivery'



@app.route('/get_data_for_delivery/<contact>')
def get_data(contact):
	key = "delivery_boy:" + str(contact) + ":deliveries"
	ids = set_members(key)
	ids = ids.split()
	result = {}
	for identity in ids:
		details = {}
		key = "user:" + str(identity) + ":details"
		name = get_hash_field(key,"name").replace("_"," ")
		key = "user:" + str(identity) + ":last_cart"
		last_cart = get_key(key)
		details["cart"] = get_hash(last_cart)
		cart = {}
		for key in details["cart"].keys():
			cart[key.replace("_"," ")] = details["cart"][key]
		details["cart"] = cart
		key = "user:" + str(identity) + ":cur_address"
		details["address"] = get_key(key)
		result[name] = details
	yield json.dumps(result)

@app.route('/cart/<identity>/delivered')
def confirm8(identity):
	key = "user:"+str(identity)+":cart_status"
	set_key(key,"delivered")
	key = "user:"+str(identity)+":assigned_rest"
	closest = get_key(key)
	key = "user:"+str(identity)+":cart:price"
	total = get_key(key)
	key_increment_by(daily_confirmed_carts,1)
	key_increment_by(daily_converted_value,total)
	if closest in "Residency_Road":
		key_increment_by(r_converted_carts,1)
		key_increment_by(r_converted_value,total)
	elif closest in "Yelahanka":
		key_increment_by(y_converted_carts,1)
		key_increment_by(y_converted_value,total)
	elif closest in "Old_Airport_Road":
		key_increment_by(o_converted_carts,1)
		key_increment_by(o_converted_value,total)
	orders.pop(str(identity),None)
	orders_branch_O.pop(str(identity),None)
	orders_branch_Y.pop(str(identity),None)
	orders_branch_R.pop(str(identity),None)
	if str(identity) in orders_branch_O:
		orders_branch_O[str(identity)]['status'] = 'delivered'
	elif str(identity) in orders_branch_Y:
		orders_branch_Y[str(identity)]['status'] = 'delivered'
	elif str(identity) in orders_branch_R:
		orders_branch_R[str(identity)]['status'] = 'delivered'
	if str(identity) in orders:
		orders[str(identity)]['status'] = 'delivered'


@app.route('/geniidata')
def geniidata():
	result = {}
	result["total_converted_value"] = get_key(total_converted_value)
	result["total_converted_carts"] = get_key(total_converted_carts)
	result["y_converted_value"] = get_key(y_converted_value)
	result["y_converted_carts"] = get_key(y_converted_carts)
	result["r_converted_value"] = get_key(r_converted_value)
	result["r_converted_carts"] = get_key(r_converted_carts)
	result["o_converted_value"] = get_key(o_converted_value)
	result["o_converted_carts"] = get_key(o_converted_carts)
	return result


@app.route('/cart/<identity>/status')
def confirm3(identity):
	key = "user:"+str(identity)+":cart_status"
	result = {}
	if(key_exists(key)):
		result['status'] = get_key(key)
		if(get_key(key)=='out_for_delivery' or get_key(key)=='delivered'):
			key = "user:"+str(identity)+":dboy"
			result['dboy'] = get_key(key)
		yield json.dumps(result)
	else:
		yield "Status not set"

@app.route('/show_old_carts/<identity>')
def old_carts(identity):
	s = set_members("user:" + identity + ":confirmed_carts")
	'''print "Surya"
	s = s.split()
	print s
	result = {}
	for i in s:
		result[i] = get_hash(i)
	yield result'''
	s = s.split()
	result = {}
	command = "redis-cli HGETALL "
	for i in s:
		result[i] = commands.getoutput(command+i)
	yield json.dumps(result)

@app.route('/<identity>/last_cart')
def last_cart(identity):
	key = "user:"+str(identity)+":last_cart"
	last_cart = get_key(key)
	yield json.dumps(get_hash(last_cart))

@app.route('/<identity>/item_history')
def last_cart(identity):
	key = "user:"+str(identity)+":ordered_items"
	yield json.dumps(ss_range(key,"0","-1"))

@app.route('/get_menu')
def get_menu():
	global dishes_db
	return dishes_db.to_json(orient="records")


@app.route('/loading_df/<filename>')
def load_df(filename):
	df = pd.DataFrame()
	i1 = open(filename,'r').read()
	df = pd.read_json(json.loads(i1),orient='index')
	print df
	#yield df

def display():
	global dishes_db
	print dishes_db


@app.route('/add_dish/<d>')
def add_dish(d):
	u = 'http://0.0.0.0:7000/addingdish/'
	h ={ 'content-type': 'application/json; charset=utf-8'}
	r = requests.get(url=u+d,headers=h)
	global dishes_db
	df = pd.read_json(d, orient = 'records')
	for row in df.itertuples():
		row.link.replace("_","/")
	print(df)
	dishes_db = dishes_db.append(df,ignore_index=True)
	#print(dishes_db)
	xyz = dishes_db.to_json(orient='index')
	with open('dishes15.txt','w') as outfile:
		json.dump(xyz, outfile)
	d = json.loads(d)
	url = "https://api.api.ai/v1/entities/2d04d8e5-02c5-4eb5-afaf-037bfb662513/entries?v=20150910"
	Headers={"Authorization": 'Bearer 9afd07100b9a4f27ae0f03eda9e3c752',"Content-Type": 'application/json; charset=utf-8'}
	body=[{"value":d[0]['name'],'synonyms':[d[0]['name']]}]
	r = requests.post(url,headers=Headers,json=body)
	display()
	#print(dishes_db)

@app.route('/delete_dish/<name>')
def delete_dish(name):
	global dishes_db
	u = 'http://0.0.0.0:7000/deletingdish/'
	h ={ 'content-type': 'application/json; charset=utf-8'}
	r = requests.get(url=u+name,headers=h)
	name = json.loads(name)
	for nam in name:
		dishes_db = dishes_db[dishes_db.name != str(nam)]
	xyz = dishes_db.to_json(orient='index')
	with open('dishes15.txt','w') as outfile:
		json.dump(xyz, outfile)
	url = "https://api.api.ai/v1/entities/2d04d8e5-02c5-4eb5-afaf-037bfb662513/entries?v=20150910"
	Headers={"Authorization": 'Bearer 9afd07100b9a4f27ae0f03eda9e3c752',"Content-Type": 'application/json; charset=utf-8'}
	body=[{"value":name}]
	r = requests.delete(url,headers=Headers,json=name)


@app.route('/set_menu')
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
	s = 'http://ec2-35-154-42-243.ap-south-1.compute.amazonaws.com/activebots/indiansaffronco/img/db/'
	dishes_db_new = {"name":[],"v_n":[],"base_ing":[],"course":[],"category":[],"count":[],"price":[],"link":[],"stock":[]}
	for course in temp["Courses"]:
		for dish in temp["Courses"][course]:
			dishes_db_new["course"].append(course)
			if(course == "Shorba"):
				dishes_db_new["category"].append("shorba")
				dishes_db_new["link"].append(s + dish.replace(" ","-").replace("(","").replace(")","").upper() + ".jpg")
			elif(course == "Kebab"):
				dishes_db_new["category"].append("kebab")
				dishes_db_new["link"].append(s + dish.replace(" ","-").replace("(","").replace(")","").upper() + ".jpg")
			elif(course == "Kathi Rolls"):
				dishes_db_new["category"].append("kathi_roll")
				dishes_db_new["link"].append(s + "isc_logo.jpg")
			elif(course == "Curries"):
				dishes_db_new["category"].append("curry")
				dishes_db_new["link"].append(s + dish.replace(" ","-").replace("(","").replace(")","").upper() + ".jpg")
			elif(course == "Dal"):
				dishes_db_new["category"].append("dal")
				dishes_db_new["link"].append(s + dish.replace(" ","-").replace("(","").replace(")","").upper() + ".jpg")
			elif(course == "Rice"):
				dishes_db_new["category"].append("rice")
				dishes_db_new["link"].append(s + dish.replace(" ","-").replace("(","").replace(")","").upper() + ".jpg")
			elif(course == "Roti Parantha"):
				dishes_db_new["category"].append("roti_parantha")
				dishes_db_new["link"].append(s + "isc_logo.jpg")
			elif(course == "Dahi"):
				dishes_db_new["category"].append("dahi")
				dishes_db_new["link"].append(s + dish.replace(" ","-").replace("(","").replace(")","").upper() + ".jpg")
			elif(course == "Dessert"):
				dishes_db_new["category"].append("dessert")
				dishes_db_new["link"].append(s + dish.replace(" ","-").replace("(","").replace(")","").upper() + ".jpg")
			else:
				dishes_db_new["category"].append("HERO")
				dishes_db_new["link"].append(s + dish.replace(" ","-").replace("(","").replace(")","").upper() + ".jpg")
			dishes_db_new["name"].append(dish.replace(" ","_").lower().replace("(","").replace(")",""))
			dishes_db_new["stock"].append("In")

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



@app.route('/cart/<identity>/remove/<d>')
def change_cart(identity, d):
	d = d.lower()
	d = json.loads(d)
	key = "user:"+ identity +":cart:"+str(int(set_count("user:"+identity+":confirmed_carts"))+1)
	for item in d:
		incr_hash_field_by(key,item,d[item])
	cart = get_hash(key)
	for dish in cart:
			if(int(cart[dish]) <= 0):
				delete_hash_field(key,dish)
	cart = get_hash(key)
	if(cart == {}):
		yield "Cart empty"
	else:
		yield "Done"


@app.route('/<identity>/set_contact/<contact>')
def set_contact(identity,contact):
	key = "user:"+str(identity)+":cur_contact"
	set_key(key,str(contact))
	key = "user:"+str(identity)+":contacts"
	ss_member_increment_by(key,str(contact),"1")

@app.route('/<identity>/set_address/<address>')
def set_address(identity,address):
	key = "user:"+str(identity)+":cur_address"
	s = address.split(",")
	q = get_nearest_hotel(s[0],s[1])
	print q
	set_key(key,str(address).replace(" ","_"))
	key = "user:"+str(identity)+":addresses"
	ss_member_increment_by(key,str(address).replace(" ","_"),"1")
	if(q!=None):
		key = "user:"+str(identity)+":assigned_rest"
		set_key(key,q)
		return q
	else:
		set_key(key,"None")
		return "None"

@app.route('/<identity>/set_note/<note>')
def set_contact(identity,note):
	key = "user:"+str(identity)+":cur_note"
	set_key(key,str(note).replace(" ","_"))
	key = "user:"+str(identity)+":notes"
	ss_member_increment_by(key,str(note).replace(" ","_"),"1")

@app.route('/<identity>/get_contact')
def get_contact(identity):
	key = "user:"+str(identity)+":cur_contact"
	yield get_key(key)

@app.route('/<identity>/get_contacts')
def get_contacts(identity):
	key = "user:"+str(identity)+":contacts"
	yield json.dumps(ss_range(key,"0","-1"))

@app.route('/<identity>/get_address')
def get_address(identity):
	key = "user:"+str(identity)+":cur_address"
	yield get_key(key)

@app.route('/<identity>/get_addresses')
def get_addresses(identity):
	key = "user:"+str(identity)+":addresses"
	yield json.dumps(ss_range(key,"0","-1"))

@app.route('/<identity>/get_note')
def get_note(identity):
	key = "user:"+str(identity)+":cur_note"
	yield get_key(key)

@app.route('/<identity>/get_notes')
def get_contacts(identity):
	key = "user:"+str(identity)+":notes"
	yield json.dumps(ss_range(key,"0","-1"))

@app.route('/<pass_key>/get_payment_status_2')
def get_payment_status(pass_key):
	result = payment(str(pass_key))
	yield result["status"]


def get_cart_price1(id):
	global dishes_db
	key = "user:"+ str(id)+":cart:"+str(int(set_count("user:"+str(id)+":confirmed_carts")))
	print(key)
	cart = get_hash(key)
	prices = {}
	prices["cart_id"] = key
	total = 0
	for item in cart:
		if(int(cart[item])>0):
			val =  dishes_db[dishes_db["name"] == item]["price"].tolist()[0]
			prices[item] = (int(val) ,int(cart[item]))
			a,b = prices[item]
			total += a*b
	prices["total"] = total
	key = "user:"+str(id)+":cart:price"
	set_key(key,str(total))
	key = "rest_discount"
	prices["discount"]=prices["total"]*int(get_key(key))/100
	return prices

@app.route('/get_new_receipt/<dic>')
def get_new_reciept(dic):
	data = json.loads(dic)
	identity = data["Id"]
	confirm10(identity)
	lat_long = get_key("user:"+str(identity)+":cur_address")
	lat_long = lat_long.split(",")
	key = "user:" + str(identity) + ":details"
	data.pop("Id",None)
	data["address"] = data["address"].replace(" ","_")
	data['name'] = data["name"].replace(" ","_")
	set_hash(key,data)
	#data['address'] = get_hash_field(key,"address").replace("_"," ")
	#data['number'] = str(get_hash_field(key,"number")) #get_geocode(lat_long[0],lat_long[1])
	total = get_cart_price1(identity)
	data['cart'] = total
	data["address"] = data["address"].replace("_"," ")
	data['name'] = data["name"].replace("_"," ")
	data['discount']
	key = "user:"+str(identity)+":cart_status"
	data['order_status'] = get_key(key)
	yield json.dumps(data)

@app.route('/get_receipt/<identity>')
def get_reciept(identity):
	data = {}
	confirm10(identity)
	lat_long = get_key("user:"+str(identity)+":cur_address")
	lat_long = lat_long.split(",")
	key = "user:" + str(identity) + ":details"
	data['address'] = get_hash_field(key,"address").replace("_"," ")
	data['number'] = str(get_hash_field(key,"number")) #get_geocode(lat_long[0],lat_long[1])
	total = get_cart_price1(identity)
	data['cart'] = total
	data['name'] = get_hash_field(key,"name").replace("_"," ")

	key = "user:"+str(identity)+":cart_status"
	data['order_status'] = get_key(key)
	yield json.dumps(data)


@app.route('/read_orders')
def read_orders():
	global orders
	yield json.dumps(orders)

@app.route('/read_orders_R')
def read_orders_R():
	global orders_branch_R
	yield json.dumps(orders_branch_R)

@app.route('/read_orders_O')
def read_orders_O():
	global orders_branch_O
	yield json.dumps(orders_branch_O)

@app.route('/read_orders_Y')
def read_orders_Y():
	global orders_branch_Y
	yield json.dumps(orders_branch_Y)

@app.route('/<identity>/get_notes')
def get_contacts(identity):
	key = "user:"+str(identity)+":notes"
	yield json.dumps(ss_range(key,"0","-1"))


@app.route('/get_location_total/<identity>')
def location(identity):
	key = "user:" + str(identity) + ":cur_address"
	data = {}
	if(key_exists(key)):
		lat,longi = get_key(key).split(',')
		data["address"] = get_geocode(lat,longi)
	else:
		data["address"] = ''
	data["total"] = get_cart_price(identity)["total"]
	yield json.dumps(data)

def get_geocode_address(address):
	gmaps = googlemaps.Client(key='AIzaSyCGIi0Ts6EavD1FN4Ckx0uR7Ikr1Z1Jwgw')
	geocode_result = gmaps.geocode(address)
	return geocode_result

@app.route('/set_user_default/<identity>/<d>')
def set_user_def(identity,d):
	d = json.loads(d)
	print d
	key = "user:" + str(identity) + ":details"
	set_hash_field(key,"number",str(d["number"]))
	set_hash_field(key,"address",d["address"].replace(" ","_"))
	set_hash_field(key,"name",d["name"])

@app.route('/get_user_default/<identity>')
def get_user_def(identity):
	key = "user:" + str(identity) + ":details"
	key2 = "user:" + str(identity) + ":cur_address"
	result = get_hash(key)
	result["name"] = result["name"].replace("_"," ")
	if(hash_field_exists(key,"number")):
		result["number"] = result["number"].replace("_"," ")
	if(key_exists(key2)):
		latlong = get_key(key2)
		latlong = latlong.split(",")
		result["address"] = get_geocode(latlong[0],latlong[1])
	elif(hash_field_exists(key,"address")):
		result["address"] = result["address"].replace("_"," ")
	yield json.dumps(result)

def get_reciept1(identity):
	data = {}
	confirm10(identity)
	lat_long = get_key("user:"+str(identity)+":cur_address")
	lat_long = lat_long.split(",")
	key = "user:" + str(identity) + ":details"
	data['address'] = get_hash_field(key,"address").replace("_"," ")
	data['number'] = str(get_hash_field(key,"number")) #get_geocode(lat_long[0],lat_long[1])
	total = get_cart_price1(identity)
	data['cart'] = total
	data['name'] = get_hash_field(key,"name").replace("_"," ")
	key = "user:"+str(identity)+":cart_status"
	data['order_status'] = get_key(key)
	return data

@app.route('/bypass_payments/<identity>')
def bypass(identity):
	if (key_exists("user:"+str(identity)+":details")):
		#confirm10(identity)
		yield json.dumps(get_reciept1(identity))
	else:
		yield "No data"

@app.route('/set_confirmation/<identity>/<d>')
def set_confirm(identity,d):
	d = json.loads(d)
	key = "user:" + str(identity) + ":details"
	confirm10(identity)
	set_hash_field(key,"number",str(d["number"]))
	set_hash_field(key,"address",d["address"].replace(" ","_"))
	set_hash_field(key,"name",d["name"].replace(" ","_"))

@app.route('/refresh_stock')
def refresh_stock():
	global dishes_db
	dishes_db = dishes_db.replace("Out","In")
	u = 'http://0.0.0.0:7000/refreshing'
	h ={ 'content-type': 'application/json; charset=utf-8'}
	r = requests.get(url=u,headers=h)
	print dishes_db

@app.route('/outofstock/<dname>')
def outstock(dname):
	dname = dname.lower().replace(" ","_")
	if(dishes_db[dishes_db['name']==dname]['stock'].tolist()[0]== 'In'):
		dishes_db.loc[dishes_db['name']==dname,'stock'] = 'Out'
	elif(dishes_db[dishes_db['name']==dname]['stock'].tolist()[0]== 'Out'):
		dishes_db.loc[dishes_db['name']==dname,'stock'] = 'In'
	u = 'http://0.0.0.0:7000/outofstock/'
	h ={ 'content-type': 'application/json; charset=utf-8'}
	r = requests.get(url=u+dname,headers=h)
	#print dishes_db
	return "Success"

i1 = open('dishes15.txt','r').read()
df = pd.read_json(json.loads(i1),orient='index')
global dishes_db
dishes_db = df
store_the_dishes()
print dishes_db
app.install(EnableCors())
app.run(host='0.0.0.0', port=5000, debug=True,server='gevent')


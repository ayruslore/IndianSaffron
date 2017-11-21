import requests
import json
h ={ 'content-type': 'application/json; charset=utf-8'}
d = {'dname':'kheer'}
d1 = 'kheer'
u = 'http://0.0.0.0:5000/outofstock/'
r = requests.get(url=u+d1,headers=h)
#print r.status_code
#print r.json()

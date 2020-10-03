from flask import Flask, request, jsonify
from pymongo import MongoClient
from config import app_config, app_active

config = app_config[app_active]


def create_app(config_name):
    app = Flask(__name__)

    app.config.from_object(app_config[app_active])
    app.config.from_pyfile('config.py')

    client = MongoClient()
    db = client.prova

    @app.route('/')
    def index():
        return 'Home.'

    #users

    @app.route('/users', methods=['GET', 'POST'])
    def users():
        if request.method == 'POST':
            body = request.get_json()
            if db.users.find_one() == None:
                userid = 1
            else:
                userid = 0
                for user in db.users.find():
                    if user['_id'] > userid:
                        userid = user['_id']
                userid += 1
            db.users.insert_one({'_id':userid,'name':body['name'],'country':body['country'],'active':True})
            return db.users.find_one({'_id':userid}), 200
        elif request.method == 'GET':
            users = []
            searchword = request.args.get('active', '')
            if searchword == "false":
                for user in db.users.find({"active":False}):
                    users.append(user)
            else:
                for user in db.users.find({"active":True}):
                    users.append(user)
            return jsonify(users), 200

    def objExist(collection, objid):
        if collection.find_one({'_id': objid}) != None:
            return True
        return False

    def userActive(userid):
        user = db.users.find_one({'_id':userid})
        if user['active'] == True:
            return True
        return False

    @app.route('/users/<int:userid>', methods=['GET', 'PUT', 'DELETE'])
    def userbyid(userid):
        if objExist(db.users, userid):
            if request.method == 'GET':
                    return db.users.find_one({'_id':userid}), 200
            elif userActive(userid):
                if request.method == 'PUT':
                    body = request.get_json()
                    myquery = { "_id": userid}
                    newvalues = { "$set": { "country": body['country']} }
                    db.users.update_one(myquery, newvalues)
                    return db.users.find_one({'_id':userid}), 200
                elif request.method == 'DELETE':
                    myquery = { "_id": userid}
                    newvalues = { "$set": { "active": False}}
                    db.users.update_one(myquery, newvalues)
                    return db.users.find_one({'_id':userid}), 200
            else:
                return {'error':'user is not active'}, 409
        else:
            return {'error':'user does not exist'}, 404
        
    #orders

    @app.route('/orders', methods=['GET', 'POST'])
    def orders():
        if request.method == 'POST':
            body = request.get_json()
            if db.orders.find_one() == None:
                orderid = 1
            else:
                orderid = 0
                for order in db.orders.find():
                    if order['_id'] > orderid:
                        orderid = order['_id']
                orderid += 1
            if objExist(db.users, body['user']):
                if userActive(body['user']):
                    db.orders.insert_one({'_id': orderid, 'state':'unpaid', 'user':body['user'], 'price':body['price']})
                    return db.orders.find_one({'_id':orderid}), 200
                else:
                    return {'error':'order not made','reason':'user is not active'}, 409
            else:
                return {'error':'order not made','reason':'user does not exist'}, 409
        elif request.method == 'GET':
            orders = []
            userid = request.args.get('user', '')
            if userid == '':
                for order in db.orders.find():
                    orders.append(order)
            else:
                for order in db.orders.find({"user": int(userid)}):
                    orders.append(order)
            return jsonify(orders), 200

    @app.route('/orders/<int:orderid>', methods=['GET', 'PUT'])
    def orderbyid(orderid):
        if objExist(db.orders, orderid):
            if request.method == 'GET':
                return db.orders.find_one({'_id': orderid}), 200
            elif request.method == 'PUT':
                body = request.get_json()
                myquery = {"_id":orderid}
                newvalues = {"$set":{ "state": body['state']}}
                db.orders.update_one(myquery, newvalues)
                return db.orders.find_one({'_id':orderid}), 200
        else:
            return {'error':'order does not exist'}, 404

    #reports

    @app.route('/reports/orders-by-country')
    def ordersbycountry():
        country = request.args.get('country', '')
        pipeline = [
            {  
                '$lookup': {
                    'from' : 'users',
                    'localField' : 'user',
                    'foreignField' : '_id',
                    'as':'userobj'
                }
            },
            {
                '$replaceRoot': { 'newRoot': { '$mergeObjects': [ { '$mergeObjects': [ {'country': 0, 'name': 0} , { '$arrayElemAt': [ "$userobj", 0 ] } ] }, "$$ROOT" ] } }
            },
            {
                '$project': { 'userobj': 0 }
            }]
        if country == '':
            body = {'BR':[],'UK':[],'US':[]}         
            for order in db.orders.aggregate(pipeline):
                body[order['country']].append({'_id':order['_id'],'state':order['state'],'name':order['name'],'price':order['price']})
        else:
            body = {country:[]}
            for order in db.orders.aggregate(pipeline):
                if country == order['country']:
                    body[country].append({'_id':order['_id'],'state':order['state'],'name':order['name'],'price':order['price']})
        return body, 200

    @app.route('/reports/payments-by-country')
    def paymentsbycountry():
        pipeline = [
            {  
                '$lookup': {
                    'from' : 'users',
                    'localField' : 'user',
                    'foreignField' : '_id',
                    'as':'userobj'
                }
            },
            {
                '$replaceRoot': { 'newRoot': { '$mergeObjects': [ { '$mergeObjects': [ {'country': 0, 'name': 0} , { '$arrayElemAt': [ "$userobj", 0 ] } ] }, "$$ROOT" ] } }
            },
            {
                '$project': { 'userobj': 0 }
            }]
        body = {'BR':[{'paid':0.0,'unpaid':0.0}],'UK':[{'paid':0.0,'unpaid':0.0}],'US':[{'paid':0.0,'unpaid':0.0}]} 
        for order in db.orders.aggregate(pipeline):
            body[order['country']][0][order['state']] += order['price']
        return body, 200

    return app
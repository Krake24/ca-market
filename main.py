import json
import requests
import pickle
import atexit
from functools import wraps
from flask import request, abort, Flask

with open ("db.pkl", "rb") as file:
    db = pickle.load(file)

def exit_handler():
    with open ("db.pkl", "wb") as file:
        pickle.dump(db, file)


atexit.register(exit_handler)

if 'offers' not in db:
    db['offers'] = []

if 'needs' not in db:
    db['needs'] = []

f = open("pets.json", "r")
all_pets = json.loads(f.read())

def convertOfferKeysFromDb(old):
    return {
        "pet_id": old['pet_id'],
        "user": old['user'],
        "user_id": old['user_id'],
        "family": old['Family'],
        "house_banner": old['House Banner'],
        "favorite_family": old['Favorite Family'],
        "personality": old['Personality'],
        "favorite_toy": old['Favorite Toy'],
        "favorite_food": old['Favorite Food']
    }

def convertOfferKeysFromCollection(old, user, user_id):
    return {
        "pet_id": old['id'],
        "user": user,
        "user_id": user_id,
        "family": old['Family'],
        "house_banner": old['House Banner'],
        "favorite_family": old['Favorite Family'],
        "personality": old['Personality'],
        "favorite_toy": old['Favorite Toy'],
        "favorite_food": old['Favorite Food']
    }


def convertNeedKeys(old):
    return {
        "user": old['user'],
        "user_id": old['user_id'],
        "family": old['Family'],
        "house_banner": old['House Banner'],
        "favorite_family": old['Favorite Family']
    }


def read_user(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        state = request.headers.get('state')
        if not state:
            abort(400, "no state given")
        try:
          user_info = requests.get("https://static.164.158.34.188.clients.your-server.de/3dbot/me?state=" + state).json()
        except:
            abort(401, "Unauthorized")
        if not user_info:
            abort(401, "Unauthorized")
        user = user_info['username'] + '#' + user_info['discriminator']
        return view_function(user_id = user_info['id'], user=user, *args, **kwargs)

    return decorated_function

app = Flask(__name__)

@app.route('/petmarket/offers')
def get_offers():
    result = []
    for offer in db['offers']:
        result.append(convertOfferKeysFromDb(dict(offer)))
    return json.dumps(result, ensure_ascii=False).encode('utf8')


@app.route('/petmarket/offers/<id>', methods=['POST', 'DELETE'])
@read_user
def post_offer(id, user_id, user):
    print(request.method + " offer " + str(id))
  
    if request.method == 'POST':
        result = offer_pet(int(user_id), user, int(id))
    elif request.method == 'DELETE':
        result = remove_pet_offer(int(user_id), int(id))
    return json.dumps(result, ensure_ascii=False).encode('utf8')

@app.route('/petmarket/needs', methods=['GET'])
def get_needs():
    result = []
    for need in db['needs']:
        result.append(convertNeedKeys(dict(need)))
    return json.dumps(result, ensure_ascii=False).encode('utf8')


@app.route('/petmarket/needs', methods=['POST', 'DELETE'])
@read_user
def post_needs(user_id, user):
    print(request.method + " need " + str(id))
    need = json.loads(request.data.decode('utf-8'))
    family = need['family']
    house_banner = need['house_banner']
    favorite_family = need['favorite_family']
    
    if request.method == 'POST':
        result = need_pet(user_id, user, family, house_banner, favorite_family)        
    elif request.method == 'DELETE':
        result = remove_pet_need(user_id, family, house_banner, favorite_family)
    return json.dumps(result, ensure_ascii=False).encode('utf8')


@app.after_request
def apply_caching(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "*")
    response.headers.add("Access-Control-Allow-Methods", "*")
    return response


def map_to_offer(id, user, user_id, pet):
    offer = {}
    offer['pet_id'] = id
    offer['user'] = user
    offer['user_id'] = user_id

    family = pet['Family']
    house_banner = pet['House Banner']
    favorite_family = pet['Favorite Family']
    offer['Family'] = family
    offer['House Banner'] = house_banner
    offer['Favorite Family'] = favorite_family
    offer['Personality'] = pet['Personality']
    offer['Favorite Toy'] = pet['Favorite Toy']
    offer['Favorite Food'] = pet['Favorite Food']
    return offer

def offer_pet(user_id, user, id):
    result = {}
    if next(filter(lambda d: str(d['pet_id']) == str(id), db['offers']), False):
        raise Exception("Error: Pet with ID " + str(id) + " is already listed")

    pet = next(filter(lambda p: str(p['id']) == str(id), all_pets))

    offer = map_to_offer(id, user, user_id, pet)

    db['offers'].append(offer)
    

    search_results = db['needs']
    search_results = list(
        filter(lambda s: s['user_id'] != user_id, search_results))
    
    family = pet['Family']
    house_banner = pet['House Banner']
    favorite_family = pet['Favorite Family']
    search_results = list(
        filter(lambda s: s['Family'] == family or s['Family'] == 'Any',
               search_results))

    search_results = list(
        filter(
            lambda s: s['House Banner'] == house_banner or s['House Banner'] ==
            'Any', search_results))

    search_results = list(
        filter(
            lambda s: s['Favorite Family'] == favorite_family or s[
                'Favorite Family'] == 'Any', search_results))

    distinct_users = set()
    for result in search_results:
        distinct_users.add(result['user'])

    message = "Pet with ID " + str(id) + " registered."
    if distinct_users:
        message = "\nThese users have a fitting need registered:\n"
        for user in distinct_users:
            message += user + "\n"
    result['message'] = message
    result['offer'] = convertOfferKeysFromCollection(pet, user, user_id)
    return result

def remove_pet_offer(user_id, pet_id):
    result = {}
    offer = next(filter(lambda d: d['pet_id'] == pet_id, db['offers']), False)
    if not offer:
        raise Exception("Error: Pet with ID " + str(pet_id) + " is not listed")
    if not user_id == offer['user_id']:
        raise Exception("Error: Pet with ID " + str(
            pet_id) + " was listed by " + offer['user'] + ". You can't remove it.")
    db['offers'].remove(offer)
    
    result['message'] = "Pet with ID " + str(pet_id) + " has been removed"
    result['offer'] = convertOfferKeysFromDb(dict(offer))
    return result


def search_pet(user_id, family, house_banner, favorite_family):

    search_results = db['offers']

    ## Search matching offers from others only
    search_results = list(
        filter(lambda s: s['user_id'] != user_id, search_results))

    if family != 'Any':
        search_results = list(
            filter(lambda s: s['Family'] == family, search_results))

    if house_banner != 'Any':
        search_results = list(
            filter(lambda s: s['House Banner'] == house_banner,
                   search_results))

    if favorite_family != 'Any':
        search_results = list(
            filter(lambda s: s['Favorite Family'] == favorite_family,
                   search_results))

    if len(search_results) == 0:
        return "No matching pets found"

    if len(search_results) > 30:
        return "More than 30 pets found."
    result = ""
    for pet in search_results:
        result += str(
            pet['pet_id']
        ) + " " + pet['House Banner'][0] + pet['Favorite Family'] + " " + pet[
            'Family'] + " (" + pet['user'] + ")\n"
    return result


def need_pet(user_id, user, family, house_banner, favorite_family):
    result = {}
    search_results = db['needs']
    search_results = list(
        filter(lambda s: s['user_id'] == user_id, search_results))

    search_results = list(
        filter(lambda s: s['Family'] == family, search_results))

    search_results = list(
        filter(lambda s: s['House Banner'] == house_banner, search_results))

    search_results = list(
        filter(lambda s: s['Favorite Family'] == favorite_family,
               search_results))

    if len(search_results) > 0:
        result['message'] =  "Such a need is already registered"
        return result

    need = {}
    need['user'] = user
    need['user_id'] = user_id

    need['Family'] = family
    need['House Banner'] = house_banner
    need['Favorite Family'] = favorite_family

    db['needs'].append(need)
    
    search_result = search_pet(user_id, family, house_banner,                              favorite_family)
    result['need'] = convertNeedKeys(need)
    result['message'] = "Need registered\n" + search_result
    return result


def remove_pet_need(user_id, family, house_banner, favorite_family):
    search_results = db['needs']

    search_results = list(
        filter(lambda s: s['user_id'] == user_id, search_results))

    search_results = list(
        filter(lambda s: s['Family'] == family, search_results))

    search_results = list(
        filter(lambda s: s['House Banner'] == house_banner, search_results))

    search_results = list(
        filter(lambda s: s['Favorite Family'] == favorite_family,
               search_results))

    if len(search_results) == 0:
        return "No such need found"

    result = ""
    for need in search_results:
        db['needs'].remove(need)
        
        result += "Need for " + need['House Banner'] + " " + need[
            'Favorite Family'] + " " + need['Family'] + " (" + need[
                'user'] + ") removed\n"
    return result

app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)

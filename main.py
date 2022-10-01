import os
import json
import disnake
import threading
from disnake.ext import commands
from replit import db
from functools import wraps
from flask import request, abort, Flask
import requests

bot = commands.Bot(command_prefix=commands.when_mentioned)

osAssetUrl = "https://opensea.io/assets/0x753f10598c026e73182ca74ed33de05974b9f083/"
caArtUrl = "https://www.champions.io/pets/nfts/art/"
website = "https://prime-utils.web.app/"

f = open("collection.json", "r")
all_pets = json.loads(f.read())


def convertOfferKeysFromDb(old):
    return {
        some change
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


app = Flask(__name__)


def read_user(view_function):
    @wraps(view_function)
    async def decorated_function(*args, **kwargs):
        state = request.headers.get('state')
        if not state:
            abort(400, "no state given")
        try:
          user_info = requests.get("https://discord-auth.krake24.repl.co/me?state=" + state).json()
        except:
            abort(401, "Unauthorized")
        if not user_info:
            abort(401, "Unauthorized")
        user = user_info['username'] + '#' + user_info['discriminator']
        return await view_function(user_id = user_info['id'], user=user, *args, **kwargs)

    return decorated_function


@app.route('/')
async def main():
    return 'alive'


@app.route('/offers')
async def get_offers():
    result = []
    for offer in db['offers']:
        result.append(convertOfferKeysFromDb(dict(offer)))
    return json.dumps(result, ensure_ascii=False).encode('utf8')


@app.route('/offers/<id>', methods=['POST', 'DELETE'])
@read_user
async def post_offer(id, user_id, user):
    print(request.method + " offer " + str(id))
  
    if request.method == 'POST':
        result = await offer_pet(int(user_id), user, int(id))
    elif request.method == 'DELETE':
        result = await remove_pet_offer(int(user_id), int(id))
    return json.dumps(result, ensure_ascii=False).encode('utf8')

@app.route('/needs', methods=['GET'])
async def get_needs():
    result = []
    for need in db['needs']:
        result.append(convertNeedKeys(dict(need)))
    return json.dumps(result, ensure_ascii=False).encode('utf8')


@app.route('/needs', methods=['POST', 'DELETE'])
@read_user
async def post_needs(user_id, user):
    print(request.method + " need " + str(id))
    need = json.loads(request.data.decode('utf-8'))
    family = need['family']
    house_banner = need['house_banner']
    favorite_family = need['favorite_family']
    
    if request.method == 'POST':
        result = await need_pet(user_id, user, family, house_banner, favorite_family)        
    elif request.method == 'DELETE':
        result = await remove_pet_need(user_id, family, house_banner, favorite_family)
    return json.dumps(result, ensure_ascii=False).encode('utf8')


@app.after_request
def apply_caching(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "*")
    response.headers.add("Access-Control-Allow-Methods", "*")
    return response

if 'offers' not in db:
    db['offers'] = []

if 'needs' not in db:
    db['needs'] = []


@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))


@bot.slash_command()
async def pet(inter):
    pass


@pet.sub_command(description="Prints Website URL", name="website")
async def get_website(inter):
    await inter.response.send_message(website)


@pet.sub_command(description="Registered a pet as being offered for trade")
async def offer(inter, id: commands.Range[1, 22238]):

    user_id = inter.user.id
    user = str(inter.user)

    try:
        result = await offer_pet(user_id, user, id)
        await inter.response.send_message(result['message'])
    except Exception as e:
        return await inter.response.send_message(str(e))

async def map_to_offer(id, user, user_id, pet):
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

async def offer_pet(user_id, user, id):
    result = {}
    if next(filter(lambda d: d['pet_id'] == id, db['offers']), False):
        raise Exception("Error: Pet with ID " + str(id) + " is already listed")

    pet = next(filter(lambda p: p['id'] == id, all_pets))

    offer = await map_to_offer(id, user, user_id, pet)

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


@pet.sub_command_group()
async def remove(inter):
    pass


@remove.sub_command(description="Remove listed pet", name="offer")
async def remove_offer(inter, id: commands.Range[1, 22238]):
    result = await remove_pet_offer(inter.user.id, id)
    return await inter.response.send_message(result['message'])


async def remove_pet_offer(user_id, pet_id):
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


Family = commands.option_enum(
    ["Any", "Xiva", "Geckoid", "Cramster", "Sumonot", "Papiro"])
Favorite_Family = commands.option_enum([
    "Any", "Aos", "Darulk", "Fenrir", "Gatekeeper", "Grondal", "Il’gra",
    "Karkadon", "Keymaster", "Saadari", "Seris", "Vitra", "Whisperer"
])
House_Banner = commands.option_enum([
    "Any",
    "⛰️  Earth",
    "🔮  Arcane",
    "💀  Death",
    "🌪️  Air",
    "🌊   Water",
    "🔥  Fire",
    "🌱   Life",
])


@pet.sub_command(description="Search all offered Pets excluding your own")
async def search(inter, family: Family, house_banner: House_Banner,
                 favorite_family: Favorite_Family):

    await inter.response.send_message(await search_pet(inter.user.id, family,
                                                       house_banner,
                                                       favorite_family))


async def search_pet(user_id, family, house_banner, favorite_family):

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


@pet.sub_command(description="Register a need for a certain pet Type")
async def need(inter, family: Family, house_banner: House_Banner,
               favorite_family: Favorite_Family):

    user_id = inter.user.id 
    user = str(inter.user)
                 
    result = await need_pet(user_id, user, family, house_banner, favorite_family)
    await inter.response.send_message(result['message'])

async def need_pet(user_id, user, family, house_banner, favorite_family):
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
    search_result = await search_pet(user_id, family, house_banner,                              favorite_family)
    result['need'] = convertNeedKeys(need)
    result['message'] = "Need registered\n" + search_result
    return result


@remove.sub_command(description="Remove listed pet", name="need")
async def remove_need(inter, family: Family, house_banner: House_Banner,
                      favorite_family: Favorite_Family):

    user_id = inter.user.id                    
                        
    result = await remove_pet_need(user_id, family, house_banner, favorite_family)
    await inter.response.send_message(result)

async def remove_pet_need(user_id, family, house_banner, favorite_family):
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


@pet.sub_command(description="Show values of pet with given ID")
async def show(inter, id: commands.Range[1, 22238]):
    pet = next(filter(lambda p: p['id'] == id, all_pets))
    embed = disnake.Embed(title="Pet #" + str(id),
                          url=osAssetUrl + str(id),
                          colour=0x710193)
    embed.set_image(url=caArtUrl + str(id) + "/pfp.png")
    embed.add_field(name="Family", value=pet['Family'], inline=True)
    embed.add_field(name="House Banner",
                    value=pet['House Banner'],
                    inline=True)
    embed.add_field(name="Favorite Family",
                    value=pet['Favorite Family'],
                    inline=True)
    embed.add_field(name="Personality", value=pet["Personality"], inline=True)
    embed.add_field(name="Favorite Toy",
                    value=pet['Favorite Toy'],
                    inline=True)
    embed.add_field(name="Favorite Food",
                    value=pet['Favorite Food'],
                    inline=True)
    embed.add_field(name="Wallpaper",
                    value="[PFP](" + caArtUrl + str(id) + "/pfp.png)",
                    inline=True)
    embed.add_field(name="Video",
                    value="[Video](" + caArtUrl + str(id) + "/nft.mp4)",
                    inline=True)
    await inter.response.send_message(embed=embed)


if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(
        host='0.0.0.0', port=5000, debug=True, use_reloader=False)).start()
try:
    bot.run(os.environ['botToken'])
except disnake.errors.HTTPException as e:
    print(e.response)
    print(e)

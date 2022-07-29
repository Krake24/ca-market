import os
import json
from disnake.ext import commands
from replit import db

bot = commands.Bot(command_prefix=commands.when_mentioned)

f = open("collection.json", "r")
all_pets = json.loads(f.read())

if 'offers' not in db:
    db['offers'] = []


@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))


@bot.slash_command()
async def pet(inter):
    pass


@pet.sub_command(description="Registered a pet as being offered for trade")
async def offer(inter, id: commands.Range[1, 22238]):
    myfilter = filter(lambda d: d['pet_id'] == id, db['offers'])
    if next(myfilter, False):
        return await inter.response.send_message("Error: Pet with ID " +
                                                 str(id) +
                                                 " is already registered")

    pet = next(filter(lambda p: p['id'] == id, all_pets))

    offer = {}
    offer['pet_id'] = id
    offer['user'] = str(inter.user)
    offer['user_id'] = inter.user.id

    offer['Family'] = pet['Family']
    offer['House Banner'] = pet['House Banner']
    offer['Favorite Family'] = pet['Favorite Family']
    offer['Personality'] = pet['Personality']
    offer['Favorite Toy'] = pet['Favorite Toy']
    offer['Favorite Food'] = pet['Favorite Food']

    db['offers'].append(offer)
    await inter.response.send_message("Pet with ID " + str(id) + " registered")


Family = commands.option_enum(
    ["Any", "Xiva", "Geckoid", "Cramster", "Sumonot", "Papiro"])
Favorite_Family = commands.option_enum([
    "Any", "Il’gra", "Karkadon", "Gatekeeper", "Saadari", "Seris", "Darulk",
    "Grondal", "Fenrir", "Keymaster", "Vitra", "Whisperer", "Aos"
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


@pet.sub_command(description="Search all offered Pets")
async def search(inter, family: Family, house_banner: House_Banner,
                 favorite_family: Favorite_Family):
    search_results = db['offers']
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
        return await inter.response.send_message("No pets found")

    if len(search_results) > 30:
        return await inter.response.send_message(
            "More than 30 hits. Please narrow your search.")
    result = ""
    for pet in search_results:
        result += pet['user'] + "offers pet id: " + str(pet['pet_id']) + "\n"
    await inter.response.send_message(result)


bot.run(os.environ['botToken'])

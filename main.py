import os
import json
import disnake
import threading
from disnake.ext import commands
from replit import db
from flask import Flask

app = Flask(__name__)


@app.route('/')
def main():
    return 'alive'


bot = commands.Bot(command_prefix=commands.when_mentioned)

osAssetUrl = "https://opensea.io/assets/0x753f10598c026e73182ca74ed33de05974b9f083/"
caArtUrl = "https://www.champions.io/pets/nfts/art/"

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
    if next(filter(lambda d: d['pet_id'] == id, db['offers']), False):
        return await inter.response.send_message("Error: Pet with ID " +
                                                 str(id) +
                                                 " is already listed")

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


@pet.sub_command(description="Remove listed pet")
async def remove(inter, id: commands.Range[1, 22238]):
    pet = next(filter(lambda d: d['pet_id'] == id, db['offers']), False)
    if not pet:
        return await inter.response.send_message("Error: Pet with ID " +
                                                 str(id) + " is not listed")
    if not inter.user_id == pet['user_id']:
        return await inter.response.send_message("Error: Pet with ID " +
                                                 str(id) + " was listed by " +
                                                 pet['user'] +
                                                 ". You can't remove it.")
    db['offers'].remove(pet)
    return await inter.response.send_message("Pet with ID " + str(id) +
                                             " has been removed")


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
        result += pet['user'] + " offers pet id: " + str(pet['pet_id']) + "\n"
    await inter.response.send_message(result)


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
bot.run(os.environ['botToken'])

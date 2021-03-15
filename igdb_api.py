from igdb.wrapper import IGDBWrapper
import shutil
import time
import requests
import json
import os

slugs_list = [line.rstrip('\n') for line in open('slugs.txt')]

## Requests for IGDB, don't post this to github 
## TODO: remove tokens to file
r = requests.post("https://id.twitch.tv/oauth2/token?client_id="+os.environ('CLIENT_ID')+"&client_secret="+os.environ('CLIENT_SECRET')+"&grant_type=client_credentials")
access_token = json.loads(r._content)['access_token']
wrapper = IGDBWrapper(os.environ('CLIENT_SECRET'), access_token)

#Setting Variables
game_ids = {}
system_ids_dict = {}
system_ids = []

#Get Game information to be used for later parsing
print("Getting game information.")
for i in slugs_list:
    byte_array = wrapper.api_request(
                'games',
                'fields id, cover, platforms, name; offset 0; where slug="'+i+'";'
                )
   
    info = json.loads(byte_array)

    if not info:
        print(i +" cannot be found")
    else:
        game_ids[int(info[0]['id'])] = {}

        game_ids[int(info[0]['id'])]['name'] = info[0]['name']
        game_ids[int(info[0]['id'])]['slug'] = i

        game_ids[int(info[0]['id'])]['cover_id'] = ""
        if 'cover' in info[0]:
            game_ids[int(info[0]['id'])]['cover_id'] = info[0]['cover']
        
        game_ids[int(info[0]['id'])]['platform_ids'] = ""
        if 'platforms' in info[0]:
            game_ids[int(info[0]['id'])]['platform_ids'] = info[0]['platforms']
            for system_id in info[0]['platforms']:
                if system_id not in system_ids:
                    system_ids.append(system_id)
    
    time.sleep(10)


print("Get game cover information.")
#Lets get the url information for the covers
for i in game_ids:
    if game_ids[i]['cover_id'] != "":
        byte_array = wrapper.api_request(
                    'covers',
                    'fields id, url, image_id; offset 0; where id='+str(game_ids[i]['cover_id'])+';'
                    )
        print("Game cover for: "+ str(game_ids[i]['name']))
        info = json.loads(byte_array)
        game_ids[i]['cover_url'] = info[0]['url']
        game_ids[i]['image_id'] = info[0]['image_id']

        time.sleep(10)

    
#Get all three image sizes
#t_thumb
#t_cover_small
#t_cover_big


file_names = ['t_cover_small', 't_cover_big', 't_thumb']

print("Saving images")
for i in game_ids:
    if 'image_id' in game_ids[i]:
        for f in file_names:
            r = requests.get("https://images.igdb.com/igdb/image/upload/"+ f + "/" +game_ids[i]['image_id'] + ".jpg", stream = True)

            if r.status_code == 200:
                r.raw.decode_content = True

                filename = f + "_" + game_ids[i]['slug'] + '.jpg'
                # Open a local file with wb ( write binary ) permission.
                with open(filename,'wb') as f:
                    shutil.copyfileobj(r.raw, f)
                
                print('Image successfully Downloaded: ',filename)
            else:
                print('Image Couldn\'t be retrieved')

        time.sleep(10)

def get_systems():
    #Get the System Information for each ID
    for i in system_ids:
        byte_array = wrapper.api_request(
            'platforms',
            'fields id, name; offset 0; where id='+str(i)+';'
            )
        info = json.loads(byte_array)

        system_ids_dict[i] = info[0]['name']

        time.sleep(10)


    #Print system ids dictionary to file
    #TODO: Eventually just read this file to get dictionary versus querying IGDB

    print("Dumping System Dictionary to File")
    json = json.dumps(system_ids_dict)
    f = open("system_dict.json", "w")
    f.write(json)
    f.close()

    #Get System Ids -> System Names
    for i in game_ids:
        game_ids[i]['platform_names'] = []
        for x in game_ids[i]['platform_ids']:
            game_ids[i]['platform_names'].append(system_ids_dict[x])



    #Print these to file
    print("Dumping Game:System pairings to File")
    f = open("game_sys.txt", "a")
    for i in game_ids:
        val =  ",".join(game_ids[i]['platform_names'])
        f.write(game_ids[i]['name']+" : "+ val + "\n")
    f.close()

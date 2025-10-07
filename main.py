import requests
import time

print(
    '''
 (                                                                     
 )\\ )                   (        (   (                              )  
(()/( (            (    )\\ )     )\\  )\\            (  (      )   ( /(  
 /(_)))\\ (   (  (  )(  (()/(   (((_)((_)(   (     ))\\ )(    /((  )(_)) 
(_))_((_))\\  )\\ )\\(()\\  ((_))  )\\___ _  )\\  )\\ ) /((_|()\\  (_))\\((_)   
 |   \\(_|(_)((_|(_)((_) _| |  ((/ __| |((_)_(_/((_))  ((_) _)((_)_  )  
 | |) | (_-< _/ _ \\ '_/ _` |   | (__| / _ \\ ' \\)) -_)| '_| \\ V / / /   
 |___/|_/__|__\\___/_| \\__,_|    \\___|_\\___/_||_|\\___||_|    \\_/ /___|  
                                                                                                                                                                                              
    '''
)

USER_TOKEN = input(
    f'Enter your token to proceed\n >'
)
SOURCE_GUILD_ID = input(
    f'Enter the ID of the server you wish to replicate\n >'
)
NEW_GUILD_ID = input(
    f'Enter the ID of the destination server to paste the copied server\n>'
)

BASE_URL = "https://discord.com/api/v10"
HEADERS = {
    "Authorization": USER_TOKEN,
    "Content-Type": "application/json"
}

def request_with_retry(method, url, **kwargs):
    while True:
        response = requests.request(method, url, headers=HEADERS, **kwargs)
        if response.status_code == 429:
            retry_after = response.json().get("retry_after", 1)
            print(f"Rate limited. Retrying after {retry_after} seconds...")
            time.sleep(retry_after)
            continue
        response.raise_for_status()
        return response.json()

def get_guild_roles(guild_id):
    url = f"{BASE_URL}/guilds/{guild_id}/roles"
    return request_with_retry("GET", url)

def get_guild_channels(guild_id):
    url = f"{BASE_URL}/guilds/{guild_id}/channels"
    return request_with_retry("GET", url)

def create_role(guild_id, role_data):
    url = f"{BASE_URL}/guilds/{guild_id}/roles"
    payload = {
        "name": role_data["name"],
        "permissions": role_data["permissions"],
        "color": role_data["color"],
        "hoist": role_data["hoist"],
        "mentionable": role_data["mentionable"],
        "unicode_emoji": role_data.get("unicode_emoji"),
        "icon": role_data.get("icon")
    }
    return request_with_retry("POST", url, json=payload)

def create_channel(guild_id, channel_data, parent_id=None):
    url = f"{BASE_URL}/guilds/{guild_id}/channels"
    payload = {
        "name": channel_data["name"],
        "type": channel_data["type"],
        "topic": channel_data.get("topic"),
        "bitrate": channel_data.get("bitrate"),
        "user_limit": channel_data.get("user_limit"),
        "parent_id": parent_id,
        "permission_overwrites": channel_data.get("permission_overwrites", [])
    }
    return request_with_retry("POST", url, json=payload)

def remap_permission_overwrites(overwrites, role_id_map, old_guild_id, new_guild_id):
    new_overwrites = []
    for ow in overwrites:
        new_ow = ow.copy()
        if ow["type"] == 0:
            if ow["id"] == old_guild_id:
                new_ow["id"] = new_guild_id
            elif ow["id"] in role_id_map:
                new_ow["id"] = role_id_map[ow["id"]]
            else:
                pass
        new_overwrites.append(new_ow)
    return new_overwrites

def main():
    print("Fetching roles and channels from source guild...")
    roles = get_guild_roles(SOURCE_GUILD_ID)
    channels = get_guild_channels(SOURCE_GUILD_ID)

    print(f"Using existing guild ID {NEW_GUILD_ID} for cloning")
    print("Creating roles...")
    role_id_map = {}
    for role in roles:
        if role["id"] == SOURCE_GUILD_ID:
            continue
        new_role = create_role(NEW_GUILD_ID, role)
        role_id_map[role["id"]] = new_role["id"]
        print(f"Created role: {new_role['name']}")

    print("Creating channels...")
    category_id_map = {}
    for channel in channels:
        if channel["type"] == 4:
            overwrites = remap_permission_overwrites(
                channel.get("permission_overwrites", []),
                role_id_map,
                SOURCE_GUILD_ID,
                NEW_GUILD_ID
            )
            channel["permission_overwrites"] = overwrites
            new_category = create_channel(NEW_GUILD_ID, channel)
            category_id_map[channel["id"]] = new_category["id"]
            print(f"Created category: {new_category['name']}")

    for channel in channels:
        if channel["type"] == 4:
            continue
        parent_id = None
        if channel["parent_id"]:
            parent_id = category_id_map.get(channel["parent_id"])
        overwrites = remap_permission_overwrites(
            channel.get("permission_overwrites", []),
            role_id_map,
            SOURCE_GUILD_ID,
            NEW_GUILD_ID
        )
        channel["permission_overwrites"] = overwrites
        new_channel = create_channel(NEW_GUILD_ID, channel, parent_id=parent_id)
        print(f"Created channel: {new_channel['name']}")

    print("Server cloning completed!")

if __name__ == "__main__":
    main()

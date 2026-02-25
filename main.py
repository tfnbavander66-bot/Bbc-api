import requests , os , psutil , sys , jwt , pickle , json , binascii , time , urllib3 , base64 , datetime , re , socket , threading , ssl , pytz , aiohttp
from protobuf_decoder.protobuf_decoder import Parser
from xC4 import * ; from xHeaders import *
from datetime import datetime
from google.protobuf.timestamp_pb2 import Timestamp
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from Pb2 import DEcwHisPErMsG_pb2 , MajoRLoGinrEs_pb2 , PorTs_pb2 , MajoRLoGinrEq_pb2 , sQ_pb2 , Team_msg_pb2
from cfonts import render, say

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  

online_writer = None
whisper_writer = None
key = None
iv = None
region = None

spam_room = False
spammer_uid = None
spam_chat_id = None
spam_uid = None
Spy = False
Chat_Leave = False

team_members_data = []
team_history = []
current_team_leader = None
team_collection_active = False
last_member_update = None
previous_team_state = set()
previous_team_uids = set()  # Track previous state

def Get_clan_info(clan_id):
    try:
        url = f"https://get-clan-info.vercel.app/get_clan_info?clan_id={clan_id}"
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json()
            msg = f""" 
[11EAFD][b][c]
°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°
▶▶▶▶GUILD DETAILS◀◀◀◀
Achievements: {data['achievements']}\n\n
Balance : {fix_num(data['balance'])}\n\n
Clan Name : {data['clan_name']}\n\n
Expire Time : {fix_num(data['guild_details']['expire_time'])}\n\n
Members Online : {fix_num(data['guild_details']['members_online'])}\n\n
Regional : {data['guild_details']['regional']}\n\n
Reward Time : {fix_num(data['guild_details']['reward_time'])}\n\n
Total Members : {fix_num(data['guild_details']['total_members'])}\n\n
ID : {fix_num(data['id'])}\n\n
Last Active : {fix_num(data['last_active'])}\n\n
Level : {fix_num(data['level'])}\n\n
Rank : {fix_num(data['rank'])}\n\n
Region : {data['region']}\n\n
Score : {fix_num(data['score'])}\n\n
Timestamp1 : {fix_num(data['timestamp1'])}\n\n
Timestamp2 : {fix_num(data['timestamp2'])}\n\n
Welcome Message: {data['welcome_message']}\n\n
XP: {fix_num(data['xp'])}\n\n
°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°
[FFB300][b][c]MADE BY MatrixCoder
            """
            return msg
        else:
            msg = """
[11EAFD][b][c]
°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°
Failed to get info, please try again later!!

°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°
[FFB300][b][c]Developed BY MatrixCoder
            """
            return msg
    except:
        pass

#GET INFO BY PLAYER ID
def get_player_info(player_id):
    url = f"https://like2.vercel.app/player-info?uid={player_id}&server={server2}&key={key2}"
    response = requests.get(url)
    print(response)    
    if response.status_code == 200:
        try:
            r = response.json()
            return {
                "Account Booyah Pass": f"{r.get('booyah_pass_level', 'N/A')}",
                "Account Create": f"{r.get('createAt', 'N/A')}",
                "Account Level": f"{r.get('level', 'N/A')}",
                "Account Likes": f" {r.get('likes', 'N/A')}",
                "Name": f"{r.get('nickname', 'N/A')}",
                "UID": f" {r.get('accountId', 'N/A')}",
                "Account Region": f"{r.get('region', 'N/A')}",
                }
        except ValueError as e:
            pass
            return {
                "error": "Invalid JSON response"
            }
    else:
        pass
        return {
            "error": f"Failed to fetch data: {response.status_code}"
        }

#CHAT WITH AI
def talk_with_ai(question):
    url = f"https://gemini-api-api-v2.vercel.app/prince/api/v1/ask?key=prince&ask={question}"
    res = requests.get(url)
    if res.status_code == 200:
        data = res.json()
        msg = data["message"]["content"]
        return msg
    else:
        return "An error occurred while connecting to the server."

#SPAM REQUESTS
def spam_requests(player_id):
    url = f"https://like2.vercel.app/send_requests?uid={player_id}&server={server2}&key={key2}"
    try:
        res = requests.get(url, timeout=20)
        if res.status_code == 200:
            data = res.json()
            return f"API Status: Success [{data.get('success_count', 0)}] Failed [{data.get('failed_count', 0)}]"
        else:
            return f"API Error: Status {res.status_code}"
    except requests.exceptions.RequestException as e:
        print(f"Could not connect to spam API: {e}")
        return "Failed to connect to spam API."

####################################

# ** NEW INFO FUNCTION using the new API **
def newinfo(uid):
    url = "https://like2.vercel.app/player-info"
    params = {
        'uid': uid,
        'server': server2,
        'key': key2
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "basicInfo" in data:
                return {"status": "ok", "data": data}
            else:
                return {"status": "error", "message": data.get("error", "Invalid ID or data not found.")}
        else:
            try:
                error_msg = response.json().get('error', f"API returned status {response.status_code}")
                return {"status": "error", "message": error_msg}
            except ValueError:
                return {"status": "error", "message": f"API returned status {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"Network error: {str(e)}"}
    except ValueError: 
        return {"status": "error", "message": "Invalid JSON response from API."}

#ADDING-100-LIKES-IN-24H
def send_likes(uid):
    try:
        likes_api_response = requests.get(
             f"https://yourlikeapi/like?uid={uid}&server_name={server2}&x-vercel-set-bypass-cookie=true&x-vercel-protection-bypass={BYPASS_TOKEN}",
             timeout=15
             )
        if likes_api_response.status_code != 200:
            return f"""
[C][B][FF0000]━━━━━
[FFFFFF]Like API Error!
Status Code: {likes_api_response.status_code}
Please check if the uid is correct.
━━━━━
"""
        api_json_response = likes_api_response.json()
        player_name = api_json_response.get('PlayerNickname', 'Unknown')
        likes_before = api_json_response.get('LikesbeforeCommand', 0)
        likes_after = api_json_response.get('LikesafterCommand', 0)
        likes_added = api_json_response.get('LikesGivenByAPI', 0)
        status = api_json_response.get('status', 0)
        if status == 1 and likes_added > 0:
            return f"""
[C][B][11EAFD]‎━━━━━━━━━━━━
[FFFFFF]Likes Status:
[00FF00]Likes Sent Successfully!
[FFFFFF]Player Name : [00FF00]{player_name}  
[FFFFFF]Likes Added : [00FF00]{likes_added}  
[FFFFFF]Likes Before : [00FF00]{likes_before}  
[FFFFFF]Likes After : [00FF00]{likes_after}  
[C][B][11EAFD]‎━━━━━━━━━━━━
[C][B][FFB300]Subscribe: [FFFFFF]MatrixCoder [00FF00]!!
"""
        elif status == 2 or likes_before == likes_after:
            return f"""
[C][B][FF0000]━━━━━━━━━━━━
[FFFFFF]No Likes Sent!
[FF0000]You have already taken likes with this UID.
Try again after 24 hours.
[FFFFFF]Player Name : [FF0000]{player_name}  
[FFFFFF]Likes Before : [FF0000]{likes_before}  
[FFFFFF]Likes After : [FF0000]{likes_after}  
[C][B][FF0000]━━━━━━━━━━━━
"""
        else:
            return f"""
[C][B][FF0000]━━━━━━━━━━━━
[FFFFFF]Unexpected Response!
Something went wrong.
Please try again or contact support.
━━━━━━━━━━━━
"""
    except requests.exceptions.RequestException:
        return """
[C][B][FF0000]━━━━━
[FFFFFF]Like API Connection Failed!
Is the API server (app.py) running?
━━━━━
"""
    except Exception as e:
        return f"""
[C][B][FF0000]━━━━━
[FFFFFF]An unexpected error occurred:
[FF0000]{str(e)}
━━━━━
"""
####################################

Hr = {
    'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 11; ASUS_Z01QD Build/PI)",
    'Connection': "Keep-Alive",
    'Accept-Encoding': "gzip",
    'Content-Type': "application/x-www-form-urlencoded",
    'Expect': "100-continue",
    'X-Unity-Version': "2018.4.11f1",
    'X-GA': "v1 1",
    'ReleaseVersion': "OB52"}

def get_random_color():
    colors = [
        "[FF0000]", "[00FF00]", "[0000FF]", "[FFFF00]", "[FF00FF]", "[00FFFF]", "[FFFFFF]", "[FFA500]",
        "[A52A2A]", "[800080]", "[000000]", "[808080]", "[C0C0C0]", "[FFC0CB]", "[FFD700]", "[ADD8E6]",
        "[90EE90]", "[D2691E]", "[DC143C]", "[00CED1]", "[9400D3]", "[F08080]", "[20B2AA]", "[FF1493]",
        "[7CFC00]", "[B22222]", "[FF4500]", "[DAA520]", "[00BFFF]", "[00FF7F]", "[4682B4]", "[6495ED]",
        "[5F9EA0]", "[DDA0DD]", "[E6E6FA]", "[B0C4DE]", "[556B2F]", "[8FBC8F]", "[2E8B57]", "[3CB371]",
        "[6B8E23]", "[808000]", "[B8860B]", "[CD5C5C]", "[8B0000]", "[FF6347]", "[FF8C00]", "[BDB76B]",
        "[9932CC]", "[8A2BE2]", "[4B0082]", "[6A5ACD]", "[7B68EE]", "[4169E1]", "[1E90FF]", "[191970]",
        "[00008B]", "[000080]", "[008080]", "[008B8B]", "[B0E0E6]", "[AFEEEE]", "[E0FFFF]", "[F5F5DC]",
        "[FAEBD7]"
    ]
    return random.choice(colors)


# ============================================
# BROADCAST FUNCTION - WebSocket Updates
# ============================================

def broadcast_team_change(event_type, team_data):
    """Broadcast team changes to WebSocket clients with data validation"""
    try:
        # Validate data before sending
        if event_type in ['member_joined', 'member_left']:
            player = team_data.get('player', {})
            
            # Ensure all required fields exist
            validated_player = {
                'uid': str(player.get('uid', 'unknown')),
                'name': player.get('name', 'Unknown'),
                'region': player.get('region', 'UNK'),
                'level': int(player.get('level', 0)),
                'character': str(player.get('character', 'Unknown')),
                'position': player.get('position', 'Member')
            }
            
            team_data['player'] = validated_player
            
            # Debug log
            print(f"[WS-PREP] {event_type}: {validated_player['name']} (Level {validated_player['level']})")
        
        from api import broadcast_team_update
        broadcast_team_update(event_type, team_data)
    except Exception as e:
        print(f"[WS-ERROR] Failed to broadcast: {e}")


# ============================================
# TEAM COLLECTION WITH STATE MANAGEMENT
# ============================================

async def collect_team_members_dynamic(packet_type, parsed_data):
    """Team collection with proper state management and WebSocket broadcasting"""
    global team_members_data, current_team_leader, team_collection_active
    global last_member_update, previous_team_uids
    
    try:
        if packet_type != '0500_LARGE':
            return False
        
        new_members = []
        
        # Leader detection
        if '1' in parsed_data and parsed_data['1'].get('data'):
            leader_uid = parsed_data['1']['data']
            if leader_uid != current_team_leader:
                current_team_leader = leader_uid
            
            leader_info = await extract_complete_player_info(parsed_data, leader_uid, "Leader")
            if leader_info and leader_info['name'] != "Player_Unknown":
                if not any(m['uid'] == str(leader_uid) for m in new_members):
                    new_members.append(leader_info)

        # Deep scan
        deep_players = await deep_scan_for_players(parsed_data)
        for player in deep_players:
            if not any(m['uid'] == player['uid'] for m in new_members):
                new_members.append(player)

        # Field structures
        if '5' in parsed_data and 'data' in parsed_data['5']:
            squad_data = parsed_data['5']['data']
            field6_players = await extract_from_field_structure_fixed(squad_data)
            for player in field6_players:
                if not any(m['uid'] == player['uid'] for m in new_members):
                    new_members.append(player)

            # Nested
            if '3' in squad_data and 'data' in squad_data['3']:
                nested_data = squad_data['3']['data']
                nested_players = await extract_from_field_structure_fixed(nested_data)
                for player in nested_players:
                    if not any(m['uid'] == player['uid'] for m in new_members):
                        new_members.append(player)

        # ========== STATE CHANGE DETECTION ==========
        current_uids = set(m['uid'] for m in new_members)
        
        # Detect JOINED players
        joined = current_uids - previous_team_uids
        if joined:
            for uid in joined:
                player = next((m for m in new_members if m['uid'] == uid), None)
                if player:
                    print(f"[TEAM] + {player['name']} joined")
                    
                    # Broadcast join event with COMPLETE data
                    broadcast_team_change('member_joined', {
                        'player': {
                            'uid': player['uid'],
                            'name': player['name'],
                            'region': player['region'],
                            'level': player['level'],
                            'character': player.get('character', 'Unknown'),
                            'position': player['position']
                        },
                        'total_members': len(current_uids)
                    })
        
        # Detect LEFT/KICKED players
        left = previous_team_uids - current_uids
        if left:
            for uid in left:
                old_player = next((m for m in team_members_data if m['uid'] == uid), None)
                if old_player:
                    print(f"[TEAM] - {old_player['name']} left")
                    
                    # Broadcast leave event with COMPLETE data
                    broadcast_team_change('member_left', {
                        'player': {
                            'uid': old_player['uid'],
                            'name': old_player['name'],
                            'region': old_player['region'],
                            'level': old_player['level'],
                            'character': old_player.get('character', 'Unknown'),
                            'position': old_player['position']
                        },
                        'total_members': len(current_uids)
                    })
        
        # Update global state with ONLY current members
        team_members_data.clear()
        team_members_data.extend(new_members)
        previous_team_uids = current_uids
        
        # Update team status
        if len(new_members) > 0:
            if not team_collection_active:
                print(f"[TEAM] ✓ Joined team ({len(new_members)} members)")
                
                # Broadcast team joined with COMPLETE member data
                broadcast_team_change('team_joined', {
                    'in_team': True,
                    'total_members': len(new_members),
                    'leader_uid': str(current_team_leader) if current_team_leader else None,
                    'members': [
                        {
                            'uid': m['uid'],
                            'name': m['name'],
                            'region': m['region'],
                            'level': m['level'],
                            'character': m.get('character', 'Unknown'),
                            'position': m['position']
                        }
                        for m in new_members
                    ]
                })
            
            team_collection_active = True
            last_member_update = datetime.now()
            return True
        else:
            # No members found - bot left team
            if team_collection_active:
                print(f"[TEAM] ✗ Left team")
                
                # Broadcast team left
                broadcast_team_change('team_left', {
                    'in_team': False,
                    'total_members': 0,
                    'members': []
                })
            
            team_collection_active = False
            team_members_data.clear()
            previous_team_uids.clear()
            current_team_leader = None
        
        return False
        
    except:
        return False


async def extract_complete_player_info(parsed_data, uid, position="Member"):
    """Extract player info - Better name detection"""
    try:
        player_info = {
            'uid': str(uid),
            'name': None,  # Will be set below
            'region': 'UNK',
            'level': 0,
            'position': position,
            'character': 'Unknown',
            'timestamp': datetime.now().isoformat()
        }
        
        def find_player_details(obj, target_uid, depth=0):
            if depth > 5:
                return None
                
            if isinstance(obj, dict):
                if ('1' in obj and obj['1'].get('data') == target_uid):
                    details = {}
                    
                    if '2' in obj and isinstance(obj['2'].get('data'), str):
                        name = obj['2']['data']
                        if name and len(name) > 1 and not name.isdigit():
                            details['name'] = name
                    
                    if '3' in obj and isinstance(obj['3'].get('data'), str):
                        details['region'] = obj['3']['data']
                    
                    if '5' in obj and isinstance(obj['5'].get('data'), int):
                        details['level'] = obj['5']['data']
                    
                    if '6' in obj and isinstance(obj['6'].get('data'), (int, str)):
                        details['character'] = str(obj['6']['data'])
                    
                    return details
                
                for key, value in obj.items():
                    if isinstance(value, dict):
                        result = find_player_details(value, target_uid, depth+1)
                        if result:
                            return result
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                result = find_player_details(item, target_uid, depth+1)
                                if result:
                                    return result
            return None
        
        details = find_player_details(parsed_data, uid)
        if details:
            player_info.update(details)
        
        # If still no name found, use UID as fallback
        if not player_info['name']:
            player_info['name'] = f"Player_{uid}"
        
        return player_info
        
    except:
        return None


async def deep_scan_for_players(data, path="", depth=0):
    """Scan for players"""
    players = []
    
    if depth > 6:
        return players
        
    if isinstance(data, dict):
        if ('1' in data and '2' in data and 
            isinstance(data['1'].get('data'), (int, str)) and
            isinstance(data['2'].get('data'), str)):
            
            uid = data['1']['data']
            name = data['2']['data']
            
            if (name and 
                name != "Player_Unknown" and 
                not name.startswith("Player_") and
                not name.isdigit() and
                len(name) > 1):
                
                player = {
                    'uid': str(uid),
                    'name': name,
                    'region': data['3']['data'] if '3' in data and isinstance(data['3'].get('data'), str) else 'UNK',
                    'level': data['5']['data'] if '5' in data and isinstance(data['5'].get('data'), int) else 0,
                    'character': str(data['6']['data']) if '6' in data and isinstance(data['6'].get('data'), (int, str)) else 'Unknown',
                    'position': 'Leader' if str(uid) == str(current_team_leader) else 'Member',
                    'timestamp': datetime.now().isoformat()
                }
                players.append(player)
        
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                nested_players = await deep_scan_for_players(value, f"{path}.{key}", depth+1)
                players.extend(nested_players)
    
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                nested_players = await deep_scan_for_players(item, f"{path}[]", depth+1)
                players.extend(nested_players)
    
    return players


async def extract_from_field_structure_fixed(squad_data):
    """Extract from field structure"""
    players = []
    
    try:
        if '6' in squad_data and 'data' in squad_data['6']:
            player_data = squad_data['6']['data']
            if isinstance(player_data, dict) and '1' in player_data and '2' in player_data:
                uid = player_data['1'].get('data')
                name = player_data['2'].get('data')
                
                if uid and isinstance(name, str) and len(name) > 1 and not name.isdigit():
                    player = {
                        'uid': str(uid),
                        'name': name,
                        'region': player_data['3']['data'] if '3' in player_data and isinstance(player_data['3'].get('data'), str) else 'UNK',
                        'level': player_data['5']['data'] if '5' in player_data and isinstance(player_data['5'].get('data'), int) else 0,
                        'character': str(player_data['6']['data']) if '6' in player_data and isinstance(player_data['6'].get('data'), (int, str)) else 'Unknown',
                        'position': 'Leader' if str(uid) == str(current_team_leader) else 'Member',
                        'timestamp': datetime.now().isoformat()
                    }
                    players.append(player)
        
        for pos in ['1', '2', '3', '4', '7', '8']:
            if pos in squad_data and 'data' in squad_data[pos]:
                player_data = squad_data[pos]['data']
                if isinstance(player_data, dict) and '1' in player_data and '2' in player_data:
                    uid = player_data['1'].get('data')
                    name = player_data['2'].get('data')
                    
                    if uid and isinstance(name, str) and len(name) > 1 and not name.isdigit():
                        player = {
                            'uid': str(uid),
                            'name': name,
                            'region': player_data['3']['data'] if '3' in player_data and isinstance(player_data['3'].get('data'), str) else 'UNK',
                            'level': player_data['5']['data'] if '5' in player_data and isinstance(player_data['5'].get('data'), int) else 0,
                            'character': str(player_data['6']['data']) if '6' in player_data and isinstance(player_data['6'].get('data'), (int, str)) else 'Unknown',
                            'position': 'Leader' if str(uid) == str(current_team_leader) else 'Member',
                            'timestamp': datetime.now().isoformat()
                        }
                        players.append(player)
                        
    except:
        pass
    
    return players



async def encrypted_proto(encoded_hex):
    key = b'Yg&tc%DEuh6%Zc^8'
    iv = b'6oyZDr22E3ychjM%'
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_message = pad(encoded_hex, AES.block_size)
    encrypted_payload = cipher.encrypt(padded_message)
    return encrypted_payload

async def GeNeRaTeAccEss(uid , password):
    url = "https://100067.connect.garena.com/oauth/guest/token/grant"
    headers = {
        "Host": "100067.connect.garena.com",
        "User-Agent": (await Ua()),
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "close"}
    data = {
        "uid": uid,
        "password": password,
        "response_type": "token",
        "client_type": "2",
        "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
        "client_id": "100067"}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=Hr, data=data) as response:
            if response.status != 200: return "Failed to get access token"
            data = await response.json()
            open_id = data.get("open_id")
            access_token = data.get("access_token")
            return (open_id, access_token) if open_id and access_token else (None, None)

async def EncRypTMajoRLoGin(open_id, access_token):
    major_login = MajoRLoGinrEq_pb2.MajorLogin()
    major_login.event_time = str(datetime.now())[:-7]
    major_login.game_name = "free fire"
    major_login.platform_id = 1
    major_login.client_version = "1.120.1"
    major_login.system_software = "Android OS 9 / API-28 (PQ3B.190801.10101846/G9650ZHU2ARC6)"
    major_login.system_hardware = "Handheld"
    major_login.telecom_operator = "Verizon"
    major_login.network_type = "WIFI"
    major_login.screen_width = 1920
    major_login.screen_height = 1080
    major_login.screen_dpi = "280"
    major_login.processor_details = "ARM64 FP ASIMD AES VMH | 2865 | 4"
    major_login.memory = 3003
    major_login.gpu_renderer = "Adreno (TM) 640"
    major_login.gpu_version = "OpenGL ES 3.1 v1.46"
    major_login.unique_device_id = "Google|34a7dcdf-a7d5-4cb6-8d7e-3b0e448a0c57"
    major_login.client_ip = "223.191.51.89"
    major_login.language = "en"
    major_login.open_id = open_id
    major_login.open_id_type = "4"
    major_login.device_type = "Handheld"
    memory_available = major_login.memory_available
    memory_available.version = 55
    memory_available.hidden_value = 81
    major_login.access_token = access_token
    major_login.platform_sdk_id = 1
    major_login.network_operator_a = "Verizon"
    major_login.network_type_a = "WIFI"
    major_login.client_using_version = "7428b253defc164018c604a1ebbfebdf"
    major_login.external_storage_total = 36235
    major_login.external_storage_available = 31335
    major_login.internal_storage_total = 2519
    major_login.internal_storage_available = 703
    major_login.game_disk_storage_available = 25010
    major_login.game_disk_storage_total = 26628
    major_login.external_sdcard_avail_storage = 32992
    major_login.external_sdcard_total_storage = 36235
    major_login.login_by = 3
    major_login.library_path = "/data/app/com.dts.freefireth-YPKM8jHEwAJlhpmhDhv5MQ==/lib/arm64"
    major_login.reg_avatar = 1
    major_login.library_token = "5b892aaabd688e571f688053118a162b|/data/app/com.dts.freefireth-YPKM8jHEwAJlhpmhDhv5MQ==/base.apk"
    major_login.channel_type = 3
    major_login.cpu_type = 2
    major_login.cpu_architecture = "64"
    major_login.client_version_code = "2019118695"
    major_login.graphics_api = "OpenGLES2"
    major_login.supported_astc_bitset = 16383
    major_login.login_open_id_type = 4
    major_login.analytics_detail = b"FwQVTgUPX1UaUllDDwcWCRBpWAUOUgsvA1snWlBaO1kFYg=="
    major_login.loading_time = 13564
    major_login.release_channel = "android"
    major_login.extra_info = "KqsHTymw5/5GB23YGniUYN2/q47GATrq7eFeRatf0NkwLKEMQ0PK5BKEk72dPflAxUlEBir6Vtey83XqF593qsl8hwY="
    major_login.android_engine_init_flag = 110009
    major_login.if_push = 1
    major_login.is_vpn = 1
    major_login.origin_platform_type = "4"
    major_login.primary_platform_type = "4"
    string = major_login.SerializeToString()
    return  await encrypted_proto(string)

async def MajorLogin(payload):
    url = "https://loginbp.ggblueshark.com/MajorLogin"
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload, headers=Hr, ssl=ssl_context) as response:
            if response.status == 200: return await response.read()
            return None

async def GetLoginData(base_url, payload, token):
    url = f"{base_url}/GetLoginData"
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    Hr['Authorization']= f"Bearer {token}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload, headers=Hr, ssl=ssl_context) as response:
            if response.status == 200: return await response.read()
            return None

async def DecRypTMajoRLoGin(MajoRLoGinResPonsE):
    proto = MajoRLoGinrEs_pb2.MajorLoginRes()
    proto.ParseFromString(MajoRLoGinResPonsE)
    return proto

async def DecRypTLoGinDaTa(LoGinDaTa):
    proto = PorTs_pb2.GetLoginData()
    proto.ParseFromString(LoGinDaTa)
    return proto

async def DecodeWhisperMessage(hex_packet):
    packet = bytes.fromhex(hex_packet)
    proto = DEcwHisPErMsG_pb2.DecodeWhisper()
    proto.ParseFromString(packet)
    return proto

async def decode_team_packet(hex_packet):
    packet = bytes.fromhex(hex_packet)
    proto = sQ_pb2.recieved_chat()
    proto.ParseFromString(packet)
    return proto

async def xAuThSTarTuP(TarGeT, token, timestamp, key, iv):
    uid_hex = hex(TarGeT)[2:]
    uid_length = len(uid_hex)
    encrypted_timestamp = await DecodE_HeX(timestamp)
    encrypted_account_token = token.encode().hex()
    encrypted_packet = await EnC_PacKeT(encrypted_account_token, key, iv)
    encrypted_packet_length = hex(len(encrypted_packet) // 2)[2:]
    if uid_length == 9: headers = '0000000'
    elif uid_length == 8: headers = '00000000'
    elif uid_length == 10: headers = '000000'
    elif uid_length == 7: headers = '000000000'
    else: print('Unexpected length') ; headers = '0000000'
    return f"0115{headers}{uid_hex}{encrypted_timestamp}00000{encrypted_packet_length}{encrypted_packet}"

async def cHTypE(H):
    if not H: return 'Squid'
    elif H == 1: return 'CLan'
    elif H == 2: return 'PrivaTe'

async def SEndMsG(H , message , Uid , chat_id , key , iv):
    TypE = await cHTypE(H)
    if TypE == 'Squid': msg_packet = await xSEndMsgsQ(message , chat_id , key , iv)
    elif TypE == 'CLan': msg_packet = await xSEndMsg(message , 1 , chat_id , chat_id , key , iv)
    elif TypE == 'PrivaTe': msg_packet = await xSEndMsg(message , 2 , Uid , Uid , key , iv)
    return msg_packet

async def SEndPacKeT(OnLinE , ChaT , TypE , PacKeT):
    if TypE == 'ChaT' and ChaT: whisper_writer.write(PacKeT) ; await whisper_writer.drain()
    elif TypE == 'OnLine': online_writer.write(PacKeT) ; await online_writer.drain()
    else: return 'UnsoPorTed TypE ! >> ErrrroR (:():)' 

async def TcPOnLine(ip, port, key_val, iv_val, AutHToKen, reconnect_delay=0.5):
    global online_writer, key, iv, team_members_data, current_team_leader
    global team_collection_active, previous_team_uids
    
    key = key_val
    iv = iv_val
    
    while True:
        try:
            # Reset team state on new connection
            team_members_data = []
            current_team_leader = None
            team_collection_active = False
            previous_team_uids = set()
            
            reader, writer = await asyncio.open_connection(ip, int(port))
            online_writer = writer
            print(f"[ONLINE] Connected to {ip}:{port}")
            
            bytes_payload = bytes.fromhex(AutHToKen)
            online_writer.write(bytes_payload)
            await online_writer.drain()
            
            while True:
                data2 = await reader.read(9999)
                if not data2: break

                packet_hex = data2.hex()
                
                # Team collection
                if packet_hex.startswith('0500') and len(packet_hex) > 1000:
                    try:
                        decoded = await DeCode_PackEt(packet_hex[10:])
                        parsed = json.loads(decoded)
                        await collect_team_members_dynamic('0500_LARGE', parsed)
                    except:
                        pass
                
                # Your existing chat code
                if data2.hex().startswith('0500') and len(data2.hex()) > 1000:
                    try:
                        packet = await DeCode_PackEt(data2.hex()[10:])
                        packet = json.loads(packet)
                        OwNer_UiD, CHaT_CoDe, SQuAD_CoDe = await GeTSQDaTa(packet)

                        JoinCHaT = await AutH_Chat(3, OwNer_UiD, CHaT_CoDe, key, iv)
                        await SEndPacKeT(whisper_writer, online_writer, 'ChaT', JoinCHaT)

                        message = f'[B][C]{get_random_color()}\n- WeLComE To Emote Bot ! '
                        P = await SEndMsG(0, message, OwNer_UiD, OwNer_UiD, key, iv)
                        await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)
                    except:
                        pass

            online_writer.close()
            await online_writer.wait_closed()
            online_writer = None
            
            # Broadcast disconnect
            if team_collection_active:
                print(f"[TEAM] ✗ Disconnected from team")
                broadcast_team_change('team_left', {
                    'in_team': False,
                    'total_members': 0,
                    'members': []
                })
            
            # Reset state on disconnect
            team_members_data = []
            current_team_leader = None
            team_collection_active = False
            previous_team_uids = set()

        except Exception as e:
            print(f"[ERROR] {ip}:{port} - {e}")
            online_writer = None
            
            # Reset state on error
            team_members_data = []
            current_team_leader = None
            team_collection_active = False
            previous_team_uids = set()
            
        await asyncio.sleep(reconnect_delay)

async def TcPChaT(ip, port, AutHToKen, key_val, iv_val, LoGinDaTaUncRypTinG, ready_event, region_val, reconnect_delay=0.5):
    global spam_room, whisper_writer, spammer_uid, spam_chat_id, spam_uid, online_writer, chat_id, XX, uid, Spy, data2, Chat_Leave
    global region  # API access के लिए
    
    # Update global variables for API
    region = region_val
    
    print(region, 'TCP CHAT')
    
    while True:
        try:
            reader, writer = await asyncio.open_connection(ip, int(port))
            whisper_writer = writer
            print(f"[CHAT] Connected to {ip}:{port}")  # Debug message
            
            bytes_payload = bytes.fromhex(AutHToKen)
            whisper_writer.write(bytes_payload)
            await whisper_writer.drain()
            ready_event.set()
            
            if LoGinDaTaUncRypTinG.Clan_ID:
                clan_id = LoGinDaTaUncRypTinG.Clan_ID
                clan_compiled_data = LoGinDaTaUncRypTinG.Clan_Compiled_Data
                print('\n - TarGeT BoT in CLan ! ')
                print(f' - Clan Uid > {clan_id}')
                print(f' - BoT ConnEcTed WiTh CLan ChaT SuccEssFuLy ! ')
                pK = await AuthClan(clan_id, clan_compiled_data, key_val, iv_val)
                if whisper_writer:
                    whisper_writer.write(pK)
                    await whisper_writer.drain()
                    
            while True:
                data = await reader.read(9999)
                if not data: break

                if data.hex().startswith("120000"):
                    msg = await DeCode_PackEt(data.hex()[10:])
                    chatdata = json.loads(msg)
                    try:
                        response = await DecodeWhisperMessage(data.hex()[10:])
                        uid = response.Data.uid
                        chat_id = response.Data.Chat_ID
                        XX = response.Data.chat_type
                        inPuTMsG = response.Data.msg.lower()
                    except:
                        response = None

                    if response:
                        if inPuTMsG.startswith(("/5")):
                            try:
                                dd = chatdata['5']['data']['16']
                                print('msg in private')
                                message = f"[B][C]{get_random_color()}\n\nAccepT My Invitation FasT\n\n"
                                P = await SEndMsG(response.Data.chat_type, message, uid, chat_id, key_val, iv_val)
                                await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)
                                PAc = await OpEnSq(key_val, iv_val, region_val)
                                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', PAc)
                                C = await cHSq(5, uid, key_val, iv_val, region_val)
                                await asyncio.sleep(0.5)
                                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', C)
                                V = await SEnd_InV(5, uid, key_val, iv_val, region_val)
                                await asyncio.sleep(0.5)
                                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', V)
                                E = await ExiT(None, key_val, iv_val)
                                await asyncio.sleep(3)
                                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', E)
                            except:
                                print('msg in squad')

                        if inPuTMsG.startswith('/x/'):
                            CodE = inPuTMsG.split('/x/')[1]
                            try:
                                dd = chatdata['5']['data']['16']
                                print('msg in private')
                                EM = await GenJoinSquadsPacket(CodE, key_val, iv_val)
                                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', EM)
                            except:
                                print('msg in squad')

                        if inPuTMsG.startswith('/solo'):
                            leave = await ExiT(uid, key_val, iv_val)
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', leave)

                        if inPuTMsG.strip().startswith('/s'):
                            EM = await FS(key_val, iv_val)
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', EM)

                        if inPuTMsG.strip().startswith('!e'):
                            try:
                                dd = chatdata['5']['data']['16']
                                print('msg in private')
                                message = f"[B][C]{get_random_color()}\n\nCommand Available OnLy In SQuaD ! \n\n"
                                P = await SEndMsG(response.Data.chat_type, message, uid, chat_id, key_val, iv_val)
                                await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)
                            except:
                                print('msg in squad')
                                parts = inPuTMsG.strip().split()
                                print(response.Data.chat_type, uid, chat_id)
                                message = f'[B][C]{get_random_color()}\nACITVE TarGeT -> {xMsGFixinG(uid)}\n'
                                P = await SEndMsG(response.Data.chat_type, message, uid, chat_id, key_val, iv_val)
                                uid2 = uid3 = uid4 = uid5 = None
                                s = False
                                try:
                                    uid = int(parts[1])
                                    uid2 = int(parts[2])
                                    uid3 = int(parts[3])
                                    uid4 = int(parts[4])
                                    uid5 = int(parts[5])
                                    idT = int(parts[5])
                                except ValueError as ve:
                                    print("ValueError:", ve)
                                    s = True
                                except Exception:
                                    idT = len(parts) - 1
                                    idT = int(parts[idT])
                                    print(idT)
                                    print(uid)
                                if not s:
                                    try:
                                        await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)
                                        H = await Emote_k(uid, idT, key_val, iv_val, region_val)
                                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
                                        if uid2:
                                            H = await Emote_k(uid2, idT, key_val, iv_val, region_val)
                                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
                                        if uid3:
                                            H = await Emote_k(uid3, idT, key_val, iv_val, region_val)
                                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
                                        if uid4:
                                            H = await Emote_k(uid4, idT, key_val, iv_val, region_val)
                                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
                                        if uid5:
                                            H = await Emote_k(uid5, idT, key_val, iv_val, region_val)
                                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
                                    except Exception as e:
                                        pass

                        if inPuTMsG in ("hi", "hello", "fen", "help"):
                            uid = response.Data.uid
                            chat_id = response.Data.Chat_ID
                            message = '[C][B][00FFFF]━━━━━━━━━━━━\n[ffd319][B]☂︎Add 100 Likes\n[FFFFFF]/like/(uid)\n[ffd319][b]❄︎Join Bot In Group\n[FFFFFF][b]/x/(teamcode)\n[ffd319][b]❀To Perform AnyEmote\n[FFFFFF][b]!e (uid) (emote) code)\n[ffd319]⚡Make 5 Player Group:\n[FFFFFF]❄️/5 \n[ffd319][b][c]🎵Make leave Bot \n[FFFFFF][b][c]©️/solo\n[00FF7F][B]!!admin Commond!!\n[ffd319][b]To Stop The Bot\n[FFFFFF][b]/stop\n[ffd319][b]To Mute Bot\n[FFFFFF][b]/mute (time)\n[C][B][FFB300]OWNER: WINTER\n[00FFFF]━━━━━━━━━━━━\n[00FF00]\n[00ff00][B]⚓Thankyou For Joining Our Guild⚓                            '
                            P = await SEndMsG(response.Data.chat_type, message, uid, chat_id, key_val, iv_val)
                            await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)
                        response = None

            whisper_writer.close()
            await whisper_writer.wait_closed()
            whisper_writer = None

        except Exception as e:
            print(f"ErroR {ip}:{port} - {e}")
            whisper_writer = None
        await asyncio.sleep(reconnect_delay)


# ============================================
# NEW FUNCTIONS FOR API COMMANDS
# ============================================

async def process_command_queue():
    """Process commands from API queue"""
    from api import command_queue
    
    while True:
        try:
            if not command_queue.empty():
                command = command_queue.get_nowait()
                
                # CASE 1: JOIN + EMOTE + LEAVE
                if command['type'] == 'join_emote_leave':
                    teamcode = command['teamcode']
                    uids = command['uids']
                    emote_code = command['emote_code']
                    
                    # Background task
                    asyncio.create_task(join_emote_and_leave(teamcode, uids, emote_code))
                    print(f"[QUEUE] ✅ Processing join+emote+leave for team {teamcode}")
                
                # CASE 2: 5-PLAYER GROUP
                elif command['type'] == 'create_five_group':
                    uid = command['uid']
                    asyncio.create_task(create_five_player_group(uid))
                    print(f"[QUEUE] 🎮 Processing 5-player group for UID: {uid}")
                
                # CASE 3: SOLO LEAVE
                elif command['type'] == 'solo_leave':
                    asyncio.create_task(solo_leave_command())
                    print(f"[QUEUE] 👋 Processing solo leave")
                
                # CASE 4: NORMAL EMOTE
                elif command['type'] == 'emote':
                    uids = command['uids']
                    emote_code = command['emote_code']
                    asyncio.create_task(normal_emote_command(uids, emote_code))
                    print(f"[QUEUE] 📨 Processing emote for {len(uids)} player(s)")
                
                # CASE 5: JOIN ONLY
                elif command['type'] == 'join':
                    teamcode = command['teamcode']
                    asyncio.create_task(join_only_command(teamcode))
                    print(f"[QUEUE] 🔑 Processing join for team {teamcode}")
            
            await asyncio.sleep(0.1)
            
        except Exception as e:
            print(f"[QUEUE ERROR] {e}")
            await asyncio.sleep(0.5)


async def join_emote_and_leave(teamcode, uids, emote_code):
    """Join team, send emote, then leave after 1 second (uses /solo)"""
    global whisper_writer, online_writer, key, iv, region
    
    try:
        print(f"[JEL] 🚀 Starting: Join team {teamcode} → Emote {len(uids)} player(s) → Leave after 1s")
        
        # STEP 1: JOIN TEAM (same as /x/ command)
        join_packet = await GenJoinSquadsPacket(teamcode, key, iv)
        if online_writer:
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', join_packet)
            print(f"[JEL] ✅ Joined team with code: {teamcode}")
        else:
            print(f"[JEL] ❌ Online writer not available")
            return
        
        # Wait for team to be ready
        await asyncio.sleep(2.0)
        
        # STEP 2: SEND EMOTE to all UIDs (same as !e command)
        for uid in uids:
            try:
                emote_packet = await Emote_k(int(uid), int(emote_code), key, iv, region)
                if online_writer:
                    await SEndPacKeT(whisper_writer, online_writer, 'OnLine', emote_packet)
                    print(f"[JEL] 📨 Emote sent to UID: {uid}")
                    await asyncio.sleep(0.2)
            except Exception as e:
                print(f"[JEL] ❌ Failed to send emote to {uid}: {e}")
        
        print(f"[JEL] ✅ Emote sent to {len(uids)} player(s)")
        
        # STEP 3: WAIT 1 SECOND
        await asyncio.sleep(1.0)
        
        # STEP 4: LEAVE TEAM (same as /solo command)
        if online_writer:
            leave_packet = await ExiT(None, key, iv)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', leave_packet)
            print(f"[JEL] 👋 Left team after emote")
        else:
            print(f"[JEL] ❌ Cannot leave - online writer not available")
        
    except Exception as e:
        print(f"[JEL ERROR] {e}")


async def create_five_player_group(uid):
    """Create 5-player group (same as /5 command)"""
    global whisper_writer, online_writer, key, iv, region
    
    try:
        print(f"[5-GROUP] 🎮 Creating 5-player group for UID: {uid}")
        
        # Step 1: Send private message
        message = f"[B][C]{get_random_color()}\n\nAccepT My Invitation FasT\n\n"
        P = await SEndMsG(2, message, int(uid), int(uid), key, iv)
        await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)
        print(f"[5-GROUP] 📨 Private message sent to {uid}")
        
        # Step 2: Open squad
        PAc = await OpEnSq(key, iv, region)
        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', PAc)
        print(f"[5-GROUP] 🚪 Squad opened")
        
        # Step 3: Change to 5 players
        C = await cHSq(5, int(uid), key, iv, region)
        await asyncio.sleep(0.5)
        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', C)
        print(f"[5-GROUP] 👥 Changed to 5 players")
        
        # Step 4: Send invitation
        V = await SEnd_InV(5, int(uid), key, iv, region)
        await asyncio.sleep(0.5)
        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', V)
        print(f"[5-GROUP] ✉️ Invitation sent")
        
        # Step 5: Exit after 3 seconds
        E = await ExiT(None, key, iv)
        await asyncio.sleep(3)
        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', E)
        print(f"[5-GROUP] 👋 Exited squad after 3 seconds")
        
        print(f"[5-GROUP] ✅ Successfully created 5-player group for {uid}")
        
    except Exception as e:
        print(f"[5-GROUP ERROR] {e}")


async def solo_leave_command():
    """Leave team (same as /solo)"""
    global whisper_writer, online_writer, key, iv
    
    try:
        if online_writer:
            leave_packet = await ExiT(None, key, iv)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', leave_packet)
            print(f"[SOLO] 👋 Left team")
        else:
            print(f"[SOLO] ❌ Online writer not available")
    except Exception as e:
        print(f"[SOLO ERROR] {e}")


async def normal_emote_command(uids, emote_code):
    """Send normal emote to UIDs"""
    global whisper_writer, online_writer, key, iv, region
    
    try:
        print(f"[EMOTE] 📨 Sending emote to {len(uids)} player(s)")
        
        for uid in uids:
            try:
                emote_packet = await Emote_k(int(uid), int(emote_code), key, iv, region)
                if online_writer:
                    await SEndPacKeT(whisper_writer, online_writer, 'OnLine', emote_packet)
                    print(f"[EMOTE] ✅ Emote sent to UID: {uid}")
                    await asyncio.sleep(0.2)
            except Exception as e:
                print(f"[EMOTE] ❌ Failed to send emote to {uid}: {e}")
        
        print(f"[EMOTE] ✅ Emote completed for {len(uids)} player(s)")
        
    except Exception as e:
        print(f"[EMOTE ERROR] {e}")


async def join_only_command(teamcode):
    """Join team only"""
    global whisper_writer, online_writer, key, iv
    
    try:
        join_packet = await GenJoinSquadsPacket(teamcode, key, iv)
        if online_writer:
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', join_packet)
            print(f"[JOIN] ✅ Joined team with code: {teamcode}")
        else:
            print(f"[JOIN] ❌ Online writer not available")
    except Exception as e:
        print(f"[JOIN ERROR] {e}")


# ============================================
# MAIN FUNCTION
# ============================================

async def MaiiiinE():
    Uid, Pw = '4416690878','ESHHUUU_xyz007_3DOPN_BY_SPIDEERIO_GAMING_DMC1F'

    open_id, access_token = await GeNeRaTeAccEss(Uid, Pw)
    if not open_id or not access_token:
        print("ErroR - InvaLid AccounT")
        return None

    PyL = await EncRypTMajoRLoGin(open_id, access_token)
    MajoRLoGinResPonsE = await MajorLogin(PyL)
    if not MajoRLoGinResPonsE:
        print("TarGeT AccounT => BannEd / NoT ReGisTeReD ! ")
        return None

    MajoRLoGinauTh = await DecRypTMajoRLoGin(MajoRLoGinResPonsE)
    UrL = MajoRLoGinauTh.url
    print(UrL)
    region_val = MajoRLoGinauTh.region

    ToKen = MajoRLoGinauTh.token
    TarGeT = MajoRLoGinauTh.account_uid
    key_val = MajoRLoGinauTh.key
    iv_val = MajoRLoGinauTh.iv
    timestamp = MajoRLoGinauTh.timestamp

    LoGinDaTa = await GetLoginData(UrL, PyL, ToKen)
    if not LoGinDaTa:
        print("ErroR - GeTinG PorTs From LoGin DaTa !")
        return None
        
    LoGinDaTaUncRypTinG = await DecRypTLoGinDaTa(LoGinDaTa)
    OnLinePorTs = LoGinDaTaUncRypTinG.Online_IP_Port
    ChaTPorTs = LoGinDaTaUncRypTinG.AccountIP_Port
    OnLineiP, OnLineporT = OnLinePorTs.split(":")
    ChaTiP, ChaTporT = ChaTPorTs.split(":")
    acc_name = LoGinDaTaUncRypTinG.AccountName
    
    print(ToKen)
    equie_emote(ToKen, UrL)
    AutHToKen = await xAuThSTarTuP(int(TarGeT), ToKen, int(timestamp), key_val, iv_val)
    ready_event = asyncio.Event()

    task1 = asyncio.create_task(TcPChaT(ChaTiP, ChaTporT, AutHToKen, key_val, iv_val, LoGinDaTaUncRypTinG, ready_event, region_val))
    await ready_event.wait()
    await asyncio.sleep(1)
    task2 = asyncio.create_task(TcPOnLine(OnLineiP, OnLineporT, key_val, iv_val, AutHToKen))
    
    # ADD QUEUE PROCESSOR TASK
    task3 = asyncio.create_task(process_command_queue())
    
    os.system('clear')
    print(render('BIGBULL', colors=['white', 'green'], align='center'))
    print('')
    print(f" - BoT STarTinG And OnLine on TarGet : {TarGeT} | BOT NAME : {acc_name}\n")
    print(f" - BoT sTaTus > GooD | OnLinE ! (:")    
    print(f" - Subscribe > Bigbullcheats | Gaming ! (:")    
    
    # UPDATE GATHER WITH TASK3
    await asyncio.gather(task1, task2, task3)

async def StarTinG():
    while True:
        try:
            await asyncio.wait_for(MaiiiinE(), timeout=7 * 60 * 60)
        except asyncio.TimeoutError:
            print("Token ExpiRed ! , ResTartinG")
        except Exception as e:
            print(f"ErroR TcP - {e} => ResTarTinG ...")

if __name__ == '__main__':
    asyncio.run(StarTinG())

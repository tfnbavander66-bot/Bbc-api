# ============================================
# PRODUCTION API WITH WEBSOCKET - api.py
# Real-time team updates, no JSON storage
# ============================================

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sock import Sock
import queue
import json
import time

app = Flask(__name__)
CORS(app)
sock = Sock(app)

command_queue = queue.Queue()

# WebSocket clients list
websocket_clients = []

# ============================================
# WEBSOCKET - Real-time Team Updates
# ============================================

@sock.route('/ws')
def websocket(ws):
    """WebSocket connection for real-time updates"""
    print(f"[WS] Client connected")
    websocket_clients.append(ws)
    
    try:
        # Send initial team status
        team_status = get_live_team_status()
        ws.send(json.dumps({
            'type': 'initial',
            'data': team_status
        }))
        
        # Keep connection alive
        while True:
            # Receive messages from client (optional)
            message = ws.receive(timeout=30)
            if message:
                data = json.loads(message)
                
                # Handle client requests
                if data.get('type') == 'get_team':
                    team_status = get_live_team_status()
                    ws.send(json.dumps({
                        'type': 'team_update',
                        'data': team_status
                    }))
    
    except Exception as e:
        print(f"[WS] Client disconnected: {e}")
    
    finally:
        if ws in websocket_clients:
            websocket_clients.remove(ws)
        print(f"[WS] Client removed")


def broadcast_team_update(event_type, data):
    """Broadcast team updates to all connected WebSocket clients"""
    
    # DEBUG: Log what we're sending
    if event_type in ['member_joined', 'member_left']:
        player = data.get('player', {})
        print(f"[WS→] {event_type}: {player.get('name')} (UID: {player.get('uid')})")
    
    message = json.dumps({
        'type': event_type,
        'data': data,
        'timestamp': time.time()
    }, ensure_ascii=False)  # Important for Unicode characters
    
    disconnected = []
    sent_count = 0
    
    for client in websocket_clients:
        try:
            client.send(message)
            sent_count += 1
        except Exception as e:
            print(f"[WS→] Failed to send to client: {e}")
            disconnected.append(client)
    
    if sent_count > 0:
        print(f"[WS→] Sent to {sent_count} client(s)")
    
    # Remove disconnected clients
    for client in disconnected:
        if client in websocket_clients:
            websocket_clients.remove(client)


# ============================================
# JOIN TEAM API
# ============================================

@app.route('/join', methods=['GET', 'POST'])
def join_team():
    """Join a team using teamcode"""
    try:
        if request.method == 'GET':
            teamcode = request.args.get('teamcode')
        else:
            data = request.get_json(silent=True)
            teamcode = data.get('teamcode') if data else None
        
        if not teamcode:
            return jsonify({
                'success': False,
                'message': 'teamcode is required'
            }), 400
        
        command_queue.put({
            'type': 'join',
            'teamcode': teamcode
        })
        
        return jsonify({
            'success': True,
            'message': 'Join command queued',
            'teamcode': teamcode
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# ============================================
# EMOTE API - NOW SUPPORTS BOTH GET & POST
# ============================================

@app.route('/emote', methods=['GET', 'POST'])
def send_emote():
    """Send emote to players (bot must be in team) - Supports GET & POST"""
    try:
        uids = []
        emote_code = None
        
        # Handle GET request with query parameters
        if request.method == 'GET':
            # Get UIDs from query parameters (uid, uid2, uid3, uid4, uid5)
            uids = []
            for i in range(1, 6):  # Support up to 5 UIDs
                uid_param = f'uid{i}' if i > 1 else 'uid'
                uid_value = request.args.get(uid_param)
                if uid_value:
                    uids.append(uid_value)
            
            emote_code = request.args.get('emote_code')
            
            # If no UIDs found in numbered parameters, try single uid
            if not uids:
                single_uid = request.args.get('uid')
                if single_uid:
                    uids = [single_uid]
        
        # Handle POST request with JSON body
        else:
            data = request.get_json(silent=True)
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'JSON body required for POST'
                }), 400
            
            uids = data.get('uids', [])
            emote_code = data.get('emote_code')
            
            # Convert single UID to list if needed
            if isinstance(uids, str):
                uids = [uids]
        
        # Validation
        if not emote_code:
            return jsonify({
                'success': False,
                'message': 'emote_code is required'
            }), 400
        
        if not uids or len(uids) == 0:
            return jsonify({
                'success': False,
                'message': 'At least one UID is required'
            }), 400
        
        if len(uids) > 5:
            return jsonify({
                'success': False,
                'message': 'Maximum 5 UIDs allowed per request'
            }), 400
        
        # Check if bot is in team (LIVE CHECK)
        team_status = get_live_team_status()
        if not team_status['in_team']:
            return jsonify({
                'success': False,
                'message': 'Bot is not in any team. Join a team first.',
                'in_team': False
            }), 400
        
        # Queue emote command
        command_queue.put({
            'type': 'emote',
            'uids': uids,
            'emote_code': emote_code
        })
        
        response_data = {
            'success': True,
            'message': f'Emote queued for {len(uids)} player(s)',
            'uids': uids,
            'emote_code': emote_code,
            'in_team': True,
            'method': request.method
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# ============================================
# EMOTE ALL TEAM MEMBERS
# ============================================

@app.route('/emote/team', methods=['POST'])
def emote_team():
    """Send emote to all team members"""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({
                'success': False,
                'message': 'JSON body required'
            }), 400
        
        emote_code = data.get('emote_code')
        
        if not emote_code:
            return jsonify({
                'success': False,
                'message': 'emote_code is required'
            }), 400
        
        # Get LIVE team status
        team_status = get_live_team_status()
        if not team_status['in_team']:
            return jsonify({
                'success': False,
                'message': 'Bot is not in any team',
                'in_team': False
            }), 400
        
        if not team_status.get('members'):
            return jsonify({
                'success': False,
                'message': 'No team members found',
                'in_team': True
            }), 400
        
        uids = [m['uid'] for m in team_status['members']]
        
        # Queue emote for all members
        command_queue.put({
            'type': 'emote',
            'uids': uids,
            'emote_code': emote_code
        })
        
        return jsonify({
            'success': True,
            'message': f'Emote queued for all {len(uids)} team members',
            'uids': uids,
            'emote_code': emote_code,
            'team_size': len(uids)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# ============================================
# GET TEAM MEMBERS - LIVE DATA
# ============================================

@app.route('/team/members', methods=['GET'])
def get_team_members():
    """Get current team members - LIVE from memory, not JSON"""
    try:
        team_status = get_live_team_status()
        
        # Bot is NOT in team
        if not team_status['in_team']:
            return jsonify({
                'success': False,
                'message': 'Bot is not in any team',
                'in_team': False,
                'members': [],
                'total_members': 0
            })
        
        # Bot IS in team - return LIVE data
        return jsonify({
            'success': True,
            'message': 'Team members retrieved',
            'in_team': True,
            'total_members': team_status['total_members'],
            'leader_uid': team_status['leader_uid'],
            'members': team_status['members']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# ============================================
# BOT STATUS
# ============================================

@app.route('/status', methods=['GET'])
def bot_status():
    """Get bot connection status"""
    try:
        from main import online_writer, whisper_writer, key, iv, region
        
        connections = {
            'online': online_writer is not None,
            'chat': whisper_writer is not None,
            'authenticated': key is not None and iv is not None,
            'region': region
        }
        
        team_status = get_live_team_status()
        
        return jsonify({
            'success': True,
            'bot_online': connections['online'] and connections['chat'],
            'connections': connections,
            'team': team_status,
            'queue_size': command_queue.qsize(),
            'ws_clients': len(websocket_clients)
        })
        
    except ImportError:
        return jsonify({
            'success': False,
            'message': 'Bot not running',
            'bot_online': False
        }), 503


# ============================================
# HOME / API INFO
# ============================================

@app.route('/', methods=['GET'])
def home():
    """API documentation"""
    return jsonify({
        'name': 'FF Emote Bot API',
        'version': '2.0',
        'status': 'online',
        'websocket': 'ws://host:5000/ws',
        'endpoints': {
            'GET/POST /join': 'Join team - Body: {"teamcode": "ABC123"} or ?teamcode=ABC123',
            'GET/POST /emote': 'Send emote - Body: {"uids": ["123"], "emote_code": "909000001"} or ?uid=123&uid2=456&emote_code=909000001',
            'POST /emote/team': 'Emote all team - Body: {"emote_code": "909000001"}',
            'GET /team/members': 'Get team members (LIVE)',
            'GET /status': 'Bot status',
            'WS /ws': 'WebSocket for real-time updates'
        }
    })


# ============================================
# HELPER FUNCTIONS - LIVE DATA FROM MEMORY
# ============================================

def get_live_team_status():
    """Get LIVE team status from bot memory (not JSON file)"""
    try:
        from main import team_collection_active, team_members_data, current_team_leader
        
        # Check if bot is actually in a team RIGHT NOW
        in_team = team_collection_active and len(team_members_data) > 0
        
        if not in_team:
            return {
                'in_team': False,
                'total_members': 0,
                'leader_uid': None,
                'members': []
            }
        
        return {
            'in_team': True,
            'total_members': len(team_members_data),
            'leader_uid': str(current_team_leader) if current_team_leader else None,
            'members': team_members_data
        }
    except:
        return {
            'in_team': False,
            'total_members': 0,
            'leader_uid': None,
            'members': []
        }


# ============================================
# RUN SERVER
# ============================================

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════╗
║   FF Emote Bot API - Production v2.0         ║
║   with WebSocket Support                     ║
╚══════════════════════════════════════════════╝

📡 HTTP API: http://0.0.0.0:5000
🔌 WebSocket: ws://0.0.0.0:5000/ws

Endpoints:
  • GET/POST /join       - Join team
  • GET/POST /emote      - Send emote (requires team)
  • POST /emote/team     - Emote all team members
  • GET  /team/members   - Get team info (LIVE)
  • GET  /status         - Bot status
  • WS   /ws             - Real-time updates

GET Emote Examples:
  /emote?uid=123456789&uid2=5263194623&uid3=4086317886&emote_code=909000081

    """)
    app.run(host='0.0.0.0', port=5000, debug=False)
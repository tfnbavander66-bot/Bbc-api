
import asyncio
import threading
from api import app, command_queue
import sys

# ============================================
# COMMAND PROCESSOR - Clean & Efficient
# ============================================

async def process_api_commands():
    """Process commands from API queue - production version"""
    while True:
        try:
            if not command_queue.empty():
                command = command_queue.get_nowait()
                
                if command['type'] == 'join':
                    await handle_join(command)
                
                elif command['type'] == 'emote':
                    await handle_emote(command)
            
            await asyncio.sleep(0.1)
        
        except Exception as e:
            print(f"[API ERROR] {e}")
            await asyncio.sleep(1)


# ============================================
# JOIN HANDLER
# ============================================

async def handle_join(command):
    """Handle join team command"""
    teamcode = command['teamcode']
    
    try:
        from main import online_writer, key, iv
        from xC4 import GenJoinSquadsPacket
        
        if not online_writer:
            print(f"[JOIN] Failed - Bot not connected")
            return
        
        if not key or not iv:
            print(f"[JOIN] Failed - No encryption keys")
            return
        
        packet = await GenJoinSquadsPacket(teamcode, key, iv)
        online_writer.write(packet)
        await online_writer.drain()
        
        print(f"[JOIN] ✓ Team: {teamcode}")
        
    except Exception as e:
        print(f"[JOIN] ✗ Error: {e}")


# ============================================
# EMOTE HANDLER - Only works if in team
# ============================================

async def handle_emote(command):
    """Handle emote command - checks team status first"""
    uids = command['uids']
    emote_code = command['emote_code']
    
    try:
        from main import online_writer, key, iv, region, team_collection_active, team_members_data
        from xC4 import Emote_k
        
        # Check if bot is in team
        if not team_collection_active or len(team_members_data) == 0:
            print(f"[EMOTE] ✗ Bot not in team - Skipped")
            return
        
        if not online_writer or not key or not iv or not region:
            print(f"[EMOTE] ✗ Bot not ready")
            return
        
        success = 0
        failed = 0
        
        for uid in uids:
            try:
                packet = await Emote_k(
                    int(uid), 
                    int(emote_code), 
                    key, 
                    iv,
                    region
                )
                
                online_writer.write(packet)
                await online_writer.drain()
                success += 1
                
                await asyncio.sleep(0.3)  # Rate limit
                
            except Exception as e:
                failed += 1
        
        if success > 0:
            print(f"[EMOTE] ✓ Sent: {success}/{len(uids)} | Code: {emote_code}")
        if failed > 0:
            print(f"[EMOTE] ✗ Failed: {failed}")
        
    except Exception as e:
        print(f"[EMOTE] ✗ Error: {e}")


# ============================================
# FLASK SERVER THREAD
# ============================================

def run_flask():
    """Run Flask in separate thread"""
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)


# ============================================
# MAIN RUNNER
# ============================================

async def run_bot_with_api():
    """Main function - runs bot + API together"""
    
    # Start Flask API
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("[API] Started on http://0.0.0.0:5000")
    
    # Start command processor
    api_processor = asyncio.create_task(process_api_commands())
    
    # Start main bot
    try:
        from main import StarTinG
        
        print("[BOT] Starting...")
        bot_task = asyncio.create_task(StarTinG())
        
        await asyncio.gather(api_processor, bot_task)
    
    except ImportError as e:
        print(f"[ERROR] Could not import bot: {e}")
        print("[API] Running in API-only mode...")
        await api_processor


# ============================================
# ENTRY POINT
# ============================================

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════╗
║      FF Emote Bot - Production Mode          ║
╚══════════════════════════════════════════════╝

Starting services...
    """)
    
    try:
        asyncio.run(run_bot_with_api())
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Stopping...")
        sys.exit(0)
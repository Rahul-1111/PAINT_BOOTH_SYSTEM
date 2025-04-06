import time
import threading
import pymcprotocol
from datetime import datetime
from booth.models import OEEDashboardData
import asyncio

plc_ip = "192.168.3.10"
plc_port = 5000

plc = pymcprotocol.Type3E()

async def toggle_heartbeat():
    heartbeat = 0
    while True:
        try:
            await asyncio.to_thread(plc.batchwrite_wordunits, 'D5101', [heartbeat])
            heartbeat = 1 - heartbeat
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"[Heartbeat Error] {e}")
            await asyncio.sleep(2)

def read_oee_and_store():
    try:
        values = plc.batchread_wordunits('D5102', 5)
        OEEDashboardData.objects.create(
            date=datetime.now().date(),
            time=datetime.now().time(),
            shift="Auto",
            part_number="AutoFetch",
            ok_production=int(values[0]),
            cycle_on_time=int(values[1]),
            cycle_off_time=int(values[2])
        )
    except Exception as e:
        print(f"[OEE Read Error] {e}")

def handle_recipe_change():
    plc.batchwrite_wordunits('D5100', [1])
    time.sleep(0.6)
    plc.batchwrite_wordunits('D5100', [0])

def handle_manual_fetch():
    plc.batchwrite_wordunits('D5205', [1])
    time.sleep(0.5)
    read_oee_and_store()
    plc.batchwrite_wordunits('D5205', [0])

def handle_manual_fetch_2():
    plc.batchwrite_wordunits('D5206', [1])
    time.sleep(0.5)
    read_oee_and_store()
    plc.batchwrite_wordunits('D5206', [0])

def start_async_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(toggle_heartbeat())

def monitor_plc_loop():
    global plc
    while True:
        try:
            print("🔌 Trying to connect to PLC...")
            plc = pymcprotocol.Type3E()
            plc.connect(plc_ip, plc_port)
            print("✅ PLC Connected.")

            # Start heartbeat in a new async thread
            threading.Thread(target=start_async_loop, daemon=True).start()

            break  # Exit loop once connected and heartbeat started
        except Exception as e:
            print(f"[PLC Monitor Error] {e}")
            print("🔁 Reconnecting in 5 seconds...")
            time.sleep(5)
            
def handle_recipe_change_with_input(part_number: str):
    try:
        print(f"📦 Recipe Change Triggered → Part: {part_number}")
        plc.batchwrite_wordunits('D5100', [1])
        time.sleep(0.6)
        plc.batchwrite_wordunits('D5100', [0])
    except Exception as e:
        print(f"[Recipe Change Error] {e}")



def run():
    print("🚀 Starting PLC monitoring thread...")
    threading.Thread(target=monitor_plc_loop, daemon=True).start()

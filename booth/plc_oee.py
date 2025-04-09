import time
import threading
import pymcprotocol
from datetime import datetime
from booth.models import OEEDashboardData
import asyncio

plc_ip = "192.168.3.10"
plc_port = 5000
plc = pymcprotocol.Type3E()

last_entered_part_number = None  # 🔁 Store last entered part (in Python only)

# ✅ Called from view or API when user enters new part
def handle_recipe_change_with_input(part_number):
    global last_entered_part_number
    last_entered_part_number = part_number
    print(f"✅ Part number updated by user: {part_number}")

    try:
        # Send signal to PLC that new recipe entered (only when user inputs)
        plc.batchwrite_wordunits('D5100', [1])
        time.sleep(0.5)
        plc.batchwrite_wordunits('D5100', [0])
        print("📤 Recipe change signal sent to PLC")
    except Exception as e:
        print(f"[PLC Write Error - Recipe Signal] {e}")

def connect_plc():
    global plc
    try:
        plc = pymcprotocol.Type3E()
        plc.connect(plc_ip, plc_port)
        print("✅ PLC Connected")
    except Exception as e:
        print(f"[PLC Connection Error] {e}")

async def toggle_heartbeat():
    heartbeat = 0
    while True:
        try:
            await asyncio.to_thread(plc.batchwrite_wordunits, 'D5101', [heartbeat])
            heartbeat = 1 - heartbeat
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"[Heartbeat Error] {e}")
            await asyncio.sleep(3)
            connect_plc()

def monitor_signals():
    while True:
        try:
            signals = plc.batchread_wordunits('D5105', 2)
            on_signal, off_signal = signals

            if on_signal == 1:
                on_time = plc.batchread_wordunits('D5103', 1)[0]
                store_oee_data(cycle_on_time=on_time)

            if off_signal == 1:
                off_time = plc.batchread_wordunits('D5104', 1)[0]
                store_oee_data(cycle_off_time=off_time)

            time.sleep(1)

        except Exception as e:
            print(f"[Signal Monitor Error] {e}")
            time.sleep(3)
            connect_plc()

def store_oee_data(cycle_on_time=None, cycle_off_time=None):
    global last_entered_part_number
    try:
        values = plc.batchread_wordunits('D5102', 1)  # OK production
        temps = plc.batchread_wordunits('D5111', 5)   # Temp values

        data = OEEDashboardData(
            part_number=last_entered_part_number or " ",  # 🔁 Reuse last entered part
            cycle_time=0.0,
            plan_production_qty=0,
            rejection_qty=0,
            ok_production=int(values[0]),
            cycle_on_time=cycle_on_time or 0.0,
            cycle_off_time=cycle_off_time or 0.0,
            convection_temp_1=temps[0],
            convection_temp_2=temps[1],
            convection_temp_3=temps[2],
            cooling_temp_1=temps[3],
            cooling_temp_2=temps[4],
            remarks_off_time='idle',
            dft=0.0,
            viscosity=0.0,
            resistivity=0.0,
        )
        data.save()
        print(f"📥 OEE Data Saved for Part: {data.part_number}")

    except Exception as e:
        print(f"[DB Save Error] {e}")

def start_async_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(toggle_heartbeat())

def run():
    print("🚀 Starting PLC monitor...")
    connect_plc()

    # Start heartbeat
    threading.Thread(target=start_async_loop, daemon=True).start()

    # Start signal monitor
    threading.Thread(target=monitor_signals, daemon=True).start()

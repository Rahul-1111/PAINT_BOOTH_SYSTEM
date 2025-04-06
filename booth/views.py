from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import OEEDashboardData
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

def dashboard_form_view(request):
    if request.method == "POST":
        data = request.POST

        # Get current datetime
        now = timezone.now()

        # Determine shift from time
        hour = now.hour
        if 6 <= hour < 14:
            shift = "Shift 1"
        elif 14 <= hour < 22:
            shift = "Shift 2"
        else:
            shift = "Shift 3"

        try:
            record = OEEDashboardData(
                date=now.date(),
                time=now.time(),
                shift=shift,
                part_number=data.get('part_number'),
                cycle_time=float(data.get('cycle_time') or 0),
                plan_production_qty=int(data.get('planned_qty') or 0),
                rejection_qty=int(data.get('rejection_qty') or 0),
                remarks_off_time=data.get('remarks_off_time'),
                dft=float(data.get('dft') or 0),
                viscosity=float(data.get('viscosity') or 0),
                resistivity=float(data.get('resistivity') or 0),
                # These fields will be fetched from PLC in background task or updated later
                ok_production=0,
                cycle_on_time=0,
                cycle_off_time=0,
                convection_temp_1=0,
                convection_temp_2=0,
                convection_temp_3=0,
                cooling_temp_1=0,
                cooling_temp_2=0,
            )
            record.save()
            return redirect("booth:oee_form")

        except Exception as e:
            print(f"Error saving form data: {e}")
            return render(request, "booth/oee_form.html", {"error": "Invalid input or server error."})

    return render(request, "booth/oee_form.html")

def fetch_torque_data(request):
    recent_records = OEEDashboardData.objects.order_by("-date", "-time")[:50]  # limit to latest 50 records
    data = []

    for record in recent_records:
        oee = calculate_oee(record)
        data.append({
            "part_number": record.part_number,
            "date": record.date.strftime("%Y-%m-%d"),
            "time": record.time.strftime("%H:%M:%S"),
            "shift": record.shift,
            "load_time": record.cycle_on_time,
            "cycle_time": record.cycle_time,
            "stop_time": record.cycle_off_time,
            "availability": oee["availability"],
            "performance": oee["performance"],
            "quality": oee["quality"],
            "oee": oee["oee"],
        })

    return JsonResponse({"data": data})

def calculate_oee(record):
    try:
        total_time = record.cycle_on_time + record.cycle_off_time
        total_production = record.ok_production + record.rejection_qty
        planned_production_time = record.plan_production_qty * record.cycle_time

        availability = (record.cycle_on_time / total_time) * 100 if total_time else 0
        performance = (record.ok_production * record.cycle_time / record.cycle_on_time) * 100 if record.cycle_on_time else 0
        quality = (record.ok_production / total_production) * 100 if total_production else 0

        oee = (availability * performance * quality) / 10000

        return {
            "availability": round(availability, 2),
            "performance": round(performance, 2),
            "quality": round(quality, 2),
            "oee": round(oee, 2)
        }
    except Exception as e:
        return {
            "availability": 0,
            "performance": 0,
            "quality": 0,
            "oee": 0
        }


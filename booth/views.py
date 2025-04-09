from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from .models import OEEDashboardData
from .plc_oee import handle_recipe_change_with_input

# Utility functions
def get_float(value):
    try:
        return float(value or 0)
    except (ValueError, TypeError):
        return 0.0

def get_int(value):
    try:
        return int(value or 0)
    except (ValueError, TypeError):
        return 0

# Dashboard form view
def dashboard_form_view(request):
    last_part = request.session.get('last_part_number', '')

    if request.method == "POST":
        data = request.POST
        now = timezone.now()

        # Determine shift
        hour = now.hour
        if 6 <= hour < 14:
            shift = "Shift 1"
        elif 14 <= hour < 22:
            shift = "Shift 2"
        else:
            shift = "Shift 3"

        part_number = data.get('part_number')

        try:
            existing = OEEDashboardData.objects.filter(
                date=now.date(),
                shift=shift,
                part_number=part_number
            ).first()

            if existing:
                existing.cycle_time = get_float(data.get('cycle_time'))
                existing.plan_production_qty = get_int(data.get('planned_qty'))
                existing.rejection_qty = get_int(data.get('rejection_qty'))
                existing.remarks_off_time = data.get('remarks_off_time')
                existing.dft = get_float(data.get('dft'))
                existing.viscosity = get_float(data.get('viscosity'))
                existing.resistivity = get_float(data.get('resistivity'))
                existing.time = now.time()
                existing.save()
            else:
                OEEDashboardData.objects.create(
                    date=now.date(),
                    time=now.time(),
                    shift=shift,
                    part_number=part_number,
                    cycle_time=get_float(data.get('cycle_time')),
                    plan_production_qty=get_int(data.get('planned_qty')),
                    rejection_qty=get_int(data.get('rejection_qty')),
                    remarks_off_time=data.get('remarks_off_time'),
                    dft=get_float(data.get('dft')),
                    viscosity=get_float(data.get('viscosity')),
                    resistivity=get_float(data.get('resistivity')),
                    ok_production=0,
                    cycle_on_time=0,
                    cycle_off_time=0,
                    convection_temp_1=0,
                    convection_temp_2=0,
                    convection_temp_3=0,
                    cooling_temp_1=0,
                    cooling_temp_2=0,
                )

            request.session['last_part_number'] = part_number
            return redirect("booth:oee_form")

        except Exception as e:
            print(f"Error saving form data: {e}")
            return render(request, "booth/oee_form.html", {
                "error": "Invalid input or server error.",
                "last_part_number": last_part
            })

    return render(request, "booth/oee_form.html", {
        "last_part_number": last_part
    })

# Fetch last 50 records
def fetch_torque_data(request):
    recent_records = OEEDashboardData.objects.order_by("-date", "-time")[:50]
    data = []

    for record in recent_records:
        oee = calculate_oee(record)
        total_production = get_int(record.ok_production) + get_int(record.rejection_qty)

        data.append({
            "id": record.id,
            "part_number": record.part_number,
            "date": record.date.strftime("%Y-%m-%d"),
            "time": record.time.strftime("%H:%M:%S"),
            "shift": record.shift,
            "load_time": record.cycle_on_time,
            "cycle_time": record.cycle_time,
            "stop_time": record.cycle_off_time,
            "plan_production_qty": record.plan_production_qty,
            "ok_production": record.ok_production,
            "rejection_qty": record.rejection_qty,
            "total_production": total_production,
            "shift_down_time": record.shift_down_time,
            "remarks_off_time": record.remarks_off_time,
            "dft": record.dft,
            "viscosity": record.viscosity,
            "resistivity": record.resistivity,
            "convection_temp_1": record.convection_temp_1,
            "convection_temp_2": record.convection_temp_2,
            "convection_temp_3": record.convection_temp_3,
            "cooling_temp_1": record.cooling_temp_1,
            "cooling_temp_2": record.cooling_temp_2,
            "availability": oee["availability"],
            "performance": oee["performance"],
            "quality": oee["quality"],
            "oee": oee["oee"],
        })

    return JsonResponse({"data": data})

# OEE Calculation Logic
def calculate_oee(record):
    try:
        total_time = get_float(record.cycle_on_time) + get_float(record.cycle_off_time)
        total_production = get_int(record.ok_production) + get_int(record.rejection_qty)

        availability = (get_float(record.cycle_on_time) / total_time) * 100 if total_time else 0
        performance = (get_int(record.ok_production) * get_float(record.cycle_time) / get_float(record.cycle_on_time)) * 100 if get_float(record.cycle_on_time) else 0
        quality = (get_int(record.ok_production) / total_production) * 100 if total_production else 0

        oee = (availability * performance * quality) / 10000

        return {
            "availability": round(availability, 2),
            "performance": round(performance, 2),
            "quality": round(quality, 2),
            "oee": round(oee, 2)
        }
    except Exception:
        return {
            "availability": 0,
            "performance": 0,
            "quality": 0,
            "oee": 0
        }

# Edit record
def edit_oee_record(request, pk):
    record = get_object_or_404(OEEDashboardData, pk=pk)

    if request.method == "POST":
        data = request.POST
        try:
            record.part_number = data.get('part_number')
            record.cycle_time = get_float(data.get('cycle_time'))
            record.plan_production_qty = get_int(data.get('planned_qty'))
            record.rejection_qty = get_int(data.get('rejection_qty'))
            record.remarks_off_time = data.get('remarks_off_time')
            record.dft = get_float(data.get('dft'))
            record.viscosity = get_float(data.get('viscosity'))
            record.resistivity = get_float(data.get('resistivity'))
            record.save()

            return redirect("booth:oee_form")
        except Exception as e:
            print(f"Error updating record: {e}")
            return render(request, "booth/oee_form_edit.html", {"error": "Invalid input", "record": record})

    return render(request, "booth/oee_form_edit.html", {"record": record})

# Get list of distinct part numbers
def get_part_numbers(request):
    part_numbers = OEEDashboardData.objects.values_list('part_number', flat=True).distinct()
    return JsonResponse({'part_numbers': list(part_numbers)})

# Manual entry update
def manual_entry_view(request):
    if request.method == 'POST':
        part_number = request.POST.get('part_number')
        existing_record = OEEDashboardData.objects.filter(part_number=part_number).order_by('-id').first()

        if existing_record:
            existing_record.cycle_time = get_float(request.POST.get('cycle_time'))
            existing_record.plan_production_qty = get_int(request.POST.get('planned_qty'))
            existing_record.rejection_qty = get_int(request.POST.get('rejection_qty'))
            existing_record.remarks_off_time = request.POST.get('remarks_off_time')
            existing_record.dft = get_float(request.POST.get('dft'))
            existing_record.viscosity = get_float(request.POST.get('viscosity'))
            existing_record.resistivity = get_float(request.POST.get('resistivity'))
            existing_record.date = timezone.now().date()
            existing_record.time = timezone.now().time()
            existing_record.save()
        else:
            print(f"No existing record for part number {part_number}")

        return redirect("booth:oee_form")

    return render(request, "booth/oee_form.html")

# PLC recipe change trigger
@csrf_exempt
def recipe_input_view(request):
    if request.method == 'POST':
        part_number = request.POST.get('part_number', '').strip()
        if part_number:
            handle_recipe_change_with_input(part_number)
            request.session['last_part_number'] = part_number
        return redirect(request.META.get('HTTP_REFERER', '/'))

from booth.plc_oee import handle_recipe_change_with_input

def submit_part_number(request):
    if request.method == 'POST':
        part_number = request.POST.get('part_number')
        handle_recipe_change_with_input(part_number)
        return JsonResponse({'message': 'Part number set successfully'})

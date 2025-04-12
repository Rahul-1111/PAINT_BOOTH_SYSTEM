from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from .models import OEEDashboardData
from .plc_oee import handle_recipe_change_with_input
from django.db.models import F
from datetime import datetime

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
                existing.cycle_on_time = get_float(data.get('cycle_on_time'))
                existing.cycle_off_time = get_float(data.get('cycle_off_time'))
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
                    cycle_on_time=get_float(data.get('cycle_on_time')),
                    cycle_off_time=get_float(data.get('cycle_off_time')),
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

def fetch_torque_data(request):
    data = OEEDashboardData.objects.all().order_by('-id')[:50]  # or any limit you want
    json_data = [
        {
            'date': str(d.date),
            'time': str(d.time),
            'shift': d.shift,
            'part_number': d.part_number,
            'cycle_time': d.cycle_time,
            'plan_production_qty': d.plan_production_qty,
            'rejection_qty': d.rejection_qty,
            'ok_production': d.ok_production,
            'total_production': d.total_production,
            'shift_down_time': d.shift_down_time,
            'cycle_off_time': d.cycle_off_time,
            'cycle_on_time': d.cycle_on_time,
            'remarks_off_time': d.remarks_off_time,
            'dft': d.dft,
            'viscosity': d.viscosity,
            'resistivity': d.resistivity,
            'convection_temp_1': d.convection_temp_1,
            'convection_temp_2': d.convection_temp_2,
            'convection_temp_3': d.convection_temp_3,
            'cooling_temp_1': d.cooling_temp_1,
            'cooling_temp_2': d.cooling_temp_2,
        }
        for d in data
    ]
    return JsonResponse({'data': json_data})
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
            record.cycle_on_time = get_float(data.get('cycle_on_time'))
            record.cycle_off_time = get_float(data.get('cycle_off_time'))
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

# Manual Entry
def manual_entry_view(request):
    if request.method == 'POST':
        part_number = request.POST.get('part_number')
        selected_date = request.POST.get('selected_date')
        selected_time = request.POST.get('selected_time')  # Format: 'HH:MM:SS'
        selected_shift = request.POST.get('selected_shift')

        try:
            existing_record = OEEDashboardData.objects.filter(
                part_number=part_number,
                date=selected_date,
                time__startswith=selected_time,
                shift=selected_shift
            ).first()

            if existing_record:
                existing_record.cycle_time = get_float(request.POST.get('cycle_time'))
                existing_record.plan_production_qty = get_int(request.POST.get('planned_qty'))
                existing_record.rejection_qty = get_int(request.POST.get('rejection_qty'))
                existing_record.remarks_off_time = request.POST.get('remarks_off_time')
                existing_record.dft = get_float(request.POST.get('dft'))
                existing_record.viscosity = get_float(request.POST.get('viscosity'))
                existing_record.resistivity = get_float(request.POST.get('resistivity'))
                existing_record.save()
                print(f"✅ Updated record: {existing_record.part_number} at {existing_record.time}")
            else:
                print(f"❌ No match found for part={part_number}, date={selected_date}, time={selected_time}, shift={selected_shift}")

        except Exception as e:
            print(f"[Manual Entry Error] {e}")

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

def submit_part_number(request):
    if request.method == 'POST':
        part_number = request.POST.get('part_number')
        handle_recipe_change_with_input(part_number)
        return JsonResponse({'message': 'Part number set successfully'})

# Filtered options for date, time, and shift based on part_number
def get_filters_for_part(request):
    part_number = request.GET.get("part_number", "").strip()
    if part_number:
        records = OEEDashboardData.objects.filter(part_number=part_number)
        dates = records.values_list('date', flat=True).distinct().order_by('-date')
        times = records.values_list('time', flat=True).distinct().order_by('-time')
        shifts = records.values_list('shift', flat=True).distinct()

        return JsonResponse({
            "dates": [str(d) for d in dates],
            "times": [t.strftime('%H:%M:%S') for t in times],
            "shifts": list(shifts)
        })

    return JsonResponse({"dates": [], "times": [], "shifts": []})

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

def dashboard_form_view(request):
    last_part = request.session.get('last_part_number', '')

    if request.method == "POST":
        data = request.POST
        now = timezone.now()

        part_number = data.get('part_number')
        shift = data.get('shift')  # <<< directly use posted shift

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
                existing.time = now.time()
                existing.cycle_on_time = get_float(data.get('cycle_on_time'))
                existing.cycle_off_time = get_float(data.get('cycle_off_time'))
                existing.save()
            else:
                OEEDashboardData.objects.create(
                    date=now.date(),
                    time=now.time(),
                    shift=shift,  # <<< use posted shift
                    part_number=part_number,
                    cycle_time=get_float(data.get('cycle_time')),
                    plan_production_qty=get_int(data.get('planned_qty')),
                    rejection_qty=get_int(data.get('rejection_qty')),
                    remarks_off_time=data.get('remarks_off_time'),
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
    data = OEEDashboardData.objects.all().order_by('-id')
    json_data = [
        {
            'date': str(d.date),
            'time': d.time.strftime('%H:%M:%S'),
            'shift': d.shift,
            'part_number': d.part_number,
            'cycle_time': d.cycle_time,
            'plan_production_qty': d.plan_production_qty,
            'rejection_qty': d.rejection_qty,
            'ok_production': d.ok_production,
            'total_production': d.total_production,
            'cycle_off_time': d.cycle_off_time,
            'cycle_on_time': d.cycle_on_time,
            'remarks_off_time': d.remarks_off_time,
            'paint_batch_no': d.paint_batch_no,
            'thinner_batch_no': d.thinner_batch_no,
            'raw_paint_viscosity': d.raw_paint_viscosity,
            'paint_viscosity': d.paint_viscosity,
            'seam_dft': d.seam_dft,
            'mid_1_dft': d.mid_1_dft,
            'mid_2_dft': d.mid_2_dft,
            'upper_1_dft': d.upper_1_dft,
            'upper_2_dft': d.upper_2_dft,
            'dome_dft': d.dome_dft,
        }
        for d in data
    ]
    return JsonResponse({'data': json_data})

from django.views.decorators.http import require_GET

@require_GET
def fetch_latest_record(request):
    latest = OEEDashboardData.objects.last()
    if not latest:
        return JsonResponse({'data': None})

    data = {
        'date': str(latest.date),
        'time': latest.time.strftime('%H:%M:%S'),
        'shift': latest.shift,
        'part_number': latest.part_number,
        'cycle_time': latest.cycle_time,
        'plan_production_qty': latest.plan_production_qty,
        'rejection_qty': latest.rejection_qty,
        'ok_production': latest.ok_production,
        'total_production': latest.total_production,
        'cycle_off_time': latest.cycle_off_time,
        'cycle_on_time': latest.cycle_on_time,
        'remarks_off_time': latest.remarks_off_time,
        'convection_temp_1': latest.convection_temp_1,
        'convection_temp_2': latest.convection_temp_2,
        'convection_temp_3': latest.convection_temp_3,
        'cooling_temp_1': latest.cooling_temp_1,
        'cooling_temp_2': latest.cooling_temp_2,
    }
    return JsonResponse({'data': data})

# OEE Calculation Logic
def calculate_oee(record):
    try:
        total_time = get_float(record.cycle_on_time) + get_float(record.cycle_off_time)
        total_production = get_int(record.total_production)
        rejection_qty = get_int(record.rejection_qty)
        ok_production = total_production - rejection_qty

        availability = (get_float(record.cycle_on_time) / total_time) * 100 if total_time else 0
        performance = (ok_production * get_float(record.cycle_time) / get_float(record.cycle_on_time)) * 100 if get_float(record.cycle_on_time) else 0
        quality = (ok_production / total_production) * 100 if total_production else 0

        oee = (availability * performance * quality) / 10000

        return {
            "availability": round(availability, 2),
            "performance": round(performance, 2),
            "quality": round(quality, 2),
            "oee": round(oee, 2)
        }
    except Exception as e:
        print(f"Error in calculate_oee: {e}")
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
            rejection_qty = get_int(data.get('rejection_qty'))
            total_production = get_int(data.get('total_production'))
            ok_production = total_production - rejection_qty

            record.part_number = data.get('part_number')
            record.cycle_time = get_float(data.get('cycle_time'))
            record.plan_production_qty = get_int(data.get('planned_qty'))
            record.rejection_qty = rejection_qty
            record.total_production = total_production
            record.ok_production = ok_production
            record.remarks_off_time = data.get('remarks_off_time')
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

                # Additional manual fields
                existing_record.paint_batch_no = request.POST.get('paint_batch_no')
                existing_record.thinner_batch_no = request.POST.get('thinner_batch_no')
                existing_record.raw_paint_viscosity = get_float(request.POST.get('raw_paint_viscosity'))
                existing_record.paint_viscosity = get_float(request.POST.get('paint_viscosity'))
                existing_record.seam_dft = get_int(request.POST.get('seam_dft'))
                existing_record.mid_1_dft = get_int(request.POST.get('mid_1_dft'))
                existing_record.mid_2_dft = get_int(request.POST.get('mid_2_dft'))
                existing_record.upper_1_dft = get_int(request.POST.get('upper_1_dft'))
                existing_record.upper_2_dft = get_int(request.POST.get('upper_2_dft'))
                existing_record.dome_dft = get_int(request.POST.get('dome_dft'))

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

from django.db.models.functions import Round  # For rounding float fields

def get_filters_for_part(request):
    selected_date = request.GET.get('selected_date')
    selected_shift = request.GET.get('selected_shift')
    part_number = request.GET.get('part_number')
    selected_time = request.GET.get('selected_time')

    response_data = {}

    # Handle the case when no parameters are provided (initial load of dates)
    if not any([selected_date, selected_shift, part_number, selected_time]):
        dates = OEEDashboardData.objects.values_list('date', flat=True).distinct()
        response_data['dates'] = sorted(list(set(str(d) for d in dates)))

    elif selected_date and not selected_shift:
        # Return unique shifts for the selected date
        shifts = OEEDashboardData.objects.filter(
            date=selected_date
        ).values_list('shift', flat=True).distinct()
        response_data['shifts'] = sorted(list(set(s for s in shifts)))

    elif selected_date and selected_shift and not part_number:
        # Return unique part numbers for the selected date and shift
        part_numbers = OEEDashboardData.objects.filter(
            date=selected_date,
            shift=selected_shift
        ).values_list('part_number', flat=True).distinct()
        response_data['part_numbers'] = sorted(list(set(p for p in part_numbers)))

    elif selected_date and selected_shift and part_number and not selected_time:
        # Return unique times that have non-empty and non-zero cycle_off_time
        times = OEEDashboardData.objects.filter(
            date=selected_date,
            shift=selected_shift,
            part_number=part_number
        ).exclude(cycle_off_time__isnull=True).exclude(cycle_off_time=0).values_list('time', flat=True).distinct()
        response_data['times'] = sorted(list(set(str(t) for t in times)))

    elif selected_date and selected_shift and part_number and selected_time:
        # Return cycle_off_time values for the selected combination
        off_times = OEEDashboardData.objects.filter(
            date=selected_date,
            shift=selected_shift,
            part_number=part_number,
            time=selected_time
        ).values_list('cycle_off_time', flat=True).distinct()
        rounded_off_times = sorted(list(set(round(float(t), 2) for t in off_times if t is not None)))
        response_data['cycle_off_times'] = rounded_off_times

    return JsonResponse(response_data)
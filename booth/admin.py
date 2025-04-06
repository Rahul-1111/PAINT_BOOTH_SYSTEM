from django.contrib import admin
from .models import OEEDashboardData

@admin.register(OEEDashboardData)
class OEEDashboardAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'time', 'shift',
        'part_number', 'cycle_time', 'plan_production_qty',
        'rejection_qty', 'ok_production', 'total_production',
        'shift_down_time', 'cycle_off_time', 'cycle_on_time',
        'remarks_off_time', 'dft', 'viscosity', 'resistivity',
        'convection_temp_1', 'convection_temp_2', 'convection_temp_3',
        'cooling_temp_1', 'cooling_temp_2',
    ]

    list_filter = ('date', 'shift', 'part_number')
    search_fields = ('part_number', 'remarks_off_time')
    ordering = ('-date', '-time')
    date_hierarchy = 'date'

    fieldsets = (
        ('Basic Info', {
            'fields': ('shift', 'part_number')  # removed 'date', 'time'
        }),
        ('Production Data (User + PLC)', {
            'fields': (
                'cycle_time', 'plan_production_qty',
                'ok_production', 'rejection_qty', 'total_production'
            )
        }),
        ('Downtime & Cycle Timing', {
            'fields': (
                'shift_down_time', 'cycle_off_time',
                'cycle_on_time', 'remarks_off_time'
            )
        }),
        ('Quality Measurements', {
            'fields': ('dft', 'viscosity', 'resistivity')
        }),
        ('Temperature Monitoring', {
            'fields': (
                'convection_temp_1', 'convection_temp_2', 'convection_temp_3',
                'cooling_temp_1', 'cooling_temp_2'
            )
        }),
    )

    # Now date, time, total_production, shift_down_time are read-only
    readonly_fields = ('date', 'time', 'total_production', 'shift_down_time')

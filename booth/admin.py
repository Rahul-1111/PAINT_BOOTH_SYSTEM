from django.contrib import admin
from .models import OEEDashboardData

@admin.register(OEEDashboardData)
class OEEDashboardAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'date', 'time', 'shift',
        'part_number', 'cycle_time', 'plan_production_qty',
        'rejection_qty', 'ok_production', 'total_production',
        'cycle_off_time', 'cycle_on_time',
        'remarks_off_time', 'paint_batch_no', 'thinner_batch_no',
        'raw_paint_viscosity', 'paint_viscosity',
        'seam_dft', 'mid_1_dft', 'mid_2_dft',
        'upper_1_dft', 'upper_2_dft', 'dome_dft',
        'convection_temp_1', 'convection_temp_2', 'convection_temp_3',
        'cooling_temp_1', 'cooling_temp_2',
    ]

    list_filter = ('date', 'shift', 'part_number')
    search_fields = ('part_number', 'remarks_off_time')
    ordering = ('-date', '-time')
    date_hierarchy = 'date'

    fieldsets = (
        ('Basic Info', {
            'fields': ('shift', 'part_number')
        }),
        ('Production Data (User + PLC)', {
            'fields': (
                'cycle_time', 'plan_production_qty',
                'ok_production', 'rejection_qty', 'total_production'
            )
        }),
        ('Downtime & Cycle Timing', {
            'fields': (
                'cycle_off_time', 'cycle_on_time', 'remarks_off_time'
            )
        }),
        ('Paint Quality Data', {
            'fields': (
                'paint_batch_no', 'thinner_batch_no',
                'raw_paint_viscosity', 'paint_viscosity',
                'seam_dft', 'mid_1_dft', 'mid_2_dft',
                'upper_1_dft', 'upper_2_dft', 'dome_dft'
            )
        }),
        ('Temperature Monitoring', {
            'fields': (
                'convection_temp_1', 'convection_temp_2', 'convection_temp_3',
                'cooling_temp_1', 'cooling_temp_2'
            )
        }),
    )

    readonly_fields = ('date', 'time', 'total_production')

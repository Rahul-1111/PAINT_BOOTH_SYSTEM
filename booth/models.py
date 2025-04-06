from django.db import models

class OEEDashboardData(models.Model):
    # Auto-generated
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)
    shift = models.CharField(max_length=20, default="Shift 1")

    # Input from User
    part_number = models.CharField(max_length=100, help_text="Part Number (Recipe)")
    cycle_time = models.FloatField(help_text="Cycle time for part (in seconds)")
    plan_production_qty = models.IntegerField()
    rejection_qty = models.IntegerField()

    # From PLC
    ok_production = models.IntegerField()
    cycle_off_time = models.FloatField(help_text="Cycle OFF Time (seconds)")
    cycle_on_time = models.FloatField(help_text="Cycle ON Time (seconds)")
    convection_temp_1 = models.FloatField(help_text="Convection zone 1 Temp")
    convection_temp_2 = models.FloatField(help_text="Convection zone 2 Temp")
    convection_temp_3 = models.FloatField(help_text="Convection zone 3 Temp")
    cooling_temp_1 = models.FloatField(help_text="Cooling zone 1 Temp")
    cooling_temp_2 = models.FloatField(help_text="Cooling zone 2 Temp")

    # Calculated in Software
    total_production = models.IntegerField(editable=False)
    shift_down_time = models.FloatField(editable=False, help_text="Per shift down time in seconds")

    # Remarks (Dropdown/User Input)
    remarks_off_time = models.CharField(
        max_length=255,
        choices=[
            ('breakdown', 'Breakdown'),
            ('maintenance', 'Maintenance'),
            ('idle', 'Idle'),
            ('others', 'Others')
        ],
        help_text="Remarks for OFF Time"
    )

    # Manual User Inputs
    dft = models.FloatField(help_text="DFT")
    viscosity = models.FloatField(help_text="Viscosity")
    resistivity = models.FloatField(help_text="Resistivity")

    def save(self, *args, **kwargs):
        self.total_production = self.ok_production + self.rejection_qty
        self.shift_down_time = self.cycle_off_time  # You can enhance this logic further
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.date} - {self.shift} - {self.part_number}"

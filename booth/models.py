from django.db import models

class OEEDashboardData(models.Model):
    id = models.AutoField(primary_key=True)
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

    # Remarks (Dropdown/User Input)
    remarks_off_time = models.CharField(
        max_length=255,
        help_text="Remarks for OFF Time"
    )

    # New fields to be added
    paint_batch_no = models.CharField(max_length=255, blank=True, null=True)  # Alphanumeric
    thinner_batch_no = models.CharField(max_length=255, blank=True, null=True)  # Alphanumeric
    raw_paint_viscosity = models.FloatField(blank=True, null=True)  # Floating
    paint_viscosity = models.FloatField(blank=True, null=True)  # Floating
    seam_dft = models.IntegerField(blank=True, null=True)  # Integer
    mid_1_dft = models.IntegerField(blank=True, null=True)  # Integer
    mid_2_dft = models.IntegerField(blank=True, null=True)  # Integer
    upper_1_dft = models.IntegerField(blank=True, null=True)  # Integer
    upper_2_dft = models.IntegerField(blank=True, null=True)  # Integer
    dome_dft = models.IntegerField(blank=True, null=True)  # Integer

    def save(self, *args, **kwargs):
        self.total_production = self.ok_production + self.rejection_qty
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.date} - {self.shift} - {self.part_number}"

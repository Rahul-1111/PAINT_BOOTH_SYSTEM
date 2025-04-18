# Generated by Django 4.2.18 on 2025-04-14 12:04

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("booth", "0003_alter_oeedashboarddata_id"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="oeedashboarddata",
            name="dft",
        ),
        migrations.RemoveField(
            model_name="oeedashboarddata",
            name="resistivity",
        ),
        migrations.RemoveField(
            model_name="oeedashboarddata",
            name="viscosity",
        ),
        migrations.AddField(
            model_name="oeedashboarddata",
            name="dome_dft",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="oeedashboarddata",
            name="mid_1_dft",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="oeedashboarddata",
            name="mid_2_dft",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="oeedashboarddata",
            name="paint_batch_no",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="oeedashboarddata",
            name="paint_viscosity",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="oeedashboarddata",
            name="raw_paint_viscosity",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="oeedashboarddata",
            name="seam_dft",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="oeedashboarddata",
            name="thinner_batch_no",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="oeedashboarddata",
            name="upper_1_dft",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="oeedashboarddata",
            name="upper_2_dft",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]

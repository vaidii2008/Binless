from django.db import migrations, models


def mark_sample_shops_as_simulated(apps, schema_editor):
    """Flag the shops that already run on simulated sales: the sample organisation's."""
    Store = apps.get_model("orders", "Store")
    Store.objects.filter(organisation__is_sample=True).update(is_simulated=True)


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0004_require_organisation"),
    ]

    operations = [
        migrations.AddField(
            model_name="store",
            name="is_simulated",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(mark_sample_shops_as_simulated, migrations.RunPython.noop),
    ]

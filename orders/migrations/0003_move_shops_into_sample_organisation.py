from django.db import migrations

# Copied rather than imported, so the migration keeps working if the constant changes.
SAMPLE_ORGANISATION_NAME = "Sample organisation (simulated)"


def move_shops_into_sample_organisation(apps, schema_editor):
    """Give every existing shop, product and forecast to the sample organisation."""
    Organisation = apps.get_model("accounts", "Organisation")
    Store = apps.get_model("orders", "Store")
    Product = apps.get_model("orders", "Product")
    Forecast = apps.get_model("orders", "Forecast")
    if not Store.objects.exists():
        return
    organisation, _ = Organisation.objects.get_or_create(
        name=SAMPLE_ORGANISATION_NAME, defaults={"is_sample": True}
    )
    Store.objects.filter(organisation__isnull=True).update(organisation=organisation)
    for store in Store.objects.all():
        Product.objects.filter(store=store).update(
            organisation_id=store.organisation_id
        )
    for product in Product.objects.all():
        Forecast.objects.filter(product=product).update(
            organisation_id=product.organisation_id
        )


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0002_add_organisation"),
    ]

    operations = [
        migrations.RunPython(
            move_shops_into_sample_organisation, migrations.RunPython.noop
        ),
    ]

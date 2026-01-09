from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0005_add_flash_sale_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='flash_sale_price',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Special price for flash sale', max_digits=10, null=True),
        ),
    ]

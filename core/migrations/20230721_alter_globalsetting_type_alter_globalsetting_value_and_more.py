# Generated by Django 4.2.3 on 2023-10-08 14:53

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "20230720_alter_emailmessage_template_context"),
    ]

    operations = [
        migrations.AlterField(
            model_name="globalsetting",
            name="type",
            field=models.CharField(
                choices=[("bool", "Boolean"), ("int", "Integer"), ("str", "String")],
                max_length=127,
            ),
        ),
        migrations.AlterField(
            model_name="globalsetting",
            name="value",
            field=models.CharField(max_length=254),
        ),
        migrations.AlterField(
            model_name="orgsetting",
            name="default",
            field=models.CharField(max_length=254),
        ),
        migrations.AlterField(
            model_name="orgsetting",
            name="type",
            field=models.CharField(
                choices=[("bool", "Boolean"), ("int", "Integer"), ("str", "String")],
                max_length=127,
            ),
        ),
        migrations.AlterField(
            model_name="orguserorgusersetting",
            name="value",
            field=models.CharField(max_length=254),
        ),
        migrations.AlterField(
            model_name="orgusersetting",
            name="default",
            field=models.CharField(max_length=254),
        ),
        migrations.AlterField(
            model_name="orgusersetting",
            name="owner_value",
            field=models.CharField(
                help_text="The value that will be enforced for the org owner over all other defaults and values.",
                max_length=254,
            ),
        ),
        migrations.AlterField(
            model_name="orgusersetting",
            name="type",
            field=models.CharField(
                choices=[("bool", "Boolean"), ("int", "Integer"), ("str", "String")],
                max_length=127,
            ),
        ),
        migrations.AlterField(
            model_name="orgusersettingdefault",
            name="value",
            field=models.CharField(max_length=254),
        ),
        migrations.AlterField(
            model_name="overriddenorgsetting",
            name="value",
            field=models.CharField(max_length=254),
        ),
        migrations.AlterField(
            model_name="planorgsetting",
            name="value",
            field=models.CharField(max_length=254),
        ),
    ]

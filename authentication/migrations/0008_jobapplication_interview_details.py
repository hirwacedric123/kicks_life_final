# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0007_post_inventory'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobapplication',
            name='interview_details',
            field=models.TextField(blank=True, help_text='Details about interview time, place, etc.', null=True),
        ),
        migrations.AlterField(
            model_name='jobapplication',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('under_review', 'Under Review'), ('pre_interview', 'Pre-Interview Assessment'), ('interview', 'Interview'), ('accepted', 'Accepted'), ('rejected', 'Rejected')], default='pending', max_length=20),
        ),
    ] 
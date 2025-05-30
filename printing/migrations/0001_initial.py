# Generated by Django 5.2.1 on 2025-05-27 19:53

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Building',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=10, unique=True, verbose_name='Код здания')),
                ('name', models.CharField(max_length=255, verbose_name='Название')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Дата создания')),
            ],
            options={
                'verbose_name': 'Здание',
                'verbose_name_plural': 'Здания',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Computer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Имя компьютера')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Дата создания')),
            ],
            options={
                'verbose_name': 'Компьютер',
                'verbose_name_plural': 'Компьютеры',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=20, unique=True, verbose_name='Код подразделения')),
                ('name', models.CharField(max_length=255, verbose_name='Название')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Дата создания')),
            ],
            options={
                'verbose_name': 'Отдел',
                'verbose_name_plural': 'Отделы',
                'ordering': ['code'],
            },
        ),
        migrations.CreateModel(
            name='Port',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Название порта')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Дата создания')),
            ],
            options={
                'verbose_name': 'Порт',
                'verbose_name_plural': 'Порты',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='PrinterModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, unique=True, verbose_name='Код модели')),
                ('manufacturer', models.CharField(max_length=100, verbose_name='Производитель')),
                ('model', models.CharField(max_length=50, verbose_name='Модель')),
                ('is_color', models.BooleanField(default=False, verbose_name='Цветной')),
                ('is_duplex', models.BooleanField(default=False, verbose_name='Двусторонняя печать')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Дата создания')),
            ],
            options={
                'verbose_name': 'Модель принтера',
                'verbose_name_plural': 'Модели принтеров',
                'ordering': ['manufacturer', 'model'],
            },
        ),
        migrations.CreateModel(
            name='Printer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Название принтера')),
                ('room_number', models.CharField(max_length=10, verbose_name='Номер помещения')),
                ('printer_index', models.IntegerField(verbose_name='Индекс принтера')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Дата создания')),
                ('building', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='printers', to='printing.building', verbose_name='Здание')),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='printers', to='printing.department', verbose_name='Отдел')),
                ('model', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='printers', to='printing.printermodel', verbose_name='Модель принтера')),
            ],
            options={
                'verbose_name': 'Принтер',
                'verbose_name_plural': 'Принтеры',
                'ordering': ['name'],
                'unique_together': {('building', 'room_number', 'printer_index')},
            },
        ),
        migrations.CreateModel(
            name='PrintEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document_id', models.IntegerField(db_index=True, verbose_name='ID документа')),
                ('document_name', models.CharField(max_length=512, verbose_name='Название документа')),
                ('job_id', models.CharField(db_index=True, max_length=64, verbose_name='ID задания')),
                ('timestamp', models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name='Время печати')),
                ('byte_size', models.IntegerField(verbose_name='Размер в байтах')),
                ('pages', models.IntegerField(verbose_name='Количество страниц')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Дата создания')),
                ('computer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='print_events', to='printing.computer', verbose_name='Компьютер')),
                ('port', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='print_events', to='printing.port', verbose_name='Порт')),
                ('printer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='print_events', to='printing.printer', verbose_name='Принтер')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='print_events', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Событие печати',
                'verbose_name_plural': 'События печати',
                'ordering': ['-timestamp'],
                'indexes': [models.Index(fields=['document_id'], name='printing_pr_documen_bab57f_idx'), models.Index(fields=['job_id'], name='printing_pr_job_id_af4892_idx'), models.Index(fields=['timestamp'], name='printing_pr_timesta_956b59_idx')],
            },
        ),
    ]

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('taxi', '0003_questiontestresult'),
    ]

    operations = [
        migrations.CreateModel(
            name='MockExam',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.DateTimeField(auto_now_add=True)),
                ('end_time', models.DateTimeField(blank=True, null=True)),
                ('total_questions', models.IntegerField(default=0)),
                ('correct_answers', models.IntegerField(default=0)),
                ('completed', models.BooleanField(default=False)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mock_exams', to='taxi.category')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mock_exams', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-start_time'],
            },
        ),
        migrations.CreateModel(
            name='MockExamQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.IntegerField()),
                ('is_correct', models.BooleanField(blank=True, null=True)),
                ('mock_exam', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exam_questions', to='taxi.mockexam')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='taxi.question')),
                ('selected_choices', models.ManyToManyField(blank=True, related_name='selected_in_mock_exams', to='taxi.choice')),
            ],
            options={
                'ordering': ['order'],
                'unique_together': {('mock_exam', 'order')},
            },
        ),
    ]

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("configs", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ApprovalRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("config_version", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="approval_request",
                    to="configs.configversion",
                )),
                ("jira_issue_key", models.CharField(blank=True, default="", max_length=50)),
                ("jira_issue_id", models.CharField(blank=True, default="", max_length=50)),
                ("jira_issue_url", models.URLField(blank=True, default="")),
                ("status", models.CharField(
                    choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
                    db_index=True,
                    default="pending",
                    max_length=20,
                )),
                ("submitted_by", models.CharField(max_length=255)),
                ("reviewed_by", models.CharField(blank=True, default="", max_length=255)),
                ("submission_notes", models.TextField(blank=True, default="")),
                ("review_comment", models.TextField(blank=True, default="")),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"db_table": "approval_requests"},
        ),
    ]

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="JiraUser",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("jira_account_id", models.CharField(db_index=True, max_length=255, unique=True)),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("display_name", models.CharField(max_length=255)),
                ("avatar_url", models.URLField(blank=True, default="")),
                ("jira_groups", models.JSONField(default=list)),
                ("jira_project_roles", models.JSONField(default=list)),
                ("configsphere_role", models.CharField(
                    choices=[
                        ("viewer", "Viewer"),
                        ("operator", "Operator"),
                        ("approver", "Approver"),
                        ("admin", "Admin"),
                    ],
                    default="viewer",
                    max_length=20,
                )),
                ("role_override", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("last_synced_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "jira_users", "ordering": ["email"]},
        ),
        migrations.CreateModel(
            name="JiraRoleMapping",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("jira_entity_type", models.CharField(
                    choices=[("group", "Jira Group"), ("project_role", "Jira Project Role")],
                    max_length=20,
                )),
                ("jira_entity_name", models.CharField(max_length=255)),
                ("configsphere_role", models.CharField(
                    choices=[
                        ("viewer", "Viewer"),
                        ("operator", "Operator"),
                        ("approver", "Approver"),
                        ("admin", "Admin"),
                    ],
                    max_length=20,
                )),
                ("priority", models.PositiveIntegerField(default=100)),
            ],
            options={
                "db_table": "jira_role_mappings",
                "ordering": ["priority"],
                "unique_together": {("jira_entity_type", "jira_entity_name")},
            },
        ),
        migrations.CreateModel(
            name="RefreshToken",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("jti", models.CharField(db_index=True, max_length=255, unique=True)),
                ("jira_user", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="refresh_tokens",
                    to="users.jirauser",
                )),
                ("expires_at", models.DateTimeField()),
                ("revoked", models.BooleanField(db_index=True, default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "refresh_tokens"},
        ),
    ]

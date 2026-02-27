import uuid
from django.db import models


class Company(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
    )

    name = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "companies"

    def __str__(self):
        return self.name


class User(models.Model):

    class Role(models.TextChoices):
        PARENT_ADMIN = "PARENT_ADMIN", "Parent Admin"
        CHILD_USER = "CHILD_USER", "Child User"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="users",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.email
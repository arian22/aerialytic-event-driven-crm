import uuid
from django.db import models


class Lead(models.Model):

    class Status(models.TextChoices):
        NEW = "NEW", "New"
        QUALIFIED = "QUALIFIED", "Qualified"
        CONTACTED = "CONTACTED", "Contacted"
        REJECTED = "REJECTED", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)
    email = models.EmailField()

    status = models.CharField(max_length=20, choices=Status.choices, default="NEW")

    company_id = models.UUIDField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "leads"
        unique_together = ("email", "company_id")

    def __str__(self):
        return self.name
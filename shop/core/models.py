from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField("создано", db_index=True, auto_now_add=True)
    updated_at = models.DateTimeField("обновлено", auto_now=True)

    class Meta:
        abstract = True

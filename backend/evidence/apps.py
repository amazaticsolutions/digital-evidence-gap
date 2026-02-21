"""Evidence app configuration."""

from django.apps import AppConfig


class EvidenceConfig(AppConfig):
    default_auto_field = 'django_mongodb_backend.fields.ObjectIdAutoField'
    name = 'evidence'
    verbose_name = 'Evidence Management'
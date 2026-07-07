from django.db import models  # noqa: F401

# This app is aggregation-only — it has no models of its own; it reads from
# employees, leave, attendance, recruitment, performance, training, assets,
# and disciplinary.

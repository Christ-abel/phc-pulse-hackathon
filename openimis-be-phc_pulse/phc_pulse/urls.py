from django.urls import path

from . import views

# Mounted by openIMIS core at /{SITE_ROOT}phc_pulse/ (module name from
# openimis.json, underscore not hyphen) -- final path is
# /{SITE_ROOT}phc_pulse/webhook/chw-sync/, not the "/phc-pulse/..." path
# assumed in the original plan.
urlpatterns = [
    path("webhook/chw-sync/", views.chw_sync_webhook, name="phc_pulse_chw_sync_webhook"),
]

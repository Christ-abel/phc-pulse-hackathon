from django.apps import apps
from django.test import TestCase


class PhcPulseModuleLoadedTest(TestCase):
    def test_module_registered_with_django(self):
        self.assertTrue(apps.is_installed("phc_pulse"))

import datetime

from django.test import TestCase
from django.urls import reverse

from accounts.models import ClientProfile, LawyerProfile, User
from .models import Case


class CaseAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser('admin', '', 'Admin@123')
        cls.admin.role = User.Role.ADMIN
        cls.admin.save()

        lu = User.objects.create_user('lw', '', 'pass1234', role=User.Role.LAWYER)
        cls.lawyer = LawyerProfile.objects.create(user=lu)
        cls.lawyer_user = lu

        cu1 = User.objects.create_user('c1', '', 'pass1234', role=User.Role.CLIENT)
        cls.client1 = ClientProfile.objects.create(user=cu1)
        cls.client1_user = cu1
        cu2 = User.objects.create_user('c2', '', 'pass1234', role=User.Role.CLIENT)
        cls.client2 = ClientProfile.objects.create(user=cu2)

        cls.case1 = Case.objects.create(
            case_number='CASE-001', title='Client1 matter', case_type='CIVIL',
            status='OPEN', client=cls.client1, lawyer=cls.lawyer,
            opened_date=datetime.date(2026, 6, 1),
        )
        cls.case2 = Case.objects.create(
            case_number='CASE-002', title='Client2 matter', case_type='CIVIL',
            status='OPEN', client=cls.client2, lawyer=cls.lawyer,
            opened_date=datetime.date(2026, 6, 1),
        )

    def test_admin_sees_all_cases(self):
        self.assertEqual(Case.objects.for_user(self.admin).count(), 2)

    def test_client_sees_only_own_case(self):
        qs = Case.objects.for_user(self.client1_user)
        self.assertEqual(list(qs), [self.case1])

    def test_client_cannot_open_another_clients_case(self):
        self.client.force_login(self.client1_user)
        self.assertEqual(self.client.get(reverse('case_detail', args=[self.case2.pk])).status_code, 404)

    def test_client_cannot_create_cases(self):
        self.client.force_login(self.client1_user)
        self.assertEqual(self.client.get(reverse('case_add')).status_code, 403)

    def test_lawyer_can_create_cases(self):
        self.client.force_login(self.lawyer_user)
        self.assertEqual(self.client.get(reverse('case_add')).status_code, 200)

    def test_search_filters_results(self):
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('case_list'), {'q': 'CASE-001'})
        self.assertContains(resp, 'CASE-001')
        self.assertNotContains(resp, 'CASE-002')

from django.test import TestCase
from django.urls import reverse

from .models import ClientProfile, User


class SignUpTests(TestCase):
    def test_signup_creates_client_and_logs_in(self):
        resp = self.client.post(reverse('signup'), {
            'first_name': 'Nia', 'last_name': 'Verma',
            'email': 'nia@example.com',
            'password1': 'simple123', 'password2': 'simple123',
        })
        self.assertRedirects(resp, reverse('dashboard'))
        user = User.objects.get(email='nia@example.com')
        self.assertEqual(user.role, User.Role.CLIENT)
        self.assertEqual(user.username, 'nia@example.com')  # email is the login id
        self.assertTrue(ClientProfile.objects.filter(user=user).exists())

    def test_role_cannot_be_escalated_via_form(self):
        self.client.post(reverse('signup'), {
            'first_name': 'Mal', 'email': 'mal@example.com',
            'password1': 'simple123', 'password2': 'simple123',
            'role': 'ADMIN', 'is_superuser': 'true',
        })
        user = User.objects.get(email='mal@example.com')
        self.assertEqual(user.role, User.Role.CLIENT)
        self.assertFalse(user.is_superuser)

    def test_duplicate_email_rejected(self):
        data = {'first_name': 'A', 'email': 'dup@example.com',
                'password1': 'simple123', 'password2': 'simple123'}
        self.client.post(reverse('signup'), data)
        self.client.post(reverse('signup'), data)
        self.assertEqual(User.objects.filter(email='dup@example.com').count(), 1)

    def test_short_password_rejected(self):
        self.client.post(reverse('signup'), {
            'first_name': 'S', 'email': 's@example.com',
            'password1': 'ab1', 'password2': 'ab1',
        })
        self.assertFalse(User.objects.filter(email='s@example.com').exists())


class LoginTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('admin', '', 'Admin@123')
        self.admin.role = User.Role.ADMIN
        self.admin.save()

    def test_client_signs_in_with_email(self):
        self.client.post(reverse('signup'), {
            'first_name': 'Nia', 'email': 'nia@example.com',
            'password1': 'simple123', 'password2': 'simple123',
        })
        self.client.logout()
        ok = self.client.post(reverse('login'), {
            'username': 'nia@example.com', 'password': 'simple123',
        })
        self.assertEqual(ok.status_code, 302)

    def test_admin_rejected_from_client_portal(self):
        resp = self.client.post(reverse('login'), {
            'username': 'admin', 'password': 'Admin@123',
        })
        self.assertEqual(resp.status_code, 200)  # re-rendered with error
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_admin_signs_in_at_staff_portal(self):
        resp = self.client.post(reverse('admin_login'), {
            'username': 'admin', 'password': 'Admin@123',
        })
        self.assertEqual(resp.status_code, 302)


class ProfileTests(TestCase):
    def test_client_can_edit_own_profile(self):
        self.client.post(reverse('signup'), {
            'first_name': 'Nia', 'email': 'nia@example.com',
            'password1': 'simple123', 'password2': 'simple123',
        })
        self.client.post(reverse('profile'), {
            'first_name': 'Nia', 'last_name': 'Verma', 'email': 'nia@example.com',
            'phone': '999', 'address': '12 Park', 'company': 'NV Co',
        })
        user = User.objects.get(email='nia@example.com')
        self.assertEqual(user.last_name, 'Verma')
        self.assertEqual(user.client_profile.company, 'NV Co')


class PasswordResetTests(TestCase):
    def test_reset_email_sent(self):
        from django.core import mail
        self.client.post(reverse('signup'), {
            'first_name': 'Nia', 'email': 'nia@example.com',
            'password1': 'simple123', 'password2': 'simple123',
        })
        self.client.logout()
        self.client.post(reverse('password_reset'), {'email': 'nia@example.com'})
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('reset', mail.outbox[0].body.lower())

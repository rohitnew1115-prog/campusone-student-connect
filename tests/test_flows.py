import os
import tempfile
import unittest
from pathlib import Path

import app as campus


class CampusOneFlows(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        campus.DB = root / 'test.sqlite3'
        campus.UPLOADS = root / 'uploads'
        campus.UPLOADS.mkdir()
        os.environ['CAMPUSONE_ADMIN_EMAIL'] = 'admin@campus.test'
        campus.init_db()
        campus.app.config.update(TESTING=True, SECRET_KEY='test-secret')
        self.a = campus.app.test_client()
        self.b = campus.app.test_client()
        self.admin = campus.app.test_client()
        self.register(self.a, 'Avery Student', 'avery@campus.test')
        self.register(self.b, 'Blake Student', 'blake@campus.test')
        self.register(self.admin, 'Campus Admin', 'admin@campus.test')

    def tearDown(self):
        self.temp.cleanup()

    def register(self, client, name, email):
        r = client.post('/api/auth/register', json={'name': name, 'email': email, 'password': 'long-test-password', 'confirm_password': 'long-test-password'})
        self.assertEqual(r.status_code, 201, r.get_json())
        return r.get_json()['user']

    def create(self, client, module, title, data=None):
        r = client.post('/api/' + module, json={'title': title, 'data': data or {}})
        self.assertEqual(r.status_code, 201, r.get_json())
        return r.get_json()['item']

    def test_login_profile_and_hash(self):
        self.a.post('/api/auth/logout')
        r = self.a.post('/api/auth/login', json={'email': 'avery@campus.test', 'password': 'long-test-password'})
        self.assertEqual(r.status_code, 200)
        r = self.a.put('/api/profile', json={'department': 'Computing', 'skills': 'Python, UI design', 'interests': 'Robotics'})
        self.assertEqual(r.status_code, 200)
        self.assertIn('Python', r.get_json()['profile']['skills'])
        with campus.app.app_context():
            password_hash = campus.db().execute('select password_hash from users where email=?', ('avery@campus.test',)).fetchone()[0]
        self.assertNotEqual(password_hash, 'long-test-password')

    def test_six_modules_and_student_collaboration(self):
        modules = ['teams', 'tutoring', 'lost-found', 'mentors', 'issues']
        for module in modules:
            listing = self.create(self.a, module, 'A shared ' + module + ' listing', {'description': 'Campus details'})
            results = self.b.get('/api/' + module + '?q=shared').get_json()['items']
            self.assertTrue(any(item['id'] == listing['id'] for item in results))
            sent = self.b.post(f"/api/{module}/{listing['id']}/requests", json={'message': 'Please connect', 'datetime': '2026-12-01T10:00'})
            self.assertEqual(sent.status_code, 201, sent.get_json())
            request_id = sent.get_json()['request_id']
            inbox = self.a.get('/api/requests').get_json()['requests']
            self.assertTrue(any(row['id'] == request_id for row in inbox))
            response = self.a.put('/api/requests/' + str(request_id), json={'status': 'Confirmed'})
            self.assertEqual(response.status_code, 200)
            notifications = self.b.get('/api/notifications').get_json()['notifications']
            self.assertTrue(any('confirmed' in n['message'].lower() for n in notifications))
        admin_post = self.create(self.admin, 'opportunities', 'Campus hackathon', {'category': 'Hackathons'})
        self.assertTrue(self.b.get('/api/opportunities?q=hackathon').get_json()['items'])
        denied = self.a.post('/api/opportunities', json={'title': 'Unauthorized event', 'data': {}})
        self.assertEqual(denied.status_code, 403)
        save = self.b.post(f"/api/opportunities/{admin_post['id']}/bookmark")
        self.assertTrue(save.get_json()['saved'])
        self.assertTrue(self.b.get('/api/opportunities?saved=1').get_json()['items'])

    def test_admin_issue_status_and_user_controls(self):
        issue = self.create(self.a, 'issues', 'Broken classroom light', {'location': 'Room 5'})
        self.assertTrue(issue['data']['complaint_id'].startswith('CO-'))
        denied = self.b.put('/api/admin/records/' + str(issue['id']), json={'status': 'Resolved'})
        self.assertEqual(denied.status_code, 403)
        updated = self.admin.put('/api/admin/records/' + str(issue['id']), json={'status': 'In Progress', 'note': 'Maintenance assigned'})
        self.assertEqual(updated.status_code, 200)
        history = self.a.get('/api/records/' + str(issue['id']) + '/history').get_json()['history']
        self.assertEqual(history[-1]['status'], 'In Progress')
        student_id = self.b.get('/api/auth/me').get_json()['user']['id']
        self.assertTrue(self.admin.put('/api/admin/users/' + str(student_id), json={'active': False}).get_json()['ok'])
        self.assertEqual(self.b.get('/api/auth/me').status_code, 401)

    def test_team_creation_and_named_member_invitation(self):
        self.a.put('/api/profile', json={'skills': 'Python, Web design', 'department': 'Computing'})
        self.b.put('/api/profile', json={'skills': 'Python, UI design', 'department': 'Computing'})
        search = self.a.get('/api/students?q=Python').get_json()['students']
        self.assertTrue(any(s['name'] == 'Blake Student' for s in search))
        team = self.create(self.a, 'teams', 'Campus app team', {'listing_type': 'Create a team', 'required_skills': ['Python'], 'team_size': '4'})
        invite = self.a.post(f"/api/teams/{team['id']}/invitations", json={'user_id': self.b.get('/api/auth/me').get_json()['user']['id'], 'role': 'Backend developer'})
        self.assertEqual(invite.status_code, 201, invite.get_json())
        incoming = self.b.get('/api/requests').get_json()['requests']
        team_invite = next(r for r in incoming if r.get('is_team_invitation'))
        self.assertEqual(team_invite['title'], 'Campus app team')
        answer = self.b.put(f"/api/teams/invitations/{invite.get_json()['invitation_id']}", json={'status': 'Accepted'})
        self.assertEqual(answer.status_code, 200)
        roster = self.a.get(f"/api/teams/{team['id']}/members").get_json()
        self.assertEqual(roster['members'][0]['status'], 'Accepted')
        self.assertEqual(roster['members'][0]['role'], 'Backend developer')

    def test_upload_validation_and_health(self):
        self.assertEqual(self.a.get('/api/health').get_json()['database'], 'sqlite3')
        bad = self.b.post('/api/upload', data={'file': (BytesIO(b'not image'), 'payload.exe')}, content_type='multipart/form-data')
        self.assertEqual(bad.status_code, 400)


from io import BytesIO

if __name__ == '__main__':
    unittest.main()

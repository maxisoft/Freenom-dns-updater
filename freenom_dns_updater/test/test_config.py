import pathlib
import shutil
import tempfile
import unittest

from freenom_dns_updater import Config

default_file = u"""
login: yourlogin@somemail.domain
password: yourpassword
"""


class ConfigTest(unittest.TestCase):
    def setUp(self):
        self.working_dir = pathlib.Path(tempfile.mkdtemp("ConfigTest"))
        self.config_file = self.working_dir / 'freenom.yml'
        with self.config_file.open('w') as f:
            f.write(default_file)
        self.config = Config(str(self.config_file))

    def tearDown(self):
        shutil.rmtree(str(self.working_dir.absolute()))

    def test_reload(self):
        self.config.reload(str(self.config_file))
        self.test_get()

    def test_get(self):
        self.assertEqual('yourlogin@somemail.domain', self.config['login'])

    def test_set(self):
        self.config['login'] = 'test1'
        self.assertEqual('test1', self.config['login'])

    def test_login_get(self):
        self.assertEqual('yourlogin@somemail.domain', self.config.login)

    def test_password_get(self):
        self.assertEqual('yourpassword', self.config.password)

    def test_save(self):
        self.test_set()
        self.config.save()
        config = Config(str(self.config_file))
        self.assertEqual(self.config, config)


if __name__ == '__main__':
    unittest.main()

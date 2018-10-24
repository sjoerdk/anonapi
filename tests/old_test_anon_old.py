import unittest
from unittest.mock import Mock, patch

from API.anonymization import AnonCommandLineParser, AnonClientSettingsFromFile, \
    AnonClientSettingsException, DefaultAnonClientSettings, AnonClientTool, RemoteAnonServer, \
    AnonCommandLineParserException
from tests import TestResourcesFolder, FileTemplate


class Test(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @patch('sys.stdout')  # catch print statements to keep test output clean
    @patch('anonymization.anon.AnonCommandLineParser.get_status')  # catch print statements to keep test output clean
    def test_command_line_tool_basic(self, mock_get_status, mock_stdout):
        """Test some commands"""
        client_tool_mock = Mock()
        settings = DefaultAnonClientSettings()
        parser = AnonCommandLineParser(client_tool=client_tool_mock, settings=settings)
        parser.execute_command("status".split(" "))

        # status should have been printed, nothing should have crashed
        mock_get_status.assert_called()

    @patch('sys.stdout')  # catch print statements to keep test output clean
    def test_command_line_tool_status_without_active_server(self, mock_stdout):
        """Error found live, making sure its fixed """
        client_tool_mock = Mock()
        settings = DefaultAnonClientSettings()
        settings.active_server = None
        parser = AnonCommandLineParser(client_tool=client_tool_mock, settings=settings)

        # this should not crash
        parser.get_status()

    @patch('sys.stdout')  # catch print statements to keep test output clean
    def test_command_line_tool_add_remove_server(self, mock_stdout):
        """Test some commands"""
        client_tool_mock = Mock()
        settings = DefaultAnonClientSettings()
        parser = AnonCommandLineParser(client_tool=client_tool_mock, settings=settings)

        # this should not crash
        parser.execute_command("server list".split(" "))
        mock_stdout.write.assert_called()

        # there should be one
        self.assertEqual(len(parser.settings.servers), 1)

        # add a server
        parser.execute_command("server add server2 https://something.com".split(" "))

        # now there should be two servers
        self.assertEqual(len(parser.settings.servers), 2)

        # remove the original server called 'test'
        parser.execute_command("server remove test".split(" "))

        # now there should be one again
        self.assertEqual(len(parser.settings.servers), 1)

        # the original server was the active one. so now what is active server?
        test = 1

    @patch('anonymization.anon.AnonCommandLineParser.server_status')
    def test_command_line_tool_server_status(self, mock_server_status, ):
        """Test checking status"""
        client_tool = AnonClientTool(username="test", token="testpass")
        settings = DefaultAnonClientSettings()
        settings.servers.append(RemoteAnonServer(name='sandbox', url='https://umcradanonp11.umcn.nl/sandbox'))
        settings.servers.append(RemoteAnonServer(name='wrong', url='https://umcradanonp11.umcn.nl/non_existant'))
        settings.servers.append(RemoteAnonServer(name='p01', url='https://umcradanonp11.umcn.nl/p01'))

        parser = AnonCommandLineParser(client_tool=client_tool, settings=settings)

        # this should not crash
        parser.execute_command("server status p01".split(" "))
        mock_server_status.assert_called()

    @patch('sys.stdout')  # catch print statements to keep test output clean
    def test_command_line_tool_job_info(self, mock_std_out):
        """Test checking status"""
        client_tool = Mock()
        client_tool.get_job_info.return_value = "{'job_id': 1}"  # return some fake job info
        settings = DefaultAnonClientSettings()
        settings.servers.append(RemoteAnonServer(name='sandbox', url='https://umcradanonp11.umcn.nl/sandbox'))

        parser = AnonCommandLineParser(client_tool=client_tool, settings=settings)

        parser.execute_command("server activate sandbox".split(" "))
        parser.execute_command("job info 10".split(" "))

        # nothing should have crashed, and something should have been written. Better then nothing.
        mock_std_out.write.assert_called()

    @patch('sys.stdout')  # catch print statements to keep test output clean
    def test_command_line_tool_activate_server(self, mock_std_out):
        """Test activating a server"""
        client_tool = Mock()
        settings = DefaultAnonClientSettings()
        settings.servers.append(RemoteAnonServer(name='sandbox', url='https://umcradanonp11.umcn.nl/sandbox'))
        settings.servers.append(RemoteAnonServer(name='sandbox2', url='https://umcradanonp11.umcn.nl/sandbox2'))

        parser = AnonCommandLineParser(client_tool=client_tool, settings=settings)

        # activate a known server should not crash
        parser.execute_command("server activate sandbox".split(" "))
        mock_std_out.write.assert_called()

        # activate a non-existant server name should just give a nice message, no crashes
        mock_std_out.reset_mock()
        parser.execute_command("server activate yomomma".split(" "))
        mock_std_out.write.assert_called()

    @patch('anonymization.anon.WebAPIClient')
    @patch('sys.stdout')  # catch print statements to keep test output clean
    def test_command_line_tool_job_functions(self, mock_std_out, mock_client):
        """Check a whole lot of commands without doing actual queries

        Kind of a mop up test trying to get coverage up"""
        client_tool = AnonClientTool(username="test", token="testpass")
        settings = DefaultAnonClientSettings()
        parser = AnonCommandLineParser(client_tool=client_tool, settings=settings)

        parser.execute_command("job info 1234".split(" "))
        mock_client.assert_called()

        mock_client.reset_mock()
        parser.execute_command("job reset 1234".split(" "))
        mock_client.assert_called()

        mock_client.reset_mock()
        parser.execute_command("job cancel 1234".split(" "))
        mock_client.assert_called()

        mock_client.reset_mock()
        before = settings.active_server
        settings.active_server = None
        parser.execute_command("job cancel 1234".split(" "))
        mock_client.assert_not_called()
        mock_std_out.write.assert_called()
        settings.active_server = before

    @patch('anonymization.anon.WebAPIClient')
    @patch('sys.stdout')  # catch print statements to keep test output clean
    def test_command_line_tool_functions_with_data(self, mock_std_out, mock_client):
        """ Exercise some extra bits of the code that require actual data to be got from web API client"""
        client_tool = AnonClientTool(username="test", token="testpass")
        settings = DefaultAnonClientSettings()
        parser = AnonCommandLineParser(client_tool=client_tool, settings=settings)

        mock_client.reset_mock()
        # when asking client, return the following minimal example of some valid job info
        mock = Mock()
        mock.get.return_value = {1: {'job_id': 1, 'date': 'some date', 'status': 'DONE',
                                                 'files_downloaded': 400, 'files_processed': None,
                                                 'user_name': 'testuser'}}
        client_tool.get_client = lambda url: mock
        parser.execute_command("server jobs".split(" "))
        mock.get.assert_called()

    @patch('anonymization.anon.WebAPIClient')
    @patch('sys.stdout')  # catch print statements to keep test output clean
    def test_command_line_tool_server_functions(self, mock_std_out, mock_client):
        """Check a whole lot of commands without doing actual queries

        Kind of a mop up test trying to get coverage up"""
        client_tool = AnonClientTool(username="test", token="testpass")
        settings = DefaultAnonClientSettings()
        parser = AnonCommandLineParser(client_tool=client_tool, settings=settings)

        parser.execute_command("server jobs".split(" "))
        mock_client.assert_called()

        mock_client.reset_mock()
        parser.execute_command("server jobs p01".split(" "))
        # server p01 does not exist. Error about this should be printed before ever hitting any client
        mock_client.assert_not_called()

        mock_client.reset_mock()
        # server test exists (from DefaultAnonClientSetttings) so this should work
        parser.execute_command("server status test".split(" "))
        mock_client.assert_called()

        mock_client.reset_mock()
        # server test exists (from DefaultAnonClientSetttings) so this should work
        parser.execute_command("status".split(" "))
        mock_client.assert_not_called()

    def test_get_server_when_none_is_active(self):
        """In certain cases active server can be None. handle this gracefully
        """
        client_tool = Mock()
        settings = DefaultAnonClientSettings()
        settings.active_server = None
        parser = AnonCommandLineParser(client_tool=client_tool, settings=settings)

        #Calling for server here should fail because there is no active server
        self.assertRaises(AnonCommandLineParserException, parser.get_server_or_active_server, None)

    @patch('anonymization.anon.WebAPIClient')
    @patch('sys.stdout')  # catch print statements to keep test output clean
    def test_command_line_tool_user_functions(self, mock_std_out, mock_client):
        client_tool = AnonClientTool(username="test", token="testpass")
        settings = DefaultAnonClientSettings()
        parser = AnonCommandLineParser(client_tool=client_tool, settings=settings)

        parser.execute_command("user set_username test_changed".split(" "))
        self.assertEqual(settings.user_name, "test_changed")




class TestSettings(unittest.TestCase):

    def setUp(self):
        self.test_resources = TestResourcesFolder(calling_file_path=__file__, relative_folder='resources')
        self.templates = []

    def tearDown(self):
        for template in self.templates:
            template.clean_all_copies()

    def test_settings_load(self):
        org_settings_file = self.test_resources.get_path("test_settings/settings.yml")
        settings_file_template = FileTemplate(file_path=org_settings_file)
        self.templates.append(settings_file_template)

        settings_file = settings_file_template.get_copy()
        settings = AnonClientSettingsFromFile(settings_file)

        self.assertEqual(settings.user_name, 'kees')
        self.assertEqual(settings.user_token, 'token')
        self.assertEqual(settings.active_server.name, 'sandbox')
        self.assertEqual(len(settings.servers), 2)

    def test_settings_save(self):
        """Load settings, change, save and see whether they have been saved
        """
        org_settings_file = self.test_resources.get_path("test_settings/settings.yml")
        settings_file_template = FileTemplate(file_path=org_settings_file)
        self.templates.append(settings_file_template)

        settings_file = settings_file_template.get_copy()
        settings = AnonClientSettingsFromFile(settings_file)

        self.assertEqual(settings.user_name, 'kees')
        self.assertEqual(settings.user_token, 'token')
        self.assertEqual(settings.active_server.name, 'sandbox')
        self.assertEqual(len(settings.servers), 2)

        settings.user_name = 'other_username'
        settings.save()

        new_settings = AnonClientSettingsFromFile(filename=settings_file)
        self.assertEqual(new_settings.user_name, 'other_username')

    def test_settings_save_with_none_active(self):
        """ fixing a bug found live: saving when active server = none
        """
        org_settings_file = self.test_resources.get_path("test_settings/settings.yml")
        settings_file_template = FileTemplate(file_path=org_settings_file)
        self.templates.append(settings_file_template)

        settings_file = settings_file_template.get_copy()
        settings = AnonClientSettingsFromFile(settings_file)

        # It is possible that there is no active server. You should still be able to save
        settings.active_server = None
        settings.save()

        # And also load
        new_settings = AnonClientSettingsFromFile(filename=settings_file)
        self.assertEqual(new_settings.active_server, None)

    def test_settings_load_error(self):
        """ Poor mans YAML validation should at least raise some informative exception when a key is missing from
        settings
        """
        org_settings_file = self.test_resources.get_path("test_settings/settings_wrong.yml")
        settings_file_template = FileTemplate(file_path=org_settings_file)
        self.templates.append(settings_file_template)

        settings_file = settings_file_template.get_copy()
        self.assertRaises(AnonClientSettingsException, AnonClientSettingsFromFile, settings_file)

    def test_settings_load_error2(self):
        """ Some more easy errors to make when manually editing settings file
        """
        org_settings_file = self.test_resources.get_path("test_settings/settings_wrong_2.yml")
        settings_file_template = FileTemplate(file_path=org_settings_file)
        self.templates.append(settings_file_template)

        settings_file = settings_file_template.get_copy()
        self.assertRaises(AnonClientSettingsException, AnonClientSettingsFromFile, settings_file)




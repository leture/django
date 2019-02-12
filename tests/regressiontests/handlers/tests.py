from django.conf import settings
from django.core.handlers.wsgi import WSGIHandler
from django.test import RequestFactory
from django.test.utils import override_settings
from django.utils import six
from django.utils import unittest


class HandlerTests(unittest.TestCase):

    def test_lock_safety(self):
        """
        Tests for bug #11193 (errors inside middleware shouldn't leave
        the initLock locked).
        """
        # Mangle settings so the handler will fail
        old_middleware_classes = settings.MIDDLEWARE_CLASSES
        settings.MIDDLEWARE_CLASSES = 42
        # Try running the handler, it will fail in load_middleware
        handler = WSGIHandler()
        self.assertEqual(handler.initLock.locked(), False)
        try:
            handler(None, None)
        except:
            pass
        self.assertEqual(handler.initLock.locked(), False)
        # Reset settings
        settings.MIDDLEWARE_CLASSES = old_middleware_classes

    def test_bad_path_info(self):
        """Tests for bug #15672 ('request' referenced before assignment)"""
        environ = RequestFactory().get('/').environ
        environ['PATH_INFO'] = '\xed'
        handler = WSGIHandler()
        response = handler(environ, lambda *a, **k: None)
        self.assertEqual(response.status_code, 400)


@override_settings(ROOT_URLCONF='handlers.urls')
class HandlerNotFoundTest(unittest.TestCase):

    def test_invalid_urls(self):
        response = self.client.get('~%A9helloworld')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.context['request_path'], '/%7E%25A9helloworld')

        response = self.client.get('d%aao%aaw%aan%aal%aao%aaa%aad%aa/')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.context['request_path'], '/d%25AAo%25AAw%25AAn%25AAl%25AAo%25AAa%25AAd%25AA')

        response = self.client.get('/%E2%99%E2%99%A5/')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.context['request_path'], '/%25E2%2599%E2%99%A5/')

        response = self.client.get('/%E2%98%8E%E2%A9%E2%99%A5/')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.context['request_path'], '/%E2%98%8E%25E2%25A9%E2%99%A5/')

    def test_environ_path_info_type(self):
        environ = RequestFactory().get('/%E2%A8%87%87%A5%E2%A8%A0').environ
        self.assertIsInstance(environ['PATH_INFO'], six.text_type)

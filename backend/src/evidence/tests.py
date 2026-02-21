from django.test import TestCase, Client
import os

from multimedia_rag import config


class VideoProxyTests(TestCase):
    def setUp(self):
        os.makedirs(config.TEMP_VIDEO_DIR, exist_ok=True)
        self.file_path = os.path.join(config.TEMP_VIDEO_DIR, 'example_test.mp4')
        # Create a small dummy file to simulate a video
        with open(self.file_path, 'wb') as f:
            f.write(b'0' * 1024 * 50)  # 50 KB
        self.client = Client()

    def tearDown(self):
        try:
            os.remove(self.file_path)
        except Exception:
            pass

    def _get_response_bytes(self, resp):
        """Collect bytes from a regular or streaming response."""
        if hasattr(resp, 'streaming_content'):
            return b''.join(resp.streaming_content)
        return resp.content

    def test_proxy_returns_full_file(self):
        url = f'/api/evidence/video-proxy/?video_url={self.file_path}'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(int(resp.get('Content-Length', 0)), os.path.getsize(self.file_path))
        body = self._get_response_bytes(resp)
        self.assertGreater(len(body), 0)

    def test_proxy_supports_range(self):
        url = f'/api/evidence/video-proxy/?video_url={self.file_path}'
        headers = {'HTTP_RANGE': 'bytes=0-1023'}
        resp = self.client.get(url, **headers)
        self.assertIn(resp.status_code, (200, 206))
        # If 206, Content-Range should be present
        if resp.status_code == 206:
            self.assertIn('Content-Range', resp)
        body = self._get_response_bytes(resp)
        self.assertGreaterEqual(len(body), 0)

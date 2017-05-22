from functools import wraps
from pprint import pprint
from time import sleep
import unittest
from unittest.mock import patch

from requests import Response

from pipeline_base import TestPipelineBase
from scrapemeagain.pipeline import EXIT
from scrapemeagain.utils.http import get


def queue_waiter(f):
    """Give queues some time to end properly."""
    @wraps(f)
    def with_sleep(*args, **kwargs):
        retval = f(*args, **kwargs)
        sleep(0.1)
        return retval

    return with_sleep


def create_responses(urls, statuses):
    responses = []

    for fake_url, fake_status in zip(urls, statuses):
        response = Response()
        response.url = fake_url
        response.status_code = fake_status

        responses.append(response)

    return responses


class TestPipeline(TestPipelineBase):
    def test_change_ip(self):
        """Test 'change_ip' simply sets a new IP via Tor."""
        self.pipeline.change_ip()

        self.pipeline.tor_ip_changer.get_new_ip.assert_called_once_with()

    def test_produce_list_urls(self):
        """Test 'produce_list_urls' populates 'url_queue'."""
        mock_urls = ['url1', 'url2', 'url3']
        mock_generate_list_urls = self.pipeline.scraper.generate_list_urls
        mock_generate_list_urls.return_value = mock_urls

        self.pipeline.produce_list_urls()

        mock_generate_list_urls.assert_called_once_with()
        for mock_url in mock_urls:
            self.pipeline.url_queue.put.assert_any_call(mock_url)

    def test_produce_item_urls(self):
        """Test 'produce_item_urls' populates 'url_queue'."""
        mock_urls = ['url1', 'url2', 'url3']
        mock_get_item_urls = self.pipeline.databaser.get_item_urls
        mock_get_item_urls.return_value = mock_urls

        self.pipeline.produce_item_urls()

        mock_get_item_urls.assert_called_once_with()
        for mock_url in mock_urls:
            self.pipeline.url_queue.put.assert_any_call(mock_url)

    def test_classify_response_ok(self):
        """Test '_classify_response' puts an OK response to
        'response_queue'."""
        mock_response_ok = Response()
        mock_response_ok.url = 'url1'
        mock_response_ok.status_code = 200

        self.pipeline._classify_response(mock_response_ok)

        self.pipeline.response_queue.put.assert_called_once_with(
            mock_response_ok
        )
        with self.assertRaises(AssertionError):
            self.pipeline.url_queue.put.assert_called_once_with(
                mock_response_ok.url
            )

    def test_classify_response_not_ok(self):
        """Test '_classify_response' puts a non OK response URL back to
        'url_queue'."""
        mock_response_not_ok = Response()
        mock_response_not_ok.url = 'url1'
        mock_response_not_ok.status_code = 500

        self.pipeline._classify_response(mock_response_not_ok)

        self.pipeline.url_queue.put.assert_called_once_with(
            mock_response_not_ok.url
        )
        with self.assertRaises(AssertionError):
            self.pipeline.response_queue.put.assert_called_once_with(
                mock_response_not_ok
            )

    @patch('scrapemeagain.pipeline.logging')
    @patch('scrapemeagain.pipeline.Pipeline._classify_response')
    def test_actually_get_html(self, mock_classify_response, mock_logging):
        """Test '_actually_get_html' fires requests for given URLs."""
        mock_urls = ['url1', 'url2', 'url3']
        mock_url_statuses = [200, 500, 200]
        self.mock_map.return_value = create_responses(
            mock_urls, mock_url_statuses
        )

        self.pipeline._actually_get_html(mock_urls)

        self.mock_map.assert_called_once_with(get, mock_urls)
        self.assertEqual(mock_classify_response.call_count, len(mock_urls))
        self.pipeline.requesting_in_progress.set.assert_called_once_with()
        self.pipeline.requesting_in_progress.clear.assert_called_once_with()
        with self.assertRaises(AssertionError):
            mock_logging.exception.assert_called_once_with(
                'Failed scraping URLs'
            )

    @patch('scrapemeagain.pipeline.logging')
    def test_actually_get_html_fails(self, mock_logging):
        """Test '_actually_get_html' logs an exception message on fail."""
        self.mock_map.side_effect = ValueError

        self.pipeline._actually_get_html(None)

        self.mock_map.assert_called_once_with(get, None)
        self.pipeline.requesting_in_progress.set.assert_called_once_with()
        self.pipeline.requesting_in_progress.clear.assert_called_once_with()
        mock_logging.exception.assert_called_once_with('Failed scraping URLs')

    @patch('scrapemeagain.pipeline.Pipeline._actually_get_html')
    @patch('scrapemeagain.pipeline.Pipeline.change_ip')
    def test_get_html(self, mock_change_ip, mock_actually_get_html):
        """Test 'get_html' pupulates and passes URL bulks for processing."""
        mock_urls = ['url1', 'url2', 'url3']
        self.pipeline.url_queue.get.side_effect = mock_urls + [EXIT]
        self.pipeline.processes = len(mock_urls)

        self.pipeline.get_html()

        # 4 = len(mock_urls) + EXIT
        self.assertEqual(self.pipeline.url_queue.get.call_count, 4)

        mock_change_ip.assert_called_once_with()
        mock_actually_get_html.assert_called_once_with(mock_urls)


if __name__ == '__main__':
    unittest.main()

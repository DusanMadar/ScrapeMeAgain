import unittest
from unittest.mock import patch

from requests import Response

from pipeline_base import TestPipelineBase
from scrapemeagain.pipeline import EXIT
from scrapemeagain.utils.http import get


def create_responses(mock_urls, mock_statuses):
    responses = []

    for mock_url, mock_status in zip(mock_urls, mock_statuses):
        response = Response()
        response.url = mock_url
        response.status_code = mock_status

        responses.append(response)

    return responses


class TestPipeline(TestPipelineBase):
    @patch('scrapemeagain.pipeline.Event')
    @patch('scrapemeagain.pipeline.Pool')
    @patch('scrapemeagain.pipeline.Queue')
    def test_prepare_multiprocessing(self, mock_queue, mock_pool, mock_event):
        """Test 'prepare_multiprocessing' initializes all necessary
        multiprocessing objects.
        """
        self.pipeline.prepare_multiprocessing()

        self.assertTrue(mock_queue.call_count, 3)
        mock_pool.assert_called_once_with(self.pipeline.scrape_processes)
        self.assertTrue(mock_event.call_count, 2)

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
        self.pipeline.pool.map.return_value = create_responses(
            mock_urls, mock_url_statuses
        )

        self.pipeline._actually_get_html(mock_urls)

        self.pipeline.pool.map.assert_called_once_with(get, mock_urls)
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
        self.pipeline.pool.map.side_effect = ValueError

        self.pipeline._actually_get_html(None)

        self.pipeline.pool.map.assert_called_once_with(get, None)
        self.pipeline.requesting_in_progress.set.assert_called_once_with()
        self.pipeline.requesting_in_progress.clear.assert_called_once_with()
        mock_logging.exception.assert_called_once_with('Failed scraping URLs')

    @patch('scrapemeagain.pipeline.Pipeline._actually_get_html')
    @patch('scrapemeagain.pipeline.Pipeline.change_ip')
    def test_get_html(self, mock_change_ip, mock_actually_get_html):
        """Test 'get_html' populates and passes URL bulks for processing."""
        mock_urls = ['url1', 'url2', 'url3']
        self.pipeline.url_queue.get.side_effect = mock_urls + [EXIT]
        self.pipeline.processes = len(mock_urls)

        self.pipeline.get_html()

        # 4 = len(mock_urls) + EXIT
        self.assertEqual(self.pipeline.url_queue.get.call_count, 4)

        mock_change_ip.assert_called_once_with()
        mock_actually_get_html.assert_called_once_with(mock_urls)

    def test_actually_collect_data_list(self):
        """Test '_actually_collect_data' gets item URLs from a list page."""
        mock_item_urls_response = Response()
        mock_item_urls_response.url = 'url?search=1'
        mock_item_urls_response.status_code = 200

        self.pipeline.scraper.list_url_template = 'url?search='
        self.pipeline.scraper.get_item_urls.return_value = {}

        self.pipeline._actually_collect_data(mock_item_urls_response)

        self.pipeline.scraper.get_item_urls.assert_called_once_with(
            mock_item_urls_response
        )
        with self.assertRaises(AssertionError):
            self.pipeline.scraper.get_item_properties.assert_called_once_with()

        self.pipeline.data_queue.put.assert_called_once_with({})
        self.pipeline.scraping_in_progress.set.assert_called_once_with()
        self.pipeline.scraping_in_progress.clear.assert_called_once_with()

    def test_actually_collect_data_item(self):
        """Test '_actually_collect_data' gets item data from items page."""
        mock_item_response = Response()
        mock_item_response.url = 'url-item-1'
        mock_item_response.status_code = 200

        self.pipeline.scraper.list_url_template = 'url?search='
        self.pipeline.scraper.get_item_properties.return_value = {}

        self.pipeline._actually_collect_data(mock_item_response)

        self.pipeline.scraper.get_item_properties.assert_called_once_with(
            mock_item_response
        )
        with self.assertRaises(AssertionError):
            self.pipeline.scraper.get_item_urls.assert_called_once_with()

        self.pipeline.data_queue.put.assert_called_once_with({})
        self.pipeline.scraping_in_progress.set.assert_called_once_with()
        self.pipeline.scraping_in_progress.clear.assert_called_once_with()

    @patch('scrapemeagain.pipeline.logging')
    def test_actually_collect_data_fails(self, mock_logging):
        """Test '_actually_collect_data' logs an exception message on fail."""
        mock_item_response = Response()
        mock_item_response.url = 'url-item-1'
        mock_item_response.status_code = 200

        self.pipeline.data_queue.side_effect = ValueError

        self.pipeline._actually_collect_data(mock_item_response)

        self.pipeline.scraping_in_progress.set.assert_called_once_with()
        self.pipeline.scraping_in_progress.clear.assert_called_once_with()
        mock_logging.exception.assert_called_once_with(
            'Failed processing response for "url-item-1"'
        )

    @patch('scrapemeagain.pipeline.Pipeline._actually_collect_data')
    def test_collect_data(self, mock_actually_collect_data):
        """Test 'collect_data' populates and passes response bulks for
        processing.
        """
        mock_urls = ['url1', 'url2', 'url3']
        mock_url_statuses = [200, 500, 200]
        mock_responses = create_responses(mock_urls, mock_url_statuses)
        self.pipeline.response_queue.get.side_effect = mock_responses + [EXIT]

        self.pipeline.collect_data()

        # 4 = len(mock_responses) + EXIT
        self.assertEqual(self.pipeline.response_queue.get.call_count, 4)

        # 3 = len(mock_responses)
        self.assertEqual(mock_actually_collect_data.call_count, 3)

    def test_actually_store_data_item_urls(self):
        """Test '_actually_store_data' is able to store item URLs."""
        mock_data = [{'url': 'url1'}, {'url': 'url2'}]
        self.pipeline.scrape_processes = len(mock_data)

        self.pipeline._actually_store_data(mock_data)

        self.pipeline.databaser.insert_multiple.assert_called_once_with(
            mock_data, self.pipeline.databaser.item_urls_table
        )
        self.assertEqual(self.pipeline.transaction_items, 2)

    def test_actually_store_data_item_properties(self):
        """Test '_actually_store_data' is able to store item properties."""
        mock_data = {'url': 'url1', 'key': 'value'}

        self.pipeline._actually_store_data(mock_data)

        self.pipeline.databaser.insert.assert_called_once_with(
            mock_data, self.pipeline.databaser.item_data_table
        )
        self.pipeline.databaser.delete_url.assert_called_once_with(
            mock_data['url']
        )
        self.assertEqual(self.pipeline.transaction_items, 2)

    def test_actually_store_data_commits(self):
        """Test '_actually_store_data' commits chnages after a threshold is
        reached and resets the counter.
        """
        self.pipeline.transaction_items_max = 1

        mock_data = {'url': 'url1', 'key': 'value'}

        self.pipeline._actually_store_data(mock_data)

        self.pipeline.databaser.commit.assert_called_once_with()
        self.assertEqual(self.pipeline.transaction_items, 0)

    @patch('scrapemeagain.pipeline.logging')
    def test_actually_store_data_fails(self, mock_logging):
        """Test '_actually_store_data' logs an exception message on fail."""
        self.pipeline._actually_store_data(None)

        mock_logging.exception.assert_called_once_with('Failed storing data')

    @patch('scrapemeagain.pipeline.Pipeline._actually_store_data')
    def test_store_data(self, mock_actually_store_data):
        """Test 'store_data' takes data from the 'data_queue' and pass it to
        '_actually_store_data' (to save it in DB), and all changes are
        committed before exiting.
        """
        mock_data = [
            {'url': 'url1', 'key': 'value'}, {'url': 'url2', 'key': 'value'}
        ]
        self.pipeline.data_queue.get.side_effect = mock_data + [EXIT]

        self.pipeline.store_data()

        # 3 = len(mock_data) + EXIT
        self.assertEqual(self.pipeline.data_queue.get.call_count, 3)

        self.pipeline.databaser.commit.assert_called_once_with()

    def test_exit_workers(self):
        """Test 'exit_workers' passes an EXIT message to all queues."""
        self.pipeline.exit_workers()

        self.pipeline.url_queue.put.assert_called_once_with(EXIT)
        self.pipeline.response_queue.put.assert_called_once_with(EXIT)
        self.pipeline.data_queue.put.assert_called_once_with(EXIT)

    @patch('scrapemeagain.pipeline.time')
    @patch('scrapemeagain.pipeline.Pipeline.exit_workers')
    def test_switch_power(self, mock_exit_workers, mock_time):
        """Test 'switch_power' repeatedly checks the program can end."""
        self.pipeline.url_queue.empty.side_effect = [True, False, True]
        self.pipeline.response_queue.empty.side_effect = [False, True]
        self.pipeline.data_queue.empty.side_effect = [True]
        self.pipeline.requesting_in_progress.is_set.side_effect = [False]
        self.pipeline.scraping_in_progress.is_set.side_effect = [False]

        self.pipeline.switch_power()

        # Both 'url_queue' and 'response_queue' aren't empty once so we expect
        # 'switch_power' will need to wait 2 times.
        self.assertTrue(mock_time.sleep.call_count, 2)

        mock_exit_workers.assert_called_once_with()

    @patch('scrapemeagain.pipeline.Process')
    def test_employ_worker(self, mock_process):
        """Test 'employ_worker' creates and registers a dameon worker."""
        self.pipeline.employ_worker(all)

        mock_process.assert_called_once_with(target=all)
        self.assertTrue(mock_process.daemon)
        mock_process.return_value.start.assert_called_once_with()

        self.assertEqual(len(self.pipeline.workers), 1)

    @patch('scrapemeagain.pipeline.Process')
    def test_release_workers(self, mock_process):
        """Test 'release_workers' waits till a worker is finished."""
        self.pipeline.workers = [mock_process]

        self.pipeline.release_workers()

        mock_process.join.assert_called_once_with()

    @patch('scrapemeagain.pipeline.Pipeline.release_workers')
    @patch('scrapemeagain.pipeline.Pipeline.employ_worker')
    @patch('scrapemeagain.pipeline.Pipeline.get_html')
    def test_get_item_urls(
        self, mock_get_html, mock_employ_worker, mock_release_workers
    ):
        """Test 'get_item_urls' starts all necessary workers and waits till
        they are finished.
        """
        self.pipeline.get_item_urls()

        mock_employ_worker.assert_any_call(self.pipeline.produce_list_urls)
        mock_employ_worker.assert_any_call(self.pipeline.collect_data)
        mock_employ_worker.assert_any_call(self.pipeline.store_data)
        mock_employ_worker.assert_any_call(self.pipeline.switch_power)
        mock_get_html.assert_called_once_with()
        mock_release_workers.assert_called_once_with()

    @patch('scrapemeagain.pipeline.Pipeline.release_workers')
    @patch('scrapemeagain.pipeline.Pipeline.employ_worker')
    @patch('scrapemeagain.pipeline.Pipeline.get_html')
    def test_get_item_properties(
        self, mock_get_html, mock_employ_worker, mock_release_workers
    ):
        """Test 'get_item_properties' starts all necessary workers and waits
        till they are finished.
        """
        self.pipeline.get_item_properties()

        mock_employ_worker.assert_any_call(self.pipeline.produce_item_urls)
        mock_employ_worker.assert_any_call(self.pipeline.collect_data)
        mock_employ_worker.assert_any_call(self.pipeline.store_data)
        mock_employ_worker.assert_any_call(self.pipeline.switch_power)
        mock_get_html.assert_called_once_with()
        mock_release_workers.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()

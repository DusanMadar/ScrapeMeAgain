from unittest.mock import patch, PropertyMock

from requests import Response

from tests.pipeline_base import TestPipelineBase
from scrapemeagain.pipeline import EXIT, DUMP_URLS_BUCKET
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
    @patch("scrapemeagain.pipeline.Value")
    @patch("scrapemeagain.pipeline.Event")
    @patch("scrapemeagain.pipeline.Pool")
    @patch("scrapemeagain.pipeline.Queue")
    def test_prepare_multiprocessing(
        self, mock_queue, mock_pool, mock_event, mock_value
    ):
        """Test 'prepare_multiprocessing' initializes all necessary
        multiprocessing objects.
        """
        self.pipeline.prepare_multiprocessing()

        self.assertTrue(mock_queue.call_count, 3)
        mock_pool.assert_called_once_with(self.pipeline.scrape_processes)
        self.assertTrue(mock_event.call_count, 2)
        self.assertTrue(mock_value.call_count, 2)

    @patch("scrapemeagain.pipeline.get_current_datetime")
    @patch("scrapemeagain.pipeline.logging")
    @patch("scrapemeagain.pipeline.print", create=True)
    def test_inform(self, mock_print, mock_logging, mock_get_current_datetime):
        """Test 'inform' is able to both log and print a message."""
        mock_get_current_datetime.return_value = "a datetime"
        mock_message = "something happened"

        self.pipeline.inform(mock_message)

        mock_logging.info.assert_called_once_with(mock_message)
        mock_print.assert_called_once_with(
            "{0} {1}".format("a datetime", "something happened"), end="\n"
        )

    @patch("scrapemeagain.pipeline.Pipeline.inform")
    def test_inform_progress(self, mock_inform):
        """Test '_inform_progress' prints scraping progress."""
        self.pipeline.urls_processed.value = 10
        self.pipeline.urls_to_process.value = 100

        self.pipeline._inform_progress()

        mock_inform.assert_called_once_with(
            "Processed 10 (10.00%) URLs", log=False, end="\r"
        )

    @patch("scrapemeagain.pipeline.Pipeline.inform")
    def test_inform_progress_fail(self, mock_inform):
        """Test '_inform_progress' does nothing on ZeroDivisionError."""
        self.pipeline.urls_to_process.value = 0

        self.pipeline._inform_progress()

        with self.assertRaises(AssertionError):
            mock_inform.assert_called_once_with()

    @patch("scrapemeagain.pipeline.logging")
    def test_change_ip(self, mock_logging):
        """Test 'change_ip' simply sets a new IP via Tor."""
        self.pipeline.tor_ip_changer.get_new_ip.return_value = "8.8.8.8"

        self.pipeline.change_ip()

        self.pipeline.tor_ip_changer.get_new_ip.assert_called_once_with()
        mock_logging.info.assert_called_once_with(
            "New IP: {new_ip}".format(new_ip="8.8.8.8")
        )

    @patch("scrapemeagain.pipeline.logging")
    def test_change_ip_fail(self, mock_logging):
        """Test 'change_ip' tries again on fail."""
        self.pipeline.tor_ip_changer.get_new_ip.side_effect = [
            ValueError,
            "8.8.8.8",
        ]

        self.pipeline.change_ip()

        self.assertTrue(self.pipeline.tor_ip_changer.get_new_ip.call_count, 2)
        mock_logging.error.assert_called_once_with("Failed setting new IP")
        mock_logging.info.assert_called_once_with(
            "New IP: {new_ip}".format(new_ip="8.8.8.8")
        )

    @patch("scrapemeagain.pipeline.time.sleep")
    @patch("scrapemeagain.pipeline.Pipeline.inform")
    def test_produce_urls_wrapper(self, mock_inform, mock_sleep):
        """Test '_produce_urls_wrapper' informs about URLs count and manages
        the 'producing_urls_in_progress' event.
        """
        self.pipeline._produce_urls_wrapper(lambda: 5)

        self.assertEqual(self.pipeline.urls_to_process.value, 5)
        mock_inform.assert_called_once_with(
            "URLs to process: {}".format(self.pipeline.urls_to_process.value)
        )
        mock_sleep.assert_called_once_with(1)
        self.pipeline.producing_urls_in_progress.set.assert_called_once_with()
        self.pipeline.producing_urls_in_progress.clear.assert_called_once_with()

    @patch("scrapemeagain.pipeline.Pipeline.inform")
    @patch("scrapemeagain.pipeline.time.sleep")
    def test_produce_list_urls(self, mock_sleep, mock_inform):
        """Test 'produce_list_urls' uses 'scraper.generate_list_urls'."""
        mock_urls = ["url1", "url2", "url3"]
        self.pipeline.scraper.generate_list_urls.return_value = mock_urls

        self.pipeline.produce_list_urls()

        self.pipeline.scraper.generate_list_urls.assert_called_once_with()
        for mock_url in mock_urls:
            self.pipeline.url_queue.put.assert_any_call(mock_url)

    @patch("scrapemeagain.pipeline.Pipeline.inform")
    @patch("scrapemeagain.pipeline.time.sleep")
    def test_produce_item_urls(self, mock_sleep, mock_inform):
        """Test 'produce_item_urls' uses 'databaser.get_item_urls'."""
        mock_urls = [("url1",), ("url2",), ("url3",)]
        self.pipeline.databaser.get_item_urls.return_value = mock_urls

        self.pipeline.produce_item_urls()

        self.pipeline.databaser.get_item_urls.assert_called_once_with()
        for mock_url in mock_urls:
            self.pipeline.url_queue.put.assert_any_call(mock_url[0])

    def test_classify_response_ok(self):
        """Test '_classify_response' puts an OK response to
        'response_queue'."""
        mock_response_ok = Response()
        mock_response_ok.url = "url1"
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
        mock_response_not_ok.url = "url1"
        mock_response_not_ok.status_code = 500

        self.pipeline._classify_response(mock_response_not_ok)

        self.pipeline.url_queue.put.assert_called_once_with(
            mock_response_not_ok.url
        )
        with self.assertRaises(AssertionError):
            self.pipeline.response_queue.put.assert_called_once_with(
                mock_response_not_ok
            )

    @patch("scrapemeagain.pipeline.logging")
    @patch("scrapemeagain.pipeline.Pipeline._classify_response")
    def test_actually_get_html(self, mock_classify_response, mock_logging):
        """Test '_actually_get_html' fires requests for given URLs."""
        mock_urls = ["url1", "url2", "url3"]
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
            mock_logging.error.assert_called_once_with("Failed scraping URLs")

    @patch("scrapemeagain.pipeline.logging")
    def test_actually_get_html_fails(self, mock_logging):
        """Test '_actually_get_html' logs an exception message on fail."""
        self.pipeline.pool.map.side_effect = ValueError

        self.pipeline._actually_get_html(None)

        self.pipeline.pool.map.assert_called_once_with(get, None)
        self.pipeline.requesting_in_progress.set.assert_called_once_with()
        self.pipeline.requesting_in_progress.clear.assert_called_once_with()
        mock_logging.error.assert_called_once_with("Failed scraping URLs")
        self.assertEqual(mock_logging.exception.call_count, 1)

    @patch("scrapemeagain.pipeline.Pipeline._actually_get_html")
    @patch("scrapemeagain.pipeline.Pipeline.change_ip")
    def test_get_html(self, mock_change_ip, mock_actually_get_html):
        """Test 'get_html' populates and passes URL bulks for processing."""
        mock_urls = ["url1", "url2", "url3"]
        self.pipeline.url_queue.get.side_effect = (
            mock_urls + [DUMP_URLS_BUCKET] + [EXIT]
        )
        self.pipeline.scrape_processes = 4

        self.pipeline.get_html()

        # 4 = len(mock_urls) + DUMP_URLS_BUCKET + EXIT
        self.assertEqual(self.pipeline.url_queue.get.call_count, 5)

        mock_change_ip.assert_called_once_with()
        mock_actually_get_html.assert_called_once_with(mock_urls)

    def test_scrape_data_item_urls(self):
        """Test '_scrape_data' gets item URLs from a list page."""
        mock_item_urls_response = Response()
        mock_item_urls_response.url = "url?search=1"
        mock_item_urls_response.status_code = 200

        self.pipeline.scraper.list_url_template = "url?search="
        self.pipeline.scraper.get_item_urls.return_value = []

        data = self.pipeline._scrape_data(mock_item_urls_response)
        self.assertEqual(data, [])

        self.pipeline.scraper.get_item_urls.assert_called_once_with(
            mock_item_urls_response
        )
        with self.assertRaises(AssertionError):
            self.pipeline.scraper.get_item_properties.assert_called_once_with()

    def test_scrape_data_item_properties(self):
        """Test '_scrape_data' gets item properties from an item page."""
        mock_item_response = Response()
        mock_item_response.url = "url-item-1"
        mock_item_response.status_code = 200

        self.pipeline.scraper.list_url_template = "url?search="
        self.pipeline.scraper.get_item_properties.return_value = {}

        data = self.pipeline._scrape_data(mock_item_response)
        self.assertEqual(data, {})

        self.pipeline.scraper.get_item_properties.assert_called_once_with(
            mock_item_response
        )
        with self.assertRaises(AssertionError):
            self.pipeline.scraper.get_item_urls.assert_called_once_with()

    @patch("scrapemeagain.pipeline.Pipeline._scrape_data")
    def test_actually_collect_data(self, mock_scrape_data):
        """Test '_actually_collect_data' populates 'data_queue'."""
        mock_scrape_data.return_value = {"key": "value"}

        mock_item_response = Response()
        mock_item_response.url = "url-item-1"
        mock_item_response.status_code = 200

        self.pipeline._actually_collect_data(mock_item_response)

        self.pipeline.data_queue.put.assert_called_once_with({"key": "value"})
        self.pipeline.scraping_in_progress.set.assert_called_once_with()
        self.pipeline.scraping_in_progress.clear.assert_called_once_with()

    @patch("scrapemeagain.pipeline.logging")
    @patch("scrapemeagain.pipeline.Pipeline._scrape_data")
    def test_actually_collect_data_fails(self, mock_scrape_data, mock_logging):
        """Test '_actually_collect_data' logs an exception message on fail."""
        mock_scrape_data.side_effect = ValueError

        mock_item_response = Response()
        mock_item_response.url = "url-item-1"
        mock_item_response.status_code = 200

        self.pipeline._actually_collect_data(mock_item_response)

        self.pipeline.scraping_in_progress.set.assert_called_once_with()
        self.pipeline.scraping_in_progress.clear.assert_called_once_with()
        mock_logging.error.assert_called_once_with(
            'Failed processing response for "url-item-1"'
        )
        self.assertEqual(mock_logging.exception.call_count, 1)

    @patch("scrapemeagain.pipeline.Pipeline._actually_collect_data")
    def test_collect_data(self, mock_actually_collect_data):
        """Test 'collect_data' populates and passes response bulks for
        processing.
        """
        mock_urls = ["url1", "url2", "url3"]
        mock_url_statuses = [200, 500, 200]
        mock_responses = create_responses(mock_urls, mock_url_statuses)
        self.pipeline.response_queue.get.side_effect = mock_responses + [EXIT]

        self.pipeline.collect_data()

        # 4 = len(mock_responses) + EXIT
        self.assertEqual(self.pipeline.response_queue.get.call_count, 4)

        # 3 = len(mock_responses)
        self.assertEqual(mock_actually_collect_data.call_count, 3)

    def test_store_item_urls(self):
        """Test '_store_item_urls' stores item URLs to DB."""
        mock_data = [{"url": "url1"}, {"url": "url2"}]

        self.pipeline._store_item_urls(mock_data)

        self.pipeline.databaser.insert_multiple.assert_called_once_with(
            mock_data, self.pipeline.databaser.item_urls_table
        )

    def test_store_item_urls_empty(self):
        """Test '_store_item_urls' only stores actual item URLs."""
        self.pipeline._store_item_urls([])

        self.assertEqual(self.pipeline.databaser.insert_multiple.call_count, 0)

    def test_store_item_properties(self):
        """Test '_store_item_properties' saves item properties to DB."""
        mock_data = {"url": "url1", "key": "value"}

        self.pipeline._store_item_properties(mock_data)

        self.pipeline.databaser.insert.assert_called_once_with(
            mock_data, self.pipeline.databaser.item_data_table
        )
        self.pipeline.databaser.delete_url.assert_called_once_with(
            mock_data["url"]
        )

    def test_store_item_properties_empty(self):
        """Test '_store_item_properties' does not store the item and only
        removes its URL if there are no properties set.
        """
        mock_data = {"url": "url1"}

        self.pipeline._store_item_properties(mock_data)

        self.assertEqual(self.pipeline.databaser.insert.call_count, 0)
        self.pipeline.databaser.delete_url.assert_called_once_with(
            mock_data["url"]
        )

    @patch("scrapemeagain.pipeline.Pipeline._store_item_urls")
    @patch("scrapemeagain.pipeline.Pipeline._store_item_properties")
    def test_actually_store_data(
        self, mock_store_item_properties, mock_store_item_urls
    ):
        """Test '_actually_store_data' is able to handle both item URLs and
        properties.
        """
        mock_urls = [{"url": "url1"}, {"url": "url2"}]
        self.pipeline._actually_store_data(mock_urls)
        mock_store_item_urls.assert_called_once_with(mock_urls)

        mock_properties = {"url": "url1", "key": "value"}
        self.pipeline._actually_store_data(mock_properties)
        mock_store_item_properties.assert_called_once_with(mock_properties)

    # @patch('scrapemeagain.pipeline.Pipeline._store_item_urls')
    # @patch('scrapemeagain.pipeline.Pipeline._store_item_properties')
    # def test_actually_store_data_commits(
    #     self, mock_store_item_properties, mock_store_item_urls
    # ):
    #     """Test '_actually_store_data' commits changes on exit.
    #     """
    #     self.pipeline._actually_store_data(EXIT)
    #
    #     self.pipeline.databaser.commit.assert_called_once_with()

    @patch("scrapemeagain.pipeline.logging")
    def test_actually_store_data_fails(self, mock_logging):
        """Test '_actually_store_data' logs an exception message on fail."""
        self.pipeline._actually_store_data(None)

        mock_logging.error.assert_called_once_with("Failed storing data")
        self.assertEqual(mock_logging.exception.call_count, 1)

    @patch("scrapemeagain.pipeline.Pipeline._actually_store_data")
    def test_store_data(self, mock_actually_store_data):
        """Test 'store_data' takes data from the 'data_queue' and pass it to
        '_actually_store_data' (to save it in DB), and all changes are
        committed before exiting.
        """
        mock_data = [
            {"url": "url1", "key": "value"},
            {"url": "url2", "key": "value"},
        ]
        self.pipeline.data_queue.get.side_effect = mock_data + [EXIT]

        self.pipeline.store_data()

        # 3 = len(mock_data) + EXIT
        self.assertEqual(self.pipeline.data_queue.get.call_count, 3)
        self.assertEqual(self.pipeline._actually_store_data.call_count, 2)

        # check 'urls_processed' is reset before actualy storing data
        self.assertEqual(self.pipeline.urls_processed.value, 0)

        # Should commit after EXIT.
        self.pipeline.databaser.commit.assert_called_once_with()

    @patch("scrapemeagain.pipeline.Pipeline.inform")
    def test_exit_workers(self, mock_inform):
        """Test 'exit_workers' passes an EXIT message to all queues."""
        self.pipeline.exit_workers()

        mock_inform.assert_called_once_with("Exiting workers, please wait ...")

        self.pipeline.url_queue.put.assert_called_once_with(EXIT)
        self.pipeline.response_queue.put.assert_called_once_with(EXIT)
        self.pipeline.data_queue.put.assert_called_once_with(EXIT)

    def test_queues_empty(self):
        """Test '_queues_empty' checks if all queues are empty."""
        self.pipeline.url_queue.empty.return_value = True
        self.pipeline.response_queue.empty.return_value = True
        self.pipeline.data_queue.empty.return_value = True

        queues_empty = self.pipeline._queues_empty()

        self.assertTrue(queues_empty)

        self.pipeline.url_queue.empty.assert_called_once_with()
        self.pipeline.response_queue.empty.assert_called_once_with()
        self.pipeline.data_queue.empty.assert_called_once_with()

    def test_workers_idle(self):
        """Test '_workers_idle' checks if all workers are idle."""
        self.pipeline.producing_urls_in_progress.is_set.return_value = False
        self.pipeline.requesting_in_progress.is_set.return_value = False
        self.pipeline.scraping_in_progress.is_set.return_value = False

        workers_idle = self.pipeline._workers_idle()

        self.assertTrue(workers_idle)

        self.pipeline.producing_urls_in_progress.is_set.assert_called_once_with()  # noqa
        self.pipeline.requesting_in_progress.is_set.assert_called_once_with()
        self.pipeline.scraping_in_progress.is_set.assert_called_once_with()

    @patch("scrapemeagain.pipeline.time")
    @patch("scrapemeagain.pipeline.Pipeline._inform_progress")
    @patch("scrapemeagain.pipeline.Pipeline.exit_workers")
    @patch("scrapemeagain.pipeline.Pipeline._queues_empty")
    @patch("scrapemeagain.pipeline.Pipeline._workers_idle")
    def test_switch_power(
        self,
        mock_workers_idle,
        mock_queues_empty,
        mock_exit_workers,
        mock_inform_progress,
        mock_time,
    ):
        """Test 'switch_power' repeatedly checks the program can end."""
        mock_queues_empty.side_effect = [False, False, True, True, True]
        mock_workers_idle.side_effect = [False, True, True]

        self.pipeline.switch_power()

        # Both 'url_queue' and 'response_queue' aren't empty once so we expect
        # 'switch_power' will need to wait 2 times.
        self.assertEqual(mock_time.sleep.call_count, 2)
        self.assertEqual(mock_inform_progress.call_count, 2)
        self.assertEqual(self.pipeline.url_queue.put.call_count, 0)

        mock_exit_workers.assert_called_once_with()

    @patch("scrapemeagain.pipeline.logging")
    @patch("scrapemeagain.pipeline.time")
    @patch("scrapemeagain.pipeline.Pipeline._inform_progress")
    @patch("scrapemeagain.pipeline.Pipeline.exit_workers")
    @patch("scrapemeagain.pipeline.Pipeline._queues_empty")
    @patch("scrapemeagain.pipeline.Pipeline._workers_idle")
    def test_switch_power_dumps_urls(
        self,
        mock_workers_idle,
        mock_queues_empty,
        mock_exit_workers,
        mock_inform_progress,
        mock_time,
        mock_logging,
    ):
        """Test 'switch_power' is able to dump URLs bucket."""
        mock_queues_empty.side_effect = [True, True, True]
        mock_workers_idle.side_effect = [True, True, True]
        type(self.pipeline.urls_bucket_empty).value = PropertyMock(
            side_effect=[0, 0, 1]
        )

        self.pipeline.switch_power()

        self.assertEqual(mock_time.sleep.call_count, 1)
        self.assertEqual(mock_inform_progress.call_count, 1)
        self.pipeline.url_queue.put.assert_called_once_with(DUMP_URLS_BUCKET)

        mock_logging.info.assert_called_once_with("Dumping URLs bucket")
        mock_exit_workers.assert_called_once_with()

    @patch("scrapemeagain.pipeline.Process")
    def test_employ_worker(self, mock_process):
        """Test 'employ_worker' creates and registers a dameon worker."""
        self.pipeline.employ_worker(all)

        mock_process.assert_called_once_with(target=all)
        self.assertTrue(mock_process.daemon)
        mock_process.return_value.start.assert_called_once_with()

        self.assertEqual(len(self.pipeline.workers), 1)

    @patch("scrapemeagain.pipeline.Process")
    def test_release_workers(self, mock_process):
        """Test 'release_workers' waits till a worker is finished."""
        self.pipeline.workers = [mock_process]

        self.pipeline.release_workers()

        mock_process.join.assert_called_once_with()

    @patch("scrapemeagain.pipeline.Pipeline.inform")
    @patch("scrapemeagain.pipeline.Pipeline.release_workers")
    @patch("scrapemeagain.pipeline.Pipeline.employ_worker")
    @patch("scrapemeagain.pipeline.Pipeline.get_html")
    def test_get_item_urls(
        self,
        mock_get_html,
        mock_employ_worker,
        mock_release_workers,
        mock_inform,
    ):
        """Test 'get_item_urls' starts all necessary workers and waits till
        they are finished.
        """
        self.pipeline.get_item_urls()

        mock_inform.assert_called_once_with("Collecting item URLs")

        mock_employ_worker.assert_any_call(self.pipeline.produce_list_urls)
        mock_employ_worker.assert_any_call(self.pipeline.collect_data)
        mock_employ_worker.assert_any_call(self.pipeline.store_data)
        mock_employ_worker.assert_any_call(self.pipeline.switch_power)
        mock_get_html.assert_called_once_with()
        mock_release_workers.assert_called_once_with()

    @patch("scrapemeagain.pipeline.Pipeline.inform")
    @patch("scrapemeagain.pipeline.Pipeline.release_workers")
    @patch("scrapemeagain.pipeline.Pipeline.employ_worker")
    @patch("scrapemeagain.pipeline.Pipeline.get_html")
    def test_get_item_properties(
        self,
        mock_get_html,
        mock_employ_worker,
        mock_release_workers,
        mock_inform,
    ):
        """Test 'get_item_properties' starts all necessary workers and waits
        till they are finished.
        """
        self.pipeline.get_item_properties()

        mock_inform.assert_called_once_with("Collecting item properties")

        mock_employ_worker.assert_any_call(self.pipeline.produce_item_urls)
        mock_employ_worker.assert_any_call(self.pipeline.collect_data)
        mock_employ_worker.assert_any_call(self.pipeline.store_data)
        mock_employ_worker.assert_any_call(self.pipeline.switch_power)
        mock_get_html.assert_called_once_with()
        mock_release_workers.assert_called_once_with()

from unittest import TestCase
from unittest.mock import Mock, patch

from scrapemeagain.pipeline import Pipeline


class TestPipelineBase(TestCase):
    def setUp(self):
        # Mock Event.
        event_patcher = patch('scrapemeagain.pipeline.Event')
        mock_event = event_patcher.start()
        self.addCleanup(mock_event.stop)

        # Mock Pool and Pool.map.
        self.mock_map = Mock()
        pool_patcher = patch('scrapemeagain.pipeline.Pool')
        mock_pool = pool_patcher.start()
        mock_pool.return_value.map = self.mock_map
        self.addCleanup(mock_pool.stop)

        # Mock Queue.
        queue_patcher = patch('scrapemeagain.pipeline.Queue')
        mock_queue = queue_patcher.start()
        self.addCleanup(mock_queue.stop)

        # Mock TorIpChanger.
        tor_ip_changer_patcher = patch('scrapemeagain.pipeline.TorIpChanger')
        mock_tor_ip_changer = tor_ip_changer_patcher.start()
        self.addCleanup(mock_tor_ip_changer.stop)

        # Prepare pipeline.
        self.pipeline = Pipeline(Mock(), Mock())
        self.pipeline.prepare_dependencies()
        self.pipeline.prepare_multiprocessing()

        # Ensure each pipeline's Queue is an unique Mock.
        self.pipeline.url_queue = Mock()
        self.pipeline.response_queue = Mock()
        self.pipeline.data_queue = Mock()

        # Ensure each pipeline's Event is an unique Mock.
        self.pipeline.requesting_in_progress = Mock()
        self.pipeline.scraping_in_progress = Mock()

        # Mock scraping methods - 'get_item_urls', 'get_item_properties'.
        self.pipeline.scraper.get_item_urls = Mock()
        self.pipeline.scraper.get_item_properties = Mock()

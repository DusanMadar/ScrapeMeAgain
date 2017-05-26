from unittest import TestCase
from unittest.mock import Mock

from scrapemeagain.pipeline import Pipeline


class TestPipelineBase(TestCase):
    def setUp(self):
        self.pipeline = Pipeline(Mock(), Mock(), Mock())

        # Mock Scraper.
        self.pipeline.scraper.get_item_urls = Mock()
        self.pipeline.scraper.get_item_properties = Mock()

        # Mock Databaser.
        self.pipeline.databaser.insert = Mock()
        self.pipeline.databaser.insert_multiple = Mock()
        self.pipeline.databaser.delete_url = Mock()
        self.pipeline.databaser.commit = Mock()

        #
        # Mock multiprocessing (instead of calling 'prepare_multiprocessing').
        # Mock pipeline's Pool and Pool.map.
        mock_pool = Mock()
        mock_pool.return_value.map = Mock()
        self.pipeline.pool = mock_pool

        # Ensure each pipeline's Queue is an unique Mock object.
        self.pipeline.url_queue = Mock()
        self.pipeline.response_queue = Mock()
        self.pipeline.data_queue = Mock()

        # Ensure each pipeline's Event is an unique Mock object.
        self.pipeline.producing_urls_in_progress = Mock()
        self.pipeline.requesting_in_progress = Mock()
        self.pipeline.scraping_in_progress = Mock()

        # Mock counter Values.
        mock_urls_to_process = Mock()
        mock_urls_to_process.value = 0
        self.pipeline.urls_to_process = mock_urls_to_process
        mock_urls_processed = Mock()
        mock_urls_processed.value = 0
        self.pipeline.urls_processed = mock_urls_processed

        # Mock URLs bucket state.
        self.pipeline.urls_bucket_empty = Mock()

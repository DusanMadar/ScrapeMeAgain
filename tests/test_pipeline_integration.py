# class TestPipelineIntegration(unittest.TestCase):
#     def setUp(self):
#         # Mock Pool and Pool.map.
#         self.mock_map = Mock()
#         pool_patcher = patch('scrapemeagain.pipeline.Pool')
#         mock_pool = pool_patcher.start()
#         mock_pool.return_value.map = self.mock_map
#         self.addCleanup(mock_pool.stop)
#
#         # Mock TorIpChanger.
#         tor_ip_changer_patcher = patch('scrapemeagain.pipeline.TorIpChanger')
#         self.mock_tor_ip_changer = tor_ip_changer_patcher.start()
#         self.addCleanup(self.mock_tor_ip_changer.stop)
#
#         # Prepare pipeline.
#         self.pipeline = Pipeline(Mock(), Mock())
#         self.pipeline.prepare_dependencies()
#         self.pipeline.prepare_multiprocessing()
#
#     @queue_waiter
#     def test_get_html(self):
#         mock_urls = ['url1', 'url2', 'url3']
#         fake_url_statuses = [200, 500, 200]
#
#         self.pipeline.scraper.generate_list_urls.return_value = mock_urls
#         self.mock_map.return_value = create_responses(
#             mock_urls, fake_url_statuses
#         )
#
#         self.pipeline.processes = len(mock_urls)
#         self.pipeline.produce_list_urls()
#
#         # We are faking 3 URLs.
#         self.assertEqual(self.pipeline.url_queue.qsize(), 3)
#
#         self.pipeline.url_queue.put(EXIT)
#         self.pipeline.get_html()
#
#         # Only 2 responses are OK.
#         self.assertEqual(self.pipeline.response_queue.qsize(), 2)
#         # The third one should returned back for scraping.
#         self.assertEqual(self.pipeline.url_queue.qsize(), 1)

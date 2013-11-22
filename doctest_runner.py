#!/usr/bin/env python
"""
  Module to run the doc_tests for the different pytomo modules that need
  not access the network.
  The following modules are considered:
  pytomo.start_pytomo:
      format_stats
  pytomo.lib_cache_url:
      trunk_url
  pytomo.lib_youtube_api:
      get_time_frame
  pytomo.lib_youtube_download:
      format_bytes
      calc_percent
      calc_eta
      calc_speed
  pytomo.lib_database: The doc_test is writen for the whole module



"""

if __name__ == '__main__':
    import doctest
    import pytomo

    doctest.testmod(pytomo.start_pytomo)
    doctest.testmod(pytomo.lib_cache_url)
    doctest.testmod(pytomo.lib_youtube_api)
    doctest.testmod(pytomo.lib_youtube_download)
    doctest.testmod(pytomo.lib_dns)
    doctest.testmod(pytomo.lib_database)

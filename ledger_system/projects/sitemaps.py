# sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.shortcuts import reverse

class StaticViewSitemap(Sitemap):
    def items(self):
        return ['home',]  # replace with your actual view names

    def location(self, item):
        return reverse(item)

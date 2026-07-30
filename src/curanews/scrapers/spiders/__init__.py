"""Spider package exports."""

from curanews.scrapers.spiders.base import BaseNewsSpider
from curanews.scrapers.spiders.example_news import ExampleNewsSpider

__all__ = ["BaseNewsSpider", "ExampleNewsSpider"]

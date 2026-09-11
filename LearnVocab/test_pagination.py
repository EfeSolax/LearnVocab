"""
Sayfalama yardımcılarının testleri.

Aynı arayüz hem "Kelimelerim" hem "Tüm Kelimeler" sayfasında kullanılıyor;
bağlam üretimi bozulursa iki sayfa birden bozulur.
"""

from django.test import RequestFactory, TestCase

from LearnVocab import pagination


class BuildPageWindowTests(TestCase):
    def test_single_page(self):
        self.assertEqual(pagination.build_page_window(1, 1), [1])

    def test_no_pages(self):
        self.assertEqual(pagination.build_page_window(1, 0), [])

    def test_short_range_has_no_ellipsis(self):
        self.assertEqual(pagination.build_page_window(2, 5, side=3), [1, 2, 3, 4, 5])

    def test_middle_of_a_long_range(self):
        self.assertEqual(
            pagination.build_page_window(10, 20, side=3),
            [1, None, 7, 8, 9, 10, 11, 12, 13, None, 20],
        )

    def test_near_the_start(self):
        window = pagination.build_page_window(2, 20, side=3)
        self.assertEqual(window[:6], [1, 2, 3, 4, 5, 20] if len(window) == 6 else window[:6])
        self.assertIn(20, window)
        self.assertNotIn(None, window[:2])

    def test_pages_are_unique(self):
        window = pagination.build_page_window(1, 3, side=3)
        numbers = [p for p in window if p is not None]
        self.assertEqual(len(numbers), len(set(numbers)))

    def test_no_double_ellipsis(self):
        window = pagination.build_page_window(50, 100, side=1)
        for first, second in zip(window, window[1:]):
            self.assertFalse(first is None and second is None)


class ResolvePerPageTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _request(self, value=None):
        path = "/" if value is None else f"/?per_page={value}"
        return self.factory.get(path)

    def test_default_when_missing(self):
        self.assertEqual(pagination.resolve_per_page(self._request(), (25, 50), 50), 50)

    def test_allowed_value_is_used(self):
        self.assertEqual(pagination.resolve_per_page(self._request(25), (25, 50), 50), 25)

    def test_disallowed_value_falls_back(self):
        self.assertEqual(pagination.resolve_per_page(self._request(999), (25, 50), 50), 50)

    def test_garbage_falls_back(self):
        self.assertEqual(pagination.resolve_per_page(self._request("abc"), (25, 50), 50), 50)


class PaginationContextTests(TestCase):
    def _page(self, count=100, per_page=25, number=2):
        from django.core.paginator import Paginator
        paginator = Paginator(list(range(count)), per_page)
        return paginator.get_page(number), paginator

    def test_empty_params_are_dropped(self):
        page_obj, paginator = self._page()
        context = pagination.pagination_context(
            page_obj, paginator,
            params=[("q", "kelime"), ("filter_by", ""), ("level", None), ("x", "all")],
            per_page=25, per_page_options=(25, 50), default_per_page=25,
        )
        self.assertEqual(context["base_qs"], "q=kelime")
        self.assertEqual(context["pagination_params"], [{"name": "q", "value": "kelime"}])

    def test_per_page_is_added_only_when_it_differs(self):
        page_obj, paginator = self._page(per_page=50)

        varsayilan = pagination.pagination_context(
            page_obj, paginator, params=[], per_page=50,
            per_page_options=(25, 50), default_per_page=50,
        )
        self.assertEqual(varsayilan["base_qs"], "")

        farkli = pagination.pagination_context(
            page_obj, paginator, params=[], per_page=25,
            per_page_options=(25, 50), default_per_page=50,
        )
        self.assertEqual(farkli["base_qs"], "per_page=25")

    def test_values_are_url_encoded(self):
        """Arama kutusuna boşluk veya & yazılırsa bağlantı bozulmamalı."""
        page_obj, paginator = self._page()
        context = pagination.pagination_context(
            page_obj, paginator, params=[("q", "give up & go")],
            per_page=25, per_page_options=(25,), default_per_page=25,
        )
        self.assertNotIn(" ", context["base_qs"])
        self.assertIn("%26", context["base_qs"])

    def test_page_is_never_part_of_the_query_string(self):
        page_obj, paginator = self._page()
        context = pagination.pagination_context(
            page_obj, paginator, params=[("q", "x")],
            per_page=25, per_page_options=(25,), default_per_page=25,
        )
        base_qs = context["base_qs"]
        self.assertFalse(base_qs.startswith("page="))
        self.assertNotIn("&page=", base_qs)

    def test_window_and_flags(self):
        page_obj, paginator = self._page(count=500, per_page=25, number=10)
        context = pagination.pagination_context(
            page_obj, paginator, params=[], per_page=25,
            per_page_options=(25,), default_per_page=25,
        )
        self.assertTrue(context["is_paginated"])
        self.assertIn(1, context["page_window"])
        self.assertIn(20, context["page_window"])
        self.assertEqual(context["per_page"], 25)

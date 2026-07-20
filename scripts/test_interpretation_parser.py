#!/usr/bin/env python3
"""Regression tests for strict interpretation-header parsing."""

import unittest

from extract_manual import parse_interpretation_header


class InterpretationHeaderTests(unittest.TestCase):
    cases = (
        ("【95年6月6日農授金字第0955080181號函】", "95年6月6日", "農授金字第0955080181號"),
        ("【95年6月6日農授金字第0955080186號函】", "95年6月6日", "農授金字第0955080186號"),
        ("【中華民國95年6月26日農授金字第0955013311號函】", "95年6月26日", "農授金字第0955013311號"),
        ("【95年8月17日農授金字第0955014492號函】", "95年8月17日", "農授金字第0955014492號"),
        ("【96年3月21日農授金字第0965080067號函】", "96年3月21日", "農授金字第0965080067號"),
        ("【102年4月26日農授金字第1025080192號函】", "102年4月26日", "農授金字第1025080192號"),
        ("【102年11月8日農授金字第1025015623號函】", "102年11月8日", "農授金字第1025015623號"),
        ("【114年12月3日農授金字第1147426893號函】", "114年12月3日", "農授金字第1147426893號"),
    )

    def test_known_headers(self):
        for header, date, number in self.cases:
            with self.subTest(header=header):
                parsed = parse_interpretation_header(header)
                self.assertIsNotNone(parsed)
                self.assertEqual(parsed["date"], date)
                self.assertEqual(parsed["documentNumber"], number)

    def test_layout_whitespace(self):
        parsed = parse_interpretation_header("【95 年 6 月 6 日 農 授 金 字 第 0955080181 號 函】")
        self.assertEqual(parsed["date"], "95年6月6日")
        self.assertEqual(parsed["documentNumber"], "農授金字第0955080181號")

    def test_reject_invalid_or_missing_date(self):
        self.assertIsNone(parse_interpretation_header("【日農授金字第0955080181號函】"))
        self.assertIsNone(parse_interpretation_header("【農授金字第0955080181號函】"))


if __name__ == "__main__":
    unittest.main()

{
    "pages": [
        {
            "url": "https://example-shortener1.com/page1",
            "name": "URL Shortener 1",
            "elements_to_click": [
                {"selector": "button.skip-ad", "by": "css"},
                {"selector": "//a[contains(@class, 'continue')]", "by": "xpath"}
            ],
            "wait_time": [5, 10],
            "scroll_behavior": "natural",
            "retry_on_failure": true,
            "importance_weight": 2
        },
        {
            "url": "https://example-shortener2.com/page2",
            "name": "URL Shortener 2",
            "elements_to_click": [
                {"selector": "#countdown", "by": "css", "wait_for_enabled": true},
                {"selector": ".get-link", "by": "css"}
            ],
            "wait_time": [3, 8],
            "scroll_behavior": "quick",
            "retry_on_failure": true,
            "importance_weight": 1
        },
        {
            "url": "https://example-shortener3.com/page3",
            "name": "URL Shortener 3",
            "elements_to_click": [
                {"selector": "//button[contains(text(), 'Skip')]", "by": "xpath"},
                {"selector": ".download-link", "by": "css"}
            ],
            "wait_time": [4, 9],
            "scroll_behavior": "thorough",
            "retry_on_failure": true,
            "importance_weight": 3
        },
        {
            "url": "https://example-shortener4.com/page4",
            "name": "URL Shortener 4",
            "elements_to_click": [
                {"selector": "#timer", "by": "css", "wait_seconds": 5},
                {"selector": "//div[contains(@class, 'result')]/a", "by": "xpath"}
            ],
            "wait_time": [6, 12],
            "scroll_behavior": "natural",
            "retry_on_failure": true,
            "importance_weight": 2
        }
    ]
}

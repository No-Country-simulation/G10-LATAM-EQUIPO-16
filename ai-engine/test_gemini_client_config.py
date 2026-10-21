from analyzer import client


def test_gemini_http_configuration():
    options = client._api_client._http_options

    assert options.timeout == 10000
    assert options.retry_options.attempts == 1
    assert 429 not in options.retry_options.http_status_codes
    assert options.retry_options.http_status_codes == [
        408, 500, 502, 503, 504
    ]

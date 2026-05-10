import asyncio

from services.python_api.app.services import orchestration


def test_parse_uploaded_artifacts_combines_multiple_screenshot_ocr():
    original = orchestration._extract_ocr_cached
    texts = iter(
        [
            {"ocrText": "First screen"},
            {"ocrText": "Second screen"},
        ]
    )
    orchestration._extract_ocr_cached = lambda _bytes: next(texts)
    try:
        parsed = asyncio.run(
            orchestration.parse_uploaded_artifacts(
                xml_bytes=b"<Root><TestName>MultiShot</TestName><Step><StepName>Open</StepName><Timing>10</Timing></Step></Root>",
                startlog_bytes=b"",
                screenshot_bytes_list=[b"one", b"two"],
                test_name=None,
                filenames={
                    "logXml": "log.xml",
                    "startLog": "STARTLog.txt",
                    "screenshots": ["1.png", "2.png"],
                },
            )
        )
    finally:
        orchestration._extract_ocr_cached = original

    assert "First screen" in parsed.bundle["ocrText"]
    assert "Second screen" in parsed.bundle["ocrText"]
    assert parsed.uploaded_artifacts["screenshotCount"] == 2
    assert parsed.uploaded_artifacts["screenshots"] == ["1.png", "2.png"]


def test_parse_uploaded_artifacts_falls_back_to_filename_for_test_name():
    parsed = asyncio.run(
        orchestration.parse_uploaded_artifacts(
            xml_bytes=b"<Root><Step><StepName>Open</StepName><Timing>10</Timing></Step></Root>",
            startlog_bytes=b"",
            screenshot_bytes_list=[],
            test_name=None,
            filenames={
                "logXml": "SalesQuote_Search.xml",
                "startLog": "STARTLog.txt",
                "screenshots": [],
            },
        )
    )

    assert parsed.bundle["testName"] == "SalesQuote_Search"

from aqis.parser.xml_parser import parse_xml


def test_parse_xml_recovers_from_encoding_mismatch():
    xml_bytes = (
        b'<?xml version="1.0" encoding="UTF-16"?>\n'
        b"<Root>"
        b"<TestName>EncodingCase</TestName>"
        b"<Step><StepName>Open</StepName><Timing>10</Timing></Step>"
        b"</Root>"
    )

    result = parse_xml(xml_bytes)

    assert result["testName"] == "EncodingCase"
    assert result["steps"][0]["stepName"] == "Open"

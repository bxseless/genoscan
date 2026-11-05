from genoscan.patterns import scan_text


def rules(line):
    return [m.pattern.rule for m in scan_text(line)]


def test_home_directory_beats_absolute_path():
    # Overlapping matches: only the more severe one should be kept.
    assert rules("ref=/Users/jdoe/projects/ref.fa") == ["home-directory"]


def test_email():
    assert "email" in rules("##contact=someone@example.org")


def test_ip_address():
    assert "ip-address" in rules("##server=10.12.4.27")


def test_version_number_is_not_an_ip():
    assert "ip-address" not in rules("##source=GATK version=4.2.6.1")


def test_out_of_range_octets_are_not_an_ip():
    assert "ip-address" not in rules("value 300.1.2.3")


def test_clean_line_has_no_hits():
    assert rules('##INFO=<ID=AF,Number=A,Type=Float,Description="Allele frequency">') == []

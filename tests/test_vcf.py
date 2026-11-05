import pytest

from genoscan.findings import Severity
from genoscan.scanners.vcf import classify_sample_id, scan_vcf

HEADER = "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT"


def make_vcf(meta_lines, samples):
    return "\n".join(["##fileformat=VCFv4.2", *meta_lines,
                      "\t".join([HEADER, *samples]),
                      "chr1\t100\t.\tA\tG\t50\tPASS\t.\tGT" + "\t0/1" * len(samples)]) + "\n"


@pytest.mark.parametrize("sample, expected_rule, expected_severity", [
    ("NA12878", "sample-id-public", Severity.LOW),
    ("PT-19850412", "sample-id-date", Severity.HIGH),
    ("MRN00482913", "sample-id-number", Severity.HIGH),
    ("Jane_Doe", "sample-id-name", Severity.HIGH),
    ("S1", "sample-id", Severity.MEDIUM),
])
def test_classify_sample_id(sample, expected_rule, expected_severity):
    severity, rule, _ = classify_sample_id(sample)
    assert (rule, severity) == (expected_rule, expected_severity)


def test_finds_leaks_in_header(write_file):
    path = write_file("x.vcf", make_vcf(
        ["##fileDate=20260314",
         "##reference=file:///Users/jdoe/ref/hg38.fa",
         '##toolCommandLine=<CommandLine="run --in /data/lab/a.bam">'],
        ["S1"],
    ))
    rules = {f.rule for f in scan_vcf(path)}
    assert {"vcf-file-date", "home-directory", "vcf-command-line",
            "absolute-path", "sample-id"} <= rules


def test_sample_listed_twice_is_reported_once(write_file):
    path = write_file("x.vcf", make_vcf(["##SAMPLE=<ID=Jane_Doe,Assay=WGS>"], ["Jane_Doe"]))
    samples = [f for f in scan_vcf(path) if f.rule.startswith("sample-id")]
    assert len(samples) == 1


def test_minimal_vcf_only_reports_sample(write_file):
    path = write_file("x.vcf", make_vcf([], ["NA12878"]))
    assert [f.rule for f in scan_vcf(path)] == ["sample-id-public"]


def test_gzipped_vcf(write_file):
    path = write_file("x.vcf.gz", make_vcf(["##contact=a@example.org"], ["S1"]))
    assert "email" in {f.rule for f in scan_vcf(path)}


def test_line_numbers(write_file):
    path = write_file("x.vcf", make_vcf(["##contact=a@example.org"], ["S1"]))
    email = next(f for f in scan_vcf(path) if f.rule == "email")
    assert email.line == 2

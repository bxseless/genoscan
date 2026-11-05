from genoscan.scanners.fastq import scan_fastq


def make_fastq(names):
    return "".join(f"{n}\nACGT\n+\nIIII\n" for n in names)


def test_illumina_read_names(write_file):
    names = [f"@M70421:118:000000000-KXJ4P:1:1101:{i}:200 1:N:0:ATCACG" for i in range(5)]
    findings = scan_fastq(write_file("r.fastq", make_fastq(names)))
    by_rule = {f.rule: f.evidence for f in findings}
    assert by_rule["fastq-instrument"] == "M70421"
    assert by_rule["fastq-flowcell"] == "000000000-KXJ4P (run 118)"
    assert by_rule["fastq-index"] == "ATCACG"
    # 5 reads from the same run: each value reported once, not 5 times
    assert len(findings) == 3


def test_anonymous_read_names_are_clean(write_file):
    assert scan_fastq(write_file("r.fastq", make_fastq(["@read1", "@read2"]))) == []


def test_sequence_lines_are_ignored(write_file):
    # A sequence line that happens to look like an email must not be flagged.
    text = "@read1\nACGT@ACGT.com\n+\nIIII\n"
    assert scan_fastq(write_file("r.fastq", text)) == []


def test_max_records(write_file):
    names = ["@read1", "@read2 /home/jdoe/x"]
    findings = scan_fastq(write_file("r.fq", make_fastq(names)), max_records=1)
    assert findings == []


def test_gzipped_fastq(write_file):
    names = ["@M1:1:FC1:1:1:1:1"]
    findings = scan_fastq(write_file("r.fq.gz", make_fastq(names)))
    assert {f.rule for f in findings} == {"fastq-instrument", "fastq-flowcell"}

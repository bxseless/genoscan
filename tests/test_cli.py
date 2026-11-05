import json

from genoscan.cli import EXIT_CLEAN, EXIT_ERROR, EXIT_FINDINGS, main

LEAKY_VCF = ("##fileformat=VCFv4.2\n##contact=jdoe@example.org\n"
             "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tS1\n")
CLEAN_VCF = ("##fileformat=VCFv4.2\n"
             "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tNA12878\n")


def test_exit_code_findings(write_file, capsys):
    assert main(["scan", str(write_file("a.vcf", LEAKY_VCF))]) == EXIT_FINDINGS


def test_exit_code_clean(write_file, capsys):
    assert main(["scan", str(write_file("a.vcf", CLEAN_VCF))]) == EXIT_CLEAN


def test_fail_on_threshold(write_file, capsys):
    # The sample "S1" is MEDIUM. With --fail-on medium it should fail even
    # when the email line is removed.
    vcf = LEAKY_VCF.replace("##contact=jdoe@example.org\n", "")
    path = str(write_file("a.vcf", vcf))
    assert main(["scan", path]) == EXIT_CLEAN
    assert main(["scan", "--fail-on", "medium", path]) == EXIT_FINDINGS


def test_json_output(write_file, capsys):
    main(["scan", "--format", "json", str(write_file("a.vcf", LEAKY_VCF))])
    data = json.loads(capsys.readouterr().out)
    assert data["summary"]["high"] == 1
    assert data["findings"][0]["rule"] == "email"


def test_min_severity_hides_low(write_file, capsys):
    vcf = LEAKY_VCF.replace("##contact", "##fileDate=20260101\n##contact")
    main(["scan", "--format", "json", "--min-severity", "medium",
          str(write_file("a.vcf", vcf))])
    rules = {f["rule"] for f in json.loads(capsys.readouterr().out)["findings"]}
    assert "vcf-file-date" not in rules


def test_missing_file(tmp_path, capsys):
    assert main(["scan", str(tmp_path / "nope.vcf")]) == EXIT_ERROR


def test_unsupported_type(write_file, capsys):
    assert main(["scan", str(write_file("a.txt", "hello"))]) == EXIT_ERROR

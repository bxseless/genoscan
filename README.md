# genoscan

**Find identifying metadata in genomic files before you share them.**

Genomic files often carry more than DNA. Headers and read names can quietly
record usernames, email addresses, server paths, sequencing machine serial
numbers, and sample IDs built from names, dates of birth or medical record
numbers. `genoscan` scans VCF and FASTQ files (plain or gzipped) and reports
what it finds, with a severity for each, before the data goes to a
collaborator, a public repository or a GitHub repo.

## Why

Many people dont notice that genetic files carry more information than just the DNA itself. Genetic data can’t be changed like a password. And researchers have re-identified people from “anonymous” genomic data (for example, Gymrek et al., 2013, identified people by inferring their surnames from Y-chromosome markers). Security tools scan code for leaked secrets before its published and genomic data deserves the same check.

## Install

```bash
git clone https://github.com/<your-username>/genoscan.git
cd genoscan
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

```bash
genoscan scan sample.vcf reads.fastq.gz
genoscan scan --format json sample.vcf          # machine-readable output
genoscan scan --fail-on medium sample.vcf       # stricter exit code
genoscan scan --min-severity medium sample.vcf  # hide LOW findings
```

Example output:

```
examples/leaky.vcf
  HIGH    line 4     home-directory: Home directory path reveals a username
                     evidence: /Users/jdoe
  HIGH    line 6     email: Email address
                     evidence: jdoe@example.org
  ...
Scanned 1 file(s): 6 high, 3 medium, 2 low
```

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | Nothing at or above `--fail-on` (default `high`) |
| 1 | Findings at or above `--fail-on` |
| 2 | Error (missing file, unsupported type) |

This makes `genoscan` usable in scripts, CI and pre-commit hooks.

## What it checks (v0.1)

| Severity | Examples |
|----------|----------|
| HIGH | Home-directory paths (usernames), email addresses, sample IDs that look like names, dates or record numbers |
| MEDIUM | Absolute file paths, IP addresses, generic sample IDs, Illumina instrument serials and flowcell IDs |
| LOW | File dates, recorded command lines, sample barcodes, public reference samples (e.g. NA12878) |

## Try it

```bash
./scripts/demo.sh
```

This generates **fake** example files in `examples/` and scans them. Every
person, path and machine in them is invented.

## Roadmap

- [x] v0.1: scan VCF and FASTQ headers and read names
- [ ] v0.2: `genoscan clean` writes a sanitized copy (pseudonymized samples, stripped paths)
- [ ] v0.3: re-identification risk from rare variants and Y-STRs
- [ ] v0.4: BAM/SAM support, pre-commit hook and GitHub Action, PyPI release

## Limitations

`genoscan` uses heuristics. A clean report does not guarantee a file is safe
to share, and some findings will be false positives. Treat it as a checklist
that catches common mistakes, not a replacement for your institution's
data-sharing review.

## License

MIT

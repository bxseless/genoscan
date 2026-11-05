"""One module per file format. Each exposes a scan_<format>(path) function."""
from genoscan.scanners.fastq import scan_fastq
from genoscan.scanners.vcf import scan_vcf

SCANNERS = {
    "vcf": scan_vcf,
    "fastq": scan_fastq,
}

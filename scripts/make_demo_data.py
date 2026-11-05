"""Generate FAKE genomic files for demos and testing.

Everything here is invented: the people, paths, machines and variants. Never
put real patient or participant data in this repository.

Usage:  python scripts/make_demo_data.py          (writes into examples/)
"""
from __future__ import annotations

import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "examples"
BASES = "ACGT"


def fake_variants(rng: random.Random, n_samples: int, n_variants: int = 20) -> list:
    rows = []
    pos = 10_000
    for i in range(n_variants):
        pos += rng.randint(500, 50_000)
        ref = rng.choice(BASES)
        alt = rng.choice([b for b in BASES if b != ref])
        genotypes = [rng.choice(["0/0", "0/1", "1/1"]) for _ in range(n_samples)]
        rows.append("\t".join(["chr1", str(pos), f"var{i}", ref, alt, "50", "PASS",
                               f"AF={rng.random():.3f}", "GT", *genotypes]))
    return rows


def vcf(samples: list, meta: list, rng: random.Random) -> str:
    header = [
        "##fileformat=VCFv4.2",
        *meta,
        '##INFO=<ID=AF,Number=A,Type=Float,Description="Allele frequency">',
        '##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">',
        "##contig=<ID=chr1,length=248956422>",
        "\t".join(["#CHROM", "POS", "ID", "REF", "ALT", "QUAL", "FILTER", "INFO", "FORMAT",
                   *samples]),
    ]
    return "\n".join(header + fake_variants(rng, len(samples))) + "\n"


def fastq(name_for, rng: random.Random, n_reads: int = 25) -> str:
    out = []
    for i in range(n_reads):
        seq = "".join(rng.choice(BASES) for _ in range(50))
        out += [name_for(i), seq, "+", "I" * len(seq)]
    return "\n".join(out) + "\n"


def main() -> None:
    rng = random.Random(42)  # fixed seed = same files every time
    OUT.mkdir(exist_ok=True)

    (OUT / "leaky.vcf").write_text(vcf(
        samples=["Jane_Doe", "PT-19850412", "MRN00482913", "lab_sample_07"],
        meta=[
            "##fileDate=20260314",
            "##source=FakeCaller v2.1",
            "##reference=file:///Users/jdoe/projects/smithlab_cancer/ref/hg38.fa",
            '##FakeCallerCommandLine=<ID=Call,CommandLine="call --in '
            '/home/jdoe/raw/batch3.bam --out /data/smithlab/cohort/batch3.vcf">',
            "##contact=jdoe@example.org",
            "##server=10.12.4.27",
        ],
        rng=rng,
    ))

    (OUT / "clean.vcf").write_text(vcf(
        samples=["S1", "S2", "S3"],
        meta=["##source=FakeCaller v2.1"],
        rng=rng,
    ))

    (OUT / "leaky.fastq").write_text(fastq(
        lambda i: f"@M70421:118:000000000-KXJ4P:1:1101:{15000 + i}:{1300 + i} "
                  f"1:N:0:ATCACG+GCTTAA",
        rng,
    ))

    (OUT / "clean.fastq").write_text(fastq(lambda i: f"@read{i}", rng))

    for path in sorted(OUT.iterdir()):
        print(f"wrote {path.relative_to(OUT.parent)}")


if __name__ == "__main__":
    main()

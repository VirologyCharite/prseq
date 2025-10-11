#!/usr/bin/env python3
"""Coordinate and run all benchmarks, then display results."""

import argparse
import subprocess
import sys
from pathlib import Path


def ensure_data_exists(
    data_dir: Path,
    sequences: int,
    line_length: int,
    seed: int | None,
    seq_min: int,
    seq_max: int,
) -> tuple[Path, Path]:
    """Ensure benchmark data exists, generate if needed."""
    fasta_file = data_dir / "benchmark.fasta"
    fastq_file = data_dir / "benchmark.fastq"

    if not fasta_file.exists() or not fastq_file.exists():
        print("Generating benchmark data...")
        cmd = [
            sys.executable,
            "generate_data.py",
            "--sequences",
            str(sequences),
            "--line-length",
            str(line_length),
            "--seq-min",
            str(seq_min),
            "--seq-max",
            str(seq_max),
            "--output-dir",
            str(data_dir),
        ]
        if seed is not None:
            cmd.extend(["--seed", str(seed)])

        result = subprocess.run(cmd, check=True)
        if result.returncode != 0:
            print("Error generating data", file=sys.stderr)
            sys.exit(1)
        print()

    return fasta_file, fastq_file


def run_benchmark(script: Path, datafile: Path, size_hint: int = None) -> dict:
    """Run a single benchmark script and parse results."""
    cmd = [sys.executable, str(script), str(datafile)]
    if size_hint is not None:
        cmd.append(str(size_hint))

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error running {script.name}: {result.stderr}", file=sys.stderr)
        return None

    # Parse output
    lines = result.stdout.strip().split("\n")
    name = lines[0] if lines else "Unknown"
    stats = {}

    for line in lines[1:]:
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()

            # Extract numeric value
            if "Sequences" in key:
                stats["sequences"] = int(value.replace(",", ""))
            elif "Total bases" in key:
                stats["total_bases"] = int(value.replace(",", ""))
            elif "Time" in key:
                stats["time"] = float(value.rstrip("s"))
            elif "Throughput" in key:
                stats["throughput"] = float(value.split()[0])

    return {"name": name, **stats}


def print_results(fasta_results: list, fastq_results: list):
    """Print formatted benchmark results."""
    print("\n" + "=" * 120)
    print("BENCHMARK RESULTS")
    print("=" * 120)

    # Track stats for summary
    c_python_fasta_pct = 0
    c_python_fasta_slowdown = 0
    c_python_fastq_pct = 0
    c_python_fastq_slowdown = 0
    rust_fasta_pct = 0
    rust_fasta_slowdown = 0
    rust_fastq_pct = 0
    rust_fastq_slowdown = 0
    bio_fasta_pct = 0
    bio_fasta_slowdown = 0
    bio_fastq_pct = 0
    bio_fastq_slowdown = 0
    pure_fasta_pct = 0
    pure_fasta_slowdown = 0
    pure_fastq_pct = 0
    pure_fastq_slowdown = 0

    if fasta_results:
        print("\nFASTA Benchmarks:")
        print("-" * 120)
        print(
            f"{'Implementation':<20} {'Sequences':>12} {'Bases':>15} {'Time (s)':>10} {'Throughput':>15} {'% of C':>10} {'Slowdown':>10}"
        )
        print("-" * 120)

        # Get C baseline throughput (first result should be C)
        c_throughput = (
            fasta_results[0].get("throughput", 0)
            if fasta_results and fasta_results[0]
            else 0
        )

        for i, result in enumerate(fasta_results):
            if result:
                throughput = result.get("throughput", 0)
                pct_of_c = (
                    (throughput / c_throughput * 100) if c_throughput > 0 else 100
                )
                slowdown = (c_throughput / throughput) if throughput > 0 else 0

                # Store for summary (assuming order: C, C/Python, Rust, BioPython, Pure Python)
                if i == 1:
                    c_python_fasta_pct = pct_of_c
                    c_python_fasta_slowdown = slowdown
                elif i == 2:
                    rust_fasta_pct = pct_of_c
                    rust_fasta_slowdown = slowdown
                elif i == 3:
                    bio_fasta_pct = pct_of_c
                    bio_fasta_slowdown = slowdown
                elif i == 4:
                    pure_fasta_pct = pct_of_c
                    pure_fasta_slowdown = slowdown

                print(
                    f"{result['name']:<20} "
                    f"{result.get('sequences', 0):>12,} "
                    f"{result.get('total_bases', 0):>15,} "
                    f"{result.get('time', 0):>10.3f} "
                    f"{throughput:>12.2f} MB/s "
                    f"{pct_of_c:>9.1f}% "
                    f"{slowdown:>9.2f}x"
                )

    if fastq_results:
        print("\nFASTQ Benchmarks:")
        print("-" * 120)
        print(
            f"{'Implementation':<20} {'Sequences':>12} {'Bases':>15} {'Time (s)':>10} {'Throughput':>15} {'% of C':>10} {'Slowdown':>10}"
        )
        print("-" * 120)

        # Get C baseline throughput (first result should be C)
        c_throughput = (
            fastq_results[0].get("throughput", 0)
            if fastq_results and fastq_results[0]
            else 0
        )

        for i, result in enumerate(fastq_results):
            if result:
                throughput = result.get("throughput", 0)
                pct_of_c = (
                    (throughput / c_throughput * 100) if c_throughput > 0 else 100
                )
                slowdown = (c_throughput / throughput) if throughput > 0 else 0

                # Store for summary (assuming order: C, C/Python, Rust, BioPython, Pure Python)
                if i == 1:
                    c_python_fastq_pct = pct_of_c
                    c_python_fastq_slowdown = slowdown
                elif i == 2:
                    rust_fastq_pct = pct_of_c
                    rust_fastq_slowdown = slowdown
                elif i == 3:
                    bio_fastq_pct = pct_of_c
                    bio_fastq_slowdown = slowdown
                elif i == 4:
                    pure_fastq_pct = pct_of_c
                    pure_fastq_slowdown = slowdown

                print(
                    f"{result['name']:<20} "
                    f"{result.get('sequences', 0):>12,} "
                    f"{result.get('total_bases', 0):>15,} "
                    f"{result.get('time', 0):>10.3f} "
                    f"{throughput:>12.2f} MB/s "
                    f"{pct_of_c:>9.1f}% "
                    f"{slowdown:>9.2f}x"
                )

    print("=" * 120)

    # Print key findings summary
    print("\nKey findings:")
    if fasta_results and c_python_fasta_pct > 0:
        print(
            f"- C/Python: {c_python_fasta_pct:.1f}% of C speed for FASTA, "
            f"{c_python_fastq_pct:.1f}% for FASTQ ({c_python_fasta_slowdown:.2f}x slower)"
        )
    if fasta_results and rust_fasta_pct > 0:
        print(
            f"- Rust/Python (prseq): {rust_fasta_pct:.1f}% of C speed for FASTA, "
            f"{rust_fastq_pct:.1f}% for FASTQ ({rust_fasta_slowdown:.2f}x slower)"
        )
    if fastq_results and bio_fasta_pct > 0:
        print(
            f"- BioPython: {bio_fasta_pct:.1f}% of C speed for FASTA ({bio_fasta_slowdown:.2f}x slower), "
            f"{bio_fastq_pct:.1f}% for FASTQ ({bio_fastq_slowdown:.2f}x slower)"
        )
    if fasta_results and pure_fasta_pct > 0:
        print(
            f"- Pure Python: {pure_fasta_pct:.1f}% of C speed for FASTA ({pure_fasta_slowdown:.2f}x slower), "
            f"{pure_fastq_pct:.1f}% for FASTQ ({pure_fastq_slowdown:.2f}x slower)"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Run benchmarks comparing FASTA/FASTQ parsers"
    )
    parser.add_argument(
        "--sequences",
        type=int,
        default=500000,
        help="Number of sequences in benchmark data (default: 500,000)",
    )
    parser.add_argument(
        "--line-length",
        type=int,
        default=80,
        help="Line length for generated data (default: 80, -1 for unlimited)",
    )
    parser.add_argument("--seed", type=int, help="Random seed for data generation")
    parser.add_argument(
        "--seq-min",
        type=int,
        default=100,
        help="Minimum sequence length (default: 100)",
    )
    parser.add_argument(
        "--seq-max",
        type=int,
        default=20000,
        help="Maximum sequence length (default: 20,000)",
    )
    parser.add_argument(
        "--size-hint",
        type=int,
        help="Sequence size hint for Rust/Python implementation",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Data directory (default: data)",
    )
    parser.add_argument(
        "--fasta-only", action="store_true", help="Run only FASTA benchmarks"
    )
    parser.add_argument(
        "--fastq-only", action="store_true", help="Run only FASTQ benchmarks"
    )
    parser.add_argument(
        "--skip",
        action="append",
        choices=["rust", "biopython", "c", "c_python", "pure"],
        help="Skip specific implementations",
    )

    args = parser.parse_args()

    # Ensure data exists
    fasta_file, fastq_file = ensure_data_exists(
        args.data_dir,
        args.sequences,
        args.line_length,
        args.seed,
        args.seq_min,
        args.seq_max,
    )

    benchmark_dir = Path(__file__).parent / "benchmarks"
    skip = set(args.skip or [])

    fasta_results = []
    fastq_results = []

    # Run benchmarks
    implementations = [
        ("c", "bench_c.py"),
        ("c_python", "bench_c_python.py"),
        ("rust", "bench_rust_python.py"),
        ("biopython", "bench_biopython.py"),
        ("pure", "bench_pure_python.py"),
    ]

    for impl_name, script_name in implementations:
        if impl_name in skip:
            continue

        script = benchmark_dir / script_name
        # Only pass size hint to Rust/Python implementation
        size_hint = args.size_hint if impl_name == "rust" else None

        if not args.fastq_only:
            print(f"Running {impl_name} FASTA benchmark...")
            result = run_benchmark(script, fasta_file, size_hint)
            fasta_results.append(result)

        if not args.fasta_only:
            print(f"Running {impl_name} FASTQ benchmark...")
            result = run_benchmark(script, fastq_file, size_hint)
            fastq_results.append(result)

    # Print results
    print_results(
        fasta_results if not args.fastq_only else [],
        fastq_results if not args.fasta_only else [],
    )


if __name__ == "__main__":
    main()

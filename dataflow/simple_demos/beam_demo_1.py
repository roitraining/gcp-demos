"""
This is intentionally small, focused code meant to illustrate a few key Apache Beam concepts
in a minimal way. It is NOT production code; it's an educational demo. The key points shown here:

- How to read data into a PCollection using I/O transforms (ReadFromText).
- Element-wise transforms: Map (one-to-one), FlatMap (one-to-many), Filter (predicate).
- How to write results with WriteToText sinks.

Setup notes (local testing):
- Use pyenv to install a supported Python version (3.11 or earlier). For example:
    # Install a specific Python version using pyenv (3.11.x or earlier)
    # $ pyenv install 3.11.2
    # Create and activate a virtualenv (venv or pyenv-virtualenv):
    # $ python -m venv .venv
    # $ source .venv/bin/activate
    # Install dependencies (for local runs):
    # $ pip install apache-beam
    # If you plan to run on Google Cloud Dataflow and access GCS/BQ, install GCP extras:
    # $ pip install "apache-beam[gcp]"
"""

import apache_beam as beam
from apache_beam.io import ReadFromText, WriteToText
import sys


def count_words(line):
    """Count words in a single line.

    What it does:
    - Splits the incoming text line on whitespace and returns the word count (an int).

    Called by:
    - The 'CountWords' Map transform below. Beam calls this once per element in the input
        PCollection (one-to-one transform).
    """
    return len(line.split())


def lear_there(line):
    """FlatMap helper: yield the line if it contains the string 'Lear'.

    What it does:
    - Checks if the substring 'Lear' appears in the line. If yes, yields the line.
    - Because this is used with FlatMap, it can emit zero or more outputs per input.

    Called by:
    - The 'FlatMapLear' FlatMap transform below. FlatMap expects an iterable/generator
        of zero-or-more output elements per input element.
    """
    if "Lear" in line:
        yield line


# Build a Pipeline object. This is the root of your Beam program. The Pipeline object
# is used to apply transforms and then run the resulting graph.
p = beam.Pipeline(argv=sys.argv)


# Read: create an initial PCollection of text lines.
# Concept: ReadFromText is an I/O transform that returns a PCollection where each
# element is one line from the input file. Here we point to a sample file in GCS.
lines = p | "Read" >> ReadFromText("gs://dataflow-samples/shakespeare/kinglear.txt")


# Example sink: write the raw lines out to a file. This demonstrates a sink transform.
# Concept: Sinks are also transforms that consume PCollections.
_ = lines | "lines_out" >> WriteToText("beam_demo_1_lines.txt")


# Map transform: apply a function to each element, producing a one-to-one mapping.
# Concept: Map is useful for stateless, per-element computations. Note that you pass the function as an argument,
# with no other arguments. The receiving function will receive the next element of the input pcollection as it's first
# positional argument.
word_counts = lines | "CountWords" >> beam.Map(count_words)
_ = word_counts | "word_counts_out" >> WriteToText("beam_demo_1_word_counts.txt")


# FlatMap example: the supplied function may return zero, one, or many outputs per input.
# Concept: FlatMap is used when you need to expand or filter elements and potentially
# emit multiple outputs for a single input element. Again, the function is passed as an argument
# with no other arguments and will receive the next element of the input pcollection as it's first positional argument.
lear_there_flatmap = lines | "FlatMapLear" >> beam.FlatMap(lear_there)
_ = lear_there_flatmap | "lear_there_flatmap_out" >> WriteToText(
    "beam_demo_1_flatmap.txt"
)


# Filter: keep elements where the predicate is True.
# Lambda behavior: receives each element and returns True when 'Lear' is present.
# Use a lambda for short, one-off predicates; prefer a top-level function or DoFn
# when logic is non-trivial, reused, or to avoid potential runner/serialization issues.
lear_there_filter = lines | "FilterLear" >> beam.Filter(lambda x: "Lear" in x)
_ = lear_there_filter | "lear_there_filter_out" >> WriteToText("beam_demo_1_filter.txt")


# Run: execute the pipeline. For the DirectRunner this runs locally
p.run().wait_until_finish()


# End-of-file notes:
# - After running locally you should see files created in the current directory:
#   out_1-00000-of-00001, out_2-00000-of-00001, out_3-00000-of-00001, out_4-00000-of-00001
#   (WriteToText names are suffixed by shard information).
# - Inspect those files to verify the transformations: raw lines, numeric word counts,
#   lines containing 'Lear' produced by FlatMap, and lines selected by Filter.

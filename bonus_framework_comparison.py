"""Bonus: compare two evaluation styles on the same dataset.

This script avoids API keys by using:
1. RAGAS-inspired heuristic metrics from solution.solution.
2. DeepEval-style local assertions that behave like CI quality gates.

Run:
    python bonus_framework_comparison.py
"""

from __future__ import annotations

from dataclasses import dataclass

from solution.solution import BenchmarkRunner, QAPair, RAGASEvaluator


@dataclass
class Case:
    case_id: str
    qa: QAPair
    answer: str


CASES = [
    Case(
        "B01",
        QAPair(
            question="What is RAG?",
            expected_answer="RAG stands for Retrieval-Augmented Generation and combines retrieval with generation.",
            context="RAG stands for Retrieval-Augmented Generation. It combines document retrieval with text generation.",
        ),
        "What is RAG? RAG stands for Retrieval-Augmented Generation and combines retrieval with generation.",
    ),
    Case(
        "B02",
        QAPair(
            question="What does context precision reward?",
            expected_answer="Context precision rewards relevant chunks appearing earlier in the retrieved list.",
            context="Context precision is rank-aware and rewards relevant chunks that appear early.",
        ),
        "What does context precision reward? Context precision rewards relevant chunks appearing earlier in the retrieved list.",
    ),
    Case(
        "B03",
        QAPair(
            question="Should a RAG answer include unsupported facts?",
            expected_answer="No, a RAG answer should avoid unsupported facts and stay grounded in context.",
            context="Faithfulness checks whether answer claims are supported by context.",
        ),
        "Yes, it should add impressive facts even when the context does not mention them.",
    ),
    Case(
        "B04",
        QAPair(
            question="Why use regression testing?",
            expected_answer="Regression testing detects metric drops compared with a previous baseline.",
            context="Regression testing compares current evaluation scores with a baseline and flags drops.",
        ),
        "Why use regression testing? Regression testing detects metric drops compared with a previous baseline.",
    ),
]


def agent_fn(question: str) -> str:
    for case in CASES:
        if case.qa.question == question:
            return case.answer
    return ""


def deepeval_style_assertions(result, threshold: float = 0.5) -> dict[str, bool]:
    """Local DeepEval-style assertions: each metric is a quality gate."""
    return {
        "faithfulness_gate": result.faithfulness >= threshold,
        "relevance_gate": result.relevance >= threshold,
        "completeness_gate": result.completeness >= threshold,
        "conciseness_gate": RAGASEvaluator().evaluate_conciseness(result.actual_answer) >= 0.8,
    }


if __name__ == "__main__":
    evaluator = RAGASEvaluator()
    runner = BenchmarkRunner()
    results = runner.run([case.qa for case in CASES], agent_fn, evaluator)
    report = runner.generate_report(results)

    print("=== Framework 1: RAGAS-inspired heuristic report ===")
    print(f"pass_rate: {report['pass_rate']:.0%}")
    print(f"avg_faithfulness: {report['avg_faithfulness']:.3f}")
    print(f"avg_relevance: {report['avg_relevance']:.3f}")
    print(f"avg_completeness: {report['avg_completeness']:.3f}")
    print(f"failure_types: {report['failure_types']}")

    print("\n=== Framework 2: DeepEval-style local assertions ===")
    assertion_pass_count = 0
    for case, result in zip(CASES, results):
        gates = deepeval_style_assertions(result)
        passed = all(gates.values())
        assertion_pass_count += int(passed)
        print(f"{case.case_id}: {'PASS' if passed else 'FAIL'} | {gates}")

    print(f"\nDeepEval-style pass_rate: {assertion_pass_count / len(results):.0%}")

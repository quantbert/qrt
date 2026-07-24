from pydantic import BaseModel
import time
import pytest

import qrt as q


class LookupArgs(BaseModel):
    symbol: str


class PriceResult(BaseModel):
    price: float


def test_prompt_rendering_is_typed_and_hashed():
    prompt = q.ai.prompts.Prompt(name="memo", version="1.0", template="Review {symbol}", variables=("symbol",))
    rendered = prompt.render(symbol="ACME")
    assert rendered.text == "Review ACME"
    assert rendered.prompt_hash != rendered.rendered_hash


def test_tool_registry_validates_and_allowlists():
    @q.ai.tool(name="lookup_price", input=LookupArgs, output=PriceResult)
    def lookup(arguments):
        return {"price": 101.5 if arguments.symbol == "ACME" else 0}

    registry = q.ai.tools.ToolRegistry([lookup])
    assert registry.execute("lookup_price", {"symbol": "ACME"}) == PriceResult(price=101.5)
    try:
        registry.execute("delete_everything", {})
    except q.ai.tools.ToolExecutionError as exc:
        assert "not allowlisted" in str(exc)
    else:
        raise AssertionError("unknown tools must never execute")


def test_tool_timeout_does_not_wait_for_the_worker_to_finish():
    @q.ai.tool(name="slow", input=LookupArgs, output=PriceResult, timeout=0.01)
    def slow(arguments):
        time.sleep(0.2)
        return {"price": 1.0}

    started = time.monotonic()
    try:
        slow.execute({"symbol": "ACME"})
    except q.ai.tools.ToolExecutionError as exc:
        assert "exceeded" in str(exc)
    else:
        raise AssertionError("slow tool should time out")
    assert time.monotonic() - started < 0.1


def test_evaluation_suite_and_pydantic_dataset_conversion():
    suite = q.ai.evals.Suite(
        "extractor",
        [q.ai.evals.EvalCase(name="one", input="x", expected="X")],
        [q.ai.evals.exact_match],
    )
    report = suite.run(str.upper, subject_name="uppercase-v1")
    assert report.mean_score == 1.0
    pytest.importorskip("pydantic_evals")
    assert suite.to_pydantic_dataset().name == "extractor"
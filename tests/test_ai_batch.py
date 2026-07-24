import json

import pandas as pd
from pydantic import BaseModel

import qrt as q
from qrt.ai._backend import MemoryBackend


class Value(BaseModel):
    value: int


def test_batch_alignment_cache_artifacts_and_resume(tmp_path):
    attempts = {"bad": 0}

    def respond(request):
        text = request.messages[0].content[0].text
        if text == "bad" and attempts["bad"] == 0:
            attempts["bad"] += 1
            return "invalid"
        return json.dumps({"value": len(text)})

    client = q.ai.Client(
        providers={"test": q.ai.HostedProvider()},
        _backends={"test": MemoryBackend(respond)},
    )
    store = q.ai.storage.RunStore(tmp_path)
    frame = pd.DataFrame({"id": ["a", "b"], "text": ["good", "bad"]})

    run = q.ai.batch.extract(frame, key="id", input="text", client=client, model="test/model", output=Value, store=store)
    assert run.results.index.tolist() == ["a"]
    assert run.failures.index.tolist() == ["b"]
    assert (tmp_path / run.run_id / "results.parquet").exists()

    resumed = run.resume()
    assert resumed.results.index.tolist() == ["b"]
    assert resumed.failures.empty

    cached = q.ai.batch.extract(frame.iloc[:1], key="id", input="text", client=client, model="test/model", output=Value, store=store)
    assert bool(cached.results.loc["a", "cache_hit"])
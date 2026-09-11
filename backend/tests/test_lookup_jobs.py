import asyncio
import threading
from types import SimpleNamespace

from app.services.market import lookup_jobs as jobs


def test_background_lookup_deduplicates_and_survives_memory_cache_reset(tmp_path, monkeypatch):
    monkeypatch.setattr(jobs, '_directory', tmp_path)
    jobs._results.clear()
    release = threading.Event()
    calls = []

    def operation():
        calls.append(1)
        release.wait(2)
        return SimpleNamespace(model_dump=lambda **kw: {'status': 'AVAILABLE', 'options': ['real returned row']})

    async def scenario():
        first = await jobs.lookup('test', ['district'], operation, 3600)
        second = await jobs.lookup('test', ['district'], operation, 3600)
        assert first['status'] == second['status'] == 'PENDING'
        release.set()
        await asyncio.gather(*list(jobs._tasks.values()))
        assert len(calls) == 1
        jobs._results.clear()
        cached = await jobs.lookup('test', ['district'], operation, 3600)
        assert cached['result']['options'] == ['real returned row']
        assert len(calls) == 1
    asyncio.run(scenario())


def test_different_parents_have_separate_results(tmp_path, monkeypatch):
    monkeypatch.setattr(jobs, '_directory', tmp_path)
    jobs._results.clear()

    async def scenario():
        for parent in ['one', 'two']:
            await jobs.lookup('test', [parent], lambda p=parent: SimpleNamespace(model_dump=lambda **kw: {'status': 'AVAILABLE', 'parent': p}), 3600)
        await asyncio.gather(*list(jobs._tasks.values()))
        for parent in ['one', 'two']:
            result = await jobs.lookup('test', [parent], None, 3600)
            assert result['result']['parent'] == parent
    asyncio.run(scenario())

"""Deduplicated background lookups with durable, dated successful results."""
import asyncio
import hashlib
import json
import logging
import time
from pathlib import Path

_tasks: dict[str, asyncio.Task] = {}
_results: dict[str, tuple[float, dict]] = {}
_retry_after: dict[str, float] = {}
_slots = asyncio.Semaphore(4)
_directory = Path(__file__).resolve().parents[3] / '.lookup-cache'
_logger = logging.getLogger(__name__)


async def lookup(kind, arguments, operation, ttl):
    key = hashlib.sha256(json.dumps([kind, arguments], sort_keys=True).encode()).hexdigest()
    if key not in _results:
        try:
            saved = json.loads((_directory / (key + '.json')).read_text())
            _results[key] = (saved['at'], saved['result'])
        except (OSError, ValueError, KeyError):
            pass
    previous = _results.get(key)
    fresh = previous and time.time() - previous[0] < ttl
    if not fresh and key not in _tasks and time.time() >= _retry_after.get(key, 0):
        if len(_tasks) >= 64:
            return {'status': 'PENDING', 'retry_after_ms': 3000}

        async def run():
            try:
                for attempt in range(3):
                    async with _slots:
                        result = (await asyncio.to_thread(operation)).model_dump(mode='json')
                    if result['status'] == 'AVAILABLE':
                        break
                    if attempt < 2:
                        await asyncio.sleep(2 ** attempt)
                at = time.time()
                _retry_after[key] = at + 15
                # Failed lookups are retained briefly to prevent retry storms.
                if result['status'] == 'AVAILABLE' or previous is None:
                    _results[key] = (at, result)
                if result['status'] == 'AVAILABLE':
                    try:
                        _directory.mkdir(exist_ok=True)
                        temporary = _directory / (key + '.tmp')
                        temporary.write_text(json.dumps({'at': at, 'result': result}))
                        temporary.replace(_directory / (key + '.json'))
                    except OSError:
                        _logger.warning('Could not persist lookup cache')
            except Exception:
                _logger.exception('Public lookup failed')
                if previous is None:
                    _results[key] = (time.time(), {'status': 'INSUFFICIENT', 'limitations': ['The source is currently unavailable. Please retry shortly.']})
            finally:
                _tasks.pop(key, None)
        _tasks[key] = asyncio.create_task(run())
    if previous:
        at, result = previous
        # A failed lookup may be retried after 15 seconds.
        if result['status'] != 'AVAILABLE' and time.time() - at >= 15 and key not in _tasks:
            _results.pop(key, None)
            return await lookup(kind, arguments, operation, ttl)
        return {'status': 'COMPLETE', 'result': result, 'cached_at': at, 'refreshing': key in _tasks}
    return {'status': 'PENDING', 'retry_after_ms': 1000}

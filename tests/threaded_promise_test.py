from concurrent.futures import ThreadPoolExecutor

from pytest import raises

from earwax import ThreadedPromise, ThreadedPromiseStates


def test_init(thread_pool: ThreadPoolExecutor) -> None:
    p: ThreadedPromise = ThreadedPromise(thread_pool)
    assert p.thread_pool is thread_pool
    assert p.state is ThreadedPromiseStates.not_ready
    assert p.future is None
    assert p.func is None
    with raises(RuntimeError):
        p.run()

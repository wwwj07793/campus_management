from __future__ import annotations

from typing import Any, Callable, Iterable, TypeVar

from sqlalchemy import event
from sqlalchemy.orm import Session

from core.cache import cache


ModelT = TypeVar("ModelT")
_MISSING = object()
_CACHE_ACTIONS_KEY = "cache_after_commit_actions"
_CACHE_EVENTS_BOUND_KEY = "cache_events_bound"


def register_cache_action(session: Session, action: Callable[[], None]) -> None:
    if not session.in_transaction():
        action()
        return

    _bind_cache_events(session)
    session.info.setdefault(_CACHE_ACTIONS_KEY, []).append(action)


def cache_set_after_commit(session: Session, key: str, value: Any) -> None:
    register_cache_action(session, lambda key=key, value=value: cache.set(key, value))


def cache_delete_after_commit(session: Session, key: str) -> None:
    register_cache_action(session, lambda key=key: cache.delete(key))


def cache_delete_prefix_after_commit(session: Session, prefix: str) -> None:
    register_cache_action(session, lambda prefix=prefix: cache.delete_prefix(prefix))


def cache_call_after_commit(session: Session, action: Callable[[], None]) -> None:
    register_cache_action(session, action)


def cached_value(key: str, factory: Callable[[], Any]) -> Any:
    value = cache.get(key, default=_MISSING)
    if value is not _MISSING:
        return value

    value = factory()
    cache.set(key, value)
    return value


def cached_model_by_id(
    session: Session,
    key: str,
    model: type[ModelT],
    factory: Callable[[], ModelT | None],
    validator: Callable[[ModelT], bool] | None = None,
) -> ModelT | None:
    if _has_pending_cache_actions(session):
        return factory()

    object_id = cached_value(
        key,
        lambda: _model_id(factory()),
    )
    if object_id is None:
        return None
    item = session.get(model, object_id)
    if item is not None and (validator is None or validator(item)):
        return item

    cache.delete(key)
    item = factory()
    cache.set(key, _model_id(item))
    return item


def cached_model_by_composite_key(
    session: Session,
    key: str,
    model: type[ModelT],
    factory: Callable[[], ModelT | None],
) -> ModelT | None:
    if _has_pending_cache_actions(session):
        return factory()

    object_key = cached_value(
        key,
        lambda: _composite_key(factory()),
    )
    if object_key is None:
        return None
    item = session.get(model, object_key)
    if item is not None:
        return item

    cache.delete(key)
    item = factory()
    cache.set(key, _composite_key(item))
    return item


def cached_models_by_ids(
    session: Session,
    key: str,
    model: type[ModelT],
    factory: Callable[[], Iterable[ModelT]],
) -> list[ModelT]:
    if _has_pending_cache_actions(session):
        return list(factory())

    object_ids = cached_value(
        key,
        lambda: [_model_id(item) for item in factory()],
    )
    objects = _load_models_by_ids(session, model, object_ids)
    if len(objects) == len([object_id for object_id in object_ids if object_id is not None]):
        return objects

    cache.delete(key)
    objects = list(factory())
    cache.set(key, [_model_id(item) for item in objects])
    return objects


def cached_models_by_composite_keys(
    session: Session,
    key: str,
    model: type[ModelT],
    factory: Callable[[], Iterable[ModelT]],
) -> list[ModelT]:
    if _has_pending_cache_actions(session):
        return list(factory())

    object_keys = cached_value(
        key,
        lambda: [
            (item.student_id, item.course_id)
            for item in factory()
        ],
    )
    objects = _load_models_by_ids(session, model, object_keys)
    if len(objects) == len([object_key for object_key in object_keys if object_key is not None]):
        return objects

    cache.delete(key)
    objects = list(factory())
    cache.set(
        key,
        [
            (item.student_id, item.course_id)
            for item in objects
        ],
    )
    return objects


def _model_id(model: Any) -> int | None:
    if model is None:
        return None
    return model.id


def _composite_key(model: Any) -> tuple[int, int] | None:
    if model is None:
        return None
    return (model.student_id, model.course_id)


def _load_models_by_ids(
    session: Session,
    model: type[ModelT],
    object_ids: Iterable[Any],
) -> list[ModelT]:
    objects: list[ModelT] = []
    for object_id in object_ids:
        if object_id is None:
            continue
        item = session.get(model, object_id)
        if item is not None:
            objects.append(item)
    return objects


def _bind_cache_events(session: Session) -> None:
    if session.info.get(_CACHE_EVENTS_BOUND_KEY):
        return

    event.listen(session, "after_commit", _run_cache_actions)
    event.listen(session, "after_rollback", _clear_cache_actions)
    session.info[_CACHE_EVENTS_BOUND_KEY] = True


def _run_cache_actions(session: Session) -> None:
    actions = session.info.pop(_CACHE_ACTIONS_KEY, [])
    for action in actions:
        action()


def _clear_cache_actions(session: Session) -> None:
    session.info.pop(_CACHE_ACTIONS_KEY, None)


def _has_pending_cache_actions(session: Session) -> bool:
    return bool(session.info.get(_CACHE_ACTIONS_KEY))

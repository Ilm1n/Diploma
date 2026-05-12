# Backend Architecture Notes

New backend work should follow the feature-based flow:

`router -> schemas -> dto -> use_cases -> repository/permissions -> UnitOfWork -> events`

Routers own FastAPI details only: path/query/body dependencies, request schema mapping, response models, cookies, redirects, and background tasks.

Use cases own business scenarios. They should not import FastAPI, should raise `AppError` subclasses instead of `HTTPException`, and should collect domain events instead of publishing realtime directly.

Repositories own SQLAlchemy access only. They must not call `commit()` or `rollback()`.

Permissions modules own role and access rules. FastAPI dependencies may exist as thin adapters over repositories and policies.

`UnitOfWork` owns transaction boundaries. It commits once, rolls back on errors, and dispatches collected domain events only after a successful commit.

Feature `events.py` files map domain events to current realtime payloads. Future activity logging should consume the same domain events rather than being written manually in use cases.

Read scenarios should still go through query use cases and repositories. They do not need a `UnitOfWork` unless they intentionally mutate state.

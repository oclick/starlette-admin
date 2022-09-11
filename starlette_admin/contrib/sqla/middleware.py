from contextlib import contextmanager
from typing import Generator

from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp
from starlette_admin.contrib.sqla._types import ENGINE_TYPE


class DBSessionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, engine: ENGINE_TYPE) -> None:
        super().__init__(app)
        self.engine = engine

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if isinstance(self.engine, AsyncEngine):
            async with AsyncSession(self.engine, expire_on_commit=False) as session:
                request.state.session = session
                response = await call_next(request)
                return response
        else:
            with get_session(self.engine) as session:
                request.state.session = session
                response = await call_next(request)
                return response


@contextmanager
def get_session(engine: Engine) -> Generator[Session, None, None]:
    session: Session = Session(engine, expire_on_commit=False)
    try:
        yield session
    except Exception as e:  # pragma: no cover
        session.rollback()
        raise e
    finally:
        session.close()
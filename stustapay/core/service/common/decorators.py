import json
from functools import wraps
from inspect import signature
from typing import Optional

from stustapay.core.service.common.error import AccessDenied
from stustapay.core.schema.terminal import Terminal
from stustapay.core.schema.user import User, Privilege


def with_db_connection(func):
    @wraps(func)
    async def wrapper(self, **kwargs):
        if "conn" in kwargs:
            return await func(self, **kwargs)

        async with self.db_pool.acquire() as conn:
            # leads to slow queries in some cases
            await conn.set_type_codec("json", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")

            return await func(self, conn=conn, **kwargs)

    return wrapper


def with_db_transaction(func):
    @wraps(func)
    async def wrapper(self, **kwargs):
        if "conn" in kwargs:
            return await func(self, **kwargs)

        async with self.db_pool.acquire() as conn:
            # leads to slow queries in some cases
            await conn.set_type_codec("json", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")

            async with conn.transaction():
                return await func(self, conn=conn, **kwargs)

    return wrapper


def requires_user_privileges(privileges: Optional[list[Privilege]] = None):
    """
    Check if a user is logged in via a user jwt token and has ALL provided privileges.
    If the current_user is already know from a previous authentication, it can be used the check the privileges
    Sets the arguments current_user in the wrapped function
    """

    def f(func):
        @wraps(func)
        async def wrapper(self, **kwargs):
            if "token" not in kwargs and "current_user" not in kwargs:
                raise RuntimeError("token or user was not provided to service function call")

            if "conn" not in kwargs:
                raise RuntimeError(
                    "requires_user_privileges needs a database connection, "
                    "with_db_transaction needs to be put before this decorator"
                )

            token = kwargs["token"] if "token" in kwargs else None
            user = kwargs["current_user"] if "current_user" in kwargs else None
            conn = kwargs["conn"]
            if user is None:
                if self.__class__.__name__ == "AuthService":
                    user = await self.get_user_from_token(conn=conn, token=token)
                elif hasattr(self, "auth_service"):
                    user = await self.auth_service.get_user_from_token(conn=conn, token=token)
                else:
                    raise RuntimeError("requires_terminal needs self.auth_service to be a AuthService instance")

            if user is None:
                raise AccessDenied("invalid user token")

            if privileges:
                if not any([p in privileges for p in user.privileges]):
                    raise AccessDenied(f"user does not have any of the required privileges: {privileges}")

            if "current_user" in signature(func).parameters:
                kwargs["current_user"] = user
            elif "current_user" in kwargs:
                kwargs.pop("current_user")

            if "token" not in signature(func).parameters and "token" in kwargs:
                kwargs.pop("token")

            return await func(self, **kwargs)

        return wrapper

    return f

def requires_customer(func):
    """
    Check if a customer is logged in via a customer jwt token
    If the current_customer is already know from a previous authentication, it can be used the check the privileges
    Sets the arguments current_customer in the wrapped function
    """
    @wraps(func)
    async def wrapper(self, **kwargs):
        if "token" not in kwargs and "current_customer" not in kwargs:
            raise RuntimeError("token or customer was not provided to service function call")

        if "conn" not in kwargs:
            raise RuntimeError(
                "requires_customer_privileges needs a database connection, "
                "with_db_transaction needs to be put before this decorator"
            )

        token = kwargs["token"] if "token" in kwargs else None
        customer = kwargs["current_customer"] if "current_customer" in kwargs else None
        conn = kwargs["conn"]
        if customer is None:
            if self.__class__.__name__ == "AuthService":
                customer = await self.get_customer_from_token(conn=conn, token=token)
            elif hasattr(self, "auth_service"):
                customer = await self.auth_service.get_customer_from_token(conn=conn, token=token)
            else:
                raise RuntimeError("requires_terminal needs self.auth_service to be a AuthService instance")

        if customer is None:
            raise AccessDenied("invalid customer token")

        if "current_customer" in signature(func).parameters:
            kwargs["current_customer"] = customer
        elif "current_customer" in kwargs:
            kwargs.pop("current_customer")

        if "token" not in signature(func).parameters and "token" in kwargs:
            kwargs.pop("token")

        return await func(self, **kwargs)

    return wrapper


def requires_terminal(user_privileges: Optional[list[Privilege]] = None):
    """
    Check if a terminal is logged in via a provided terminal jwt token
    Further, if privileges are provided, checks if a user is logged in and if it has ALL provided privileges
    Sets the arguments current_terminal and current_user in the wrapped function
    """

    def f(func):
        @wraps(func)
        async def wrapper(self, **kwargs):
            if "token" not in kwargs and "current_terminal" not in kwargs:
                raise RuntimeError("token was not provided to service function call")

            if "conn" not in kwargs:
                raise RuntimeError(
                    "requires_terminal needs a database connection, "
                    "with_db_transaction needs to be put before this decorator"
                )

            token = kwargs["token"] if "token" in kwargs else None
            terminal = kwargs["current_terminal"] if "current_terminal" in kwargs else None
            conn = kwargs["conn"]
            if terminal is None:
                if self.__class__.__name__ == "AuthService":
                    terminal: Terminal = await self.get_terminal_from_token(conn=conn, token=token)
                elif hasattr(self, "auth_service"):
                    terminal: Terminal = await self.auth_service.get_terminal_from_token(conn=conn, token=token)
                else:
                    raise RuntimeError("requires_terminal needs self.auth_service to be a AuthService instance")

            if terminal is None:
                raise AccessDenied("invalid terminal token")

            if user_privileges is not None:
                if terminal.till.active_user_id is None:
                    raise AccessDenied(
                        f"no user is logged into this terminal but "
                        f"the following privileges are required {user_privileges}"
                    )

                logged_in_user = User.parse_obj(
                    await kwargs["conn"].fetchrow(
                        "select * from usr_with_privileges where id = $1", terminal.till.active_user_id
                    )
                )

                if not any([p in user_privileges for p in logged_in_user.privileges]):
                    raise AccessDenied(f"user does not have any of the required privileges: {user_privileges}")

                if "current_user" in signature(func).parameters:
                    kwargs["current_user"] = logged_in_user
                elif "current_user" in kwargs:
                    kwargs.pop("current_user")

            if "current_terminal" in signature(func).parameters:
                kwargs["current_terminal"] = terminal
            elif "current_terminal" in kwargs:
                kwargs.pop("current_terminal")

            if "token" not in signature(func).parameters and "token" in kwargs:
                kwargs.pop("token")

            return await func(self, **kwargs)

        return wrapper

    return f

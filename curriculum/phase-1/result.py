from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, Never, TypeVar


SuccessT = TypeVar("SuccessT", covariant=True)
ErrorT = TypeVar("ErrorT", covariant=True)

NextSuccessT = TypeVar("NextSuccessT")
NextErrorT = TypeVar("NextErrorT")


class Result(ABC, Generic[SuccessT, ErrorT]):
    @abstractmethod
    def map(
        self,
        operation: Callable[[SuccessT], NextSuccessT],
    ) -> Result[NextSuccessT, ErrorT]:
        """Transform an Ok value without changing the error type."""
        ...

    @abstractmethod
    def and_then(
        self,
        operation: Callable[
            [SuccessT],
            Result[NextSuccessT, NextErrorT],
        ],
    ) -> Result[
        NextSuccessT,
        ErrorT | NextErrorT,
    ]:
        """Run the next fallible operation only when this result is Ok."""
        ...


@dataclass(frozen=True, slots=True)
class Ok(Result[SuccessT, Never], Generic[SuccessT]):
    value: SuccessT

    def map(
        self,
        operation: Callable[[SuccessT], NextSuccessT],
    ) -> Result[NextSuccessT, Never]:
        return Ok(operation(self.value))

    def and_then(
        self,
        operation: Callable[
            [SuccessT],
            Result[NextSuccessT, NextErrorT],
        ],
    ) -> Result[NextSuccessT, NextErrorT]:
        return operation(self.value)


@dataclass(frozen=True, slots=True)
class Err(Result[Never, ErrorT], Generic[ErrorT]):
    error: ErrorT

    def map(
        self,
        operation: Callable[[Never], NextSuccessT],
    ) -> Result[NextSuccessT, ErrorT]:
        return self

    def and_then(
        self,
        operation: Callable[
            [Never],
            Result[NextSuccessT, NextErrorT],
        ],
    ) -> Result[
        NextSuccessT,
        ErrorT | NextErrorT,
    ]:
        return self

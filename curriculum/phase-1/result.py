from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, Never, TypeVar


T = TypeVar("T", covariant=True)
E = TypeVar("E", covariant=True)

U = TypeVar("U")
F = TypeVar("F")


class Result(ABC, Generic[T, E]):
    @abstractmethod
    def map(
        self,
        operation: Callable[[T], U],
    ) -> Result[U, E]:
        pass

    @abstractmethod
    def map_err(
        self,
        operation: Callable[[E], F],
    ) -> Result[T, F]:
        pass

    @abstractmethod
    def and_then(
        self,
        operation: Callable[[T], Result[U, F]],
    ) -> Result[U, E | F]:
        pass

    @abstractmethod
    def or_else(
        self,
        operation: Callable[[E], Result[U, F]],
    ) -> Result[T | U, F]:
        pass

    @abstractmethod
    def is_ok(self) -> bool:
        pass

    @abstractmethod
    def is_err(self) -> bool:
        pass


# OK
@dataclass(frozen=True, slots=True)
class Ok(Result[T, Never], Generic[T]):
    value: T

    def map(
        self,
        operation: Callable[[T], U],
    ) -> Result[U, Never]:
        return Ok(operation(self.value))

    def map_err(
        self,
        operation: Callable[[Never], F],
    ) -> Result[T, F]:
        return self

    def and_then(
        self,
        operation: Callable[[T], Result[U, F]],
    ) -> Result[U, F]:
        return operation(self.value)

    def or_else(
        self,
        operation: Callable[[Never], Result[U, F]],
    ) -> Result[T | U, F]:
        return self

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False


# Err
@dataclass(frozen=True, slots=True)
class Err(Result[Never, E], Generic[E]):
    error: E

    def map(
        self,
        operation: Callable[[Never], U],
    ) -> Result[U, E]:
        return self

    def map_err(
        self,
        operation: Callable[[E], F],
    ) -> Result[Never, F]:
        return Err(operation(self.error))

    def and_then(
        self,
        operation: Callable[[Never], Result[U, F]],
    ) -> Result[U, E | F]:
        return self

    def or_else(
        self,
        operation: Callable[[E], Result[U, F]],
    ) -> Result[U, F]:
        return operation(self.error)

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

from typing import Generic, TypeVar, Optional

T = TypeVar('T')


class Result(Generic[T]):
    def __init__(
        self,
        success: bool,
        data: Optional[T] = None,
        message: str = "Success",
        error_code: Optional[str] = None,
        status_code: int = 200,
    ):
        self.success = success
        self.data = data
        self.message = message
        self.error_code = error_code
        self.status_code = status_code

    @classmethod
    def success_result(cls, data: T, message: str = "Success", status_code: int = 200):
        return cls(success=True, data=data, message=message, status_code=status_code)

    @classmethod
    def failure_result(cls, message: str, error_code: Optional[str] = None, status_code: int = 400):
        return cls(success=False, message=message, error_code=error_code, status_code=status_code)

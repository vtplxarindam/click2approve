from fastapi import HTTPException


class AppException(HTTPException):
    def __init__(self, status_code: int, detail: str, title: str = "Error"):
        super().__init__(status_code=status_code, detail=detail)
        self.title = title


class ValidationException(AppException):
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail, title="Validation Error")


class AuthenticationException(AppException):
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=401, detail=detail, title="Authentication Error")


class AuthorizationException(AppException):
    def __init__(self, detail: str = "Access denied"):
        super().__init__(status_code=403, detail=detail, title="Authorization Error")


class NotFoundException(AppException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=404, detail=detail, title="Not Found")
import re
from collections.abc import Sequence
from typing import TYPE_CHECKING, Annotated, Any, Callable, TypeAlias

from api.exceptions.categories.validator import ValidationError
from pydantic import BeforeValidator

if TYPE_CHECKING:
    from api.models.schema.user import UserPermission

DEFAULT_DENIED_SYMBOLS = r'\/:*?"<>|@'
ALLOWED_ALPHANUMERIC = r"a-zA-Z0-9"
ALLOWED_ALPHANUMERIC_WITH_HYPHEN = rf"{ALLOWED_ALPHANUMERIC}\-"
ALLOWED_ITEM_CODE = rf"{ALLOWED_ALPHANUMERIC}\-/"
ALLOWED_ALPHANUMERIC_WITH_UNDERSCORE = r"A-Za-z0-9_"


def required_validator(value: str) -> str:
    if not value or not value.strip():
        raise ValidationError("必須項目が入力されていません")
    return value


def denied_symbol_validator(denied: str) -> Callable[[str], str]:
    def _validator(value: str) -> str:
        if re.search(f"[{re.escape(denied)}]", value):
            example_text = ", ".join(denied)
            raise ValidationError(f"使用できない記号が入っています（例：{example_text}）")
        return value

    return _validator


def allowed_character_validator(allowed: str) -> Callable[[str], str]:
    def _validator(value: str) -> str:
        if value and not re.fullmatch(f"^[{allowed}]+$", value):
            raise ValidationError("使用できない文字が含まれています")
        return value

    return _validator


def required_symbol_validator(required_symbols: str) -> Callable[[str], str]:
    def _validator(value: str) -> str:
        if value:
            missing_symbols = [
                symbol for symbol in required_symbols if symbol not in value
            ]
            if missing_symbols:
                raise ValidationError(f"必須の記号が入っていません：{', '.join(missing_symbols)}")
        return value

    return _validator


def length_validator(
    *,
    ge: int | None = None,
    le: int | None = None,
) -> Callable[[str | Sequence[Any]], str | Sequence[Any]]:
    def _validator(value: str | Sequence) -> str | Sequence:
        if value is not None:
            value_length = len(value)
            if ge is not None and value_length < ge:
                error_message = (
                    f"{ge}文字以上で入力してください" if isinstance(value, str) else f"最小要素数は{ge}です"
                )
                raise ValidationError(error_message)
            if le is not None and value_length > le:
                error_message = (
                    f"{le}文字以下で入力してください" if isinstance(value, str) else f"最大要素数は{le}です"
                )
                raise ValidationError(error_message)
        return value

    return _validator


def no_whitespace_only_validator(value: str) -> str:
    if value and not value.strip():
        raise ValidationError("使用できない文字が含まれています。（例：空白文字など）")
    return value


def number_range_validator(
    ge: int | float | None = None, le: int | float | None = None
) -> Callable[[int | float], int | float]:
    def _validator(value: int | float) -> int | float:
        if ge is not None and value < ge:
            raise ValidationError(f"{ge}以上で入力してください")
        if le is not None and value > le:
            raise ValidationError(f"{le}以下で入力してください")
        return value

    return _validator


def is_int_validator(value: Any) -> int:
    if not isinstance(value, int):
        raise ValidationError("半角数字を入力してください")
    return value


def login_id_validator(value: str) -> str:
    if (
        not value
        or not value.strip()
        or re.search(r"<\/?script.*?>", value, re.IGNORECASE)
    ):
        raise ValidationError("メールアドレスまたはパスワードが異なります")
    return value


def password_validator(value: str) -> str:
    denied_symbols = DEFAULT_DENIED_SYMBOLS.replace("@", "")
    if any(s in denied_symbols for s in value):
        raise ValidationError(f"使用できない記号が入っています（例：{', '.join(denied_symbols)}）")

    pattern_parts = [
        r"(?=.*[A-Z])",  # 大文字を含む
        r"(?=.*[a-z])",  # 小文字を含む
        r"(?=.*\d)",  # 数字を含む
        r"(?=.*[!@#$%^&()_+=\-\[\]{};,'~`])",  # 許可された記号を含む
        r".{8,64}$",  # 長さ制限
    ]
    pattern = "".join(pattern_parts)
    if not re.match(pattern, value):
        raise ValidationError("パスワードは8桁以上64桁以下で、大文字、小文字、数字、記号を含む必要があります")

    return value


def user_permission_validator(value: "UserPermission") -> "UserPermission":
    from api.models.schema.user import UserPermission

    if not value or not value.strip() or not UserPermission.contains(value):
        raise ValidationError("権限を選択してください")
    return value


# user
UserNameStr: TypeAlias = Annotated[
    str,
    BeforeValidator(allowed_character_validator(ALLOWED_ALPHANUMERIC_WITH_UNDERSCORE)),
    BeforeValidator(length_validator(le=20)),
    BeforeValidator(required_validator),
]
UserEmailStr: TypeAlias = Annotated[
    str,
    BeforeValidator(denied_symbol_validator(DEFAULT_DENIED_SYMBOLS.replace("@", ""))),
    BeforeValidator(required_symbol_validator("@")),
    BeforeValidator(length_validator(le=255)),
    BeforeValidator(required_validator),
]
UserPermissionEnum: TypeAlias = Annotated[
    "UserPermission",
    BeforeValidator(user_permission_validator),
]

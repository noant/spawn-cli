from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class NavFile(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    path: str
    description: str


class NavExtGroup(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ext: str
    files: list[NavFile] = Field(default_factory=list)


class NavRuleRow(BaseModel):
    """Maintainer ``read-required`` ``rules`` row: file-backed (``path``) or hint-only (``hint``), never both."""

    model_config = ConfigDict(populate_by_name=True)

    path: str | None = None
    description: str | None = None
    hint: str | None = None

    @model_validator(mode='after')
    def path_xor_hint(self) -> NavRuleRow:
        path_ok = bool(self.path and str(self.path).strip())
        hint_ok = bool(self.hint and str(self.hint).strip())
        if not path_ok and not hint_ok:
            raise ValueError('navigation rule row needs a non-empty path or a non-empty hint')
        if path_ok and hint_ok:
            raise ValueError(
                'navigation rule row cannot combine path and hint; use a standalone hint-only row'
            )
        return self


class NavRulesGroup(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    rules: list[NavRuleRow] = Field(default_factory=list)


class NavigationFile(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    read_required: list[dict] = Field(default_factory=list, alias="read-required")
    read_contextual: list[dict] = Field(default_factory=list, alias="read-contextual")

from typing import Any, Callable, Iterable

from transctl.models.engine_config import EngineConfig

import click


def styled_prompt(label: str, default: Any | None = None, *, value_proc: Any | None = None,
                  type_: Any | None = None) -> Any:
    lines: list[str] = [click.style(label, fg="cyan")]

    # Choices (for click.Choice)
    if isinstance(type_, click.Choice):
        choices: str = ", ".join(type_.choices)
        lines.append(
            f"{click.style('choices:', fg='bright_black')} "
            f"{click.style(choices, fg='yellow')}"
        )

    # Default
    if default not in (None, ""):
        lines.append(
            f"{click.style('default:', fg='bright_black')} "
            f"{click.style(str(default), fg='green')}"
        )

    prompt_text: str = "\n".join(lines) + "\n> "

    return click.prompt(
        prompt_text,
        default=default,
        show_default=False,
        value_proc=value_proc,
        type=type_,
        show_choices=False,
    )


def construct_engine_params(engine_model: EngineConfig) -> dict[str, str]:
    params: dict[str, str] = {}
    header_printed: bool = False

    def print_header() -> None:
        click.echo()
        click.secho("Engine configuration", fg="cyan", bold=True)
        click.secho("Please provide the settings required by the selected engine.", fg="bright_black")
        click.echo()

    for field_name, field in engine_model.model_fields.items():
        raw_extra: dict[str, Any] | Callable[[dict[str, Any]], None] | None = field.json_schema_extra

        extra: dict[str, Any]
        if raw_extra is None:
            extra = {}
        elif callable(raw_extra):
            tmp: dict[str, Any] = {}
            raw_extra(tmp)  # callable mutates tmp in-place
            extra = dict(tmp)
        else:
            extra = dict(raw_extra)

        # skip invisible fields
        if not extra.get("visible", True):
            continue

        if not header_printed:
            print_header()
            header_printed = True

        ui_label: str = field.title if field.title else field_name.replace("_", " ").capitalize()
        params[field_name] = styled_prompt(
            f"{ui_label}",
            type_=field.annotation if field.annotation is not None else None,
            value_proc=None,
        )

    return params


def parse_key_value_pairs(pairs: Iterable[str]) -> dict[str, str]:
    result: dict[str, str] = {}

    for item in pairs:
        if "=" not in item:
            raise ValueError(f"Invalid parameter '{item}'. Expected format KEY=VALUE.")

        key, value = item.split("=", 1)

        key = key.strip()
        value = value.strip()

        if not key:
            raise ValueError(f"Invalid parameter '{item}'. Key cannot be empty.")

        result[key] = value

    return result
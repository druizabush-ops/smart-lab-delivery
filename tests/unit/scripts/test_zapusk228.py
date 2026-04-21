"""Тесты административного инструмента ZAPUSK228."""

from __future__ import annotations

from scripts.zapusk228 import CommandRunner, Zapusk228, Zapusk228Config


class RecordingRunner(CommandRunner):
    """Runner-двойник, записывающий команды без выполнения."""

    def __init__(self) -> None:
        super().__init__(dry_run=True)
        self.commands: list[tuple[list[str], str | None]] = []

    def run(self, command: list[str], *, cwd=None, check: bool = True) -> int:  # noqa: ANN001
        self.commands.append((command, str(cwd) if cwd is not None else None))
        return 0


def _full_config(*, assume_yes: bool) -> Zapusk228Config:
    return Zapusk228Config(
        update_code=True,
        install_deps=True,
        run_migrations=True,
        rebuild_frontend=True,
        restart_services=True,
        run_smoke=True,
        run_tests=True,
        assume_yes=assume_yes,
        dry_run=True,
    )


def test_zapusk228_runs_expected_commands_in_assume_yes_mode() -> None:
    runner = RecordingRunner()
    tool = Zapusk228(
        config=_full_config(assume_yes=True),
        runner=runner,
    )

    tool.execute()

    commands = [item[0] for item in runner.commands]
    assert ["git", "fetch", "origin"] in commands
    assert ["git", "checkout", "main"] in commands
    assert ["git", "pull", "origin", "main"] in commands
    assert ["python", "-m", "alembic", "upgrade", "head"] in commands
    assert ["python", "-m", "pytest"] in commands


def test_zapusk228_interactive_decline_skips_all_steps() -> None:
    runner = RecordingRunner()
    tool = Zapusk228(
        config=_full_config(assume_yes=False),
        runner=runner,
        input_fn=lambda _: "n",
    )

    tool.execute()

    assert runner.commands == []

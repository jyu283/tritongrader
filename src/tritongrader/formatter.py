from typing import Dict, Callable, List, Union, Iterable, Tuple, Optional
from tritongrader import Autograder

from tritongrader.test_case import TestCaseBase
from tritongrader.test_case import IOTestCase
from tritongrader.test_case import BasicTestCase
from tritongrader.test_case import CustomTestCase


class ResultsFormatterBase:
    def __init__(self, src: Union[Autograder, Iterable[Autograder]]):
        self.formatters: Dict[TestCaseBase, Callable[[TestCaseBase], None]] = {
            IOTestCase: self.format_io_test,
            BasicTestCase: self.format_basic_test,
            CustomTestCase: self.format_custom_test,
        }
        self.test_cases: List[TestCaseBase] = []
        ags = [src] if isinstance(src, Autograder) else src
        for autograder in ags:
            self.test_cases.extend(autograder.test_cases)

    def format_io_test(self, test: IOTestCase):
        raise NotImplementedError

    def format_basic_test(self, test: BasicTestCase):
        raise NotImplementedError

    def format_custom_test(self, test: CustomTestCase):
        raise NotImplementedError

    def format_test(self, test: TestCaseBase):
        return self.formatters[type(test)](test)

    def execute(self):
        raise NotImplementedError


class GradescopeResultsFormatter(ResultsFormatterBase):
    def __init__(
        self,
        src: Union[Autograder, Iterable[Autograder]],
        message: str = "",
        visibility: str = "visible",
        stdout_visibility: str = "hidden",
        hidden_tests_setting: str = "hidden",
        hide_points: bool = False,
        max_output_bytes: int = 5000,
        verbose: bool = True,
        html_diff: bool = True,
        leaderboard: List[Tuple[str, Optional[Union[int, float, str]], Optional[str]]] = None,
    ):
        super().__init__(src)
        self.message = message
        self.visibility: str = visibility
        self.stdout_visibility: str = stdout_visibility
        self.hidden_tests_setting: str = hidden_tests_setting
        self.hide_points: bool = hide_points
        self.max_output_bytes: int = max_output_bytes
        self.verbose: bool = verbose
        self.html_diff: bool = html_diff
        self.leaderboard: List[Tuple[str, Optional[Union[int, float, str]], Optional[str]]] = leaderboard

        self.results = {
            "output": self.message,
            "visibility": self.visibility,
            "stdout_visibility": self.stdout_visibility,
        }

    def generate_html_diff(self, test: IOTestCase):
        pass

    def basic_io_output(self, test: IOTestCase):
        if not test.result.has_run or not test.runner:
            return "This test was not run."

        if test.result.error:
            return "\n".join(
                [
                    "Unexpected runtime error!",
                    "== stdout ==",
                    test.actual_stdout,
                    "== stderr ==",
                    test.actual_stderr,
                ]
            )
        if test.result.timed_out:
            return "\n".join(
                [
                    f"Test case timed out. (limit={test.timeout})",
                    "== stdout ==",
                    test.actual_stdout,
                    "== stderr ==",
                    test.actual_stderr,
                ]
            )

        status_str = "PASSED" if test.result.passed else "FAILED"
        summary = []
        summary.append(f"{status_str} in {test.runner.running_time:.2f} ms.")

        if self.verbose:
            summary.extend(["== test command ==", test.command])

            if test.test_input is not None:
                summary.extend(["== test input ==", test.test_input])
            summary.extend(
                [
                    "== expected stdout ==",
                    test.expected_stdout,
                    "== expected stderr ==",
                ]
            )
            if not test.result.passed:
                summary.extend(
                    [
                        test.expected_stderr,
                        f"Return value: {test.runner.returncode}",
                        "== actual stdout ==",
                        test.actual_stdout,
                        "== actual stderr ==",
                        test.actual_stderr,
                    ]
                )

        return "\n".join(summary)

    def format_io_test(self, test: IOTestCase):
        return {
            "output_format": "html" if self.html_diff else "simple_format",
            "output": (
                self.generate_html_diff(test)
                if self.html_diff
                else self.basic_io_output(test)
            ),
        }

    def format_basic_test(self, test: BasicTestCase):
        summary = []
        summary.extend(
            [
                "== test command ==",
                test.command,
                "== return code ==",
                str(test.runner.returncode),
            ]
        )
        if self.verbose:
            summary.extend(
                [
                    "== stdout ==",
                    test.runner.stdout,
                    "== stderr ==",
                    test.runner.stderr,
                ]
            )
        return {"output": "\n".join(summary)}

    def format_custom_test(self, test: CustomTestCase):
        return {
            "output": test.result.output,
        }

    def format_test(self, test: TestCaseBase):
        item = {
            "name": test.name,
            "visibility": "visible" if not test.hidden else self.hidden_tests_setting,
        }
        if not self.hide_points:
            item["score"] = test.result.score
        if test.point_value is not None:
            item["max_score"] = test.point_value
        if test.result.passed is not None:
            item["status"] = "passed" if test.result.passed else "failed"

        item.update(super().format_test(test))
        return item

    def get_total_score(self):
        return sum(i.result.score for i in self.test_cases)

    def execute(self):
        self.results.update(
            {
                "score": self.get_total_score(),
                "tests": [self.format_test(i) for i in self.test_cases],
            }
        )
        if self.hide_points:
            self.results["score"] = 0
        if self.leaderboard:
            self.results["leaderboard"] = []
            for name, value, order in self.leaderboard:
                entry = {"name": name}
                if value is not None:
                    entry["value"] = value
                if order is not None:
                    entry["order"] = order
                self.results["leaderboard"].append(entry)

        return self.results


if __name__ == "__main__":
    formatter = GradescopeResultsFormatter()
    formatter.formatters[IOTestCase](None)

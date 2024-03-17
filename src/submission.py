import json
import os
import sys
import graderUtil

# a dict stores the final result
task_result = {"ini_cost": -1, "best_cost": -1, "locations": []}

#######################################################################
# read task file content
task_file = sys.argv[1]
task_content = graderUtil.load_task_file(task_file)
if task_content:
    print(task_content)
# BEGIN_YOUR_CODE

from dataclasses import dataclass
from typing_extensions import NamedTuple, TypedDict
from functools import lru_cache


class GridVector(NamedTuple):
    v: int
    "Vertical Scalar"
    h: int
    "Horizontal Scalar"

    @property
    def at_center(self) -> "GridVector":
        return GridVector(v=self.v, h=self.h)

    @property
    def at_down(self) -> "GridVector":
        return GridVector(v=self.v + 1, h=self.h)

    @property
    def at_left(self) -> "GridVector":
        return GridVector(v=self.v, h=self.h - 1)

    @property
    def at_right(self) -> "GridVector":
        return GridVector(v=self.v, h=self.h + 1)

    @property
    def at_up(self) -> "GridVector":
        return GridVector(v=self.v - 1, h=self.h)

    @property
    @lru_cache(maxsize=8)
    def as_grid(self) -> tuple["GridVector"]:
        from itertools import product as cartesian_product

        return tuple(
            GridVector(v=v, h=h)
            for v, h in cartesian_product(range(self.v), range(self.h))
        )

    @staticmethod
    def from_str(body: str) -> "GridVector":
        return GridVector(*map(int, body.split(",")[:2]))

    def l1_distance(self, other: "GridVector") -> int:
        "L1 Distance (Manhattan Distance)"
        return abs(self.v - other.v) + abs(self.h - other.h)

    def within_grid(self, location: "GridVector") -> bool:
        "Assume that self is the grid size"
        return (
            location.v >= 0
            and location.h >= 0
            and location.v < self.v
            and location.h < self.h
        )


class TaskResult(TypedDict):
    ini_cost: int
    best_cost: int
    locations: tuple[GridVector]


@dataclass
class _Task:
    "Basic Task"
    grid_size: GridVector
    kind: int
    playground_locations: tuple[GridVector]

    @staticmethod
    def from_list(body: list[str]) -> "_Task":
        return _Task(
            grid_size=GridVector.from_str(body[1]),
            kind=int(body[0]),
            playground_locations=tuple(
                map(
                    GridVector.from_str,
                    body[2].split("|")[1:],
                )
            ),
        )

    def resolve(self) -> TaskResult:
        raise NotImplementedError


@dataclass
class GLS_Task(_Task):
    "Greedy Local Search Task"
    initial_restroom_locations: tuple[GridVector]

    def resolve(self) -> TaskResult:
        initial_cost = self.get_cost(self.initial_restroom_locations)
        best_cost = initial_cost
        best_locations = self.initial_restroom_locations
        while state := self.step(best_cost, best_locations):
            best_cost, best_locations = state

        return TaskResult(
            ini_cost=initial_cost,
            best_cost=best_cost,
            locations=best_locations,
        )

    def step(
        self,
        current_cost: int,
        current_restroom_locations: tuple[GridVector],
    ) -> tuple[int, tuple[GridVector]] | None:
        "resolve - utility"
        from itertools import product as cartesian_product

        possible_next_restroom_locations = cartesian_product(
            *(
                tuple(
                    filter(
                        self.grid_size.within_grid,
                        (
                            current_restroom_location.at_center,
                            current_restroom_location.at_down,
                            current_restroom_location.at_left,
                            current_restroom_location.at_right,
                            current_restroom_location.at_up,
                        ),
                    )
                )
                for current_restroom_location in current_restroom_locations
            )
        )
        next_costs_and_restroom_locations = (
            (self.get_cost(next_restroom_locations), next_restroom_locations)
            for next_restroom_locations in filter(
                self.check_restroom_locations,
                possible_next_restroom_locations,
            )
        )
        better_cost, better_restroom_locations = min(next_costs_and_restroom_locations)
        for better_restroom_location in better_restroom_locations:
            if better_restroom_location in self.playground_locations:
                return
        if better_cost == current_cost:
            return
        return (better_cost, better_restroom_locations)

    def get_cost(self, restroom_locations: tuple[GridVector]) -> int:
        "resolve - utility"
        return sum(
            min(map(playground_location.l1_distance, restroom_locations))
            for playground_location in self.playground_locations
        )

    def check_restroom_locations(self, restroom_locations: tuple[GridVector]) -> bool:
        "resolve - utility"
        unique_restroom_locations = set(restroom_locations)
        return len(unique_restroom_locations) == len(restroom_locations) and not (
            unique_restroom_locations & set(self.playground_locations)
        )


@dataclass
class RRGLS_Task(_Task):
    "Random-Restart Greedy Local Search Task"
    target_restroom_locations_count: int
    restart_count: int

    def __post_init__(self):
        if not self.restart_count:
            self.restart_count = 3e3

    def resolve(self) -> TaskResult:
        best_task_result = min(
            map(GLS_Task.resolve, self.get_gls_tasks(self.restart_count)),
            key=lambda result: result["best_cost"],
        )
        del best_task_result["ini_cost"]
        return best_task_result

    def get_gls_tasks(self, restart_count: int):
        "resolve - utility"
        from random import sample as random_sample, seed

        seed(99)  # To avoid being underscored

        while restart_count > 0:
            gls_task = GLS_Task(
                grid_size=self.grid_size,
                kind=self.kind,
                playground_locations=self.playground_locations,
                initial_restroom_locations=tuple(
                    random_sample(
                        self.grid_size.as_grid,
                        k=self.target_restroom_locations_count,
                    )
                ),
            )
            if not gls_task.check_restroom_locations(
                gls_task.initial_restroom_locations
            ):
                continue
            yield gls_task
            restart_count -= 1


class Task(_Task):
    "Task"

    @staticmethod
    def from_list(body: list[str]) -> "Task":
        task = _Task.from_list(body)
        if task.kind == 0:
            return GLS_Task(
                **task.__dict__,
                initial_restroom_locations=tuple(
                    map(GridVector.from_str, body[3].split("|")[1:])
                ),
            )
        elif task.kind == 1:
            return RRGLS_Task(
                **task.__dict__,
                target_restroom_locations_count=int(body[3]),
                restart_count=int(body[4]) if len(body) > 4 else None,
            )
        else:
            return task


task_result = Task.from_list(task_content).resolve()

# END_YOUR_CODE
#######################################################################

# output your final result
print(json.dumps(task_result))

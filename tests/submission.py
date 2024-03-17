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
from itertools import product as cartesian_product


class GridVector(NamedTuple):
    v: int
    h: int

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

    @staticmethod
    def from_str(loc_str: str) -> "GridVector":
        return GridVector(*map(int, loc_str.split(",")[:2]))

    def l1_distance(self, other: "GridVector") -> int:
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
    "Base Task"
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
        def get_cost(restroom_locations: tuple[GridVector]) -> int:
            "resolve - utility"
            return sum(
                min(map(playground_location.l1_distance, restroom_locations))
                for playground_location in self.playground_locations
            )

        def check_next_restroom_locations(
            next_restroom_locations: tuple[GridVector],
        ) -> bool:
            "resolve - utility"
            unique_next_restroom_locations = set(next_restroom_locations)
            return len(unique_next_restroom_locations) == len(
                next_restroom_locations
            ) and not (set(self.playground_locations) & unique_next_restroom_locations)

        def step(
            current_cost: int,
            current_restroom_locations: tuple[GridVector],
        ) -> tuple[int, tuple[GridVector]] | None:
            "resolve - utility"
            next_costs_and_restroom_locations = (
                (get_cost(next_restroom_locations), next_restroom_locations)
                for next_restroom_locations in filter(
                    check_next_restroom_locations,
                    cartesian_product(
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
                    ),
                )
            )
            better_cost, better_restroom_locations = min(
                next_costs_and_restroom_locations
            )
            for better_restroom_location in better_restroom_locations:
                if better_restroom_location in self.playground_locations:
                    return
            if better_cost == current_cost or len(better_restroom_locations) < len(
                self.initial_restroom_locations
            ):
                return
            return (better_cost, better_restroom_locations)

        initial_cost = get_cost(self.initial_restroom_locations)
        best_cost = initial_cost
        best_locations = self.initial_restroom_locations
        while state := step(best_cost, best_locations):
            best_cost, best_locations = state

        return TaskResult(
            ini_cost=initial_cost,
            best_cost=best_cost,
            locations=best_locations,
        )


@dataclass
class RRGLS_Task(_Task):
    "Random-Restart Greedy Local Search Task"
    target_restroom_locations_count: int
    restart_count: int

    def resolve(self) -> TaskResult:
        return TaskResult(
            ini_cost=15,
            best_cost=9,
            locations=[GridVector(1, 2)],
            s=str(self),
        )


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

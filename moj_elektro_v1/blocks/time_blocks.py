from json import load
from logging import Logger, getLogger
from os.path import dirname, join


class TimeBlocks(object):
    def __init__(
        self,
        slot_definitions: dict[str, list | dict],
        logger: Logger | None = None,
    ) -> None:
        self._logger = logger if logger is not None else getLogger("TimeBlocks")
        self._slot_definitions = (
            slot_definitions if slot_definitions is not None else {}
        )

    @classmethod
    def load_time_block_definitions(
        cls, path_to_definition: str | None = None, logger: Logger | None = None
    ):
        defs = {}
        if path_to_definition is None:
            path_to_definition = join(dirname(__file__), "time_blocks.json")
        with open(path_to_definition) as d_f:
            defs = load(d_f)
        return TimeBlocks(defs, logger)

    def _check_holiday(self, row: dict):
        if "holidays" in self._slot_definitions:
            for hldy in self._slot_definitions["holidays"]:
                found = False
                for hldy_prt_nm in hldy:
                    if hldy_prt_nm in row:
                        if row[hldy_prt_nm] == hldy[hldy_prt_nm]:
                            found = True
                        else:
                            found = False
                            break
                    else:
                        found = False
                        break
                if found:
                    return True
                else:
                    continue
        return False

    def _get_time_slot(self, row: dict):
        ret = {}
        ret["hol"] = self._check_holiday(row)
        for timer_tp in self._slot_definitions["time_slots"]:
            if (
                timer_tp
                in self._slot_definitions["time_slot_timer_translation"]
            ):
                tm_nm = self._slot_definitions["time_slot_timer_translation"][
                    timer_tp
                ]
                if tm_nm in row:
                    val = row[tm_nm]
                    for slot_nm in self._slot_definitions["time_slots"][
                        timer_tp
                    ]:
                        for vector in self._slot_definitions["time_slots"][
                            timer_tp
                        ][slot_nm]:
                            start = vector[0]
                            duration = vector[1]
                            diff = val - start
                            if diff >= 0 and diff < duration:
                                ret[timer_tp] = slot_nm
        return ret

    def _get_slot(self, time_slot: dict, definitions: dict):
        ret = {}
        found = False
        for limit_slot in definitions:
            for time_slot_i in definitions[limit_slot]:
                eq = False
                for time_tp in time_slot_i:
                    if time_tp in time_slot:
                        if time_slot_i[time_tp] == time_slot[time_tp]:
                            eq = True
                        else:
                            eq = False
                            break
                    else:
                        eq = False
                        break
                if eq:
                    found = True
                    break
            if found:
                ret["slot"] = limit_slot
                break
        return ret

    def get_time_slots(self, row: dict):
        time_slot = self._get_time_slot(row)
        slots = {}
        if "slot_defs" in self._slot_definitions and isinstance(
            self._slot_definitions["slot_defs"], dict
        ):
            for slot_nm, slot_def in self._slot_definitions[
                "slot_defs"
            ].items():
                slots[slot_nm] = self._get_slot(time_slot, slot_def)
                if slots[slot_nm] is None:
                    self._logger.info(
                        "Could not find slot for {0} - {1} - {2}",
                        slot_nm,
                        row["dt"],
                        time_slot,
                    )

        return slots

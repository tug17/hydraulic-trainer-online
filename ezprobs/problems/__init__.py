#!/usr/bin/env python3


class Parameter:
    """Holds a parameter and it's description for a problem."""

    def __init__(
        self,
        name,
        display,
        val_min,
        val_max,
        val_step,
        val_initial,
        unit="",
        description="",
    ):
        """Initializes the parameter with the given values.

        Raises a ``ValueError`` if the initial value is not between the minimum
        and maximum value."""
        if val_initial < val_min or val_initial > val_max:
            raise ValueError(
                f"initial value ({val_initial}) must be between minimum ({val_min}) and maximum ({val_max})"
            )

        self.name = name
        self.unit = unit
        self.display = display
        self.description = description
        self.val_initial = val_initial
        self.val_min = val_min
        self.val_max = val_max
        self.val_step = val_step


class Plot:
    """Plot which should appear over the parameter section."""

    def __init__(self, url, alt="", caption=""):
        self.url = url
        self.alt = alt
        self.caption = caption

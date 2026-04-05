from dataclasses import dataclass, field
from typing import Optional, Literal
from datetime import datetime, timedelta


# ------------------------------------------------
# DURATION HELPERS

def _parse_duration(duration: str) -> timedelta:
    """Parse HH:MM:SS string into a timedelta."""
    try:
        parts = duration.split(":")
        return timedelta(hours=int(parts[0]), minutes=int(parts[1]), seconds=int(parts[2]))
    except (ValueError, IndexError):
        raise ValueError(f"Duration must be in format HH:MM:SS, got: '{duration}'")


def time_since(start_time: Optional[str], end_time: Optional[str] = None) -> Optional[str]:
    if not start_time or not end_time:
        return None
    start_dt = datetime.fromisoformat(start_time)
    end_dt = datetime.fromisoformat(end_time)
    delta = end_dt - start_dt
    if delta.total_seconds() < 0:
        return None
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def end_time_from_duration(start_time: str, duration: str) -> str:
    """Calculate end time from a start date string (isoformat) and a duration ("HH:MM:SS" format)."""
    return (datetime.fromisoformat(start_time) + _parse_duration(duration)).isoformat()


def add_durations(durations: list[str]) -> str:
    """Add two durations ("HH:MM:SS" format)"""
    total = sum((_parse_duration(d).total_seconds() for d in durations), 0.0)
    return str(timedelta(seconds=total))


def subtract_durations(duration1: str, duration2: str) -> str:
    """Subtract duration2 from duration1 ("HH:MM:SS" format)"""
    result = _parse_duration(duration1).total_seconds() - _parse_duration(duration2).total_seconds()
    if result < 0:
        raise ValueError("Resulting duration cannot be negative")
    return str(timedelta(seconds=result))


# ------------------------------------------------
# TIMESTAMP & ID

def generate_bake_id() -> str:
    """Generate a unique ID for a bake based on the current timestamp."""
    return "BAKE-" + datetime.now().strftime("%Y%m%d-%H%M%S")

def generate_starter_id() -> str:
    """Generate a unique ID for a starter based on the current timestamp."""
    return "STARTER-" + datetime.now().strftime("%Y%m%d-%H%M%S")


def get_timestamp(override: Optional[str] = None) -> str:
    """Get current timestamp in isoformat."""
    if override:
        return override
    return datetime.now().isoformat()


# ------------------------------------------------
# DATACLASSES


@dataclass
class Ingredient:
    name: str
    type: Literal["flour", "liquid", "starter", "salt", "other"]
    grams: float
    percentage: Optional[float] = None
    timestamp: str = field(default_factory=get_timestamp)


@dataclass
class Feeding:
    """A single feeding/refresh of the starter."""
    time: str = field(default_factory=get_timestamp)
    temperature: Optional[float] = None  # Celsius
    flour_grams: Optional[float] = None
    water_grams: Optional[float] = None
    starter_grams: Optional[float] = None

    @property
    def hydration(self) -> Optional[float]:
        """Calculate hydration ratio of starter (water/flour * 100)."""
        if self.flour_grams <= 0:
            return None
        return round((self.water_grams / self.flour_grams) * 100, 1)


@dataclass
class Starter:
    """Represents a sourdough starter with feeding history."""
    id: str = field(default_factory=generate_starter_id)
    name: Optional[str] = None
    created_at: str = field(default_factory=get_timestamp)
    feedings: list[Feeding] = field(default_factory=list)
    notes: Optional[str] = None

    @property
    def last_feeding(self) -> Optional[Feeding]:
        """Get the most recent feeding."""
        return self.feedings[-1] if self.feedings else None

    @property
    def current_hydration(self) -> Optional[float]:
        """Get hydration from the most recent feeding."""
        feeding = self.last_feeding
        return feeding.hydration if feeding else None

    def add_feeding(self, flour: float, water: float, starter: float, 
                    temperature: Optional[float] = None) -> None:
        """Add a new feeding to the starter."""
        feeding = Feeding(
            temperature=temperature,
            flour_grams=flour,
            water_grams=water,
            starter_grams=starter
        )
        self.feedings.append(feeding)


@dataclass
class Fold:
    """Sub-type used in a baking Stage."""
    type: Literal["stretch-and-fold", "coil fold", "knead"]
    timestamp: str = field(default_factory=get_timestamp)
    previous_timestamp: Optional[str] = field(default=None, repr=False)
    time_since_previous: Optional[str] = field(default=None, init=False)

    def __post_init__(self):
        self.timestamp = get_timestamp(override=self.timestamp)
        self.time_since_previous = time_since(self.previous_timestamp, self.timestamp)


@dataclass
class Proof:
    """Sub-type of the Stage "final proof"."""
    type: Literal["cold", "warm"]
    start_time: str = field(default_factory=get_timestamp)
    end_time: Optional[str] = None
    temperature: Optional[float] = None
    duration: Optional[str] = field(default=None, init=False)

    def __post_init__(self):
        if self.end_time:
            self.duration = time_since(self.start_time, self.end_time)

    def close(self, end_time: Optional[str] = None) -> None:
        """Close this proof by setting end_time and recalculating duration."""
        end_time = get_timestamp(override=end_time)
        if end_time < self.start_time:
            raise ValueError("Proof end_time cannot be before start_time")
        self.end_time = end_time
        self.duration = time_since(self.start_time, self.end_time) 


@dataclass
class Stage:
    """Represents any stage in the baking process."""
    name: str
    start_time: str = field(default_factory=get_timestamp)
    end_time: Optional[str] = None
    duration: Optional[str] = None
    ingredients: list[Ingredient] = field(default_factory=list)
    notes: Optional[str] = None
    folds: list[Fold] = field(default_factory=list)
    proofs: list[Proof] = field(default_factory=list)

    def __post_init__(self):
        # Backfill duration if end_time is already known on construction
        if self.end_time and not self.duration:
            self.duration = time_since(self.start_time, self.end_time)

    def close(self, end_time: Optional[str] = None) -> None:
        """Close this stage by setting end_time and calculating duration."""
        end_time = get_timestamp(override=end_time)
        if end_time < self.start_time:
            raise ValueError("Stage end_time cannot be before start_time")
        self.end_time = end_time
        self.duration = time_since(self.start_time, self.end_time)


@dataclass
class BakeStage:
    """Represents the oven/baking phase with optional steam and open phases."""
    name: str = field(default_factory="bake")
    type: Optional[Literal["open bake", "dutch oven"]] = None
    start_time: str = Optional[str]
    end_time: Optional[str] = None
    score_time: Optional[str] = None
    duration: Optional[str] = None
    notes: Optional[str] = None
    preheat_time: Optional[str] = None
    preheat_duration: Optional[str] = None
    preheat_temperature: Optional[float] = None
    steam_time: Optional[str] = None
    steam_duration: Optional[str] = None
    steam_temperature: Optional[str] = None
    open_time: Optional[str] = None
    open_duration: Optional[str] = None
    open_temperature: Optional[float] = None

    def __post_init__(self):
        if not self.start_time and (self.steam_time or self.open_time):
            self.start_time = self.steam_time or self.open_time
        self._resolve_preheat()
        if not self.start_time:
            self.start_time = get_timestamp(override=self.start_time)
        self.score_time = get_timestamp(override=self.score_time or self.start_time)
        self._resolve_total_duration()
        self._resolve_steam()
        self._resolve_oven_open()

    def _resolve_preheat(self):
        if self.preheat_time and self.preheat_duration:
            # Derive start_time from preheat end
            self.start_time = end_time_from_duration(self.preheat_time, self.preheat_duration)
        elif self.preheat_time and self.start_time:
            # Both explicitly provided — validate ordering
            if self.preheat_time >= self.start_time:
                raise ValueError(
                    f"preheat_time ({self.preheat_time}) must be before start_time ({self.start_time})"
                )
            else:
                self.preheat_duration = time_since(self.preheat_time, self.start_time)
        elif self.start_time and self.preheat_duration and not self.preheat_time:
            # Derive preheat_time by working backwards from start_time
            preheat_dt = datetime.fromisoformat(self.start_time) - _parse_duration(self.preheat_duration)
            self.preheat_time = preheat_dt.isoformat()

    def _resolve_total_duration(self):
        """Resolve end_time and duration from each other, or from steam + open phases."""
        if self.end_time and not self.duration:
            self.duration = time_since(self.start_time, self.end_time)
        elif self.duration and not self.end_time:
            self.end_time = end_time_from_duration(self.start_time, self.duration)
        elif self.steam_duration and self.open_duration and not self.duration:
            self.duration = add_durations([self.steam_duration, self.open_duration])
            self.end_time = end_time_from_duration(self.start_time, self.duration)

    def _resolve_steam(self):
        """Steam phase starts at oven start if no explicit steam_time given."""
        if self.steam_duration and not self.steam_time:
            self.steam_time = self.start_time

    def _resolve_oven_open(self):
        """
        Resolve open_time and open_duration.
        open_time derives from end of steam phase.
        open_duration fills the gap from open_time to end_time, or works backwards.
        """
        # Derive open_time from end of steam phase
        if not self.open_time and self.steam_time and self.steam_duration:
            self.open_time = end_time_from_duration(self.steam_time, self.steam_duration)

        # Derive open_duration from open_time → end_time
        if self.open_time and self.end_time and not self.open_duration:
            self.open_duration = time_since(self.open_time, self.end_time)

        # Derive open_time by working backwards from end_time and open_duration
        elif self.open_duration and self.end_time and not self.open_time:
            open_dt = datetime.fromisoformat(self.end_time) - _parse_duration(self.open_duration)
            self.open_time = open_dt.isoformat()


@dataclass
class BakeOutcome:
    """Baking outcome scores (1-5) and notes."""
    oven_spring: Optional[float] = None
    crumb: Optional[float] = None
    crust: Optional[float] = None
    flavour: Optional[float] = None
    overall: Optional[float] = None
    notes: Optional[str] = None

    def __post_init__(self):
        for field_name in ['oven_spring', 'crumb', 'crust', 'flavour', 'overall']:
            value = getattr(self, field_name, None)
            if value is not None and (value < 1 or value > 5):
                raise ValueError(f"{field_name} score must be between 1 and 5, got {value}")
        
        if not self.overall and any([self.oven_spring, self.crumb, self.crust, self.flavour]):
            # If overall score is missing but other scores are present, calculate average
            scores = [s for s in [self.oven_spring, self.crumb, self.crust, self.flavour] if s is not None]
            if scores:
                self.overall = round(sum(scores) / len(scores), 1)
    

@dataclass
class Bake:
    """Represents a bake instance with all associated attributes and details."""
    id: str = field(default_factory=generate_bake_id)
    start_time: str = field(default_factory=get_timestamp)
    end_time: Optional[str] = None
    room_temperature: Optional[float] = None
    recipe_label: Optional[str] = None
    ingredients: list[Ingredient] = field(default_factory=list)
    starter: Optional[Starter] = None
    stages: list[Stage] = field(default_factory=list)
    bake_stage: Optional[BakeStage] = None
    outcome: BakeOutcome = field(default_factory=BakeOutcome)

    def __post_init__(self):
        if not self.recipe_label:
            date_obj = datetime.fromisoformat(self.start_time)
            self.recipe_label = f"Bake {date_obj.strftime('%d-%m-%Y')}"

    def adjust_start_time(self):
        """Set bake start_time to the timestamp of the first ingredient."""
        if self.ingredients:
            first_ingredient_time = min(i.timestamp for i in self.ingredients)
            if first_ingredient_time:
                self.start_time = first_ingredient_time


    def starter_percentages(self) -> tuple[Optional[float], Optional[float]]:
        """Calculate flour and water percentages in the starter."""
        if not self.starter or not self.starter.current_hydration:
            hydration_ratio = 100 / 100  # Assume 100% hydration if unknown (equal parts flour and water)
        else:
            hydration_ratio = starter.current_hydration / 100
        starter_grams = sum(i.grams for i in self.ingredients if i.type == "starter")
        if starter_grams > 0:
            starter_flour = starter_grams / (1 + hydration_ratio)
            starter_water = starter_flour * hydration_ratio
            return starter_flour, starter_water, starter_grams
        return None, None, None

    @property
    def total_flour(self) -> Optional[float]:
        """Calculate total flour from ingredients."""
        flour_total = sum(i.grams for i in self.ingredients if i.type == "flour")
        starter_flour, _, _ = self.starter_percentages() 
        if starter_flour:
            flour_total += starter_flour
        return flour_total if flour_total > 0 else None

    def calculate_ingredient_percentages(self):
        """Calculate the percentage of each ingredient as compared to the total flour."""
        total_flour = self.total_flour
        if total_flour == 0:
            raise ValueError("Total flour weight cannot be zero")
        for i in self.ingredients:
            i.percentage = round((i.grams / total_flour) * 100, 1)
        return

    @property
    def hydration(self) -> Optional[float]:
        """Calculate hydration percentage from liquid ingredients."""
        try:
            if not self.total_flour or self.total_flour <= 0:
                return None

            # Total liquid ingredients
            total_liquid = sum(i.grams for i in self.ingredients if i.type == "liquid")

            _, starter_water, _ = self.starter_percentages()
            if starter_water:
                total_liquid += starter_water
            return round((total_liquid / self.total_flour) * 100, 1)
        except (ValueError, ZeroDivisionError):
            return None

    @property
    def inoculation(self) -> Optional[float]:
        """Calculate inoculation percentage from starter ingredients."""
        try:
            if not self.total_flour or self.total_flour <= 0:
                return None
            total_starter = sum(i.grams for i in self.ingredients if i.type == "starter")
            return round((total_starter / self.total_flour) * 100, 1)
        except (ValueError, ZeroDivisionError):
            return None

    @property
    def salt_percentage(self) -> Optional[float]:
        """Calculate salt percentage from salt ingredients."""
        try:
            if not self.total_flour or self.total_flour <= 0:
                return None
            total_salt = sum(i.grams for i in self.ingredients if i.type == "salt")
            return round((total_salt / self.total_flour) * 100, 1)
        except (ValueError, ZeroDivisionError):
            return None


# ------------------------------------------------
# STAGE DETECTION


def detect_stage(ingredients: list[Ingredient]) -> str:
    """
    Detect mixing stage from the set of ingredient types present.
    Uses cumulative ingredient list — later additions accumulate earlier ones.
    """
    types = {i.type for i in ingredients}

    has_flour = "flour" in types
    has_liquid = "liquid" in types
    has_starter = "starter" in types
    has_salt = "salt" in types

    if has_flour and has_liquid and has_salt and has_starter:
        return "mixing"
    elif has_flour and has_liquid and has_starter and not has_salt:
        return "fermentolyse"
    elif has_flour and has_liquid and not has_starter and not has_salt:
        return "autolyse"
    else:
        return "invalid_combination"


def group_ingredients_by_stage(ingredients: list[Ingredient]) -> list[Stage]:
    """
    Groups ingredients by truncated timestamp (minute-level precision).
    Each group is cumulative — later timestamps include all prior ingredients —
    so that detect_stage sees the full accumulated dough at each point.

    Each stage closes when the next one begins.
    Bulk fermentation opens when starter is added and closes when
    a handling stage is explicitly added via add_handling_stage().
    """
    timestamps = sorted(set(i.timestamp[:16] for i in ingredients))

    stages = []
    for idx, ts in enumerate(timestamps):
        group = [i for i in ingredients if i.timestamp[:16] <= ts]
        stage_name = detect_stage(group)

        # End time is the start of the next timestamp group, if one exists
        end_ts = timestamps[idx + 1] if idx + 1 < len(timestamps) else None

        stage = Stage(name=stage_name, start_time=ts, end_time=end_ts, ingredients=group)

        # Calculate duration if we have both times
        if end_ts:
            stage.duration = time_since(ts, end_ts)

        stages.append(stage)

    # Bulk fermentation — starts when starter is added, left open
    # (closed explicitly by add_handling_stage)
    starter_ingredients = [i for i in ingredients if i.type == "starter"]
    if starter_ingredients:
        starter_timestamp = min(i.timestamp for i in starter_ingredients)
        stages.append(Stage(
            name="bulk fermentation",
            start_time=starter_timestamp,
            ingredients=ingredients
        ))

    return stages
from bake_utils import Bake, Ingredient, BakeStage
from bake_ops import (
    add_ingredients, add_fold, add_handling_stage,
    add_proof, close_proof, add_bake_stage, set_outcome
)
from bake_storage import save_bake, load_bake
from bake_adviser import get_bake_advice
import json
from dataclasses import asdict

# 1. Start a bake
bake = Bake(recipe_label="Test White Sourdough")

# 2. Add ingredients with staggered timestamps (autolyse → fermentolyse → mixing)
bake = add_ingredients(bake, [
    Ingredient(name="white bread flour", type="flour",   grams=400, timestamp="2026-04-04T09:00:00"),
    Ingredient(name="water",             type="liquid",  grams=300, timestamp="2026-04-04T09:00:00"),
    Ingredient(name="starter",           type="starter", grams=80,  timestamp="2026-04-04T09:30:00"),
    Ingredient(name="salt",              type="salt",    grams=9,   timestamp="2026-04-04T09:45:00"),
])

# 3. Folds during bulk fermentation
bake = add_fold(bake, "stretch-and-fold", fold_time="2026-04-04T10:30:00")
bake = add_fold(bake, "stretch-and-fold", fold_time="2026-04-04T11:00:00")
bake = add_fold(bake, "coil fold",        fold_time="2026-04-04T11:30:00")
bake = add_fold(bake, "coil fold",        fold_time="2026-04-04T12:00:00")

# 4. Pre-shape and bench rest
bake = add_handling_stage(bake, "pre-shape", start_time="2026-04-04T14:00:00")

# 5. Final shape and open final proof
bake = add_handling_stage(bake, "final shape", start_time="2026-04-04T14:20:00")

# 6. Cold proof overnight
bake = add_proof(bake, "cold", temperature=4.0)
bake = close_proof(bake, end_time="2026-04-04T22:00:00")

# 7. Oven stage
bake = add_bake_stage(bake, BakeStage(
    name="bake",
    preheat_time="2026-04-05T07:00:00",
    preheat_duration="00:45:00",
    preheat_temperature=250.0,
    steam_duration="00:20:00",
    open_duration="00:25:00",
))

# 8. Score the outcome
bake = set_outcome(bake, oven_spring=4, crumb=3, crust=5, flavour=4, overall=4,
                   notes="Good crust, slightly dense crumb. Extend bulk next time.")

# 9. Inspect the JSON
print(json.dumps(asdict(bake), indent=2, default=str))

# 10. Save and reload
save_bake(bake)
reloaded = load_bake(bake.id)
assert reloaded is not None, "Save/load failed"
print(f"\n✓ Saved and reloaded bake {bake.id}")

# 11. Get AI advice
print("\n--- Adviser ---")
print(get_bake_advice(bake))
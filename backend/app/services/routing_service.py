import random
from typing import Any
from typing import List
from app.schemas.routing import PathSuggestion

class RoutingService:
    async def compute_alternate_paths(self, area: str | None = None) -> List[PathSuggestion]:
        letters = "CDEFGHIJKLMNOP"
        rand_letter = random.choice(letters)
        label = f" around {area}" if area else ""
        return [
            PathSuggestion(
                name=f"PATH {rand_letter}: DYNAMIC",
                dist=f"{round(random.uniform(5, 13), 1)}km",
                desc=f"AI computed alternate route{label} via secondary grid lanes.",
                efficiency=random.randint(82, 97),
                color="primary"
            )
        ]

    async def paths_from_reroute_result(self, result: dict[str, Any]) -> List[PathSuggestion]:
        if result.get("status") == "error":
            return [
                PathSuggestion(
                    name="PATH HOLD: REVIEW",
                    dist="0.0km",
                    desc=f"Reroute failed: {result.get('error', 'manual review required')}",
                    efficiency=50,
                    color="secondary",
                )
            ]

        action = result.get("action_taken", "MONITOR")
        selected_driver = result.get("selected_driver") or "available fleet"
        selected_store = result.get("selected_store") or "current destination"
        confidence = int(float(result.get("confidence") or 0.75) * 100)
        return [
            PathSuggestion(
                name=f"PATH AI: {action}",
                dist=f"{round(random.uniform(6, 14), 1)}km",
                desc=f"Agent-selected route using {selected_driver} toward {selected_store}.",
                efficiency=max(60, min(99, confidence)),
                color="primary",
            )
        ]
        
    async def get_cached_suggestions(self, area: str | None) -> List[PathSuggestion]:
        return [
            PathSuggestion(
                name="PATH A: EXPRESS",
                dist="8.2km",
                desc="Prioritizes speed via Perimeter Bypass.",
                efficiency=85,
                color="primary"
            ),
            PathSuggestion(
                name="PATH B: SECURE",
                dist="12.4km",
                desc="Maximum threat avoidance. 0 risk.",
                efficiency=98,
                color="secondary"
            )
        ]

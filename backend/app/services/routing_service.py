import random
from typing import List
from app.schemas.routing import PathSuggestion

class RoutingService:
    async def compute_alternate_paths(self) -> List[PathSuggestion]:
        letters = "CDEFGHIJKLMNOP"
        rand_letter = random.choice(letters)
        return [
            PathSuggestion(
                name=f"PATH {rand_letter}: DYNAMIC",
                dist=f"{round(random.uniform(5, 13), 1)}km",
                desc="AI computed alternate route via secondary grid lanes.",
                efficiency=random.randint(82, 97),
                color="primary"
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

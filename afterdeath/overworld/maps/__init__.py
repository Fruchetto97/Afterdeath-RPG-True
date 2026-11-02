"""Overworld maps and the roadmap of event-driven map transitions.

Each event name maps to a tuple: (map config module, spawnpoint name).
"""

from afterdeath.overworld.maps import citta_01, foresta_dorsale_est, foresta_dorsale_sud

MAP_TRANSITIONS = {
    # 1. Event triggers transition to foresta_dorsale_est at Spawnpoint_1
    "evento_transizione_foresta_dorsale_sud_est_1": (foresta_dorsale_est, "Spawnpoint_1"),
    # 2. Event triggers transition to foresta_dorsale_est at Spawnpoint_2
    "evento_transizione_foresta_dorsale_sud_est_2": (foresta_dorsale_est, "Spawnpoint_2"),
    # 3. Event triggers transition to foresta_dorsale_sud at Spawnpoint_3
    "evento_transizione_foresta_dorsale_est_sud_1": (foresta_dorsale_sud, "Spawnpoint_3"),
    # 4. Event triggers transition to foresta_dorsale_sud at Spawnpoint_2
    "evento_transizione_foresta_dorsale_est_sud_2": (foresta_dorsale_sud, "Spawnpoint_2"),
    # 5. Event triggers transition to citta_01 at Spawnpoint_1
    "evento_transizione_foresta_dorsale_sud_citta_1": (citta_01, "Spawnpoint_1"),
    # 6. Event triggers transition to citta_01 at Spawnpoint_2
    "evento_transizione_citta_1_foresta_dorsale_sud": (foresta_dorsale_sud, "Spawnpoint_1"),
}

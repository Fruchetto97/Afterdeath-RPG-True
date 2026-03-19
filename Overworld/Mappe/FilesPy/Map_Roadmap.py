# Map_Roadmap.py
# Central roadmap for event-driven map transitions
# Each event name maps to a tuple: (map config module, spawnpoint name)

import foresta_dorsale_est_config
import foresta_dorsale_sud_config
import citta_01_config

MAP_TRANSITIONS = {
    # 1. Event triggers transition to foresta_dorsale_est_config at Spawnpoint_1
    "evento_transizione_foresta_dorsale_sud_est_1": (foresta_dorsale_est_config, "Spawnpoint_1"),
    # 2. Event triggers transition to foresta_dorsale_est_config at Spawnpoint_2
    "evento_transizione_foresta_dorsale_sud_est_2": (foresta_dorsale_est_config, "Spawnpoint_2"),
    # 3. Event triggers transition to foresta_dorsale_sud_config at Spawnpoint_3
    "evento_transizione_foresta_dorsale_est_sud_1": (foresta_dorsale_sud_config, "Spawnpoint_3"),
    # 4. Event triggers transition to foresta_dorsale_sud_config at Spawnpoint_2
    "evento_transizione_foresta_dorsale_est_sud_2": (foresta_dorsale_sud_config, "Spawnpoint_2"),
    # 5. Event triggers transition to citta_01_config at Spawnpoint_1
    "evento_transizione_foresta_dorsale_sud_citta_1": (citta_01_config, "Spawnpoint_1"),
    # 6. Event triggers transition to citta_01_config at Spawnpoint_2
    "evento_transizione_citta_1_foresta_dorsale_sud": (foresta_dorsale_sud_config, "Spawnpoint_1"),
}

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

Position = Tuple[int, int]
DEFAULT_LOG_LIMIT = 100


@dataclass
class MoveResult:
    """Represents the final outcome of a movement attempt.

    This object is meant to be produced by the game logic layer and then
    consumed by GameState. It contains the intended action, the attempted
    position, the final resolved position, and any side effects that should
    be committed to state such as rewards, status flags, or event text.
    """

    intended_direction: str
    attempted_pos: Position
    final_pos: Position
    success: bool
    turn_spent: bool = True
    event_type: Optional[str] = None
    event_text: Optional[str] = None
    reward: Optional[Dict[str, int]] = None
    status_updates: Optional[Dict[str, bool]] = None


@dataclass
class GameState:
    """Stores the canonical state of a single game session.

    This class is responsible for holding persistent gameplay data such as
    map dimensions, player and goal positions, turn count, discovered tiles,
    inventory, status flags, and the event log. It does not decide whether a
    move is legal; instead, it applies already-resolved outcomes provided by
    MoveResult or another rules layer.
    """

    rows: int
    cols: int
    player_pos: Position
    goal_pos: Position
    turn: int = 0
    log_limit: int = DEFAULT_LOG_LIMIT
    log: List[str] = field(default_factory=list)
    inventory: Dict[str, int] = field(default_factory=dict)
    status: Dict[str, bool] = field(default_factory=dict)
    discovered: List[List[bool]] = field(default_factory=list)

    def __post_init__(self):
        """Normalize positions and initialize discovery data after construction.

        Player and goal positions are clamped to stay within map bounds. If no
        discovery grid is provided, a fresh one is created and the player's
        starting tile is marked as discovered.
        """
        self.player_pos = self._clamp_pos(self.player_pos)
        self.goal_pos = self._clamp_pos(self.goal_pos)

        if not self.discovered:
            self.discovered = [
                [False for _ in range(self.cols)]
                for _ in range(self.rows)
            ]

        self.discover(self.player_pos)

    def _clamp_pos(self, pos: Position) -> Position:
        """Clamp a position so it always remains inside the map boundaries."""
        r, c = pos
        r = max(0, min(self.rows - 1, r))
        c = max(0, min(self.cols - 1, c))
        return (r, c)

    def discover(self, pos: Position) -> None:
        """Mark a tile as discovered if the given position is in bounds."""
        r, c = pos
        if 0 <= r < self.rows and 0 <= c < self.cols:
            self.discovered[r][c] = True

    def add_log(self, text: str) -> None:
        """Append a message to the log and trim it to the configured limit.

        The newest entries are preserved. Older entries are discarded once the
        log grows beyond log_limit.
        """
        self.log.append(text)
        if len(self.log) > self.log_limit:
            self.log = self.log[-self.log_limit:]

    def apply_move_result(self, result: MoveResult) -> None:
        """Apply a resolved move outcome to the current game state.

        This updates the player's final position, optionally increments the
        turn counter, reveals the destination tile, applies inventory rewards,
        updates status flags, and records an event or fallback movement log.
        """
        self.player_pos = self._clamp_pos(result.final_pos)

        if result.turn_spent:
            self.turn += 1

        self.discover(self.player_pos)

        if result.reward:
            for item, qty in result.reward.items():
                self.inventory[item] = self.inventory.get(item, 0) + qty

        if result.status_updates:
            self.status.update(result.status_updates)

        if result.event_text:
            self.add_log(result.event_text)
        else:
            if result.success:
                self.add_log(
                    f"Moved {result.intended_direction} to {result.final_pos}."
                )
            else:
                self.add_log(
                    f"Tried to move {result.intended_direction}, but remained at {self.player_pos}."
                )

    def is_victory(self) -> bool:
        """Return True when the player has reached the goal position."""
        return self.player_pos == self.goal_pos

    def reset(self, player_pos: Position, goal_pos: Position) -> None:
        """Reset the session to a fresh state with new start and goal positions.

        Turn count, log, inventory, status flags, and discovery data are all
        cleared. The new starting tile is then marked as discovered and a reset
        message is added to the log.
        """
        self.player_pos = self._clamp_pos(player_pos)
        self.goal_pos = self._clamp_pos(goal_pos)
        self.turn = 0
        self.log.clear()
        self.inventory.clear()
        self.status.clear()
        self.discovered = [
            [False for _ in range(self.cols)]
            for _ in range(self.rows)
        ]
        self.discover(self.player_pos)
        self.add_log("Game reset.")

    def to_dict(self) -> Dict:
        """Serialize the current state into a plain dictionary.

        This is useful for storage, Streamlit session state, debugging, or
        sending a compact state snapshot to other parts of the application.
        """
        return {
            "rows": self.rows,
            "cols": self.cols,
            "player_pos": self.player_pos,
            "goal_pos": self.goal_pos,
            "turn": self.turn,
            "log_limit": self.log_limit,
            "log": self.log,
            "inventory": self.inventory,
            "status": self.status,
            "discovered": self.discovered,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "GameState":
        """Build a GameState instance from a serialized dictionary.

        Missing optional fields fall back to sensible defaults so the state can
        be reconstructed even from partial saved data.
        """
        state = cls(
            rows=data["rows"],
            cols=data["cols"],
            player_pos=tuple(data["player_pos"]),
            goal_pos=tuple(data["goal_pos"]),
            turn=data.get("turn", 0),
            log_limit=data.get("log_limit", DEFAULT_LOG_LIMIT),
            log=data.get("log", []),
            inventory=data.get("inventory", {}),
            status=data.get("status", {}),
            discovered=data.get("discovered", []),
        )
        return state

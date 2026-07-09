from grid_rpg_ai.gamestate import GameState, MoveResult

state = GameState(
    rows=6,
    cols=6,
    player_pos=(2, 2),
    goal_pos=(5, 5),
)

print("INITIAL")
print("player_pos:", state.player_pos)
print("turn:", state.turn)
print("inventory:", state.inventory)
print("status:", state.status)
print("log:", state.log)
print()

dummy_result = MoveResult(
    intended_direction="right",
    attempted_pos=(2, 3),
    final_pos=(2, 3),
    success=True,
    turn_spent=True,
    event_type="reward",
    event_text="You step onto a dusty tile and find a rusty key.",
    reward={"rusty_key": 1},
    status_updates={"saw_strange_marks": True},
)

state.apply_move_result(dummy_result)

print("AFTER APPLY")
print("player_pos:", state.player_pos)
print("turn:", state.turn)
print("inventory:", state.inventory)
print("status:", state.status)
print("log:", state.log)
print("victory:", state.is_victory())